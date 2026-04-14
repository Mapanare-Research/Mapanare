# Coral v4.120.0 Review — Language design

## Score: 8.1 / 10
## Verdict: PASS WITH NOTES

## Context

At v4.99.0 I gave **7.5 WITH RESERVATIONS** — above the NEEDS WORK
line because the language design itself was coherent; the
implementation had gaps.

At v4.114.0 I gave **8.3 PASS WITH NOTES**. SPEC had been synced in
v4.116.0 (actually before my review; the header went from "1.0.0
Final" to "4.116.0 Live"). The v4.112.0 naming churn I dinged then
— the release said "fixed-point verification," did divergence
analysis — was patched in v4.114.1.

Phase E landed:
- v4.115.0 native async I/O demos (language feature exercised)
- v4.116.0 documentation batch (SPEC + README + cookbook + guides)
- v4.117.0 testing sweep (no language changes)

Phase F: no changes.

My lens: is the language surface stable enough for a v5 tag? What
are the embarrassment-shaped gaps?

---

## Language surface

I walked the feature matrix in `V5_READINESS.md` (285 lines,
authored in v4.119.0) against the SPEC and the 64 golden programs.
It is **neutrally written**, which I appreciate. Key surfaces:

### What works end-to-end

- Functions, structs, enums, pattern matching, control flow
- Generics (monomorphization) with one edge case: bounded-generic
  trait in `tests/semantic/test_traits.py::test_trait_with_bounded_
  generic_fn` (flagged in v4.117.0 audit; real edge case, not
  stale)
- Result / Option / Ok / Err / Some / None
- `print`, `println` (deprecated), `str`, `int`, `float`, all
  builtins
- Lists, Maps (Robin Hood hash), Result, Option
- Agents (full lifecycle via C runtime)
- Signals (reactivity with computed + subscribers + batching)
- Streams (map/filter/take/skip/collect/fold + backpressure)
- Closures (free-variable capture via environment structs)
- Traits, module imports, pipes (`|>`)
- All string methods (length, contains, starts_with in user code —
  `starts_with` tips Sh.2 in self-hosted emitter but works in
  Python bootstrap)
- GPU kernel dispatch (`@gpu`/`@cuda`/`@vulkan`)
- Tensors (literals, indexing, broadcasting, reductions, slicing —
  shape stable since v4.45.0)
- Async / await / block_on (Python bootstrap; native runtime
  linking since v4.102.0; user demos v4.115.0)

### What doesn't (partial / planned / not implemented)

From the V5_READINESS matrix:

- `const` keyword: **◐ parser alias** for `ModuleLetDef`. Does
  not enforce immutability. v4.27.0 removed `const` from the
  grammar under Path B; module-level `let` is canonical.
- Tensor reshape, mutable views, stepped slices: **⬜ planned** per
  SPEC, deferred to v5.x minor releases.
- `for await`: **⬜ SPEC §29.7 explicitly planned/v5.x**.
- DWARF debug info: **✖ SPEC §21.3 defers to v5.x**; `-g` flag
  silent today (should print warning per spec, v4.117.0 audit
  flagged this as 3 failing tests in `test_dwarf_debug_info.py`).
- Self-hosted async/const/tensor/closure-type lowering: **✖**
  (Sh.4/5/6/7) — Python bootstrap handles all four; user programs
  using these via `mnc-stage1` fail.

### Net read

The language surface is **coherent, complete for v5 declaration on
user-visible features**, with **known gaps on "would-be-nice"
surface** (const immutability, tensor advanced ops, `for await`).

Nothing on the V5_READINESS matrix would embarrass a v5 label *as
a language* — every gap is either (a) explicitly planned for v5.x
per SPEC, or (b) a compiler-layer issue (Sh.4/5/6/7 in the self-
hosted lowerer, which is Cobra's domain more than mine).

The "struct literal syntax" failures in `tests/bootstrap/test_
phase5_self_hosted.py::TestStructLiteralSyntax` (3 tests) surprised
me. I hunted down what "struct literal syntax" means here. From the
tests:

```python
# TestStructLiteralSyntax tries to parse:
let p = Point { x: 1, y: 2 }  # ← this syntax
```

This syntax is **not in the grammar** (`mapanare.lark` does not
have a rule for it). The canonical constructor pattern is:

```python
fn make_point(x: Int, y: Int) -> Point {
    let p: Point = x      # state-struct pattern
    p.y = y
    return p
}
```

Or, equivalently for constructors, call a `make_*` function. This
is the pattern every self-hosted module uses (see `ast.mn`,
`lexer.mn`, `parser.mn`). So the test is asserting a feature the
SPEC does not claim.

**This is a cleanup item, not a language gap.** Either delete the
tests (the feature is not on the roadmap) or add struct literal
syntax to the grammar (it's a common v5 request). The test files
suggest the intent was the latter; the grammar suggests the former
won. Should pick one before v5.

---

## SPEC currency

v4.116.0 synced `docs/SPEC.md` header to "4.116.0 Live" and added a
sync-discipline note naming `mapanare.lark`, `types.py`, `self/
lexer.mn` as canonical. §29 has a v4.115.0 status paragraph
correctly describing cooperative-not-preemptive async with native
I/O demoed.

§2.1.1 (added v4.113.0) is a 42-row reserved keyword table. I went
through every row. `async` and `await` are correctly marked hard-
reserved since v4.68.0/v4.72.0. `continue` and `const` are **not**
in the reserved list (Appendix C, future-reserved), which matches
the implementation — both are treatable as regular identifiers
today.

SPEC + grammar + self/lexer.mn cross-check: three keywords
(`ensure`, `invariant`, `let!`) appear in the SPEC but **not** in
the grammar or the lexer. I opened the SPEC at each occurrence —
they're in future-planned sections (contract programming, v5.x).
Acceptable, but SPEC §29 could be similarly precise ("planned for
v5.x") rather than just appearing in the syntax grammar.

Overall: **SPEC is current and mostly precise**. The precision that
Cobra and I both want is on self-hosting — the README sentence "the
compiler compiles itself" is ambiguous. SPEC §29 is better.

---

## What I'd dock

### 1. Struct literal syntax inconsistency (0.2)

Three tests expect it, grammar does not have it. Either decide the
feature is coming (v5.x scope) and mark the tests xfail with a
reason, or delete them. Right now the repo is pretending the
feature is something the grammar has, which it doesn't.

### 2. README precision on "self-hosted" (0.2)

See Cobra. The README says "the compiler compiles itself." More
precisely: the compiler compiles user `.mn` programs correctly
(26/64 literal / 39/64 effective). The compiler does not re-compile
`mapanare/self/mnc_all.mn` end-to-end yet (Sh.8 blocks it). Pick a
precise sentence before v5.

### 3. `const` keyword half-life (0.1)

v4.24.0 introduced `const`. v4.27.0 removed it (Path B: module-
level `let` is canonical). v4.31.0+ still sometimes talks about it.
V5_READINESS's `const` row correctly flags this as **◐ partial,
v5.x may add real `ConstDef`**. Pick a direction — add
immutability, or delete the notion — before v5.

## What I credit

- **Documentation is current through v4.116.0.** README badge is
  4.116.0 not 4.31.0 (I dinged that at v4.99.0 — they fixed it).
  Headline benchmark line in README points to the real benchmark
  report. Feature status table has the async/await row.
- **The SPEC sync-discipline note is the kind of thing I'd put in
  the SPEC cover page.** Naming the canonical source of truth for
  each surface is grown-up language-design practice.
- **The 42-row reserved keyword table (§2.1.1)** closes a docket
  from v4.99.0 that I expected to linger. Grammar + lexer + SPEC
  are synchronised as of v4.113.0.

## Final score

Last panel (v4.114.0): **8.3**
This panel: **8.1** (−0.2)

Small drop tracks the two docs-precision items (self-hosted
wording, const half-life) that I would have dinged at v4.114.0 if I
had been sharper. The language surface itself is where it was at
v4.114.0 — v4.115.0-v4.118.0 added async I/O examples and
measurement, not new language features.

## Verdict: PASS WITH NOTES

The language is ready for v5 **if the README + SPEC get one
precision pass**. The three language-layer cleanup items (struct
literal syntax decision, self-hosted precision, const direction)
are total maybe 2-3 hours of writing. Not compiler work. Not
blocker work. Pre-v5 polish.

## Carry-forward for v4.121.0+

- **Co.1** — README sentence "the compiler compiles itself" precision
- **Co.2** — struct literal syntax decision (grammar or delete tests)
- **Co.3** — `const` keyword direction (implement immutability or remove notion)
- **Co.4** — SPEC §29 `for await` + contract programming (ensure/invariant) precision notes

## Reproducibility

```bash
grep -n "let p = Point" tests/bootstrap/test_phase5_self_hosted.py
grep -n "struct_literal" mapanare/mapanare.lark   # returns no hits
pytest tests/semantic/test_traits.py::TestTraitLLVMEmission::test_trait_with_bounded_generic_fn -v
```
