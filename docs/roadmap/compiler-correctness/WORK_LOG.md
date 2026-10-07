# Compiler correctness and self-hosting work log

## Resume point — 2026-10-07

Priority 1 of the [reliability roadmap](../RELIABILITY_ROADMAP.md) is active.
Starting revision: `cbcfa0da9cdb69f61c5eef8017b5eb56785d8c9d` (v5.54.2, `dev`).
Changes are local and uncommitted. The existing untracked desktop restart plan
was not modified. Do not begin priority 2 until the compiler gates below pass.

**Current checkpoint: first reliability milestone verified.** The optimized
production compiler and self-hosted successor pass 103/103 LLVM goldens and
eight executable fixtures. Stage2 and stage3 IR are byte-identical, and the
production compiler emits that same fixed point. All 16 new regression checks
pass on the production build. Native explicit `::<T>` syntax remains open;
priority 1 is not complete. No build or validation remains running for this batch.

## Implemented changes

1. `mapanare/lower.py`: `_specialize_fn` substitutes types throughout a copied
   generic body, including nested explicit type arguments and local annotations.
   Both generic functions and generic impl methods use this path. Independent
   instantiations do not mutate the shared generic template.
2. `mapanare/self/emit_llvm.mn`: String-returning functions clone borrowed heap
   strings while preserving literals and transferring locally owned buffers.
   This matches the emitter's existing caller-owns-String-results convention.
3. The native emitter now clears String ownership slots at `Move` and user-call
   transfer points. It compares buffer pointers to handle loaded aliases. The
   previous bookkeeping only skipped final drops; loop free-before-store still
   freed strings already captured in lists/aggregates.
4. `mapanare/self/mir_opt.mn`: both inliner cloning and downstream use replacement
   now rename `Move` operands. The new lifetime tests exposed undefined SSA uses
   that were previously hidden because Move emitted no runtime instructions.
5. Native `print`/`println` format booleans as `true`/`false`, matching bootstrap
   and the existing executable fixture, instead of `1`/`0`.
6. `scripts/verify_fixed_point.py` and its shell wrapper replace the permissive
   gate. The validator regenerates concatenated source and runtime, links the
   correct compiler wrapper, checks all LLVM goldens and eight executable
   fixtures on both generations, rejects crashes/empty IR, and requires exact
   stage2/stage3 byte equality. Each run retains a manifest and raw logs.
7. Native fixed-size LLVM allocas now go into the existing function-entry
   prelude. Loop-local runtime argument slots previously grew the stack on every
   iteration. The new test performs 100,000 list updates with a 1 MB stack;
   the original compiler segfaults, and the diagnostic candidate passes.

The return/transfer fixes do **not** establish general recursive container
cleanup or leak freedom. User-call transfers retain the existing conservative
ownership contract. The ASan regressions disable leak detection to isolate
invalid access/free; broader lifetime accounting remains priority 2.

## Reproductions and evidence

Evidence paths below are relative to `build/compiler-correctness/`, an ignored
local directory. Keep this document as the durable summary; logs may not exist
on another machine.

| Check | Result / evidence |
|---|---|
| Original generic specialization | `generic-before.log`: O0/O2 schema execution failed; properties incorrectly empty |
| Generic fix and related checks | `generic-after.log`: 96 passed, 1 xfailed; final generic + gate checks: `generic-gate-final.log`, 8 passed |
| LLVM/MIR suite | `llvm-mir-tests.log`: 1,068 passed |
| Original native baseline | 103/103 LLVM-valid goldens, but case 26 printed `1` instead of fixture `true` |
| Original optimized successor | 99/103 LLVM-valid goldens; 26/29/30/31 failed; stage3 emission double-freed at `definition_name` |
| Borrowed String regression | `ownership-before.log`: repeated enum accessor double-free under ASan; struct/owned controls pass |
| Loop lifetime regressions | `loop-before.log`: both list capture and function capture fail under ASan on original compiler |
| Current focused native checks | `loop-quick-tests.log`: 7 passed on diagnostic compiler |
| Required self-hosted/bootstrap/optimizer suites | 854 passed, 5 xfailed, 2 xpassed; 10 CLI failures were missing PATH, all 10 pass with corrected PATH in `bootstrap-cli-recheck.log` |
| Optimized successor before stack fix | `fixed-point-move.log`; `build/fixed-point-13mmf75b/`: both generations 103 LLVM goldens + 8 executions; successor focused tests 7 passed; stage3 stack overflow |
| Constrained stack | `stack-before.log`: original compiler SIGSEGV; `stack-quick-tests.log`: all 8 focused tests pass after hoisting allocas |
| Latest strict gate | `fixed-point-stack.log`; `build/fixed-point-clx5qwfc/`: PASS; stage2/stage3 byte-identical, both generations 103/103 + 8 executions |
| Final successor focused tests | `stack-successor-regressions.log`: 8 passed |
| Final production rebuild | `rebuild-stack-production.log`: PASS, current source, LLVM O2 |
| Production validation | `production-validation.log` and `production-validation/manifest.json`: 103/103 + 8 executions; emitted compiler IR equals the validated fixed point |
| Production regression checks | `production-regressions.log`: all 16 passed |
| Python formatting | Black `--target-version py312 --check`: all 7 authored Python files pass |
| Lint/type checks | Ruff 0.15.2: all 7 files pass; mypy 1.19.1: lowerer and gate pass (`mypy-final.log`, `mypy-gate-final.log`) |

An intermediate successor after only the return fix repaired all four generic
shape failures, but then exposed the loop-capture corruption. It is **not** a
validated compiler and must not be promoted. Current code includes the transfer
and inliner fixes as well.

The remaining stage3 crash after transfer fixes was **stack exhaustion**, not
invalid list contents. GDB (`stage3-move-detail.log`) shows `rsp` at the guard
page and the fault at `mn_list_detach`'s second register push. The list descriptor
was valid. Hoisting fixed-size allocas addresses the growth rather than raising
the compiler thread's 32 MB stack allowance.

The validated stage2/stage3 IR is 138,775,939 bytes with shared SHA256
`7bd42052806224b816222265baee71051b57ecf3fd8e6e94dfccebf08f062492`.
The optimized successor binary SHA256 is
`316dedcf569e887a4b29304a4fd0b9371785224acf11c2ad0b658711c9aaf9c8`.
The input concatenated-source SHA256 is
`0f9dea758f5721fb8d095306833cbcc690d677fd4e7394b258beabc3fcb73860`.
The final optimized production binary SHA256 is
`ff2934b9795b6ff5286af3a8c0e9cb48c44272c6acebe6ed2c84d06e77ae9542`.

Production validation regenerated concatenated source and required it to match
the gate's input, ran its own 103 goldens/eight fixtures, then required its
emitted compiler IR to equal the already validated stage2/stage3 bytes. This
reuses the proven successor rather than recompiling identical IR a second time.
All native execution validation was Linux/WSL; this does not certify Windows
or macOS native releases.

WSL's existing Ruff/mypy executables crashed. Verification succeeded using the
installed Windows Python at
`C:/Users/Juan/.pyenv/pyenv-win/versions/3.12.0/python.exe` with `-m ruff` and
`-m mypy`; no dependency was installed to work around this.

The old fixed-point script had three false-success risks: it accepted a
nonzero compiler exit if IR looked valid, tolerated a default 100-line diff,
and linked the compiler's `void mn_main` to an application wrapper expecting
`i32 mn_main`. The replacement uses `mapanare/self/mnc_main.c`, which also
provides the compiler's larger stack. Six unit tests enforce strict rejection
of crashes, empty IR, and any byte difference.

## Binaries and toolchain

- Preserved original: `build/compiler-correctness/mnc-baseline`.
- Original SHA256:
  `f285149b519d55bdc2fed412183175121b9d6db0e613e6af28db21e0de2c3bff`.
- Diagnostic: `build/compiler-correctness/mnc-quick`; Python bootstrap MIR O2,
  clang LLVM O0 for faster investigation. Not the production build.
- Final optimized production binary: `mapanare/self/mnc-stage1`, rebuilt from
  current source and verified as above. Check its hash when resuming.
- Ubuntu WSL; `.venv/bin/python` 3.12.3; clang/LLVM 18.1.3. Runtime rebuilt with
  `make build-rt` for version 5.54.2. Exact hashes live in each gate manifest.

## Remaining work, in order

1. Close the native generic frontend gap: `Expr::Call` currently
   stores only callee and value args; `parse_call_args` has no explicit type-arg
   channel; `specialize_fn` substitutes signatures only. Native support needs
   AST/parser/semantic/lowering changes and executable parity tests, not merely
   a copy of the Python walker. Native `__struct_meta` parity also needs review.
2. Add a failing native regression before changing the AST layout, including
   nested `identity::<T>(value)` calls and independent concrete instantiations.
   Run impact analysis on each touched symbol and review native callers manually
   where GitNexus has no coverage.
3. Rerun strict self-hosting and relevant regressions after that frontend work.
   Keep the preserved baseline; do not add IR repair or diff tolerance.
4. Keep priority 1 active until native generic parity is validated, then proceed
   to priority 2. Update this checkpoint after each milestone. No commit/release
   was made for the current batch.

## Resume commands

Run from the repository root in Ubuntu WSL. Windows invocations use
`wsl -d Ubuntu -- bash -c 'cd /mnt/c/Users/Juan/Documents/GitHub/Mapanare && ...'`.
On this host WSL commands require sandbox escalation; this was approved during
this task. Avoid `bash -lc`, whose startup PATH expansion fails here.

```bash
.venv/bin/python scripts/build_stage1.py
.venv/bin/python -m pytest tests/llvm/test_generic_specialization.py tests/integration/test_string_return_ownership.py tests/integration/test_native_bool_output.py tests/integration/test_native_loop_stack.py tests/bootstrap/test_fixed_point_validation.py -q
.venv/bin/python scripts/verify_fixed_point.py --keep
env PATH=/mnt/c/Users/Juan/Documents/GitHub/Mapanare/.venv/bin:/usr/local/bin:/usr/bin:/bin .venv/bin/python -m pytest tests/self_hosted/ tests/bootstrap/ tests/mir_opt/ -q --tb=short
```

To check a retained successor, set
`MAPANARE_TEST_COMPILER=build/fixed-point-<run>/mnc-stage2` before the focused
integration pytest command. The gate itself accepts `--stage1 <binary>`.

## GitNexus scope and limitation

MCP tools were unavailable; used the installed CLI. A stale index and concurrent
Windows/WSL refresh caused lock/corruption errors. Stopped this task's WSL writer
and repaired via Windows `npx --offline gitnexus analyze --force --embeddings`.
Use the Windows CLI for this index; do not start concurrent cross-platform writers.

After repair, `_specialize_fn` impact: LOW, six affected symbols, two direct
callers (`_monomorphize_call`, `_monomorphize_impl`), one affected process summary.
Native `.mn` symbols are not indexed: impact calls return target not found / UNKNOWN.
This is a coverage limitation, not a clean native impact result. Source callers
were inspected and broad emitter/inliner risk was communicated before edits.

`detect-changes-final.log` records LOW for indexed changes (13 symbols / 13
tracked files, zero affected flows). It does not cover native symbols or new
untracked test/validator files. Manual review supplements it. GitNexus-generated
AGENTS/CLAUDE/skill edits appeared during refresh; they are separate from the
compiler changes and were left intact. No commit was created.
