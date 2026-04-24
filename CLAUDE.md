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

- **v5.5.5** (shipped) — **Sh.4 Option B Phase 2 —
  scheduler-driven AwaitSuspend.** Replaces v5.5.4's
  synchronous `llvm.coro.resume` drive inside
  `AwaitSuspend` with the real 6-block save/suspend/switch
  pattern mirroring `emit_llvm_text.py:5305-5372`. Fast-path
  readiness check → `aw.drive.N` (coro.resume inner once) →
  `aw.check.N` (re-check state) → `aw.suspend.N`
  (`__mn_coro_register_wait` + `llvm.coro.save` +
  `llvm.coro.suspend` + switch to `coro.ret`/`aw.resume.N`/
  `coro.cleanup`) → `aw.resume.N` → `aw.ready.N` (payload
  extract). All SSA names prefixed `aw.*.N` via `st.counter`.
  `emit_llvm.mn` `await_suspend` branch: +80 / −15 LOC.
  Post-opt CoroSplit now produces **outer** resume/destroy
  split pairs for every async fn with awaits: 56 ships
  `@outer.resume`/`@outer.destroy`, 57 ships
  `@fanout.resume`/`@fanout.destroy`, 58 ships
  `@process.resume`/`@process.destroy`, 59 ships
  `@fanout.resume`/`@fanout.destroy` — proving the outer
  coroutines really do have suspension points now (v5.5.4
  elided them because every resume was synchronous). PLAN.md
  §R5 predicted the 5 Sh.4 goldens might hang; reality —
  they all still execute correctly (55→42, 56→43, 57→110,
  58→done, 59→220) because the check-after-drive fast-path
  short-circuits: Sh.4 async fns return constants with no real
  I/O, so `future.state==1` is already true when `aw.check.N`
  runs, and control never reaches `aw.suspend.N` /
  `register_wait` / `coro.suspend` at runtime. CoroSplit
  still generates the suspend edge; it just never fires.
  Extended fast-path + no coro.destroy + no free in
  `aw.ready.N` matches the Python reference (structurally
  necessary: `%aw.hdl.N` is defined only on the drive edge,
  so it does not dominate ready from the fast-path or
  scheduler-resume edges — leak preferred over dominance
  violation). stage2.ll 194,553 lines (+501 vs v5.5.4, +0.26%)
  / 906 defines, llvm-as clean. Goldens 59/66 preserved;
  `make lint` clean; non-bootstrap pytest 5507 passed (after
  rebuilding `libmapanare_rt.a` for the version macro bump);
  bootstrap pytest 225 passed. BlockOn scheduler integration +
  `__mn_coro_scheduler_init` in main deferred to v5.5.6 —
  that's the release where the suspend path actually becomes
  load-bearing for non-trivial async programs. Risks R1-R5
  from PLAN.md all mitigated or observed-not-realized. See
  `docs/roadmap/v5/v5.5.5/SESSION_REPORT.md`.
- **v5.5.4** (shipped) — **Sh.4 Option B Phase 1 — real LLVM
  coroutines.** First real-coroutine release. Ships
  `presplitcoroutine` + full `@llvm.coro.id/begin/save/
  suspend/end` pipeline on async fns. `opt -O1` runs
  CoroSplit and produces `@foo.resume` + `@foo.destroy` split
  functions (verified). All 5 Sh.4 goldens execute correctly
  through the real LLVM coroutine ABI: 55→42, 56→43, 57→110,
  58→done, 59→220. Phase 0 empirical findings: (Q2) `llc
  -O2` alone crashes on coro intrinsics — `opt -O1 in.ll |
  llc -O2` pipeline required; (Q3) Ve.1 stage3 regression is
  orthogonal to async, stage2.ll remains llvm-as clean.
  Changes: `mir_opt.mn::should_inline` skips async fns (+9
  LOC); `emit_llvm.mn` (+~190 LOC) adds `is_async` gate to
  `emit_mir_function` (ptr return + presplitcoroutine attr +
  coro.entry prologue + pre_entry trampoline + coro.final/
  cleanup/ret epilogue), `emit_mir_return` rewrites `ret
  <ty> <val>` to box-payload store + `br %coro.final` via a
  `"ASYNC_PTR:"` prefix on `current_ret_type`, and
  `emit_mir_by_kind` replaces Option A's copy-based
  AwaitSuspend/BlockOn with real `llvm.coro.resume` + GEP +
  load + `llvm.coro.destroy` + free (bundled together
  because async fns now return `ptr` not the declared T).
  FnEntry registration bumped to ret_type="ptr" for async in
  both forward-declare and per-function sites. v4.102.0
  handle-reload foot-gun respected: handle loaded once pre-
  resume, reused for coro.destroy. Goldens 59/66 preserved;
  stage2.ll 194,052 lines / 906 defines, llvm-as clean;
  valgrind 0 errors on 55. Scheduler still declared but
  unused — v5.5.5 adds scheduler-driven await, v5.5.6 adds
  scheduler-driven block_on + main lifecycle. Risks R1-R7
  from DESIGN.md §6 all mitigated or deferred appropriately.
  See `docs/roadmap/v5/v5.5.4/SESSION_REPORT.md`.
- **v5.5.3** (shipped) — **Self-hosted coroutine emission
  design (docs-only).** Zero code changes. Ships one 480-line
  `DESIGN.md` that (1) re-validates v4.67.0 DESIGN.md against
  v5.5.x context, (2) surveys how Rust / Go / C++20 / Zig
  handle async and confirms LLVM switched-resume coroutines
  remain the correct choice, (3) maps the 6 remaining
  emitter-side gaps between v5.5.2's synchronous Option A
  stubs and full Python-parity coroutine emission, (4)
  specifies implementation phases v5.5.4 (inliner gate + async
  fn structural rewrite, ~155 LOC) → v5.5.5 (AwaitSuspend,
  ~90 LOC) → v5.5.6 (BlockOn + main scheduler lifecycle,
  ~80 LOC) → v5.5.7 (sanitizer hardening) → v5.5.8 (spawn +
  join + multi-fanout golden) → v5.5.9 (PARITY_GAPS.md Sh.4
  Historical + docs). User directive: "no cheap shit that
  bites us later" — Option A silently degrades any async fn
  with real I/O to single-threaded blocking. v5.5.4+ ships
  the real thing: `presplitcoroutine` attribute + full
  `@llvm.coro.id/size/begin/save/suspend/end` pipeline +
  `{i8 state, ptr payload}` Future struct + real scheduler
  drive via the existing C runtime API (which has been
  complete and TSan-clean since v5.1.4 — no runtime work
  needed). Risk register flags drop-glue × coroutine cleanup
  as HIGH; Ve.1 (stage3 segfault) noted as adjacent concern.
  Goldens 59/66 unchanged. See `docs/roadmap/v5/v5.5.3/`.
- **v5.5.2** (shipped) — **Sh.4 Phase 3 (Option A) — synchronous
  async emission.** Ships coroutine intrinsic + scheduler
  runtime declarations (17 decls total: 6 `__mn_coro_scheduler_*`
  + 11 `@llvm.coro.*` — unconditional, linker drops unused)
  and real emission for `AwaitSuspend` / `BlockOn` MIR variants
  as synchronous copies (`%dest = add i64 0, %future`). **Async
  fns stay as plain fns returning their declared type — no
  `presplitcoroutine`, no coroutine frame, no future struct.**
  All 5 Sh.4 goldens now llvm-as clean **and execute
  correctly**: 55_async_basic → 42, 56_async_await → 43,
  57_real_await → 110, 58_async_file_io → done, 59_async_fanout
  → 220. The tradeoff: Option A only works because every Sh.4
  golden uses `return <const>` async fns with no real
  suspension points. `mir_opt.mn::replace_uses_in_instr` +
  `clone_instr_for_inline` gain cases for `await_suspend` /
  `block_on` so the inliner properly renames the future operand
  when a call gets inlined into `block_on(...)`. Goldens harness
  59/66 unchanged; self-hosting preserved (stage2.ll 192,790
  lines / 906 defines, llvm-as clean). Valgrind 0 errors on
  55_async_basic. Option B (real coroutine wrapping) deferred
  to v5.5.3+ — that's where `presplitcoroutine` + future struct
  alloc + `ret → future.payload` rewrite + scheduler-driven
  `block_on` land, closing Sh.4 semantically for non-trivial
  async programs. See `docs/roadmap/v5/v5.5.2/`.
- **v5.5.1** (shipped) — **Sh.4 Phase 2 — MIR variants +
  lowerer.** Adds `AwaitSuspend(Value, Value)` + `BlockOn(Value,
  Value)` to `mir.mn::Instruction`, matching string-tag
  dispatch branches (`"await_suspend"` / `"block_on"`) in
  `instr_kind` + `instr_dest`, plus accessors for the future
  operand. New helper `fn_is_async(f: MIRFunction) -> Bool`
  scans the existing `decorators` list for `"async"` —
  non-invasive, no struct-layout change, no Reg.1 registry
  bump. The parser already stashes `async fn` as a `"async"`
  decorator (`parser.mn:797–798`); the helper is the
  authoritative check the v5.5.2 emitter will use to wrap the
  function body in a coroutine frame. `lower.mn` now emits
  `Instruction::AwaitSuspend(dest, inner)` for `await expr`
  (was a silent pass-through previously) and
  `Instruction::BlockOn(dest, args[0])` for `block_on(future)`
  (before monomorphization; mirrors `lower.py:1836–1845`).
  `emit_llvm.mn` gets stub handlers for both kinds that emit a
  comment line — prevents the `ERROR: unknown MIR instruction
  kind` stderr spam while keeping IR text stable and
  inspectable. Stub IR references undefined SSA names for
  dest; `llvm-as` still rejects — that's v5.5.2's fix.
  Goldens harness 59/66 unchanged (v5.5.0 already bumped it).
  Self-hosting preserved: stage1 compiles `mnc_all.mn` →
  191,802-line stage2.ll / 908 defines / 0 stderr. 7 FAIL
  unchanged. See `docs/roadmap/v5/v5.5.1/`.
- **v5.5.0** (shipped) — **Sh.4 Phase 1 — async builtin semantic
  registration.** Micro-release split: the original monolithic
  v5.5.0 plan (builtins + lower + emit + close Sh.4) re-scoped
  into v5.5.0 / v5.5.1 / v5.5.2. This release only touches
  `mapanare/self/semantic.mn` (+17 lines, 3 edits): adds
  `block_on` to `is_builtin_function`, `builtin_return_type`
  (returns `<unknown>` — type-inferred from the awaited
  `Future<T>`), and `register_builtins`; plus an explicit
  `"await"` case in `infer_expr` that recurses into the inner
  expression so errors inside `await foo()` are caught. 5 Sh.4
  goldens (55_async_basic through 59_async_fanout) advance past
  `mnc-stage1`'s semantic check and emit LLVM IR; the IR still
  contains an undeclared `call i64 @block_on(...)` and would
  fail `llvm-as` / not link. `scripts/test_native.py` compares
  stage1 against the Python bootstrap by function-count /
  function-name set (not IR validity, per v4.126.0 relaxation),
  so the harness PASS count flips **54/66 → 59/66** even though
  execution correctness is pending. `spawn` / `join` builtins
  deferred — the 5 goldens don't use them. 7 failures remain
  (Sh.6 × 5 tensor, Sh.7 × 1 closure, B × 1 bootstrap-fail);
  no regressions in the previously-passing 54. `v5.5.1` adds
  `BlockOn` / `AwaitSuspend` MIR variants + lowerer + Fn.is_async
  propagation; `v5.5.2` adds emitter coroutine intrinsic
  emission, scheduler init, and closes Sh.4 with sanitizer
  sweeps. See `docs/roadmap/v5/v5.5.0/`.
- **v5.4.4** (shipped) — **Own.1 Phase 2 — Move-aware drop-glue
  infrastructure; guard-lift deferred.** Three new `EmitState`
  fields (`str_owned_source`, `list_owned_source`, `boxed_owned_source`)
  parallel to the existing owner lists, carrying the bare SSA source
  name the slot was allocated for; registry 22/22 clean. Python
  mirror: `_local_strings_source` / `_local_boxed_source` /
  `_list_vars_source` lists + `_moved_locals: set[str]`. Lowerer Move
  emission in both `lower.mn` and `lower.py`: `Move(val)` fires after
  every resource-consuming op (list.push, map/list IndexSet,
  StructInit per field, EnumInit per payload, Some / Ok / Err, and
  MapInit literals). Drop-glue helpers rewritten to accept
  `List<String>` of ret-ptrs; `is_moved` check consults the parallel
  source array. Also fixes a latent `emit_fn` flush cap of 65536 that
  silently truncated large functions' drop-glue tail (raised to 1M).
  Guard-lift for `%struct.*` returns was implemented (one-level field
  walk extracting each escaping String/List/ptr) and reverted: the
  ~40 extractvalue lines per `%struct.EmitState`-returning call site
  inflated stage2.ll by 5× and triggered mnc-stage2 runtime segfault
  during lex of mnc_all.mn. v5.4.5+ re-lifts with a size gate.
  62_list_output stays LEAK; baseline unchanged from v5.4.3. Goldens
  54/66, UAF 55/11/0, valgrind 0 new ERRORS — all preserved.
  **Ve.1 regressed:** stage2.ll `llvm-as` OK but mnc-stage2 segfaults
  before stage3 emission (previously crashed on teardown with non-
  empty stage3). Not remediated this release. See
  `docs/roadmap/v5/v5.4.4/`.
- **v5.4.3** (shipped) — **Own.1 Phase 2 — close Rt.03 (loop-
  reassignment leaks).** Adds `EmitState.loop_depth: Int` (19th field,
  Reg.1 gate 24 → 25 clean) with matched push/pop around `for_body` /
  `while_body` / `mapfor_body` label emission in `emit_mir_basic_block`;
  Python `LLVMTextEmitter._loop_depth` + `_emit_fn` reset + push/pop
  around `for bb in fn.blocks` provide parity. `emit_track_string` /
  `_boxed` / `_closure` (self-hosted) + `_track_string` / `_track_boxed`
  / `_track_closure` (Python) prepend a `load {slot_ty}, slot` +
  `@__mn_str_free` / `@free` before the store when `loop_depth > 0`;
  outside loops the emission is byte-identical to v5.4.2. Zero-init in
  the entry-block prelude + null-tolerant runtime free fns make the
  first-iteration free a no-op. Closes Rt.03: 22_string_builder 6 objs
  / 19 B → CLEAN; baseline TSV refreshed; regression back to leaking
  now fails CI. D3 UAF risk (aliased copies + reassignment) did not
  materialize on the current corpus — UAF sweep byte-identical (55
  CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN). Goldens 54/66 preserved;
  valgrind 66 WARNINGS_ONLY / 0 ERRORS preserved; leak sweep 45 CLEAN /
  3 LEAK (baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0
  regressions. stage2.ll 169280 lines (+0.19% vs v5.4.2); `llvm-as`
  OK. `docs/known_issues.md` Rt.03 row flipped to CLOSED. See
  `docs/roadmap/v5/v5.4.3/`.
- **v5.4.2** (shipped) — **Own.1 Phase 2 — ASan leak-detection
  gate.** Flips `detect_leaks=1` across all 66 goldens via new
  `scripts/run_asan_leak_goldens.sh` (compile with `mnc-stage1`, `llc`
  to object, link with `libmapanare_rt.a` under `-fsanitize=address`,
  run under LSan). First sweep revealed 5 leak classes; 2 fixed by
  extending Phase 3.2's tracking hook with `is_string_returning_
  builtin(fn_name)` (13 Mapanare-level builtins whose MIR dest
  defaults to `mir_unknown()` in lower.mn's generic call path — 4
  goldens, 9 objs / 202 B) and adding `emit_track_boxed(ep)` in
  `emit_enum_init`'s boxed-payload branch (1 golden / 16 B).
  Suppressions (`scripts/asan_leak_suppressions.txt`, LSan format via
  `LSAN_OPTIONS`) trim libcuda cuInit; Mesa/Vulkan loader
  (`<unknown module>`) + loop-reassignment + struct-return
  intermediates are baseline-gated in `scripts/check_leak_summary.py`
  with PLAN.md §D3 / §D4 deferrals to v5.4.3. `make leak-check` +
  `.github/workflows/sanitizers.yml` leak-check job ratify the sweep
  as a merge gate. Goldens 54/66 preserved; UAF sweep 55/11
  preserved; valgrind 0 ERRORS preserved; leak sweep 44 CLEAN / 4
  LEAK (baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0
  regressions. stage2.ll 168k lines (+1.8%); `llvm-as` OK. See
  `docs/roadmap/v5/v5.4.2/`.
- **v5.4.1** (shipped) — **Own.1 Phase 2 — make v5.4.0 drop-glue
  actually fire.** Populates v5.4.0's dormant owner lists with the
  shadow-slot architecture ported from Python. Three new `EmitState`
  fields (`entry_prelude_lines`, `entry_block_body`,
  `in_entry_block`) buffer the function body while `emit_track_*`
  can fire from any basic block; prelude flushes into the entry
  block at function close. Owner lists populated at `emit_mir_call`
  dispatch (runtime + user String returns), `emit_binop +` (String
  concat), `emit_interp_concat` (intermediates), `emit_list_init`
  (allocas hoisted + zero-init so they dominate all drop-glue
  loads). Drop-glue revised with per-slot `icmp eq ptr` +
  multi-block branch to skip frees that would alias the returned
  value (scalar String / List / ptr). Aggregate returns (struct /
  enum / Option / Result) conservatively skip all drops — UAF-safe,
  leaks until v5.4.2. Runtime free declarations landed. String
  literals intentionally NOT tracked (Python omits; rodata, is_heap=0
  no-ops, tracking each would explode IR quadratically). Goldens
  54/66; valgrind 0 new ERRORS; ASan 55 CLEAN / 11 CRASH_NO_ASAN
  unchanged; narrow leak test (`greet()`) reports 0 leaks under
  `detect_leaks=1`. stage2.ll 165k lines (+33% vs baseline, within
  R3 budget); stage2 `llvm-as` OK. See `docs/roadmap/v5/v5.4.1/`.
- **v5.4.0** (shipped) — **Own.1 Phase 2 — self-hosted drop-glue
  infrastructure.** Phase 0 baseline revealed all 11 Sh.2 tests
  already pass; release rescoped from "close 11 Sh.2 goldens" to
  "memory-correctness infrastructure, 0 new goldens". Ships: `Move`
  MIR variant (both emitters), four ownership slots in `EmitState`,
  three drop-glue helpers + `emit_drop_glue` dispatcher wired into
  `emit_mir_return`, Python `_do_move` routing to `_move_resource`,
  self-hosted `"move"` kind populating `moved_locals`. Goldens
  54/66 preserved; valgrind + ASan byte-identical to baseline.
  Owner-list population + lowerer Move emission + runtime free
  declarations deferred to v5.4.1. See `docs/roadmap/v5/v5.4.0/`.
- **v5.3.3** (shipped) — **SPEC + docs polish.** Zero compiler
  changes. SPEC §30 Package Management (manifest, install, lock,
  constraints, registry API). SPEC header 4.143.0 → 5.3.3 (27-release
  staleness closed). `examples/signals/counter.mn` signal demo. All
  three Coral LOW carry-forwards closed. Closeout arc complete.
  See `docs/roadmap/v5/v5.3.3/`.
### Planned / in-progress

- **v5.4.5** — **Close Rt.04 + fix Ve.1 regression.** Re-lift the
  `%struct.*` aggregate-return guard with a size gate (skip field
  walk when struct has >N fields, or when the calling function has
  >M tracked slots). Diagnose and remediate the Ve.1 regression
  introduced in v5.4.4 (mnc-stage2 segfault during lex of
  mnc_all.mn).
- **v5.5.0** — **Sh.4 — self-hosted async.** `block_on`/`await` +
  coroutine lowering.
- **v5.6.0** — **Sh.6 — self-hosted tensor.** `Tensor`/`Float` types
  + nested-array literal parser.
- **v5.7.0** — **Sh.7 + or-pattern fix — 66/66.**
- **v5.7.1** — SPEC + docs polish (pre-panel).
- **v5.8.0** — **RE-PANEL** (target 9.7+). Features first, panel last.

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

**Current baseline:** 54/66. The 12 gap: Sh.2 (11), Sh.4 (5),
Sh.6 (5), Sh.7 (1), bootstrap-also-fails (1). Closure tracked
across v5.4.0–v5.7.0.

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
| `/culebra-scan` | Culebra v2.0.0 — 49 templates (41 IR + 8 C) |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (27389 symbols, 61093 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
