# v5.34.0 — Dt.\* — date / time stdlib

**Status:** PLANNING
**Type:** Stdlib expansion. Pure `.mn` library on top of native
runtime syscalls (no compiler edits, no runtime edits beyond a
thin C shim for `clock_gettime` / `localtime_r`).
**Breaking:** No. Net-new module at `stdlib/time/`.
**Prerequisite:** v5.33.0 shipped (release tarballs ship native
`mnc` on all desktop platforms).
**Estimated effort:** 1–2 sessions. Pure data-types-and-formatting
work with a small portable C shim.

---

## Why this exists

There is no first-class date/time stdlib in Mapanare. Users get
"now is some integer of seconds since epoch" via `runtime.now()`
and nothing else. Real applications need:

- `Date(2026, 5, 3)` as a value, not an integer
- `DateTime` with timezone awareness
- Parsing `"2026-05-03T14:32:00Z"`
- Formatting back: `dt.format("%Y-%m-%d %H:%M:%S")`
- Differences: `dt2 - dt1 -> Duration`
- Arithmetic: `now() + Duration::days(7)`

This is the first item in the **stdlib gap-close arc** (v5.34.0
through v5.39.0) — the foundational items real apps need before
the manifesto items (`ask`, distributed agents, etc.) make sense
to build on.

---

## Goals

1. **Dt.1** — Core types: `Date`, `Time`, `DateTime`, `Duration`,
   `Timezone`. All as `.mn` structs.
2. **Dt.2** — Construction: `Date::new`, `Date::today`,
   `DateTime::now`, `DateTime::from_epoch`, etc.
3. **Dt.3** — Parsing: ISO 8601 + RFC 3339 first; common formats
   (`"YYYY-MM-DD"`, `"HH:MM:SS"`) second.
4. **Dt.4** — Formatting: strftime-compatible format string subset.
5. **Dt.5** — Arithmetic: `+`/`-` with `Duration`; `dt2 - dt1`
   returns `Duration`.
6. **Dt.6** — Timezone support v0: UTC and system-local only. Named
   tzdb lookup (`"America/Lima"`) deferred to v5.34.1 / v5.35.0.
7. **Dt.7** — Tests in `stdlib/time/tests/` — one `.mn` test per
   public API surface, plus three property-style tests for
   round-trip parse/format invariants.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Dt.1** | HIGH | **Core types in `stdlib/time/types.mn`.** `struct Date { year: Int, month: Int, day: Int }`. `struct Time { hour: Int, minute: Int, second: Int, nanos: Int }`. `struct DateTime { date: Date, time: Time, tz_offset_minutes: Int }`. `struct Duration { seconds: Int, nanos: Int }`. `enum Timezone { UTC, Local, FixedOffset(Int) }`. Validate at construction (month 1-12, day per-month with leap year). | 2h |
| **Dt.2** | HIGH | **Constructors in `stdlib/time/construct.mn`.** `Date::new(y,m,d) -> Result<Date, String>`, `Date::today() -> Date`, `DateTime::now() -> DateTime`, `DateTime::from_epoch(seconds: Int) -> DateTime`, `Duration::seconds`/`minutes`/`hours`/`days`. `now()` calls a runtime shim `__mn_clock_gettime_realtime` returning `(secs, nanos)` tuple. | 2h |
| **Dt.3** | HIGH | **Parsers in `stdlib/time/parse.mn`.** `Date::parse_iso("2026-05-03") -> Result<Date, String>`, `DateTime::parse_rfc3339("2026-05-03T14:32:00Z") -> Result<DateTime, String>`, `Duration::parse("PT1H30M") -> Result<Duration, String>` (ISO 8601 duration form). Tolerant of common variants (with/without `T`, `Z` vs `+00:00`). | 3h |
| **Dt.4** | HIGH | **Formatters in `stdlib/time/format.mn`.** `dt.format("%Y-%m-%d %H:%M:%S") -> String`. Support: `%Y %m %d %H %M %S %z %Z` for v5.34.0; full strftime subset for v5.34.1+. Default-format method on each type returns ISO/RFC form. | 2h |
| **Dt.5** | MEDIUM | **Arithmetic in `stdlib/time/arith.mn`.** Operator overloads: `DateTime + Duration -> DateTime`, `DateTime - DateTime -> Duration`, `Duration + Duration -> Duration`, `Duration * Int -> Duration`. Use `__mn_normalize_datetime` runtime helper for month/day rollover (it's annoying to do correctly in `.mn` and a 30-LOC C shim is faster than 200 LOC of `.mn`). | 3h |
| **Dt.6** | MEDIUM | **Timezone v0 in `stdlib/time/tz.mn`.** `Timezone::UTC` and `Timezone::Local` only. `Local` reads `TZ` env var or system default via `localtime_r`. Named-zone lookup (`"America/Lima"`, `"Europe/Madrid"`) returns `Err("named tzdb not yet supported")` — explicit defer, not silent failure. v5.34.1 adds tzdb integration (probably bundled IANA tzdb at install time). | 2h |
| **Dt.7** | HIGH (gate) | **Tests in `stdlib/time/tests/`.** `test_date.mn`, `test_datetime.mn`, `test_parse_iso.mn`, `test_format.mn`, `test_arithmetic.mn`. Plus property tests: parse-then-format is identity for ISO 8601 + RFC 3339; epoch round-trip preserves seconds; arithmetic is associative for `Duration + Duration`. | 3h |
| **Dt.8** | LOW | **Runtime C shim** in `runtime/native/mapanare_time.c`. Exports `__mn_clock_gettime_realtime`, `__mn_localtime_r`, `__mn_timegm`, `__mn_normalize_datetime`. Cross-platform: POSIX everywhere, Windows uses `GetSystemTimePreciseAsFileTime` + `localtime_s`. ~80 LOC. | 2h |
| **Dt.9** | LOW | **Doc page** at `docs/stdlib/time.md`. Examples + cookbook (parse-then-format, "1 week from now", "is this date in the past"). | 1h |

**Total source delta:** ~1500 LOC of `.mn` (types + parsers +
formatters + tests) + ~80 LOC of C runtime shim.

---

## Phase plan

- **Phase 0** — Pre-flight: v5.33.0 HEAD clean.
- **Phase 1** — Dt.8 C shim first. Compiler/runtime ground truth
  before `.mn` builds on it.
- **Phase 2** — Dt.1 + Dt.2 core types and constructors.
- **Phase 3** — Dt.3 parsers (the biggest single item; pin tests
  early).
- **Phase 4** — Dt.4 formatters.
- **Phase 5** — Dt.5 arithmetic + Dt.6 timezone v0.
- **Phase 6** — Dt.7 round out tests; Dt.9 docs.
- **Phase 7** — Bump + tag.

---

## Out of scope

- **Named tzdb (`"America/Lima"`).** v5.34.1 or v5.35.0. Requires
  bundling IANA tzdb (`/usr/share/zoneinfo` on Unix, ICU or zoneinfo
  port on Windows). Significant packaging work — separate release.
- **Calendars other than Gregorian.** Hijri, Hebrew, Buddhist, etc.
  — never going in stdlib core; downstream package territory.
- **Sub-nanosecond precision.** Not needed for v5.x apps.
- **Date64 / DateTime64 wide types.** Year ±9999 range is
  sufficient for v5.x.
- **Tn.1, M.1, A.1, Ra.New1, Pv.8.B** — carry forward.

---

## Risk

1. **Leap-year + month-length correctness.** The bug class that
   bites every date library author. Mitigation: Dt.7 property
   tests over the next 1000 years; explicit table-driven tests
   for known boundary cases (Feb 29, year 1900 not leap, year
   2000 leap, etc.).
2. **TZ offset sign confusion.** "+05:30" vs "-05:00" parsing,
   `tz_offset_minutes` direction (offset *from* UTC or *to* UTC?).
   Mitigation: pick "minutes east of UTC" (POSIX convention),
   document it explicitly, lock with parse-then-render tests for
   both signs.
3. **Windows `localtime_s` vs `localtime_r`.** Different signature.
   Mitigation: Dt.8 shim wraps the difference internally.
4. **`.mn` operator overload syntax.** Currently supported for
   `+`/`-` on user types via `impl Add for Type`. Confirm at
   Phase 0 that this works for `Duration + Duration` on the
   LLVM backend; if not, expose as `dur.add(other)` method
   instead (no syntax change, just less ergonomic).

---

## Success criteria

- ✅ `import time` works; `let now = DateTime::now()` returns
  current UTC datetime.
- ✅ `DateTime::parse_rfc3339("2026-05-03T14:32:00Z").unwrap()`
  round-trips through `.format(...)`.
- ✅ `now() + Duration::days(7)` returns a date 7 days hence
  with month-rollover handled.
- ✅ All Dt.7 tests pass on Linux + macOS + Windows.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- "no first-class date/time stdlib" gap.

**Inherits to v5.35.0:**
- Tn.1 (must ship at v5.35.0 or be the exclusive scope of an
  unscheduled hotfix; this is the deadline).
- Named tzdb support (Dt.6 deferred).
- macOS notarization (still LOW; carry).

**Aggregate state entering v5.35.0:** 0 HIGH / 2 MEDIUM (Tn.1
DEADLINE; macOS notarization) / ~6 LOW (added named-tzdb).
