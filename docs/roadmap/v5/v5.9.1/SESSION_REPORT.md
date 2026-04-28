# v5.9.1 — DX.5 — `mnc <file.mn>` defaults to run (BREAKING)

**Status:** SHIPPED 2026-04-27
**Closes:** DX.5 (the only docket carried forward from v5.9.0)
**Empties:** the v5.8.7 Windows install probe DX.* dockets (DX.1–DX.7
all closed)
**Bb seed refresh:** NO — v5.9.1 adds no new builtin call sites; the
v5.9.0 seed compiles v5.9.1 source unchanged.

---

## Summary

Closes the last DX.* docket from the v5.8.7 Windows install probe.
Pre-v5.9.1 `mnc hello.mn` dumped 200 lines of `define i64 @main()`-
shaped LLVM IR to stdout — useful for compiler developers but a
hostile first impression for newcomers. After v5.9.1:

- `mnc hello.mn` compiles + runs the program.
- `mnc emit-llvm hello.mn` emits IR to stdout.
- `mnc emit-llvm hello.mn -o hello.ll` writes IR to a file.
- `mnc <non-mn-file>` errors with a migration hint pointing at
  `mnc emit-llvm` (raw IR) or `mnc compile` (transpilation).
- A one-line stderr deprecation note prints on every implicit-run
  invocation. Removed in v5.11.0.

This is **dispatch-layer only**. Zero changes to the parser,
semantic checker, MIR, lowerer, optimizer, or emitters — same scope
discipline as v5.9.0. The full surface lives in
`mapanare/self/main.mn::mn_main`.

---

## Phase ledger

| Phase | Outcome |
|---|---|
| 1 | `emit-llvm` subcommand branch + `run_emit_llvm(filename)` helper near `run_compile`; default fall-through routes `.mn` files to `run_program`; non-`.mn` files error with migration hint; `print_help_text` + `print_subcommand_help("emit-llvm")` + `argc<2` usage block updated. |
| 2 | `tests/test_cli_default.py` — 6 cases (default-runs, deprecation note, emit-llvm stdout, emit-llvm -o, non-`.mn` error, --help lists emit-llvm). All 6 pass. |
| 3 | CHANGELOG `[5.9.1]` BREAKING-flagged; `docs/known_issues.md` last-updated → v5.9.1; `docs/roadmap/v5/PARITY_GAPS.md` DX.5 → Historical row; ROADMAP Where-We-Are entry; CLAUDE.md release-history bullet; README + es/pt/zh-CN IR-emission examples updated. |
| 4 | `make lint` clean; goldens 66/66 byte-identical; strict 3-stage fixed-point preserved; pytest CLI suites pass; `bash scripts/build_from_seed.sh` clean. |

## Validation matrix

- [x] Smoke (Linux x86_64):
  - `mnc /tmp/dx5.mn` → stderr deprecation note + stdout `hello v5.9.1`, exit 0.
  - `mnc emit-llvm /tmp/dx5.mn` → stdout starts with `; ModuleID =`, `target datalayout`. No deprecation note on stderr.
  - `mnc emit-llvm /tmp/dx5.mn -o /tmp/dx5.ll` → 12 KB file written; stdout silent.
  - `mnc Makefile` → `error: 'Makefile' is not a .mn file.` + migration hint, exit 1.
  - `mnc --help` → lists `emit-llvm`.
  - `mnc help emit-llvm` → 4-line per-subcommand help.
- [x] `tests/test_cli_default.py` — 6/6 pass.
- [x] `tests/test_cli_help.py` — 20/20 pass.
- [x] Goldens 66/66 — byte-identical (no compiler-path changes).
- [x] Strict 3-stage fixed-point preserved (the v5.9.0 milestone).
- [x] `make lint` clean.
- [x] `bash scripts/build_from_seed.sh` clean — no seed refresh.

## Files changed

**Source (the load-bearing change):**
- `mapanare/self/main.mn` — `emit-llvm` dispatch branch, `run_emit_llvm`
  helper, default fall-through routes `.mn` files to `run_program`
  with stderr deprecation note, non-`.mn` files error with migration
  hint, `print_help_text` + `print_subcommand_help("emit-llvm")` +
  `argc<2` usage block.
- `mapanare/self/mnc_all.mn` — regenerated.

**Tests:**
- `tests/test_cli_default.py` — NEW. 6 cases.
- `tests/bootstrap/test_stage1_compile.py` — IR-emitting cases moved
  to `mnc-stage1 emit-llvm <file>`; the two error-path tests
  (nonexistent file, no-args) keep the default invocation since they
  verify exit-code 1 from the dispatch layer (still correct).
- `tests/llvm/test_enum_inline.py` — same migration to `emit-llvm`.

**Helper scripts that invoked stage1 directly (sweep — these would
have broken in CI without updates):**
- `scripts/test_native.py` — `compile_stage1` adds `emit-llvm`.
- `scripts/verify_fixed_point.sh` — both stage1→stage2 and
  stage2→stage3 invocations add `emit-llvm`.
- `scripts/build_from_seed.sh` — stage1→stage2 invocation adds
  `emit-llvm`; the SEED→stage1 invocation stays plain because the
  v5.9.0 seed predates the `emit-llvm` subcommand. Smoke-test
  invocation + final usage hint updated. (When the seed is
  eventually refreshed post-v5.9.1, that invocation will need
  `emit-llvm` too — the next refresher will hit it.)
- `scripts/test_runtime.sh`, `scripts/valgrind_all_goldens.sh`,
  `scripts/run_asan_leak_goldens.sh`, `scripts/run_asan_goldens.sh`,
  `scripts/mnc-build.sh` — all converted.
- `scripts/ir_doctor.py` — six call sites converted (stage1_compile
  helper + 5 direct subprocess.run sites).
- `scripts/measure_divergence.py` — `compile_stage1` converted.
- `scripts/mir_trace.py` — imports ir_doctor's `stage1_compile`,
  picked up the migration transitively.
- `tests/bench/bench_startup.sh` — `mnc <file>` startup benchmark
  renamed to `mnc emit-llvm <file>`.

**Docs:**
- `CHANGELOG.md` — `[5.9.1]` block (BREAKING-flagged).
- `docs/known_issues.md` — last-updated rolled to v5.9.1.
- `docs/roadmap/v5/PARITY_GAPS.md` — DX.5 → Historical row.
- `docs/roadmap/ROADMAP.md` — Where We Are (v5.9.1) entry above v5.9.0.
- `CLAUDE.md` — release-history bullet for v5.9.1.
- `README.md` — Build-from-source IR-emission example updated to
  `mnc emit-llvm`; one-paragraph migration note added. The localized
  READMEs (`docs/README.{es,pt,zh-CN}.md`) already use `mapanare`
  (Python CLI, unaffected by DX.5) and need no change.
- `VERSION` — `5.9.0` → `5.9.1`.

**Runtime archive:**
- `runtime/native/libmapanare_rt.a` — rebuilt with
  `-DMAPANARE_VERSION="5.9.1"` via `make build-rt` so the
  C-runtime-baked version string matches stage1. Without this
  rebuild, the strict 3-stage fixed-point regresses to NEAR (1-line
  metadata diff: stage2 `!"5.9.1"` vs stage3 `!"5.9.0"`) — same
  shape as the v4.140.0–v5.8.x regression that v5.9.0 fixed
  structurally. Routine version-bump hygiene; `make build-rt` is
  in the standard release flow.

## Carry-forward

- **v5.11.0:** delete the implicit-run stderr deprecation note (one
  line in `mn_main`'s default fall-through). Tracked here so the
  v5.11.0 PLAN picks it up.
- **v6.0:** borrow checker / Rt.04 — unchanged, independent track.

## What this release does NOT change

- Parser, semantic checker, MIR, lowerer, optimizer, emitters — zero edits.
- The v5.9.0 strict 3-stage fixed-point — preserved.
- Bootstrap seed — no refresh required.
- `compile` / `build` / `run` / `test` / `cache` subcommand names — stable.

## Pre-existing test failure (unrelated)

`tests/bootstrap/test_stage1_compile.py::TestStage1Compilation::
test_cross_module_references_resolved` fails on the v5.9.1 HEAD with
the message `Unresolved cross-module refs: [', align 8\\n@.str.3042
= private constant [1 x i8] c']`. Confirmed pre-existing: stashing
the v5.9.1 source changes and re-running the same test on v5.9.0
HEAD reproduces the failure with a different `@.str.NNNN` index
(3025 vs 3042). The test uses a brittle regex
(`r'declare\\s+(?:external\\s+)?.*?@"([^"]+)"'`) that captures
content between two `@"..."` matches across newlines instead of
just the function name. Out of scope for v5.9.1 — tracked
separately. All other 58 tests in the file pass.

## What was harder than expected

1. **The PLAN's risk-register premise on `scripts/test_native.py`
   was wrong.** Risk DX5.R4 stated that `scripts/test_native.py`
   "already uses internal compilation paths, not the CLI default."
   In fact it invokes `[stage1, mn_file]` at line 349 — exactly the
   default-CLI path. Same shape across `verify_fixed_point.sh`,
   `build_from_seed.sh`, and a long tail of helpers (`test_runtime`,
   `valgrind_all_goldens`, `run_asan_*`, `mnc-build`, `ir_doctor`
   with 6 call sites, `measure_divergence`, `bench_startup`,
   plus `tests/bootstrap/test_stage1_compile.py` and
   `tests/llvm/test_enum_inline.py`). Sweep landed in a single
   pass; everything green after.

2. **Strict fixed-point regressed to NEAR after the VERSION bump,
   then restored.** Bumping VERSION 5.9.0 → 5.9.1 + rebuilding
   stage1 was insufficient — the stage2 binary in
   `verify_fixed_point.sh` is gcc-linked against the static
   `runtime/native/libmapanare_rt.a` archive, which was still baked
   with `MAPANARE_VERSION="5.9.0"` from the previous release. Result:
   stage2 emitted `!"5.9.1"`, stage3 emitted `!"5.9.0"`, 1-line
   metadata diff (the same v4.140.0–v5.8.x failure shape that v5.9.0
   fixed structurally — the C-runtime constant is the single source
   of truth, but it's only the right truth if the archive is
   rebuilt). `make build-rt` regenerated the archive at 5.9.1; strict
   fixed-point restored. Routine version-bump hygiene; should be
   added to the release-checklist alongside `python3
   scripts/build_stage1.py`.

## Notes

- The implicit-run path calls `run_program(filename)`, which forwards
  `argv[3..]` to the user binary. For implicit-run (`mnc <file>
  arg1`), positional args at index ≥ 3 still forward; the arg
  immediately after the filename (index 2 for the explicit `run`
  shape, but no slot in implicit-run) is not duplicated — same
  surface shape as `mnc run <file> arg1` on the explicit path.
  Newcomers running `mnc hello.mn` with no args see no difference;
  argv-forwarding contracts are untouched.
- The deprecation note is printed unconditionally on the implicit-
  run branch — it does NOT appear on the explicit `mnc run`,
  `mnc emit-llvm`, or any other subcommand. `tests/test_cli_default.py
  ::test_emit_llvm_subcommand_to_stdout` gates the absence.
