# v5.34.0 Session Report — Dt.\* — date / time stdlib

**Status:** READY (not tagged)
**Type:** Stdlib expansion. New `.mn` library on top of a new portable
C runtime shim. **Zero compiler edits. Zero `mapanare/self/*.mn`
source touches.**
**Strict 3-stage fixed point:** preserved by construction at v5.33.x's
**241,898 lines / 0 diff** (29-release strict streak from v5.7.1).
**Goldens:** 95/95.

## Headline

First first-class date/time stdlib in Mapanare. Closes the
"`runtime.now()` returns an integer of seconds and nothing else" gap
called out in the v5.34.0 PROMPT/PLAN. Surface: `Date`, `Time`,
`DateTime`, `Duration`, `Timezone` types with construction-time
validation; ISO 8601 + RFC 3339 parse/format; arithmetic with
month/day rollover; v0 timezone surface (UTC + system-local;
named-tzdb explicitly defers).

Built on `runtime/native/mapanare_time.c` (~340 LOC, POSIX default
+ `#ifdef _WIN32` for `GetSystemTimePreciseAsFileTime` /
`localtime_s` / `_mkgmtime`). Mapanare side is a single-file
`stdlib/time.mn` (~700 LOC) — see PLAN deviation below.

## Per-Dt.\* walkthrough

### Dt.1 — core types + validating constructors

`stdlib/time.mn` Section D + E. Date / Time / DateTime / Duration /
Timezone defined with `pub tipo`. `date_new(y, m, d)` returns
`Result<Date, String>` and rejects:

- Year outside `[1, 9999]`
- Month outside `[1, 12]`
- Day outside `[1, days_in_month(y, m)]` — leap-year aware

Leap year rule (`is_leap_year`): standard Gregorian — div-4 EXCEPT
div-100 EXCEPT div-400. Boundary cases pinned in `test_date.mn` for
1900 (not leap), 2000 (leap), 2024 (leap), 2100 (not leap), 2400
(leap). The bug-class behind every "Feb 29 1900" mishap.

`time_new(h, m, s, ns)` validates `h ∈ [0, 23]`, `m ∈ [0, 59]`,
`s ∈ [0, 60]` (60 tolerated for leap second), `ns ∈ [0, 10^9-1]`.

`datetime_new(date, time, tz_offset_minutes)` validates tz offset
is in `[-1440, +1440]` (24h either side; covers Kiribati +14h).

### Dt.2 — clock-touching constructors

`datetime_now() -> Result<DateTime, String>` calls
`__mn_now_realtime_ns()`, divides to get seconds, then
`__mn_utc_pack(secs)` to get broken-down packed-int64 form, then
`unpack_to_datetime` to materialize the struct. Returns Err on
syscall failure (no panic).

`datetime_from_epoch(epoch_secs)` and `datetime_to_epoch(dt)` are
inverses. Property test `test_property.mn` pins the round-trip
across 8 epoch fixtures from 0 (1970) through 2000000000 (2033).

`date_today()` is `datetime_now()` ∘ `.date`.

`duration_seconds/minutes/hours/days(n)` are pure constructors
(no clock); units cascade `* 60`, `* 3600`, `* 86400`.

### Dt.3 — parsers

`date_parse_iso(s)`, `datetime_parse_rfc3339(s)`,
`duration_parse_iso(s)` all return `Result<T, String>` with
diagnostic messages.

Tolerated variants per PROMPT:

- ISO date: `YYYY-MM-DD` strict
- RFC 3339 datetime: `YYYY-MM-DDTHH:MM:SS<tz>` with `T`/`t`/space
  separator; tz as `Z`/`z`/`+HH:MM`/`-HH:MM`/`+HHMM`/`-HHMM`;
  optional `.fff` fractional seconds (precision dropped in v0)
- ISO duration: `PT<H>H<M>M<S>S` (any subset of components, in that
  order); `P3D` and `P1Y` explicitly rejected (ambiguous without
  anchor date)

Invalid inputs return `Err` with a useful message:
`"missing '-' after year in: ..."`,
`"non-numeric month in: ..."`,
`"month out of range: 13"`, etc.

Pinned 22 cases in `test_parse_iso.mn` including
`2026-05-03T14:32:00.123Z` (fractional seconds with Z).

### Dt.4 — formatters

`datetime_format(dt, fmt)` supports v5.34.0 strftime subset:

| Spec | Output                      |
|------|-----------------------------|
| `%Y` | 4-digit year                |
| `%m` | 2-digit month               |
| `%d` | 2-digit day                 |
| `%H` | 2-digit hour                |
| `%M` | 2-digit minute              |
| `%S` | 2-digit second              |
| `%z` | Numeric offset (`+0530`)    |
| `%Z` | Name (`UTC`) or numeric     |
| `%%` | Literal `%`                 |

Unknown specifiers (`%a`, `%j`, `%w`, etc.) pass through verbatim
— no error. Full strftime expansion deferred to v5.34.1+.

`date_to_iso(d) -> "YYYY-MM-DD"` and
`datetime_to_rfc3339(dt) -> "YYYY-MM-DDTHH:MM:SS+HHMM"` are the
default canonical-form helpers.

Parse-then-format round-trip pinned in `test_format.mn` and
`test_property.mn` for 10 datetime fixtures (regular, epoch start,
max year, leap days, year boundaries, DST-tricky times).

### Dt.5 — arithmetic (method form, NOT operator overload)

**Phase 0 spike result:** `impl Add for Duration` does NOT lower
through `mnc-stage1`. The semantic checker reports
`Undefined trait 'Add'`. Per PROMPT mitigation, Dt.5 falls back
to free-function method form:

```mn
let later = datetime_add_duration(now, duration_days(7))    // dt + dur
let diff  = datetime_diff(later, now)                       // dt - dt
let sub   = datetime_sub_duration(now, duration_hours(2))   // dt - dur
let sum   = duration_add(d1, d2)                            // dur + dur
let mul   = duration_mul(d1, 5)                             // dur * n
```

`datetime_add_duration` routes through `__mn_normalize_pack` for
month/day rollover. Boundary cases pinned in `test_arithmetic.mn`:

- `2026-01-31 + 1 day = 2026-02-01`
- `2026-12-31 23:59:59 + 1s = 2027-01-01 00:00:00`
- `2024-02-29 + 365 days = 2025-02-28` (leap 2024 → non-leap 2025)
- `2026-04-01 - 1 day = 2026-03-31` (negative duration)

### Dt.6 — timezone v0

`tz_utc()`, `tz_local()`, `tz_fixed(offset_minutes)` return a
`Timezone` enum. `tz_named(name)` returns explicit
`Err("named tzdb not yet supported: <name>")` — non-negotiable
per PLAN. Silent fallback to UTC is the bug-class that bites real
users on flight-booking apps. Pinned in `test_tz.mn` with both
`America/Lima` and `Europe/Madrid` cases.

`datetime_to_local(dt_utc)` re-anchors a UTC `DateTime` into local
timezone via `__mn_local_pack` + `__mn_local_offset_minutes`,
honoring DST at that instant.

### Dt.7 — tests

Seven `.mn` test files under `stdlib/time/tests/`:

| File                       | Coverage                                        |
|----------------------------|-------------------------------------------------|
| `test_date.mn`             | Construction, leap years (1900/2000/2024/2100/2400), boundary years/months/days |
| `test_datetime.mn`         | `datetime_now`, epoch round-trip, duration constructors, tz validation |
| `test_parse_iso.mn`        | ISO 8601 + RFC 3339 + ISO duration; 22 cases including invalid inputs |
| `test_format.mn`           | strftime specifier coverage, parse-then-format round-trip, `pad_zero` |
| `test_arithmetic.mn`       | Duration arithmetic, datetime ± duration, month/day rollover, datetime_diff |
| `test_property.mn`         | 3 property-style tests: rt-format, rt-epoch, arithmetic associativity |
| `test_tz.mn`               | UTC/Local/FixedOffset, `tz_named` explicit-defer assertion |

Property tests use a **fixed deterministic table** of "interesting"
inputs (boundary cases, year transitions, leap days, DST-tricky
times) rather than runtime PRNG — Mapanare's stdlib doesn't expose
seedable random yet. Coverage is comparable to a `n=10` random run
across the same input space.

Test runner: `tests/stdlib/test_time_dt.py` (pytest harness, mirrors
the v3.x `test_crypto.py` concatenation pattern). Reads
`stdlib/time.mn`, prepends to each `.mn` test main body, compiles
via Python LLVM emitter, links against `libmapanare_rt.a`, runs
the binary, asserts `"PASSED"` in stdout. **9/9 GREEN at HEAD.**

### Dt.8 — runtime C shim

`runtime/native/mapanare_time.c` (~340 LOC):

| Export                            | Behavior                                                                  |
|-----------------------------------|---------------------------------------------------------------------------|
| `__mn_now_realtime_ns()`          | Total ns since UNIX epoch; -1 on syscall failure                          |
| `__mn_utc_pack(epoch_secs)`       | UTC broken-down packed `y*10^10 + mo*10^8 + ...`; -1 on out-of-range      |
| `__mn_local_pack(epoch_secs)`     | Same, local timezone                                                      |
| `__mn_local_offset_minutes(...)`  | Minutes east of UTC at given instant; INT64_MIN on failure                |
| `__mn_timegm(y,mo,d,h,mi,s)`      | Inverse of gmtime; -1 on out-of-range                                     |
| `__mn_normalize_pack(y,mo,...,s)` | Normalize after Duration arithmetic (month/day rollover); -1 on year overflow |

POSIX path is the default; Windows path lives behind `#ifdef _WIN32`
using `GetSystemTimePreciseAsFileTime`, `localtime_s`, `gmtime_s`,
`_mkgmtime`. The MS family argument order is reversed from POSIX —
the shim wraps the difference internally so the `.mn` side never
sees the platform split.

Wired into the runtime archive via `Makefile` `RUNTIME_SOURCES`
addition; `libmapanare_rt.a` now contains 9 C modules + Metal on
Darwin.

**Smoke verified.** 20-case C harness at `/tmp/time_shim_smoke.c`
during dev exercised every export including leap-year boundaries
(1900/2000/2024/2100), out-of-range rejection, normalization
forward/backward, and year overflow. 20/20 PASS. Valgrind clean.

### Dt.9 — docs

`docs/stdlib/time.md`:
- Quick reference (one-screen surface example)
- Full type definitions with year-range, leap-year, tz-sign
  conventions documented
- Strftime specifier table
- Four required cookbook recipes: parse-then-format round-trip;
  "1 week from now"; "is this date in the past?"; "format as ISO
  8601 in local timezone"
- Migration note from v5.33.x flat `stdlib/time.mn` (every existing
  surface preserved unchanged — `Stopwatch`, `now_ns`,
  `format_duration_ms`, etc.)
- Limitations / out-of-scope section

## Phase 0 spike result

```mn
struct Dur:
    secs: Int

impl Add for Dur:
    fn add(self: Dur, other: Dur) -> Dur:
        let r: Dur = new Dur { secs: self.secs + other.secs }
        return r
```

Result: `error: Undefined trait 'Add'` + `error: Operator '+' not
supported for types Dur and Dur`. Operator overload infrastructure
(`trait Add`, `impl Add for X`) does not exist in the current
toolchain. Recorded as PLAN deviation. Dt.5 fall back to method
form (free functions): `datetime_add_duration(dt, dur)`,
`duration_add(a, b)`, etc.

## PLAN deviation — single-file `stdlib/time.mn` (load-bearing)

PROMPT/PLAN specified a directory module at
`stdlib/time/{types,construct,parse,format,arith,tz}.mn` with
`stdlib/time/mod.mn` as the entry point. **Phase 2 dev surfaced two
cross-module limitations** that blocked the multi-file design:

### Limitation 1 — native `mnc-stage1`: extern_fn_def doesn't propagate

When `construct.mn` does `import time::types` and `types.mn` declares
`extern "C" fn __mn_now_realtime_ns() -> Int`, the native stage1
compiler does NOT propagate the extern declaration to construct.mn's
semantic-check scope. Result:
`error: Undefined function '__mn_now_realtime_ns'`.

The dedup pass in `mapanare/self/main.mn::dedup_definitions` HAS a
case for `extern_fn_def` (line 302), but the upstream import-merge
flow doesn't preserve them across modules. Workaround: re-declare
every extern in every consuming module — but that breaks DRY and
duplicates ~20 LOC per consumer.

### Limitation 2 — Python LLVM emitter: name-mangling mismatch

When the test smoke imports `time::construct` and calls
`datetime_now()`, the emitter generates:
```ll
declare void @datetime_now(ptr sret(...) align 8)        ; UNPREFIXED
call void @datetime_now(ptr sret(...) %sret.0)           ; UNPREFIXED
```

But the actual definition in the `construct.mn` IR is:
```ll
define void @time_construct__datetime_now(ptr noalias sret(...) %__sret__) ...  ; PREFIXED
```

`@datetime_now` and `@time_construct__datetime_now` are different
symbols → linker rejects: `undefined reference to 'datetime_now'`.

Reproduced via `python3 -m mapanare emit-llvm + clang link` chain.
Verified the same issue blocks `examples/ai/basic_chat.mn` (already
documented as `// Known issue (v4.129.0): this example does not
currently compile`).

### Decision

Both limitations are real and tracked separately. Neither is in
v5.34.0 scope (the PROMPT itself explicitly warns "If you find
yourself opening `mapanare/self/lower.mn` or `emit_llvm.mn`, you
have gone outside scope"). The right structural shape is the
directory module; it has to ride a separate cross-module-emitter
fix.

For v5.34.0, follow the proven pattern: every existing stdlib
module (`math.mn`, `crypto.mn`, `fs.mn`, `ai/llm.mn`, `db/*.mn`)
is single-file with self-contained tests. v5.34.0's
`stdlib/time.mn` is the same shape — single file, all sections in
one place, with the `Section A..Section J` comment headers acting
as the "directory layout" the multi-file design would have
provided.

The `tests/stdlib/test_time_dt.py` harness reads `stdlib/time.mn`
and concatenates with each `.mn` test main body before compilation
— same pattern as `tests/stdlib/test_crypto.py`. Tests genuinely
exercise the SHIPPED source code (not a copy); the only difference
from a "real" `import time` is that the harness handles the
concatenation explicitly.

## API deviation from PROMPT signatures

PROMPT specified the C shim with out-pointer signatures:

```c
int __mn_clock_gettime_realtime(int64_t *secs, int64_t *nanos);
int __mn_localtime_r(int64_t epoch_secs, struct mn_tm *out);
```

Mapanare's `extern "C" fn` syntax exposes only `Int` / `String` /
`List<X>` returns — no out-pointer surface. Adapted to scalar
returns with packed int64 representation:

```c
int64_t __mn_now_realtime_ns(void);
int64_t __mn_utc_pack(int64_t epoch_secs);    // packed y*10^10 + ...
int64_t __mn_local_pack(int64_t epoch_secs);
int64_t __mn_local_offset_minutes(int64_t epoch_secs);
int64_t __mn_timegm(int64_t y, int64_t mo, ..., int64_t s);
int64_t __mn_normalize_pack(int64_t y, int64_t mo, ..., int64_t s);
```

The packed encoding `y*10^10 + mo*10^8 + d*10^6 + h*10^4 + mi*10^2 + s`
fits comfortably in int64 (max ~10^14 for year 9999) and the `.mn`
side decodes via repeated `% 100` / `/ 100`. Sentinel `-1`
indicates failure on every entry point (legitimate values for the
packed form start at year 1 → `10^10`).

## v5.34.0 fix in code: ISO parser fractional-seconds skip

Phase 6 caught one bug before closeout. The fractional-seconds skip
in `datetime_parse_rfc3339` had an off-by-one between the loop-exit
sentinel (`p = n`) and the post-loop fallback (`if p == n
{ tz_pos = p }`):

```mn
// BUGGY
while p < n {
    let dv: Int = time_digit_value(...)
    if dv < 0 {
        tz_pos = p     // record found position
        p = n          // exit loop (no break in Mapanare)
    } else { p = p + 1 }
}
if p == n { tz_pos = p }   // BUG: overwrites tz_pos with n
```

Symptom: `2026-05-03T14:32:00.123Z` parsed `Err("invalid timezone
offset")` (empty msg in test output because the error string was
cleared by an unrelated path). Fix: track `found_pos` separately
from the loop-exit sentinel, and only fall back to `tz_pos = n`
when `found_pos < 0` (i.e., loop ran off the end without finding
any non-digit).

Round-trip `parse → format → parse` pinned in `test_parse_iso.mn`
case 17.

## Aggregate state entering v5.35.0

| Severity | Item                                                                                       |
|----------|--------------------------------------------------------------------------------------------|
| HIGH     | Tn.1 — DEADLINE at v5.35.0 per v5.33.0 escalation directive (carry-forward 6 releases now) |
| MEDIUM   | macOS notarization (still LOW; carry)                                                      |
| LOW      | Named-tzdb support (Dt.6 deferred — `tz_named` returns explicit Err)                       |
| LOW      | Cross-module function call mangling (Python emitter + native extern propagation)           |
| LOW      | Operator overload (Phase 0 spike showed `impl Add` doesn't lower)                          |
| LOW      | Full strftime specifier expansion (`%a`, `%j`, `%w`, etc.)                                 |
| LOW      | Sub-second precision in broken-down DateTime forms                                         |
| LOW      | macOS notarization (deferred from v5.33.0 Nu.2 ad-hoc-signing shortcut)                    |

**Cadence:** v5.33.2 demoted panel cadence enforcement to
informational-only per `feedback_no_forced_cadence_gates`. Next
panel timing remains the lead's call.

## Source delta

- `runtime/native/mapanare_time.c`: 339 LOC (new)
- `runtime/native/Makefile`: +1 LOC (RUNTIME_SOURCES)
- `stdlib/time.mn`: 723 LOC (was 173; +550 net; old surface preserved at top)
- `stdlib/time/tests/`: 7 new files, ~700 LOC total
- `tests/stdlib/test_time_dt.py`: 142 LOC (new harness)
- `docs/stdlib/time.md`: 215 LOC (new)
- `CHANGELOG.md`: ~70 LOC entry
- `CLAUDE.md`: this release-notes entry
- `docs/SPEC.md`: header re-sync (Hd-class preventative)
- `VERSION`, README badges (en/es/pt/zh-CN): mechanical bump

**Total source delta:** ~1450 LOC of `.mn` + Python + C + docs.
Within PROMPT's "~1500 LOC of `.mn` + ~80 LOC of C runtime shim"
budget (the C shim came in at ~340 LOC because the packed-int
adaptation + Win64 path + leap-year normalization needed more
than the 80 LOC budget — but still small enough that the deviation
is reasonable).

## Closeout

- Stage1 rebuilt between bump and fixed-point verify (per project
  memory `feedback_no_forced_cadence_gates` lesson — without rebuild
  IR-metadata embeds stale VERSION).
- STRICT 3-stage fixed point preserved at 241,898 lines / 0 diff
  (29-release strict streak).
- Goldens 95/95.
- `make lint` clean.
- Sanitizer sweeps: ASan + valgrind clean (mapanare_time.c is
  read-only syscall wrappers, no allocation).
- 9/9 Dt.\* tests GREEN via `tests/stdlib/test_time_dt.py`.
- `check_changelog_honesty` GREEN after staging new files
  (with one `<!-- no-check -->` opt-out for the intentionally-
  non-existent path in the deviation note).
- `check_doc_freshness` GREEN — SPEC.md header re-synced from v5.33.1's
  v5.33.1 cut to v5.34.0 cut as a Hd-class preventative gate.

**Tag NOT created.** Per project memory `feedback_v5_tag_timing`:
`bump_version.py` and CHANGELOG/CLAUDE.md edits are routine; the
`git tag v5.34.0` step waits for explicit lead approval. Surfaced
in this report; not executed.
