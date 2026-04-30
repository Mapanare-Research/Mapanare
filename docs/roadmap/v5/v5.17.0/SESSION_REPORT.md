# v5.17.0 — Sh.* — self-host rewrite to terse syntax

**Date:** 2026-04-30
**Status:** Shipped (not yet tagged)
**Prerequisites:** v5.13.0 (`mnc fmt`), v5.14.0/v5.14.1 (colon
blocks + bootstrap mirror), v5.15.0/v5.15.1 (comprehensions +
implicit-return + bootstrap mirror), v5.16.0 (string-interp
parity).

---

## Summary

The mechanical brace → colon rewrite of `mapanare/self/*.mn`. All
17 hand-edited modules processed via `mapanare fmt --to-terse` in
dependency order, one commit per module, with stage1 build +
goldens 80/80 validated between every commit. Strict 3-stage fixed
point preserved (231,957 lines, 0-line diff). Bootstrap seed
refreshed (the v5.10.0-vintage Linux seed segfaulted on
colon-block source).

**No semantic change.** The IR `mnc-stage1` emits is byte-identical
to v5.16.0 modulo the version-metadata string. This is the headline
release of the v5.13–v5.21 terseness arc — the language now ships
in its canonical terse form.

---

## Mechanical line-count delta (Sh.B)

`mnc_all.mn` is generated from the per-module sources by
`scripts/concat_self.py` and listed separately because it's the
largest single file in the tree.

| Module | Before | After | Δ | % shrink |
|---|---:|---:|---:|---:|
| abi.mn | 94 | 89 | -5 | 5.3% |
| ast.mn | 952 | 760 | -192 | 20.2% |
| lexer.mn | 601 | 533 | -68 | 11.3% |
| emit_llvm_ir.mn | 275 | 224 | -51 | 18.5% |
| mir.mn | 921 | 774 | -147 | 16.0% |
| lower_state.mn | 595 | 509 | -86 | 14.5% |
| parser.mn | 2,749 | 2,390 | -359 | 13.1% |
| semantic.mn | 2,292 | 2,002 | -290 | 12.7% |
| lower.mn | 5,157 | 4,554 | -603 | 11.7% |
| emit_llvm.mn | 6,428* | 5,782 | -646 | 10.0% |
| main.mn | 1,334 | 1,137 | -197 | 14.8% |
| mir_opt.mn | 1,880 | 1,619 | -261 | 13.9% |
| transpiler.mn | 596 | 500 | -96 | 16.1% |
| from_python.mn | 578 | 490 | -88 | 15.2% |
| from_go.mn | 1,524 | 1,271 | -253 | 16.6% |
| from_php.mn | 1,161 | 972 | -189 | 16.3% |
| from_typescript.mn | 1,561 | 1,311 | -250 | 16.0% |
| **Sources total** | **28,698** | **24,917** | **-3,781** | **13.2%** |
| mnc_all.mn (regen) | 23,282 | 20,377 | -2,905 | 12.5% |

`*` `emit_llvm.mn` baseline of 6,428 is the pre-rewrite line count
on the v5.16.0 HEAD post-Sh.A.1.C `}}` canonicalization (4 sites
re-indented during Phase 0 to make the module amenable to
`--to-terse`).

The 13.2% mechanical shrink falls short of the PLAN's 30% target.
Comprehension upgrades (Sh.C) and implicit-return upgrades (Sh.D)
are deferred to v5.17.1 where the per-site judgment work will close
some of the remaining gap. The 30% target was always
arc-cumulative; the v5.13–v5.21 arc has more terseness wins to
ship.

---

## Per-module commit ledger (dependency order)

| Order | Module | Commit | Δ |
|---:|---|---|---:|
| 1 | abi.mn | `1807675` | -5 |
| 2 | ast.mn | `4c56295` | -192 |
| 3 | lexer.mn | `acd6270` | -68 |
| 4 | emit_llvm_ir.mn | `a9515ac` | -51 |
| 5 | mir.mn | `28026f7` | -147 |
| 6 | lower_state.mn | `d6a6a8f` | -86 |
| 7 | parser.mn | `53af337` | -359 |
| 8 | semantic.mn | `7250b22` | -290 |
| 9 | lower.mn | `e5aed85` | -603 |
| 10 | emit_llvm.mn | `caa4113` | -646 |
| 11 | main.mn | `65ce247` | -197 |
| 12 | mir_opt.mn | `a964182` | -261 |
| 13 | transpiler.mn | `381b954` | -96 |
| 14 | from_python.mn | `f74a0d5` | -88 |
| 15 | from_go.mn | `78aff77` | -253 |
| 16 | from_php.mn | `44498c4` | -189 |
| 17 | from_typescript.mn | `e8ed30a` | -250 |
| - | mnc_all.mn (regen) | `70b052c` | -2,905 |
| - | bootstrap seed refresh | `590169e` | (binary) |

Every per-module commit was gated on:

- `python3 scripts/build_stage1.py` — stage1 builds green.
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  — goldens 80/80 pass.

No module required a revert. Phase 0 (Sh.A.1.A/B/C, shipped
ab057e0) preemptively fixed three v5.14.0-era latent rewriter bugs;
the per-module rewrite ran to completion without surfacing further
issues.

---

## Sh.E — bootstrap seed refresh

`bash scripts/build_from_seed.sh` (the no-Python pipeline)
segfaulted at stage 1 against the new colon-block sources because
the Linux seed at `bootstrap/seed/linux-x86_64/mnc` was a v5.10.0
binary that predates v5.14.0's `_indent_to_braces` preprocessor.
Refreshed seed from this branch's `mapanare/self/mnc-stage1`. New
`mnc.sha256`:

```
929e7a4b87f7b3f04f10b50fd108e034bb4b8ae361298b37b55db7988b19b0a0  mnc
```

Post-refresh validation:

- Seed checksum: OK
- Stage 1 IR: 231,957 lines
- Stage 2 IR: 231,957 lines
- Stage 2 IR `llvm-as` validation: OK
- Final binary smoke test: OK

---

## Sh.F — strict 3-stage fixed point

```
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 231957 lines
  llvm-as: OK
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 231957 lines
  llvm-as: OK
[Verify] diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (231957 lines, 0 diff)
```

The v5.9.0 strict-fixed-point milestone is preserved across the
mechanical rewrite. This is the load-bearing assertion for the
release: the 17-module rewrite is `to_terse` followed by parser-
synthesis-back-to-the-same-AST, so the IR shape is conserved by
construction. The 0-diff result confirms the rewriter is sound.

The teardown crash on `mnc-stage2` (exit code 3) is the same known
issue tracked for v4.30.0; `verify_fixed_point.sh` already validates
that stage3.ll is non-empty and llvm-valid below the teardown
return.

---

## Goldens

- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  → **All 80 tests passed in 14–16s** at every per-module commit
  and at the final HEAD.

---

## Out of scope (deferred)

- **Sh.C — comprehension upgrades** (per-site judgment). Slipped to
  v5.17.1 along with Sh.D and Sh.G. The mechanical pass alone is the
  releasable v5.17.0 unit; bundling Sh.C/D/G into v5.17.0 would have
  blocked the strict-fixed-point payoff release behind ~6 more hours
  of judgment work.
- **Sh.D — implicit-return upgrades.** Slipped to v5.17.1.
- **Sh.G — SPEC.md / README.md / CLAUDE.md example refresh.**
  Slipped to v5.17.1 (the docs polish naturally pairs with the
  per-site upgrades since both are about how the canonical examples
  read).

The v5.17.1 PLAN is already authored at
`docs/roadmap/v5/v5.17.1/PLAN.md`; the work resumes there.

---

## Validation summary

| Check | Result |
|---|---|
| Stage1 build at every per-module commit | ✅ 17/17 |
| Goldens 80/80 at every per-module commit | ✅ |
| Strict 3-stage fixed point (post-`mnc_all.mn` regen) | ✅ 0-diff |
| Bootstrap seed refresh + `build_from_seed.sh` | ✅ |
| Final stage2.ll line count | 231,957 (== v5.16.0) |

---

## Files committed

- `mapanare/self/abi.mn`
- `mapanare/self/ast.mn`
- `mapanare/self/lexer.mn`
- `mapanare/self/emit_llvm_ir.mn`
- `mapanare/self/mir.mn`
- `mapanare/self/lower_state.mn`
- `mapanare/self/parser.mn`
- `mapanare/self/semantic.mn`
- `mapanare/self/lower.mn`
- `mapanare/self/emit_llvm.mn`
- `mapanare/self/main.mn`
- `mapanare/self/mir_opt.mn`
- `mapanare/self/transpiler.mn`
- `mapanare/self/from_python.mn`
- `mapanare/self/from_go.mn`
- `mapanare/self/from_php.mn`
- `mapanare/self/from_typescript.mn`
- `mapanare/self/mnc_all.mn` (regenerated)
- `bootstrap/seed/linux-x86_64/mnc` (refreshed)
- `bootstrap/seed/linux-x86_64/mnc.sha256`

---

## Next

- v5.17.1 — Sh.C + Sh.D + Sh.G. PLAN already authored.
- v5.18.0 — Mc.1/3/4 — tooling pack (LSP, `mnc init`, `mnc check`,
  VSCode extension).
