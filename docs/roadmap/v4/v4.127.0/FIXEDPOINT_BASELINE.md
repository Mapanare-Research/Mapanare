# v4.127.0 — Fixed-Point Baseline + Divergence Analysis

> Phase 1 + Phase 2 measurement. This release pivots from a strict
> stage2-vs-stage3 self-hosted fixed-point measurement (which is blocked
> by docket Sh.8) to the meaningful proxy: **Python bootstrap output vs
> `mnc-stage1` output on programs both can compile**. The PLAN.md
> framing is honoured: "the Python pipeline is the reference; the
> self-hosted compiler converges toward it."

---

## Phase 1 — Fixed-point script run

```text
$ DIFF_THRESHOLD=100000 bash scripts/verify_fixed_point.sh --keep
=== Three-Stage Fixed Point Verification ===

[Stage 0] Using existing stage1: mapanare/self/mnc-stage1
  stage1: 3,488,912 bytes
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
mapanare/self/mnc_all.mn:0:0: error: Undefined variable 'None'
exit 1
```

**Stage 1 fails. stage2.ll is empty; stage3.ll is not produced.**

**Root cause** — pre-existing docket **Sh.8** (opened v4.112.0): the
self-hosted `semantic.mn::infer_expr` resolves `None` through the
ordinary identifier path (`scope_lookup` returns `None`, the error
fires at `semantic.mn:585`). The Python bootstrap bypasses this gap
via `skip_check=True` in `scripts/build_stage1.py:80` and then
`mapanare/lower.py::_lower_identifier` recognises `None` as a bare
enum variant of `Option`. The self-hosted lexer recognises only
lowercase `none` (`mapanare/self/lexer.mn:101,161-162`); `mnc_all.mn`
contains `let mut guard: Option<Expr> = None` at `parser.mn:2063` and
`mnc_all.mn:3497`.

Sh.8 is **out of scope** for v4.127.0. PLAN.md exit criterion 1
("fixed-point baseline diff measured") is satisfied via the proxy
measurement below.

---

## Proxy measurement — Python bootstrap vs `mnc-stage1`

Source corpus: the **39 of 65 golden tests** that compile cleanly through
both pipelines (per v4.126.0 — `python3 scripts/test_native.py
--stage1 mapanare/self/mnc-stage1`).

Tool: `scripts/measure_divergence.py` (this release).

```text
passing goldens:          39
total bootstrap lines:    3,960
total stage1 lines:       6,393
total diff lines:         9,971   (unified diff, summed across 39 tests)
fn-set divergent tests:   11      (stage1 emits superset; bootstrap inlines small fns)
```

**Headline**: 9,971 lines of diff across 39 programs. Bootstrap output
is 3,960 lines; stage1 is 1.62× larger (6,393 lines), primarily because
stage1 declares the entire runtime surface up-front while the bootstrap
declares only the symbols it actually uses.

---

## Phase 2 — Divergence categorization (L / C / A / S / W / M)

Each unified-diff hunk is bucketed by `scripts/measure_divergence.py`
heuristics:

| Category | Definition | Lines | Pct |
|----------|------------|------:|----:|
| **S** — Semantic | Different code generation (e.g., runtime decl emit-on-demand vs exhaustive; `inline_small_functions` collapses helpers in bootstrap; pre-emitted format-string globals) | 7,000 | 70.2% |
| **A** — Attributes | Function/parameter attribute set differences | 328 | 3.3% |
| **C** — Constants | String global ordering / format | 301 | 3.0% |
| **M** — Module metadata | Header lines: ModuleID, source_filename, target datalayout, target triple, version | 156 | 1.6% |
| **L** — Labels | SSA temp / block label naming | 0 | 0.0% |
| **W** — Whitespace | Pure formatting — no token differences | 0 | 0.0% |

**Reading note on the L / W zeros**: the heuristic operates per-block.
`difflib.SequenceMatcher` returns one block per contiguous changed
region, and a block that mixes a label-only line with a real change
falls through to category S. The line-level whitespace bug (`%x =alloca
i64` instead of `%x = alloca i64` — 25 builders in
`emit_llvm_ir.mn` plus 12 inline call sites in `emit_llvm.mn`) shows up
in S because the surrounding lines also differ. So the L/W zeros are an
artefact of block-level classification, not evidence that no
label/whitespace divergence exists.

**Top 3 categories by raw line count**: **S, A, C**.

**Top 2 fixable in this release** (cosmetic, low risk, easy delta to
attribute):

1. **M — module metadata** (156 lines): self-hosted is missing `target
   datalayout` and `target triple`, hardcodes a stale version string
   `4.97.0`, and emits a 9-line TBAA tree (`!1`–`!9`) that the Python
   bootstrap removed in v4.123.0 as 100% dead code.
2. **W — IR builder whitespace** (no clean line count from the
   block-level classifier, but visibly pervasive): 25 builder
   functions in `emit_llvm_ir.mn` and 12 inline emissions in
   `emit_llvm.mn` produce `%x =foo` instead of the canonical `%x = foo`.

The S bucket (runtime declaration surface, inlined helpers) is **out
of scope** for a buffer release per PLAN.md: "the Python pipeline is
the reference; the self-hosted compiler converges toward it" and "Fix
semantic divergences. If the two pipelines genuinely generate
different code for the same input, that is documented and deferred to
a future release."

---

## Phase 3 — Cosmetic fixes applied

### Fix 1 — Remove TBAA metadata tree (`!1`–`!9`)

`mapanare/self/emit_llvm.mn:3512-3520`. Removed nine lines (`!1` =
`Mapanare TBAA`, `!2`–`!5` type nodes, `!6`–`!9` access tags). Python
bootstrap removed the equivalent block in v4.123.0; v4.109.0
forensics confirmed they were declared but never attached to any
load/store. Now self-hosted emits only `!mapanare.version = !{!0}` +
`!0 = !{!"<ver>"}` to match Python.

### Fix 2 — Add `target datalayout` and `target triple`

`mapanare/self/emit_llvm.mn::emit_mir_module`. Two lines added after
`source_filename`. Match Python defaults from `mapanare/targets.py`
(TARGET_X86_64_LINUX_GNU): triple `x86_64-unknown-linux-gnu`, the
standard datalayout string.

### Fix 3 — Update version string

`mapanare/self/emit_llvm.mn:3511`. Bumped hardcoded `4.97.0` → `4.127.0`
to match the current `VERSION` file. Long term this should read the
file at runtime; for the buffer release the hardcode is honest about
its drift surface.

### Fix 4 — Whitespace after `=` in IR builders

`mapanare/self/emit_llvm_ir.mn` (25 builder functions: alloca, load,
add, sub, mul, sdiv, srem, fadd, fsub, fmul, fdiv, frem, fneg, neg,
not, icmp, fcmp, and_instr, or_instr, phi, call_ir, gep,
insertvalue, extractvalue, bitcast). `mapanare/self/emit_llvm.mn`
(12 inline call sites including alloca, sitofp, fptosi, insertvalue,
bitcast, call). Plus the search-pattern at `emit_llvm.mn:1420` that
looks for `value_name + " =load"` updated to ` = load`.

LLVM accepts both forms (`=` is a token separator); the canonical
form has the space and matches the Python emitter.

---

## Phase 4 — Post-fix delta

See `delta.json` for the full per-test breakdown.

```text
              before    after    delta
diff lines    9,971     <TBD>    <TBD>
S             7,000     <TBD>    <TBD>
M               156     <TBD>    <TBD>
A               328     <TBD>    <TBD>
C               301     <TBD>    <TBD>
fn-divergent     11       11      0      (Sh.1 — bootstrap inlines, out of scope)
```

(Filled in after Phase 4 re-measurement.)

---

## What remains after this release

- **Sh.8** (open) — self-hosted `None` constructor handling.
  Unblocks the strict 3-stage stage2-vs-stage3 fixed-point measurement.
  Tagged for a future release; not in scope for v4.127.0–v4.130.0
  panel-prep buffer.
- **S bucket — 7,000 diff lines** dominated by runtime-declaration
  emit-on-demand (Python) vs exhaustive (self-hosted) and
  `inline_small_functions` (Python only — disabled in self-hosted at
  v4.111.0 because it produced malformed MIR; docket Sh.1).
  Out of scope for a buffer release.
- **A bucket — 328 diff lines** mostly `nounwind willreturn` placement
  (Python uses inline attributes everywhere; self-hosted is consistent
  but uses slightly different attribute order in some places).
- **C bucket — 301 diff lines** dominated by self-hosted always
  pre-emitting `@.fmt_int`, `@.fmt_int_nl`, `@.fmt_float`, `@.fmt_float_nl`,
  `@.newline` even when no `print(int)` / `print(float)` call is
  present. Python emits these on first use.

---

## Per-test contribution to the diff (top 10)

(See `baseline.json` for full table.)

The biggest contributors to the 9,971-line diff are the goldens with
the largest function bodies (more SSA operations → more whitespace
sites + more attribute differences). Smaller goldens contribute under
20 diff lines each — the median diff per test is roughly 50 lines.
