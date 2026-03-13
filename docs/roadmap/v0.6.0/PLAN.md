# Mapanare v0.6.0 — "The Compiler"

> v0.5.0 built the ecosystem around the language — linter, playground, registry, docs.
> v0.6.0 must build the **compiler infrastructure beneath it** — so the language
> can grow without drowning in duplicated logic.
>
> Core theme: **MIR, self-hosting, and compiler architecture.**

---

## Scope Rules

1. **Introduce MIR** — a typed, SSA-based intermediate representation between AST and emission
2. **Move optimizer passes to MIR** — constant folding, DCE, agent inlining, stream fusion
3. **Refactor emitters to consume MIR** — eliminate duplicated lowering logic
4. **Advance self-hosting** — multi-module compilation, enum lowering, struct literals
5. **Freeze the Python bootstrap** — snapshot current Python compiler into `bootstrap/`, stop modifying it
6. **No new language features** — no new syntax, no new primitives; this is a compiler-internal version

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Phase Overview

| Phase | Name | Status | Sub-phases |
|-------|------|--------|------------|
| 1 | MIR Design & Core | `Complete` | — |
| 2 | AST → MIR Lowering | `Complete` | — |
| 3 | MIR-Based Optimizer | `Complete` | — |
| 4 | MIR → Emitter Backends | `Complete` | — |
| 5 | Self-Hosted Compiler Gaps | `Complete` | Tasks 5-7 deferred to v0.7.0 |
| 6 | Bootstrap Freeze & Validation | `[ ]` | — |

---

## Phase 1 — MIR Design & Core
**Priority:** CRITICAL — foundation for everything else in this release

The current compiler goes AST → Optimizer (AST) → Emitter (AST). Both emitters
duplicate control flow lowering, constant materialization, struct field access,
and feature detection. MIR sits between semantic analysis and emission, giving
optimizations and backends a single, clean representation to work with.

### Design Goals

- **SSA-based:** Every value is assigned exactly once; phi nodes at control flow merges
- **Typed:** Every MIR value carries its Mapanare type (from semantic analysis)
- **Explicit control flow:** No nested `if`/`match` — basic blocks with terminators
- **Flat:** No nested expressions — everything is `dest = op(args)` three-address form
- **Backend-agnostic:** No Python-isms or LLVM-isms in the MIR itself

### MIR Instruction Set (Core)

```
// Values
Const(dest, type, literal)        // load a constant
Copy(dest, src)                   // copy a value
Cast(dest, src, target_type)      // type conversion

// Arithmetic / Logic
BinOp(dest, op, lhs, rhs)        // +, -, *, /, %, ==, !=, <, >, <=, >=, &&, ||
UnaryOp(dest, op, operand)        // -, !

// Memory / Aggregates
StructInit(dest, type, fields)    // construct a struct
FieldGet(dest, obj, field_name)   // read a struct field
FieldSet(obj, field_name, val)    // write a struct field (mut only)
ListInit(dest, type, elements)    // construct a list
IndexGet(dest, list, index)       // read list[i]
IndexSet(list, index, val)        // write list[i] (mut only)
MapInit(dest, key_type, val_type, pairs)

// Enum / Tagged Union
EnumInit(dest, type, variant, payload)    // construct enum variant
EnumTag(dest, enum_val)                   // extract tag for matching
EnumPayload(dest, enum_val, variant)      // extract payload after tag check

// Option / Result
WrapSome(dest, val)               // Some(val)
WrapNone(dest, type)              // None
WrapOk(dest, val)                 // Ok(val)
WrapErr(dest, val)                // Err(val)
Unwrap(dest, val)                 // extract inner value (after tag check)

// Functions
Call(dest, fn_name, args)         // call a function
Return(val)                       // return from function
ExternCall(dest, abi, module, fn_name, args)  // FFI call (C or Python)

// Control Flow (terminators — one per basic block)
Jump(target_block)                // unconditional jump
Branch(cond, true_block, false_block)     // conditional branch
Switch(tag, cases: [(val, block)], default_block)  // multi-way branch (match)

// Agents / Signals / Streams
AgentSpawn(dest, agent_type, args)
AgentSend(agent, channel, val)
AgentSync(dest, agent, channel)
SignalInit(dest, type, initial_val)
SignalGet(dest, signal)
SignalSet(signal, val)
StreamOp(dest, op_kind, source, args)     // map, filter, fold, etc.

// Strings
InterpConcat(dest, parts)         // string interpolation concatenation

// Phi
Phi(dest, [(block, val), ...])    // SSA phi node at block entry
```

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Define MIR data structures in `mapanare/mir.py` (BasicBlock, Instruction, Function, Module) | `[x]` | Dataclass-based, mirrors AST style |
| 2 | Define MIR instruction enum (all opcodes above) | `[x]` | One dataclass per instruction kind |
| 3 | Define MIR types (map from `types.py` TypeInfo to MIR type representation) | `[x]` | Reuse TypeKind; MIR types are thin wrappers |
| 4 | Implement MIR pretty-printer (textual dump for debugging) | `[x]` | `fn main() { bb0: %0 = const i64 42; ret %0 }` style |
| 5 | Implement MIR verifier (type consistency, SSA dominance, terminator checks) | `[x]` | Catches bugs before emission; run after every pass |
| 6 | Add `mapanare emit-mir` CLI command for debugging | `[x]` | Dump MIR to stdout or file |
| 7 | Add MIR unit tests (construction, pretty-print, verification) | `[x]` | `tests/mir/test_mir_core.py` |

**Done when:** MIR data structures exist, can be constructed programmatically,
pretty-printed to text, and verified for structural correctness.

---

## Phase 2 — AST → MIR Lowering
**Priority:** CRITICAL — connects the existing frontend to the new MIR

The lowering pass walks the typed AST (after semantic analysis) and produces
MIR functions with basic blocks. This is where nested expressions become flat
three-address code and control flow becomes explicit jumps.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `mapanare/lower.py` — AST-to-MIR lowering pass | `[x]` | Walks typed AST, emits MIR instructions |
| 2 | Lower expressions: literals, variables, binary ops, unary ops, calls | `[x]` | Three-address form: `%t = add %a, %b` |
| 3 | Lower `let` bindings (immutable and mutable) | `[x]` | Immutable → single SSA assignment; mutable → alloca-style with load/store |
| 4 | Lower `if`/`else` to basic blocks with `Branch` terminators | `[x]` | Split into then-block, else-block, merge-block with phi nodes |
| 5 | Lower `match` to `Switch` + basic blocks per arm | `[x]` | Extract tag, switch on variant, lower arm bodies; IdentPattern enum variants handled |
| 6 | Lower `for` loops to basic blocks (header, body, exit) | `[x]` | Loop header with branch; body jumps back to header |
| 7 | Lower function definitions (params, body, return) | `[x]` | Entry block receives params; implicit return of last expression |
| 8 | Lower struct construction, field access, method calls | `[x]` | `StructInit`, `FieldGet`, `FieldSet`; methods desugar to `call Type_method(self, ...)` |
| 9 | Lower enum construction and pattern matching | `[x]` | `EnumInit` for construction; `EnumTag` + `Switch` for matching; bare variant Identifiers handled |
| 10 | Lower Option/Result (`Some`, `None`, `Ok`, `Err`, `?` operator) | `[x]` | `?` lowers to tag-check + branch (early return on Err/None); Some/Ok/Err detected as builtins in CallExpr |
| 11 | Lower string interpolation (`InterpString`) | `[x]` | Convert parts to string via Cast, then `InterpConcat` |
| 12 | Lower agent operations (`spawn`, `send`, `sync`) | `[x]` | `AgentSpawn`, `AgentSend`, `AgentSync` instructions |
| 13 | Lower signal operations (`signal()`, `.value` read/write) | `[x]` | `SignalInit`, `SignalGet`, `SignalSet` |
| 14 | Lower stream operations (pipe chains, stream operators) | `[x]` | `StreamOp` with operator kind; detected via method call name |
| 15 | Lower pipe operator (`|>`) | `[x]` | Desugar `a |> f` to `Call(f, [a])` — both PipeExpr and BinaryExpr pipe handled |
| 16 | Lower `extern "C"` and `extern "Python"` declarations | `[x]` | Registered in module.extern_fns during declaration pass |
| 17 | Lower `impl` blocks and trait dispatch | `[x]` | Methods become standalone functions `Type_method`; impl-for-trait uses target type prefix |
| 18 | Lower decorators (`@allow`, `@restart`, etc.) | `[x]` | Attach as metadata on MIR functions via decorators list |
| 19 | Add roundtrip tests: AST → MIR → pretty-print, verify against expected output | `[x]` | `tests/mir/test_lower.py` — 71 tests covering all constructs |
| 20 | Add equivalence tests: ensure MIR lowering preserves semantics (compare Python output before/after) | `[!]` | Deferred: MIR emitters (Phase 4) needed to run MIR through Python backend; verifier-based correctness tests added instead |

**Done when:** Every valid Mapanare program can be lowered to MIR. The MIR
verifier passes on all lowered programs. Existing e2e tests produce identical
output through the MIR path.

---

## Phase 3 — MIR-Based Optimizer
**Priority:** HIGH — migrate existing passes from AST to MIR

The current optimizer in `optimizer.py` operates on AST nodes. Once MIR exists,
these passes should operate on MIR instead — the flat, SSA representation makes
analysis and transformation much simpler.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `mapanare/mir_opt.py` — MIR optimization pass manager | `[x]` | Runs passes in sequence; tracks stats; respects O-levels |
| 2 | Port constant folding to MIR (evaluate `BinOp`/`UnaryOp` on `Const` operands) | `[x]` | Simpler on MIR: just pattern-match instruction operands |
| 3 | Port constant propagation to MIR (replace uses of `Const`-assigned vars) | `[x]` | SSA makes this trivial: follow single def to all uses |
| 4 | Port dead code elimination to MIR (remove instructions with no uses) | `[x]` | Walk use-def chains; remove unused defs |
| 5 | Port dead function elimination (remove uncalled functions) | `[x]` | Build call graph from `Call` instructions |
| 6 | Port agent inlining to MIR (single-spawn agents → direct calls) | `[x]` | Replace `AgentSpawn`/`AgentSend`/`AgentSync` with `Call` |
| 7 | Port stream fusion to MIR (fuse adjacent `StreamOp` instructions) | `[x]` | Combine `map`+`filter`+`fold` into single fused op |
| 8 | Add new pass: unreachable block elimination | `[x]` | Remove blocks with no predecessors (except entry) |
| 9 | Add new pass: branch simplification (constant conditions → `Jump`) | `[x]` | `Branch(true, A, B)` → `Jump(A)` |
| 10 | Add new pass: copy propagation (`Copy(a, b)` → replace uses of `a` with `b`) | `[x]` | Standard SSA optimization |
| 11 | Verify optimizer preserves semantics (run e2e suite at each O-level) | `[x]` | O0 through O3 must produce identical output |
| 12 | Add optimizer pass tests | `[x]` | `tests/mir/test_mir_opt.py` — 61 tests covering all passes |
| 13 | Remove old AST-based optimizer (or gate behind `--legacy-optimizer` flag) | `[x]` | `--legacy-optimizer` flag on `emit-mir`; `optimizer.py` kept for one release |

**Done when:** All existing optimizer passes run on MIR. New SSA-enabled passes
(copy propagation, unreachable block elimination, branch simplification) work.
All e2e tests pass at every optimization level.

---

## Phase 4 — MIR → Emitter Backends
**Priority:** HIGH — the payoff: emitters consume MIR instead of AST

Refactor both emitters to consume MIR. This eliminates the duplicated control
flow lowering, feature detection, and type mapping that currently exists in
both `emit_python.py` and `emit_llvm.py`.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `mapanare/emit_python_mir.py` — Python emitter from MIR | `[x]` | Walk MIR basic blocks, emit Python source |
| 2 | Map MIR instructions to Python constructs | `[x]` | `BinOp` → Python ops; `Call` → function call; `Branch` → if/else |
| 3 | Reconstruct Python control flow from basic blocks | `[x]` | Detect if/else diamonds, loop patterns; emit structured Python |
| 4 | Handle agent/signal/stream MIR instructions → asyncio/reactive runtime | `[x]` | Same runtime imports, but driven by MIR opcodes not AST nodes |
| 5 | Handle `ExternCall` for Python interop | `[x]` | Emit import + wrapper call |
| 6 | Create `mapanare/emit_llvm_mir.py` — LLVM emitter from MIR | `[x]` | Walk MIR, emit llvmlite IR |
| 7 | Map MIR instructions to LLVM IR | `[x]` | `BinOp` → llvmlite builder ops; `StructInit` → alloca + GEP |
| 8 | Map MIR basic blocks to LLVM basic blocks (1:1 mapping) | `[x]` | Natural correspondence; phi nodes map directly |
| 9 | Handle agent MIR instructions → C runtime thread pool calls | `[x]` | Spawn → thread create; Send → ring buffer write; Sync → semaphore |
| 10 | Handle memory management (arena allocation for strings/lists) | `[x]` | Same arena strategy, driven by MIR types |
| 11 | Cross-backend equivalence tests (run all e2e tests through MIR path on both backends) | `[x]` | Equivalence tests in tests/mir/test_emitter_equiv.py |
| 12 | Wire MIR pipeline into CLI: `--use-mir` flag (default off initially) | `[x]` | MIR is default; --no-mir flag for legacy AST path |
| 13 | Make MIR pipeline the default (remove `--use-mir` flag) | `[x]` | MIR pipeline is default (use_mir=True); --no-mir to opt out |
| 14 | Update `emit-llvm` CLI command to go through MIR | `[x]` | emit-llvm uses MIR path by default |

**Done when:** Both emitters consume MIR. All e2e tests pass through the MIR
pipeline on both backends. The MIR path is the default compilation path.

---

## Phase 5 — Self-Hosted Compiler Gaps
**Priority:** MEDIUM — close the remaining gaps preventing full self-hosting

The self-hosted compiler (`mapanare/self/`) has 5,800+ lines of Mapanare code
covering lexer, parser, semantic checker, and LLVM emitter. But it can't produce
a standalone binary yet due to several gaps.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Implement multi-module compilation (resolve imports across `.mn` files) | `[x]` | `_compile_multi_module_llvm` + `build-multi` CLI command; ModuleResolver handles import resolution |
| 2 | Add struct literal syntax to grammar (disambiguate from function calls) | `[x]` | `new Name { field: value }` syntax with `KW_NEW` keyword for LALR disambiguation |
| 3 | Complete enum lowering in LLVM IR (tagged union construction + match) | `[x]` | `_emit_enum_construct` + `_emit_enum_match` + `_extract_enum_payload` in emit_llvm.py |
| 4 | Add string interpolation support to self-hosted lexer/parser | `[x]` | `\$` escape in lexer.mn; `has_interpolation` + `split_interp_parts` in parser.mn |
| 5 | Implement MIR lowering in self-hosted compiler (`mapanare/self/lower.mn`) | `[!]` | Deferred to v0.7.0: requires ~1500 lines of Mapanare; blocked on struct literal usage in self-hosted code |
| 6 | Compile all 6 self-hosted modules into a single native binary | `[!]` | Deferred to v0.7.0: blocked on task 5 (MIR lowering) and full enum codegen in self-hosted emitter |
| 7 | Three-stage bootstrap verification | `[!]` | Deferred to v0.7.0: blocked on tasks 5-6; requires working self-hosted binary |
| 8 | Add self-hosted compiler integration tests | `[x]` | 20 tests in `tests/bootstrap/test_phase5_self_hosted.py` covering struct literals, enum lowering, multi-module, interpolation, bootstrap snapshot |
| 9 | Update `bootstrap/` with frozen v0.5.0 compiler snapshot | `[x]` | All Python sources + grammar copied; README updated with snapshot info |

**Done when:** The self-hosted compiler can compile itself. Three-stage bootstrap
reaches a fixed point. The Python bootstrap is no longer needed for compilation
(only for bootstrapping a new platform).

---

## Phase 6 — Bootstrap Freeze & Validation
**Priority:** MEDIUM — mark the transition point clearly

Once the MIR pipeline is stable and self-hosting gaps are closed, freeze the
Python bootstrap compiler. This is a project milestone, not a code change.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Snapshot Python compiler sources into `bootstrap/` directory | `[ ]` | Copy `mapanare/*.py`, `mapanare/mapanare.lark`, `runtime/*.py` |
| 2 | Add `bootstrap/README.md` explaining the snapshot and how to use it | `[ ]` | "This is the v0.5.0 Python bootstrap compiler, preserved for reference" |
| 3 | Add `bootstrap/Makefile` for bootstrapping from scratch | `[ ]` | `make bootstrap` builds self-hosted compiler from Python bootstrap |
| 4 | Run full test suite through MIR pipeline — confirm 100% pass rate | `[ ]` | All 2,279+ tests must pass |
| 5 | Run full test suite through self-hosted compiler — track pass rate | `[ ]` | Target: compile and run all e2e tests; parser/semantic tests may need adaptation |
| 6 | Update SPEC.md with MIR description in Appendix B | `[ ]` | Add "MIR (Phase 1.5)" between semantic analysis and emission |
| 7 | Write CHANGELOG entry for v0.6.0 | `[ ]` | MIR, optimizer migration, self-hosting progress, bootstrap freeze |
| 8 | Bump VERSION to 0.6.0 | `[ ]` | Update VERSION file, pyproject.toml, CLI version string |
| 9 | Update README with v0.6.0 compiler architecture diagram | `[ ]` | Show AST → MIR → Optimizer → Emitter pipeline |

**Done when:** `bootstrap/` contains a working snapshot of the Python compiler.
The MIR pipeline is the default. Self-hosted compiler compiles itself.
All tests pass. Version is 0.6.0.

---

## What v0.6.0 Does NOT Include

| Item | Deferred To | Reason |
|------|-------------|--------|
| Agent tracing (OpenTelemetry) | v0.7.0 | Production observability — needs stable MIR first |
| Built-in test runner (`mapanare test`) | v0.7.0 | Developer tool; MIR must land first |
| Debug info (DWARF) | v0.7.0 | Needs MIR for clean source mapping |
| Deployment infrastructure (Docker, health checks) | v0.7.0 | Production concern |
| WASM backend | v0.8.0+ | MIR enables this, but not in scope for v0.6.0 |
| GPU kernel dispatch | Post-1.0 | Needs MIR + SPIR-V backend |
| Autograd / computation graphs | Post-1.0 | Research-level feature |
| Effect typing for agents | Post-1.0 | Research-level |
| Session types for channels | Post-1.0 | Research-level |
| SPIR-V backend | Post-1.0 | Needs stable MIR |
| New language syntax or primitives | v0.7.0+ | v0.6.0 is compiler-internal only |

---

## Success Criteria for v0.6.0

v0.6.0 ships when ALL of the following are true:

1. **MIR exists:** Typed, SSA-based intermediate representation with pretty-printer and verifier.
2. **Lowering works:** Every valid Mapanare program can be lowered from AST to MIR.
3. **Optimizer on MIR:** Constant folding, DCE, agent inlining, and stream fusion operate on MIR. New passes: copy propagation, unreachable block elimination, branch simplification.
4. **Emitters on MIR:** Both Python and LLVM emitters consume MIR. All existing e2e tests pass.
5. **MIR is default:** The MIR pipeline is the default compilation path (no `--use-mir` flag needed).
6. **Self-hosting progress:** Multi-module compilation works. Enum lowering complete. Self-hosted compiler can compile itself (three-stage bootstrap).
7. **Bootstrap frozen:** `bootstrap/` contains a working v0.5.0 Python compiler snapshot.
8. **Tests:** All existing tests pass + new MIR tests (core, lowering, optimizer, emitter equivalence).

---

## Priority Order

If time is limited, ship in this order:

1. Phase 1 (MIR core — everything depends on this)
2. Phase 2 (AST → MIR lowering — useless without it)
3. Phase 4 (MIR → emitters — proves MIR works end-to-end, enables validation)
4. Phase 3 (MIR optimizer — port existing passes, add new ones)
5. Phase 5 (self-hosting gaps — high effort, can partially defer to v0.7.0)
6. Phase 6 (bootstrap freeze — ceremonial once the rest lands)

---

*"A compiler without an IR is a translator. An IR without backends is an exercise. Together, they are a platform."*
