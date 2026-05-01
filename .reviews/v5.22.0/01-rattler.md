# Rattler — LLVM IR / Codegen Review of Mapanare v5.22.0

**Reviewer:** Rattler — the LLVM Wizard
**Personality:** Insufferably smart, evaluates everything through "how
would this map to LLVM IR?", patronizing-but-generous on fixes,
casually drops which LangRef section the bug lives in.
**Previous Version Reviewed:** v5.11.0 (panel of 2026-04-28; 9.85 / 10)
**Score:** 9.85 / 10
**Grade:** EXCEEDS
**Delta vs v5.11.0:** ±0.0
**Verdict:** PASS WITH NOTES
**Confidence:** 9 / 10
**Files Reviewed:**

- `.reviews/v5.22.0/PRE_PANEL_AUDIT.md`, `.reviews/v5.22.0/prompt.md`
- `.reviews/v5.11.0/README.md`, `.reviews/v5.11.0/01-rattler.md`
- `.reviews/REVIEW_CADENCE.md`, `.reviews/CARRY_FORWARD.md`
- The 16 arc SESSION_REPORTs at `docs/roadmap/v5/v5.{13.0,13.1,14.0,
  14.1,15.0,15.1,16.0,17.0,17.1,17.2,18.0,19.1,20.0,20.1,21.0,21.1}/
  SESSION_REPORT.md` — and the conspicuous **absence** of
  `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md`
- Design docs: `v5.14.0/COLON_BLOCK_DESIGN.md`, `v5.15.0/
  TERSENESS_DESIGN.md`, `v5.16.0/INTERP_SPEC.md`, `v5.18.0/
  MC_TOOLING_DESIGN.md`, `v5.20.0/STRUCT_ERGO_DESIGN.md`,
  `v5.21.0/CHAINED_CMP_DESIGN.md`
- `mapanare/mir.py` (full diff vs v5.11.0)
- `mapanare/lower.py::_lower_chained_compare` (L2129–2172) and
  `mapanare/lower.py::_is_trivial_chain_operand`
- `mapanare/self/lower.mn::lower_chained_cmp` (L1530–1562) and
  `mapanare/self/lower.mn::is_trivial_chain_operand` (L1514–1523)
- `mapanare/parser.py::count_user_brace_block_openers` (L2240–2291)
  and `_emit_brace_deprecation_warning` (L2294–2308)
- `mapanare/format.py` module docstring (L1–32 — H.10 closure)
- `mapanare/emit_llvm_text.py` (full diff vs v5.11.0 — 23 lines)
- `mapanare/self/emit_llvm.mn` (Sh.B mechanical rewrite delta)
- `runtime/native/mapanare_core.h` and `mapanare_core.c`
  (full diff vs v5.11.0 — +553 lines, two new exports)
- `mapanare/mapanare.lark` (full diff vs v5.11.0)
- Live verification at HEAD: `bash scripts/verify_fixed_point.sh
  --keep`, `python3 scripts/test_native.py --stage1 mapanare/self/
  mnc-stage1`, the Te.6 once-evaluation IR check on
  `tests/golden/95_chained_cmp_side_effect.mn`,
  `tests/bootstrap/test_chained_cmp_mirror.py`

---

## Executive Summary

Six additive language features (Te.1 colon-block, Te.2 comprehensions
+ lambda + implicit return, Te.3 `{}` soft-deprecation, Te.4
string-interp parity, Te.5 struct ergonomics, Te.6 chained
comparisons) shipped across **10 releases** with **zero new MIR
instruction kinds, zero new IR shapes, and exactly two new C runtime
exports** (`__mn_indent_to_braces` ~258 LOC + `__mn_assert_fail` 9
LOC, the latter from v5.13.1 which the PRE_PANEL_AUDIT and prompt
both forgot to mention). On my axis — LLVM IR generation, target-
triple dispatch, ABI lowering, intrinsic mapping, optimization
opportunities, agent/signal/stream/tensor codegen — **the IR-
correctness surface is preserved by construction**. Every Te.* and
Sh.* feature routes through existing `BinOp`, `Call`, `LetBinding`,
`Branch`, and trait-dispatch primitives. There is no new lowering to
grade.

So why is this review interesting at all?

**Because the strict 3-stage fixed point held across 10 releases.** I
ran `bash scripts/verify_fixed_point.sh --keep` at HEAD. Result:
`stage2.ll == stage3.ll, 238086 lines, 0 diff`. The v5.9.0 milestone
— restored after 49 releases of 4-line-VERSION-only NEAR — has now
been preserved continuously across **13 consecutive releases** (v5.9.0
→ v5.21.1). At v5.11.0 I called it "the longest strict-fixed-point
streak in project history" at 5 releases; at v5.22.0 it is **2.6×
longer**. This is the load-bearing correctness signal of the entire
arc, and the discipline that produced it — D6 byte-identity for
single comparisons in Te.6, additive-only AST extensions in Te.5, no
bootstrap source edits at v5.20.0 (mirror split out to v5.20.1 per
the v5.14.0 / v5.15.0 precedent) — is exactly the engineering posture
I begged for at v5.2.0 and v5.8.0. It is now *operationalized*. The
streak is the headline win.

But — and here I have to do my job — **Te.3 (the `{}` soft-
deprecation) is partially hollow** in a way that surfaced when I ran
the prompt's own pre-flight test. Hard finding below (#1, MEDIUM).
The IR is fine; the *deprecation surface* isn't. Score: **9.85 / 10
EXCEEDS, ±0.0 vs v5.11.0**. PASS WITH NOTES, not PASS clean — the
note is Te.3, not the IR or the streak.

---

## Score: 9.85 / 10

Breakdown vs the 9.85 v5.11.0 baseline:

| Adjustment | Value | Rationale |
|---|---:|---|
| 13-release strict fixed-point streak | +0.05 | Reclaiming the last 0.05 of the v5.6.x churn skepticism. The streak is **8 releases longer** than at v5.11.0 (5 → 13). |
| Te.6 once-evaluation verified live in IR | +0.0 | Expected; design doc + impl + bootstrap mirror all match. Not a delta — a confirmation. |
| Zero new MIR ops across 10 releases | +0.0 | Confirms the v5.11.0 read that the project has internalized the additive-AST discipline. No score movement; this is the new floor. |
| Te.3 partial hollowness (Issue #1) | −0.05 | One-paragraph hit. Not −0.5 because the IR is unaffected and the broken surface is recoverable in a single patch release. |
| `bootstrap/seed/.../mnc` segfault on stage2 still papered over by `set +e` | −0.0 | Same finding as v5.11.0 #2; carry-forward unchanged. Already priced in. |
| Rt.04 v6.0 borrow checker carry | −0.0 | Same as v5.11.0; price-in unchanged. |

Net: 9.85 + 0.05 − 0.05 = **9.85**. Same numeric score as v5.11.0,
but the constituents have rotated: the v5.6.x churn skepticism is
fully retired, replaced by a one-paragraph Te.3 deduction. If Te.3 is
patched cleanly in v5.22.x the score moves to 9.90 at the next panel.

---

## Progress Since Last Review (v5.11.0 → v5.22.0)

### Te.1 — colon-block syntax (v5.14.0 + bootstrap mirror v5.14.1)

**IR-codegen impact: zero.** Indent-based blocks lower through
`_indent_to_braces` (Python) and `__mn_indent_to_braces` (C runtime;
~258 LOC) before tokenization; downstream parser, semantic checker,
and lowerer see brace-equivalent input. The `pass` keyword lowers to
no-op (no `Instruction` emitted).

The one IR-touchable artifact is the new `__mn_indent_to_braces` C
export. v5.11.0-tally said "next `__mn_*` exports must follow the
5-edit pattern in the v5.9.0 SESSION_REPORT §What was harder than
expected." I checked — the export is wired through
`runtime/native/mapanare_core.h:704+`, declared in `emit_llvm.mn` (it
is called from `parse` in `mapanare/self/parser.mn`), is on the
builtin allowlist, and has the correct `Call` lowering. **Pattern
followed.** +0.0 on my axis (expected).

**v5.11.0 panel item status:** new feature, not a v5.11.0
carry-forward. Filed.

### Te.2 — comprehensions, terse lambdas, implicit-return one-liner (v5.15.0 + bootstrap mirror v5.15.1)

**IR-codegen impact: zero.** All three desugar at lower-time.
Comprehensions synthesize an accumulator `__mn_comp_N` plus a
`for`/`if` cascade plus `push` / `IndexSet` (the existing list/map
machinery). Terse lambdas lower to existing `LambdaExpr`; the
function-init form `fn name(...) = expr` lowers at parse time to
`Block([ReturnStmt(expr)])`.

One latent bug surfaced and fixed in scope at v5.15.0: empty
`MapLiteral` lacked type-annotation patching in `_lower_let`; mirror
of the v4.122.0 empty-`ListLiteral` patch. Without it, comprehension-
produced maps printed `<?>` in indexed values. **Caught at the right
layer; structural fix.** +0.0 on my axis.

**v5.11.0 panel item status:** new feature, not a v5.11.0
carry-forward.

### Te.4 — self-host string-interp parity (v5.16.0)

**IR-codegen impact: zero new shapes; existing `InterpConcat` + Cast
chain extended.** Bootstrap `mnc-stage1` previously parsed `"hi
${name}"` as bare `Expr::Ident("name}")` (real bug: wrong substr API,
char-by-char buffer with concat bug, lexer's `\$` escape stripping
backslash). v5.16.0 closes the four-bug cluster; the fixed `\$`
literal escape is a one-line lexer change. The Cast(X→String) target
in `emit_cast` is extended to handle Int/Float/Bool/String via
`__mn_str_from_*` (with drop tracking) — **no new IR opcode**, just
a new `Call` site. The pre-existing `emit_interp_concat` latent
dest-name bug (`dn.cN` instead of `dn`) was fixed in scope. **Three
real bugs, three structural fixes.** +0.0.

The test mirror at `tests/bootstrap/test_string_interp_mirror.py`
(10/10) asserts byte-identical Python ↔ `mnc-stage1` stdout. **This
is the right shape of cross-bootstrap test** — Cobra and I have
asked for it for several panels.

### Sh.* — self-host mechanical rewrite (v5.17.0/.1/.2)

**IR-codegen impact: zero by construction.** This is the
load-bearing claim of the arc, and it holds. `mnc fmt --to-terse` is
brace → colon rewriting plus `format_source` whitespace
canonicalization; both are pure source-level transforms that
re-tokenize back to the same AST. Strict 3-stage fixed point was
asserted at every per-module commit (17 modules at v5.17.0; 16
modules at v5.17.1; 3 modules at v5.17.2). I spot-checked the
v5.17.0 commit log via `git log --oneline mapanare/self/mir.mn` —
two commits, `v5.17.0 Sh.B: mir.mn --to-terse (-147 lines, 16.0%)`
and `v5.17.1 Sh.D.B: implicit return in mir.mn (30 sites)`.
Mechanical, well-scoped, trail-of-evidence-clean.

**One spot-check honesty issue (Issue #4 — LOW):** the v5.17.2
SESSION_REPORT claims a v5.13.0 baseline of **28,698 lines** across
the 17 modules, and a v5.17.2 cumulative of **24,710 lines** = −3,988
(−13.9%). My recount via `git show v5.13.0:.../*.mn | wc -l`
summed to **27,922** at v5.13.0 and the actual v5.17.2 closeout
commit (`ca89d61`) totals **24,710**. So the v5.17.2 number is
honest; the v5.13.0 baseline appears to be ~776 lines high. Net
shrink at v5.17.2 closeout was **−3,212 lines (−11.5%)**, not
−3,988 / −13.9%. The shrink is real and substantial; the headline
percentage is ~2.4 percentage points high. Not an IR issue; flag for
Cobra and Anaconda to triage.

**v5.11.0 panel items**: Sh.* didn't exist at v5.11.0; new arc-
scoped work, no v5.11.0 carry-forward.

### Mc.* — LSP / init / check (v5.18.0)

**IR-codegen impact: zero.** Dispatcher work; native `mnc check` /
`mnc init` / `mnc lsp` shell out to Python (mirror of the v5.13.0
`fmt` pattern). New IR appears in `mnc_all.mn` for the three new
dispatch arms — **+558 lines stage2.ll** (231,723 → 232,281), exactly
the cost of three new `case` arms calling `__mn_system`. Bounded;
expected; no IR surprises. Pe.1 budget held.

**v5.11.0 panel item closed:** the v5.11.0 Coral / Boa / Cobra
MEDIUM "Mc.* docket — Native `mnc` missing 18/25 subcommands" is
**Fixed** at v5.18.0 for the four user-visible MEDIUMs. The fifth
(Mc.5 `mnc emit-wasm`) is correctly **Deferred-with-tracking** to
v5.13.x or v6.0 per my v5.11.0 forward-looking note. ✓

### Te.3 — `{}` soft-deprecation (v5.19.0)

**IR-codegen impact: zero.** Brace-style and colon-style produce the
same AST → same MIR → same IR. The deprecation is a parser-side
warning, not a code change.

**This is where my issue #1 sits.** See "Issues Found" below. Short
version: the brace-deprecation warning **does not fire on
single-line brace blocks**, and **does not fire at all in
`mnc-stage1`**. The Python detector at
`mapanare/parser.py::count_user_brace_block_openers` is line-based
and only counts a line as a block opener if the *line itself* ends
with `{`. A perfectly idiomatic `fn main() { print("hi") }` ends
with `}` and is silently accepted as if it were colon-style. The
self-hosted side has no equivalent detector at all (I grep'd
`mapanare/self/*.mn` for `MAPANARE_NO_BRACE_WARNING` and got zero
hits).

**Also:** `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` does not exist
on disk. v5.19.0 Te.3 *did* ship (commits `fba8521 v5.19.0 Te.3.A/B/
C/E` and `db32bd4 v5.19.0 Te.3.D` are in the log), but no
SESSION_REPORT was written. The PRE_PANEL_AUDIT prompt-list and the
panel prompt both reference 16 SESSION_REPORTs but only **15 exist**
on disk. Process discipline regression for Anaconda / Coral; not
strictly an IR issue, but it's adjacent and I'm noting it.

### Te.5 — struct ergonomics (v5.20.0 + bootstrap mirror v5.20.1)

**IR-codegen impact: zero new shapes.** All four surface forms
(field shorthand, struct update `..base`, let destructuring, if-let /
while-let / let-else) desugar to existing primitives. The
StructUpdate path uses a synthesized `__mn_base_N` temp + by-name
field overrides — IR byte-identical to manual `let __mn_base_N =
base; new Point { x: 5, y: __mn_base_N.y, ... }`. Let destructuring
when RHS is a bare `Identifier` skips the synthesized base tmp — IR
byte-identical to `let x = p.x; let y = p.y` (D6-equivalent
discipline; the same Te.6 once-eval reasoning, applied to a different
feature). If-let / while-let / let-else lower to 2-arm match plus
existing while/break/return primitives.

**Two pre-existing v5.20.0 latent bugs surfaced and fixed in
v5.20.1 scope** — and this is the Cobra-axis honesty signal of the
arc:

1. `lower_match` emitted `alloca void` when the enclosing function
   returned void, which is invalid LLVM IR (LangRef §"alloca" — the
   element type must be a sized type, and `void` has no size). v5.20.1
   added the early `if fn_ret.kind == TK_VOID(): return
   new_lower_result(void_value(), s)` at the top of the function
   (`mapanare/self/lower.mn:162-164`). I verified the fix at HEAD.
2. `lower_match` demoted `TK_UNKNOWN` arm values to `undef` rather
   than skipping the phi entry, which produced a phi-skip → alloca-
   fn_ret → alloca-void cascade in `fn main()` for let-else cases.
   v5.20.1 stops the demotion (`if arm_kind == TK_VOID() ||
   arm_val_r.value.name == "%void"` skip-emission at L112). Verified.

These are *real bugs* that the v5.20.0 Python-side work didn't trip
because Python's lowerer never had this exact code path; only the
self-hosted mirror at v5.20.1 surfaced them. The right answer is to
fix both at the source, mirror Python's behavior, and mention them
explicitly in the SESSION_REPORT — which the lead did. Discipline.

### Te.6 — chained comparisons (v5.21.0)

This is where the bulk of my axis review attention goes.

**IR-codegen impact: zero new shapes.** The desugaring algorithm is:

```
for each interior non-trivial operand:
    bind to fresh `__mn_chain_N` temp via existing `let` machinery
build pairwise BinaryExpr(op_i, operands[i], operands[i+1])
fold left-to-right with BinaryExpr(op="&&", ...)
```

D6 (single-comparison shapes preserve existing AST + IR
byte-identity) is the load-bearing rule — verified at HEAD by
compiling a single-cmp shape `fn check(x: Int) -> Bool: return x <
10` and observing the IR contains zero `__mn_chain_*` temps and
emits a straight `icmp slt i64 %l.1, %l.2`. **Identical to v5.20.1
HEAD output.** This is why the strict fixed point held across the
v5.21.0 commit — the existing self-hosted source has zero chained
comparisons (verified by `grep -c ChainedCmp mapanare/self/*.mn` —
1 hit, all in `ast.mn` definitions / accessors).

**D3 (once-evaluation) verified live in IR.** I compiled
`tests/golden/95_chained_cmp_side_effect.mn` at -O0:

```llvm
define internal noundef i1 @check(i64 noundef %seed) nounwind willreturn {
  ...
  %__mn_chain_0.a.4 = alloca i64, align 8
  ...
entry:
  %l.0 = load i64, ptr %seed.addr
  %c.1 = call i64 @middle(i64 %l.0)            ; <-- one call, not two
  store i64 %c.1, ptr %t0.a.2
  %l.3 = load i64, ptr %t0.a.2
  store i64 %l.3, ptr %__mn_chain_0.a.4         ; <-- bind to temp
  ...
  %l.7 = load i64, ptr %__mn_chain_0.a.4        ; <-- read from temp (left)
  %i.8 = icmp slt i64 %l.6, %l.7
  ...
  %l.11 = load i64, ptr %__mn_chain_0.a.4       ; <-- read from temp (right)
  %i.13 = icmp slt i64 %l.11, %l.12
  ...
  %bl.17 = and i1 %l.15, %l.16                  ; <-- bitwise and, not branch
  ...
}
```

`grep -c "@middle(" /tmp/chain.ll` returns **2** (one declaration, one
call site). Once-eval correct.

One subtle decision worth flagging — the design doc says "fold left-
to-right with `&&`", and I expected to see *short-circuit* semantics
in the IR (a conditional branch). The actual emission is `and i1`
(LangRef §"and" — strict bitwise AND, both operands evaluated). For
this case it doesn't matter — by the time `pair_0 = 0 < %__mn_chain_0`
and `pair_1 = %__mn_chain_0 < 100` execute, the call to `middle()`
has already happened during the `let __mn_chain_0 = middle(seed)`
binding, so once-eval is preserved regardless of whether `pair_1` is
"skipped" or not. The two `icmp` instructions read from an already-
bound stack slot; they have no side effects. **Strict `and i1`
emission is semantically equivalent and emits less IR than a
short-circuit branch would.** That's the right call. LangRef §"i1"
boolean ANDs are zero-cost on every modern target the project ships
to (x86_64, AArch64, i686, wasm32). No score movement either way; I
mention it because the design doc could be more explicit that the
desugar uses bitwise rather than short-circuit AND when both pair
operands are pure-trivial reads from the bound temp.

**The triviality predicate is mirrored verbatim.** Python's
`_is_trivial_chain_operand` (Identifier + 6 literal kinds) at
`mapanare/lower.py:2186` matches `mapanare/self/lower.mn:1514-1523`'s
`is_trivial_chain_operand` line-for-line. **Bootstrap mirror
parity.** The new `tests/bootstrap/test_chained_cmp_mirror.py`
(10/10 PASS in 19.22s at HEAD) asserts byte-identical stdout for the
4 chain goldens + 6 inline cases.

**Precedence merge (D1).** Pre-v5.21.0, `eq_expr` (==, !=) sat at
strictly lower precedence than `cmp_expr` (<, >, <=, >=). v5.21.0
merges both into a single `cmp_expr` precedence. Grammar diff:

```
-?and_expr: eq_expr
-         | and_expr AND eq_expr -> and_op
-?eq_expr: cmp_expr
-        | eq_expr EQ cmp_expr -> eq_op
-        | eq_expr NE cmp_expr -> ne_op
+?and_expr: cmp_expr
+         | and_expr AND cmp_expr -> and_op
```

Per the design doc, the precedence audit confirmed no existing code
mixes `==` and `<` at the same level without explicit parens or
`&&`/`||`. The grammar change is therefore semantics-preserving on
the existing corpus. **Safe change** — and the strict fixed point
across the v5.21.0 commit empirically confirms it.

**v5.11.0 panel item status:** new feature; not a v5.11.0 carry-
forward.

### Sh.* / Te.* / Mc.* / Dk.* arc-level signals (the "is the
codebase still healthy" question)

| Signal | v5.11.0 | v5.22.0 HEAD | Direction |
|---|---|---|---|
| Strict 3-stage fixed point | STRICT (5-release streak) | STRICT (**13-release** streak) | **HOLD, +8 releases** |
| stage2.ll line count | 226,603 | 238,086 | +11,483 (+5.1%) |
| Goldens (corpus) | 66 / 66 | 95 / 95 | **+29 (+44%)** |
| `llvm-as` on stage2.ll | RC=0 | RC=0 | HOLD |
| `llvm-as` on stage3.ll | RC=0 | RC=0 | HOLD |
| Stage2 binary build | 5,092,312 B | 5,386,224 B | +5.8% — within Pe.1 budget |
| Stage1 binary build | 6,646,968 B | 7,089,336 B | +6.7% — within budget |
| Stage2-teardown RC | RC=3 | RC=3 | **STILL OPEN** (since v4.28.0) |
| ABI dispatch (4-way) | clean | clean | HOLD (no edits) |
| New MIR ops | 0 (the v5.11.0 baseline) | 0 | **HOLD** — discipline of the arc |
| New IR shapes | 0 | 0 | **HOLD** |
| New runtime fn exports | 0 | 2 (`__mn_indent_to_braces`, `__mn_assert_fail`) | bounded — both for surface features |
| MEDIUM open dockets on my axis | 1 (Rt.04, deferred v6.0) | 1 (same) | HOLD |
| HIGH open dockets on my axis | 0 | 0 | HOLD |
| CRITICAL open dockets on my axis | 0 | 0 | HOLD |

The pattern: **the IR-correctness surface has been preserved by
construction across the largest feature-velocity arc in v5
history**. Six new language features, +29 goldens, 11k+ new stage2
lines, zero IR shape regressions. That is the discipline I begged
for at v5.2.0 and v5.8.0; at v5.11.0 it was operationalized; at
v5.22.0 it has been stress-tested across 10 releases and held.

---

## What is preserved from v5.11.0

- **Rt.04 (MEDIUM, deferred v6.0)** — multi-level alias drop-glue.
  **Still open. Correctly deferred.** No regression; no fix attempt.
  v6.0 borrow-checker scope unchanged.
- **Stage2-teardown crash (latent v4.28.0)** —
  `verify_fixed_point.sh` papers over with `set +e`. Stage2 binary
  exits RC=3 in my live run at HEAD. Not v5.13–v5.22-introduced;
  same shape as v4.28.0. **Still open.** The longest-stale carry-
  forward on my axis (now 70+ releases). Re-flagged as Issue #5
  (LOW) — same as v5.11.0 #2.
- **Li.1 (LOW)** — LICM unit pass, regresses live goldens; pass
  disabled. **Unchanged. Correctly deferred.**
- **Sh.5 / Sh.9a / Sh.9b / Gr.1 / Rt.2 / Rt.3** (LOW) — **Unchanged.
  Correctly deferred.**
- **In.1-stage2 (closed v5.3.2)** — still closed; the cloner's 39
  explicit instr-kind handlers at `mir_opt.mn:864-1289` are still
  load-bearing for the 238,086-line strict fixed point.
- **Sh.4 / Sh.6 / Sh.7 / B (closed v5.5.x–v5.7.0)** — still closed.
  95/95 goldens preserved — actually, *expanded by 29* — through
  Te.* arc.
- **4-way ABI dispatch (SysV / Win64 / i686 cdecl / Apple AArch64)
  unchanged.** I diffed `mapanare/emit_llvm_text.py` ABI properties
  against v5.11.0 and `mapanare/self/abi.mn` (94 lines, unchanged).
  No edits to ABI logic across the arc. Discipline.

**v5.11.0 panel #1 (BENCHMARKS Windows section header stale at
v5.8.8):** **Fixed** at v5.21.1 H.12 — `BENCHMARKS-windows.md`
gained a "last sync v5.8.8" admonition; per-platform split was
already structural at v5.11.0. ✓

**v5.11.0 panel #2 (stage2-teardown RC=3 crash):** **Still open.**
Same shape, RC=3 in my live run at HEAD. The v4.30.0 PLAN was meant
to close this; it is now 70+ releases stale. The longest-stale
carry-forward on my axis. Carry to v5.22.x or v6.0 cleanup. See
Issue #5.

**v5.11.0 panel #3 (Mc.5 `mnc emit-wasm` self-hosted):** **Still
deferred-with-tracking.** Mc.1–Mc.4 closed at v5.18.0 as I
recommended; Mc.5 is correctly out of v5.13–v5.21 scope. Forward
note at the next IR-touching panel (likely v5.13.x → v6.0).

---

## Issues Found

### #1 — Te.3 brace-deprecation warning misses single-line brace blocks AND the entire native-side surface (MEDIUM, NEW)

**Severity:** MEDIUM
**File(s):** `mapanare/parser.py:2240-2291`
(`count_user_brace_block_openers`); `mapanare/self/parser.mn` (no
brace-deprecation logic at all)
**Reproduction at HEAD:**

```bash
$ echo 'fn main() { print("hi") }' > /tmp/brace.mn
$ python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
[dev mode] Using Python bootstrap compiler. ...
emitted /tmp/brace.mn -> /tmp/brace.ll (target: x86_64-unknown-linux-gnu)
# expected: warning: ... uses deprecated {}-block syntax (1 occurrence) ...
# actual: NO WARNING
```

The detector is line-based: it scans each non-comment, non-string
line and counts it as a brace opener iff the *line itself* ends with
`{` (after stripping). The idiom `fn main() { print("hi") }` ends
with `}` and is **silently accepted** as if it were colon-style.

I verified the gap exists for the multi-line shape too on
`mnc-stage1`:

```bash
$ printf 'fn main() {\n    print("hi")\n}\n' > /tmp/brace2.mn
$ python3 -m mapanare emit-llvm /tmp/brace2.mn 2>&1 | head -3
warning: /tmp/brace2.mn: uses deprecated {}-block syntax (1 occurrence). ...
$ ./mapanare/self/mnc-stage1 emit-llvm /tmp/brace2.mn -o /tmp/x.ll 2>&1 | head -3
# (silent — no warning emitted)
```

**Native `mnc-stage1` has zero brace-deprecation logic.** I grep'd
`mapanare/self/*.mn` for `MAPANARE_NO_BRACE_WARNING` and
`brace_deprecation` — zero hits. The Python detector itself
(`count_user_brace_block_openers`) has no `.mn` mirror.

**Why this matters on my axis:** the IR is identical for brace and
colon, so this is **not** an IR correctness issue. But Te.3 is a
soft-deprecation contract that v6.0 will use to time the hard
removal. If users wrote single-line brace code across v5.19.0 →
v6.0 thinking they were getting warnings (and weren't), v6.0's hard
removal will surprise them. The deprecation cycle (SPEC §22) has a
2-release soak window contract; that contract requires the warning
to actually fire on every brace shape across both compilers.

**Why it's only MEDIUM (not HIGH):**
- IR is unaffected; no miscompilation.
- The v6.0 hard removal hasn't shipped — 1+ release-cycle of soak
  window remains.
- The fix is a single-pass character-level scan + a bootstrap
  mirror.

**Suggested fix (LangRef-equivalent — sketch):**

```python
# mapanare/parser.py — replace count_user_brace_block_openers
def count_user_brace_block_openers(source: str) -> int:
    """Count user-written ``{`` block openers (any position on a line),
    skipping strings, chars, comments, and ``#{`` map literals."""
    count = 0
    i = 0
    in_str = in_char = in_line_cmt = False
    while i < len(source):
        ch = source[i]
        if in_line_cmt:
            if ch == "\n":
                in_line_cmt = False
            i += 1
            continue
        if in_str:
            if ch == "\\" and i + 1 < len(source):
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if in_char:
            if ch == "\\" and i + 1 < len(source):
                i += 2
                continue
            if ch == "'":
                in_char = False
            i += 1
            continue
        if ch == "/" and i + 1 < len(source) and source[i + 1] == "/":
            in_line_cmt = True
            i += 2
            continue
        if ch == '"':
            in_str = True; i += 1; continue
        if ch == "'":
            in_char = True; i += 1; continue
        # `#{` is a map literal opener, not a block opener
        if ch == "#" and i + 1 < len(source) and source[i + 1] == "{":
            i += 2
            continue
        if ch == "{":
            count += 1
        i += 1
    return count
```

For the bootstrap mirror, port that same loop to
`mapanare/self/parser.mn`, hook it into `parse()` before
`tokenize()`, and have it print to stderr via the existing
`__mn_str_eprint` shim. ~50 LOC of `.mn` plus tests in
`tests/bootstrap/`. **Effort: 2–4 hours.**

Tracking version: **v5.22.x** (single patch release; do not let this
go past v5.22.5 without re-evaluation).

### #2 — `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` does not exist (LOW, NEW)

**Severity:** LOW
**File:** `docs/roadmap/v5/v5.19.0/` (PLAN.md + PROMPT.md +
DOCKER_DESIGN.md present; no SESSION_REPORT.md)
**Reproduction:**

```bash
$ ls docs/roadmap/v5/v5.19.0/
DOCKER_DESIGN.md  PLAN.md  PROMPT.md
$ git log --oneline | grep "v5.19.0"
db32bd4 v5.19.0 Te.3.D: migrate tests/golden/ to colon syntax
fba8521 v5.19.0 Te.3.A/B/C/E: brace deprecation + fmt auto-migration + formatter polish
6adfee7 v5.19.0 design: scope split — Te.3 here, Dk.* moved to v5.19.1
```

**v5.19.0 Te.3 shipped (3 commits in the log) but no SESSION_REPORT
was written.** The PRE_PANEL_AUDIT.md and the panel prompt both
reference 16 SESSION_REPORTs as required reading; only **15 exist**
on disk. The lead's own CLAUDE.md preamble lists v5.19.0 under
"Planned / in-progress" rather than "ready, not tagged" — which is
where v5.19.1, v5.20.0, v5.21.0 etc. sit.

**Why this is on my axis (peripherally):** missing release docs
break the "every claim in every SESSION_REPORT is fact-checkable"
contract that Cobra and I have asked for since v5.6.x. Te.3 is the
release where my Issue #1 lives; if there were a SESSION_REPORT, it
would specify exactly which parser entry paths are supposed to fire
the warning, and #1 might have been caught at-source.

**Why it's only LOW:** the *code* shipped fine — fixed point held
through v5.19.0, goldens didn't regress, the Dk.* split-out at
`6adfee7` was the right scope decision. The docs hole is recoverable
in a single commit.

**Suggested fix:** write the missing
`docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` retroactively, even if
brief, summarizing Te.3.A/B/C/D/E and the scope split commit
`6adfee7`. Backfill takes ~1 hour. Anaconda owns this; flag for the
panel summary.

### #3 — H.10 closure description is misleading (LOW, COSMETIC)

**Severity:** LOW
**File:** `.reviews/v5.22.0/PRE_PANEL_AUDIT.md:58`
**Audit text:** "format-pass arm added; `mnc fmt` round-trips chains
stable"
**Actual closure at `mapanare/format.py:22-32`:** module docstring
documents that **no `ChainedCompare` arm is needed** because the
existing line-based whitespace canonicalization preserves chain
shapes by construction; new unit tests guard idempotence.

The actual closure is *structurally cleaner* than what the audit
described — "no arm needed because invariants hold by construction"
is the better fix than "added an arm". But the audit text says "arm
added" which suggests a code addition that didn't happen.

**Why on my axis:** H.10 is the closure I would care about most as a
codegen reviewer — chain whitespace round-trip is exactly the kind
of formatter rule that could perturb fixed point if mishandled. The
audit being slightly wrong about *what changed* is the kind of
detail mismatch I have to flag.

**Why LOW:** the actual closure is correct and the tests guard the
right invariant.

**Suggested fix:** correct the audit row to "verified — line-based
canonicalization preserves chains by construction; new unit tests
added in `tests/test_format.py`". Effort: <5 min.

### #4 — Sh.* shrink claim is ~2.4 percentage points high (LOW)

**Severity:** LOW
**File:** `docs/roadmap/v5/v5.17.2/SESSION_REPORT.md` (and inherited
into CLAUDE.md preamble at the v5.17.2 release-note line)
**Reproduction:**

```bash
$ total=0
$ for f in $(git ls-tree -r --name-only v5.13.0 | grep "^mapanare/self/.*\.mn$" | grep -v mnc_all); do
$   n=$(git show v5.13.0:$f 2>/dev/null | wc -l)
$   total=$((total + n))
$ done
$ echo $total
27922  # SR claim: 28,698. Discrepancy: 776 lines.

$ for f in ...; do n=$(git show ca89d61:$f | wc -l); ...; done   # v5.17.2 closeout
24710  # SR claim matches.

$ python3 -c "print((24710 - 27922) / 27922 * 100)"
-11.50%   # actual
```

The v5.17.2 SR's headline shrink is **−3,988 lines (−13.9%)**; my
recount shows **−3,212 lines (−11.5%)**. Discrepancy of ~776 lines
is in the v5.13.0 baseline; the v5.17.2 endpoint is correct.

**Why on my axis:** Sh.* is the rewrite arc that was supposed to
preserve fixed point by construction (which it did). The shrink is
real and substantial regardless of whether it's 11.5% or 13.9%, but
the headline number is repeatedly cited (CLAUDE.md, README.md,
SESSION_REPORTs of v5.18.0+) and is ~21% higher than reality.

**Why LOW:** does not affect IR correctness, fixed point, or any
runtime behavior. This is a numerator/denominator hygiene issue.

**Suggested fix:** re-run the count using a single canonical method
(e.g. `wc -l mapanare/self/*.mn | grep -v mnc_all | tail -1`) for
both endpoints and update the v5.17.2 SR + the propagating
references. Effort: 30 min.

### #5 — Stage2-binary teardown crash (RC=3) still papered over (LOW, CARRY-FORWARD from v4.28.0)

**Severity:** LOW
**File:** `scripts/verify_fixed_point.sh:124-137`
**Live evidence at HEAD:**

```
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  note: mnc-stage2 exited with code 3
  (teardown crash is a known issue tracked for v4.30.0; the script
   still validates that stage3.ll is non-empty and llvm-valid below)
  stage3.ll: 238086 lines
  llvm-as: OK
```

**Same finding as v5.11.0 #2.** No fix attempt across the v5.13–v5.21
arc. v4.30.0 PLAN was meant to close this — now 70+ releases stale.
The longest-stale carry-forward on my axis (after Rt.04, which is
correctly v6.0-scoped). Recommended fix sketch from v5.11.0 #2 still
applies: bisect with `valgrind --error-exitcode=99
--track-origins=yes`, look for "Invalid read"/"Invalid free" in
atexit / `__run_exit_handlers`, fix the offending free-after-free or
double-registered atexit handler. The `valgrind-map` skill exists
specifically for this work.

**Why still LOW:** does not affect IR correctness, output is valid,
13-release strict fixed-point streak holds.

**Tracking version:** v5.22.x or v6.0 cleanup window.

---

## Recommendations

### For the v5.22.0 panel verdict (no IR-axis blockers)

- **Ship it as Option A or Option C.** No NEEDS WORK on my axis. The
  13-release strict fixed-point streak is the load-bearing health
  signal of the entire arc, and it holds at 238,086 lines / 0 diff.

### For v5.22.x

- **Close Issue #1** (Te.3 single-line brace-block detector + native
  mirror). 2–4 hours; one patch release. If it's not closed by
  v5.22.5 it should be re-graded as a *contract* issue with v6.0
  rather than a hygiene issue.

### For v5.23.0 / v5.24.0

- **Close Issue #5** (the v4.28.0 stage2-teardown crash). Apply
  `valgrind-map` to bisect destructor ordering. Once closed,
  `verify_fixed_point.sh` can drop the `set +e` block and become a
  more rigorous gate.
- **Audit `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md`** absence
  (Issue #2) — backfill or document the absence explicitly.
- **Sh.* shrink number reconciliation** (Issue #4) — single-method
  recount; update the SRs and CLAUDE.md.

### For v6.0 (unchanged from v5.11.0)

- **Borrow checker closes Rt.04.** Multi-level alias drop-glue at
  struct→list→string depth 2 is the only remaining MEDIUM on my
  axis. Carries forward unchanged.
- **Te.3 hard removal** of `{}`. Per SPEC §22 deprecation cycle,
  v6.0 is the contracted hard-removal target. Issue #1 must be
  fully closed before v6.0 ships, otherwise the deprecation cycle
  never actually completed its soak window for one of the two brace
  shapes.

---

## Post-Production Health Assessment

**Health gate read: GREEN, with one note.**

22 minor versions after v5.0.0 release-gate, **the codebase is more
healthy on every IR-correctness signal than it was at v5.0.0**:

- Strict 3-stage fixed point at 238,086 lines, 0 diff, 13-release
  streak (was: NEAR with 4-line VERSION-only diff at v5.0.0–v5.8.x).
- Goldens 95/95 (was: 66/66 at v5.0.0; +44%).
- 4-way ABI dispatch verified clean (was: 1-way SysV at v5.0.0;
  4-way at v5.8.8 closeout has been preserved unchanged across
  v5.9–v5.22).
- Zero new MIR ops, zero new IR shapes across 22 minor versions of
  feature work. The "every Te.* desugars to existing primitives"
  posture has now been stress-tested across 6 features over 10
  releases and held.
- New runtime fn additions: 2 (`__mn_indent_to_braces` ~258 LOC
  for Te.1, `__mn_assert_fail` 9 LOC for At.* / `@test`). Bounded.
  Both follow the v5.9.0 5-edit pattern. Pe.1 budget held.

The note: **Te.3 is partially hollow** (Issue #1). Single-line
brace blocks bypass the deprecation warning entirely on the Python
side, and the native side has no detector at all. This is *not* an
IR correctness regression — the IR is identical for both brace
shapes — but it is a **soft-contract regression**: the v5.19.0
deprecation cycle is supposed to give users a 2-release soak window
of warnings before v6.0 hard-removes `{}`, and that contract is
currently broken for the most idiomatic legacy form.

If Issue #1 ships clean in v5.22.x, my next-panel score moves to
9.90. If it goes past v5.22.5 unfixed, the next panel should
re-grade Te.3 as HIGH not MEDIUM.

**Trajectory:** 9.3 → 9.8 → 9.85 → 9.85 across the v5.2.0 → v5.7.1
→ v5.11.0 → v5.22.0 panels. Slope is correct; the reserved 0.15
from a perfect 10 is the same composition as v5.11.0 (0.10 Rt.04 +
0.05 stage2-teardown), with a small temporary 0.05 deduction for
Issue #1 offset by a 0.05 retirement of v5.6.x churn skepticism.
Both are recoverable.

**Is this still a normal point release after 22 minor versions of
post-v5.0.0 evolution?** **Yes.** The arc shipped six additive
language features without breaking the IR, without inflating the C
runtime beyond two surface-feature exports, without disturbing 4-way
ABI dispatch, and without losing the strict fixed-point invariant.
That's the discipline I asked for at v5.2.0 ("no cheap shit") and
v5.8.0 ("operationalize the IR-stability discipline"). It is now
operationalized **and** stress-tested. That is the cleanest signal a
codegen reviewer can give.

---

## Raw Notes

```
# Live verification at HEAD
$ git rev-parse HEAD
24d5be749e102992efc39c20fe5bfba0d9cd4d5c  # v5.21.1 (panel target = v5.22.0)

$ cat VERSION
5.21.1

$ bash scripts/verify_fixed_point.sh --keep 2>&1 | tail -10
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (238086 lines, 0 diff)
=== La Culebra Se Muerde La Cola ===

$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 \
    2>&1 | tail -3
PASS 95_chained_cmp_side_effect 26L->166L 10bb 122stk 9ms (2 fns) ...
All 95 tests passed in 26.4s

# v5.11.0..HEAD diff scope
$ git diff v5.11.0..HEAD --stat -- mapanare/mir.py
# (zero output — Python MIR unchanged)

$ git diff v5.11.0..HEAD --stat -- runtime/native/
 runtime/native/mapanare_core.c | 549 +++++++++++++++++++++++++++++++++
 runtime/native/mapanare_core.h |   4 +
 2 files changed, 553 insertions(+)

$ git diff v5.11.0..HEAD -- runtime/native/mapanare_core.c | grep ^+MN_EXPORT
+MN_EXPORT void __mn_assert_fail(MnString message) {
+MN_EXPORT MnString __mn_indent_to_braces(MnString source) {
# Two new exports. PRE_PANEL_AUDIT only mentioned __mn_indent_to_braces.

# Te.6 once-evaluation verified
$ python3 -m mapanare emit-llvm -O0 \
    tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain.ll
$ grep -c "@middle(" /tmp/chain.ll
2  # 1 declare + 1 call site -> once-evaluated
# Single call site verified in lowered @check function:
#   %c.1 = call i64 @middle(i64 %l.0)
#   store i64 %c.1, ptr %t0.a.2
#   %l.3 = load i64, ptr %t0.a.2
#   store i64 %l.3, ptr %__mn_chain_0.a.4
#   ; both subsequent comparisons read from %__mn_chain_0.a.4

# D6 byte-identity verified
$ printf 'fn check(x: Int) -> Bool:\n    return x < 10\n' > /tmp/single.mn
$ python3 -m mapanare emit-llvm -O0 /tmp/single.mn -o /tmp/single.ll
$ grep "__mn_chain" /tmp/single.ll
# (zero output — single comparison emits no chain temp)

# Bootstrap mirror at HEAD
$ python3 -m pytest tests/bootstrap/test_chained_cmp_mirror.py -v
============================== 10 passed in 19.22s ==============================

# Te.3 brace-warning gap (Issue #1)
$ echo 'fn main() { print("hi") }' > /tmp/brace.mn
$ python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | grep -i warn
# (zero output — single-line brace block silently accepted)
$ printf 'fn main() {\n    print("hi")\n}\n' > /tmp/brace2.mn
$ python3 -m mapanare emit-llvm /tmp/brace2.mn 2>&1 | grep -i warn
warning: /tmp/brace2.mn: uses deprecated {}-block syntax (1 occurrence). ...
$ ./mapanare/self/mnc-stage1 emit-llvm /tmp/brace2.mn -o /tmp/x.ll 2>&1 | grep -i warn
# (zero output — native side has no brace-deprecation logic at all)

# v5.19.0 SESSION_REPORT existence (Issue #2)
$ ls docs/roadmap/v5/v5.19.0/
DOCKER_DESIGN.md  PLAN.md  PROMPT.md
# (no SESSION_REPORT.md)
$ git log --oneline | grep "v5.19.0"
db32bd4 v5.19.0 Te.3.D: migrate tests/golden/ to colon syntax
fba8521 v5.19.0 Te.3.A/B/C/E: brace deprecation + fmt auto-migration + formatter polish
6adfee7 v5.19.0 design: scope split — Te.3 here, Dk.* moved to v5.19.1

# Sh.* shrink baseline (Issue #4)
$ for f in $(git ls-tree -r --name-only v5.13.0 | grep "^mapanare/self/.*\.mn$" \
              | grep -v mnc_all); do
$   git show v5.13.0:$f 2>/dev/null | wc -l
$ done | awk '{s+=$1} END{print s}'
27922
$ wc -l mapanare/self/*.mn | grep -v mnc_all | tail -1
  25637 total
# Delta: -2,285 lines vs v5.13.0 (across all features added since,
# including +742 from Te.5.F and chain stuff). Sh.*-only delta at
# v5.17.2 closeout commit ca89d61: -3,212 (-11.5%). SR claim:
# -3,988 (-13.9%). Off by ~776 lines.

# stage2.ll line-count trajectory
v5.7.1:  217,879  (NEAR — VERSION 4-line diff)
v5.8.0:  217,879  (NEAR)
v5.9.0:  225,831  (STRICT — first since v4.139.0)
v5.11.0: 226,603  (STRICT — preserved)
v5.13.0: ~226,603 (no IR-touching change)
v5.14.0: ~228,630 (Te.1 colon-block IR — same shape)
v5.15.0: 228,630  (Te.2 — same shape)
v5.16.0: 231,723  (Te.4 — interp parity)
v5.17.0: 231,957  (Sh.* — IR-byte-identical)
v5.17.2: 231,723  (Sh.H — slight shrink from defensive-loop cleanup)
v5.18.0: 232,281  (Mc.* — +558 lines for 3 dispatch arms)
v5.19.0: ~232,281 (Te.3 — parser-only)
v5.19.1: ~232,281 (Dk.* — packaging-only)
v5.20.0: 232,281  (Te.5 Python — no .mn edits)
v5.20.1: 238,086  (Te.5.F bootstrap mirror — +5,805 lines from new .mn code)
v5.21.0: 238,086  (Te.6 — D6 preserves byte-identity)
v5.21.1: 238,086  (hygiene — no IR change)
v5.22.0: 238,086  (panel only — pending tag)
delta v5.7.1 → v5.22.0: +20,207 lines (+9.3%)
delta v5.11.0 → v5.22.0: +11,483 lines (+5.1%)
# Both within Pe.1 budget. The +5,805 jump at v5.20.1 is the
# bootstrap mirror code, not the emitter — same shape, more callers.

# 5-edit pattern compliance for new __mn_* exports (preserved
# through v5.20.1)
1. runtime/native/mapanare_core.c    — the export itself
2. runtime/native/mapanare_core.h    — header decl
3. mapanare/emit_llvm_text.py        — Python emitter dispatch
4. mapanare/self/emit_llvm.mn        — declare_runtime_fn
5. mapanare/self/semantic.mn         — is_builtin_function + Symbol
6. mapanare/self/lower.mn            — Call return-type
__mn_indent_to_braces: ✓ all 6 sites at v5.14.1
__mn_assert_fail:       ✓ all 6 sites at v5.13.1

# Score breakdown vs v5.11.0 (9.85)
+0.05  13-release strict fixed-point streak (vs 5 at v5.11.0)
+0.00  v5.13–v5.21 IR-correctness preserved by construction
-0.05  Issue #1 (Te.3 single-line brace block detector gap +
       native side has no detector — partial deprecation hollow)
-0.00  Issue #2 (v5.19.0 SESSION_REPORT.md missing — process,
       not IR)
-0.00  Issue #3 (H.10 audit text mismatch — cosmetic)
-0.00  Issue #4 (Sh.* shrink 2.4 pp high — honesty, not IR)
-0.00  Issue #5 (stage2 teardown crash, carry-forward from
       v4.28.0 / v5.11.0 — already priced in)
-0.00  Rt.04 still open but unchanged (v6.0 borrow-checker scope)
v5.22.0 = 9.85 / 10 EXCEEDS

# Reserved 0.15 from a perfect 10:
- 0.10 Rt.04 multi-level alias drop-glue (v6.0 borrow-checker)
- 0.05 v4.28.0 stage2 teardown crash (70+ releases stale)
```

---

**One-line summary for lead:** **9.85 / 10 EXCEEDS — strict
3-stage fixed-point preserved across the entire v5.13–v5.21
terseness arc (13-release streak at 238,086 lines / 0 diff,
longest in project history); zero new MIR ops, zero new IR
shapes, two new C-runtime exports (only one mentioned in the
PRE_PANEL_AUDIT); Te.6 once-evaluation verified live in IR;
goldens 66/66 → 95/95 (+44%); the only IR-adjacent finding is
Te.3 partially hollow — single-line `{}` blocks bypass the
deprecation warning on Python and the entire native side has
no detector at all (MEDIUM, fixable in 2-4 hours); v5.11.0 #1
(BENCHMARKS staleness) closed at v5.21.1 H.12; v5.11.0 #2
(stage2 teardown RC=3) still open and now 70 releases stale.
PASS WITH NOTES — Option A defensible if Issue #1 lands a
v5.22.x patch within the soak window.**
