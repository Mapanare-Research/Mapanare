# Coral — v4.136.0 language design review

**Score: 8.7/10**
**Grade: MEETS**
**Prior (v4.120.0): 8.1/10 PASS**
**Delta: +0.6**

---

## Executive summary

The v4.121.0 → v4.134.0 closeout arc moved every language-side note
from my v4.120.0 review (Co.1–Co.4) into the SPEC, into the parser,
or into a properly-named v5.x docket. The SPEC header now reads
`Version: 4.129.0` (`docs/SPEC.md:3`); the eleven SPEC edits
documented in `docs/roadmap/v4/v4.129.0/SPEC_AUDIT.md` are all
present in the file; the parser predicate that silently dropped
`const`/`trait` declarations at module scope has been fixed
(`mapanare/self/parser.mn:380-386`); the `List<Int>` indexing
correctness gap is closed and pinned by a regression test
(`tests/golden/65_list_int_indexing.mn`); and the three new dockets
opened during the SPEC sync (Gr.1, Gr.2, Sem.1) are honest grammar/
semantic gaps that **do not block v5** because each is small, named,
and produces an explicit parse-error or undefined-name diagnostic
rather than wrong code at runtime.

The language surface is **coherent for v5 declaration**. Where the
SPEC promises a feature, that feature works through the Python
bootstrap; where it does not (Sh.4 async self-hosted lowering,
Sh.5–7 const/tensor/closure-typed self-hosted lowering), the SPEC
either notes the v5.x carve-out (§29 async block-quote at line
2404) or the divergence is implementation-internal (the user's
program still compiles via the bootstrap pipeline).

I am moving from **8.1 → 8.7 (+0.6)**. Justification at the bottom.

---

## SPEC audit — did v4.129.0 actually close the gaps?

I read every section flagged in `docs/roadmap/v4/v4.129.0/SPEC_AUDIT.md`
against the live SPEC.

### Items audited and verified fixed

1. **§0 Header (line 3).** Was "4.116.0 Live"; now `Version: 4.129.0`,
   `Status: Live — synced to the v4.129.0 cut (2026-04-15)`. **OK.**

2. **§2.1 const note (lines 130–156).** Was the wrong "v4.18.0
   alias / v4.27.0 removed" story; now correctly reflects v4.55.0
   reintroduction with `ConstDef`, immutability enforcement,
   `SymbolKind.CONST`, tensor-shape-position usability, and the
   v4.126.0 self-hosted parser fix. The historical timeline is
   preserved as context. **OK.**

3. **§2.1.1 master list `const` row (line 77).** Now reads
   "Compile-time constant: `const N: T = EXPR`; requires a type
   annotation and a constant-foldable initializer (see §2.1 note)"
   under category Bindings. **OK.**

4. **§3.2 Generic Container Types (line 467).** Now includes the
   `Future<T>` row with `FUTURE` TypeKind and a §29 cross-reference
   noting v4.69.0 introduction. **OK.**

5. **§3.6 duplicate heading.** Resolved. §3.6 is "Type Inference
   Rules" (line 541), §3.7 "Struct Types" (line 590), §3.8 "Enum
   Types" (line 632), §3.9 "Option and Result Types" (line 681),
   §3.10 Agent (line 740), §3.11 Tensor (line 760), §3.12 Type
   Aliases (line 848), §3.13 Function Types (line 858). Renumbering
   is consistent and no broken cross-references found. **OK.**

6. **§6.3 lambda example (line 1162).** The contradictory
   `(x: Int) => x + offset` example is replaced with the untyped
   `(x) => x + offset`. The note above it remains correct: "Type
   annotations on lambda parameters are not supported in the
   grammar — use a named function if explicit types are needed."
   **OK.**

7. **§27.1 TypeKind count (line 2281).** Updated from "25" to "29"
   variants. I cross-checked the categories in the audit table —
   they sum to 29. **OK.**

8. **§28 Standard library (line 2310).** No more "seven modules
   (v0.9.0)" claim. New text describes the stdlib as "written in
   Mapanare and compiled via LLVM" with a domain-by-domain table
   pointing to representative modules. **OK.**

9. **Appendix B pipeline diagram (lines 2612–2617).** Now shows
   three live targets: `LLVM IR → Native Binary`, `C Source →
   gcc/clang → Native Binary`, `WebAssembly (WAT/WASM)`. The dead
   "Python (legacy)" emitter is gone from the diagram and the
   "Python Transpiler (Legacy)" subsection has been replaced by the
   "C Backend (v3.0.0+)" subsection (line 2689). The remaining
   parenthetical reference at §0 line 6 ("A legacy Python
   transpiler backend exists for reference and bootstrapping
   only") is **stale** — the v4.58.0 deletion is documented in
   Appendix B itself. Two-word inconsistency, not a v5 blocker.
   See "What I'd dock" item 1.

10. **§28 stdlib preamble** + **MIR optimizer pass list** in
    Appendix B — both updated to reflect current state.

### Items I'd add to the next SPEC pass (not v5 blockers)

- `docs/SPEC.md:6` still claims "A legacy Python transpiler backend
  exists for reference and bootstrapping only." Deleted v4.58.0; see
  §B.
- §29.7 "for await ... — *planned (v5.x)*" is precisely worded.
  Match.
- §27.1 "All 15 string methods" — I did not re-count against
  `runtime/native/`. Cobra/Boa territory; flagging as a future
  audit.

**Net SPEC currency**: 9 of 10 v4.129.0 edits are clean. One stray
phrasing remnant. No new wrong claims found in the audit subset.

---

## Open language dockets (Gr.1, Gr.2, Sem.1, Sh.4–7)

These are the items my v4.120.0 carry-forward (Co.2, Co.3, Co.4)
correctly anticipated as needing definition before v5. The closeout
arc converted three to "closed by SPEC decision" (Co.2, Co.3, Co.4
all closed in `DOCKET_LEDGER.md` lines 107–109) and surfaced three
new ones (Gr.1, Gr.2, Sem.1) during the v4.129.0 examples sweep.

### Gr.1 — Multi-line list/tensor literal grammar (LOW)

Source: `docs/roadmap/v4/v4.129.0/EXAMPLES_REPORT.md` Category A.
Five examples blocked. The grammar requires single-line list and
tensor literals; a literal like

```mn
let xs = [
    1,
    2,
]
```

emits a parse error. **Failure mode: parse-time diagnostic.** The
user gets `Unexpected newline — expected ']' ...`, not silent
miscompilation. This is a developer-experience gap, not a
correctness gap. Fixing it is grammar work in `mapanare.lark` plus
matching changes in the Lark transformer; tractable for a v4.137.0+
grammar-quality release. **Not a v5 blocker.**

### Gr.2 — Qualified type refs in type position (MEDIUM)

Source: `docs/roadmap/v4/v4.129.0/EXAMPLES_REPORT.md` Category B.
Three examples blocked because `stdlib/gpu/tensor.mn:90:19` and
`stdlib/gpu/kernel.mn:63:20` use `device.DeviceKind` as a parameter
type — qualified names work in expression position but not in type
position. **The defect is in shipped stdlib code**, not just in
examples. This means a user trying to import the GPU stdlib gets a
parse error on stdlib compilation.

This is the only **MEDIUM** open language docket. It is **not** a
v5 blocker, because (a) the fix is "either bare-import the type or
add `qualified_name` to the type-position grammar rule" — about a
day of work, (b) GPU stdlib is itself v5.x-aspirational per
`stdlib/gpu/` directory layout. But it is the docket I would
schedule first in v4.137.0+.

### Sem.1 — Module-level `let mut` scoping (LOW)

Source: `docs/roadmap/v4/v4.129.0/EXAMPLES_REPORT.md` Category E.
Module-level `let mut counter: Int = 0` parses but functions reading
`counter` get `Undefined variable 'counter'`. Either the SPEC needs
to add module-level `let mut` to §2.1 (and the semantic checker
needs to register the symbol in the module scope), or the SPEC
needs to disallow module-level `mut` and the parser should reject
it. **One example blocked**, and the failure mode is a clear
diagnostic.

This is a **language-design decision deferred**, which is exactly
the v5.x category I called for in my v4.120.0 Co.3. The SPEC §2.1
currently documents only immutable module-level `let`; the parser
silently accepts `let mut` at module scope. The SPEC and parser
should agree before v5 declares stability. Action: pick one. Either
behavior is defensible.

### Sh.4–Sh.7 (self-hosted async/const/tensor/closure-typed)

Status from `DOCKET_LEDGER.md` lines 47–50: all four open, all
labeled v5.x track. **These are not language gaps.** The Python
bootstrap compiler handles all four feature surfaces correctly,
and the SPEC's §29 async paragraph (line 2410-2413) explicitly
notes "The self-hosted compiler (`mnc-stage1`) does not yet lower
async — async programs currently compile through the Python
bootstrap's `emit-llvm` pipeline." This is the kind of honest
implementation note I asked for at v4.114.0. **Not v5 blockers.**

### Net read

Three open MEDIUM/LOW dockets named at the language layer (Gr.1,
Gr.2, Sem.1). All three (a) have a clear failure mode that is a
diagnostic, not silent wrong code, (b) are honestly documented in
the v4.129.0 EXAMPLES_REPORT and v4.135.0 DOCKET_LEDGER, (c) are
sized correctly for v4.137.0+ or v5.x. **A major version release
with three named, scoped grammar/semantic carve-outs is normal.**

---

## Qs.1 regression guard assessment

Verified `tests/golden/65_list_int_indexing.mn` exists and exercises
five usage patterns (line 14: direct call argument; line 18: let
binding; line 22: second-element indexing; line 26: post-mutation
indexing; line 29: arithmetic on two indices). The header comment
correctly cites the v4.122.0 docket and explicitly contrasts pre-
fix behavior (`<?>` and raw pointer values) against expected
post-fix output.

`docs/roadmap/v4/v4.122.0/SESSION_REPORT.md` lines 96–127 document
the test surface added with the fix:

- `tests/llvm/test_emitter_hardening.py::TestListIntIndexingQs1`
  (5 IR-level invariant tests covering `List<Int>`, `List<Float>`,
  `List<MyStruct>`, the let-binding shape, and the arithmetic
  shape).
- `tests/integration/expected/65_list_int_indexing.expected`
  (stdout assertion `42\n42\n99\n100\n141\n`).

The fix itself is a 6-line change in `mapanare/lower.py::_lower_let`
documented in v4.122.0 SESSION_REPORT line 99–105, and the v4.135.0
PRE_PANEL_AUDIT verifies the fix is still in place at HEAD (verified
section "v4.122.0 — Qs.1 resolved").

The guard surface is comprehensive (5 IR-level tests + 1 integration
+ 1 golden). A future regression in any of the five shapes I'd
expect would be caught at PR time. **Closure is complete.**

---

## `const` keyword status

The v4.126.0 parser fix (`mapanare/self/parser.mn:380-386`)
verified at HEAD: `KW_CONST` and `KW_TRAIT` are both present in
`is_definition_start`. The 9-line comment block above lines 385–386
correctly attributes the bug to v4.55.0 (when const was reintroduced)
and explains why three downstream workarounds (in `register_def`,
`parse_const_def`, `parse_definition.mn:476/524`) had no effect —
the upstream filter was rejecting `KW_CONST` before any of them
fired. Goldens `54_const_basic` and `58_const_scope` pass through
both pipelines (DOCKET_LEDGER line 124).

SPEC §2.1 const note (lines 130–156) accurately describes the
v4.55.0 reintroduction: requires type annotation and constant-
foldable initializer; `SymbolKind.CONST` (distinct from
`SymbolKind.VARIABLE`); usable in tensor-shape positions where
`let`-bound values are not. The v4.126.0 self-hosted parser fix
is cross-referenced in the same note. SPEC and implementation
agree.

This is a clean closure of my v4.120.0 Co.3 ("`const` keyword
direction — implement immutability or remove the notion"). The
project picked "implement immutability" and shipped it.

---

## Rt.1 enum unboxing — language-observable?

v4.124.0 changed `mapanare/emit_llvm_text.py` to store small enum
payloads inline as `{i64, i64, ..., i64}` instead of `{i64, ptr}`
+ heap allocation, with eligibility "≤ 2 payload fields, each
8-byte-or-smaller, no self-reference." This is a **layout
optimization in the Python emitter, not observable through the
language**. The user-visible enum semantics (variant matching,
payload extraction, exhaustiveness) are unchanged. The SPEC §3.8
Enum Types section was not touched in v4.129.0 because it didn't
need to be. The 1.77× speedup on `enum_match` is a benchmark fact,
not a language change.

ABI.1 (residual 2.3× gap to C on enum_match, opened v4.124.0) is
explicitly LOW + v5.x calling-convention work per
`DOCKET_LEDGER.md` line 94. **Not a language docket.** This matches
my v4.120.0 lens — calling-convention is implementation, not
language design.

---

## Cookbook + guides sync (v4.129.0)

`docs/cookbook/async.md` and `docs/guides/async.md` were audited
and judged current per v4.129.0 SR ("audited and judged current.
Cookbook's Sh.9 workaround section is still accurate"). The
cookbook header at `docs/cookbook/async.md:5-15` correctly notes
the v4.116.0 correction that async programs compile through the
Python bootstrap, not through `mnc run`. SPEC §29 line 2410–2413
agrees.

`docs/guides/getting_started.md:1-25` is a "from zero to a native
binary" walk that names the Python bootstrap and `mnc-stage1` as
two separate paths. This is the kind of honest precision I asked
for at v4.114.0 and v4.120.0 (Co.1).

---

## What I'd dock

### 1. Stale "legacy Python transpiler" line at SPEC §0 (0.05)

`docs/SPEC.md:6` still says "A legacy Python transpiler backend
exists for reference and bootstrapping only." Appendix B (lines
2671–2675) correctly notes the deletion at v4.58.0 with a
regression test `tests/test_python_emitter_deleted.py` preventing
reintroduction. Two parts of the same SPEC contradict each other
in two sentences. One-line cleanup, but it's there.

### 2. Gr.2 is MEDIUM, not LOW (0.1)

`DOCKET_LEDGER.md` line 127 marks Gr.2 as MEDIUM, which I agree
with — but the impact note ("blocks 2 stdlib modules + 3 examples")
underplays it slightly. A user who imports `stdlib/gpu/tensor.mn`
gets a parse error on a SPEC-blessed stdlib module. The fix is
small (either bare-import or extend the type-position grammar rule
to accept qualified names — both routes documented). I'd schedule
this first in v4.137.0.

### 3. Sem.1 needs a SPEC decision before v5 (0.1)

`let mut counter: Int = 0` at module scope parses today but the
symbol is not visible to function bodies. SPEC §2.1 documents only
immutable module-level `let`. The parser silently accepting this
form is misleading. Either:
- (a) SPEC §2.1 adds module-level `let mut` and the semantic
  checker registers the symbol — this is the "static" feature
  reserved in Appendix C (line 2728).
- (b) Parser rejects `let mut` at module scope with a clear "module-
  level state is not yet supported; see §2.1" diagnostic.

Both are defensible. **Picking neither is the v4.x state.** I
flagged this exact pattern at v4.120.0 ("`const` keyword direction"
under Co.3 — closed by picking immutability). Sem.1 is the same
shape. Pick it before v5.

These three items are total **−0.25 points** (rounded). The
language-surface itself is ready.

---

## What I credit

- **SPEC currency at v4.129.0 is the strongest it has been across
  any panel I've reviewed.** Eleven targeted edits, each backed by
  a file:line reference in `SPEC_AUDIT.md`. No performative sweep;
  every edit closes a real drift.

- **The `const` keyword half-life I dinged at v4.120.0 (Co.3) is
  now resolved with implementation that matches documentation.**
  v4.126.0 parser fix + v4.129.0 SPEC §2.1 update + v4.55.0
  semantics all line up.

- **Three new dockets (Gr.1, Gr.2, Sem.1) were named honestly at
  v4.129.0** rather than swept under the v4.130.0 panel rug. The
  EXAMPLES_REPORT walks 29 examples, splits them 16/13 with named
  failure categories, and adds header comments to broken examples
  pointing at the report. This is grown-up documentation hygiene.

- **The v4.122.0 Qs.1 fix was minimal (6 lines), correct (5 IR-
  level invariant tests + 1 golden), and at the right layer**
  (lowerer, not emitter). The accompanying SESSION_REPORT correctly
  documents that the self-hosted compiler doesn't have the same
  bug for two structural reasons (lower.mn unconditionally
  rewrites `val_ty = declared`; emit_index_get defaults to
  `load i64`). This is the kind of "fix the bug, not the symptom"
  engineering I want at the language layer.

- **The struct-literal-syntax cleanup item from my v4.120.0
  list (Co.2) is closed in DOCKET_LEDGER as "deferred to v5.x per
  design."** The grammar still doesn't have `Point { x: 1, y: 2 }`
  and the SPEC doesn't claim it does; the v4.120.0 tests asserting
  the feature were either xfail-skipped or removed in the v4.133.0
  An.1 hygiene sweep. Direction is now clear: feature is v5.x
  scope, not v4.x scope.

---

## Verdict

**MEETS.** The language is ready for v5 declaration. The three
language-side items I asked for at v4.120.0 (Co.1 self-hosted
precision, Co.3 const direction, Co.4 contract-programming/struct-
literal direction) are all closed. SPEC currency is strong. The
three new dockets (Gr.1, Gr.2, Sem.1) are scoped correctly for
v4.137.0+ or v5.x and produce diagnostic errors rather than wrong
code.

The 0.05 + 0.1 + 0.1 = 0.25 dock is for: (1) the stray "legacy
Python transpiler" line at §0 contradicting Appendix B; (2) Gr.2
being a stdlib-blocking parse error worth scheduling early; (3)
Sem.1 needing a binary SPEC decision before v5 declares syntax
frozen.

None of these blocks v5. Each is a one-day or smaller edit.

---

## Carry-forward for v4.137.0+

| Docket | Source | Severity | Action |
|---|---|---|---|
| **Sem.1** decision | v4.129.0 EXAMPLES_REPORT Cat. E | LOW | SPEC §2.1: add `let mut` at module scope OR parser rejects with named diagnostic. Pick one. |
| **Gr.2** stdlib | v4.129.0 EXAMPLES_REPORT Cat. B | MEDIUM | Either bare-import the type in `stdlib/gpu/tensor.mn:90` and `stdlib/gpu/kernel.mn:63`, or extend grammar `type_expr` to accept qualified names. |
| **Gr.1** multi-line | v4.129.0 EXAMPLES_REPORT Cat. A | LOW | Grammar work in `mapanare.lark`; allow newlines inside `[ ... ]` and `Tensor<T>[...]`. |
| **§0 stale phrasing** | this review | LOW | Delete "A legacy Python transpiler backend exists" from `docs/SPEC.md:6`. Appendix B already documents the v4.58.0 deletion. |
| **Co.1 retest** | this review | LOW | One more cross-check that "compiler compiles itself" wording is precise everywhere — the v4.134.0 strict 3-stage fixed point makes this claim now literally true at the IR level, so README/SPEC could be sharpened. |
| **Sh.4–Sh.7** | v4.106.0 / v4.45.0 / v4.103.0 | LOW each | v5.x feature work — self-hosted compiler closes feature parity with Python bootstrap. SPEC already calls these out as v5.x. |
| **Struct-literal grammar** | v4.120.0 Co.2 (closed v4.129.0) | — | Decision: **v5.x scope per design.** Tests removed in v4.133.0 An.1 hygiene. No further action this arc. |

---

## v4.120.0 delta reasoning

**v4.99.0**: 7.5 (with reservations)
**v4.114.0**: 8.3 (PASS WITH NOTES)
**v4.120.0**: 8.1 (PASS WITH NOTES, −0.2 for two doc-precision
items that should have been caught at v4.114.0)
**v4.136.0**: **8.7 (MEETS, +0.6)**

Components of the +0.6:

- **+0.4** for SPEC currency: 11 targeted edits in v4.129.0 closed
  every section I and other reviewers had flagged across v4.99.0–
  v4.120.0. The §2.1 const note alone was wrong on three
  independent claims. The §3.6/3.7/3.8/3.9/3.10/3.11/3.12/3.13
  renumbering eliminated a duplicate section heading that had
  silently lived since pre-v4.99.0.

- **+0.2** for the v4.122.0 Qs.1 closure (was the headline
  "would embarrass v5" item per V5_READINESS.md). 6-line lowerer
  fix + 5 IR-level invariants + 1 golden + integration assertion.
  Closed completely.

- **+0.1** for v4.126.0 parser fix (`KW_CONST`/`KW_TRAIT` in
  `is_definition_start`). This is the kind of latent-since-
  v4.55.0 bug that a panel cycle uncovers; closed honestly.

- **−0.1** for the three new opened dockets (Gr.1, Gr.2, Sem.1).
  These are honest discovery during the v4.129.0 SPEC sync, but
  they widen the open-docket count. Gr.2 in particular blocks
  stdlib code, which is a slightly larger surface than the
  examples-only framing of Cat. B implies.

Net: **+0.6** to **8.7**.

If Anaconda moves from 7.6 NEEDS WORK at v4.120.0 to PASS at
v4.136.0 (the An.1 closure + the An.2 lint-debt deferral both make
that plausible), the aggregate may cross 9.0 for Option A. From the
language-design lens specifically, I have no NEEDS WORK to report.

---

## Reproducibility

```bash
# SPEC header version
head -5 docs/SPEC.md

# Renumbering correctness
grep -n "^### 3\." docs/SPEC.md

# §2.1 const note
sed -n '125,160p' docs/SPEC.md

# §6.3 lambda example fix (no `(x: Int) =>` form)
grep -n "add_offset" docs/SPEC.md

# §27.1 TypeKind count
grep -n "29 TypeKind" docs/SPEC.md

# §3.2 Future<T> row
grep -n "Future<T>" docs/SPEC.md

# v4.126.0 parser fix
sed -n '380,388p' mapanare/self/parser.mn

# Qs.1 regression test surface
ls tests/golden/65_list_int_indexing.* tests/integration/expected/65_list_int_indexing.expected
grep -n "TestListIntIndexingQs1" tests/llvm/test_emitter_hardening.py

# Open language dockets
grep -nE "^\| [0-9]+ \| \*\*(Gr|Sem|Sh)\." docs/roadmap/v4/v4.135.0/DOCKET_LEDGER.md

# v4.129.0 examples sweep result (16 PASS / 13 FAIL)
sed -n '1,30p' docs/roadmap/v4/v4.129.0/EXAMPLES_REPORT.md
```
