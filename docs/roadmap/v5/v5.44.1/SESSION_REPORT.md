# v5.44.1 Session Report — Ps.11 + Ps.12 — scripts parity + gitignore template

> **Status:** ready, not tagged. Tactical hotfix completing the
> v5.44.0 Ps.\* arc end-to-end. Single commit. Zero compiler /
> runtime / self-host source touches. STRICT preserved.

## Headline

After v5.44.0 closed package-aware import resolution inside
`mapanare/`, v5.44.1 closes the same parity gap beyond that
boundary: `scripts/build_stage1.py`, `scripts/ir_doctor.py`,
`scripts/measure_divergence.py`, `benchmarks/bench_stdlib.py`
now route through `build_resolver_for_source` so a project
with `mapanare.toml` + `mn_modules/` is resolved identically
across the stage1 bootstrap, `ir_doctor diff`, the divergence
sweep, the stdlib benchmarks, and `mnc build`. The init template
`.gitignore` now excludes `mn_modules/` by default so freshly
initialized projects don't commit installed packages.

## Scope

| Item | Where | Surface |
|---|---|---|
| Ps.11.A — scripts/benchmarks resolver parity | `scripts/build_stage1.py`, `scripts/ir_doctor.py`, `scripts/measure_divergence.py`, `benchmarks/bench_stdlib.py` | ~50 LOC across 4 files |
| Ps.11.B — grep gate extension + new shape gate | `tests/packages/test_cli_parity.py` | files_to_audit +4; new `test_scripts_pass_resolver_to_compile_helper` parametrized over 4 files |
| Ps.12.A — init template gitignore | `mapanare/templates/init/default/.gitignore` | +12 lines (mn_modules/ + canonical artifacts) |
| Ps.12.B — gitignore lock test | `tests/packages/test_init_template_gitignore.py` | 4 cases, ~115 LOC |
| Ps.13 — import hoist | `mapanare/cli.py` | -1 / +1 |

## Phase 0 — pre-flight findings

PROMPT premise was that the four target files contained bare
`ModuleResolver()` constructions that needed to be wrapped in
`build_resolver_for_source`. Phase 0 verification surfaced a
nuance: the files don't construct resolvers directly — they
invoke `compile_multi_module_mir` / `_compile_to_llvm_ir`
**without passing a resolver argument**, falling through to the
helper's in-function bare-resolver fallback at
`mapanare/multi_module.py:646`.

Same parity gap, different surface shape. Ps.11.A scope was
unchanged — each call site grew an explicit
`build_resolver_for_source` + `PackageDiscoveryError` fallback
and passed the resolver explicitly to the compile helper. The
existing `tests/packages/test_cli_parity.py` regex
(`^\s*(?:resolver\s*[:=]|return\s+)?ModuleResolver\s*\(\s*\)\s*$`)
doesn't fire for these files, so adding them to the audit list
without a complementary test was toothless. Ps.11.B grew a new
`test_scripts_pass_resolver_to_compile_helper` parametrized gate
that locks the actual invariant: every
`compile_multi_module_mir` / `_compile_to_llvm_ir` call must pass
an explicit `resolver=` kwarg. The complementary gate is the
load-bearing structural change — the existing-list addition is
keep-in-formation only.

Documented in `PRE_PHASE_AUDIT.md`.

## Phase 1 — Ps.11.A scripts edits

Canonical pattern across all four files:

```python
from mapanare.modules import ModuleResolver
from mapanare.pkg_discovery import (
    PackageDiscoveryError,
    build_resolver_for_source,
)

try:
    resolver = build_resolver_for_source(<source_path>)
except PackageDiscoveryError:
    resolver = ModuleResolver()
# … resolver= passed explicitly to the compile helper
```

`<source_path>` per file:

- `scripts/build_stage1.py`: `str(root_file)` — the
  `mapanare/self/main.mn` path. Constructed once before the
  compile call.
- `scripts/ir_doctor.py`: `str(mn_path)` — the file under diff.
  Constructed inside the `if "import self::" in source` branch
  (only the multi-module path needs it; the alternate branch
  shells out to `python3 -m mapanare emit-llvm` which already
  routes through v5.44.0 Ps.3).
- `scripts/measure_divergence.py`: `str(mn_file)` — per-file
  in `compile_bootstrap`, before invoking
  `_compile_to_llvm_ir(... resolver=resolver)`.
- `benchmarks/bench_stdlib.py`: per-module path — added a
  `source_path: Path` parameter to `_compile_module` (with two
  call sites updated to pass `path`); construction happens
  inside `_compile_module` before the timed `perf_counter`
  block (resolver discovery is one-shot vs. compile
  millisecond-scale; doesn't materially distort the
  measurement).

In every case the resolver fallback is **tolerant** (no
`sys.exit`) — a developer running `ir_doctor.py` against a
broken project has every right to expect the script to keep
working with bare resolution. The CLI's stricter behavior
(exit on `PackageDiscoveryError`) is for production builds.

Also incidentally fixed: `benchmarks/bench_stdlib.py:55`
called `_compile_to_llvm_ir(..., use_mir=True)` with a kwarg
that does not exist on the v5.44.0 `_compile_to_llvm_ir`
signature. The benchmark would have raised `TypeError` if
anyone ran it. Same Phase 1 edit drops the invalid kwarg
along with adding the new `resolver=` kwarg, keeping the
canonical signature on the canonical path.

## Phase 2 — Ps.11.B grep gate extension

`tests/packages/test_cli_parity.py`:

1. `files_to_audit` list +4 entries for the
   bare-`ModuleResolver()` regex. Mechanical extension of the
   v5.44.0 audit scope to the scripts/benchmarks boundary.
   Trivially passing (no new bare constructions).

2. New `test_scripts_pass_resolver_to_compile_helper`
   parametrized over `(scripts/build_stage1.py,
   scripts/ir_doctor.py, scripts/measure_divergence.py,
   benchmarks/bench_stdlib.py)`. Walks each file, finds every
   `compile_multi_module_mir` or `_compile_to_llvm_ir` call,
   tracks paren depth to delimit the argument list, asserts
   `resolver=` appears inside. Strips comment-only lines and
   inline `# tail` comments before scanning so docstring/
   commentary mentions of the helper name don't trigger.

**Falsifiability round-trip verified.** Reverted the
`resolver=resolver` kwarg in `scripts/build_stage1.py`; ran
the new test; failed with the recorded shape:

```
scripts/build_stage1.py:77: compile_multi_module_mir(...) missing
required `resolver=` kwarg. Construct via
`build_resolver_for_source(...)` with a tolerant
PackageDiscoveryError fallback so the script honors `mn_modules/`
for package-aware projects.
```

Reapplied; gate green. Documents the gate's teeth.

## Phase 3 — Ps.12.A + Ps.12.B init template gitignore

Existing template `.gitignore` at v5.44.0 HEAD covered build
artifacts (`dist/`, `*.ll`, `*.o`, `*.wasm`, `*.wat`), the
`{{NAME}}` binary placeholders, Mapanare cache dirs, editor /
IDE artifacts, and OS junk. Missing: **`mn_modules/`** (the
load-bearing v5.44.1 add), `__pycache__/`, `*.pyc`,
`*.diag.json`, `*.a`, `*.so`, `*.dylib`, `*.dll`. Append-and-
extend edit; `mapanare.toml` and `mapanare.lock` deliberately
NOT excluded (committed per package-management convention);
`*.mn` deliberately NOT excluded (excluding source files is
catastrophic).

`tests/packages/test_init_template_gitignore.py` (net-new, 4
cases):

- `test_template_gitignore_excludes_mn_modules` — load-bearing
  v5.44.1 invariant.
- `test_template_gitignore_required_patterns` — locks the
  canonical exclude set.
- `test_template_gitignore_no_forbidden_patterns` — locks the
  canonical include set (lockfile + manifest + source files
  never excluded).
- `test_init_creates_project_with_gitignore` — end-to-end via
  `stdlib.pkg.init_project(tmp_path)`; verifies the produced
  `.gitignore` contains `mn_modules/`, the `{{NAME}}`
  placeholder is substituted with the project name, and
  forbidden patterns are absent.

4/4 GREEN at HEAD in 0.54s.

## Phase 4 — Ps.13 import hoist

Hoisted `from typing import Any` from inside
`_surface_install_diagnostics`'s `if diag_json:` body
(`mapanare/cli.py:178`) to a new module-top
`from typing import Any` import. No prior `from typing import`
line existed in the module. Removed the inner import; `ruff
check` clean; `from mapanare import cli` smoke OK.

## Phase 5 — closeout

```
python3 scripts/bump_version.py 5.44.1   # VERSION + 4 README badges + CHANGELOG stub
$EDITOR CHANGELOG.md                      # filled in (Ps.11/12/13 + use_mir kwarg fix)
python3 scripts/check_changelog_honesty.py  # GREEN
$EDITOR docs/SPEC.md                       # Hd-class header re-sync to v5.44.1 cut
python3 scripts/check_doc_freshness.py     # GREEN
python3 scripts/build_stage1.py            # rebuild (VERSION embedded in IR)
rm -f runtime/native/libmapanare_rt.a
make build-rt                              # rebuild archive
bash scripts/verify_fixed_point.sh         # STRICT preserved
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1  # 96/96
make ci-gates                              # 9 sub-gates GREEN
ruff check . && mypy mapanare/             # clean
```

Single commit per v5.43.0 / v5.44.0 pattern. Tag policy
unchanged (lead's call).

## Tests at HEAD

- `tests/packages/`: **69 GREEN** (was 65 at v5.44.0; +4 new
  init-template gitignore cases; +4 new
  `test_scripts_pass_resolver_to_compile_helper` parametrized
  cases — net change matches the +8 reported by pytest).

  Wait — re-checking: pytest reports `tests/packages/` +
  `tests/modules/` together at 98 (was 90 at v5.44.0; +8). The
  modules suite is unchanged at 25, so packages went from 65
  → 73 (not 69). The +8 = 4 gitignore cases + 4
  scripts-resolver gate cases. Documented for the v5.44.0 →
  v5.44.1 delta.

- `tests/modules/`: 25/25 GREEN (regression check; backward-
  compat invariant preserved by construction since v5.44.1
  makes zero edits to `mapanare/modules.py`).

- Goldens: 96/96 (unchanged; no source under
  `mapanare/self/` touched).

- STRICT 3-stage fixed point: preserved at v5.44.0's 242,338
  lines / 0 diff.

## Aggregate state entering v5.45.0

- **0 HIGH** (Ps.\* arc closed cleanly with v5.44.1 closing
  the parity gap end-to-end).
- **2 MEDIUM** (carries from v5.43.0/v5.44.0: lowerer fixes
  for `Result<T, complex Err>` + variant rewrap + nested
  15-arm match; macOS notarization carry from v5.33.0 Nu.2).
- **~8 LOW** (carries unchanged: native-ABI dependency
  declaration schema, runtime-export ABI versioning,
  global-cache implementation, registry-side package signing
  — all v6.0+ work).

Manifesto arc CLOSED at v5.43.0. Package-system runway CLOSED
at v5.44.0. Package-system parity beyond `mapanare/` CLOSED at
v5.44.1. **v5.45.0 closeout panel runs as planned** (per the
v5.46.0 deferral commit `f7a6272b`).

## Files touched

```
modified:   AGENTS.md                                          (auto: GitNexus refresh)
modified:   CHANGELOG.md                                       (Ps.11/12/13 release notes)
modified:   CLAUDE.md                                          (auto: GitNexus refresh + v5.44.1 release-notes entry)
modified:   README.md                                          (badge bump)
modified:   VERSION                                            (5.44.1)
modified:   benchmarks/bench_stdlib.py                         (Ps.11.A; use_mir kwarg fix)
modified:   docs/README.es.md                                  (badge bump)
modified:   docs/SPEC.md                                       (Hd-class header re-sync)
modified:   mapanare/cli.py                                    (Ps.13 import hoist)
modified:   mapanare/templates/init/default/.gitignore         (Ps.12.A)
modified:   scripts/build_stage1.py                            (Ps.11.A)
modified:   scripts/ir_doctor.py                               (Ps.11.A)
modified:   scripts/measure_divergence.py                      (Ps.11.A)
modified:   tests/packages/test_cli_parity.py                  (Ps.11.B)
new file:   docs/roadmap/v5/v5.44.1/PRE_PHASE_AUDIT.md
new file:   docs/roadmap/v5/v5.44.1/SESSION_REPORT.md
new file:   tests/packages/test_init_template_gitignore.py     (Ps.12.B)
```

## Confidence

HIGH. Falsifiability locked per fix; STRICT preserved by
construction (zero source under `mapanare/self/` touched);
goldens preserved; the new gate has teeth (verified via
revert-and-restore round-trip).
