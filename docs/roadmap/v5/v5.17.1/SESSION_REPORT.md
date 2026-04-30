# v5.17.1 — Sh.C + Sh.D + Sh.G — terse polish

**Date:** 2026-04-30
**Status:** Shipped (not yet tagged)
**Prerequisites:** v5.17.0 (mechanical brace → colon rewrite,
bootstrap seed refresh).

---

## Summary

Per-site judgment follow-up to v5.17.0's mechanical Sh.B rewrite.
Three deliverables, 20 commits.

1. **Sh.C** — list comprehensions where the manual loop was
   strictly accumulator-shaped (3 sites).
2. **Sh.D** — implicit-return upgrades across all 16 modules:
   one-liner form (`fn name() -> T = expr`) and block-form
   (drop trailing `return` keyword).
3. **Sh.G** — SPEC.md / README.md / CLAUDE.md examples refreshed
   to terse + idiomatic style.

**Goldens 80/80** at every per-module commit and at HEAD. **Strict
3-stage fixed point preserved**: stage2.ll == stage3.ll at 231,957
lines / 0-line diff. `bash scripts/build_from_seed.sh` succeeds
unchanged. NO seed refresh required (zero new C-runtime exports;
no parser changes; the v5.15.0 Te.2.D function-init form and
v5.14.0 Te.1 block-form implicit return have both been bootstrap-
ready since their respective releases).

**No semantic change.** The IR `mnc-stage1` emits is byte-identical
to v5.17.0 modulo the version-metadata string.

---

## Per-module line-count delta (Sh.D.B + Sh.C.B)

| Module | v5.17.0 | v5.17.1 | Δ |
|---|---:|---:|---:|
| abi.mn | 89 | 89 | 0 |
| ast.mn | 760 | 749 | -11 |
| lexer.mn | 533 | 529 | -4 |
| emit_llvm_ir.mn | 224 | 181 | -43 |
| mir.mn | 774 | 749 | -25 |
| lower_state.mn | 509 | 508 | -1 |
| parser.mn | 2,390 | 2,370 | -20 |
| semantic.mn | 2,002 | 1,982 | -20 |
| lower.mn | 4,554 | 4,549 | -5 |
| emit_llvm.mn | 5,782 | 5,769 | -13 |
| main.mn | 1,137 | 1,132 | -5 |
| mir_opt.mn | 1,619 | 1,618 | -1 |
| transpiler.mn | 500 | 486 | -14 |
| from_python.mn | 490 | 488 | -2 |
| from_go.mn | 1,271 | 1,269 | -2 |
| from_php.mn | 972 | 970 | -2 |
| from_typescript.mn | 1,311 | 1,310 | -1 |
| **Sources total** | **24,917** | **24,748** | **-169** |
| mnc_all.mn (regen) | 20,377 | 20,229 | -148 |

**Cumulative v5.13.0 → v5.17.1 shrink:** the sources baseline at
v5.13.0 was 28,698 lines. v5.17.1 brings them to 24,748 — a
reduction of **3,950 lines (-13.8%)** off the v5.13.0 baseline.

The v5.17.1 delta is modest because BLOCK_SHORT conversions don't
drop lines (`return E` and bare `E` both occupy one line); the
-169 figure is essentially the ONELINER count (one line saved per
site, plus blank-line collapse).

---

## Sh.C.B — Comprehension upgrades (1 commit, 3 sites)

| Site | Verdict |
|---|---|
| `transpiler.mn:343` (match arm `rest`) | applied |
| `transpiler.mn:407` (`pop_scope::new_vars`) | applied |
| `transpiler.mn:411` (`pop_scope::new_markers`) | applied |
| `from_go.mn:559` (prepend pattern) | SKIP |
| `from_typescript.mn:543` (prepend pattern) | SKIP |

12+ sites in `lower.mn`/`parser.mn`/`emit_llvm.mn` matched the
defensive-iteration pattern (`for _ in 0..LARGE: if i < n`), all
SKIP'd as out-of-scope-for-syntax-only. Catalogued in
`COMPREHENSION_SITES.md` for any future revisit.

The `transpiler.mn` commit doesn't trigger a fixed-point change
because `transpiler.mn` is excluded from `mnc_all.mn` by
`scripts/concat_self.py`. Validated via 63/63 transpiler tests.

---

## Sh.D.B — Implicit-return upgrades (16 commits, ~280 sites)

| Module | ONELINER | BLOCK_SHORT | Total |
|---|---:|---:|---:|
| emit_llvm_ir.mn | 43 | 0 | 43 |
| mir.mn | 25 | 5 | 30 |
| parser.mn | 20 | 11 | 31 |
| semantic.mn | 20 | 15 | 35 |
| ast.mn | 11 | 1 | 12 |
| emit_llvm.mn | 13 | 17 | 30 |
| lower.mn | 5 | 12 | 17 |
| lexer.mn | 4 | 0 | 4 |
| transpiler.mn | 4 | 12 | 16 |
| mir_opt.mn | 1 | 5 | 6 |
| lower_state.mn | 1 | 8 | 9 |
| main.mn | 5 | 7 | 12 |
| from_python.mn | 2 | 5 | 7 |
| from_go.mn | 2 | 9 | 11 |
| from_php.mn | 2 | 7 | 9 |
| from_typescript.mn | 1 | 7 | 8 |
| **Total** | **159** | **121** | **280** |

ONELINER form (`fn name() -> T = expr`) lowers to
`Block([ReturnStmt(expr)])` at parse time — semantically and
MIR-shape identical to the original (v5.15.0 Te.2.D).

BLOCK_SHORT form drops the trailing `return` keyword to leave a
bare expression as the function-tail value (v5.14.0 Te.1 + SPEC
§4.5).

**Strict single-return filter.** Only functions with EXACTLY ONE
`\breturn\b` substring in the body (string literals stripped) AND
that return is the LAST non-blank, non-comment line at body
indent. The filter excludes any function with early returns
embedded in `if X { return Y }` or nested branches — those keep
their explicit `return` because dropping the trailing keyword
would change the semantics of the early-return ladder.

**BLOCK_LONG (>5 prelude statements) deliberately SKIP'd: 28
sites.** In a 30-line function the explicit `return` keyword is a
punctuation marker readers scan for; stripping it for one-line
saves a keyword at a real readability cost. Catalogued in
`IMPLICIT_RETURN_SITES.md`.

---

## Sh.G — Documentation refresh (3 commits)

- `docs/SPEC.md` — §4.2 For Loop, §4.3 While Loop, §4.5 Return
  refreshed to colon-block; §4.5 expanded with implicit-return
  examples; §4.2 expanded with comprehension cross-reference.
  SPEC compliance/crossref tests 137/137.
- `README.md` — Hello world and flagship "Language Features"
  example refreshed to colon-block. Goldens reference updated to
  80/80 (was 68/68 / v5.15.0). Fixed-point line count updated to
  231,957 (was 226k / v5.9.0).
- `CLAUDE.md` — Added v5.17.1 release-notes entry; marked v5.17.0
  as shipped (was "ready, not tagged"); marked v5.17.1 as shipped
  in the Planned/in-progress section.

---

## Phase 0 hygiene fix — runtime archive refresh

The v5.17.0 SESSION_REPORT documented strict 0-line fixed point.
At v5.17.1 baseline before any source change, the verify_fixed_point.sh
output was NEAR (4-line metadata diff) — the cached
`runtime/native/libmapanare_rt.a` artifact was built at v5.16.0 and
baked `MAPANARE_VERSION="5.16.0"` into the stage2 binary used to
produce stage3.ll.

`make build-rt` rebuilt the archive against the current VERSION
file (5.17.0 → 5.17.1 across the v5.17.1 work) and restored strict
0-line fixed point. Not a source fix, but worth documenting because
verify_fixed_point.sh's pickup-cached-artifact-when-present logic
makes the runtime archive a load-bearing input for the strict-0
claim.

---

## Per-commit ledger (v5.17.0 → v5.17.1)

```
2c3976d v5.17.1 Sh.C.B: comprehensions in transpiler.mn (3 sites)
3199235 v5.17.1 Sh.D.B: implicit return in emit_llvm_ir.mn (43 sites)
2d935c9 v5.17.1 Sh.D.B: implicit return in mir.mn (30 sites)
1928e6b v5.17.1 Sh.D.B: implicit return in parser.mn (31 sites)
dfce46f v5.17.1 Sh.D.B: implicit return in semantic.mn (35 sites)
281860a v5.17.1 Sh.D.B: implicit return in ast.mn (12 sites)
c5bb751 v5.17.1 Sh.D.B: implicit return in emit_llvm.mn (30 sites)
1a3cb76 v5.17.1 Sh.D.B: implicit return in lower.mn (17 sites)
f25298f v5.17.1 Sh.D.B: implicit return in lexer.mn (4 sites)
ed29131 v5.17.1 Sh.D.B: implicit return in mir_opt.mn (6 sites)
07e2424 v5.17.1 Sh.D.B: implicit return in lower_state.mn (9 sites)
e27d279 v5.17.1 Sh.D.B: implicit return in transpiler.mn (16 sites)
b0e201e v5.17.1 Sh.D.B: implicit return in from_python.mn (7 sites)
cbdec63 v5.17.1 Sh.D.B: implicit return in from_go.mn (11 sites)
a1c92bc v5.17.1 Sh.D.B: implicit return in from_php.mn (9 sites)
243575d v5.17.1 Sh.D.B: implicit return in from_typescript.mn (8 sites)
aab13b7 v5.17.1 Sh.D.B: implicit return in main.mn (12 sites)
b615a56 v5.17.1 Sh.G.C: refresh CLAUDE.md release-notes preamble
b47f805 v5.17.1 Sh.G.B: refresh README.md flagship example to terse style
bca20f9 v5.17.1 Sh.G.A: refresh SPEC.md examples to terse style
```

Plus closeout (this commit) and version bump.

Every per-module commit was gated on:

- `python3 scripts/build_stage1.py` — stage1 builds green.
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  — goldens 80/80 pass.
- `bash scripts/verify_fixed_point.sh` — strict 0-line diff
  (for files that affect mnc_all.mn).
- For the 5 transpiler modules (excluded from mnc_all.mn):
  `python3 -m pytest tests/transpiler/ tests/self_hosted_transpiler/` 63/63.

---

## Final validation

| Check | Result |
|---|---|
| `python3 scripts/build_stage1.py` | OK |
| Goldens (80/80) | PASS |
| `verify_fixed_point.sh` (231,957 lines, 0 diff) | STRICT |
| `build_from_seed.sh` (no Python) | OK |
| `make lint` (ruff + black + mypy) | clean |
| Full pytest sweep | 7,180 passed, 8 pre-existing failures, 237 skipped, 11 xfailed |

The 8 pre-existing failures are stable from v5.16.0/v5.17.0 and
unrelated to this release scope (6 × WSL/MinGW gcc.exe environment
+ 1 × `lower_state.mn::LowerState` registry drift +
1 × CLI `test_run_hello`).

---

## Out-of-scope (deferred)

- BLOCK_LONG implicit-return upgrades (28 sites) — judgment call,
  catalogued in `IMPLICIT_RETURN_SITES.md`.
- Defensive `for _ in 0..LARGE: if i < n` → comprehension rewrites
  — would require also removing the artificial bound, which is
  logic refactoring not syntax-only rewrite. Catalogued in
  `COMPREHENSION_SITES.md`.
- `examples/` rewrite to terse style — slated for v5.19.0 Te.3.D
  (alongside soft-deprecation of `{}`).
- `mapanare/*.py` (Python bootstrap) — out of v5.17.x scope.
- `tests/`, `stdlib/` — out of v5.17.x scope.
- Soft-deprecation of `{}` syntax — slated for v5.19.0 Te.3.

---

## Next

- v5.18.0 — Mc.1/3/4 — tooling pack (LSP, `mnc init`, `mnc check`,
  VSCode extension). PLAN at `docs/roadmap/v5/v5.18.0/PLAN.md`.
- v5.19.0 — Te.3 + Dk.* — closeout (soft-deprecate `{}`, ship
  Docker images). PLAN at `docs/roadmap/v5/v5.19.0/PLAN.md`.
- v5.20.0 — Te.5 — struct ergonomics (post-rewrite intentional).
