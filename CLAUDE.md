# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Mapanare is an AI-native compiled language with first-class agents,
signals, streams, and tensors. Compiles to LLVM IR (primary) and C
(fallback via gcc). WebAssembly backend for browser/server targets.
Self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in
`mapanare/self/`. The compiler compiles itself —
`bash scripts/build_from_seed.sh` builds from source with no Python.

**Current version:** see `VERSION` file.

## Current Version & Roadmap

Most recent releases (last 6). Full history at
`docs/roadmap/ROADMAP.md`:

- **v5.11.0** (shipped) — **Pk.* — packaging hygiene + post-bundle
  cleanup.** Three deferred-from-v5.10.0 cleanups, zero compiler
  internals. **Pk.1**: release-artifact filenames now include the
  version (`mapanare-5.11.0-win-x64.zip`, `mnc-5.11.0-linux-x64`,
  etc.), driven by the VERSION file. install.ps1 / install.sh probe
  the versioned name first, fall back to legacy unversioned for
  pre-v5.11 releases and for the 2-release alias soak window (drop
  legacy in v5.13.0). `windows-bundled-llvm-smoke` job downloads
  the versioned ZIP so a missing-versioned-asset upload trips the
  smoke gate. **Pk.2**: drops the v5.9.1 `mnc <file.mn>`
  (implicit-run) deprecation stderr line; the v5.9.1 PLAN scheduled
  removal at v5.11.0 and v5.10.0 carried it as the soak-window
  concession. `tests/test_cli_default.py::test_default_prints_
  deprecation_note` inverted to `test_default_silent_after_v5_11_0`.
  **Pk.3** (evaluate-only): native `mnc` covers 7 of `mapanare`'s
  25 subcommands. PyInstaller→native bundle swap **deferred** to
  v5.12.x+ behind Mc.\* (mnc parity) — Mc.1 `mnc lsp`, Mc.2
  `mnc fmt`, Mc.3 `mnc init`, Mc.4 `mnc check`, Mc.5 `mnc emit-wasm`.
  See `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md`. **Pk.4**
  (closeout-doc): macOS/Linux LLVM bundling stays deferred —
  system clang remains canonical, static Linux LLVM with libstdc++
  is ~300 MB, no demand signal. NO seed refresh required (zero
  new C-runtime exports — first release in 5+ to skip Bb.\*).
  **Strict 3-stage fixed-point preserved** (226,603 lines / 0 diff,
  the v5.9.0 milestone held since v5.9.0). Goldens 66/66;
  `make lint` clean. See `docs/roadmap/v5/v5.11.0/SESSION_REPORT.md`.
- **v5.10.0** (shipped) — **Win.1b — bundled LLVM toolchain in
  Windows release ZIP.** Closes the "missing clang" pain on Windows
  surfaced by the v5.8.7 install probe. v5.9.0 DX.3 made the failure
  mode helpful (install hint instead of bare "clang failed");
  v5.10.0 removes the dependency entirely. Default
  `mapanare-win-x64.zip` grows from ~10 MB to ~95 MB by bundling
  LLVM 18.1.8's minimal redistributable subset (clang.exe +
  lld-link.exe + LLVM-C.dll + compiler-rt + LICENSE.TXT) into
  `mapanare/llvm/`. **Win.1b.A**: `tools/llvm-bundle/
  extract_minimal.ps1` + `REQUIRED_FILES.md`; PATH-stripped smoke
  test. **Win.1b.B/C**: `actions/cache@v4` LLVM step + bundle staging
  in `build-cli` job. **Win.1b.D**: new `__mn_executable_dir()`
  C-runtime export + `find_clang()` helper in `mapanare/self/main.mn`
  + 6 clang shell-out sites updated. **Win.1b.E**:
  `docs/THIRD-PARTY-LICENSES.md` (Apache 2.0 + LLVM Exception).
  **Win.1b.F**: `install.ps1` honors `MAPANARE_NO_BUNDLED_LLVM=1`
  for opt-out users → `mapanare-win-x64-minimal.zip` (~10 MB).
  **Win.1b.G**: `windows-bundled-llvm-smoke` CI job validates the
  published ZIP end-to-end with PATH stripped. Linux/macOS
  artifacts unchanged (PLAN Decision 4 — those platforms have
  system clang; closeout in v5.11.0 Pk.4). Compiler internals
  untouched; packaging-only release.
  See `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md`.
- **v5.9.2** (shipped) — **hygiene — pre-existing test regex +
  stale README line.** Two pre-existing fixes carried over from
  v5.9.1 that didn't fit the DX.5 dispatch scope. Test + docs only;
  zero compiler/runtime edits. **Tg.1**: tighten the quoted-declare
  regex in `tests/bootstrap/test_stage1_compile.py` — anchor at
  start-of-line and refuse newline inside the captured group.
  Closes the latent `Unresolved cross-module refs:
  [', align 8\n@.str.NNNN = ...']` failure shape (reproduced on
  v5.9.0 HEAD with index 3025; v5.9.1 HEAD with 3042). Helper
  extraction de-dups the two call sites; new `TestRegexHelper`
  with 3 cases guards the failure shape. **Dn.1**: README
  fixed-point status line — stale `NEAR (4-line VERSION-metadata
  diff over a 217k-line stage2.ll)` was the v5.6.x state; v5.9.0
  restored STRICT at the source (DX.2), v5.9.1 preserved it.
  README now reads STRICT with v5.9.0 credit. NO seed refresh.
  **Strict 3-stage fixed-point preserved** (the v5.9.0
  milestone). Goldens 66/66; `test_stage1_compile.py` 20/20 pass
  (was 19/20 at v5.9.1 HEAD); `make lint` clean. See
  `docs/roadmap/v5/v5.9.2/SESSION_REPORT.md`.
- **v5.9.1** (shipped) — **DX.5 — `mnc <file.mn>` defaults to run
  (BREAKING).** Empties the v5.8.7 Windows install probe DX.* docket
  list (DX.1–DX.7 all closed). Single behavior change; dispatch-layer
  only. Pre-v5.9.1 `mnc hello.mn` dumped LLVM IR to stdout (useful
  for compiler devs, hostile first impression for newcomers); v5.9.1+
  compiles + runs the program. New `mnc emit-llvm <file.mn>
  [-o output]` subcommand keeps the IR-emission path verbatim,
  parallel to the Python CLI's `mapanare emit-llvm`. Non-`.mn` files
  error with a migration hint pointing at `mnc emit-llvm` (raw IR)
  or `mnc compile` (transpilation). One-line stderr deprecation note
  on the implicit-run path; removed in v5.11.0 (v5.10.0 keeps it as
  a soak window for downstream CI scripts). NO seed refresh required
  (no new builtin call sites). **Strict 3-stage fixed-point
  preserved** (the v5.9.0 milestone). Goldens 66/66; new
  `tests/test_cli_default.py` 6/6 pass; `make lint` clean. See
  `docs/roadmap/v5/v5.9.1/SESSION_REPORT.md`.
- **v5.9.0** (shipped) — **DX.* — native CLI hygiene.** Closes the
  six user-visible CLI gaps surfaced by the v5.8.7 Windows install
  probe: `mnc --help` works (DX.1); `mnc version` no longer leaks
  `__MN_VERSION__` (DX.2 — structural fix: new `__mn_version_string()`
  C-runtime export replaces the v4.28.0 placeholder + build_stage1.py
  substitution dance, same shape as v5.8.6 We.1); missing-clang prints
  platform-specific install instructions and surfaces clang stderr
  (DX.3); `mnc cache stats` / `cache clean` work on Windows via new
  native `__mn_dir_count_files` / `__mn_dir_total_size` /
  `__mn_dir_remove_recursive` exports + `__mn_dev_null_redirect()`
  shim that sweeps every `2>/dev/null` literal (DX.4); install.ps1 +
  install.sh ship `mnc` alongside `mapanare` and getting-started
  uses `mnc` consistently (DX.6 + DX.7). DX.5 (default-command
  change) deferred to v5.9.1. Bb.3 seed refresh shipped. **Strict
  3-stage fixed-point restored** (225,831 lines / 0 diff) — first
  since v4.139.0 — as a side effect of the IR-metadata node now
  calling `__mn_version_string()` at runtime. Goldens 66/66; 36 new
  pytest tests; `make lint` clean. See
  `docs/roadmap/v5/v5.9.0/SESSION_REPORT.md`.
- **v5.8.6** (shipped) — **We.1 closure — i686-w64-mingw32 ABI
  support.** 3-way ABI dispatch in the emitter (SysV/AAPCS64,
  Win64 sret/sarg, i686 cdecl sret/byval); fixes silent miscompile
  of `{ptr,i64}` returns on i686 via LLVM's eax:edx packing.
  Refines host detection (`__mn_host_is_windows()` /
  `__mn_host_arch_bits()`); deprecates `__mn_host_is_win64()`.
  Bb.2 seed refresh (6.57 MB) — old seed predates the new exports.
  stage2.ll 222,095 lines, strict fixed point in no-Python pipeline.
  Goldens 66/66; pytest 2,372 passed. See
  `docs/roadmap/v5/v5.8.6/SESSION_REPORT.md`.
> Older release notes elided. See `docs/roadmap/ROADMAP.md` for the
> full ledger and `docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` for any
> specific release.

### Planned / in-progress

- **v5.8.0** — **RE-PANEL** (target 9.7+). Features first, panel last.
- **v6.0** — Borrow checker / multi-level alias analysis. Closes
  Rt.04 (multi-level drop-glue alias analysis, rescoped
  v5.6.6 — struct→list→string depth-2). The only remaining
  v5.6.x v6.0 carry now that v5.6.12 closed Lk.1 at the
  source via destination passing.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and
`docs/roadmap/v5/PARITY_GAPS.md`.

## Pre-Push Validation (MANDATORY)

Run the full validation suite before any commit/push. Mirrors CI.
Writes results to `error.log`.

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT
.\dev.ps1 validate -Watch  # Validate then watch
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only
.\dev.ps1 fmt              # Auto-format
.\dev.ps1 e2e              # End-to-end tests
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for `examples/wasm/*.mn`
— catches WASM CI failures locally. `pytest` alone is NOT sufficient.

Quick partial checks:

```bash
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
black --check . && ruff check . && mypy mapanare/ runtime/
pytest tests/semantic/test_types.py -v
pytest tests/parser/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v  (add -n auto for parallel)
make lint             # ruff + black + mypy
make fmt              # black + ruff --fix
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches + egg-info
```

### Core workflows

```bash
# Golden test harness (WSL for stage1)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Full rebuild cycle (WSL)
bash scripts/rebuild.sh              # concat + build + goldens

# Self-hosted fixed-point (WSL)
python scripts/build_stage1.py
bash scripts/verify_fixed_point.sh --keep
```

### Debug tooling

Full command reference: **`docs/guides/tools_reference.md`**.

- `python scripts/ir_doctor.py <cmd>` — per-function IR diagnostics,
  baselines, valgrind mapping, stage2 pipeline
- `python scripts/mir_trace.py <file.mn> <fn>` — trace type inference
  in the Python lowerer
- `culebra <cmd>` — 49+ templates for IR + C diagnostics (Rust binary,
  WSL)

## Testing the Native Compiler

Golden corpus at `tests/golden/*.mn` (66 programs). Reference IR at
`tests/golden/*.ref.ll`.

Workflow:
1. Edit `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. `python scripts/build_stage1.py`
3. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. Harness compares mnc-stage1 output against Python bootstrap —
   shows which functions are missing or different.

Every run updates `tests/golden/BENCHMARKS.md`. Commit to track
regressions.

**Current baseline (v5.7.1):** **66/66 — preserved.** Sh.7
(closure-typed parameters) and B (or-pattern + identifier `None`
resolution) both closed in v5.7.0; v5.7.1 is a docs/polish release
with no compiler edits. The closure arc is closed; every test in
the corpus that defines "self-hosting" now passes through
`mnc-stage1`.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I), **MyPy** strict
- Target Python 3.11+ (bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source
  → Lark LALR parser → AST (dataclasses)
  → Semantic checker
  → MIR lowering
  → MIR optimizer (O0–O3)
  → Emitter:
      ├→ emit_llvm_text.py  → LLVM IR (text)
      ├→ emit_c.py          → C source
      └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:

| File | Role |
|---|---|
| `cli.py` | Entry point — command dispatch |
| `parser.py` | Lark transformer: parse tree → AST |
| `ast_nodes.py` | AST node definitions |
| `semantic.py` | Two-pass type checker + scope resolver |
| `mir.py` / `mir_builder.py` | MIR data + builder |
| `lower.py` | AST → MIR lowering |
| `mir_opt.py` | MIR optimizer passes |
| `emit_llvm_text.py` | LLVM IR generation |
| `emit_c.py` | C source generation |
| `emit_wasm.py` | WebAssembly (WAT) generation |
| `wasm_linker.py` | wasm-ld multi-module linking |
| `types.py` | **Single source of truth** for type system |
| `mapanare.lark` | LALR grammar, 13-level precedence |
| `tracing.py` | OpenTelemetry-compatible tracing |
| `diagnostics.py` | Rust-style structured error output |

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`,
`result.py`, `deploy.py`. **Legacy — being replaced by native .mn
stdlib.**

**Native C runtime** (`runtime/native/`): arena memory (no GC),
lock-free SPSC ring buffers, thread pool with work-stealing, coop
scheduler (mobile), agent lifecycle, TCP sockets, TLS (OpenSSL via
dlopen), file I/O, event loop (epoll/select), string interning,
memory profiling. Used by the LLVM backend.

## LLVM Backend Status

**Working:** functions, structs, enums, pattern matching, control
flow, type inference, generics, Result/Option, print, builtins, lists,
maps (Robin Hood), agents, signals (full reactivity), streams,
closures (env struct capture), traits, module imports, pipes,
multi-agent pipe definitions, string methods, GPU kernel dispatch.

**Not yet on LLVM:** tensor reshape, mutable views, stepped slices
(v5.x). Tensor surface stable since v4.45.0.

New LLVM features target `emit_llvm_text.py` (sole LLVM emitter).

## Type System (`mapanare/types.py`)

Single source of truth:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP,
  OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int,
  float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare → Python name mapping for emitters
- `PYTHON_TYPE_MAP`: Type → Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, ~14,000 lines of Mapanare. Mirrors the Python bootstrap:

| Module | ~LOC | Role |
|---|---:|---|
| `ast.mn` | 781 | AST node definitions |
| `lexer.mn` | 575 | Tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser |
| `semantic.mn` | 1,729 | Type checker + scope resolver |
| `mir.mn` | 791 | MIR data structures |
| `lower_state.mn` | 587 | Lowerer state |
| `lower.mn` | 3,602 | AST → MIR lowering |
| `emit_llvm_ir.mn` | 258 | LLVM type constants + IR builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter |
| `main.mn` | 537 | Compiler driver |

**Patterns:** constructor functions (`let r: T = first_field; return
r`), state-threading, no struct literal syntax in grammar yet.

**Fixed-point:** NEAR (stage2.ll == stage3.ll except VERSION
placeholder). Strict hit at v4.134.0; currently NEAR per v5.3.2.

## Key Conventions

- Grammar: `mapanare/mapanare.lark` (bootstrap copy at `bootstrap/`)
- Emitters detect used features (agents/signals/streams) and import
  only as needed
- Builtins dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted sources: `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Manifesto: `docs/manifesto.md` |
  RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs:
  `docs/roadmap/v0/` → `docs/roadmap/v5/`
- Version: `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

- **Stdlib in .mn:** new stdlib modules are `.mn`, compiled via LLVM.
  No more Python `.py` stdlib files.
- **C runtime as foundation:** OS primitives (sockets, TLS, file I/O)
  in C. Everything above (HTTP, JSON, routing) in Mapanare.
- **Test on LLVM:** every test runs on the LLVM backend.

## GPU / WASM / Mobile (v2.0.0)

- **GPU** — CUDA + Vulkan via dlopen; `@gpu`/`@cuda`/`@vulkan`
  annotations; PTX/SPIR-V codegen; `stdlib/gpu/`.
- **WASM** — `mapanare/emit_wasm.py` → WAT, `wasm_linker.py` for
  wasm-ld. Targets: `wasm32-unknown-unknown`, `wasm32-wasi`.
- **Mobile** — `aarch64-apple-ios`, `aarch64-linux-android`,
  `x86_64-linux-android`. Coop scheduler + smaller defaults (4 KB
  arenas, 256-slot rings, 4 K string intern cap).

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame package
  (pandas+numpy replacement), in .mn
- `net/crawl`, `security/scan`, `security/fuzz` — agents-based
- AI/LLM drivers: `stdlib/ai/` (LLM, embeddings, RAG)

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — black → ruff → mypy → pytest. Matrix: Python 3.11/3.12
- **native** — C runtime: gcc, ASan, TSan
- **wasm** — WAT emit → wat2wasm → wasmtime WASI examples
- **android** — NDK cross-compile: ARM64 + x86_64 `.o` + ELF verify

5,400+ tests across the full pipeline.

## Skills (slash commands)

| Skill | Description |
|---|---|
| `/golden` | 15/15 golden suite through mnc-stage1 + llvm-as |
| `/stage2` | Compile self-hosted modules + validate stage2 IR |
| `/rebuild` | concat + build mnc-stage1 + run goldens |
| `/ir-audit` | LLVM IR pathology audit with baselines |
| `/valgrind-map` | Valgrind + auto-map offsets to struct fields |
| `/bump-version` | Bump VERSION, README, CHANGELOG, localized docs |
| `/code-review` | 7-reviewer panel review |
| `/create-pr` | PR title + description from commits |
| `/simplify` | Review + fix changed code |
| `/autoresearch` | Autonomous experiment loop |
| `/culebra-scan` | Culebra v2.4.0 — 49+ templates (ABI / IR / Binary / Bootstrap / C). Workflow guide: `docs/guides/culebra.md` |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (28719 symbols, 62549 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Mapanare/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Mapanare/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Mapanare/clusters` | All functional areas |
| `gitnexus://repo/Mapanare/processes` | All execution flows |
| `gitnexus://repo/Mapanare/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
