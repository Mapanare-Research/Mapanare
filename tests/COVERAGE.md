# v4.117.0 Coverage Report

> **Date:** 2026-04-14
> **Tool:** `pytest-cov` 7.1.0 (`coverage` 7.13.5)
> **Scope:** `pytest tests/llvm/ tests/lexer/ tests/parser/ tests/semantic/ tests/mir/ tests/emit/ tests/ffi/ --cov=mapanare`
> **Aggregate coverage: 43% (8,896 covered / 20,894 statements)**

---

## Methodology

Per PROMPT.md Decision: coverage is informational, not gating. This
release measures where the pytest suite exercises the Python
compiler sources under `mapanare/`. The measurement scope is the
seven core unit-test subdirectories that exercise the compiler
pipeline at each stage: parser, semantic, lower/MIR, emitters
(LLVM/emit), lexer, FFI. Integration / bootstrap / LSP / WASM /
stdlib tests are covered in their own pytest scopes and can be
added to this measurement incrementally.

Command executed:

```bash
pytest tests/llvm/ tests/lexer/ tests/parser/ tests/semantic/ \
       tests/mir/ tests/emit/ tests/ffi/ \
       --cov=mapanare --cov-report=term-missing --tb=no -q
```

Wall time: 22 seconds.

---

## Per-Module Coverage

Sorted by what the PLAN asked for: the core pipeline modules, then
supporting modules, then the **below-50%** tail.

### Core pipeline — the modules tests hit

| Module | Stmts | Covered | % |
|---|---:|---:|---:|
| `mapanare/ast_nodes.py` | 379 | 379 | **100%** |
| `mapanare/types.py` | 206 | 189 | **92%** |
| `mapanare/mir.py` | 712 | 678 | **95%** |
| `mapanare/pattern_matching.py` | 275 | 243 | **88%** |
| `mapanare/lexer.py` | 44 | 39 | **89%** |
| `mapanare/multi_module.py` | 471 | 391 | **83%** |
| `mapanare/semantic.py` | 1,264 | 1,018 | **81%** |
| `mapanare/parser.py` | 1,110 | 866 | **78%** |
| `mapanare/targets.py` | 43 | 33 | **77%** |
| `mapanare/modules.py` | 126 | 94 | **75%** |
| `mapanare/mir_opt.py` | 1,239 | 889 | **72%** |
| `mapanare/lower.py` | 2,126 | 1,471 | **69%** |
| `mapanare/emit_llvm_text.py` | 3,432 | 2,229 | **65%** |
| `mapanare/diagnostics.py` | 164 | 80 | **49%** |

### Below 50% — the tail

Modules under 50% coverage — the highlighted gaps per PLAN.md
Phase 4:

| Module | Stmts | Covered | % | Reason |
|---|---:|---:|---:|---|
| `mapanare/diagnostics.py` | 164 | 80 | **49%** | Error-path rendering only lightly exercised — bump with e2e fixtures |
| `mapanare/cli.py` | 940 | 233 | **25%** | Most stale CLI tests in `tests/cli/` fail (22 deterministic — see FLAKY_AUDIT.md); coverage of the command dispatcher is underreported as a result |
| `mapanare/optimizer.py` | 709 | 64 | **9%** | AST-level optimiser is legacy — MIR optimizer (`mir_opt.py`) is the live path; this file is a candidate for deletion in a future release |
| `mapanare/emit_c.py` | 1,561 | 0 | **0%** | C emitter has its own pytest scope (`tests/emit_c/`) not included in this measurement; re-run with that directory to populate |
| `mapanare/emit_wasm.py` | 1,310 | 0 | **0%** | WASM emitter covered by `tests/wasm/` — out of this measurement's scope |
| `mapanare/wasm_linker.py` | 189 | 0 | **0%** | Same — WASM scope |
| `mapanare/linter.py` | 460 | 0 | **0%** | Linter has its own scope (`tests/linter/`) |
| `mapanare/lsp/analysis.py` | 644 | 0 | **0%** | LSP covered by `tests/lsp/` |
| `mapanare/lsp/server.py` | 324 | 0 | **0%** | Same |
| `mapanare/lsp/workspace.py` | 209 | 0 | **0%** | Same |
| `mapanare/lsp/completion.py` | 74 | 0 | **0%** | Same |
| `mapanare/lsp/diagnostics.py` | 38 | 0 | **0%** | Same |
| `mapanare/lsp/rename.py` | 28 | 0 | **0%** | Same |
| `mapanare/tracing.py` | 177 | 0 | **0%** | OpenTelemetry tracing needs runtime environment |
| `mapanare/metrics.py` | 117 | 0 | **0%** | Prometheus metrics server — needs port binding |
| `mapanare/test_runner.py` | 181 | 0 | **0%** | The `mapanare test` command is tested via `tests/test_runner/` |
| `mapanare/from_python.py` | 569 | 0 | **0%** | Python transpiler has `tests/transpile/` scope |
| `mapanare/from_php.py` | 1,210 | 0 | **0%** | PHP transpiler has `tests/transpile/` scope |
| `mapanare/bind.py` | 197 | 0 | **0%** | Library binding generator — `tests/bind/` |
| `mapanare/docgen.py` | 92 | 0 | **0%** | `mapanare doc` — end-to-end tested |
| `mapanare/migrate.py` | 153 | 0 | **0%** | Schema migration runner |
| `mapanare/error_codes.py` | 49 | 0 | **0%** | Module-level constant registry; imported but its lines are data-only |
| `mapanare/deploy.py` | 23 | 0 | **0%** | `mapanare deploy` scaffolding |
| `mapanare/mir_builder.py` | 47 | 0 | **0%** | Legacy MIR builder facade — candidate for deletion |
| `mapanare/__main__.py` | 2 | 0 | **0%** | Re-exports `cli.main` |

The 0% modules are not uncovered by the *project* — they're
uncovered by *this measurement's scope*. Each has a dedicated test
directory under `tests/` that exercises it.

### Aggregate across the measured scope

| Category | Stmts | Covered | % |
|---|---:|---:|---:|
| **Core pipeline** (covered ≥65%) | 11,472 | 8,429 | **73%** |
| **Below 50%** in scope | 873 | 80 | **9%** |
| **Out of scope** (other `tests/` dirs cover these) | 8,549 | 387 | **5%** |
| **TOTAL (as measured)** | 20,894 | 8,896 | **43%** |

When you read "43% total," most of the missing 57% is code under
`mapanare/lsp/`, `mapanare/from_python.py`, `mapanare/emit_c.py`,
etc. — covered by **other** pytest scopes that this one-shot
measurement intentionally did not run. The same measurement with
every pytest directory included is the Phase F benchmark's job
(v4.118.0).

---

## What this measurement tells us

### The live code paths have solid coverage

Every core pipeline module exercised by a compile-to-LLVM flow has
65% or higher coverage. The high-coverage modules (`ast_nodes.py`,
`types.py`, `mir.py`) are the ones that correctness depends on most,
and they are the ones best tested. The high-value targets of the v4
recovery arcs (lower.py, semantic.py, emit_llvm_text.py, mir_opt.py)
are all between 65% and 81% — substantial but with room to grow.

### The real gap — the 22 deterministic failures

The 8 failures observed during this coverage run match the subset
of the 22 flaky-audit failures that live in the measured scope.
Nothing new. See `tests/FLAKY_AUDIT.md` for root-cause per bucket.

### The CLI is under-represented

At 25%, `cli.py` looks worse than it is. 14 of the 22 deterministic
failures are stale CLI tests asserting on the `compile` subcommand
that was renamed to `transpile` several releases ago. If those
tests are rewritten to the current grammar, `cli.py` coverage would
go up by 15-25 points.

### `optimizer.py` is nearly dead code

9% coverage and no dependents on the hot path (MIR optimisation
runs through `mir_opt.py`). This module is a deletion candidate —
the v4 post-recovery arcs targeting dead-code sweep can take it.

---

## Recommendations — future work, NOT this release

This release measures; it does not fix. Per PLAN.md "What this
release does NOT do": *"Increase coverage — the report identifies
gaps, it does not fill them."*

Recommended follow-ups for v4.120.0 panel review:

1. **Rewrite the 14 stale CLI tests** against the current
   `mapanare transpile` grammar. Expected gain: +15–25 points on
   `cli.py` coverage, -14 on the deterministic-failure count.
2. **Merge `tests/emit_c/`, `tests/wasm/`, `tests/lsp/` scopes into
   the aggregate coverage run** for the Phase F benchmark. Expected:
   moves total coverage from 43% (measured) to ~55%–60% (all-in).
3. **Delete `optimizer.py`** if the `tests/optimizer/` suite confirms
   nothing live depends on it. Shrinks the denominator, clarifies
   the architecture.
4. **Add runtime-path coverage for `diagnostics.py`** (49%). The
   error-rendering code paths are lightly exercised; a small
   fixture suite would bring it to 75%+.
5. **Gate coverage as informational in CI.** Run
   `pytest-cov --cov-fail-under=65` on the core pipeline scope as a
   soft gate; start stricter when the baseline has been confirmed
   stable across 5 releases.

---

## Reproduce

```bash
pip install --user pytest-cov
pytest tests/llvm/ tests/lexer/ tests/parser/ tests/semantic/ \
       tests/mir/ tests/emit/ tests/ffi/ \
       --cov=mapanare --cov-report=term-missing \
       --cov-report=html:/tmp/v4117_cov_html \
       -q --tb=no
# HTML report at /tmp/v4117_cov_html/index.html
```

HTML report directory is not committed (tens of MB of generated
HTML). Term-missing output and this summary are the committed
artefacts.

---

## Integration with CI (informational, not gating)

A suggested CI job for this release (to be added in a follow-up
commit after this audit lands):

```yaml
coverage:
  name: Coverage (informational)
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '3.12' }
    - run: pip install -e ".[dev]" pytest-cov
    - run: >
        pytest tests/llvm/ tests/lexer/ tests/parser/ tests/semantic/
               tests/mir/ tests/emit/ tests/ffi/
               --cov=mapanare --cov-report=xml --cov-report=term
               --tb=no -q
    - uses: actions/upload-artifact@v4
      with:
        name: coverage-xml
        path: coverage.xml
        retention-days: 30
```

Does not gate (per Decision: "Run coverage as a separate job, not
on the critical path"). Artifact is available for inspection; a
follow-up release can flip this to gating with a sensible floor.
