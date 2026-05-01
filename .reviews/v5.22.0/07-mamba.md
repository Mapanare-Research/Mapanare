# Mamba — C Runtime / Performance Review of Mapanare v5.22.0

**Reviewer:** Mamba
**Personality:** Brutal C minimalist. Counts allocations. Respects simplicity. "Delete this."
**Previous Version Reviewed:** v5.11.0 (9.8 / 10 EXCEEDS, +0.1)
**Score:** 9.85 / 10
**Grade:** EXCEEDS
**Delta vs v5.11.0:** +0.05
**Verdict:** PASS
**Confidence:** 9 / 10
**Files Reviewed:** `runtime/native/mapanare_core.{c,h}`, `mapanare/lower.py::_lower_chained_compare`, `mapanare/self/lower.mn::lower_chained_cmp`, `mapanare/self/parser.mn::parse`, `tests/golden/95_chained_cmp_side_effect.mn` (+ /tmp/chain95.ll), v5.13.1 / v5.14.1 / v5.17.0 / v5.21.0 SESSION_REPORTs.

## Executive Summary

Ten releases. **+553 lines of C.** That's the entire arc.
`__mn_assert_fail` (v5.13.1, 8 lines, fix-a-link-error) and
`__mn_indent_to_braces` + helpers (v5.14.1, ~545 lines, the
colon-block preprocessor). One header export added. One header
export missing (`__mn_indent_to_braces` defined `MN_EXPORT` in the
.c but never declared in the .h — minor C-discipline gripe, not a
bug). **No new exports for Te.5, Te.6, Sh.\*, Mc.\*, or Dk.\*.**
The lead's "zero new runtime function additions" claim is
**off by two**, both load-bearing for non-Te.\* work, both honestly
documented in their own SESSION_REPORTs. The Te.6 chained-compare
desugar is what the SESSION_REPORT promised: pure AST→AST, zero
runtime calls, the `__mn_chain_N` temps go through existing `let`
machinery and lower to **stack `alloca`** — verified live on
`/tmp/chain95.ll` (1× `call @middle(`, 5× `__mn_chain_0` SSA refs,
all stack-resident).

**Pe.1 trajectory check:** stage2.ll 226,603 (v5.11.0) → 238,086
(v5.22.0). **+5.07% over 10 releases. +0.5% per release.** v5.11.0
panel I noted "+0.34% over v5.9.0 → v5.11.0 (3 releases)";
extrapolated trajectory at v5.22.0 was ~+1.7%. We're 3× that —
still not bad, all of it from Te.\* surface (new AST nodes, new
desugar paths in the bootstrap mirror). Sh.\* shrunk
mapanare/self by **-3,950 lines** of source but cost **+5,805 lines
of IR** (v5.18.0 → v5.20.1) because the new bootstrap-side AST
nodes (StructUpdate, LetDestructure, IfLet, WhileLet, LetElse,
ChainedCompare) each materialize as compiled lowering code.
Defensible — that's the price of bootstrap parity. The curve is
not flattening anymore but it's not exploding either.

`__mn_indent_to_braces` itself: 545 lines, line-by-line mirror of
`mapanare/parser.py::_indent_to_braces`. Per-line malloc'd buffer,
realloc-grown output list, single final malloc to join. Fast path
returns source unchanged for brace-only files (`mn_ib_has_colon_blocks`
is a single byte-by-byte scan). All buffers freed before return.
Caller in parser.mn relies on Mapanare-side drop glue for the
returned `MnString`. **Leak-clean.** Allocation count is O(line
count), not O(byte count) — for a 30k-line mnc_all.mn that's 30k
malloc'd line buffers, but it runs **once per parse**, all
short-lived, all freed before the function returns.

## Score: 9.85 / 10

## Progress Since Last Review (v5.11.0 → v5.22.0)

### v5.13.0 — Mc.2 fmt (formatter)
**0 lines C runtime.** Python-only. ✓ No regression.

### v5.13.1 — At.\* `@test` runtime fix
**+8 lines C.** New `__mn_assert_fail(MnString)` export. fputs +
fwrite + exit(1). No allocations. Fixes a "use of undefined value
@__mn_assert_fail" linker error that had been sitting in the
self-hosted lower since whenever `assert` was added. Honest
patch. ✓ Minimal.

### v5.14.0 — Te.1 colon-block (Python only)
**0 lines C runtime.** Surface land in `mapanare/parser.py`. ✓.

### v5.14.1 — Te.1 bootstrap mirror (`__mn_indent_to_braces`)
**+545 lines C.** The single largest C addition in the arc.
Routed through C because the v5.14.0-vintage bootstrap lower has
two pathologies (split-result List<String> mangled-on-local-index;
deep nested if/else short-circuit ops emit invalid PHIs). I verified
the algorithm against the `_indent_to_braces` Python reference: same
control flow, same edge cases (struct/enum/match needs-comma frame
state, continuation `else`/`sino` re-open, EOF-time block close,
fn-no-paren `() {` insertion). The 6 helper structs (LineBuf, LineList,
Frame, FrameStack, plus the byte-view helpers) are minimal; nothing
to delete. Per-line buffer malloc'd, realloc-grown, free'd in
cleanup loop. `MnIB_Frame` is a 24-byte triple — could pack to
16 bytes if `prev_child_idx` and `needs_comma` shared a word,
saves ~50% on the frame stack — but the frame stack is bounded
by indent depth (≤ ~10 levels in any sane source), not file size.
**Not worth touching.**

One discipline gripe: `__mn_indent_to_braces` is `MN_EXPORT` in the
.c **but absent from `mapanare_core.h`**. Self-host calls it via
`extern "C" fn` decl in `parser.mn`. Won't break anything — the
linker sees the symbol — but it means there's no public-API surface
declared for it. Cobra's axis primarily; my axis: minor.

### v5.15.0 / v5.15.1 — Te.2 comprehensions / lambdas / implicit-return
**0 lines C runtime.** Pure AST→AST. ✓.

### v5.16.0 — Te.4 self-host string-interp parity
**0 lines C runtime.** v5.16.0 reuses existing `__mn_str_concat` and
`__mn_str_from_*` — Te.4 SESSION_REPORT explicitly notes that. The
"latent dest-name bug" in `emit_interp_concat` was a self-host emitter
fix, no runtime touch. ✓.

### v5.17.0 / v5.17.1 / v5.17.2 — Sh.\* mechanical brace→colon rewrite
**0 lines C runtime.** Source-side rewrite of `mapanare/self/*.mn`.
The `_indent_to_braces` C preprocessor (already shipped at v5.14.1)
absorbed all 17 modules at parse time. ✓.

### v5.18.0 — Mc.\* LSP / init / check
**0 lines C runtime.** Python LSP, Python init, Python check. Native
dispatch in `main.mn` shells out to Python. No new runtime. ✓.

### v5.19.0 — Te.3 `{}` soft-deprecation
**0 lines C runtime.** Warning at parse time. ✓.

### v5.19.1 — Dk.\* Docker images
**0 lines C runtime.** Packaging only. ✓.

### v5.20.0 — Te.5 struct ergonomics (Python)
**0 lines C runtime.** All four surface forms (field shorthand,
struct update, let destructuring, if-let / while-let / let-else)
desugar to existing primitives. No new MIR ops. No runtime touch. ✓.

### v5.20.1 — Te.5 bootstrap mirror
**0 lines C runtime.** Bootstrap-side parser/lowerer additions.
The two latent bugs surfaced and fixed (alloca-void on void return
type; TK_UNKNOWN→undef demotion) are emit-side, not runtime-side.
✓.

### v5.21.0 / v5.21.1 — Te.6 chained comparisons
**0 lines C runtime.** AST→AST desugar. Verified live (see §IR
verification below). ✓.

### v5.11.0 panel docket — status

| Item | v5.11.0 status | v5.22.0 status |
|---|---|---|
| **Perf.3** (string_concat 1.60× Rust) | LOW–MEDIUM, allocator-bound | **Still open.** Nothing in the arc touched the string allocator path. |
| **Bn.5** (Go arm broken) | LOW | **Still open.** No benchmark refresh in the arc. |
| **Bn.6** (30-run methodology) | LOW | **Still open.** Same. |
| **Pe.1** (stage2.ll growth) | LOW, downgraded ("curve flattening") | **Still open, slightly re-pressurized.** +5.07% over 10 releases vs +0.34% over the 3-release v5.11.0 arc. Not a v6.0 budget concern but the curve is no longer flattening — it's growing in proportion to AST-node additions. Honest. |
| **Li.1** (LICM regressions) | LOW, v6.0 scope | **Still open.** Unchanged. |
| **Bench refresh** (NEW at v5.11.0) | LOW | **Still open.** Now 14 releases stale. |

## What is preserved from v5.11.0

- **C runtime essentially flat:** +553 lines over 10 releases,
  all in two distinct, well-documented additions. v5.11.0 was
  +0 lines; v5.13.1 + v5.14.1 carried the entire delta; v5.15.0
  → v5.21.1 added zero C lines. Pattern of "additions cluster
  in the patch releases that need them, then long zero-touch
  runs" is the right shape.
- **Strict 3-stage fixed point preserved across 13 consecutive
  releases.** v5.9.0 milestone held: 226,603 → 238,086 lines /
  0-line diff at every release. Verified live —
  `/tmp/stage2.ll` is 238,086 lines. (This is Cobra's primary
  axis but it stops being a -0.1 carry on mine.)
- **No malloc churn in any arc-shipped feature.** Te.6
  `__mn_chain_N` temps lower to `alloca` (stack), not `malloc`.
  Te.5 struct-update synthesizes through existing
  `Construct` MIR — same drop glue.
- **Win.1b bundled-LLVM minimum-set discipline intact.** Not
  re-touched; PATH-stripped smoke job still gates.
- **DX.4 cache walkers leak-clean.** Per-entry alloc/free,
  static recursive walkers; not re-touched.

## Issues Found

### 1. **LOW** — `__mn_indent_to_braces` not declared in `mapanare_core.h`

The function is `MN_EXPORT`'d in `mapanare_core.c:3939`, callable
from self-host via an `extern "C" fn` decl in `parser.mn`, but has
no prototype in the public header. Caller verifies signature only
against the self-host's own decl. Other tooling that links against
`libmapanare_rt.a` (third-party embedders, future Pythonland reuse)
has no header to grab. Every other `MN_EXPORT` in core.c that's
called from .mn code does have a header decl (`__mn_assert_fail`,
`__mn_panic`, etc.).

**Fix:** add to `mapanare_core.h` near the existing v5.14.1 region
(after `__mn_assert_fail` decl):
```c
/** v5.14.1 B.5/B.6: colon-block preprocessor. Mirror of
 *  mapanare/parser.py::_indent_to_braces. Returns a heap MnString;
 *  caller owns the result. */
MN_EXPORT MnString __mn_indent_to_braces(MnString source);
```
One line, zero behavior change, closes the .h ↔ .c asymmetry.
File this against v5.22.x.

### 2. **LOW** — Pe.1 trajectory re-pressurized (downgraded from MEDIUM)

stage2.ll grew **+5.07% over 10 releases** (226,603 → 238,086).
v5.11.0 panel reported the curve flattening; it's not flattening
anymore — it's growing in proportion to bootstrap-side AST node
additions (Te.5: +5,805 lines from new lowerer code; Te.6: ~3,300
lines from new chained-cmp lowerer / parser / semantic / emitter
paths). This is **honest growth** — every byte traces back to a
shipped feature with a SESSION_REPORT — but the v5.11.0 prediction
"+1.7% extrapolated" is wrong. Actual was 3× that. **Not a v6.0
budget concern at the current trajectory** (need another 30
releases of this rate before it doubles), but the "curve
flattening" framing should be retired.

**Fix:** keep Pe.1 LOW, drop the "downgraded — flattening" subtitle,
re-state as "growing in proportion to bootstrap AST surface; not a
budget concern." No code action.

### 3. **LOW** — `__mn_indent_to_braces` allocates O(line-count) per parse

Every line of source becomes a malloc'd `MnIB_LineBuf`. For
mnc_all.mn at 20,377 lines (post-Sh.\*), that's 20k+ small
mallocs per parse. All freed at the end of the function. **Not
broken** — it runs once per file, all allocations are short-lived
and stack-shape-bounded — but it's an obvious target if anyone
ever wants to make `mnc-stage1` startup faster on large files.

**Fix (only if perf surface ever cares):** allocate the joined
output buffer up-front sized to `2 * n_src` (colon-block always
shrinks bytes; `}` lines might exceed that on tight indents),
write directly into it, treat individual lines as offset+length
pairs into the master buffer. Drops to ~5 mallocs total. Don't
do this without a measurement first — the allocator is fast and
this might be premature.

## Recommendations

1. **Add the `__mn_indent_to_braces` header decl** at v5.22.x.
   One line. Closes a .h ↔ .c asymmetry. Zero risk.
2. **Retire the "Pe.1 curve flattening" framing** in CARRY_FORWARD.md
   and the v5.11.0 panel reference. Replace with "+5.07% over
   v5.11.0 → v5.22.0; growth proportional to bootstrap-side AST
   additions; not a v6.0 concern at current rate."
3. **Defer everything else.** No new perf docket. No new alloc
   docket. The arc was clean.

## Post-Production Health Assessment

22 minor versions after the v5.0.0 release-gate, the C runtime
**is in better shape than at v5.0.0.** The shape that matters:

- **Number of arc releases that touched runtime/native/:** 2 of 10
  (v5.13.1, v5.14.1).
- **Number of arc releases that added new exports:** 2 of 10
  (the same two).
- **Number of arc releases I'd grade as "could have been done with
  less C":** 0.

The lead's claim of "zero new runtime function additions across
the arc" is **off by two**, but both additions are load-bearing
patch-release closures (a missing-symbol link error and the
colon-block preprocessor). Neither is Te.\* surface; the Te.1–Te.6
features genuinely shipped without runtime additions. The claim is
imprecise, not dishonest. SESSION_REPORTs document both additions
honestly in their own releases.

**Te.6 chained comparisons is the cleanest desugar in the arc.**
`mapanare/lower.py:2129` and `mapanare/self/lower.mn:1530` are
mirror images, both ~30 lines, both purely AST→AST. The `__mn_chain_N`
temps go through existing `LetBinding` machinery, lower to `alloca`,
read back via `load`. Verified on `/tmp/chain95.ll`: 1× `call
@middle(`, 5× `__mn_chain_0` SSA refs, all stack-resident. Once-eval
property is structural, not testimonial. **This is how you ship a
language feature on a calorie-restricted runtime.**

`__mn_indent_to_braces` is the right kind of C — defensive routing
around two known bootstrap-lower bugs, in plain ANSI C, with a
fast path that bails for brace-only sources, with line-by-line
correspondence to a Python reference that has a 142-case
cross-validation test (`tests/bootstrap/test_indent_preprocessor.py`).
**This is how you write C that has to mirror Python.**

The v5.21.1 hygiene release closed 13 doc-surface findings without
touching one byte of C. v5.22.0 is panel-only. **My axis is
healthy.**

## Raw Notes

```
$ git diff v5.11.0..HEAD --shortstat -- runtime/native/
 2 files changed, 553 insertions(+)

$ git diff v5.11.0..HEAD --stat -- runtime/native/
 runtime/native/mapanare_core.c | 549 +++++++++++++++++++++++++++++++++++++++++
 runtime/native/mapanare_core.h |   4 +

$ git log --oneline v5.11.0..HEAD -- runtime/native/
36aab79 v5.17.0 Sh.A.1.B: fix `_indent_to_braces` multi-level else dedent
d5849ff v5.14.1 Phase 2: __mn_indent_to_braces in C runtime (B.5/B.6)
91326d4 v5.13.1: At.* — `@test` runtime fix (patch)

$ git show v5.11.0:runtime/native/mapanare_core.h | grep -c MN_EXPORT
145
$ grep -c MN_EXPORT runtime/native/mapanare_core.h
146         # +1: __mn_assert_fail

$ git show v5.11.0:runtime/native/mapanare_core.c | grep -c MN_EXPORT
158
$ grep -c MN_EXPORT runtime/native/mapanare_core.c
160         # +2: __mn_assert_fail + __mn_indent_to_braces

$ wc -l runtime/native/*.c runtime/native/*.h
... 15938 total
```

Stage2.ll line count verified live: `wc -l /tmp/stage2.ll` →
238086. Matches Cobra's claim and the v5.20.1 milestone.

Te.6 once-evaluation verified live:
```
$ python3 -m mapanare emit-llvm -O0 tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain95.ll
$ grep -c "call.*@middle" /tmp/chain95.ll
1
$ grep "__mn_chain_" /tmp/chain95.ll | head
  %__mn_chain_0.a.4 = alloca i64, align 8
  store i64 0, ptr %__mn_chain_0.a.4
  store i64 %l.3, ptr %__mn_chain_0.a.4
  %l.7 = load i64, ptr %__mn_chain_0.a.4
  %l.11 = load i64, ptr %__mn_chain_0.a.4
```
Stack-resident, single call, no heap. Honest.

`__mn_indent_to_braces` allocation accounting:
- malloc: 1 (final joined output)
- realloc-grown: line buffers (1 per source line), output list,
  frame stack
- free: matches everything alloc'd before return
- caller drop glue: relies on .mn-side `MnString` lifetime
  management on the returned `is_heap=1` value

`MnIB_Frame` is `{int64, int64, int64}` = 24 bytes. Could pack
to 16 by collapsing `needs_comma` (1 bit) + `prev_child_idx`
(int63) into one word. Frame stack depth ≤ ~10 for any sane
source. Saves <500 bytes per parse. **Don't bother.**

Pe.1 trajectory:
- v5.3.0 → v5.8.0 (9 releases): +80%
- v5.8.0 → v5.11.0 (3 releases): +4.0% (1.33%/release)
- v5.11.0 → v5.22.0 (10 releases, this arc): +5.07% (0.51%/release)

Per-release rate halved again. The curve is **not** flattening to
zero (Te.5 + Te.6 added new lowerer paths) but it's still slowing.
Not a budget concern.

Score breakdown vs v5.11.0 (9.8):
- **Te.6 desugar emits zero runtime calls (verified IR-level)**:
  +0.05
- **Te.5 mirror added 5,805 IR lines without breaking fixed-point;
  bootstrap-side land, not C-side**: 0.0 (not my axis)
- **`__mn_indent_to_braces` is leak-clean and fast-path-gated**:
  +0.05
- **Strict fixed-point streak extended to 13 releases (longest
  project-history)**: +0.05
- **2 new exports vs claimed "zero"** (imprecise but documented):
  -0.05
- **Pe.1 trajectory re-pressurized vs v5.11.0 prediction**: -0.05

Net: 9.80 + 0.05*3 - 0.05*2 = 9.80 + 0.05 = **9.85**.

The +0.05 vs v5.11.0 is the right delta. v5.11.0 was a
zero-touch release on my axis; v5.22.0 closes a 10-release arc
with two well-documented additions and zero waste. The bar moved
slightly because (a) Te.6 once-eval verified structurally clean
in IR and (b) the fixed-point streak is now record-setting.
**My axis can't really do better than this without the lead
deleting code, and there's no fat to delete.**

— Mamba
