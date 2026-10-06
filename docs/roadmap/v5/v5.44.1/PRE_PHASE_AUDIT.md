# v5.44.1 PRE_PHASE_AUDIT

> Read before Phase 1 edits. Premise verified against v5.44.0 HEAD
> (commit `399486b2`).

## Existing at v5.44.0 HEAD

- Branch: `dev`. Working tree clean.
- `VERSION`: `5.44.0`.
- `tests/packages/` + `tests/modules/`: **90/90 GREEN** in 2.01s
  (matches the v5.44.0 SESSION_REPORT baseline of 65 packages
  + 25 modules).
- `tests/packages/test_cli_parity.py::test_no_bare_module_resolver_construction_in_compile_paths`
  audits 4 files in `mapanare/`: `cli.py`, `multi_module.py`,
  `test_runner.py`, `lsp/analysis.py`. v5.44.0 left
  scripts/benchmarks unaudited.
- `mapanare/cli.py:178`: `from typing import Any` lives inside
  the `_surface_install_diagnostics` function body, in the
  `if diag_json:` branch. Module-top imports do NOT include
  `Any`. (Ps.13 surface confirmed.)

## ModuleResolver construction sites OUTSIDE mapanare/

The four target files do **not** construct bare
`ModuleResolver()`. Instead, they invoke `compile_multi_module_mir`
or `_compile_to_llvm_ir` **without passing a resolver argument**
— the helper falls back to a bare `ModuleResolver()` internally
at `mapanare/multi_module.py:646`. Same parity gap, different
surface shape than the PROMPT presumed:

| File | Line | Call | Resolver shape today |
|---|---:|---|---|
| `scripts/build_stage1.py` | 63 | `compile_multi_module_mir(root_source=..., root_file=..., opt_level=2, skip_check=True)` | bare (fallback inside helper) |
| `scripts/ir_doctor.py` | 701 | `compile_multi_module_mir(source, str(mn_path), opt_level=2)` | bare (fallback inside helper) |
| `scripts/measure_divergence.py` | 46 | `_compile_to_llvm_ir(source, str(mn_file))` (via `mapanare.cli`) | bare (fallback through `_compile_to_llvm_ir`'s `resolver=None` default) |
| `benchmarks/bench_stdlib.py` | 55 | `_compile_to_llvm_ir(full_source, f"{name}.mn", use_mir=True)` | bare (same fallback path) |

Because the parity gap is identical end-to-end (the resolver
that compiles the source is bare, not package-aware), Ps.11.A
scope is unchanged: each call site grows a tolerant
`build_resolver_for_source` + `PackageDiscoveryError` fallback,
and the resolver is passed explicitly to the compile helper.

After the edits, each file will contain the canonical
`try / except PackageDiscoveryError: resolver = ModuleResolver()`
pattern matching the grep gate's regex with
`PackageDiscoveryError` in the preceding 4 lines.

## Init template `.gitignore`

Exists at `mapanare/templates/init/default/.gitignore` (215
bytes, 7 categories). Current contents:

```
# Build artifacts: dist/, build/, *.ll, *.bc, *.o, *.wasm, *.wat
# Native binaries: {{NAME}}, {{NAME}}.exe
# Mapanare cache: .mapanare-cache/, .mn-cache/
# Editor / IDE: .vscode/, .idea/, *.swp, *.swo
# OS: .DS_Store, Thumbs.db
```

**Missing:** `mn_modules/`, `__pycache__/`, `*.pyc`,
`*.diag.json`. `*.a`, `*.so`, `*.dylib`, `*.dll` not present
either (the existing list covers `*.o` and `*.wasm` but not
`.so`/`.a`).

`mapanare.toml` and `mapanare.lock` are NOT excluded — correct
per package-management convention; the Ps.12 audit must keep
them committed.

`*.mn` is NOT excluded — correct; excluding it would mask every
Mapanare source file.

Ps.12.A is an **append-and-extend** edit (the file already
exists), not a create.

## `_surface_install_diagnostics` Ps.13 surface

`mapanare/cli.py:139-235` (extending past the `if diag_json:`
branch). The inner import at line 178 is inside the `if
diag_json:` conditional — only fires when `--diag-json PATH` is
passed. Hoisting it to the module top is a no-op for runtime
behavior; it's a 1-LOC cleanup.

`Any` is used at line 181 (`dict[tuple[str, str], dict[str, Any]]`).
After hoisting, the inner import is deleted and `Any` is added
to the existing `from typing import ...` block — except there is
no module-level `from typing import` line in `cli.py`. So the
hoist requires adding a NEW `from typing import Any` import to
the module top.

## Surprises vs PROMPT

1. **No bare `ModuleResolver()` in any of the four files.** The
   PROMPT/PLAN's "OLD: `resolver = ModuleResolver()`" pattern
   doesn't match HEAD; instead the files rely on the helper's
   fallback. Ps.11.A still applies — the parity gap is
   identical, just one stack frame deeper. Net edit shape is
   the same: add the resolver-construction lines and pass the
   resolver explicitly to the compile helper.

2. **`scripts/measure_divergence.py` routes via `mapanare.cli`,
   not `mapanare.multi_module`.** Same fix shape; the resolver
   passes through `_compile_to_llvm_ir`'s `resolver=` kwarg,
   which the v5.44.0 Ps.3 helper already plumbs to
   `compile_multi_module_mir`.

3. **`benchmarks/bench_stdlib.py:55` calls `_compile_to_llvm_ir`
   with `use_mir=True`** — that kwarg does NOT exist on the
   v5.44.0 `_compile_to_llvm_ir` signature. Pre-existing bug
   (would fail TypeError if anyone actually ran the benchmark).
   Out of v5.44.1 scope; the Ps.11.A edit replaces the call
   with the canonical signature plus the new resolver kwarg.
   Removing `use_mir=True` is a tangential fix that lands
   inside the same edit because keeping it would knowingly
   leave broken code on the canonical path.

4. **`scripts/measure_divergence.py:42` wraps the bootstrap call
   in a broad `except Exception` that suppresses any
   `PackageDiscoveryError`** — divergence reports already keep
   working when a project has a malformed lockfile. The Ps.11.A
   edit raises `PackageDiscoveryError` inside the `try` and
   handles it by falling back to a bare resolver, before the
   outer `except Exception` is hit; behavior is unchanged for
   the existing exception channel.

## Ps.\* deltas vs HEAD

- **Ps.11.A**: 4 files × ~10-15 LOC each (slightly above the
  PROMPT's "~5 LOC × 4" estimate because the call sites need
  argument restructuring around the new `resolver=` kwarg).
- **Ps.11.B**: extend `files_to_audit` list by 4 paths.
- **Ps.12.A**: append `mn_modules/` + `__pycache__/`, `*.pyc`,
  `*.diag.json`, `*.a`, `*.so`, `*.dylib`, `*.dll` to existing
  template `.gitignore`.
- **Ps.12.B**: net-new
  `tests/packages/test_init_template_gitignore.py` (~80 LOC,
  4 cases per PROMPT).
- **Ps.13**: hoist `from typing import Any` from cli.py:178 to
  module-top imports (1 line moved, plus 1 line deleted).

## Compiler / runtime / self-host source touches

**NONE.** Phase 5 still requires `python3 scripts/build_stage1.py`
+ `make build-rt` after `bump_version.py 5.44.1` so VERSION
metadata in stage2/stage3 IR matches.

## Estimated source delta

| Component | LOC |
|---|---:|
| `scripts/build_stage1.py` Ps.11.A | ~12 |
| `scripts/ir_doctor.py` Ps.11.A | ~12 |
| `scripts/measure_divergence.py` Ps.11.A | ~12 |
| `benchmarks/bench_stdlib.py` Ps.11.A | ~14 |
| `tests/packages/test_cli_parity.py` Ps.11.B | ~5 |
| `mapanare/templates/init/default/.gitignore` Ps.12.A | ~12 |
| `tests/packages/test_init_template_gitignore.py` Ps.12.B | ~80 |
| `mapanare/cli.py` Ps.13 | ~2 |
| **Source total** | **~149** |
| Docs (CHANGELOG + SESSION_REPORT + CLAUDE.md + SPEC) | ~200 |
| Mechanical (bump_version.py outputs) | ~10 |
| **Grand total** | **~360** |

## Confidence

HIGH. Every premise verified against working tree at HEAD.
Surprise list is small and structurally additive (no fixes
that broaden scope into compiler/runtime). Phase 5 closeout is
the standard rebuild-then-verify pattern from v5.44.0.
