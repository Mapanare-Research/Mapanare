# Coral v4.106.0 Review — Language Design

## Score: 8.0/10
## Verdict: PASS WITH NOTES

## Context: v4.99.0 → v4.106.0

At v4.99.0 I graded 7.5/10 PASS WITH RESERVATIONS and flagged three HIGH items in the language-design lens: list indexing returning garbage, `else/sino` never verified end-to-end, and closure type annotations failing lowering. All three are now addressed at the bootstrap level with named regression tests (62/63/64). The remaining question is whether users compiling at `-O2` actually receive the language as documented.

## Item #2 — list indexing

CLOSED. `62_list_output.mn` is a minimal, faithful reproducer: heap-string → `list.push` → cross-function return → `join()` read. It exercises exactly the use-after-free pattern v4.101.0 fixed (move-semantics at 6 emitter sites). Interpreter run produces the expected 3-line output. The test's virtue is that the bug's *signature* — a 16-byte garbage prefix on joined strings — would leap out of any `make test` regression. Good guard.

## Item #4 — else/sino

CLOSED. `63_else_sino.mn` covers the patterns the v4.99.0 panel actually asked about: plain `else`, Spanish `sino`, nested if-else-else, and `else` on multi-line bodies. Interpreter produces `positive/negative/zero/1/-1/0` as expected. Grammar-level coverage is adequate: both keywords reach the same AST path. One gap: no `else if` chain (because Mapanare doesn't have a dedicated `else if` token — it uses nested `if` inside `else`, which the test does cover). CLOSED cleanly.

## Item #5 — closure type annotations

CLOSED AT THE LOWERING LEVEL, but with a real-user caveat. `64_closure_typed.mn` covers the four patterns named in the docket: typed `let` binding, typed parameter call, direct call on typed binding, and multi-arg closure through a typed parameter. Interpreter and default-pipeline builds produce `10 / -3 / 20 / 15` correctly.

However, per PRE_PANEL_AUDIT Claim 10, the production pipeline `llvm-as → opt -O2 → llc → clang` miscompiles `combine(sum, 7, 8)` to `10` instead of `15`. This is `Cl.1 HIGH`. From a language-design lens this matters: the spec promises typed closures work; at `-O2` (the default release pipeline per `build_stage1.py:106`) one of four documented patterns returns the wrong value. The fix itself (three lowering changes) is *correct in principle* — the IR it emits is sound — but `opt`'s argument-promotion pass sees the `{ptr, ptr}` closure ABI differently than the callee expects, likely because the no-capture `env=null` lambda gets inlined and the second arg is dropped.

This is really Rattler's LLVM domain, not mine. But a language reviewer has to flag that the feature does not work as documented under the shipped release pipeline.

## Golden test coverage of the 3 new tests

Solid. `62` is minimal and targeted. `63` covers both keywords and one nested form. `64` covers all four patterns Phase A's fix claims to support. What I'd ask for in v4.107.0: a stdout-diff harness (per Ih.1) so that "PASS" means "correct output" rather than "exit 0". Without this, `64`'s current passing status is an illusion at `-O2`.

## Or-pattern + constructor rejection (Div.4)

Confirmed. `Some(0) | None` is rejected with `or-pattern alternatives must bind the same names: extra ['None']`. The checker is treating `None` as a potential binder rather than recognizing it as a nullary constructor. This is a missing language feature — or-patterns across enum variants are standard in Rust, OCaml, Swift. MEDIUM is appropriate severity; v4.107.0 should address.

## Findings

- F1: Phase A closed my three HIGH items cleanly at the bootstrap.
- F2: Cl.1 opt -O2 closure miscompile is a real correctness hole in the *release* pipeline.
- F3: Div.4 or-pattern + constructor is a missing language feature, not a bug.
- F4: Integration harness does not diff stdout (Ih.1) — this hides Cl.1 from CI.

## Docket items I would open

| # | Item | Severity |
|---|---|---|
| Co.1 | `else if` short-form syntax (ergonomic, not blocking) | LOW |
| Co.2 | Document closure ABI (`{ptr, ptr}` with `env=null` for no-capture) in SPEC | LOW |

Cl.1, Ih.1, Div.4 are already docketed.

## Grade justification

Up from 7.5 to 8.0. All three HIGH items in my lens are closed with faithful regression tests. The Cl.1 miscompile is serious but narrow (one pattern, one pipeline) and belongs to Rattler. PASS WITH NOTES, not PASS, because I will not certify a language feature that returns wrong values under the default release pipeline without flagging it.

## One-line summary

Three HIGH items closed with good regression coverage; `-O2` miscompile on one closure pattern prevents a clean PASS.
