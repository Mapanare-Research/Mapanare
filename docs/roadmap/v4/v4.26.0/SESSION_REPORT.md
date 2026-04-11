# v4.26.0 Session Report — 2026-04-10 (reconstructed 2026-04-11)

> **This report was not written at v4.26.0's release. It is a retrospective
> written during the v4.27.0 recovery so the release record contains a
> truthful accounting of what v4.26.0 actually shipped vs. what the
> CHANGELOG claimed at the time of the tag.** See
> `.reviews/v4.26.0/README.md` for the 7-reviewer panel response.

## Verdict
- **Panel:** 4 NEEDS WORK + 3 PASS WITH NOTES, 0 unconditional PASS.
- **Aggregate score:** ~8.2/10 (down from 9.79/10 at v3.47.0 — largest
  single-cycle regression in project history).
- **First non-unanimous panel since v3.33.0.** First NEEDS WORK verdicts
  since v3.33.0.

## What was claimed vs what shipped

| Claim | Ground truth |
|---|---|
| `const` keyword for compile-time constants | Parser alias for `ModuleLetDef`. No `ConstDef` AST node. No immutability enforcement. No compile-time evaluation. |
| `tests/parser/test_const.py` + `tests/semantic/test_const.py` | **Files did not exist on disk at tag time.** CHANGELOG entry was false. |
| `tests/golden/47_const.mn` | **Did not exist on disk.** Golden count was 46, not 47. The file exists as `42_const.mn` and `43_gpu_kernel.mn`, but both used the parser-only `const` keyword. |
| `Tensor<Float, [DIM, DIM]>` syntax | Grammar parses `Tensor<Float>[DIM, DIM]`. The comma-inside-angle-brackets form the CHANGELOG advertised **never parsed.** |
| `Tensor<Float>[N, N]` with named dimensions | `resolve_shape_from_type` only recognised `IntLiteral` shape arguments, so `[N, N]` silently dropped the shape and returned a dimensionless tensor type. |
| Roadmap consolidation: top-level `ROADMAP.md` + `docs/roadmap/v4/README.md` refreshed | **True.** This was the only claim in the release that was both real and useful — the roadmap tables really were updated from stale v4.0.0 content to the v4.26.0 state. |

## Hollow features carried across v4.18.0 → v4.26.0

v4.26.0 was not the first release with this pattern — the panel found a
consistent drift across eight versions. Five of seven reviewers
independently described the arc with the phrase "hollow features":

1. **`const` keyword** (v4.18.0, v4.26.0) — parser alias only.
2. **`@gpu` / `@cuda` / `@vulkan`** (v4.18.0) — `raise NotImplementedError`
   at `lower.py:986`. The compiler crashed the moment a decorated function
   was actually compiled.
3. **`await expr`** (v4.24.0) — lowers to `return self._lower_expr(expr.expr)`.
   Pure identity. No coroutine state machine, no suspension point, no
   Stream integration.
4. **Tensor `[N, N]` shape resolution** (v4.18.0, v4.25.0) — `const`
   dimensions never resolved because the `const_def` transformer collapsed
   the full `TypeExpr` to a bare `.name` string at parse time.
5. **v4.25.0 FFI** — `bind.py` generated ctypes wrappers with no
   `argtypes`/`restype` (so only `add(int, int) -> int` worked, by
   coincidence); DCE dropped every public function not reachable from
   `main`; the runtime archive was not built `-fPIC`; the
   `ll_text.replace("define internal ", "define ")` sledgehammer stripped
   `internal` linkage from **every** function in the module.
6. **v4.5.0 MIR verifier** — `MIRVerifier` defined in `mir.py:1118-1259`
   but called from zero sites in the compile pipeline. The v4.5.0 CHANGELOG
   said "MIR verifier before emission." False for 21 versions.

## Process findings

- **Carry-forward resolution rate collapsed** from ~64% (v3.47.0) to ~10%
  (v4.26.0). Rattler resolved 0/12 from his own carry-forward queue this
  cycle — the worst single-cycle performance in project history.
- **Two v4.0.0 hard-blockers byte-identical to v3.47.0** — matmul shape
  NULL check and dimension validation (`mapanare_gpu_builtins.c:161-185`).
  27 review-versions overdue. Suggests a revert happened and was not
  flagged.
- **`main.ll` version string is `mapanare 4.7.1`** — 19 versions stale.
  The regression test for this (`tests/self_hosted/test_main_mn.py::test_version_string`)
  is currently failing locally.
- **`extern "Python" fn` silently xfailed** — 79 tests marked xfail via
  `tests/conftest.py` since `emit_python.py` was deleted in v4.2.0. The
  panel missed this at the time. Flag from v3.47.0 to v4.2.0 and forward.
- **`verify_fixed_point.sh` cannot fail.** `EXIT=0` unconditional; the CI
  `fixed-point` job has no `exit 1` in the workflow either. The v4.17.0
  "Python bootstrap is optional" guarantee is **unfalsifiable by
  construction.**
- **`stage3.ll` is a zero-byte file from 2026-03-21** — predates v4.20.0.
  The v4.17.0 "fixed-point self-compilation" claim is no longer backed by
  any on-disk artifact.

## What the code actually does well

The panel was uniformly positive about the v4.2.0–v4.17.0 structural
refactor arc:

- Emitter consolidation (3 → 1) held up.
- MIRType enum migration (v4.23.0, 110+ comparison sites) held up.
- Dead block elimination (v4.22.0) held up.
- Drop glue rewrite (v4.3.0, v4.10.0, v4.13.0) held up — C runtime has
  zero new races from the drop path.
- Fixed-point bootstrap as a concept is correct — the falsification
  teeth are missing, but the architecture is not.

Coral: "the compiler core is in the best shape of its life." Mamba:
"the C runtime is the most disciplined piece of the project."

## Recovery arc (opened in v4.27.0)

The next five versions are a recovery arc. Zero new features. Each has
explicit no-new-features exit criteria.

| # | Version | Theme |
|---|---------|-------|
| 1 | **v4.27.0** | Honesty Recovery (CRITICAL items) |
| 2 | **v4.28.0** | Concurrency + v3.47.0 carry-forwards |
| 3 | **v4.29.0** | Build infrastructure + test honesty |
| 4 | **v4.30.0** | Codegen + emitter carry-forwards |
| 5 | **v4.31.0** | Documentation truth + process hardening |

The arc terminates **externally**. v4.31.0 ships only when the next
7-reviewer panel returns aggregate ≥9.0 with zero NEEDS WORK verdicts.
If the panel does not agree, v4.32.0 inherits the outstanding items and
the arc continues.

## Files

- `.reviews/v4.26.0/README.md` — the 7-reviewer panel summary
- `.reviews/v4.26.0/01-viper.md` through `07-coral.md` — individual reviews
- `docs/roadmap/v4/RECOVERY_MASTER_PROMPT.md` — the master prompt for the arc
- `docs/roadmap/v4/v4.27.0/PLAN.md` — v4.27.0 phase breakdown
- `docs/roadmap/v4/v4.27.0/SESSION_REPORT.md` — v4.27.0 recovery results
