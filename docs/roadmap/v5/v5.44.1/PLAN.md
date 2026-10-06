# v5.44.1 — Ps.11 + Ps.12 — scripts parity + gitignore template

**Status:** PLANNING
**Type:** Hotfix / parity-completion release. Extends v5.44.0 Ps.3
beyond the `mapanare/` boundary (scripts/ + benchmarks/) and closes
a real reproducibility gap in the project init template. Small,
tactical, no language or runtime surface changes.
**Breaking:** No.
**Prerequisite:** v5.44.0 shipped (Ps.\* package-system runway).
**Estimated effort:** 2–4 hours. Mostly resolver wiring + one
template file edit + tests.

---

## Why this exists

v5.44.0 closed CLI-side resolver parity: every `mnc` subcommand
that compiles or checks `.mn` source routes through
`_build_resolver_from_args` and exposes the same `--stdlib-path`,
`--extra-path`, `--verbose`, `--diag-json` surface. **The contract
stops at the `mapanare/` boundary.** Outside that boundary, four
script-style callers still construct bare `ModuleResolver()`:

| Site | What it does |
|---|---|
| `scripts/build_stage1.py` | builds `mnc-stage1` from `mapanare/self/mnc_all.mn` |
| `scripts/ir_doctor.py` | per-function IR diagnostics; `cmd_diff*`, `cmd_selftest` |
| `scripts/measure_divergence.py` | bootstrap-vs-stage1 IR divergence measurement |
| `benchmarks/bench_stdlib.py` | per-module stdlib compile benchmarks |

Today these scripts cannot honor a project's `mn_modules/`. If a
user runs `python3 scripts/ir_doctor.py diff some_file.mn` inside a
project with installed packages, the `import mn_collections` line
in `some_file.mn` will not resolve to the package. Surface mismatch
between the user-facing CLI (correct) and the developer-facing
scripts (still broken). v5.44.0 explicitly noted this as
out-of-scope; v5.44.1 closes it.

Separately, v5.44.0 added `mapanare/templates/init/default/` (the
project scaffold used by `mnc init`). Phase 0 audit during v5.44.0
did not check whether that template's `.gitignore` excludes
`mn_modules/`. If it doesn't, every `mnc init`-created project
silently commits its installed dependencies on first push — the
exact anti-pattern Cargo / npm / pip users have learned to avoid
through `target/`, `node_modules/`, `__pycache__/` exclusions.
Reproducibility-by-default; one-line fix.

Both items are "we missed these in v5.44.0." Bundling them keeps
v5.44.1 tight and gives v5.45.0 (the closeout panel) cleaner
ground.

---

## Goals

1. **Ps.11** — Extend the Ps.3 resolver-parity contract to every
   `ModuleResolver()` construction site outside `mapanare/`.
   Scripts and benchmarks honor installed packages identically to
   the CLI.
2. **Ps.12** — Project init template excludes `mn_modules/` from
   git by default. Reproducibility-by-default; users opt in to
   committing deps (rare; only needed for demo / vendoring cases
   like `examples/packages/consumer_collections/`).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Ps.11.A** | HIGH | **Scripts resolver parity.** Replace bare `ModuleResolver()` in `scripts/build_stage1.py`, `scripts/ir_doctor.py`, `scripts/measure_divergence.py`, `benchmarks/bench_stdlib.py` with `build_resolver_for_source(source_path)` (the v5.44.0 LSP-style primitive). Tolerant fallback on `PackageDiscoveryError` — script flows shouldn't `sys.exit(1)` on a malformed lockfile when the user is debugging. | 1.5h |
| **Ps.11.B** | HIGH (gate) | **Source-grep gate extension.** v5.44.0's `tests/packages/test_cli_parity.py::test_no_bare_module_resolver_construction_in_compile_paths` audits 4 files in `mapanare/`. Extend the audit list to include the 4 scripts/benchmarks files. Reverting any Ps.11.A edit fails this test. | 0.5h |
| **Ps.12.A** | HIGH | **Init template `.gitignore`.** Add `mn_modules/` to `mapanare/templates/init/default/.gitignore`. Also include the standard junk dirs every Mapanare project should exclude: `__pycache__/`, `*.pyc`, build artifacts (`*.ll`, `*.o`, `*.a`, the binary itself), and the diagnostic JSON path patterns (`*.diag.json`). Don't break `mn_modules/` inside the example consumer (its gitignore is its own concern; the example commits deps deliberately for self-containedness). | 0.5h |
| **Ps.12.B** | HIGH (gate) | **Template `.gitignore` test.** New `tests/packages/test_init_template_gitignore.py` parses the template's `.gitignore` and asserts the canonical excludes are present. Falsifiability: removing `mn_modules/` from the template fails the test. | 0.5h |
| **Ps.13** | LOW | **Module-top import cleanup.** `_surface_install_diagnostics` in `mapanare/cli.py` does `from typing import Any` inside the function body (lint-clean but unconventional). Hoist to module-top imports. ~3 LOC. | 0.1h |

---

## Phase plan

- **Phase 0** — Pre-flight: v5.44.0 HEAD (commit `399486b2`)
  clean. Run the v5.44.0 test suite to confirm baseline. Audit
  the four scripts/ + benchmarks/ files: which signature do they
  use? Do any take a CLI arg that should map to `--stdlib-path`?
  Audit `mapanare/templates/init/default/.gitignore` (does it
  exist? what does it contain?). Write
  `docs/roadmap/v5/v5.44.1/PRE_PHASE_AUDIT.md`.
- **Phase 1** — Ps.11.A: replace 4 bare resolver constructions
  with `build_resolver_for_source` + tolerant fallback. Each
  edit is ~5 LOC.
- **Phase 2** — Ps.11.B: extend the grep gate's audit list. Run
  red-then-green falsifiability check (revert one Ps.11.A edit
  → assert test fails with the expected shape; reapply →
  assert green).
- **Phase 3** — Ps.12.A + Ps.12.B: edit the template
  `.gitignore`, add `tests/packages/test_init_template_gitignore.py`.
  Verify a freshly-init'd project (`mnc init` against `tmp_path`)
  produces a project whose `.gitignore` has the expected entries.
- **Phase 4** — Ps.13: hoist `from typing import Any` in
  `_surface_install_diagnostics` to the cli.py module-top
  imports.
- **Phase 5** — Bump + closeout. Mandatory rebuild order:
  `bump_version.py 5.44.1` → `python3 scripts/build_stage1.py` →
  `make build-rt` → `bash scripts/verify_fixed_point.sh` →
  goldens. The v5.31.0 lesson + v5.44.0 closeout lesson both
  apply: rebuild stage1 AND `libmapanare_rt.a` between bump and
  fixed-point verify.

---

## Out of scope

- **`mnc deps list` / `mnc deps tree` subcommand.** Substantive
  enough to want its own release; deferred to v5.45.0+ or
  later. v5.44.1 is parity-completion, not new feature surface.
- **Native-ABI dependency declaration.** Per v5.44.0 PLAN, this
  is v6.0+ work.
- **Global package cache.** Same — v6.0+.
- **Moving any stdlib module to an external package.** Same.
- **Repo-level `.gitignore` audit.** The repo's own `.gitignore`
  is independent from the init template; if it currently lacks
  `mn_modules/`, that's a separate question (and likely
  intentional, since the consumer_collections example commits
  its mn_modules deliberately). v5.44.1 only touches the
  template.
- **Updating localized READMEs (es / pt / zh-CN).** Per the
  v5.28.0 panel H.4 finding and v5.44.0 audit, these are
  tracked as a separate bookkeeping cycle, not per-release work.

---

## Risk

1. **Scripts behavior change.** A script that previously didn't
   resolve packages now does. Risk: a project with a malformed
   lockfile breaks `scripts/build_stage1.py`. Mitigation:
   tolerant fallback (mirrors v5.44.0 LSP/test_runner pattern)
   — `PackageDiscoveryError` falls through to bare resolver
   instead of `sys.exit(1)`.
2. **Init template change visible to existing users.** Adding
   `.gitignore` entries doesn't affect existing projects; only
   newly-`mnc init`-created ones. Mitigation: documented in
   CHANGELOG `### Changed` (potentially-breaking-ish but
   strictly an additive default).
3. **`build_stage1.py` is on every developer's hot path.** A
   regression here breaks the bootstrap loop for everyone.
   Mitigation: re-run `verify_fixed_point.sh` post-edit
   (which itself invokes `build_stage1.py`'s pattern of bare
   resolver construction — that's literally how the script
   under test gets exercised end-to-end). If STRICT 3-stage
   fixed point survives Ps.11.A, the `build_stage1.py` change
   is by definition harmless.
4. **`benchmarks/bench_stdlib.py` is rarely-run.** Edits there
   could regress silently. Mitigation: smoke-run it once
   post-edit if the environment supports it (Linux only;
   benchmarks have heavier dependencies).
5. **Test-breakage from gitignore template change.** New
   default exclusions might mask files some test fixture
   relies on. Mitigation: limit Ps.12.A's exclusions to the
   safe set (`mn_modules/`, `__pycache__/`, `*.pyc`, build
   artifacts); avoid anything that might shadow user source.

---

## Success criteria

- ✅ All 4 scripts/benchmarks/ files route resolver
  construction through `build_resolver_for_source`.
- ✅ `tests/packages/test_cli_parity.py` audit list extended;
  reverting any Ps.11.A edit fails the test.
- ✅ `mapanare/templates/init/default/.gitignore` excludes
  `mn_modules/` (and the standard junk set).
- ✅ `tests/packages/test_init_template_gitignore.py` GREEN.
- ✅ STRICT 3-stage fixed point preserved at v5.44.0's 242,338
  lines / 0 diff baseline.
- ✅ Goldens 96/96 (no compiler edits → no IR change expected).
- ✅ `make ci-gates` clean (8 sub-gates).
- ✅ `make lint` clean.
- ✅ Existing tests/packages/ + tests/modules/ pass without
  regression (90/90 + 25/25 GREEN at v5.44.0 HEAD).

---

## Carry-forward delta

**Closes:**
- The "every entry point" Ps.3 contract gap at the
  `mapanare/` boundary.
- `mnc init` projects accidentally committing `mn_modules/`.

**Inherits to v5.45.0 (closeout panel):**
- v5.45.0 audits v5.31.0 → v5.44.1 (one more release in the
  audit window). Cadence reminder is informational; lead drives
  panel timing.

**Inherits to v6.0+:**
- All v5.44.0 v6.0 carries unchanged: native-ABI declaration
  schema, global cache, runtime-bound module migration.

**Aggregate state entering v5.45.0:** **0 HIGH** /
**2 MEDIUM** (carry from v5.43.0: lowerer fixes for
`Result<T, complex Err>`, variant rewrap, nested 15-arm match;
macOS notarization carry from v5.33.0 Nu.2) / **~8 LOW**
(carries from v5.44.0).
