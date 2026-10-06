# `stdlib/time` — Date / Time / DateTime / Duration / Timezone

**Available since:** v5.34.0 (Dt.\*)
**Status:** stable surface; Dt.\* deferred items tracked below.

First-class date/time stdlib with ISO 8601 + RFC 3339 parse/format,
arithmetic with month/day rollover, and a v0 timezone surface. Built
on a portable C shim at `runtime/native/mapanare_time.c` so the
Mapanare side never sees the platform split.

> **Compiler limitation note (v5.34.0).** Cross-module function calls
> have a known limitation in the current Mapanare LLVM toolchain — the
> Python emitter mangles defined names with the module prefix
> (`time__date_new`) but emits unprefixed forward declarations at call
> sites, producing link failures. The native `mnc-stage1` separately
> does not propagate `extern_fn_def` declarations across module
> imports. Until the cross-module emitter fix lands (tracked
> separately), pretest by reading `stdlib/time.mn` directly into your
> own test file alongside your `fn main()` — the same pattern every
> stdlib module uses today (see `tests/stdlib/test_crypto.py` and
> `tests/stdlib/test_time_dt.py` for the harness shape). The
> `import time` syntax will start working once the underlying
> emitter fix lands; the surface API will not change.

## Quick reference

```mn
// Validating constructors — Result<T, String>
let d_r:  Result<Date,     String> = date_new(2026, 5, 3)
let t_r:  Result<Time,     String> = time_new(14, 32, 0, 0)
let dt_r: Result<DateTime, String> = datetime_new(d, t, 0)

// Clock entry points (UTC)
let now_r:   Result<DateTime, String> = datetime_now()
let today_r: Result<Date,     String> = date_today()
let from_r:  Result<DateTime, String> = datetime_from_epoch(1700000000)

// Duration constructors
let d1: Duration = duration_seconds(42)
let d2: Duration = duration_minutes(30)
let d3: Duration = duration_hours(1)
let d4: Duration = duration_days(7)

// Arithmetic (method form — operator overloads not yet supported)
let later_r: Result<DateTime, String> = datetime_add_duration(now, duration_days(7))
let diff_r:  Result<Duration, String> = datetime_diff(later, earlier)
let sum:     Duration                 = duration_add(d1, d2)
let scaled:  Duration                 = duration_mul(d3, 5)

// Parse / format
let parsed_r: Result<DateTime, String> = datetime_parse_rfc3339("2026-05-03T14:32:00Z")
let s:        String                   = datetime_to_rfc3339(parsed)
let fmt:      String                   = datetime_format(dt, "%Y-%m-%d %H:%M:%S %z")

// Timezones (v0 surface — UTC + Local only)
let utc:    Timezone                   = tz_utc()
let local:  Timezone                   = tz_local()
let fixed:  Timezone                   = tz_fixed(330)
let named_r: Result<Timezone, String>  = tz_named("America/Lima")  // returns Err
```

## Types

```mn
pub tipo Date {
    year: Int,    // 1..9999
    month: Int,   // 1..12
    day: Int      // 1..days_in_month(year, month)
}

pub tipo Time {
    hour: Int,    // 0..23
    minute: Int,  // 0..59
    second: Int,  // 0..60  (60 tolerated for leap second)
    nanos: Int    // 0..999999999
}

pub tipo DateTime {
    date: Date,
    time: Time,
    tz_offset_minutes: Int  // minutes EAST of UTC, POSIX convention
                            // +05:30 IST = +330; -05:00 EST = -300; UTC = 0
}

pub tipo Duration {
    seconds: Int,
    nanos: Int
}

pub tipo Timezone {
    | UTC
    | Local
    | FixedOffset(Int)
}
```

### Year range

`[1, 9999]`. Year 0, negative years, and years above 9999 are rejected
at construction with `Err("year out of range: <n>")`. This is enough
for v5.x apps; wider ranges (Date64 / extended Gregorian) are out of
scope.

### Leap-year rule

Standard Gregorian: divisible by 4, EXCEPT divisible by 100, EXCEPT
divisible by 400. Pinned in `stdlib/time/tests/test_date.mn` for
1900 (NOT leap), 2000 (leap), 2024 (leap), 2100 (NOT leap), 2400
(leap). The bug-class behind every "Feb 29 1900" mishap.

### Timezone offset sign

**Minutes EAST of UTC** (POSIX convention).

| Zone        | Offset    | `tz_offset_minutes` |
|-------------|-----------|---------------------|
| UTC         | +00:00    | 0                   |
| IST (India) | +05:30    | +330                |
| EST (US)    | -05:00    | -300                |
| Kiribati    | +14:00    | +840                |

The sign matches the human-readable form: `+05:30` is `+330`, not
`-330`. Confusing this is the bug-class behind off-by-an-hour issues
in international apps.

## Strftime specifiers (v5.34.0)

| Spec | Meaning                              | Example      |
|------|--------------------------------------|--------------|
| `%Y` | 4-digit year                         | `2026`       |
| `%m` | 2-digit month                        | `05`         |
| `%d` | 2-digit day                          | `03`         |
| `%H` | 2-digit hour (24h)                   | `14`         |
| `%M` | 2-digit minute                       | `32`         |
| `%S` | 2-digit second                       | `07`         |
| `%z` | Numeric tz offset (`+HHMM`)          | `+0530`      |
| `%Z` | Tz name (`UTC`) or numeric fallback  | `UTC`        |
| `%%` | Literal `%`                          | `%`          |

Unknown specifiers (`%a`, `%j`, `%w`, etc.) pass through verbatim
in v5.34.0; full strftime expansion deferred to v5.34.1+.

`%z` is numeric (`+0530`); `%Z` is the name (`UTC`). Mixing them is
the "why does my log line have two timezones?" bug-class.

## Cookbook

### Parse-then-format round-trip

```mn
let r: Result<DateTime, String> = datetime_parse_rfc3339("2026-05-03T14:32:00Z")
match r {
    Ok(dt) => {
        print(datetime_to_rfc3339(dt))
        // -> "2026-05-03T14:32:00+0000"
    },
    Err(msg) => print("parse failed: " + msg)
}
```

The default RFC 3339 form uses `+0000` rather than `Z` for the UTC
offset (matches `%z`). To emit `Z`, format with a custom string and
substitute, or use `%Y-%m-%dT%H:%M:%SZ` directly when you know the
datetime is UTC.

### "1 week from now"

```mn
let now_r: Result<DateTime, String> = datetime_now()
match now_r {
    Ok(now) => {
        let later_r: Result<DateTime, String> = datetime_add_duration(now, duration_days(7))
        match later_r {
            Ok(later) => print(datetime_to_rfc3339(later)),
            Err(msg)  => print("overflow: " + msg)
        }
    },
    Err(msg) => print("clock failed: " + msg)
}
```

### "Is this date in the past?"

```mn
fn is_in_past(when: DateTime) -> Result<Bool, String> {
    let now_r: Result<DateTime, String> = datetime_now()
    match now_r {
        Ok(now) => {
            let when_secs_r: Result<Int, String> = datetime_to_epoch(when)
            let now_secs_r:  Result<Int, String> = datetime_to_epoch(now)
            match when_secs_r {
                Ok(when_secs) => {
                    match now_secs_r {
                        Ok(now_secs) => return Ok(when_secs < now_secs),
                        Err(msg)     => return Err(msg)
                    }
                },
                Err(msg) => return Err(msg)
            }
        },
        Err(msg) => return Err(msg)
    }
    return Err("unreachable")
}
```

### "Format as ISO 8601 in local timezone"

```mn
let utc_r: Result<DateTime, String> = datetime_now()
match utc_r {
    Ok(utc) => {
        let local_r: Result<DateTime, String> = datetime_to_local(utc)
        match local_r {
            Ok(local) => print(datetime_to_rfc3339(local)),
            Err(msg)  => print("tz lookup failed: " + msg)
        }
    },
    Err(msg) => print("clock failed: " + msg)
}
```

`datetime_to_local` honors DST at the given instant. The `tz_offset_minutes`
field on the returned `DateTime` carries the offset that was in effect
at that moment (which differs across the year for DST-observing zones).

## Migration from the v5.33.x flat `stdlib/time.mn`

The v5.33.x flat file contained only monotonic clock helpers
(`now_ns`, `delay_ms`), a `Stopwatch` state machine, and unit
conversion (`ns_to_ms`, `format_duration_ms`). v5.34.0 preserves
ALL of that surface unchanged at the top of the new
`stdlib/time.mn`. Existing code that uses `Stopwatch`,
`format_duration_ms`, etc. continues to work without source edits.

## Limitations / out of scope

- **Named tzdb (`"America/Lima"`).** `tz_named(name)` returns
  explicit `Err("named tzdb not yet supported: <name>")` — silent
  fallback to UTC is the bug-class that bites real users. Bundled
  IANA tzdb is deferred to v5.34.1+.
- **Calendars other than Gregorian.** Hijri / Hebrew / Buddhist —
  downstream-package territory.
- **Sub-nanosecond precision.** Not needed for v5.x apps.
- **Date64.** Year ±9999 is sufficient.
- **Operator overload (`dt + dur`).** v5.34.0 Phase 0 spike
  confirmed `impl Add for Duration` does not lower in the current
  toolchain. Use `datetime_add_duration(dt, dur)` (method form)
  until the trait/operator infrastructure lands.

## Reference

- Source: [`stdlib/time.mn`](../../stdlib/time.mn)
- C shim: [`runtime/native/mapanare_time.c`](../../runtime/native/mapanare_time.c)
- Tests: [`stdlib/time/tests/`](../../stdlib/time/tests/)
- Test harness: [`tests/stdlib/test_time_dt.py`](../../tests/stdlib/test_time_dt.py)
- Release notes: [`docs/roadmap/v5/v5.34.0/SESSION_REPORT.md`](../roadmap/v5/v5.34.0/SESSION_REPORT.md)
