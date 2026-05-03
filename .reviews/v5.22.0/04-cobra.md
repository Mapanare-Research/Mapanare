# Cobra — Bootstrap / Self-Hosted Review of Mapanare v5.22.0

**Reviewer:** Cobra
**Personality:** C++ veteran. Has seen every trend. Calls things "quaint" and "amusing." Compares everything to C++.
**Previous Version Reviewed:** v5.11.0
**Score:** 9.55 / 10
**Grade:** EXCEEDS
**Delta vs v5.11.0:** −0.15
**Verdict:** PASS WITH NOTES
**Confidence:** 9
**Files Reviewed:** `mapanare/self/{ast,lexer,parser,semantic,lower,lower_state,mir,mir_opt,emit_llvm,emit_llvm_ir,main,abi,transpiler,from_*}.mn`, `mapanare/self/mnc_all.mn`, `scripts/{verify_fixed_point,build_from_seed,check_struct_registry,build_stage1}.{sh,py}`, `.github/workflows/ci.yml`, `bootstrap/seed/linux-x86_64/`, `runtime/native/mapanare_core.{c,h}`, `tests/bootstrap/`, `tests/test_ci.py`, all 16 SESSION_REPORTs v5.13.0–v5.21.1.

## Executive Summary

Quaint. So you took the entire compiler — the *self-hosted* one, the
14k-line .mn one — and ran it through `mnc fmt --to-terse` like it was
some Python beautifier from a 2008 PyCon lightning talk, and the
fixed-point survived. By construction, you said. The C++ committee
spent a decade just *talking* about modules; you mechanically rewrote
your bootstrap source surface in a single panel cycle and the
byte-identity loop closed at the other end. Fine. Credit where due.

The strict 3-stage fixed point holds at **238,086 lines / 0 diff** at
v5.22.0 HEAD — I just ran it. That's the v5.9.0 milestone preserved
through 13 consecutive shipping releases. Longest streak in project
history. The C++ STL took twenty years to make `std::function`
deterministic across implementations; you got 13 zero-diff releases in
a quarter of a year with a self-hosted compiler that's actively
shrinking. *La culebra está delgada y cómoda.*

Two findings keep this off a 9.7+: the `check_struct_registry.py` CI
gate has been **silently broken since v5.17.0** because the regex
hard-codes brace-form struct headers (`struct Name {`) and Sh.B
mechanically rewrote every struct in `mapanare/self/*.mn` to
colon-form (`struct Name:`). 23 violations at HEAD; the local pytest
gate (`tests/test_ci.py::test_struct_registry_gate_passes`) is RED. I
don't know how this is shipping green on PR — either CI is silently
broken, or `if: always()` interacts oddly with `set -e`, or the matrix
is masking it. **This is exactly the failure mode the gate was
designed to catch in the v4.143.0 panel.** Second: the per-PR
fixed-point gate I asked for at v5.8.0, v5.11.0, and was about to ask
for a fourth time — *was actually wired into CI back at v4.29.0*. I
missed it at v5.11.0. The line is right there at
`.github/workflows/ci.yml:858`. Mea culpa, but the documented closure
in the v5.11.0 panel docket was off by 22 minor versions of latency.

## Score: 9.55 / 10

## Progress Since Last Review (v5.11.0 → v5.22.0)

### Strict 3-stage fixed point — **HELD**

Live verification at v5.22.0 HEAD:

```
$ bash scripts/verify_fixed_point.sh --keep
[Stage 1] stage2.ll: 238086 lines, llvm-as OK
[Stage 2] stage3.ll: 238086 lines, llvm-as OK
[Verify] FIXED POINT REACHED, stage2.ll == stage3.ll (238086 lines, 0 diff)
```

The streak: v5.9.0 (226,603) → v5.10.0 (226,603) → v5.11.0 (226,603) →
v5.13.0 (~227k) → v5.14.0 → v5.14.1 (228,630) → v5.15.0 → v5.15.1
(228,630) → v5.16.0 (231,957) → v5.17.0 (231,957) → v5.17.1 (231,957)
→ v5.17.2 (231,723) → v5.18.0 (232,281) → v5.19.0 → v5.19.1 → v5.20.0
(232,281) → v5.20.1 (238,086) → v5.21.0 → v5.21.1 (238,086).
**Thirteen consecutive shipping releases**, all 0-line diff. SESSION_REPORTs
cite the line counts; I sampled v5.21.1 directly and the math holds.

This is the metric, and it's the *unforgiving* metric. The whole point
of fixed-point self-compilation is that you cannot fudge a byte-for-byte
comparison. Either stage2 produces the same text as stage3, or it
doesn't. For 13 releases the answer is "yes." Sh.* shrinking the
sources by ~3k lines through mechanical rewrite — fixed point held.
Te.5 adding new AST nodes (StructUpdate, LetDestructure, IfLet,
WhileLet, LetElse) — fixed point held. Te.6 adding ChainedCmp —
fixed point held. Te.4 string-interp parity rewriting the entire
self-host lex/parse/lower path — fixed point held. The v5.6.x
broken-transient class is gone; the v5.8.x NEAR-fixed-point Dr.1 class
is gone. **Status: STRICT FIXED POINT preserved. La culebra está
delgada.**

### Per-PR fixed-point CI gate — **CLOSED** (mea culpa: was already wired)

`.github/workflows/ci.yml:817–858`:

```yaml
fixed-point:
  name: Fixed-Point Bootstrap
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
    - name: Setup Python 3.12
    - name: Install Mapanare
    - name: Install LLVM tools
    - name: Symlink clang / llvm-as
    - name: Build stage1
      run: python scripts/build_stage1.py
    - name: Verify fixed-point bootstrap
      shell: bash
      run: |
        set -e
        ulimit -s 65536
        bash scripts/verify_fixed_point.sh
```

Triggered on every `push` to `dev` and every `pull_request` against
`dev` (lines 1–8 of `ci.yml`). The job is a separate runner from `ci`
so a fixed-point break is reported independently. The comment
**explicitly cites the v4.26.0 panel** and walks through the v4.29.0
hardening (set -e, threshold ratchet, non-empty stage3 check, llvm-as
validation). All five teeth are in `verify_fixed_point.sh` and the CI
job propagates the script's exit code.

I asked for this at v5.8.0 and at v5.11.0. **It was already there
both times.** I missed it. The v5.11.0 panel docket carried "Cobra
per-PR fixed-point gate" as LOW — closing it should have happened
two panels ago. Self-correcting carry-forward: **CLOSED at v4.29.0.**

This is the same shape of failure I've seen on the C++ committee for
30 years: someone files a defect because they didn't read the latest
working draft. The data was right there in the file. Quaint.

### Self-hosted source shrink — **HELD WITH NUMBER NUANCE**

The SESSION_REPORTs claim −3,950 lines (−13.8%) cumulative through
Sh.* (v5.13.0 → v5.17.1) and **−3,988 lines (−13.9%)** through v5.17.2
including the defensive-loop cleanup. Live measurement at v5.22.0
HEAD vs **the actual `v5.13.0` git tag**:

```
$ for f in 17 modules; git show v5.13.0:mapanare/self/$f | wc -l
$ wc -l mapanare/self/$f at HEAD
v5.13.0 baseline (17 hand-edited modules): 27,922
HEAD (v5.21.1):                            25,637
Delta:                                     −2,285  (−8.18%)
```

The SESSION_REPORTs **cite a `v5.13.0` baseline of 28,698 lines, not
27,922.** The 776-line discrepancy is real and traceable: the v5.17.0
SESSION_REPORT's per-module "Before" column lists `ast.mn = 952` but
v5.13.0 git shows `ast.mn = 906`; same shape for all 17 modules. The
"baseline" measured by the rewrite scripts is the *immediate
pre-Sh.B* baseline, taken in the v5.16.0 → v5.17.0 transition window
**after** v5.16.0 Te.4 added ~3.3k lines of new lex/parse/lower for
string-interp parity (those went into the same 17 modules). They
labeled it "v5.13.0" but it isn't.

**This is a labeling drift, not a number lie.** The shrink magnitude
(`−3,988` from the immediate pre-Sh.B baseline) is correctly measured
at the point of the rewrite. The post-Sh.\* growth back up (Te.5 added
+742 bootstrap lines per the v5.20.1 SESSION_REPORT, Te.6 added +500
via ChainedCmp; the mnc_all.mn regen routinely loses lines to terser
emission) means the v5.13.0 → v5.21.1 net shrink of −2,285 lines is
the *true* arc-end picture.

Either number is impressive — a self-hosted compiler that absorbed six
new language features and *still* ended below where it started is the
right shape. But the SESSION_REPORTs should cite the measured baseline
honestly: "post-Sh.B baseline" or "v5.16.0 HEAD," not "v5.13.0."
LOW finding; numbers are accurate, the label is sloppy.

### Bootstrap mirror cross-tests — **ALL GREEN**

```
$ python3 -m pytest tests/bootstrap/test_te5_mirror.py \
    tests/bootstrap/test_chained_cmp_mirror.py \
    tests/bootstrap/test_comprehension_mirror.py \
    tests/bootstrap/test_string_interp_mirror.py \
    tests/bootstrap/test_indent_preprocessor.py \
    tests/bootstrap/test_stage1_compile.py
263 passed in 314.11s
```

By file:

| Suite | Cases | Status |
|---|---:|---|
| test_te5_mirror.py | 12 | PASS |
| test_chained_cmp_mirror.py | 10 | PASS |
| test_comprehension_mirror.py | 10 | PASS |
| test_string_interp_mirror.py | 10 | PASS |
| test_indent_preprocessor.py | 201 | PASS |
| test_stage1_compile.py | 20 | PASS |

The PRE_PANEL_AUDIT cites `test_indent_preprocessor.py` at 142 cases;
my collection shows **201**. The audit number is from v5.14.1 ship —
the suite has grown by 59 cases as goldens 67–95 landed (every new
golden gets a colon-form round-trip case). The audit is stale on the
count but not on the verdict. NEAR finding.

### Bb.* seed-refresh discipline — **HELD**

| Release | Bb.* | Justification |
|---|:---:|---|
| v5.13.0 | (no .mn edits) | Mc.2 formatter, no runtime touch |
| v5.13.1 | (At.* runtime fix) | `__mn_assert_fail` re-export, but v5.10.0 seed predates → would need refresh; v5.14.1 supersedes |
| v5.14.0 | (no seed touch) | Te.1 colon syntax, Python-side preprocessor; bootstrap mirror deferred to v5.14.1 |
| v5.14.1 | **Bb refresh** | New `__mn_indent_to_braces` C-runtime export — required |
| v5.15.0–v5.16.0 | SKIP | Pure parser/lower additions, no new C exports |
| v5.17.0 | **Bb.5 (Sh.E)** | Bootstrap source rewritten to colon syntax; old seed predates `_indent_to_braces` preprocessor → segfaulted on stage 1 |
| v5.17.1–v5.21.1 | SKIP | Five releases with zero new C-runtime exports |

Seed at HEAD: `929e7a4b...b19b0a0` (the v5.17.0 Sh.E refresh). Same
sha as commit `590169e`. **Five consecutive Bb.* skips** matches the
discipline I credited at v5.11.0 — refresh when the C-runtime ABI
changes, leave it alone when it doesn't. The cadence works.

### Self-hosted module health

```
$ wc -l mapanare/self/*.mn
   89 abi.mn
  855 ast.mn
 5765 emit_llvm.mn        (-601 from v5.13.0)
  181 emit_llvm_ir.mn      (-94)
  529 lexer.mn             (-64)
 4896 lower.mn             (+23, Te.5/Te.6 net)
  517 lower_state.mn       (-72)
 1178 main.mn              (+40, Mc.* dispatch)
  749 mir.mn               (-172)
 1618 mir_opt.mn           (-262)
 2601 parser.mn            (+2, Te.5/Te.6 net)
 2136 semantic.mn          (-132)
  486 transpiler.mn        (-110)
  ...
```

Headline: `lower.mn` net +23 over v5.13.0 despite eating Te.5
ConstructUpdate / LetDestructure / IfLet / WhileLet / LetElse + Te.6
ChainedCmp + the alloca-void/TK_UNKNOWN bug fixes. That's the right
shape — terseness arc absorbed without inflating the lowerer. Compare
to the C++ STL's `std::variant` adoption: 4,500-line patch, 2 ABI
breaks, 2 release cycles of compiler implementer pain. Yours: +500
net for an entire chained-comparison feature, fixed-point preserved.
Quaint discipline.

### v5.20.1 latent bug fixes — **VERIFIED**

The Te.5.F.E SESSION_REPORT documents two pre-existing bugs in
`lower_match` that surfaced when let-else exercised the
non-divergent-else path. I verified both fixes at HEAD in
`mapanare/self/lower.mn`:

**Fix 1 — alloca-void skip:**

```mn
let fn_ret: MIRType = get_current_fn_ret_type(s)
if fn_ret.kind == TK_VOID():
    return new_lower_result(void_value(), s)
let rr_unreach: LowerResult = make_value(s, fn_ret, "match_result")
s = rr_unreach.state
let dummy_addr: Value = new_value(rr_unreach.value.name + ".dummy", fn_ret)
s = emit_instr(s, Instruction::Alloca(dummy_addr, fn_ret))
```

The early return when `fn_ret.kind == TK_VOID()` prevents the lowerer
from emitting `alloca void` (which is invalid LLVM). The comment
explicitly cites v5.20.1 if-let / while-let / let-else as the use
case. Fix is at the right structural site and matches the
SESSION_REPORT description verbatim.

**Fix 2 — TK_UNKNOWN demotion fix:**

```mn
let arm_kind: Int = arm_val_r.value.ty.kind
if arm_kind == TK_VOID() || arm_val_r.value.name == "%void":
    let zero_arm: Value = new_value("undef", arm_val_r.value.ty)
    ...
else:
    let pe_val: PhiEntry = new_phi_entry(exit_label, arm_val_r.value)
```

Pre-fix, the demotion to undef happened on `TK_UNKNOWN || TK_VOID ||
%void`; post-fix, only `TK_VOID || %void`. Comment cites the
infer_variant_payload_type → TK_UNKNOWN → undef → phi skip → alloca
fn_ret → alloca void cascade. Treating TK_UNKNOWN as a real value
lets the emitter resolve the LLVM type from incoming phi values.
Both fixes are surgical, at the bug site, with comments documenting
the failure mode for future maintainers. **This is the discipline I
want.**

### Te.6 once-evaluation — **VERIFIED IN IR**

The load-bearing semantic test for chained comparisons. The lowerer
must bind any non-trivial middle operand to a `__mn_chain_N` temp
**exactly once** per chain instance, otherwise `0 < f() < 10` evaluates
`f()` twice and the chain has wrong semantics.

Live test on `tests/golden/95_chained_cmp_side_effect.mn`:

```
$ python3 -m mapanare emit-llvm -O0 \
    tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain.ll
$ grep "@middle" /tmp/chain.ll
define internal noundef i64 @middle(i64 noundef %seed) nounwind willreturn {
  %c.1 = call i64 @middle(i64 %l.0)
$ grep -c "@middle(" /tmp/chain.ll
2  (= 1 define + 1 call site)
```

**Exactly one call site per chain instance** in the source. The
synthesized temp is visible in IR:

```
%__mn_chain_0.a.4 = alloca i64, align 8
store i64 0, ptr %__mn_chain_0.a.4
store i64 %l.3, ptr %__mn_chain_0.a.4   ; the once-evaluated middle
%l.7  = load i64, ptr %__mn_chain_0.a.4
%l.11 = load i64, ptr %__mn_chain_0.a.4
```

Two loads, one store. The middle term is computed once; the chain's
`0 < x` and `x < 100` arms each load the cached value. **D3
once-evaluation is structurally correct.** Same pattern as the
SESSION_REPORT documents.

In C++ this would be `auto __chain_0 = f();` plus `0 < __chain_0 &&
__chain_0 < 100`, and you'd hope the optimizer is smart enough to
not double-call. You don't *hope* — the lowerer guarantees it at the
MIR level, before optimization runs. Right way.

### Spot-checks — 5 SESSION_REPORT claims

Random sampling of claims across the 16 SESSION_REPORTs against
v5.22.0 HEAD:

| Claim | Source | Verdict |
|---|---|---|
| v5.21.0: `Expr::ChainedCmp(List<Expr>, List<String>)` AST variant | v5.21.0 SESSION_REPORT line ~50 | ✓ `mapanare/self/ast.mn:128` |
| v5.21.0: `chain_compare_counter: Int` field on LowerState | v5.21.0 SESSION_REPORT | ✓ `mapanare/self/lower_state.mn:43` |
| v5.20.1 Te.5.F.C: `Expr::ConstructUpdate(String, List<FieldInit>, Expr)` | v5.20.1 SESSION_REPORT | ✓ `mapanare/self/ast.mn:119` |
| v5.20.1 Te.5.F.D: `Stmt::LetDestructure(StructPattern, Bool, Option<TypeExpr>, Expr)` | v5.20.1 SESSION_REPORT | ✓ `mapanare/self/ast.mn:149` |
| v5.20.1 Te.5.F.E: `Expr::IfLet`, `Stmt::WhileLet`, `Stmt::LetElse` | v5.20.1 SESSION_REPORT | ✓ `mapanare/self/ast.mn:122,153,155` |

All five claims hold against the actual code. Discipline check
passed. v5.20.1 SESSION_REPORT is **honest** in its claims — the AST
shape it documents is the AST shape that ships.

### No new MIR ops / IR shapes / runtime fns — **VERIFIED**

```
$ diff <(git show v5.13.0:mapanare/mir.py | grep '^class.*Instruction)') \
       <(grep '^class.*Instruction)' mapanare/mir.py)
$ echo $?
0
```

Identical Instruction subclass list between v5.13.0 and HEAD. Te.1
(colon-block) desugars at parse time. Te.2 (comprehensions) lowers to
existing Push/Insert. Te.3 (`{}` deprecation) is parse-time-only. Te.4
(string-interp parity) routes through pre-existing `__mn_str_concat`
chain. Te.5 (struct ergo) desugars at lower time to existing
Construct/match/let. Te.6 (chained-cmp) desugars to existing BinOp
LT/GT/LE/GE/EQ/NE + AND. **Zero new MIR ops** — the SESSION_REPORTs'
load-bearing claim verifies.

C runtime delta v5.13.0..HEAD:

```
$ git diff v5.13.0..HEAD --stat -- runtime/native/
 runtime/native/mapanare_core.c | 549 +++++++++++++++++++++++++++++++++++++++++
 runtime/native/mapanare_core.h |   4 +
 2 files changed, 553 insertions(+)
```

Three commits: `91326d4` (v5.13.1 At.* `@test` fix, runtime export
tightening), `d5849ff` (v5.14.1 Phase 2 — `__mn_indent_to_braces`
C-runtime preprocessor, ~280 LOC), `36aab79` (v5.17.0 Sh.A.1.B
`_indent_to_braces` multi-level dedent fix). One new export across the
arc. **Mamba's "Pe.1 budget held" claim is structurally correct** —
the C runtime is essentially flat over the v5.13–v5.21 arc.

## What is preserved from v5.11.0

### v5.11.0 panel docket

| Item | v5.11.0 status | v5.22.0 status | Notes |
|---|---|---|---|
| **Bo.21** version badges | HIGH, open | **CLOSED** v5.21.0 (badges via bump_version.py) | Verified by `cat docs/README.{es,pt,zh-CN}.md \| head -10` |
| **Bo.18r** README contradiction | MEDIUM, open | **CLOSED** v5.21.1 H.1/H.2 | Bumped 80/80 → 95/95, line counts to 238,086 |
| **Bo.17r** localized READMEs | MEDIUM, open | **CLOSED** v5.21.1 H.6 | Three subsections rewritten in es/pt/zh-CN |
| **Coral SPEC re-sync** | MEDIUM, open | **CLOSED** v5.21.1 H.5 | Header bumped v5.7.1 → v5.21.0 cut |
| **Mc.\* mnc parity** | MEDIUM, open | **CLOSED** v5.18.0 | Mc.1 LSP, Mc.3 init, Mc.4 check shipped |
| **Anaconda Pk.1.A** smoke gate | LOW, open | not in my domain | defer to Anaconda |
| **Cobra per-PR fixed-point gate** | LOW, open (3rd ask) | **WAS ALREADY CLOSED at v4.29.0** | mea culpa — see above |
| **Cobra `>= 45` magic-number** | LOW, open | **STILL OPEN** | scripts/build_from_seed.sh:159 unchanged |
| **Viper V.6/V.7/V.8** | LOW, open | not in my domain | defer to Viper |
| **Rattler #1 BENCHMARKS staleness** | LOW, open | **CLOSED** v5.21.1 H.12 | per-platform split + last-sync admonition |
| **Rattler #2 set +e teardown crash** | LOW, open | not in scope | defer to Rattler |
| **Rt.04 multi-level alias** | LOW (deferred to v6.0) | **STILL DEFERRED** v6.0 | structurally inherited |

Net: of the 12 v5.11.0-panel items, **8 are CLOSED**, 1 is *was already
closed and Cobra missed it twice*, 1 still open in my domain (`>= 45`),
1 deferred to v6.0 correctly, 1 punted to other reviewers.

### Carry-forward state (Cobra/bootstrap axis only)

- Strict 3-stage fixed point: 13-release streak (was 5 at v5.11.0 panel)
- Bb.* discipline: 5-release SKIP streak (was 1 at v5.11.0)
- Self-hosted modules: 17 hand-edited (post-Sh.B regen) vs 10 at v5.11.0
- mnc_all.mn regen size: 20,979 vs 22,507 at v5.11.0 (−1,528, −6.8%)
- ABI dispatch: 4-way (SysV/Win64/i686/Apple AArch64), unchanged
- C-runtime exports added across arc: **1** (`__mn_indent_to_braces`)
- New MIR ops: 0
- New IR shapes: 0
- New runtime functions for language features: 0

The "zero / zero / zero" line is the discipline signal. Six language
features absorbed without expanding the substrate. C++ would have
shipped at least three new function call ABI conventions, two new
linker sections, and a `<chrono>`-compatible chained-comparison
proposal that takes 4 years to standardize.

## Issues Found

### 1. **HIGH** — `check_struct_registry.py` CI gate silently broken since v5.17.0

The gate at `.github/workflows/ci.yml:148` runs
`scripts/check_struct_registry.py` as a hard gate (`set -e`,
`if: always()`). The script's regex at line 47:

```python
STRUCT_HEADER_RE = re.compile(r"^(?:pub\s+)?struct\s+([A-Z][A-Za-z0-9_]*)\s*\{")
```

requires a literal `{` at the end of the struct header. After v5.17.0
Sh.B mechanically rewrote every struct in `mapanare/self/*.mn` to
colon syntax (`struct StructEntry:`), the regex matches **zero**
struct definitions. Every entry in `build_internal_struct_list`
becomes a "no matching struct definition found" violation:

```
$ python3 scripts/check_struct_registry.py; echo "exit: $?"
check_struct_registry: 23 violation(s). build_internal_struct_list /
register_all_internal_structs must match the field order of each struct
definition in mapanare/self/*.mn.
emit_llvm.mn: registry lists 'StructEntry' in build_internal_struct_list,
but no matching struct definition found in mapanare/self/*.mn
... [22 more]
exit: 1

$ python3 -m pytest tests/test_ci.py::TestToolsRunLocally::test_struct_registry_gate_passes
FAILED
```

The associated pytest gate at `tests/test_ci.py:153–160` is **RED at
HEAD**. The CI workflow uses `set -e`, so the GHA run should be
failing on this step every push to `dev`. Either:
1. The CI status quo is "this job fails every time and nobody notices,"
2. The `if: always()` is somehow letting downstream jobs proceed and the
   final aggregate ships green,
3. Or the GHA matrix has a quirk I'm not seeing.

Whichever shape it is, **this is the exact failure mode the v4.143.0
panel commissioned this gate to catch** — registry/struct drift
producing latent miscompiles where both stages diverged the same way.
Sh.B was a perfect storm for this gate: every struct definition moved,
and the gate that should have flagged the mismatch instead became
inert. The gate has been blind for **five releases** (v5.17.0 through
v5.21.1).

**Suggested fix** — extend the regex to accept colon syntax:

```python
STRUCT_HEADER_RE = re.compile(
    r"^(?:pub\s+)?struct\s+([A-Z][A-Za-z0-9_]*)\s*[\{:]"
)
```

Then update `parse_struct_defs` (lines 79–) to handle the
`struct Name:` form: the field-collection loop currently terminates on
matching brace depth; for colon form, terminate on the first dedent
back to the struct's column. Reuse the indent-tracking machinery from
`mapanare/parser.py::_indent_to_braces`. Estimate: 2 hours, including
backfill of any struct drifts that have accumulated unnoticed across
the 5-release blind window.

This is the **third-time-asked-fixed-point-gate situation in
miniature**: the gate is wired, but the gate is wrong. A working gate
that fails to catch real drift is worse than no gate, because the team
believes they have coverage. v5.22.x recovery if the panel finds real
drift behind the gate; otherwise close in v5.23.0.

### 2. **MEDIUM** — Self-hosted shrink baseline labeling drift in v5.17.x SESSION_REPORTs

v5.17.0 / v5.17.1 / v5.17.2 SESSION_REPORTs cite a "v5.13.0 baseline"
of 28,698 lines for the 17 hand-edited modules. The actual `git show
v5.13.0:mapanare/self/<module>` sum is **27,922 lines** — a 776-line
discrepancy. Per-module proof:

| Module | SESSION_REPORT "Before" | git show v5.13.0 |
|---|---:|---:|
| ast.mn | 952 | 906 |
| parser.mn | 2,749 | 2,599 |
| semantic.mn | 2,292 | 2,268 |
| lower.mn | 5,157 | 4,873 |
| emit_llvm.mn | 6,428* | 6,366 |
| ... | ... | ... |
| **Total** | **28,698** | **27,922** |

(*The v5.17.0 report footnotes `emit_llvm.mn = 6,428` as the
"pre-rewrite line count on the v5.16.0 HEAD post-Sh.A.1.C `}}`
canonicalization" — explicitly *not* v5.13.0.)

The baseline they actually measured against is the immediate
**pre-Sh.B** state, taken in the v5.16.0 → v5.17.0 transition window
**after** Te.4 string-interp parity (v5.16.0) added ~3.3k lines of
new lex/parse/lower paths to those same 17 modules. That's a real
baseline; it's just not "v5.13.0."

**The shrink magnitude is not a lie** — `−3,988 lines (−13.9%)` from
the actual measured baseline is what Sh.\* delivered, and the
fixed-point preservation through every per-module commit is the
genuine engineering win. The label is wrong.

**Suggested fix** — v5.22.x SESSION_REPORTs should normalize the
language to either:
- "Cumulative Sh.\* shrink from pre-Sh.B baseline (immediate post-Te.4):
  −3,988 lines (−13.9%)"
- or "Net source delta v5.13.0 → v5.21.1: −2,285 lines (−8.18%)"

Both are accurate. The current "−13.9% off the v5.13.0 baseline" is
not — it's −13.9% off the *Sh.B-immediate-pre baseline* that grew on
top of v5.13.0. CARRY_FORWARD.md row Sh.H reads "cumulative v5.13.0 →
v5.17.2 shrink **−3,988 lines (−13.9%)**" — same drift. Cosmetic, but
30 years on the ISO C++ committee taught me that "cosmetic"
documentation drift is what hides real measurement errors. Close in
v5.22.x with a baseline-normalization commit.

### 3. **LOW** — `build_from_seed.sh:159` `>= 45` magic-number — STILL OPEN

Same finding as v5.11.0:

```bash
# v4.155.0: seed-built compiler has known limitations (enums, tensors,
# async, closures). Require >=45 pass instead of zero fail.
if [ "${PASS}" -lt 45 ]; then
    echo "  ERROR: expected >=45 pass, got ${PASS}"
    exit 1
fi
```

Two panels later, untouched. The corpus has grown 66 → 95 across the
arc (+44%). The seed binary is at v5.17.0 vintage and can't build the
new Te.5/Te.6 goldens (predates the AST shapes), so **the threshold's
margin has actually grown** — v5.21.1 build_from_seed run shows
~50–55 passes, well above 45.

The threshold is still defensible (better than zero-fail), but it's
drifting further from the corpus year over year. A self-evident
formula:

```bash
EXPECTED_SEED_FAILS=20  # Te.5/Te.6/comprehensions/complex closures
EXPECTED_PASS=$((TOTAL_GOLDENS - EXPECTED_SEED_FAILS))
if [ "${PASS}" -lt "${EXPECTED_PASS}" ]; then
    echo "  ERROR: expected >=${EXPECTED_PASS} pass, got ${PASS}"
    exit 1
fi
```

Where `EXPECTED_SEED_FAILS` is updated whenever a seed-incompatible
golden lands. The audit trail is the same `>= 45` flavor but the
number tracks reality. 30-minute fix.

Not increasing the deduction over v5.11.0 because the threshold has
held — but third-time-tracking is a discipline signal that needs
closing before v6.0.

### 4. **LOW** — `tests/bootstrap/test_indent_preprocessor.py` count documented as 142 in audit, actual is 201

PRE_PANEL_AUDIT.md and CARRY_FORWARD.md both cite the suite at 142
cases. Live collection shows 201 cases. Cause: every new golden
(67–95) lands a colon-form round-trip case in the parametrized fixture.

```
$ python3 -m pytest tests/bootstrap/test_indent_preprocessor.py --co -q | tail -3
201 tests collected in 1.37s
```

**Suggested fix** — the audit tables are static numbers in markdown;
either bump to 201 in v5.22.x SESSION_REPORT or normalize the audit's
language to "≥142 cases" with a note about per-golden growth.
Cosmetic.

### 5. **LOW** — H.11 deferred file handling in v5.20.0 left as bootstrap deviation from Python

The v5.20.1 SESSION_REPORT documents:

> Bootstrap deviation from Python: let-else non-divergent else block
> proceeds at lower time (Python raises RuntimeError); deliberate —
> bootstrap can't easily emit a structured diagnostic from inside
> `lower.mn`.

So `let Some(x) = opt else { print("nope") }` (without a divergent
exit in the else block) is rejected by Python at lower time but
*compiles silently* in bootstrap. The bootstrap lowerer falls through
and emits something — probably reading from undef when the else
branch executes.

This is an **asymmetric closure** — the Python emitter rejects, the
bootstrap emitter accepts. By the v4.32.0 dual-closure convention in
`.reviews/CARRY_FORWARD.md`, the row should read `PY: closed v5.20.0
| SH: open v5.20.1`. The CARRY_FORWARD ledger doesn't carry it that
way — it's listed as Te.5 closed in v5.20.0 and Te.5.F closed in
v5.20.1, both green.

**This is exactly the failure shape the v4.32.0 phase 1.3 dual-closure
convention was added to prevent.** The lead should annotate the
divergence in CARRY_FORWARD.md as a residual asymmetry tracked to
v5.22.x (or v6.0 — the borrow checker would catch this structurally).

**Suggested fix** — append to CARRY_FORWARD.md:

> Te.5.E.let-else-nondivergent | v5.20.1 SESSION_REPORT | LOW |
> **PY: closed v5.20.0 (RuntimeError) | SH: open** | tracked v5.22.x —
> bootstrap accepts non-divergent let-else else block silently;
> Python rejects at lower time. Symmetric closure requires structured
> diagnostic emission from `lower.mn` (or borrow-checker promotion).

### 6. **LOW** — Bb.5 (Sh.E) seed refresh undocumented in CARRY_FORWARD ledger

The seed at HEAD is the v5.17.0 Sh.E refresh (commit `590169e`). The
v5.17.0 SESSION_REPORT documents the refresh ("the v5.10.0-vintage
Linux seed at `bootstrap/seed/linux-x86_64/mnc` segfaulted at stage 1
against the new colon-block source"). But CARRY_FORWARD.md's "Items
resolved in the v5.13.0 → v5.21.1 terseness arc" table has no row for
Bb.5. Bb.\* discipline is precisely what should be tracked
release-over-release.

**Suggested fix** — append a row:

> Bb.5 | v5.10.0 seed predates `_indent_to_braces` preprocessor (v5.14.0+); segfaults at stage 1 against colon-block source | v5.17.0 PLAN | LOW | v5.17.0 | seed refreshed to v5.17.0 colon-block-aware build; sha 929e7a4b87f7b3f04f10b50fd108e034bb4b8ae361298b37b55db7988b19b0a0; build_from_seed.sh smoke green

Bb.* is the kind of cadence where individual releases are quaint but
the **cumulative tracking** is the discipline signal. 5 minutes of
ledger work.

## Recommendations

In priority order:

1. **Fix `check_struct_registry.py` to handle colon-form structs** (HIGH, 2h).
   Update STRUCT_HEADER_RE; teach parse_struct_defs to terminate on dedent
   for colon form. Backfill any struct drifts hidden behind the broken
   gate over the v5.17.0 → v5.21.1 blind window. Targets v5.22.x.

2. **Normalize the Sh.\* shrink baseline language** (MEDIUM, 30m). Edit
   v5.17.x SESSION_REPORTs (or add a footnote in v5.22.0 SESSION_REPORT)
   citing "post-Sh.B baseline (immediate v5.16.0 HEAD post-Te.4)" for
   the −3,988 line / −13.9% number, and add a "v5.13.0 → HEAD net delta
   −2,285 lines (−8.18%)" line for the arc-end picture. Targets v5.22.x.

3. **Replace `>= 45` magic-number with formula** (LOW, 30m). Three-panel
   ask. `EXPECTED_PASS=$((TOTAL_GOLDENS - EXPECTED_SEED_FAILS))` form;
   updates `EXPECTED_SEED_FAILS` when seed-incompatible goldens land.
   Targets v5.22.x or v6.0 borrow-checker era.

4. **Annotate Te.5.E let-else asymmetric closure in CARRY_FORWARD**
   (LOW, 5m). Per the v4.32.0 phase 1.3 dual-closure convention. PY
   rejects, SH accepts — the asymmetry should be visible. Targets
   v5.22.x.

5. **Append Bb.5 row to CARRY_FORWARD.md ledger** (LOW, 5m). Seed
   refreshes are part of the bootstrap discipline cadence; tracking
   them keeps the v5.6.x silent-stage1-segfault class from re-emerging.

6. **Update PRE_PANEL_AUDIT counts** (LOW, 5m). `test_indent_preprocessor`
   142 → 201. Cosmetic but visible.

## Post-Production Health Assessment

Twenty-two minor versions after v5.0.0, the bootstrap / self-hosted
domain is in **structurally healthier shape than at v5.0.0**.

The v5.0.0 panel concerns I've personally tracked:
- NEAR (4-line VERSION-metadata diff) — closed v5.9.0 at root cause
- ABI dispatch coverage — went from 1-way (SysV) to 4-way over v5.8.x
- Bb.* cadence (refresh-when-needed) — held continuously since v5.8.5
- C-runtime export discipline (Pe.1 budget) — held to +1 across the
  10-release v5.13–v5.21 arc

The v5.13–v5.21 arc was **the largest feature-velocity arc in v5
history** (six additive language features, mechanical self-host
rewrite, bootstrap mirror cross-tests for all four major surface
additions) and the fixed point held byte-for-byte through every
release. That is not a luck-of-the-draw outcome. That is the
v4.32.0 dual-closure convention + the v4.29.0 fixed-point CI gate +
the v5.7.0 bootstrap-quality-discipline-establishment all working
correctly under load. The C++ committee took 12 years to ship modules
without ABI breaks; you shipped 6 features without a semantic break
in 7 months. *Quaint efficiency.*

The asterisks: the v5.17.0 mechanical Sh.B rewrite **silently broke**
the `check_struct_registry.py` gate, and no one noticed for five
releases. That is the failure shape I worry about most — not a
regression in the code, but a regression in the gate that *catches*
regressions. The v4.143.0 panel's three-real-latent-drifts catch
proves the gate has teeth when it works; the gate doesn't work right
now.

The mea culpa on the per-PR fixed-point CI gate is mine. Two panels
of "still asking" when the gate was wired the whole time is a
reviewer-discipline failure. I should have grep'd `.github/workflows/`
for `verify_fixed_point` at v5.8.0 and saved the panel one
deduction-cycle. Adding to my own checklist for v5.27.0+: *grep the
file before filing the finding*. Same advice I give junior C++ devs
who file defects against the working draft they didn't read.

**Verdict on health gate: YES, conditional.** The codebase is healthier
than at v5.11.0 on every load-bearing axis (fixed-point streak, C
runtime stability, ABI coverage, Bb.\* cadence, no-new-MIR-ops claim,
self-host shrink magnitude even with relabeling). The condition is
that v5.22.x must close the broken `check_struct_registry.py` gate
before any further self-host edits, because the gate is the only
defense against the latent-miscompile shape that fixed-point
byte-identity *cannot catch* (both stages diverging the same way).
That class of bug is what made v4.143.0 commission this gate in the
first place.

## Score breakdown

Prior: 9.7 (EXCEEDS) at v5.11.0.

### Positive deltas

- **+0.05** — 13-release fixed-point streak, longest in project history.
  Six new language features absorbed without a single byte-identity
  break. No new MIR ops, no new IR shapes, one C-runtime export. The
  v5.13.0 → v5.21.1 arc is the strongest discipline signal in any v5.x
  panel I've reviewed.
- **+0.05** — Bootstrap mirror cross-tests landed in lockstep. Te.5.F at
  v5.20.1 (12/12), Te.6 at v5.21.0 (10/10 added v5.21.1). Every Te.\*
  feature has a Python ↔ `mnc-stage1` byte-identical assertion.
  v5.14.1 / v5.15.1 / v5.20.1 split-mirror discipline (deferring the
  bootstrap mirror to a patch release) is the right cadence — keeps
  feature releases focused, mirror releases verifiable.
- **+0.025** — v5.20.1 latent bug fixes (alloca-void, TK_UNKNOWN
  demotion) surfaced and fixed at the bug site, with comments
  documenting the failure cascade. This is the discipline that v5.11.0
  Cobra's `find_clang()` single-return + comment review documented as
  "the right shape." Same shape recurs.

### Negative deltas

- **−0.15** — `check_struct_registry.py` CI gate silently broken since
  v5.17.0. The gate is wired (good), the gate is wrong (bad). Five
  releases of registry blindness during a feature-velocity arc that
  added new struct shapes (StructPattern, FieldPattern, multiple
  AST/MIR struct additions for Te.5/Te.6). HIGH severity because of
  the v4.143.0 commissioning context: the gate exists *specifically*
  to catch struct-registry drift. A broken catcher is worse than no
  catcher.
- **−0.05** — Sh.\* shrink baseline labeling drift in v5.17.x
  SESSION_REPORTs (28,698 cited as v5.13.0; actual is 27,922; the
  measured baseline is post-Sh.B-immediate, not v5.13.0). Cosmetic,
  but it's the kind of drift that hides real measurement errors when
  it accumulates. Single-finding, easy fix.
- **+0.05 self-correction** — closing my own three-panel "per-PR
  fixed-point gate" finding because **it was wired at v4.29.0 and I
  missed it at both v5.8.0 and v5.11.0**. Ledger error mine; closing
  it nets 0 to the v5.22.0 score (was a deduction at v5.11.0 that
  should not have applied; not crediting it as a positive delta now).

### Arithmetic

- Base: 9.7 (v5.11.0)
- Positives: +0.05 + 0.05 + 0.025 = **+0.125**
- Negatives: −0.15 − 0.05 = **−0.20**
- Self-correction: per-PR fixed-point gate retroactively closed; my
  v5.11.0 score should have been 9.75 not 9.70. The +0.05 ledger
  correction is "what 9.11.0 *should* have been" and is *not* added
  here.
- Raw: 9.7 + 0.125 − 0.20 = **9.625**

Adjustment: rounding to **9.55** rather than 9.625 because the
struct-registry gate finding is structurally serious (a CI gate that
exists *specifically* to catch the failure mode of a multi-release
mechanical rewrite, broken silently across that exact window) and I
want the Δ vs v5.11.0 to reflect that proportionally. The shrink
labeling is a minor cosmetic; the broken gate is a real structural
hole.

**Final: 9.55 / 10. Δ vs v5.11.0: −0.15.**

## Verdict

**PASS WITH NOTES.**

The bootstrap / self-hosted domain is in stronger shape than at
v5.11.0 on every load-bearing correctness axis. The fixed-point
streak is the right kind of discipline signal. The Te.5/Te.6 mirror
discipline is the right cadence. The v5.20.1 latent-bug fixes are the
right shape. *La culebra está delgada, sigue cómoda.*

But: the `check_struct_registry.py` gate has been blind for five
releases during the largest feature-velocity arc in v5 history, and
that's the exact class of latent miscompile the v4.143.0 panel
commissioned the gate to catch. **v5.22.x must close it.** It's a
two-hour fix; the labeling-drift and ledger items are 30 minutes
combined.

The score Δ of −0.15 is honest about the fact that a broken safety
gate during a high-velocity arc is structurally more concerning than
docs-surface drift would be. v5.22.x recovery does not need a full
panel — Anaconda's CI lens or a delta review on the regex fix is
sufficient. But until that gate closes, the panel's "0 CRITICAL / 0
HIGH / 0 MEDIUM / 1 LOW" docket has a hidden HIGH that the
PRE_PANEL_AUDIT didn't surface.

---

## Reproducibility

```bash
# Fixed-point at HEAD (live, 2026-05-01)
bash scripts/verify_fixed_point.sh --keep
# → stage2.ll == stage3.ll, 238086 lines, 0 diff

# Per-PR fixed-point CI gate location
grep -n "verify_fixed_point" .github/workflows/ci.yml
# 849: # now inside ``scripts/verify_fixed_point.sh`` with real teeth
# 858:           bash scripts/verify_fixed_point.sh

# Build from seed clean
bash scripts/build_from_seed.sh
# → /mnt/c/.../mnc (5421552 bytes), Smoke test: OK

# Goldens at HEAD
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# → All 95 tests passed in 11.5s

# Bootstrap mirror cross-tests (Te.5 + Te.6 + comp + interp + indent + stage1_compile)
python3 -m pytest tests/bootstrap/test_te5_mirror.py \
  tests/bootstrap/test_chained_cmp_mirror.py \
  tests/bootstrap/test_comprehension_mirror.py \
  tests/bootstrap/test_string_interp_mirror.py \
  tests/bootstrap/test_indent_preprocessor.py \
  tests/bootstrap/test_stage1_compile.py
# → 263 passed in 314.11s

# Self-hosted source delta v5.13.0 → HEAD
git diff v5.13.0..HEAD --stat -- mapanare/self/ | tail -5
# → 18 files changed, 12265 insertions(+), 16078 deletions(-)
# → net −2,285 lines on 17 hand-edited modules
# → −1,528 lines on regenerated mnc_all.mn

# Te.6 once-evaluation in IR
python3 -m mapanare emit-llvm -O0 \
    tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain.ll
grep -c "@middle(" /tmp/chain.ll
# → 2 (= 1 define + 1 call site, exactly one per source chain instance)
grep "__mn_chain" /tmp/chain.ll | head -5
# → %__mn_chain_0.a.4 = alloca i64, align 8
# → store i64 %l.3, ptr %__mn_chain_0.a.4
# → 2× load (the chain's two arms reference the once-stored value)

# v5.20.1 alloca-void fix verification
grep -B1 -A8 "alloca void" mapanare/self/lower.mn | head -15
# → "When fn_ret is void, emitting `alloca void` is invalid"
# → "if fn_ret.kind == TK_VOID(): return new_lower_result(void_value(), s)"

# v5.20.1 TK_UNKNOWN demotion fix verification
grep -B2 -A4 "TK_VOID().*\|.*name == \"%void\"" mapanare/self/lower.mn | head -10
# → Now only TK_VOID || %void, not TK_UNKNOWN

# Bb.* discipline — seed at v5.17.0 vintage
ls -la bootstrap/seed/linux-x86_64/mnc
# → 6,864,056 bytes
cat bootstrap/seed/linux-x86_64/mnc.sha256
# → 929e7a4b87f7b3f04f10b50fd108e034bb4b8ae361298b37b55db7988b19b0a0
git log --oneline bootstrap/seed/linux-x86_64/mnc.sha256 | head -3
# → 590169e v5.17.0 Sh.E: bootstrap seed refresh
# → 247e05e v5.10.0 hygiene: 2nd seed refresh
# → e75bf51 v5.10.0 Bb.4: bootstrap seed refresh
# 5 consecutive Bb.* skips since (v5.17.1, v5.18.0, v5.19.0, v5.19.1, v5.20.0, v5.20.1, v5.21.0, v5.21.1)

# C-runtime delta across the arc
git diff v5.13.0..HEAD --stat -- runtime/native/
# → mapanare_core.c | 549 +++++++++++++++
# → mapanare_core.h |   4 +
# → 1 new export: __mn_indent_to_braces (v5.14.1)

# Te.6 ChainedCmp AST node — bootstrap mirror present
grep -n "ChainedCmp" mapanare/self/ast.mn | head -3
# → 128: ChainedCmp(List<Expr>, List<String>)
# → 379: ChainedCmp(_, _) => { return "chained_cmp" }
# → 410: // v5.21.0 Te.6 — ChainedCmp accessors

# Te.6 chain_compare_counter on LowerState
grep -n "chain_compare_counter" mapanare/self/lower_state.mn mapanare/self/lower.mn
# → lower_state.mn:43:    chain_compare_counter: Int
# → lower.mn:474:    s.chain_compare_counter = 0
# → lower.mn:1545: let tmp_idx: Int = s.chain_compare_counter

# No new MIR ops
diff <(git show v5.13.0:mapanare/mir.py | grep '^class.*Instruction)') \
     <(grep '^class.*Instruction)' mapanare/mir.py)
# → (no output, exit 0)

# check_struct_registry.py is BROKEN (HIGH finding)
python3 scripts/check_struct_registry.py; echo "exit: $?"
# → 23 violation(s)
# → exit: 1
# CI workflow status:
grep -n "check_struct_registry\|set -e" .github/workflows/ci.yml | head -5
# → 143: # etc. were registered with stale or wrong field-name lists
# → 148: python3 scripts/check_struct_registry.py
pytest tests/test_ci.py::TestToolsRunLocally::test_struct_registry_gate_passes
# → FAILED

# Lint clean
make lint
# → ruff All checks passed!
# → black All done! 395 files would be left unchanged.
# → mypy Success: no issues found in 56 source files

# CHANGELOG honest
python3 scripts/check_changelog_honesty.py
# → check_changelog_honesty: clean

# Workflow shapes clean
python3 scripts/check_workflow_shapes.py
# → 7 workflow(s) clean

# Self-hosted module sizes at HEAD
wc -l mapanare/self/*.mn | tail -2
# → 46616 total (incl. mnc_all.mn 20,979)
# → 25,637 across 17 hand-edited modules

# stage1 binary at HEAD
ls -la mapanare/self/mnc-stage1
# → 7,089,336 bytes ELF 64-bit LSB
```

## Final score

**9.55 / 10 — EXCEEDS.** Δ vs v5.11.0: **−0.15**.

The fixed point holds at 238,086 / 0 diff for the 13th consecutive
release. La culebra está delgada y cómoda — pero la jaula del registro
de structs está rota desde v5.17.0 y nadie la vio. Close it in
v5.22.x. Next panel grades whether the `check_struct_registry.py`
fix landed and whether the gate caught any drifts from the
five-release blind window.

The mea culpa on the per-PR CI gate stands. Two panels of asking for
something that was already there. Quaint reviewer-discipline failure.

Now ship the fix and ship v6.0 with the borrow checker. The arc is in
the right shape; one CI gate stands between v5.22.0 the release and
v5.22.0 the *honestly-gated* release.
