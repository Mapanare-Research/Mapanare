# Compiler correctness and self-hosting work log

## Resume point — 2026-10-07

Priority 1 of the [reliability roadmap](../RELIABILITY_ROADMAP.md) is complete.
The subsequent [memory-ownership checkpoint](../memory-ownership/WORK_LOG.md)
is now active and supersedes the installed-compiler hash recorded below.
Starting revision: `cbcfa0da9cdb69f61c5eef8017b5eb56785d8c9d` (v5.54.2, `dev`).
The first verified milestone is committed as `9c877e62` (`Fix compiler lifetime
bugs and enforce strict self-hosting validation`). The native generic follow-up
is committed as `888ab1f5` (`Support explicit generics and body specialization
in native compiler`). The existing untracked desktop restart plan was not modified.

**Current checkpoint: final source verified; optimized successor installed.**
`build/fixed-point-8a9z1nv3/manifest.json` records 103/103 LLVM goldens and eight
executable fixtures on both optimized generations, LLVM-valid full compiler IR,
and exact stage2/stage3 equality. The successor passes all 19 native regressions
(`generic-current-regressions.log`) and is installed as `mapanare/self/mnc-stage1`.
Promotion regenerated source at commit `888ab1f5`, required exact equality with
the gate's source, checked the runtime, and verified the installed binary hash.
The gate began before that commit, so its recorded HEAD is `9c877e62` with dirty
changes; the promotion manifest establishes the committed-source correspondence.

Final hashes (SHA256):

- Concatenated source: `c6dfc08fa32bbfcdaed33479c2b5732a87075f8f79eb9fa13ace0ac8a22b0164`.
- Installed optimized compiler: `819cf7753ef97d8aa0b6b4ee923956a1bc4eaa901b13a567d5845feca23d9bc1`.
- Both stage2/stage3 IR: `adc262722e9b298deecf0053f13b25e476ba3956bcd418bdab159f4a2fe3c761`.
- Runtime archive: `381638c3b620a87c04376a5988a9b93b409ad170f5b0abcdd9d1f1106a890830`.

Promotion record: `build/compiler-correctness/generic-production-validation/manifest.json`.
No release or push was performed. Compiler builds/tests are finished. Next work
is priority 2 (memory ownership); its concrete starting steps are below.

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

### Native generic frontend follow-up

The follow-up adds explicit `::<T>` calls and recursive generic body
specialization to the native compiler. `Expr::TypeApply` is appended to the AST
enum, preserving existing variant tags and the two-field `Call` representation.
The parser wraps the callee; semantic checking validates type/value argument
counts and concrete types; lowering substitutes body annotations and nested
type applications without mutating the template.

Specializations register before lowering their bodies so recursion and repeated
calls reuse one definition. Nested container arguments participate in mangling.
The native `__struct_meta::<T>()` intrinsic supports the schema regression used
for the Python fix, including generic impl methods. Impl calls retain declared
return types, and the inliner no longer emits a value-copy instruction for a
Void return.

`tests/integration/test_native_generics.py` covers independent inferred and
explicit instantiations, nested calls and types, return-only type parameters,
recursion, pipes, schema generation, generic impl methods, and five invalid-call
diagnostics. Initial reproductions failed with unresolved `T` or explicit-call
parse errors. Expanded checks exposed invalid Void and method-return LLVM types;
both were fixed at their source.

- Diagnostic candidate: **11 passed** (`native-generics-after.log`).
- Existing milestone regressions on the same candidate: **16 passed**
  (`generic-existing-regressions.log`).
- LLVM/MIR: **1,068 passed** (`generic-llvm-mir-tests.log`).
- First full-source gate (`build/fixed-point-aptewfxb`) passed 103 LLVM goldens
  and eight executable fixtures, then rejected stage2 IR: direct matching on
  `scope_lookup(...)` lost the `Option<Symbol>` payload type in the new helper.
  Added typed `Option<Symbol>` and `Option<FnDefData>` locals before matching.
  Fresh full compiler IR then passed `llvm-as` (`generic-source-check.stderr`,
  empty on success). No emitted IR was patched.
- Optimized native successor: **19 passed** (`generic-successor-regressions.log`).
  `build/fixed-point-ua3bcdb1/manifest.json` records 103/103 LLVM goldens and eight
  executable fixtures on both generations, plus exact stage2/stage3 equality.
  This snapshot includes typed Option locals but predates the standalone match
  fallbacks. The final current-source run `build/fixed-point-8a9z1nv3` also passes
  all gates (`generic-fixed-point-current.log`); its optimized successor passes
  all 19 native checks (`generic-current-regressions.log`).
- Broad run: 862 passed, 5 xfailed, 2 xpassed, two failures
  (`generic-broad-tests.log`). One was a 60-second clang object-build timeout,
  reproduced on a separate retry (`generic-object-recheck.log`). The other
  required fallback match arms in the new
  walkers when checked without AST enum definitions. After adding them, all 18
  standalone semantic checks pass (`generic-semantic-recheck.log`).
- The full-compiler object test now allows a bounded 180 seconds for over
  2.5 million LLVM lines, retaining its exit-status and nonempty-object checks.
  The isolated test passed in **79.72 seconds overall** (`generic-object-final.log`).
  Both original broad-run failures are resolved by targeted reruns.
- The long Python-bootstrap optimized build was deliberately stopped after its
  source became obsolete (`build-generics-production.log`, SIGTERM). The final
  production compiler is the optimized native successor built from current
  source, promoted only after the strict gate and focused regressions passed.
- Preserved previous verified production compiler:
  `build/compiler-correctness/mnc-reliability-9c877e62`.

### First committed milestone: historical evidence

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

For the first milestone, validated stage2/stage3 IR was 138,775,939 bytes with SHA256
`7bd42052806224b816222265baee71051b57ecf3fd8e6e94dfccebf08f062492`.
The optimized successor binary SHA256 is
`316dedcf569e887a4b29304a4fd0b9371785224acf11c2ad0b658711c9aaf9c8`.
The input concatenated-source SHA256 is
`0f9dea758f5721fb8d095306833cbcc690d677fd4e7394b258beabc3fcb73860`.
That milestone's optimized production binary SHA256 was
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
- Final optimized production binary: `mapanare/self/mnc-stage1`, copied from
  the verified `build/fixed-point-8a9z1nv3/mnc-stage2` (clang O2). Check the
  current hash at the top of this document when resuming.
- Previous verified production: `build/compiler-correctness/mnc-reliability-9c877e62`.
- Ubuntu WSL; `.venv/bin/python` 3.12.3; clang/LLVM 18.1.3. Runtime rebuilt with
  `make build-rt` for version 5.54.2. Exact hashes live in each gate manifest.

## Next work: priority 2

1. Record the ownership contract for String/List/Map/struct values at function
   arguments, returns, container insertion, copies, and destruction. Start with
   the conservative user-call transfer behavior and alias-clearing fixes above.
2. Add long-running, leak-sensitive regressions for repeated schema/String
   creation and nested container insertion/removal. Track live allocations or
   repeatable steady-state memory growth; the existing ASan tests intentionally
   disable leak detection and do not prove bounded memory use.
3. Fix confirmed cleanup/retention defects, preserving borrowed aliases and
   recursive container semantics. Re-run native executable regressions and
   exact self-hosting after lifetime changes. Preserve both verified compilers.

Priority 2 is sequenced but was not implemented in this task. Keep unrelated
agent-generated files and the desktop restart plan out of compiler commits.

## Resume commands

Run from the repository root in Ubuntu WSL. Windows invocations use
`wsl -d Ubuntu -- bash -c 'cd /mnt/c/Users/Juan/Documents/GitHub/Mapanare && ...'`.
On this host WSL commands require sandbox escalation; this was approved during
this task. Avoid `bash -lc`, whose startup PATH expansion fails here.

```bash
.venv/bin/python scripts/build_stage1.py
.venv/bin/python -m pytest tests/llvm/test_generic_specialization.py tests/integration/test_native_generics.py tests/integration/test_string_return_ownership.py tests/integration/test_native_bool_output.py tests/integration/test_native_loop_stack.py tests/bootstrap/test_fixed_point_validation.py -q
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
compiler changes and were left intact.

The first milestone was subsequently committed as `9c877e62`; its staged scope
check is `precommit-reliability.log` (13 files, 18 indexed symbols, LOW).
Post-commit `analyze --embeddings` and `--force --embeddings` both encountered
duplicate embedding primary keys. The installed CLI documents default embedding
preservation; `npx --offline gitnexus analyze --force --index-only` then completed
successfully (`reindex-preserved.log`), recording HEAD `9c877e62`, 36,155 nodes,
62,366 edges, and 19,351 retained/generated embeddings. `--index-only` avoids
rewriting agent instructions and skills. Do not run concurrent index writers.

For the generic follow-up, CLI impact calls for native AST/parser/semantic/lowerer
symbols returned UNKNOWN/not found (`generic-impact.log`). Source review covers
`lower_expr` -> call/method lowering, specialization -> function lowering, and
semantic definition registration -> call checking. The same-named Python inliner
has CRITICAL impact; that warning was reported before changing the native
inliner's Void-return guard. Full goldens and self-hosting supplement the index's
missing native coverage. Never interpret zero indexed native callers as low risk.

`precommit-native-generics.log`: nine staged files, 12 indexed symbols, zero
affected processes, LOW. The object-build test timeout change has zero indexed
callers/processes and LOW risk. Native coverage still requires source review.

The post-`888ab1f5` embedding-generation refresh hit another duplicate primary
key (`reindex-native-generics.log`). The installed CLI restores cached embeddings
before applying its generation cap. Recovery command:
`npx --offline gitnexus analyze --embeddings 1 --index-only`.
This refreshes the graph while preserving cached embeddings and skipping new
generation for a repository larger than one node. Verify `.gitnexus/meta.json`
records the latest commit and a nonzero embedding count after it finishes.
