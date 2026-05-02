# Mamba — C Runtime / Performance Review of Mapanare v5.28.0

**Reviewer:** Mamba
**Personality:** Brutal C minimalist. Counts allocations. Respects simplicity. "Delete this."
**Previous Version Reviewed:** v5.22.0 (9.85 / 10 EXCEEDS, +0.05)
**Score:** 9.80 / 10
**Grade:** EXCEEDS
**Delta vs v5.22.0:** −0.05
**Verdict:** PASS WITH NOTES
**Confidence:** 9 / 10
**Files Reviewed:** `runtime/native/mapanare_core.{c,h}`, `mapanare/self/parser.mn`,
`scripts/verify_fixed_point.sh`, `docs/roadmap/v5/v5.23.{1,2}/SESSION_REPORT.md`,
`docs/roadmap/v5/v5.25.0/SESSION_REPORT.md`, `docs/roadmap/v5/v5.26.0/SESSION_REPORT.md`,
`docs/roadmap/v5/v5.27.0/SESSION_REPORT.md`, `.reviews/CARRY_FORWARD.md`.

---

## Executive Summary

Six releases. **+306 lines of C.** That is the arc. Three commits touched
`runtime/native/`: v5.23.0 RC.10 (1 header prototype), v5.23.1 Mb.4/Mb.5
(walker depth-cap + symlink-skip, ~90 LOC), v5.23.2 Te.3.B.2
(~280 LOC — brace-deprecation mirror), and a between-release double-free
bugfix in `__mn_indent_to_braces` that landed at commit `9dcbbb5` between
v5.24.1 and v5.25.0. v5.24.0, v5.24.1, v5.25.0, v5.26.0, v5.26.1, v5.27.0
— **zero C** for six consecutive minor releases after v5.23.2. Correct.

**Pe.1 reframe verified.** My v5.22.0 request to retire the "curve flattening"
framing landed at v5.24.0 Hy.6. The actual trajectory: +3,756 lines over 5
releases = **+0.316%/release**. Well under the +0.5%/release projection I
stated. Growth is proportional to the Eu.\* lowerer/emitter arms (+1,849
lines v5.26.1 vs v5.26.0) — all bootstrap-side, none C-side. Reframe holds.

**One recurring finding: the .h vs .c header-asymmetry pattern.**
My v5.22.0 Mamba #1 found `__mn_indent_to_braces` missing from the header.
Closed at v5.23.0 RC.10. Then Te.3.B.2 added two new exports
(`__mn_count_user_brace_block_openers` + `__mn_emit_brace_deprecation_warning`)
without header declarations. The pattern recurred on the very release that
closed the last instance of itself. That is the one dock.

The C code shipped in this arc is otherwise clean. `__mn_count_user_brace_block_openers`
is a single malloc (O(source bytes)) + single free, no early-return paths
that leak. `__mn_emit_brace_deprecation_warning` is zero allocations —
`getenv` + `fputs`/`fprintf` only. Mb.4/Mb.5 are minimal and correct. The
`__mn_indent_to_braces` double-free fix (commit `9dcbbb5`) was a real fix:
the brace-only fast path was returning the input `MnString` aliased instead
of a fresh copy, producing a double-free when both source and result were
drop-tracked. Fix is correct — `__mn_str_from_parts` does one memcpy. Cost
is one extra `malloc`+`memcpy` per brace-only file; negligible.

---

## Score: 9.80 / 10

−0.05 from v5.22.0's 9.85: the .h vs .c asymmetry recurred at the exact
release that closed its prior instance. Pattern discipline costs the point.
Everything else on my axis is cleaner than v5.22.0.

---

## C Runtime Delta v5.22.0 → v5.28.0 (live-verified)

```
$ git diff 9a9c736..HEAD --stat runtime/native/
  runtime/native/mapanare_core.c | 341 ++++++++++++++++++++++++++++++++++++++---
  runtime/native/mapanare_core.h |   5 +
  2 files changed, 326 insertions(+), 20 deletions(-)
```

Net: `mapanare_core.c` 4196 → 4497 (+301 net). `mapanare_core.h` 776 → 781 (+5).
**Total +306 lines.**

**Commits that touched runtime/native/ since v5.22.0 (9a9c736):**

| Commit | Release | What changed |
|---|---|---|
| `9b91a68` | v5.23.0 RC.10 | +1 line header: `__mn_indent_to_braces` prototype (closes Mamba #1) |
| `3abe098` | v5.23.1 Mb.4/Mb.5 | `MN_DIR_WALK_MAX_DEPTH` (4096) depth-cap on 3 walkers + `FILE_ATTRIBUTE_REPARSE_POINT` skip + `stat()` → `lstat()` on POSIX count/size paths |
| `f595ec1` | v5.23.2 Te.3.B.2 | `__mn_count_user_brace_block_openers` (~150 LOC) + `__mn_emit_brace_deprecation_warning` (~25 LOC) |
| `9dcbbb5` | between v5.24.1 and v5.25.0 | `__mn_indent_to_braces` brace-only fast-path double-free fix: `return source` (alias) → `return __mn_str_from_parts(src, n_src)` (fresh copy) |

**v5.24.0 through v5.27.0: zero C runtime changes.** Confirmed by `git log`.

---

## Pe.1 Budget Verification

| Metric | v5.22.0 | v5.27.0 | Delta |
|---|---:|---:|---:|
| stage2.ll lines | 238,086 | 241,842 | +3,756 |
| Total growth | — | — | +1.58% |
| Per-release rate (5 releases) | — | — | **+0.316%/release** |

My v5.22.0 projection: "need another 30+ releases at +0.5%/release before
doubling." Actual rate is +0.316%/release — roughly 45+ releases before
doubling at this rate. **Reframe verified. Pe.1 LOW downgraded to INFO.**
Growth this arc is dominated by Eu.\* lowerer/emitter arms in v5.26.1
(+1,849 lines fixing 4 LINK_FAIL goldens) plus Te.3.B bootstrap wiring
(+350 lines v5.23.2). No C surface contributed to the IR line count.

---

## Progress Since Last Review (v5.22.0 → v5.28.0)

### v5.22.0 Mamba findings — status

| Finding | v5.22.0 status | v5.28.0 status |
|---|---|---|
| **#1 LOW** `__mn_indent_to_braces` not in `.h` | OPEN | **CLOSED v5.23.0 RC.10** — prototype at `mapanare_core.h:714`. But see NEW finding #1 below. |
| **#2 LOW** Pe.1 "curve flattening" framing | OPEN | **CLOSED v5.24.0 Hy.6** — reframed in `CARRY_FORWARD.md`; rate-based projection stated; verified live. |
| **#3 LOW** `__mn_indent_to_braces` O(line-count) allocs | informational | Still open (architecture unchanged). The new `__mn_count_user_brace_block_openers` is actually *better*: single malloc of O(byte-count) vs O(line-count) separate small mallocs. |

### v5.23.0 RC.\* (C impact)
1 line header change. Zero logic. RC.10 closed Mamba #1. Correct.

### v5.23.1 Mb.\* (C impact)
Mb.4 (`MN_DIR_WALK_MAX_DEPTH` 4096 cap) and Mb.5 (`REPARSE_POINT` skip +
`lstat`) land cleanly. I would have preferred an iterative work-queue over a
depth-cap for V.6 — O(n) stack is still O(n) stack, bounded at 4096 — but
4096 levels of real filesystem nesting is pathological territory and the
pragmatic call is right for a compiler tool. No new allocations on the hot
path.

### v5.23.2 Te.3.B.2 (C impact)
`__mn_count_user_brace_block_openers` and `__mn_emit_brace_deprecation_warning`
land in C for the same reason `__mn_indent_to_braces` did: bootstrap-lower
pathologies on complex string-walking in `.mn`. Correct call. The allocation
profile:

- **`__mn_count_user_brace_block_openers`:** single `malloc(source.len)` +
  single `free(masked)`. No early-return paths between malloc and free
  (verified: only `n <= 0` guard fires before malloc, and that returns 0
  without allocating). Leak-clean.
- **`__mn_emit_brace_deprecation_warning`:** zero allocations. `getenv` +
  `fputs` + `fprintf` to stderr. Exactly the right shape for a warning
  emitter.
- **Missing header declarations.** See Issues.

### `__mn_indent_to_braces` double-free fix (`9dcbbb5`)
The brace-only fast path returned the input `MnString` aliased. After the fix
it calls `__mn_str_from_parts` (one `malloc` + `memcpy`). Correct fix. The
v5.14.1 performance justification ("crucial for the 95% of corpus still
brace-style") was obsolete post-Sh.\*. The SESSION_REPORT acknowledges this
explicitly. One extra alloc per brace-only file parse; negligible.

### v5.24.0–v5.27.0 (zero C impact)
Six consecutive minor releases with zero C runtime changes. The right shape.
Eu.\*, Mc.\*, Tk.\* — all bootstrap and Python work. Mb.9 Win64 OOM was
zero C: the C side was always correct; the bug was the Python/self-host call
site disagreeing on byref threshold. Documented clearly.

### Bb.\* seed refresh discipline
One seed refresh in the arc: v5.23.2 Te.3.B.5. Required because the
v5.10.0-vintage seed predated the two new C-runtime exports. Zero refreshes
at v5.24.0–v5.27.0 — confirmed by `git log ... -- bootstrap/seed/`. Correct.
Eu.\* and Mc.\* added no new C-runtime exports; no refreshes needed.

---

## What is Preserved from v5.22.0

- **C runtime delta stays proportional to bootstrap-mirror additions.**
  Same pattern as v5.11.0 → v5.22.0 (only v5.14.1 and v5.13.1 touched C;
  8+ releases zero-touch). This arc: only v5.23.0/v5.23.1/v5.23.2 + one
  between-release fix; 6 releases zero-touch.
- **No malloc churn from any Eu.\* codegen fix.** All lowerer/emitter
  changes are Python+.mn only. Zero runtime allocator impact from
  Result/Option unwrap fixes, match cascade rewrites, or-pattern dedup.
- **No malloc churn from Mc.8/Mc.9/Tk.1 formatter.** Python only.
- **Stage2-binary teardown crash still papered over** — `set +e` at
  `verify_fixed_point.sh:124`. v6.0 carry. Status unchanged. Not a regression.

---

## Issues Found

### 1. **LOW** — New Te.3.B.2 exports missing from `mapanare_core.h` — Mamba #1 class recurred

`__mn_count_user_brace_block_openers` and `__mn_emit_brace_deprecation_warning`
are `MN_EXPORT`'d in `mapanare_core.c` (lines 4329, 4478) but have no
prototypes in `mapanare_core.h`. Verified live:

```
At v5.22.0: 16 exports in .c not in .h
At v5.28.0: 17 exports in .c not in .h
Net: RC.10 added __mn_indent_to_braces to header (-1),
     Te.3.B.2 added 2 new exports without header decls (+2).
```

The asymmetry count went from 16 to 17. The same class of finding I raised
at v5.22.0, closed at v5.23.0, then reopened at v5.23.2. Every time a
new C-runtime export ships, the header decl is skipped.

**Bound:** Mamba #1 (v5.22.0) — same finding, second instance.

**Fix (2 lines):**
```c
/* mapanare_core.h — add near the v5.23.2 Te.3.B region */
MN_EXPORT int64_t __mn_count_user_brace_block_openers(MnString source);
MN_EXPORT void __mn_emit_brace_deprecation_warning(MnString path, int64_t count);
```

**Structural fix (recommended for v5.28.x):** Add a `scripts/check_runtime_exports.py`
gate to `make ci-gates`. One script: diff `MN_EXPORT` function names in
`*.c` vs `*.h`; exit 1 on non-zero delta. Without this, the next C-runtime
export addition will produce Mamba #1 a third time.

---

### 2. **LOW (informational)** — `getenv("MAPANARE_NO_BRACE_WARNING")` not cached

`__mn_emit_brace_deprecation_warning` calls `getenv` on every invocation.
For a batch compiler (one call per file parse): acceptable. For an embedded
long-lived host calling `parse()` in a loop: O(parse-count) `getenv` calls
instead of O(1). `getenv` on Linux is fast but it is not free.

Not a bug. Noting it because the class matters for embedded use.

**Bound:** (none — fresh).

**Fix (if ever needed):** `static int cached = -1;` at function entry, set
on first call. Do not do this without a measured embed use case first.

---

### 3. **LOW (carry)** — Stage2-binary teardown crash (RC=3) still papered over

`verify_fixed_point.sh:124` sets `set +e`; lines 131 and 142 name the
teardown crash explicitly. Unchanged from v5.22.0. v6.0 carry.

**Bound:** Rattler #5 (v5.22.0) — carry-forward, status unchanged.

---

## Recommendations

1. **Add the two Te.3.B.2 header decls now.** Two lines. v5.28.x.
2. **Add `scripts/check_runtime_exports.py` to `make ci-gates`.** Closes
   the class structurally. Without it, the next new C export will
   produce Mamba #1 a third time.
3. **Everything else: leave it.** No new perf docket. No new alloc docket.

---

## Post-Production Health Assessment

28+ minor versions after v5.0.0, the C runtime is in the right shape.

- **6 of 8 arc releases: zero C.** The pattern I want to see.
- **Eu.\* LINK_FAIL closures: zero C.** All lowerer/emitter work. The
  codegen bugs that blocked 4 goldens for multiple releases were compiler
  logic, not runtime logic. Runtime was always correct.
- **Mb.9 Win64 OOM: zero C.** C side was always correct. The bug was the
  Python/self-host call site disagreeing on the byref threshold. Documented
  clearly in the SESSION_REPORT ("No C-runtime edits; the C side was always
  correct."). Good.
- **`__mn_indent_to_braces` double-free: real fix, right call.** The
  fast-path aliasing was a genuine safety issue. Adding a memcpy on the
  brace-only path is the right trade-off; the performance justification for
  the alias was obsolete.
- **Two new exports without header decls: pattern that needs a gate.** One
  instance is an oversight. Two consecutive panels on the same class is a
  systematic gap. The structural fix is one small script in `make ci-gates`.

On my axis: healthy, with the header caveat and the gate recommendation.

---

## Raw Notes

```
git diff 9a9c736..HEAD --stat runtime/native/
  mapanare_core.c: 301 net new lines
  mapanare_core.h: +5 lines
  Total: +306 lines

git log 9a9c736..HEAD --oneline -- runtime/native/
  9dcbbb5  Fix runtime lib detection and string alias bug
  f595ec1  Release v5.23.2: Te.3.B bootstrap brace-deprecation mirror
  3abe098  Release v5.23.1: memory hygiene fixes
  9b91a68  v5.23.0 RC.*: CI recovery + HIGH closures (15 items, mechanical)
  [4 commits; 6 named releases untouched]

Header/C export delta:
  v5.22.0: 16 exports in .c not in .h
  v5.28.0: 17 exports in .c not in .h
  RC.10 fixed __mn_indent_to_braces (-1), Te.3.B.2 added 2 without decls (+2)

__mn_count_user_brace_block_openers allocation profile:
  malloc: 1 (masked buffer, source.len bytes)
  free:   1 (at line 4474, before return count)
  early returns before malloc: 0 (n<=0 check fires before malloc; returns 0)
  Verdict: leak-clean.

__mn_emit_brace_deprecation_warning:
  malloc: 0
  getenv: 1 per call (not cached)
  output: fputs + fprintf to stderr
  Verdict: zero allocation. Correct shape for a warning emitter.

Pe.1 trajectory:
  v5.11.0 -> v5.22.0 (10 releases): +5.07%, +0.507%/release
  v5.22.0 -> v5.27.0  (5 releases): +1.58%, +0.316%/release
  Rate is slowing. Pe.1 reframe holds.

Bb.* seed refresh count in arc:
  1 (v5.23.2 Te.3.B.5 — required for new C exports)
  0 at v5.24.0, v5.24.1, v5.25.0, v5.26.0, v5.26.1, v5.27.0 ✓

Stage2 teardown: set +e at verify_fixed_point.sh:124. v6.0. Unchanged.

Score vs v5.22.0 (9.85):
  + Pe.1 reframe landed, verified:                     +0.05
  + __mn_indent_to_braces double-free fixed:           +0.05
  + Mb.4/Mb.5 walker bounds/symlink-skip clean:        +0.02
  + 6-of-8 releases zero C (correct pattern):          +0.03
  - Mamba #1 class recurred (2nd consecutive panel):   -0.15
  - getenv not cached (informational):                 -0.05
  Net: -0.05 → 9.80
```

— Mamba
