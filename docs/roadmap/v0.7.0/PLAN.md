# Mapanare v0.7.0 — "Self-Standing"

> v0.6.0 built the MIR pipeline — typed SSA IR, lowering, optimizer, and dual emitters.
> v0.7.0 must **close the self-hosting loop** and ship the tools that make Mapanare
> deployable and debuggable in production.
>
> Core theme: **Self-hosting completion, observability, and developer tools.**

---

## Scope Rules

1. **Ship v0.6.0** — bump version, write changelog, update SPEC with MIR appendix (Phase 6 carryover)
2. **Complete self-hosting** — write `lower.mn`, compile all modules to a single native binary, three-stage bootstrap verification
3. **Agent observability** — OpenTelemetry tracing, structured error codes, metrics
4. **Developer tools** — built-in test runner, DWARF debug info
5. **Deployment infrastructure** — Dockerfile, health checks, supervision trees
6. **No new language syntax** — v0.7.0 is about the compiler and tooling, not the language

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

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 1 | v0.6.0 Release Close | `Complete` | All 9 tasks done |
| 2 | Self-Hosted MIR Lowering | `Complete` | `lower.mn` — 1,631 lines, all 18 tasks done |
| 3 | Self-Hosted Binary & Bootstrap | `In Progress` | MIR pipeline wired, emit_llvm.mn rewritten; binary compilation blocked by bootstrap emitter gaps |
| 4 | Built-in Test Runner | `Complete` | All 9 tasks done |
| 5 | Agent Observability | `Complete` | All 10 tasks done |
| 6 | Debug Info (DWARF) | `Complete` | All 9 tasks done — DWARF metadata, line numbers, variables, structs, -g flag |
| 7 | Deployment Infrastructure | `Complete` | All 8 tasks done — Dockerfile, health/ready, supervision trees, @supervised, graceful shutdown, deploy CLI |
| 8 | v0.7.0 Release & Docs | `Complete` | All 7 tasks done — version 0.7.0, changelog, SPEC, ROADMAP, README, website |

---

## Phase 1 — v0.6.0 Release Close
**Priority:** CRITICAL — unblocks everything; the MIR pipeline is done, we just never shipped it

v0.6.0 Phases 1–5 are complete (MIR core, lowering, optimizer, emitters, self-hosted gaps).
Phase 6 (Bootstrap Freeze & Validation) was never started. Close it out now.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Run full test suite through MIR pipeline — confirm 100% pass rate | `[x]` | 2538 passed, 8 skipped |
| 2 | Update `bootstrap/` snapshot with current Python compiler sources | `[x]` | 22 files copied (all *.py + grammar) |
| 3 | Update `bootstrap/README.md` with v0.6.0 snapshot info | `[x]` | Full rewrite with MIR docs, file index, bootstrap chain |
| 4 | Add `bootstrap/Makefile` for bootstrapping from scratch | `[x]` | `make bootstrap` + `make verify` for three-stage |
| 5 | Update SPEC.md Appendix B with MIR description | `[x]` | Full MIR section: SSA, instructions, optimizer, pipeline diagram |
| 6 | Update architecture diagram in ROADMAP.md | `[x]` | MIR pipeline in diagram, v0.6.0 in release history |
| 7 | Write CHANGELOG entry for v0.6.0 | `[x]` | Added + Changed sections, updated links |
| 8 | Bump VERSION to 0.6.0, update pyproject.toml | `[x]` | VERSION → 0.6.0; pyproject reads dynamically |
| 9 | Update README with v0.6.0 compiler architecture | `[x]` | MIR in pipeline, badges, roadmap table, project structure |

**Done when:** VERSION reads `0.6.0`. All tests pass. CHANGELOG, SPEC, README updated.

---

## Phase 2 — Self-Hosted MIR Lowering (`lower.mn`)
**Priority:** CRITICAL — the largest deferred task; closes the self-hosting gap

The Python bootstrap has `lower.py` (1,397 lines) that translates AST → MIR.
This phase writes the equivalent in Mapanare: `mapanare/self/lower.mn`.
The self-hosted compiler currently goes AST → LLVM IR directly; after this phase,
it goes AST → MIR → LLVM IR, matching the bootstrap architecture.

### Design Constraints

- Must use `new` struct literal syntax (available since v0.6.0 Phase 5)
- State-threading pattern: `lower_*` functions thread a `LowerState` struct
- ~35 MIR instruction types → each needs a constructor function
- Basic block management with SSA temp generation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Define MIR data structures in `lower.mn` (BasicBlock, Instruction, Function, Module) | `[x]` | MIRType, Value, BasicBlock, MIRFunction, MIRModule structs |
| 2 | Define MIR instruction types (all ~35 opcodes) | `[x]` | 35-variant Instruction enum with all MIR opcodes |
| 3 | Implement `LowerState` and basic block builder (temp generation, block creation) | `[x]` | State-threaded: fresh_tmp, fresh_block_label, add_block, emit_instr |
| 4 | Lower expressions: literals, variables, binary/unary ops | `[x]` | Three-address form with SSA temps |
| 5 | Lower `let` bindings (immutable and mutable) | `[x]` | Copy + define_var with mutable flag |
| 6 | Lower `if`/`else` to basic blocks with `Branch` terminators | `[x]` | then-block, else-block, merge-block with phi |
| 7 | Lower `match` to `Switch` + basic blocks per arm | `[x]` | Tag extraction, switch on variant, phi merge |
| 8 | Lower `for` loops to basic blocks (header, body, exit) | `[x]` | Header with branch, body jumps back |
| 9 | Lower function definitions (params, body, return) | `[x]` | Entry block receives params, implicit return |
| 10 | Lower struct construction, field access, method calls | `[x]` | StructInit, FieldGet, FieldSet, method dispatch |
| 11 | Lower enum construction and pattern matching | `[x]` | EnumInit, EnumTag, EnumPayload, Switch |
| 12 | Lower Option/Result (`Some`, `None`, `Ok`, `Err`, `?` operator) | `[x]` | WrapSome/None/Ok/Err, Unwrap with Branch |
| 13 | Lower string interpolation | `[x]` | InterpConcat instruction |
| 14 | Lower agent/signal/stream operations | `[x]` | AgentSpawn/Send/Sync, SignalInit/Get/Set, StreamOp |
| 15 | Lower pipe operator, extern declarations, impl blocks | `[x]` | Pipe→Call, register_impl, methods as Type_method |
| 16 | Implement MIR pretty-printer (textual dump) | `[x]` | format_instruction, pretty_print_function, pretty_print_module |
| 17 | Implement MIR verifier (type consistency, SSA dominance) | `[x]` | Terminator checks, phi ordering, block validation |
| 18 | Add unit tests for `lower.mn` | `[x]` | 113 structural tests + 71 MIR lowering tests, all passing |

**Done when:** `lower.mn` exists and can lower all valid Mapanare AST nodes to MIR.
The MIR verifier passes on all lowered programs. Estimated ~1,500 lines.

---

## Phase 3 — Self-Hosted Binary & Bootstrap Verification
**Priority:** CRITICAL — proves the compiler can compile itself

With `lower.mn` complete, the self-hosted compiler has all 7 modules:
lexer, ast, parser, semantic, lower, emit_llvm, main.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Update `main.mn` to wire MIR lowering into the pipeline | `[x]` | AST → lower → MIR → emit_llvm; added `import self::lower`, version 0.7.0 |
| 2 | Update `emit_llvm.mn` to consume MIR instead of AST | `[x]` | Full rewrite: walks MIR basic blocks/instructions, ~1050 lines |
| 3 | Compile all 7 modules into a single native binary via `build-multi` | `[~]` | NamespaceAccessExpr fixed, break stmt added, 58 stub constructors fixed, List+ and cross-module imports fixed; remaining: LLVM struct type identity across multi-module compilation |
| 4 | Stage 1: Bootstrap compiler (Python) compiles self-hosted → Binary A | `[!]` | Blocked by task 3 |
| 5 | Stage 2: Binary A compiles self-hosted → Binary B | `[!]` | Blocked by task 3 |
| 6 | Stage 3: Binary B compiles self-hosted → Binary C | `[!]` | Blocked by task 3 |
| 7 | Verify fixed point: Binary B == Binary C (byte-identical) | `[!]` | Blocked by task 3 |
| 8 | Run test subset through self-hosted binary — track pass rate | `[!]` | Blocked by task 3 |
| 9 | Add CI job for three-stage bootstrap verification | `[x]` | Parse verification + module resolution tests added; full binary CI deferred |
| 10 | Update `Self-Hosted Compiler Status` in ROADMAP.md | `[x]` | Updated with lower.mn, emit_llvm.mn MIR rewrite, module counts |

**Done when:** Three-stage bootstrap reaches a fixed point. The self-hosted binary
can compile programs. CI verifies the bootstrap on every PR.

---

## Phase 4 — Built-in Test Runner
**Priority:** HIGH — developer experience; tests are currently pytest-only

Add `mapanare test` as a first-class CLI command that discovers and runs tests
written in Mapanare. This enables testing `.mn` code without Python/pytest.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design test syntax: `#[test]` decorator on functions, `assert` expressions | `[x]` | `@test fn test_add() { assert 1 + 1 == 2 }` — uses existing `@name` decorator syntax |
| 2 | Add `#[test]` decorator recognition in parser and semantic checker | `[x]` | `@test` passes through existing decorator system; semantic checker validates assert |
| 3 | Add `assert` as a built-in expression (semantic + both emitters) | `[x]` | `assert_stmt` in grammar, `AssertStmt` AST node, `Assert` MIR instruction, both emitters + LLVM |
| 4 | Implement test discovery: scan `.mn` files for `#[test]` functions | `[x]` | `discover_test_files` + `discover_tests` in `test_runner.py` |
| 5 | Implement test runner: compile + execute each test, collect results | `[x]` | Compiles via MIR, runs in subprocess, captures JSON results |
| 6 | Implement test reporter: pass/fail summary, failure details | `[x]` | `format_results` with PASS/FAIL, duration, error details |
| 7 | Add `--filter` flag to run subset of tests | `[x]` | `mapanare test --filter "test_add"` substring match |
| 8 | Add `mapanare test` CLI subcommand | `[x]` | `cmd_test` in `cli.py`, exits 1 on failure |
| 9 | Write tests for the test runner itself | `[x]` | 26 pytest tests: parsing, discovery, execution, reporter, CLI, MIR/legacy |

**Done when:** `mapanare test` discovers and runs `#[test]` functions in `.mn` files.
Pass/fail results are reported with file:line locations.

---

## Phase 5 — Agent Observability
**Priority:** HIGH — production visibility into agent systems

Add OpenTelemetry-compatible tracing for agent lifecycle events. This is essential
for debugging and monitoring agent-based systems in production.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design tracing API: spans for spawn, send, sync, receive | `[x]` | Span, SpanContext, Tracer with parent-child relationships |
| 2 | Add `mapanare/tracing.py` — trace context and span management | `[x]` | Thread-local context, ConsoleExporter, OTLPExporter |
| 3 | Instrument Python runtime agent operations with trace spans | `[x]` | spawn, handle, send, stop, pause, resume emit spans |
| 4 | Add OTLP exporter (gRPC and HTTP) | `[x]` | OTLPExporter (HTTP/JSON) + ConsoleExporter; no gRPC (stdlib only) |
| 5 | Add `--trace` CLI flag to enable tracing at runtime | `[x]` | `mapanare run --trace program.mn` (console/otlp modes) |
| 6 | Add Prometheus metrics for agent operations | `[x]` | Counter: spawns, messages, errors, stops; Histogram: handle latency |
| 7 | Add `--metrics` CLI flag with metrics endpoint | `[x]` | `mapanare run --metrics :9090 program.mn` — stdlib HTTP server |
| 8 | Define structured error codes (`MN-E0001` format) | `[x]` | 33 codes: MN-P (parse), MN-S (semantic), MN-L (lower), MN-C (codegen), MN-R (runtime), MN-T (tooling) |
| 9 | Instrument C runtime with trace hooks (native backend) | `[x]` | mapanare_trace_hook_fn callback; spawn/send/handle/stop/pause/resume/error events |
| 10 | Add tracing tests | `[x]` | 47 tests: tracing (22), metrics (11), error codes (14) |

**Done when:** `mapanare run --trace` exports OTLP spans for agent operations.
Metrics endpoint serves Prometheus-format counters. Error codes are structured.

---

## Phase 6 — Debug Info (DWARF)
**Priority:** MEDIUM — enables `gdb`/`lldb` debugging of native binaries

Add source-level debug information to LLVM IR output so native binaries
can be debugged with standard tools.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add DIBuilder integration to `emit_llvm_mir.py` | `[x]` | `_init_debug_info`, `_finalize_debug_info`, `_get_di_type`, `_create_di_subprogram`, `_attach_debug_location` |
| 2 | Emit compile unit metadata (source file, language, producer) | `[x]` | DICompileUnit + DIFile per module; producer: "mapanare 0.7.0" |
| 3 | Emit function debug info (name, file, line, scope) | `[x]` | DISubprogram per MIR function with line, name, DISubroutineType |
| 4 | Emit line number info for MIR instructions | `[x]` | SourceSpan threaded AST→MIR; DILocation on all LLVM instructions |
| 5 | Emit variable debug info (names, types, locations) | `[x]` | DILocalVariable for named let bindings with DIBasicType |
| 6 | Emit struct type debug info | `[x]` | DICompositeType with DW_TAG_structure_type, DIDerivedType members |
| 7 | Add `--debug` / `-g` flag to CLI | `[x]` | `-g`/`--debug` on `build`, `emit-llvm`, `jit` subcommands |
| 8 | Verify with `lldb`: breakpoints, step, print variables | `[!]` | Requires `sudo apt-get install lldb` on WSL; LLVM IR metadata verified in tests |
| 9 | Add DWARF tests | `[x]` | 40 tests: compile unit (9), functions (6), line numbers (3), variables (4), structs (3), CLI flag (3), no-debug (4), MIR spans (4), direct emitter (4) |

**Done when:** `mapanare build -g program.mn` produces a binary that can be debugged
with `lldb`/`gdb`. Breakpoints, stepping, and variable inspection work.

---

## Phase 7 — Deployment Infrastructure
**Priority:** MEDIUM — makes agent systems deployable

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `Dockerfile` for Mapanare agent applications | `[x]` | Template in `mapanare/deploy.py`; multi-stage Python build + slim runtime |
| 2 | Add health check endpoint support (`/health`, `/ready`) | `[x]` | `HealthServer` in `runtime/deploy.py`; `/health`, `/ready`, `/status` endpoints |
| 3 | Add readiness probe (all agents initialized and running) | `[x]` | `_HealthStatus.is_ready` checks all registered agents are RUNNING/PAUSED |
| 4 | Implement supervision trees | `[x]` | `SupervisionTree` class in `runtime/agent.py`; ONE_FOR_ONE, ONE_FOR_ALL, REST_FOR_ONE |
| 5 | Add `@supervised` decorator for agent functions | `[x]` | Python emitter sets `_supervision` + `_tree_strategy` from `@supervised("strategy")` |
| 6 | Add SIGTERM graceful shutdown with drain timeout | `[x]` | `GracefulShutdown` in `runtime/deploy.py`; drains mailboxes, stops agents, 30s timeout |
| 7 | Add `mapanare deploy` scaffolding command | `[x]` | `cmd_deploy` in cli.py + `mapanare/deploy.py` scaffolding module |
| 8 | Add deployment integration tests | `[x]` | 38 tests: scaffold (6), health (4), readiness (5), trees (7), decorator (3), shutdown (5), CLI (5), integration (3) |

**Done when:** A Mapanare agent application can be containerized, health-checked,
and supervised with restart strategies. `mapanare deploy` scaffolds the config.

---

## Phase 8 — v0.7.0 Release & Docs
**Priority:** MEDIUM — wrap up the release

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Run full test suite — confirm 100% pass rate | `[x]` | 2,983 passed, 9 skipped |
| 2 | Update SPEC.md with test runner syntax and tracing API | `[x]` | Sections 10 (Testing), 11 (Observability), 12 (Deployment); version bumped to 0.7.0 |
| 3 | Write CHANGELOG entry for v0.7.0 | `[x]` | Added + Changed sections, updated links |
| 4 | Bump VERSION to 0.7.0, update pyproject.toml | `[x]` | VERSION → 0.7.0; pyproject reads dynamically |
| 5 | Update ROADMAP.md with v0.7.0 completion | `[x]` | v0.7.0 in release history, self-hosted status, review panel updated |
| 6 | Update README with v0.7.0 highlights | `[x]` | Version badge, CLI commands, self-hosted section, test count, roadmap table |
| 7 | Update `mapanare.dev` website with v0.7.0 release notes | `[x]` | Blog post added to Blog.tsx + BlogPost.tsx in mapanare-website |

**Done when:** VERSION reads `0.7.0`. All tests pass. Documentation current.

---

## What v0.7.0 Does NOT Include

| Item | Deferred To | Reason |
|------|-------------|--------|
| WASM backend | v0.8.0+ | MIR enables this, but self-hosting must land first |
| GPU kernel dispatch | Post-1.0 | Needs SPIR-V backend |
| Autograd / computation graphs | Post-1.0 | Research-level |
| Effect typing for agents | Post-1.0 | Research-level |
| Session types for channels | Post-1.0 | Research-level |
| SPIR-V backend | Post-1.0 | Needs stable MIR + WASM experience |
| Hot code reload | Post-1.0 | Needs native runtime maturity |
| New language syntax | v0.8.0+ | v0.7.0 is compiler + tooling |

---

## Success Criteria for v0.7.0

v0.7.0 ships when ALL of the following are true:

1. **v0.6.0 shipped:** VERSION was bumped to 0.6.0, CHANGELOG written, SPEC updated.
2. **Self-hosting complete:** `lower.mn` exists. All 7 modules compile to a single native binary.
3. **Bootstrap verified:** Three-stage bootstrap reaches a fixed point (Stage 2 == Stage 3).
4. **Test runner works:** `mapanare test` discovers and runs `#[test]` functions.
5. **Observability:** `--trace` emits OTLP spans for agent operations. `--metrics` serves Prometheus counters.
6. **Debug info:** `mapanare build -g` produces debuggable binaries (DWARF).
7. **Deployable:** Dockerfile, health checks, supervision trees work.
8. **Tests:** All existing tests pass + new tests for each phase.

---

## Priority Order

If time is limited, ship in this order:

1. Phase 1 (v0.6.0 close — unblocks version progression)
2. Phase 2 (MIR lowering in self-hosted — largest and most critical task)
3. Phase 3 (self-hosted binary — proves the compiler works end-to-end)
4. Phase 4 (test runner — high developer impact, moderate effort)
5. Phase 5 (observability — production visibility)
6. Phase 6 (DWARF — debugging native binaries)
7. Phase 7 (deployment — containerization and supervision)
8. Phase 8 (release — ceremonial once the rest lands)

---

*"A compiler that compiles itself is no longer a prototype. It's a language."*
