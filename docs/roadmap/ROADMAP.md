# Mapanare Roadmap

> **Mapanare** is an AI-native compiled programming language.
> Agents, signals, streams, and tensors are first-class primitives — not libraries.
>
> [mapanare.dev](https://mapanare.dev) · [GitHub](https://github.com/Mapanare-Research/Mapanare)

---

## Where We Are (v4.61.0 shipped — Arc 6 panel close: deprecation + deletion graded, PASS 8.71/10)

**The compiler core is in the best shape of its life.** 46/46 golden tests,
11/11 stage2 modules, 4,845+ pytest, fixed-point self-compilation, structural
refactor (v4.2.0–v4.17.0) verified by reviewers as solid.

**But the v4.18.0–v4.26.0 evolution arc shipped six hollow features in eight
versions.** A 7-reviewer panel ran against v4.26.0 and returned the largest
single-cycle regression in project history: aggregate score **9.79 → ~8.2**,
**4 NEEDS WORK + 3 PASS WITH NOTES, 0 unconditional PASS** (first non-unanimous
panel since v3.33.0). Seven independent reviewers converged on the same finding:
features were merged when they parsed, regardless of whether they ran. Read
`.reviews/v4.26.0/README.md` for the full report.

The hollow features:

- `const` keyword is a parser alias for `ModuleLetDef` — no immutability, tensor `[N, N]` silently drops shape
- `@gpu` / `@cuda` / `@vulkan` raise `NotImplementedError` at `lower.py:986`
- `await` is `return self._lower_expr(expr.expr)` — pure identity
- v4.25.0 FFI ships broken: DCE drops non-main-reachable functions, runtime archive not -fPIC, ctypes wrappers have no argtypes/restype
- v4.5.0 MIR verifier never wired into `compile()` — dead code 21 versions
- v4.17.0 fixed-point bootstrap verification cannot fail (`EXIT=0` unconditional)

Plus process collapse: CHANGELOG advertises tests that don't exist; carry-
forward resolution rate fell from ~64% to ~10%; two v4.0.0 hard-blockers
(matmul) are byte-identical to v3.47.0 — 27 versions overdue.

**v4.27.0 starts the recovery arc.** Five focused versions, each with strict
"no new features" exit criteria. Goal: get the next 7-reviewer panel back to
≥9.0 aggregate with zero NEEDS WORK verdicts. The recovery arc terminates
externally — when the panel says it does, not when the lead does.

---

## What's Next — Recovery Arc (v4.27.0 → v4.31.0)

After the v4.26.0 panel verdict, the next 5 versions are a **recovery arc**.
Zero new features. Each version has explicit no-new-features exit criteria.
Each version's PLAN.md includes a "what this version explicitly does NOT do"
section to prevent scope creep.

| Version | Theme | Closes | Estimated |
|---------|-------|--------|-----------|
| **v4.27.0** | Honesty Recovery (CRITICAL) | 8 CRITICAL items: FFI argtypes/restype, FFI DCE, `.replace` hack, runtime `-fPIC`, `@gpu` decision, MIR verifier wiring, `const` decision, diagnostics consolidation, CHANGELOG honesty | 1–2 days |
| **v4.28.0** | Concurrency + v3.47.0 carry-forwards | New races (signal set/recompute, agent inbox MPSC, type registry), matmul shape NULL check + dim validation (27 versions overdue), GPU temp file race, Windows GPU init race propagation, `main.ll` version string regression | 1 day |
| **v4.29.0** | Build infrastructure + test honesty | Orphaned `mapanare_db.c` + `mapanare_html.c` (1,942 lines), `extern "Python" fn` decision (79 silent xfails), DWARF decision (38 silent skips), `--no-check` warning, `verify_fixed_point.sh` teeth, `stage3.ll` zero-byte stale file, NotImplementedError CI gate | 1 day |
| **v4.30.0** | Codegen + optimizer + emitter carry-forwards | `await` decision, `_emit_agent_wrap` no-op stub, optimizer non-convergence ICE, `stream_fusion` placement, self-hosted DCE BFS + `clean_phis_in_block`, six 7-cycle emitter carry-forwards (i64*, void()*, list bitcast, nsw flags, `__mn_map_new` arity, noalias/willreturn) | 1–2 days |
| **v4.31.0** | Documentation truth + process hardening | SPEC sync (26 versions stale), Spanish README sync, SPEC line 121 `di` label, bilingual keywords table, User-Agent bump, dead code removal (`__mn_list_oob_buf`), CI hollow-feature gate, CHANGELOG honesty script, docs-vs-code drift detector, carry-forward queue file, **next 7-reviewer panel re-run** | 1 day |

**The recovery arc terminated at v4.31.0** with aggregate 9.343/10, 5 PASS + 2 PASS WITH NOTES, zero NEEDS WORK.

| **v4.32.0** | Arc-end panel closure | Close 9 HIGH/MEDIUM items from v4.31.0 panel: list OOB abort, self-hosted emitter parity, drop-glue extraction, mnstr_to_cstr consolidation, signal recompute lock, bind.py unwrap, CI gate split, stale artifact cleanup, ledger schema update. Zero new features. | 1 day |

Post-recovery releases follow the **45-version plan** organized into **9 thematic arcs** of 5 releases each, with a scheduled 7-reviewer panel at the end of every arc. Full details in `docs/roadmap/v4/POST_RECOVERY_ROADMAP.md`.

### Post-Recovery Arcs (v4.33.0 → v4.76.0)

| Arc | Versions | Theme | Panel | Key deliverable |
|-----|----------|-------|-------|-----------------|
| **1** | v4.33.0 – v4.36.0 | Error handling + Pattern matching | v4.36.0 | `?` operator, decision-tree match, guards + or-patterns |
| **2** | v4.37.0 – v4.41.0 | LSP maturity | v4.41.0 | Go-to-def, find-refs, rename, completion, VS Code extension |
| **3** | v4.42.0 – v4.46.0 | Tensor completeness | v4.46.0 | Tensor literals, indexing, broadcasting, reductions + slicing |
| **4** | v4.47.0 – v4.51.0 | Stdlib AI/LLM | v4.51.0 | Unified LLM interface, structured output, embeddings + RAG |
| **5** | v4.52.0 – v4.56.0 | Compiler debt drain | v4.56.0 | Self-hosted semantic wiring (A7), UNRESOLVED/ERROR split (A8), `const` Path A |
| **6** | v4.57.0 – v4.61.0 | Deprecation + deletion | v4.61.0 | Python emitter deletion, llvmlite JIT deletion, dead code final pass |
| **7** | v4.62.0 – v4.66.0 | DWARF debug info | v4.66.0 | `DICompileUnit`, `DISubprogram`, line metadata, `llvm.dbg.declare`/`value` |
| **8** | v4.67.0 – v4.71.0 | Coroutine foundation | v4.71.0 | Design doc, `async`/`await` grammar + AST, semantic analysis, MIR suspension |
| **9** | v4.72.0 – v4.76.0 | Coroutine completion | v4.76.0 | Suspend/resume/destroy, runtime scheduler, `for await`, end-to-end demos |

Every arc follows: **3–4 feature releases → 1 panel release**. Each panel release ships minimal new work so the panel has a stable target. The lead can tag v5.0.0 at any point — the plan doesn't change.

The historical "What's Next" sequence (v4.1.0–v4.7.0) below is preserved as
the original refactor plan record. All items have been completed but the panel
found that some were claimed working without being wired through to runtime.

---

### v4.1.0 — Ecosystem Infrastructure (DONE)

The compiler is done. Now make the ecosystem work like a real language toolchain.

| Phase | What | Status |
|-------|------|--------|
| **Phase 1** | Package registry persistence (PostgreSQL connection pool + retry), web login (GitHub OAuth + cookies), account dashboard, download page | **Done** |
| **Phase 2** | Install script `--version` flag, native compiler distribution in CI (`mnc` binaries alongside PyInstaller), cross-platform seed binaries | Planned |
| **Phase 3** | `mapanare-up` version manager (pyenv-style: `.mapanare-version`, shim-based dispatch, `install`/`list`/`default`/`use`/`update`) | Planned |
| **Phase 4** | CI release pipeline: native binary builds for Linux/macOS/Windows, SHA256 checksums, staged releases (beta/stable channels) | Planned |
| **Phase 5** | Blog tutorials (transpile Python, GPU compute), new doc pages (package manager, version manager), v4.0.0 docs audit | Planned |

### v4.2.0 — "Clean House" (Emitter Consolidation)

**Goal:** One emitter, one pipeline, zero dead code. Reduce the surface area
before fixing anything.

**Why this is first:** You can't fix drop glue properly when you have 3
competing LLVM emitters with different cleanup strategies. You can't audit
memory ownership when 5,000 lines of dead code obscure the real pipeline.

| Task | What | Why |
|------|------|-----|
| Delete `emit_llvm_mir.py` | Remove deprecated llvmlite MIR emitter (~5,000 lines) | Worse drop glue than text emitter (missing list/map/signal/stream cleanup), carries 36 `_coerce_arg` call sites, requires llvmlite C++ dependency |
| Delete `emit_llvm.py` | Remove legacy AST-based emitter (~2,883 lines) | Doesn't compare return pointers in drop glue (use-after-free risk), only reached via `--no-mir` flag |
| Port `_compile_multi_module_llvm` | Move `cli.py:242` from AST emitter to MIR text pipeline | Last code path forcing old emitter to exist |
| Delete `emit_python.py` | Migrate tests to `PythonMIREmitter`, remove AST-based Python emitter (~47KB) | Parallel implementation maintained for no reason |
| Remove `--no-mir` and `--emitter llvmlite` | Clean up CLI flags | Dead options that lead to worse codegen |
| Delete `emit_c.mn` | 770 lines referencing non-existent MIR types | Cannot compile against current MIR — uses `MIRTypeInfo`, `MIRBlock`, integer opcodes that don't exist |
| Remove `_coerce_arg` | With only one emitter, fix the MIR-to-LLVM type mapping properly | Eliminates 36 call sites of raw `alloca+store+load` memory reinterpretation that can silently miscompile structs |

**Deprecation history — why these emitters failed:**

| Emitter | Born | Peak | Why abandoned |
|---------|------|------|--------------|
| `emit_llvm.py` (AST, llvmlite) | v0.1.0 | v0.8.0 | AST-based emission couldn't handle MIR optimizations; llvmlite's C++ dependency complicated builds; drop glue frees ALL strings without return-pointer comparison (use-after-free) |
| `emit_llvm_mir.py` (MIR, llvmlite) | v0.6.0 | v1.0.0 | Inherited llvmlite dependency; `_coerce_arg` grew to 130 lines with 36 call sites doing raw memory reinterpretation; missing drop glue for lists/maps/signals/streams; global mutable state (`_llvm_types_initialized`, `_target_ptr_size`) broke cross-compilation |
| `emit_llvm_text.py` (MIR, pure text) | v3.0.0 | **current** | Pure Python, no C++ deps; comprehensive drop glue (5 categories); return-pointer comparison; the only emitter that handles all types correctly |
| `emit_c.mn` (MIR, C output) | v3.0.0 | v3.0.0 | Written for an older MIR representation; references `MIRTypeInfo`, `MIRBlock`, integer opcodes — none of which exist in current `mir.mn`; only handles 17 of 30 instruction kinds; never worked after MIR was redesigned |

**Result:** ~8,500 fewer lines. One LLVM emitter. One Python emitter. No `_coerce_arg`.

### v4.3.0 — "Drop Glue Done Right" (Memory Correctness)

**Goal:** Functions returning structs stop leaking. String/list/map/signal/stream
lifetimes are correct.

**The core problem:** `emit_llvm_text.py:966` has `skip_struct_ret` which
disables ALL drop glue when a function returns a struct/enum type. This is a
deliberate leak to avoid use-after-free — if a returned string is also in the
cleanup list, freeing it would destroy the return value. The fix requires
tracking which values escape into the return value.

| Task | What | Why |
|------|------|-----|
| Fix `skip_struct_ret` | Track which values are moved into the return struct; skip only those, free the rest | Every struct-returning function currently leaks ALL temporaries (strings, closures, lists, maps, signals, streams) |
| Return-value escape analysis | Walk the return value to identify all pointers that escape (nested struct fields, not just top-level) | Current pointer comparison is shallow — misses values nested 2+ levels deep in struct fields |
| Free string intermediates | Track concat/interp temporaries and free after use | Every string concat in a loop leaks the intermediate allocation |
| Free map iterators | Emit `__mn_map_iter_free` after for-in-map loops | All map iterators leak — no emitter calls the free function |
| Free stream `user_data` | Add closure-env free to `__mn_stream_free` / `__mn_stream_free_chain` | All stream closure environments leak on stream cleanup |
| Call `__mn_intern_destroy` at exit | Add to program epilogue in `mnc_main.c` | Intern table (static hash table of all interned strings) never destroyed |
| Free agent struct | Add `free(agent)` after `mapanare_agent_destroy` in emitter epilogue | `destroy` cleans internals (ring buffers, semaphores) but never calls `free(agent)` |
| Add `mapanare_registry_destroy` | Clean up agent registry mutex at program exit | Registry `mapanare_mutex_t` currently leaks |

**Result:** No more "deliberate leaks." Memory ownership is clear for all 7 allocation categories.

### v4.4.0 — "Thread Safety" (Concurrency Hardening)

**Goal:** Concurrent agents don't corrupt shared state.

| Task | What | Why |
|------|------|-----|
| Signal free under lock | Acquire `mn_signal_lock` in `__mn_signal_free` before touching subscriber/dependency arrays | Currently races with propagation — another thread iterates a subscriber snapshot while free destroys the array |
| Atomic profiling counters | Make `mn_alloc_count`, `mn_alloc_bytes`, `mn_alloc_live`, `mn_alloc_peak`, `cow_shares`, `cow_fallbacks`, `cow_detaches` use `__atomic_*` | Currently plain `int64_t` — concurrent allocations race on these counters |
| Thread-safe arenas or per-agent guarantee | Either add locking to `mn_arena_alloc` or guarantee arenas are never shared between agents | Agent arenas could race if two agents share a runtime arena |
| Agent arena tied to agent lifecycle | `mapanare_agent_destroy` should call `mn_agent_arena_destroy` automatically | Currently separate systems — emitter must emit calls to both, and can forget |
| COW struct-copy safety | Audit all paths where `MnList` is copied by value (assignment, function arg, struct field copy) without calling `__mn_list_clone` | The known COW corruption in nested lists (workaround in `mnc_all.mn:6944`) likely comes from this |
| Message ownership on agent death | Define policy and implement: free in-flight messages when agent dies, or transfer to supervisor | Messages in ring buffer are permanently leaked if agent crashes |
| Agent restart cleanup | Ensure restarted agents properly destroy old state before reinitializing | `mapanare_agent_set_restart_policy` exists but restart path doesn't clean up old state |

**Result:** Agents, signals, and arenas are safe under concurrency.

### v4.5.0 — "Type System Tightening" (Silent Errors Become Loud)

**Goal:** The compiler tells you when something is wrong instead of producing
bad code.

| Task | What | Why |
|------|------|-----|
| Split UNKNOWN into UNRESOLVED + ERROR | `UNRESOLVED` = inference pending (will resolve). `ERROR` = inference failed (emit diagnostic). | Currently UNKNOWN is both — failed inference silently compiles because UNKNOWN matches everything (~85 locations in `semantic.py`) |
| Post-analysis validation pass | After semantic analysis, flag any remaining UNRESOLVED types as errors | Currently unresolved types flow downstream through MIR lowering and LLVM emission, crashing at runtime |
| Wire self-hosted semantic analysis | In `main.mn compile()`, call `semantic.mn` between parse and lower | Currently 1,900 lines of `semantic.mn` are imported but `compile()` skips straight from parse to lower — zero type checking in the self-hosted compiler |
| Wire self-hosted MIR verifier | Call `verify_module()` (defined in `lower.mn:3620-3717`) in `compile()` before emission | Checks: empty functions, unterminated blocks, terminators in middle, phi placement — currently all skipped |
| Emit diagnostics for unknown instructions | Replace `return st` (silent drop) with error/warning in self-hosted emitter | Currently unknown instruction kinds are silently ignored at `emit_mir_by_kind` fallthrough |
| Emit diagnostics for unknown tokens | Replace "skip unknown token" in `parser.mn` with error accumulation | Currently malformed input is silently swallowed |

**Result:** The compiler rejects bad code at compile time instead of emitting bad LLVM IR.

### v4.6.0 — "Self-Hosted Quality" (Clean Compiler)

**Goal:** The self-hosted compiler is honest — no workarounds, no manual tables,
no string-typed enums.

| Task | What | Why |
|------|------|-----|
| Replace `hardcoded_field_index` | Auto-derive field indices from struct definitions at compile time | ~160 lines of manual struct→index mapping in `emit_llvm.mn:1095` that silently produces wrong code if structs change |
| Replace MIRType string kind tags | Use an enum variant instead of `t.kind == "int"` string comparisons throughout `mir.mn` and all consumers | Every string comparison is a potential typo bug — one mismatched string silently breaks type checking |
| Fix PHI zeroinitializer workaround | Fix the root cause in stage2 codegen that produces zeroinitializer PHI nodes | Currently `emit_llvm.mn:3205` uses explicit string variables to "avoid if-expression (PHI zeroinitializer bug)" |
| Fix substr off-by-one | Fix the compiled substr that has off-by-one errors | Currently `emit_llvm.mn:2588` uses `.contains() + .replace()` instead of `.substr()` as a workaround |
| Fix ABI mismatch with C runtime | Fix range constructor to match C runtime's actual return convention | Currently `emit_llvm.mn:2513` inlines range construction to "avoid ABI mismatch" |
| Replace 2 typed pointers | Replace `i64*` (tensor alloc) and `void ()*` (function constants) with opaque `ptr` | Required for LLVM 17+ compatibility, only 2 remaining |

**Result:** Zero self-hosting workarounds. The compiler's own output is correct enough to not need patches.

### v4.7.0 — "Optimizer + Performance" (Better Code)

**Goal:** Better code generation, measurable speedups.

| Task | What | Why |
|------|------|-----|
| Unified fixpoint loop | Merge O1 (constant folding/propagation) and O2 (copy propagation, DCE, branch simplification) into one convergence loop | Currently O2 creates opportunities for O1 that are missed because O1 already finished |
| Max-iteration warning | Emit diagnostic if optimizer hits 10-iteration cap without converging | Currently silent — suboptimal code with no indication |
| Constant propagation in self-hosted | Add basic constant folding to the self-hosted MIR pipeline | Currently zero optimization in mnc — everything deferred to LLVM's passes |
| String allocation reduction | Pool `str_from_bool`/`str_from_int` for common values, avoid per-call `malloc` | Currently every `str(true)`, `str(42)` allocates a fresh heap buffer |
| COW for strings | Add refcount-based copy-on-write to strings (like lists already have) | Currently every string copy/concat allocates fresh — significant pressure in string-heavy programs |

**Result:** Faster compilation, smaller binaries, fewer runtime allocations.

### v4.8.0+ — Language Evolution (After Refactor)

**No new features until v4.7.0 is complete.** These are the targets once the
foundation is solid:

**Near-term (v4.8.0-v4.9.0):**

| Feature | Description |
|---------|-------------|
| **Compile-time tensor shapes** | `Tensor<Float>[M, K] @ Tensor<Float>[K, N]` — shape mismatch is a compile error, not a GPU crash |
| `const` keyword | Compile-time constants in grammar and semantic checker, enables static tensor dimensions |
| `@gpu` auto-kernel extraction | Wire decorator recognition -> kernel extraction -> PTX/SPIR-V emission automatically |
| Reactive async | Tie async/await natively into Mapanare Streams with cooperative scheduling |

**Growth features (v4.10.0+):**

| Feature | Description |
|---------|-------------|
| **Auto-generated FFI bindings** | `mapanare build --lib --bindings` generates `.pyi`, `.d.ts`, Go wrappers from exported functions |
| Distributed agent routing | Actor-model routing for `@Agent` across processes/machines |
| JIT hot-module replacement | Swap compiled modules at runtime without restart |
| LSP improvements | Better autocomplete, hover docs, find-all-references |

**v5.0+ vision:** Distributed actor-model routing, auto-generated Python/TS/Go
FFI bindings, JIT hot-module replacement. See era READMEs for full context.

---

## Eras

The roadmap is organized into 5 major eras. Each era folder contains a README
with goals, features, and lessons learned, plus per-version PLAN.md and
SUMMARY.md files.

| Era | Theme | Versions | Key Milestone |
|-----|-------|----------|---------------|
| [**v0**](v0/) | Foundation & Bootstrap | v0.1.0 — v0.9.0 | Self-hosted compiler boots, MIR pipeline, native stdlib |
| [**v1**](v1/) | Stability & Production | v1.0.0 — v1.3.0 | Language frozen (SPEC 1.0), AI/data/web stdlib |
| [**v2**](v2/) | Platform Expansion | v2.0.0 — v2.2.0 | GPU, WASM, mobile, self-compilation progress |
| [**v3**](v3/) | Syntax & Self-Hosted Maturity | v3.0.0 — v3.47.0 | Radical syntax reform, fixed-point, transpilers, production gate |
| [**v4**](v4/) | Production, Refactor & Evolution | v4.0.0+ | Production release, architectural refactor (v4.2-v4.7), then language evolution |

---

## Release History

### v0 — Foundation & Bootstrap

| Version | Theme | Highlights |
|---------|-------|------------|
| **v0.1.0** | Foundation | Bootstrap compiler, Lark parser, semantic checker, Python + LLVM emitters, runtime, LSP, 1,400+ tests |
| **v0.2.0** | Self-Hosting | LLVM string/list codegen, C runtime, self-hosted compiler (5,800+ lines .mn) |
| **v0.3.0** | Depth Over Breadth | Traits, module resolution, LLVM agent codegen, arena memory, TypeKind enum, 1,960+ tests |
| **v0.3.1** | Release Polish | Dynamic versioning from VERSION file |
| **v0.4.0** | Ready for the World | Scope cleanup, C runtime hardening, structured diagnostics, C FFI, self-hosted verification |
| **v0.5.0** | The Ecosystem | String interpolation, linter, Python interop, WASM playground, package registry, 2,200+ tests |
| **v0.6.0** | Compiler Infrastructure | MIR pipeline (SSA IR, lowering, optimizer), bootstrap frozen, 2,500+ tests |
| **v0.7.0** | Self-Standing | Self-hosted MIR lowering, test runner, agent observability, DWARF debug info, 2,983 tests |
| **v0.8.0** | Native Parity | LLVM backend parity, complete string methods, C runtime expansion (TCP, TLS, file I/O), 3,020 tests |
| **v0.9.0** | Connected | Native stdlib in .mn (JSON, CSV, HTTP, crypto, regex), cross-module LLVM, 3,400+ tests |

### v1 — Stability & Production

| Version | Theme | Highlights |
|---------|-------|------------|
| **v1.0.0** | Stable | Language freeze (SPEC 1.0 Final), emitter hardening, formal memory model, 15/15 golden, 3,600+ tests |
| **v1.0.1–v1.0.11** | Patch Series | 11 patches addressing 34 code review issues: type soundness, memory, drop glue, self-hosted fixes, ASan/TSan clean |
| **v1.1.0** | AI Native | LLM drivers (OpenAI, Anthropic, local), embeddings, RAG pipeline |
| **v1.2.0** | Data & Storage | Dato engine, database drivers (SQLite, PostgreSQL, Redis, KV), TOML/YAML, filesystem stdlib |
| **v1.3.0** | Web & Security | Web crawler, vulnerability scanner, HTTP fuzzer, HTTP server toolkit |

### v2 — Platform Expansion

| Version | Theme | Highlights |
|---------|-------|------------|
| **v2.0.0** | Beyond the Machine | WASM backend, GPU compute (CUDA + Vulkan), mobile targets (iOS, Android), Python deprecated, 4,465+ tests |
| **v2.0.1** | Trust Restoration | Fix 40 review issues: WASM correctness, GPU security, toolchain honesty |
| **v2.1.0** | Self-Compilation | Stage2 IR validates, 8 root causes fixed, mnc-stage2 reaches lowerer |
| **v2.2.0** | Stage2 Debugging | Valgrind crash diagnostics, struct field mapping, PHI type recovery, mnc-stage2 binary (3.8 MB) |

### v3 — Syntax & Self-Hosted Maturity

| Version | Theme | Highlights |
|---------|-------|------------|
| **v3.0.0** | La Culebra Se Muerde La Cola | C emit backend, bilingual keywords, indentation syntax, tipo/modo, @Agent |
| **v3.0.1–v3.0.3** | Bootstrap Fixes | mnc-stage1 runs, 25/25 golden, PHI type recovery |
| **v3.1.0–v3.2.0** | Native IO + Seed | File I/O, string escapes, seed binary updated |
| **v3.3.0** | **Fixed Point** | stage3 == stage4, two-stage bootstrap from seed, no Python required |
| **v3.4.0–v3.7.0** | Language Completeness | Module imports, WASM stackifier, type system, cross-module imports |
| **v3.8.0–v3.9.1** | Generics + Impl | Monomorphization, trait dispatch, generic impl blocks, 31/31 golden |
| **v3.10.0–v3.23.0** | Semantic Maturity | Error messages, memory safety, concurrency fixes, `any` type, optimizer convergence |
| **v3.24.0–v3.31.0** | Multi-Language Transpilation | Python, PHP, TypeScript, Go transpilers + shared framework |
| **v3.32.0–v3.36.0** | Review Hardening | Code review fixes, dead code removal, performance optimization |
| **v3.37.0–v3.47.0** | Production Gate | IO foundation, network, agents, examples, package manager, GPU — all prerequisites for v4.0.0 |

### v4 — Production, Refactor & Evolution

| Version | Theme | Highlights |
|---------|-------|------------|
| **v4.0.0** | Mapanare | Build real programs. 15,000+ lines self-hosted, 40/40 golden, 4,845+ tests, 9.79/10 review |
| **v4.0.0** | Bug fixes | MIR constant propagation fix (loop back-edges), transpiler return type inference, `cmd_build` obj path collision |
| **v4.1.0** | Ecosystem | Package registry persistence, web login, dashboard, download page, version manager, native CI binaries |
| **v4.2.0** | Clean House | Delete 3 dead emitters (~8,500 lines), remove `_coerce_arg` (36 call sites), consolidate to one pipeline |
| **v4.3.0** | Drop Glue | Fix `skip_struct_ret` leak, return-value escape analysis, free string/map/stream temporaries |
| **v4.4.0** | Thread Safety | Signal free under lock, atomic counters, COW struct-copy audit, agent lifecycle |
| **v4.5.0** | Type System | Split UNKNOWN into UNRESOLVED/ERROR, wire self-hosted semantic analysis + MIR verifier |
| **v4.6.0** | Self-Hosted Quality | Replace hardcoded field tables, MIRType string->enum, fix self-hosting workarounds |
| **v4.7.0** | Optimizer | Unified fixpoint loop, constant propagation in self-hosted, COW strings, string pooling |
| **v4.7.1** | Verify | WSL rebuild verified: 40/40 golden, 11/11 stage2 |
| **v4.8.0–v4.13.0** | Deep Fixes | Workaround removal, semantic safety, drop glue complete, foundation gate |
| **v4.14.0–v4.17.0** | Compiler Maturity | Break fix, module-level let, optimizer complete, fixed-point bootstrap |
| **v4.18.0** | Tensor Shapes (claim) | `const` keyword (parser alias for module-level let; reverted v4.27.0); `Tensor<Float>[3,3]` shape annotations (the grammar form — the `Tensor<Float, [3,3]>` form the original entry claimed never parsed); compile-time mismatch errors (claimed but only delivered for element-type mismatches, not shape) |
| **v4.19.0** | Reactive Async | async/await wired into Streams, backpressure ring buffers |
| **v4.20.0** | FFI Bindings | `mapanare bind --lang python\|ts\|go` generates bindings from .mn signatures |
| **v4.21.0** | Optimizer Hardening | Constant folding correctness on loop back-edges |
| **v4.22.0** | Dead Block Elimination | Fixed-point BFS, PHI-safe removal, SwitchCase fix |
| **v4.23.0** | MIRType Int Tags | Zero string-based type comparisons, 110+ sites migrated |
| **v4.24.0** | async/await Wired | Parser + lowerer + emitter in both pipelines, 46th golden test |
| **v4.25.0** | FFI End-to-End | .mn → .so → Python ctypes calls compiled code; tensor shape checking E2E |
| **v4.26.0** | `const` Keyword (claim) | Roadmap consolidation; **panel verdict NEEDS WORK** — `const` shipped as parser alias for ModuleLetDef without immutability or shape resolution; documents 6 hollow features across v4.18.0–v4.26.0 |
| **v4.27.0** | Honesty Recovery (CRITICAL) | Closed 8 CRITICAL items from v4.26.0 panel. FFI ctypes wrappers populate `argtypes`/`restype` from MIRType. Runtime archive built `-fPIC`. `MIRVerifier().verify_module()` wired into `_compile_to_llvm_ir` + `compile_multi_module_mir` + self-hosted `compile()`. `const` keyword reverted (Path B). `@gpu`/`@cuda`/`@vulkan` decorators removed (Path B). `semantic.py SemanticError` replaced by `diagnostics.py Diagnostic`. `define internal` `.replace()` sledgehammer deleted; exported set threaded through the emitter. CHANGELOG v4.26.0 entry corrected. |
| **v4.28.0** (planned) | Concurrency + Carry-forwards | Signal value mutation under lock; agent inbox MPSC-safe; type registry locked; matmul shape NULL check + dimension validation (27 versions overdue); `main.ll` version string sourced from `VERSION` |
| **v4.29.0** (planned) | Build Infrastructure + Test Honesty | `mapanare_db.c` + `mapanare_html.c` linked; Makefile build-rt enumeration; `extern "Python" fn` decision; `verify_fixed_point.sh` propagates exit; CI hollow-feature gate (`raise NotImplementedError` = 0) |
| **v4.30.0** (planned) | Codegen + Emitter Carry-Forwards | `await` decision; agent dispatch wired; optimizer non-convergence ICE; `stream_fusion` in fixpoint; self-hosted DCE BFS + `clean_phis_in_block`; six 7-cycle emitter items closed |
| **v4.31.0** (planned) | Documentation Truth + Process | SPEC sync (26 versions stale); Spanish README sync; User-Agent bump; dead code sweep; CHANGELOG honesty + docs-drift CI scripts; **next 7-reviewer panel runs and certifies recovery arc complete** |
| **v4.32.0** | Arc-End Panel Closure | Close 9 HIGH/MEDIUM from v4.31.0 panel; zero new features |
| **v4.33.0–v4.36.0** (planned) | Arc 1: Error Handling + Pattern Matching | `?` operator, decision-tree match rewrite, guards + or-patterns. Panel at v4.36.0 |
| **v4.37.0–v4.41.0** (planned) | Arc 2: LSP Maturity | Go-to-def, find-refs, rename, completion, VS Code extension. Panel at v4.41.0 |
| **v4.42.0–v4.46.0** (planned) | Arc 3: Tensor Completeness | Tensor literals, indexing, broadcasting, reductions + slicing. Panel at v4.46.0 |
| **v4.47.0–v4.51.0** (planned) | Arc 4: Stdlib AI/LLM | Unified LLM interface, structured output, embeddings + RAG. Panel at v4.51.0 |
| **v4.52.0–v4.56.0** (planned) | Arc 5: Compiler Debt Drain | Self-hosted semantic wiring, UNRESOLVED/ERROR split, `const` Path A. Panel at v4.56.0 |
| **v4.57.0–v4.61.0** (planned) | Arc 6: Deprecation + Deletion | Python emitter, llvmlite JIT, dead code final pass. Panel at v4.61.0 |
| **v4.62.0–v4.66.0** (planned) | Arc 7: DWARF Debug Info | `DICompileUnit`, `DISubprogram`, line metadata, `llvm.dbg.declare`. Panel at v4.66.0 |
| **v4.67.0–v4.71.0** (planned) | Arc 8: Coroutine Foundation | Design doc, `async`/`await` grammar + AST, semantic, MIR suspension. Panel at v4.71.0 |
| **v4.72.0–v4.76.0** (planned) | Arc 9: Coroutine Completion | Suspend/resume/destroy, scheduler, `for await`, end-to-end demos. Panel at v4.76.0 |

---

## What Works Today

- **Full compiler pipeline** — Lexer, parser, semantic checker, MIR lowering, optimizer (O0-O3), code emitter
- **Two compilation targets** — LLVM IR via text emitter (production), WebAssembly (WAT/WASM). Python transpiler (deprecated, test-only)
- **Self-hosted compiler** — 15,000+ lines of .mn across 11 modules, fixed-point verified
- **GPU compute** — CUDA + Vulkan via dlopen, @gpu/@cuda/@vulkan annotations
- **WebAssembly** — MIR-to-WAT, WASI support, JS bridge, wasm-ld multi-module linking
- **AI stdlib** — LLM drivers, embeddings, RAG pipelines
- **Data** — Dato DataFrames, SQLite/PostgreSQL/Redis drivers, TOML/YAML encoding
- **Web** — HTTP server toolkit, web crawler, vulnerability scanner, HTTP fuzzer
- **Multi-language transpilation** — Python, PHP, TypeScript, Go -> Mapanare (29-68x speedup over Python)
- **Package manager** — `mapanare install` with dependency resolution, registry at mapanare.dev/packages
- **Package registry** — PostgreSQL-backed with GitHub OAuth login, web dashboard, download API
- **Developer tools** — CLI, LSP, VS Code extension, formatter, linter, test runner, doc generator
- **Website** — mapanare.dev with docs, benchmarks, blog, download page, package registry
- **Cross-compilation** — 9 targets (Linux, macOS, Windows, WASM, iOS, Android)

### Backend Feature Status

| Feature | LLVM | WASM | Python (deprecated) |
|---------|:----:|:----:|:-------------------:|
| Functions, closures, lambdas | Yes | Yes | Yes |
| Structs, enums, pattern matching | Yes | Yes | Yes |
| Control flow (if/else, for, while) | Yes | Yes | Yes |
| Type inference, generics | Yes | Yes | Yes |
| Result/Option | Yes | Yes | Yes |
| Builtins (print, str, int, float, len) | Yes | Yes | Yes |
| Lists, Maps/Dicts | Yes | Yes | Yes |
| String methods | Yes | Yes | Yes |
| Traits | Yes | Yes | Yes |
| Module imports | Yes | Yes | Yes |
| Agents, Signals, Streams, Pipes | Yes | Yes | Yes |
| GPU compute | Yes | No | No |
| Standard library (25+ modules) | Yes | Partial | Partial |

### Performance (LLVM native vs Python)

| Workload | Speedup |
|----------|---------|
| Fibonacci (recursive) | **26-41x faster** |
| Stream pipeline (1M items) | **62.8x faster** |
| Matrix multiply (100x100) | **22.9x faster** |
| Python transpile: Collatz (1M) | **68x faster** |
| Python transpile: Primes (500K) | **29x faster** |
| Agent message passing (10K) | On par |

---

## Known Issues (Architectural Audit, 2026-04-08)

A deep audit after v4.0.0 revealed issues that accumulated across 70+ versions.
These are documented here for transparency and tracked in the v4.2.0-v4.7.0
refactor roadmap above.

### Critical (actively causing bugs)

| # | Issue | Location | Fix Version |
|---|-------|----------|-------------|
| 1 | `skip_struct_ret` disables ALL drop glue for struct-returning functions (deliberate leak to avoid use-after-free) | `emit_llvm_text.py:966` | v4.3.0 |
| 2 | `__mn_signal_free` races with signal propagation (frees arrays without holding signal mutex) | `mapanare_core.c:2052` | v4.4.0 |
| 3 | `mapanare_agent_destroy` does not free the agent struct itself (every spawn leaks) | `mapanare_runtime.c:675` | v4.3.0 |
| 4 | UNKNOWN type matches everything — failed inference silently compiles (~85 locations) | `semantic.py` | v4.5.0 |
| 5 | Known COW corruption in nested list handling (worked around, not fixed) | `mnc_all.mn:6944` | v4.4.0 |
| 6 | `_coerce_arg` raw memory reinterpretation (36 call sites in deprecated emitter) | `emit_llvm_mir.py:201` | v4.2.0 |

### High (blocks progress)

| # | Issue | Scale | Fix Version |
|---|-------|-------|-------------|
| 7 | 3 LLVM emitters, only 1 is default (~5,000 lines dead weight) | 8,800 lines | v4.2.0 |
| 8 | Self-hosted semantic analysis imported but never called | 1,900 lines dead | v4.5.0 |
| 9 | `emit_c.mn` references non-existent MIR types — broken dead code | 770 lines | v4.2.0 |
| 10 | Self-hosted MIR verifier defined but never invoked | `lower.mn:3620` | v4.5.0 |
| 11 | String intern table never destroyed (`__mn_intern_destroy` exists, never called) | All programs | v4.3.0 |
| 12 | Stream `user_data` (closure env) not freed on stream cleanup | All streams | v4.3.0 |

### Medium (quality / correctness)

| # | Issue | Fix Version |
|---|-------|-------------|
| 13 | Memory profiling counters (`mn_alloc_count` etc.) are plain `int64_t`, no atomics | v4.4.0 |
| 14 | Arena allocator not thread-safe (fine for per-function, dangerous for agent arenas) | v4.4.0 |
| 15 | MIR optimizer O1/O2 not in single fixpoint loop (missed optimizations) | v4.7.0 |
| 16 | Hardcoded struct field tables in self-hosted emitter (~160 lines manual mapping) | v4.6.0 |
| 17 | MIRType uses string-based kind tags (`t.kind == "int"`) instead of enum | v4.6.0 |
| 18 | Map iterators never freed by any emitter | v4.3.0 |
| 19 | Self-hosted emitter silently drops unknown instruction kinds | v4.5.0 |
| 20 | Self-hosted parser skips unknown tokens without error | v4.5.0 |
| 21 | 2 typed pointers remaining in self-hosted emitter (`i64*`, `void ()*`) | v4.6.0 |

### Deprecated emitter history

Three LLVM emitters were built over the project's lifetime. Understanding why
each was abandoned prevents repeating the same mistakes.

| Emitter | File | Era | Lines | Why it failed |
|---------|------|-----|-------|--------------|
| AST + llvmlite | `emit_llvm.py` | v0.1.0-v0.8.0 | 2,883 | AST-based emission couldn't leverage MIR optimizations. Drop glue frees ALL strings without comparing to return value (use-after-free). llvmlite C++ dependency complicated builds and cross-compilation. |
| MIR + llvmlite | `emit_llvm_mir.py` | v0.6.0-v1.0.0 | ~5,000 | Inherited llvmlite C++ dependency. `_coerce_arg` grew to 130 lines / 36 call sites doing raw memory reinterpretation (`alloca+store+load`) for MIR/LLVM type mismatches — silent miscompilation risk. Missing drop glue for lists, maps, signals, streams. Global mutable state (`_llvm_types_initialized`, `_target_ptr_size`) broke cross-compilation scenarios. |
| MIR + text (current) | `emit_llvm_text.py` | v3.0.0-now | ~3,800 | **Winner.** Pure Python, no C++ deps. Comprehensive drop glue (5 categories). Return-pointer comparison to avoid use-after-free. Only remaining issue: `skip_struct_ret` bail-out (v4.3.0 fix). |
| C output (.mn) | `emit_c.mn` | v3.0.0 | 770 | Written for an older MIR representation. References `MIRTypeInfo`, `MIRBlock`, integer opcodes — none exist in current `mir.mn`. Only handles 17/30 instruction kinds. Never worked after MIR was redesigned. |

---

## Test Growth

| Era | Tests | Key Quality Metric |
|-----|-------|--------------------|
| v0.1.0 | 1,400+ | Bootstrap works |
| v0.6.0 | 2,500+ | MIR pipeline validated |
| v0.9.0 | 3,400+ | Native stdlib compiles |
| v1.0.0 | 3,600+ | ASan/TSan clean (52/52) |
| v2.0.0 | 4,465+ | WASM + GPU + mobile CI |
| v4.0.0 | 4,845+ | 40/40 golden, 9.79/10 review |

---

## Directory Structure

```
docs/roadmap/
  ROADMAP.md          <- This file (index)
  v0/                 <- Foundation & Bootstrap (v0.1.0 - v0.9.0)
    README.md         <- Era summary: goals, features, lessons learned
    v0.1.0/PLAN.md    <- Detailed version plan
    v0.1.0/SUMMARY.md <- Post-release summary
    ...
  v1/                 <- Stability & Production (v1.0.0 - v1.3.0)
    README.md
    v1.0.0/PLAN.md
    ...
  v2/                 <- Platform Expansion (v2.0.0 - v2.2.0)
    README.md
    v2.0.0/PLAN.md
    ...
  v3/                 <- Syntax & Self-Hosted Maturity (v3.0.0 - v3.47.0)
    README.md
    v3.0.0/PLAN.md
    ...
  v4/                 <- Production, Refactor & Evolution (v4.0.0+)
    README.md
    v4.0.0/PLAN.md
    v4.1.0/PLAN.md
    v4.2.0/PLAN.md    <- Clean House (emitter consolidation)
    v4.3.0/PLAN.md    <- Drop Glue (memory correctness)
    ...through v4.7.0
```

Each version folder contains:
- **PLAN.md** — execution plan (phases, tasks, exit criteria)
- **SUMMARY.md** — post-release retrospective (where available)
- **PROMPT.md / prompt.md** — context prompt used during development (where available)
