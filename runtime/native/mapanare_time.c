/**
 * mapanare_time.c — Date / time runtime shim for Mapanare stdlib/time/.
 *
 * v5.34.0 Dt.8 — exports a small set of read-only syscall wrappers that the
 * .mn date/time stdlib builds on. POSIX path is the default; Windows path
 * sits behind #ifdef _WIN32 so the .mn side never sees the platform split.
 *
 * Mapanare's `extern "C" fn` syntax exposes only scalar / String / List<X>
 * returns — there is no out-pointer surface. Every function here therefore
 * returns a single Int (encoded as int64). Broken-down date/time values use
 * a packed representation:
 *
 *     packed = y*10^10 + mo*10^8 + d*10^6 + h*10^4 + mi*10^2 + s
 *
 * which fits comfortably in int64 (max value ~10^14 for year 9999) and lets
 * the .mn caller divmod-extract each field. -1 is reserved for syscall
 * failure / overflow on every entry point.
 */

/* Enable POSIX clock_gettime / localtime_r / timegm even with strict -std=c11.
 * Mirrors mapanare_core.c's pattern. */
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#elif !defined(_WIN32)
#if !defined(_POSIX_C_SOURCE) || _POSIX_C_SOURCE < 200809L
#undef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#ifndef _DEFAULT_SOURCE
#define _DEFAULT_SOURCE 1
#endif
#endif

#include "mapanare_core.h"

#include <stdint.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/time.h>
#endif

/* timegm is a BSD/GNU extension. Linux glibc + macOS expose it; Windows
 * MinGW does not, so we provide a portable inverse-of-gmtime fallback. */
#if defined(_WIN32) || (defined(__APPLE__) && !defined(_DARWIN_C_SOURCE))
static int64_t mn_timegm_portable(struct tm *tm);
#endif

/* -----------------------------------------------------------------------
 * Packed datetime helpers
 *
 * pack_dt(y, mo, d, h, mi, s) -> int64
 *   Returns -1 if year out of [1, 9999]. Caller passes already-normalized
 *   fields; this helper does NOT normalize.
 *
 * The .mn side decodes via repeated `% 100` / `/ 100`, ending with year.
 * ----------------------------------------------------------------------- */

static int64_t pack_dt(int64_t y, int64_t mo, int64_t d,
                       int64_t h, int64_t mi, int64_t s) {
    if (y < 1 || y > 9999) return -1;
    return y * 10000000000LL
         + mo * 100000000LL
         + d  * 1000000LL
         + h  * 10000LL
         + mi * 100LL
         + s;
}

/* -----------------------------------------------------------------------
 * Leap year + days-per-month — used by __mn_normalize_pack only. The .mn
 * side has its own copy for validation; this one supports normalize.
 * ----------------------------------------------------------------------- */

static int is_leap(int64_t y) {
    if (y % 400 == 0) return 1;
    if (y % 100 == 0) return 0;
    if (y % 4 == 0) return 1;
    return 0;
}

static int days_in_month(int64_t y, int64_t mo) {
    static const int dim[13] = {0, 31, 28, 31, 30, 31, 30,
                                31, 31, 30, 31, 30, 31};
    if (mo < 1 || mo > 12) return 0;
    if (mo == 2 && is_leap(y)) return 29;
    return dim[mo];
}

/* -----------------------------------------------------------------------
 * __mn_now_realtime_ns — total nanoseconds since UNIX epoch as int64.
 *
 * Wraps in year 2262 (i64 ns overflow); v5.x apps don't care.
 * Returns -1 on syscall failure.
 * ----------------------------------------------------------------------- */

MN_EXPORT int64_t __mn_now_realtime_ns(void) {
#ifdef _WIN32
    /* GetSystemTimePreciseAsFileTime is Windows 8+; gives 100ns resolution.
     * FILETIME epoch is 1601-01-01 UTC; Unix epoch is 1970-01-01 UTC.
     * Difference is 11644473600 seconds. */
    FILETIME ft;
    GetSystemTimePreciseAsFileTime(&ft);
    ULARGE_INTEGER ui;
    ui.LowPart = ft.dwLowDateTime;
    ui.HighPart = ft.dwHighDateTime;
    int64_t hundred_ns_since_1601 = (int64_t)ui.QuadPart;
    int64_t hundred_ns_since_1970 = hundred_ns_since_1601 - 116444736000000000LL;
    return hundred_ns_since_1970 * 100LL;
#else
    struct timespec ts;
    if (clock_gettime(CLOCK_REALTIME, &ts) != 0) return -1;
    return (int64_t)ts.tv_sec * 1000000000LL + (int64_t)ts.tv_nsec;
#endif
}

/* -----------------------------------------------------------------------
 * __mn_utc_pack — UTC broken-down time for a given epoch second, packed.
 * Returns -1 on syscall failure or out-of-range year.
 * ----------------------------------------------------------------------- */

MN_EXPORT int64_t __mn_utc_pack(int64_t epoch_secs) {
    time_t t = (time_t)epoch_secs;
    struct tm out;
#ifdef _WIN32
    /* MS gmtime_s argument order is reversed from POSIX gmtime_r:
     *   POSIX:  gmtime_r(const time_t*, struct tm*)
     *   MS:     gmtime_s(struct tm*, const time_t*)
     */
    if (gmtime_s(&out, &t) != 0) return -1;
#else
    if (gmtime_r(&t, &out) == NULL) return -1;
#endif
    return pack_dt((int64_t)out.tm_year + 1900,
                   (int64_t)out.tm_mon + 1,
                   (int64_t)out.tm_mday,
                   (int64_t)out.tm_hour,
                   (int64_t)out.tm_min,
                   (int64_t)out.tm_sec);
}

/* -----------------------------------------------------------------------
 * __mn_local_pack — local broken-down time for given epoch second, packed.
 * Honors the TZ env var on POSIX; honors system local on Windows.
 * Returns -1 on syscall failure or out-of-range year.
 * ----------------------------------------------------------------------- */

MN_EXPORT int64_t __mn_local_pack(int64_t epoch_secs) {
    time_t t = (time_t)epoch_secs;
    struct tm out;
#ifdef _WIN32
    /* MS localtime_s argument order is reversed from POSIX localtime_r:
     *   POSIX:  localtime_r(const time_t*, struct tm*)
     *   MS:     localtime_s(struct tm*, const time_t*)
     */
    if (localtime_s(&out, &t) != 0) return -1;
#else
    if (localtime_r(&t, &out) == NULL) return -1;
#endif
    return pack_dt((int64_t)out.tm_year + 1900,
                   (int64_t)out.tm_mon + 1,
                   (int64_t)out.tm_mday,
                   (int64_t)out.tm_hour,
                   (int64_t)out.tm_min,
                   (int64_t)out.tm_sec);
}

/* -----------------------------------------------------------------------
 * __mn_local_offset_minutes — local TZ offset in minutes east of UTC for
 * the given epoch second (handles DST at that instant).
 *
 * POSIX `struct tm.tm_gmtoff` is seconds east of UTC. Windows derives the
 * offset by computing (local_packed - utc_packed) for the same instant.
 * Returns INT64_MIN on failure (a real offset is always in [-720, +840]).
 * ----------------------------------------------------------------------- */

MN_EXPORT int64_t __mn_local_offset_minutes(int64_t epoch_secs) {
    time_t t = (time_t)epoch_secs;
#ifdef _WIN32
    /* Windows path: derive offset by subtracting utc fields from local
     * fields. Convert both to a comparable scalar (epoch minutes assuming
     * arithmetic Gregorian — only the difference matters, not absolute). */
    struct tm utc_tm, loc_tm;
    if (gmtime_s(&utc_tm, &t) != 0) return INT64_MIN;
    if (localtime_s(&loc_tm, &t) != 0) return INT64_MIN;

    /* Build minutes-since-epoch via timegm-equivalent. We treat both tms
     * as if they were UTC and subtract. _mkgmtime is Windows's timegm. */
    time_t utc_t = _mkgmtime(&utc_tm);
    time_t loc_t = _mkgmtime(&loc_tm);
    if (utc_t == (time_t)-1 || loc_t == (time_t)-1) return INT64_MIN;
    return ((int64_t)loc_t - (int64_t)utc_t) / 60;
#else
    struct tm out;
    if (localtime_r(&t, &out) == NULL) return INT64_MIN;
    /* tm_gmtoff is BSD/GNU; available on Linux glibc + macOS. */
    return (int64_t)out.tm_gmtoff / 60;
#endif
}

/* -----------------------------------------------------------------------
 * __mn_timegm — converts a UTC broken-down time to epoch seconds.
 * Inverse of gmtime. Returns -1 on out-of-range / overflow.
 * ----------------------------------------------------------------------- */

MN_EXPORT int64_t __mn_timegm(int64_t y, int64_t mo, int64_t d,
                              int64_t h, int64_t mi, int64_t s) {
    if (y < 1 || y > 9999) return -1;
    if (mo < 1 || mo > 12) return -1;
    if (d  < 1 || d  > days_in_month(y, mo)) return -1;
    if (h  < 0 || h  > 23) return -1;
    if (mi < 0 || mi > 59) return -1;
    if (s  < 0 || s  > 60) return -1; /* leap second tolerated */

    struct tm tm;
    tm.tm_year = (int)(y - 1900);
    tm.tm_mon  = (int)(mo - 1);
    tm.tm_mday = (int)d;
    tm.tm_hour = (int)h;
    tm.tm_min  = (int)mi;
    tm.tm_sec  = (int)s;
    tm.tm_isdst = 0;
    tm.tm_wday = 0;
    tm.tm_yday = 0;

#ifdef _WIN32
    time_t t = _mkgmtime(&tm);
#elif defined(__APPLE__) || defined(__linux__)
    time_t t = timegm(&tm);
#else
    time_t t = mn_timegm_portable(&tm);
#endif
    if (t == (time_t)-1) return -1;
    return (int64_t)t;
}

/* -----------------------------------------------------------------------
 * __mn_normalize_pack — normalize a (Y, M, D, h, m, s) tuple after
 * Duration arithmetic, then return packed form. Handles month / day
 * rollover and negative durations. Returns -1 if year falls outside
 * [1, 9999] after normalization.
 * ----------------------------------------------------------------------- */

MN_EXPORT int64_t __mn_normalize_pack(int64_t y, int64_t mo, int64_t d,
                                      int64_t h, int64_t mi, int64_t s) {
    /* Cascade overflow upward: seconds → minutes → hours → days → months
     * → years. Negative values cascade downward symmetrically. */

    /* seconds → minutes */
    if (s >= 60 || s < 0) {
        int64_t carry = s / 60;
        s = s - carry * 60;
        if (s < 0) { s += 60; carry -= 1; }
        mi += carry;
    }
    /* minutes → hours */
    if (mi >= 60 || mi < 0) {
        int64_t carry = mi / 60;
        mi = mi - carry * 60;
        if (mi < 0) { mi += 60; carry -= 1; }
        h += carry;
    }
    /* hours → days */
    if (h >= 24 || h < 0) {
        int64_t carry = h / 24;
        h = h - carry * 24;
        if (h < 0) { h += 24; carry -= 1; }
        d += carry;
    }
    /* months → years (do months first so day-of-month rollover sees the
     * right month length). */
    if (mo > 12 || mo < 1) {
        int64_t mzero = mo - 1;            /* shift to 0..11 domain */
        int64_t carry = mzero / 12;
        mzero = mzero - carry * 12;
        if (mzero < 0) { mzero += 12; carry -= 1; }
        mo = mzero + 1;
        y += carry;
    }
    /* days → months/years. Iterative: borrow whole months at a time. */
    while (d > days_in_month(y, mo)) {
        d -= days_in_month(y, mo);
        mo += 1;
        if (mo > 12) { mo = 1; y += 1; }
        if (y > 9999) return -1;
    }
    while (d < 1) {
        mo -= 1;
        if (mo < 1) { mo = 12; y -= 1; }
        if (y < 1) return -1;
        d += days_in_month(y, mo);
    }

    return pack_dt(y, mo, d, h, mi, s);
}

/* -----------------------------------------------------------------------
 * Portable timegm fallback (only compiled on platforms that lack timegm
 * in <time.h>). Linux glibc + macOS + Windows _mkgmtime are covered above;
 * this is for hypothetical exotic targets.
 * ----------------------------------------------------------------------- */

#if defined(_WIN32) || (defined(__APPLE__) && !defined(_DARWIN_C_SOURCE))
static int64_t mn_timegm_portable(struct tm *tm) {
    /* Days from 1970-01-01 to start of (year, 1, 1). */
    int64_t y = (int64_t)tm->tm_year + 1900;
    int64_t m = (int64_t)tm->tm_mon + 1;
    int64_t d = (int64_t)tm->tm_mday;

    int64_t days = 0;
    for (int64_t yy = 1970; yy < y; yy++) days += is_leap(yy) ? 366 : 365;
    for (int64_t mm = 1; mm < m; mm++)    days += days_in_month(y, mm);
    days += d - 1;

    return days * 86400LL
         + (int64_t)tm->tm_hour * 3600
         + (int64_t)tm->tm_min  * 60
         + (int64_t)tm->tm_sec;
}
#endif
