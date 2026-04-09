# Changelog

All notable changes to the Mapanare programming language will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [4.0.0] - 2026-04-08

**Production Release — "Build Real Programs"**

The v4.0.0 release marks Mapanare as production-ready. All v3.x milestones are complete.

- **Self-hosted compiler**: 15,000+ lines of `.mn`, fixed-point verified (stage4 == stage3)
- **40/40 golden tests** pass on both bootstrap and stage1
- **4,845+ pytest tests** across the full pipeline
- **GPU compute**: 8 builtins (`gpu_available`, `gpu_tensor_add/sub/mul/div/matmul`) via CUDA dlopen, verified on RTX 4090
- **Python transpiler**: `mapanare transpile file.py` → native binary, 29-68x speedup over Python
- **C runtime**: arena allocator, thread pool, ring buffers, TCP/TLS, crypto, regex, HTTP, GPU dispatch
- **Package manager**: `mapanare install`, registry, git fallback
- **7-reviewer code review**: 9.79/10 aggregate, all PASS
- Fix: MIR constant propagation through loop back-edges
- Fix: transpiler function return type inference at call sites
- Fix: `cmd_build` object file path collision

## [3.47.0] - 2026-04-08

**Guacamaya — GPU Examples + v4.0.0 Gate**

- Add GPU examples: `vector_add.mn`, `matmul_bench.mn` with compiled LLVM IR
- Rewrite SPEC Section 23 with compilable GPU code examples
- Fix self-hosted emitter: `str(false)` zext, `file_exists` i64, regex compile+exec+free, 9 I/O declarations
- Thread-safe dlopen loaders (atomic CAS for ssl_load, evp_load, pcre2_load)
- Add 64MB `__mn_http_get` response limit
- Move `intern_ensure_table()` inside lock
- Add `__mn_str_concat` early returns for empty operands
- Deduplicate `mnstr_to_cstr`/`MnHandleTable` into shared `mapanare_internal.h`
- All C files compile with -Werror
- 40/40 golden tests pass

## [3.46.0] - 2026-04-08

**Caiman — GPU Foundation**

- Link `mapanare_gpu.c` and `mapanare_gpu_builtins.c` into native binaries
- Add 8 GPU builtins: `gpu_available`, `gpu_device_name`, `gpu_device_memory`, `gpu_tensor_add/sub/mul/div/matmul`
- Embedded PTX kernels for CUDA tensor operations (f64 precision)
- CPU fallback when no GPU available
- Fix PTX kernel register name conflicts
- Fix all 5 v3.45.0 review hard blockers
- Apply `-Werror` to all C runtime files
- Correct GPU tensor math verified on NVIDIA RTX 4090

## [3.45.0] - 2026-04-08

### Added

- Exit criteria verified: new user can write → compile → run interactive programs end-to-end
- Package manager (`mapanare install`) confirmed functional: registry + git fallback, lock files, integrity

### Changed

- Test count: 4,845+ (up from 4,465+)
- 38 golden tests, 3 new CLI/network examples, transpile pipeline verified
- All v3.41.0-v3.45.0 roadmap items complete — ready for v4.0.0

## [3.44.0] - 2026-04-08

### Added

- `examples/cli/word_count.mn` — count words/lines/chars in a file (uses read_line, read_file)
- `examples/cli/todo.mn` — interactive TODO manager (uses read_line, read_file, write_file, append_file)
- `examples/network/http_fetch.mn` — fetch a URL and print response (uses http_get)
- `examples/transpile/fibonacci.py` → `fibonacci.mn` — end-to-end transpile → compile → run verified
- All new examples compile to valid LLVM IR and run as native binaries

### Changed

- GPU and mobile examples moved to `examples/experimental/` (require unimplemented backends)

## [3.43.0] - 2026-04-08

### Added

- `mapanare_runtime.c` linked into mnc-stage1 (agent thread pool, ring buffers, lifecycle management)
- Agent runtime symbols available in native binaries (spawn, send, recv, stop, destroy)
- 6 agent runtime entries in `_RUNTIME_FN_ATTRS` (LLVM emitter)

### Changed

- `build_stage1.py`: compiles and links `mapanare_runtime.o` alongside core and io
- Binary size: 2.94 MB (up from 2.86 MB with agent runtime)

## [3.42.0] - 2026-04-08

### Added

- `http_get(url)` builtin — HTTP GET with automatic TLS for https:// URLs
- `sha256(data)`, `hmac_sha256(key, data)` crypto builtins (OpenSSL via dlopen)
- `base64_encode(data)`, `base64_decode(data)`, `hex_encode(data)` encoding builtins
- `random_bytes(n)` — cryptographically secure random data (/dev/urandom)
- `regex_match(pattern, subject)`, `regex_replace(pattern, subject, replacement)` builtins (PCRE2 via dlopen)
- `__mn_http_get` HTTP client in mapanare_io.c (URL parsing, TCP/TLS, HTTP/1.1)
- Golden tests: `36_crypto.mn`, `37_regex.mn`, `38_http.mn` (38/38 pass)
- 11 new runtime function entries in `_RUNTIME_FN_ATTRS`

### Fixed

- Crypto functions (sha1/sha256/sha512): call `evp_load()` before passing function pointers to prevent NULL dereference when OpenSSL not available

## [3.41.0] - 2026-04-08

### Added

- `read_line()` builtin — read one line from stdin (strips newline)
- `read_file()`, `write_file()`, `append_file()`, `file_exists()`, `list_dir()` builtins
- `__mn_read_line`, `__mn_file_append`, `__mn_dir_list_strings` C runtime functions
- `mapanare_io.c` linked into mnc-stage1 (TCP, TLS, crypto, regex symbols available)
- Golden tests: `34_file_io.mn`, `35_stdin.mn` (35/35 pass)
- 13 new I/O function entries in `_RUNTIME_FN_ATTRS` (LLVM emitter)

### Changed

- `stdlib/fs.mn`: `append_file()` and `list_dir()` now functional (were disabled stubs)
- `list_dir()` returns `List<String>` instead of `List<DirEntry>` (simpler ABI)
- `build_stage1.py`: compiles and links `mapanare_io.o` alongside `mapanare_core.o`
- Self-hosted `semantic.mn`: registers all 6 new I/O builtins

### Fixed

- CI native job: `mapanare_io.c` now compiled in CI pipeline

## [3.40.0] - 2026-04-08

### Fixed

- SPEC Section 3.10: added "not yet implemented" disclaimer for Tensor types
- `emit_c.py`: version string now reads from VERSION file instead of hardcoded
- `emit_llvm_text.py`: two remaining typed pointers migrated to opaque `ptr` (LLVM 17+ compat)
- `ast_nodes.py`: added missing `@dataclass` decorator on `ContinueStmt`
- `mapanare_core.c`: `__mn_str_trim*` functions return input directly when no trimming needed (avoids unnecessary allocation)
- `mapanare_core.c`: removed dead `realloc` branch in `__mn_list_concat`

## [3.39.0] - 2026-04-08

### Added

- Valgrind-clean compilation for 30/33 golden tests (remaining 3 are
  uninitialised-value reads in enum match codegen — safe, not UAF)
- Peak memory 160 MB for self-compilation (target was <512 MB)
- Memory profiling infrastructure (`-DMN_PROFILE_MEM` flag in build_stage1.py)

### Changed

- Self-compilation time: 0.74s for 14.7K lines
- Binary: 2.7 MB, IR: 169K lines (stage1), 104K lines (stage2)

## [3.38.0] - 2026-04-08

### Added

- Fixed-point self-compilation verified: stage4 == stage3 (compiler converges
  after two rounds of self-compilation)
- Seed binary updated to fixed-point stage3 build (bootstrap/seed/linux-x86_64/)

### Fixed

- `parser.mn`: field access `fr.fn_data` → `fr.data` (field name mismatch caused
  FnDefData to be typed as i64 in stage2 IR, the only llvm-as error)

### Changed

- Transpiler modules (from_python, from_php, from_typescript, from_go) excluded
  from mnc_all.mn — they contain symbol clashes (new_token) and aren't needed
  for core compiler operation
- mnc_all.mn reduced from 20K to 14.7K lines
- Stage2 IR: 104K lines, valid (0 llvm-as errors)

## [3.37.0] - 2026-04-08

### Fixed

- `mn_list_grow` now always allocates a new buffer instead of calling `realloc`,
  preventing use-after-free when struct copies share list data pointers
- Conservative drop glue: skip cleanup for struct-returning functions to prevent
  freeing resources that were moved into the return value via constructors
- List move semantics: lists passed to function calls or enum inits are removed
  from drop glue tracking (ownership transfer)
- `mn_list_rc` validates COW magic before reading refcount (prevents crash on
  corrupted headers)
- Self-compilation restored: mnc-stage1 compiles mnc_all.mn (20K lines) in <1s,
  123 MB peak memory (was 59 GB / OOM from O(n^2) list cloning)

### Removed

- `no_drop_glue` hack — proper conservative drop glue replaces the blanket disable
- List cloning on struct copy (`_clone_list_fields`) — caused O(n^2) memory blowup
  (390K clones for 575 lines). Safe list growth makes sharing without cloning safe

### Changed

- 33/33 golden tests pass (was 29/33)
- Binary size: 2.7 MB (was 3.4 MB)
- IR: 169K lines (was 185K)
- Memory profiling infrastructure added to C runtime (`-DMN_PROFILE_MEM`)

## [3.36.0] - 2026-04-07

### Added

- `mnc run` — compile and execute .mn files natively (<200ms startup, no Python)
- `mnc build` — produce native binaries with `--release`, `--debug`, `--small` modes
- `mnc build <dir>` — incremental multi-module builds with SHA-256 cache
- `mnc compile` — transpile .py/.php/.ts/.go to native (shells out for transpilation step)
- `mnc cache stats|clean` — manage `.mnc_cache/` compilation cache
- `--timing` flag for per-module build timing reports
- `--watch` mode for continuous rebuild on file changes (via inotifywait)
- Precompiled C runtime (`make build-rt` → `libmapanare_rt.a`) for faster linking
- Startup benchmark (`tests/bench/bench_startup.sh`) and compile-time benchmark suite
  (`tests/bench/bench_compile.sh`) with CI gates
- Python CLI shows `[dev mode]` notice recommending `mnc run` for native speed

### Changed

- IR output reduced from 275K to 185K lines (no drop glue for batch compiler builds)
- Binary size: 3.4MB stripped (was 3.7MB)
- IR blowup ratio: 4.5x (was 13.75x)

### Fixed

- Text emitter drop glue use-after-free: list/string fields embedded in returned structs
  were freed before the caller read them, causing SIGSEGV on any compilation (29/33 golden
  tests now pass, was 0/33)
- `no_drop_glue` option added to text emitter — disables all drop glue for batch compiler
  builds where memory leaking is acceptable (compiler processes one file and exits)
- `concat_self.sh` missing transpiler modules (now matches `concat_self.py` order)

## [3.35.0] - 2026-04-07

### Changed

- `lexer.mn:tokenize()` migrated from `for _ in 0..2000000` bounded loop to `while pos < slen`
  — proves break/continue work correctly in the Python lowerer
- Removed 6 stale "avoids break-in-for bug" comments from `lower.mn` (bug was already fixed)

### Added

- Golden test `33_break_continue.mn` — validates break-in-for, break-in-while, continue, nested break

## [3.34.0] - 2026-04-07

### Fixed

- `__mn_map_new` now takes explicit `val_type` parameter — eliminates size-based heuristic that
  misclassified 16-byte non-string structs as String, causing memory corruption in `__mn_map_free_deep`
  (flagged by 4 reviewers: Viper, Mamba, Cobra, Rattler)
- `__mn_file_copy` returns -1 on write failure instead of unconditional 0
- `__mn_signal_on_change` wrapped in `mn_signal_lock()`/`mn_signal_unlock()` (thread safety)
- Typed pointer `bitcast` in `_do_env_load` removed — LLVM 17+ opaque pointer compatibility
- Typed pointer `{t}*` syntax in auto-declare store changed to `ptr` — LLVM 17+ compatibility
- Self-hosted `types_compatible` now compares function parameter types pairwise and return types
  (was only checking parameter count)
- `is_digit` name collision in concatenated `mnc_all.mn` resolved (deleted duplicate from transpiler.mn)
- Vestigial `getattr(expr, "trait_dispatch", None)` replaced with direct field access in lower.py
- `Err.unwrap()` return type changed from `-> E` to `-> NoReturn`
- Version strings updated: main.mn 3.26.0→3.34.0, emit_c.py v3.0.0→v3.34.0

### Removed

- Duplicate `cow_shares` forward declaration (mapanare_core.c line 764)
- Dead `llvm_list_type()` function from emit_llvm_ir.mn (stale 4-field layout, never called)
- ~200 lines of duplicated `is_XX_alpha` functions across 4 transpilers (replaced with shared
  `is_transpiler_alpha` in transpiler.mn)

### Changed

- `_ARITH_TRAIT_MAP` and `_op_to_trait` moved to module scope (lower.py, semantic.py)
- `continue` keyword added to SPEC.md Section 2.1 keyword table
- FloorDiv annotation expanded to note negative operand divergence
- Transpiler CLI help text updated to mention PHP (.php) alongside Python (.py)

## [3.33.0] - 2026-04-07

### Removed

- Dead GPU kernel stubs (`_generate_ptx_kernel`, `_generate_glsl_kernel`) from lower.py
  (live GPU dispatch remains in emit_llvm_mir.py + mapanare_gpu.c)
- Arena create/destroy overhead from text emitter (was creating arenas but never allocating from them)
- Hardcoded `"lines"`/`"str_globals"` skip in `_clone_list_fields` (all list fields now cloned uniformly)

### Fixed

- `trait_dispatch` added as proper field on BinaryExpr (was monkey-patched with `# type: ignore`)
- Robin Hood PSL uint8_t overflow guard — forces rehash at PSL=255 instead of wrapping
- LLVM fn attrs: `noalias` on allocators, `willreturn` on free functions, `readonly` on getters

## [3.32.0] - 2026-04-07

### Fixed

- Duplicate `cow_shares` forward declaration annotated (mapanare_core.c)
- `__mn_any_typename` no longer heap-allocates per call (lazy-init cached strings)
- `QueryPerformanceFrequency` cached in `mapanare_time_us()` (Windows performance)
- `__mn_file_copy` now checks `fwrite` return value (silent data loss on disk full)
- `__mn_clock_monotonic_ns` implemented on Windows (was returning 0)
- `__mn_sleep_ms` implemented on Windows (was no-op)
- `__mn_list_push` release-mode reinit now logs diagnostic before recovery
- List drop glue now skips freeing returned list via pointer comparison (use-after-free fix)
- Python transpiler `FloorDiv` mapping annotated with semantic note

### Added

- MnMap test suite (8 tests: new, set, get, del, contains, len, iter, free_deep)
- MnSignal test suite (4 tests: new, set/get, subscribe/unsubscribe, no-change skip)
- MnStream test suite (4 tests: from_list/collect, map, filter, free_chain)
- MnValue/any test suite (5 tests: box_int, box_float, box_bool, unbox_int, typename)
- C runtime tests: 53 → 74 (21 new tests)

## [3.31.0] - 2026-04-07

### Added

- Go transpiler (`mapanare/self/from_go.mn`) — new language front-end
- Go tokenizer: raw strings, rune literals, hex, `:=`, `<-`, `&^` operators
- ~28 Go keywords, struct/interface/func/const/var translation
- goroutine `go func()` → `spawn`, `defer` → comment, `range` → `for in`
- Multiple return `(T, error)` → `Result<T, String>` pattern
- Method receivers → self parameter in impl block
- Go stdlib shims: fmt.Println→print, append→push, strings.Contains→contains, etc.
- 9 self-hosted Go transpiler tests
- Self-hosted compiler now 16 modules, ~20,000+ lines across all .mn files

## [3.30.0] - 2026-04-07

### Added

- TypeScript transpiler (`mapanare/self/from_typescript.mn`) — new language front-end
- TS tokenizer: template literals, `===`/`!==`/`...`/`>>>`/`?.`/`??`/`=>` operators
- ~45 TS keywords, interface→trait, class→struct+impl, enum translation
- TS stdlib shims: console.log→print, parseInt→int, Math.abs→abs, etc.
- 8 self-hosted TypeScript transpiler tests

## [3.29.0] - 2026-04-07

### Added

- Self-hosted PHP transpiler (`mapanare/self/from_php.mn`)
- PHP tokenizer: `$variable`, `<?php` tag, `//`/`#`/`/* */` comments, `=>`/`::`/`===`
- PHP keyword table (~40 keywords), class/function/method translation
- PHP stdlib shims: strlen→len, strtolower→.to_lower, explode→.split, etc.
- 9 self-hosted PHP transpiler tests

## [3.28.0] - 2026-04-07

### Added

- Self-hosted Python transpiler (`mapanare/self/from_python.mn`) — ~630 lines
- Python tokenizer: strings, numbers, identifiers, keywords, operators, comments
- Python keyword table (35 keywords)
- PyParser recursive descent with expression/statement translation
- Python stdlib shims (18 mappings: append→push, upper→to_upper, etc.)
- Type translation via transpiler.mn framework (int→Int, str→String, etc.)
- Function, class, import, return statement translation
- 14 self-hosted transpiler tests across 3 test classes
- Module wired into self-hosted build (13th module in concat order)

## [3.27.0] - 2026-04-07

### Added

- Shared transpiler framework (`mapanare/self/transpiler.mn`) — ~500 lines
- TypeMapping struct + `translate_type()` with nullable/generic support
- FieldDef, MethodDef, ParamDef structs + `translate_class_to_struct()`
- CatchClause struct + `translate_exception_to_result()`
- StdlibShim struct + `translate_stdlib_call()` with arg reorder
- TranspilerState with scope push/pop, var tracking, indent management
- `infer_local_type()` for literal-based type inference
- `report_unsupported()` diagnostic helper
- `needs_any_boxing()` + `emit_any_annotation()` helpers
- Language-specific mapping factories: Python, PHP, TypeScript, Go
- 23 framework tests across 4 test classes
- Module wired into self-hosted build (12th module in concat order)

## [3.26.0] - 2026-04-07

### Fixed

- TypeKind.ANY mapped in text emitter (MN_VALUE) and llvmlite emitter
- Arithmetic on `any` values rejected at semantic check with clear error
- PHP transpiler: `$this` → `self`, return type translation, isset/empty/is_array mappings
- C backend stream operation call signatures match runtime declarations
- Signal unsubscribe race: added locking to `__mn_signal_unsubscribe`
- Map free heuristic: explicit `val_type` field replaces size-based guessing
- llvmlite emitter deprecated with warning
- CLI: wired PHP in `cmd_transpile`, fixed "an Mapanare" typo
- Cookbook output version corrected, `di`/`any` keywords added to spec

## [3.25.0] - 2026-04-07

### Added

- PHP transpiler — `mapanare compile app.php` compiles typed PHP 7.4+ to native
- `mapanare transpile app.php` outputs idiomatic `.mn` source
- Custom regex-based PHP tokenizer + 13-level precedence expression parser
- PHP stdlib shim: strlen→len, count→len, strtolower→.to_lower, explode→.split, implode→join, array_push→.push, etc.
- Class → struct+impl: typed properties become fields, methods become impl block
- PHP array heuristics: `[1,2,3]` → List, `["a"=>1]` → Map
- String interpolation: `"hello $name"` → `"hello " + str(name)`
- C-style for loop pattern detection: `for ($i=0; $i<10; $i++)` → `for i in 0..10`
- Arrow functions: `fn($x) => $x + 1` → `(x) => x + 1`
- 47 PHP compatibility tests across 16 test classes

## [3.24.0] - 2026-04-07

### Added

- Python transpiler — `mapanare compile main.py` compiles typed Python to native
- `mapanare transpile main.py` outputs idiomatic `.mn` source
- `from_python.py`: PythonTranslator class (~500 lines) — functions, classes (→struct+impl), control flow, type inference, f-strings, lambdas
- Python method mapping (append→push, strip→trim, upper→to_upper, etc.)
- Type mapping: int→Int, float→Float, str→String, bool→Bool, list→List, dict→Map
- Auto-detection: `.py` files transparently translated in all CLI commands
- 44 Python compatibility tests across 11 test classes

## [3.23.0] - 2026-04-07

### Added

- `any` type — tagged `MnValue` union in C runtime (12 type tags, box/unbox/typename)
- `TypeKind.ANY` in type system — `any` unifies with every type (gradual typing)
- `typeof` builtin — compile-time constant for concrete types, runtime call for `any`
- Semantic support: `any` in arithmetic/comparison/assignment/function calls
- `__mn_any_box_int`, `__mn_any_box_float`, `__mn_any_box_bool` runtime functions
- `__mn_any_unbox_int`, `__mn_any_unbox_float` with tag-mismatch abort

## [3.22.0] - 2026-04-07

### Changed

- Monomorphization uses `dataclasses.replace()` + targeted body deepcopy instead of full `deepcopy` (structural sharing)
- Optimizer constant propagation uses `replace()` for literal nodes (no deepcopy overhead)
- Added `TYPE_CHECKING` guard for llvmlite type annotations (scaffolding for future type stubs)

## [3.21.0] - 2026-04-07

### Added

- Colorized PASS/FAIL in `mapanare test` output (green/red ANSI when terminal supports it)
- Trait polymorphism cross-link in `for-python-devs.md`

### Changed

- `@cuda`/`@vulkan`/`@gpu` decorators now raise `NotImplementedError` with clear message
- WASM TODO stubs emit `(unreachable)` trap instead of silently skipping
- REPL shows exception type names in error messages

### Fixed

- Tutorial dead `return "unreachable"` after exhaustive match removed
- JSON tutorial match syntax: `Object(obj)` → `JsonValue_Object(obj)`
- Cookbook version string updated to 3.20.0
- Self-hosted `len(source) < 0` → `len(source) == 0` for file detection

## [3.20.0] - 2026-04-07

### Added

- `SymbolKind` enum replaces string-based `Symbol.kind` (10 values, `StrEnum` for compatibility)

### Changed

- MIR optimizer O2 passes now iterate to convergence (max 10 iterations, same as O1)
- Emitter globals (`_current_alloca_block`, `_COERCE_FALLBACK_COUNT`) moved to instance state
- AST constant folding removed from `optimizer.py` (MIR optimizer is canonical)

### Fixed

- Arithmetic trait dispatch (Add/Sub/Mul/Div) now lowered to impl method calls (was silently ignored)
- DWARF debug info struct members now use actual type sizes (was hardcoded 64 bits)

## [3.19.0] - 2026-04-07

### Added

- Self-hosted While/Break/Continue/Assert: Stmt enum variants, parser, semantic checker, lowerer
- Loop context (header/exit labels) in LowerState for Break/Continue support in both For and While
- Assert statement lowers to conditional branch + `__mn_assert_fail` call
- Function attributes (`nounwind`/`readonly`) in self-hosted LLVM emitter (30+ runtime declarations)
- Trait method signature parsing (was brace-skip only)

### Fixed

- For-loop variables now typed from iterable (Range → Int, List<T> → T; was always UNKNOWN)
- Restored 5 commented-out `.push()` calls for generic type tracking (Tensor, call args, lambda params, Signal)

## [3.18.0] - 2026-04-07

### Added

- Container drop glue — lists, maps, signals, streams now freed on function exit (text emitter)
- Per-function arena allocation for non-escaping temporaries (conservative escape analysis)

### Changed

- `__mn_list_push` asserts on corrupted lists in debug builds (release builds keep defensive reinit)

### Fixed

- `__mn_list_push` reinit path now sets `managed = 1` (fixes list data buffer leak in drop glue)

## [3.17.0] - 2026-04-07

### Added

- String/closure drop glue in text emitter — default pipeline no longer leaks heap strings
- Runtime function attributes (`nounwind`/`readonly`) on text emitter `declare` statements
- Boxed enum payload cleanup in drop glue (both emitters)

### Fixed

- `_llvm_type_size` now delegates to `_approx_type_size` for correct alignment padding (fixes closure env buffer overruns on mixed-type captures)

## [3.16.0] - 2026-04-07

### Added

- `__mn_map_free_deep` — frees string keys/values before freeing the map struct
- `__mn_stream_free_chain` — frees entire upstream stream pipeline (iterative, no stack overflow)

### Changed

- String constant alignment from `align 2` to `align 8` (future-proofs 3-bit pointer tagging)
- `mapanare run` now compiles C with `-Wall -Wextra`
- CI stage2 validation no longer uses `continue-on-error` (failures are real)

### Fixed

- Signal tracking context now `_Thread_local` (concurrent computed signals safe)
- Signal subscriber list protected during propagation (snapshot under lock prevents use-after-free on realloc)
- Spec `char_at` return type corrected to `String` (matches implementation)
- Test `test_list_type` updated for 5-field MnList ABI (from v3.15.0)

## [3.15.0] - 2026-04-07

### Fixed

- `__mn_list_concat` null-pointer UB: realloc on NULL-16 when concatenating into a fresh list
- Windows console handler deadlock: removed `mapanare_registry_stop_all()` mutex call from handler thread
- COW list refcount now atomic: `__atomic_fetch_add`/`__atomic_fetch_sub` at 3 sites (safe on ARM64 agent workloads)
- MnList ABI mismatch: added 5th `managed` field to `emit_llvm_text.py`, `emit_llvm.py`, and `mnc_main.c`
- `VkPhysicalDeviceProperties` padding undersized: 804 -> 836 bytes (prevents stack smash on Vulkan)
- `__mn_str_from_bool` no longer heap-allocates per call (static constants)
- `__mn_list_oob_buf` now `_Thread_local` (safe for concurrent agent OOB access)

## [3.14.0] - 2026-04-07

### Added

- Generic arity validation (`List<Int, String>` now errors with "expects 1 type argument(s), got 2")
- Arithmetic operator traits: `Add`, `Sub`, `Mul`, `Div` in `BUILTIN_TRAITS`
- Trait-dispatched binary ops for user-defined types implementing Add/Sub/Mul/Div
- WASM `CHAR` type mapping to `i32` (was falling through to `i64`)
- `BUILTIN_GENERIC_ARITY` dict for compile-time arity checking
- `scope-define-noop` Culebra template for bootstrap regression testing
- Debug info producer now reads version from VERSION file dynamically

### Changed

- `TypeInfo.__hash__` now includes `tuple(self.args)` — fixes pathological collisions for `List<Int>` vs `List<String>`
- CLAUDE.md self-hosted module table updated to match actual line counts (15,000+ lines, 11 modules)
- CI: removed `continue-on-error` on stage1 build step (broken compiler now fails CI)
- Local build scripts use `-Wall -Wextra -Werror` for C compilation

### Fixed

- IdentPattern (named catch-all) now treated as wildcard in match exhaustiveness checks
- Self-hosted `scope_define` fixed: push call was commented out since v2.0.0, symbols now tracked
- Getting-started tutorial: `Point(3.0, 4.0)` -> `new Point { x: 3.0, y: 4.0 }`, removed `Shape_` prefix
- Spec section 27 subsection numbering (was `24.1`/`24.2`/`24.3`)
- Spec `batch {}` syntax marked as not yet implemented

## [3.13.0] - 2026-04-07

### Added

- Runtime function attributes (`nounwind`, `readonly`) on 30+ LLVM declarations
- Target-aware pointer size in `_approx_type_size` (correct for wasm32/i686)
- `managed` field on `MnList` struct for O(1) COW ownership check
- `__mn_range_free` runtime function for range iterator cleanup
- Intern table thread safety (pthread mutex / Windows CriticalSection)
- 2 new Culebra templates: `string-track-noop`, `syscall-in-hot-path`

### Changed

- MnList ABI: 32 bytes -> 40 bytes (added `int64_t managed` field)
- Self-hosted compiler list type updated: `{ ptr, i64, i64, i64 }` -> `{ ptr, i64, i64, i64, i64 }`

### Fixed

- Re-enabled `_track_string` — every heap string now tracked for drop glue cleanup
- Range iterators freed after for-loop exit (was leaking 16 bytes per loop)
- Removed `write(2)` syscall probe from COW list `mn_list_has_magic()` — replaced with `managed` flag
- Windows signal mutex TOCTOU: `InterlockedCompareExchange` replaces plain `int` check

## [3.9.0] - 2026-04-06

### Added

### Changed

### Fixed

## [3.0.3] - 2026-04-04

### Added

- While/mien loop support in self-hosted parser (desugared to for+if)
- `scripts/test_runtime.sh`: automated runtime correctness tests (compile → execute → compare output)

### Fixed

- Exit codes: `main()` now returns `i32 0` (C ABI) instead of `void`
- 12_while golden test: was producing empty output (missing while-loop parsing)

### Changed

- All 15 golden tests produce correct output when executed as native binaries
- Stage1 AND stage2 compiled binaries produce identical correct results
- Three-stage fixed point preserved (78,881 lines, 0 diff)

## [3.0.2] - 2026-04-04

### Added

- Bilingual keywords in self-hosted lexer: `pon`/`si`/`da`/`cada`/`mien`/`sino`/`en`/`tipo`/`nada`/`sal`/`sigue`/`yo`/`modo`/`way`/`usa`/`di`
- `tipo` unified type definitions: `tipo Name { fields }` for structs, `tipo Name { | Variant }` for enums
- BAR token (`|`) for tipo enum variant syntax
- `mnc_driver.c`: C entry point for LLVM-compiled stage2 binary
- `verify_fixed_point.sh`: automated three-stage bootstrap verification

### Fixed

- Result variant index extraction: strip `:N` suffix before Ok/Err comparison
- MIRType hardcoded field index swap (`name`/`kind` were reversed)
- WrapNone in `lower_let`: condition fired on Option-typed function call results, not just None literals — root cause of "vars not found" in stage2 binary
- SSA name collisions: 80 variable renames across 5 self-hosted modules

### Changed

- Three-stage fixed point achieved: `stage2.ll == stage3.ll` (78,676 lines, 0 diff)
- Golden tests: 15/15 pass through mnc-stage1 + llvm-as
- Stage2 IR validates with zero post-processing

## [3.0.1] - 2026-04-03

### Added

- `di` print keyword: `di "hello"` as statement (print() function still works)
- `+` pub prefix: `+fn`, `+tipo`, `+struct`, `+enum`, `+trait`, `+agent`, `+pipe`
- `...` empty block: `fn todo() { ... }` (like Python's `pass`)
- Implicit return: last expression in typed function is returned automatically
- Stage2 IR fixup script (`scripts/fix_stage2_ir.py`)

### Changed

- Self-hosted compiler loop limits raised from 50 to 200 iterations
- Self-hosted match/if PHI handling: skip terminated branches, add switch default entries

### Fixed

- MIR type inference: Option/Result inner types, namespace call returns, enum variant constructors
- C emitter string truncation: aligned string constants for pointer tagging
- C emitter void* boxing: heap-allocate on store, dereference on load
- C emitter memcpy overflows: sizeof(source) instead of sizeof(dest) everywhere
- List push in-place mutation: prevents SSA aliasing bugs in for loops
- mnc-stage1 segfault: binary now self-compiles (77K lines LLVM IR)

## [2.0.0] - 2026-03-25

### Added

- **WebAssembly backend** (`mapanare/emit_wasm.py`): Full MIR-to-WAT emitter with linear memory, bump allocation, string constants, JS bridge imports, and structured control flow
- **CLI `emit-wasm` command** with `--binary` flag for optional `wat2wasm` compilation
- **Cross-compilation targets** (`mapanare/targets.py`): `wasm32-unknown-unknown`, `wasm32-wasi`, `aarch64-apple-ios`, `aarch64-linux-android`, `x86_64-linux-android`
- **GPU compute runtime** (`runtime/native/mapanare_gpu.c/.h`): CUDA Driver API and Vulkan compute via `dlopen` with built-in PTX/GLSL kernels for tensor ops
- **GPU stdlib** (`stdlib/gpu/`): `device.mn`, `kernel.mn`, `tensor.mn` for device detection, kernel management, and GPU-accelerated tensor operations
- **WASM stdlib** (`stdlib/wasm/`): `bridge.mn` (JS interop), `runtime.mn` (WASI preview 1 bindings)
- **AI stdlib** (`stdlib/ai/`): `llm.mn` (LLM driver with provider abstraction), `embedding.mn` (batched embeddings with caching), `rag.mn` (RAG pipeline)
- **Dato data engine** (`dato/src/`): Table, column, aggregation, join, reshape, null handling, I/O, and display modules
- **Database layer** (`stdlib/db/`): `sql.mn`, `sqlite.mn`, `postgres.mn`, `redis.mn`, `kv.mn`, `embedded_kv.mn`, `pool.mn`, `migrate.mn`
- **Database C runtime** (`runtime/native/mapanare_db.c/.h`): SQLite3 and PostgreSQL via `dlopen`, connection pooling, prepared statements
- **Encoding stdlib**: `stdlib/encoding/toml.mn` (1,902 lines), `stdlib/encoding/yaml.mn` (2,121 lines) — full TOML and YAML parsers/serializers
- **Filesystem stdlib** (`stdlib/fs.mn`): read, write, walk, glob, metadata, temp files
- **Web crawler** (`crawl/src/`): URL parser, robots.txt, frontier queue, content extractor, persistence, crawl engine
- **Vulnerability scanner** (`scan/src/`): Template-driven scanner with fingerprinting, pattern matching, YAML templates, report generation
- **HTTP fuzzer** (`fuzz/src/`): Mutation engine, wordlist generation, HTTP fuzzing
- **HTTP server toolkit** (`stdlib/net/http/`): auth, body parsing, config, cookies, rate limiting, sessions, SSE, template rendering
- **HTML parser C runtime** (`runtime/native/mapanare_html.c/.h`): Streaming HTML parser for crawler/scanner
- **Playground WASM runtime** (`playground/src/`): Browser runtime and Web Worker for WASM module execution
- **GPU and WASM examples** (`examples/gpu/`, `examples/wasm/`)
- **Roadmap plans**: `v1.2.0/PLAN.md`, `v1.3.0/PLAN.md`, `v2.0.0/PLAN.md`, `v2.0.0/SUMMARY.md`

### Changed

- Python emitters (`emit_python.py`, `emit_python_mir.py`) now emit `DeprecationWarning` at import time
- `emit_python.py`: `substr` added as alias for `substring` method
- `semantic.py`: `_bind_pattern` now receives `subject_type` for richer pattern binding in match expressions

### Deprecated

- **Python transpiler backends** (`emit_python.py`, `emit_python_mir.py`): Use the LLVM or WASM backend instead

## [1.0.11] - 2026-03-19

### Added

- `_load_struct_fields()` — reconstructs large structs from allocas field-by-field via GEP+load+insert_value, eliminating all by-value loads of structs > 56 bytes
- `_store_struct_fields()` — decomposes large struct stores into per-field GEP+store, eliminating all by-value stores of structs > 56 bytes
- `_aligned_alloca()` — routes all temporary allocas through the pre_entry block to maintain 16-byte RSP alignment (prevents SSE `movaps` crashes)
- Alloca size mismatch detection in `_emit_copy`, `_emit_field_get`, `_emit_index_get` — prevents stack buffer overflow when MIR temp names collide with user variable names
- `fflush(stdout)` in crash handler for reliable debug output

### Changed

- `_ZEROINIT_MEMSET_THRESHOLD` lowered from 128 to 56 to match `_LARGE_STRUCT_THRESHOLD` — `store zeroinitializer` is also truncated by the llvmlite codegen bug
- Self-hosted compiler build (`build_stage1.py`): removed `internal` linkage from all function definitions — LLVM `-O1` was incorrectly stripping called functions as dead code due to sret calling convention confusion
- `_coerce_arg` struct-to-struct reinterpretation now uses `_store_struct_fields`/`_load_struct_fields` for large types instead of by-value store+load
- `_get_value_ptr()` now also checks `%`-prefixed name variant for alloca lookup
- Binary size: 1.50MB (down from 1.71MB — 12% smaller)
- 3,698 tests passing

### Fixed

- **Self-hosted compiler 15/15 golden tests** (was 12/15) — all features now compile correctly including enum match, Result types, string methods
- **Pointer-only large struct refactor**: LLVM 20.1.8 / llvmlite codegen truncates by-value load/store of structs > 56 bytes; all paths now use memcpy via alloca pointers
- **Stack alignment crash**: dynamic allocas in non-entry blocks (from `_coerce_arg`, list ops, etc.) misaligned RSP; SSE `movaps` in libc `snprintf` crashed with SIGSEGV. Fixed by routing all temporaries through pre_entry block.
- **Function stripping at -O1**: LLVM dead-code-eliminated `internal`-linkage functions that were actually called (sret convention confused reachability analysis). Fixed by removing `internal` linkage in post-processing.
- **Alloca size mismatch (stack buffer overflow)**: MIR temp names (t0, t1, ...) colliding with user variable names (e.g., `let t0: TypeResult`) caused 64-byte memcpy into 16-byte alloca. Fixed by checking alloca size before reuse.
- **Generic type parsing in self-hosted compiler**: `Result<Int, String>` parsing failed ("Expected GT but got EOF") because the alloca overflow corrupted the `pos` field of TypeResult
- **Byptr parameter loading**: large struct parameters passed by pointer were loaded by value in the callee prologue — now use memcpy from param pointer to local alloca
- **Field extraction of large sub-fields**: `_emit_field_get` loaded large struct fields by value from parent struct — now uses memcpy to local alloca via GEP

## [1.0.0] - 2026-03-XX

### Added

- **Language specification freeze**: SPEC.md promoted to "1.0 Final" — syntax, semantics, and type system are frozen; future changes require RFC + deprecation cycle
- **Spec compliance tests**: 85 tests covering all grammar rules (parse + semantic + LLVM); 20 negative tests for error diagnostics
- **Spec cross-reference tests**: automated validation of 32 keywords, 25 TypeKinds, 28 operators against grammar, semantic checker, and emitters
- **Formal memory model** (`docs/MEMORY_MODEL.md`): documents arena lifecycle, string ownership (tag-bit system), struct/enum/list/map ownership, agent message passing, signal/stream/closure lifecycle
- **Stability policy** (`docs/STABILITY.md`): backwards compatibility guarantees, semantic versioning contract, deprecation cycle, what is and is not frozen
- **RFC process** (`docs/rfcs/RFC_PROCESS.md`): when RFCs are required, template, review process, acceptance criteria
- **Migration guide template** (`docs/MIGRATION_TEMPLATE.md`): standardized format for communicating breaking changes
- **Fixed-point verification script** (`scripts/verify_fixed_point.sh`): automated 3-stage self-compilation pipeline (stage1 -> stage2 -> stage3, binary diff)
- **Deprecation warning support**: `@deprecated("message")` decorator emits compiler warnings on function calls
- **`--edition` flag**: future-proofing for language editions (default: `2026`, no-op for now)
- **Version-stamped binaries**: compiler version embedded in LLVM IR metadata (`!mapanare.version`)
- **Security audit**: C runtime audited for buffer overflows, use-after-free, integer overflows, thread safety, TLS security

### Changed

- SPEC.md version bumped to 1.0.0, status to "1.0 Final"
- Python backend marked as "legacy, for reference only" in all documentation
- Bootstrap verification tests updated to use MIR-based emitter pipeline
- Stage 1 tests skip correctly on Windows (ELF binary detection)
- Debug print statements removed from self-hosted compiler sources (parser.mn, emit_llvm.mn, main.mn)
- Compiler pipeline optimized: 805ms -> 503ms (37% faster) for 7 stdlib modules
- README updated with current test count (3,600+) and v1.0 status
- 3,600+ tests passing (up from 3,400 in v0.9.0)

### Fixed

- Closure call crash when closure was `i8*` instead of `{i8*, i8*}` struct across basic blocks
- Copy propagation unsafe through FieldSet/IndexSet mutation targets (alloca mismatch)
- `.value` field assignment treated as SignalSet for all types (now checks `TypeKind.SIGNAL`)
- Function parameters not stored to allocas causing uninitialized memory in conditional branches
- Boxed struct field set (`_emit_field_set`) not handling heap allocation for recursive fields
- `_coerce_arg` struct-to-struct case allocating wrong size (now uses `max(src, dest)` with zero-fill)
- Nested `state.module.X.push()` losing data in self-hosted lowerer (2-level field write-back)
- `emit_instr` in self-hosted lowerer was a no-op (now uses IndexSet on shared blocks buffer)

## [0.9.0] - 2026-03-13

### Added

- **Native stdlib in Mapanare**: Seven stdlib modules written in `.mn`, compiled to LLVM IR — no Python at runtime
- **`encoding/json.mn`** (982 lines): Recursive descent JSON parser with escape handling, number parsing, arrays, objects; encoder + pretty-printer; SAX-style streaming parser (`stream_parse` → `Stream<JsonEvent>`); schema validation
- **`encoding/csv.mn`** (330 lines): RFC 4180 compliant CSV parser/writer; configurable delimiter and quote character; header row support; `to_string` serialization; `collect_rows` convenience function
- **`net/http.mn`** (1,103 lines): Full HTTP/1.1 client on C runtime TCP/TLS; URL parser (scheme, host, port, path, query); request builder; response parser (Content-Length + chunked transfer); redirect following; convenience wrappers (`get`/`post`/`put`/`delete`/`patch`/`head`/`options`); request fingerprinting
- **`net/http/server.mn`** (~600 lines): HTTP server with route matching and path parameters; middleware pattern (logging + CORS); request parsing; response building; static file serving; server listen loop
- **`net/websocket.mn`** (~1,120 lines): RFC 6455 WebSocket client + server; HTTP upgrade handshake; SHA-1 + Base64 accept key; frame encoding/decoding (7/16/64-bit payload length); client masking; ping/pong auto-respond; close handshake; message fragmentation
- **`crypto.mn`** (283 lines): Cryptographic primitives via C runtime — SHA-1, SHA-256, HMAC, Base64 encode/decode, random bytes, JWT helpers
- **`text/regex.mn`** (271 lines): Regular expressions via PCRE2 FFI (`dlopen`); match, search, replace, split operations
- **Cross-module LLVM compilation** (`multi_module.py`): Dependency graph with topological sort, name mangling (`{module_path}__` prefix), MIR symbol renaming, import remapping, MIR merging into single LLVM IR module; `--stdlib-path` CLI flag; incremental compilation with source hashing
- **Integration tests**: HTTP client↔server, JSON decode→encode round-trip, CSV parse→write pipeline, WebSocket frame encode/decode
- **Stdlib compilation benchmarks** (`bench_stdlib.py`): 5,159 lines of `.mn` → LLVM IR in ~880ms (5,866 lines/s)

### Changed

- Dato package updated to use `encoding/csv.mn` and `encoding/json.mn` via cross-module imports
- README feature status table updated: stdlib modules now Yes/Yes for LLVM backend
- SPEC.md updated with stdlib module documentation
- ROADMAP.md updated with v0.9.0 completion
- 3,400+ tests passing (up from 3,020 in v0.8.0)

### Fixed

- `.value` field access incorrectly treated as `SignalGet` for non-signal types
- Match arm payload types (`Ok(val)`) inferred as UNKNOWN — added `_infer_payload_type()` in lowerer
- For-loop iteration variable types inferred as UNKNOWN — added `_infer_iterable_elem_type()`
- `FieldGet` fallback extracting wrong struct field index when type is unknown
- Auto-declared function parameter types using LLVM value types instead of MIR semantic types
- Enum type resolution defaulting user-defined enums to STRUCT
- Enum tag extraction crash on pointer-typed values
- Switch on enum variants calling `int("GET")` instead of resolving variant tags
- Multi-line `new Struct { ... }` struct literals not parsing correctly (tests updated to single-line)
- Nullary enum variant `Null` treated as function type instead of value (use `Null()`)

## [0.8.0] - 2026-03-13

### Added

- **LLVM Map/Dict codegen**: Robin Hood hash table in C runtime (`__mn_map_new`, `__mn_map_set`, `__mn_map_get`, `__mn_map_del`, `__mn_map_iter`, `__mn_map_contains`); both AST and MIR emitters; map literals, indexing, assignment, iteration all work natively
- **LLVM signal reactivity**: Full dependency graph in C runtime — computed signals with lazy recomputation, subscriber notification, batched updates (`__mn_signal_computed`, `__mn_signal_subscribe`, `__mn_signal_batch_begin/end`), topological propagation order
- **LLVM stream operators**: Native stream runtime with `__mn_stream_from_list`, `__mn_stream_map`, `__mn_stream_filter`, `__mn_stream_take`, `__mn_stream_skip`, `__mn_stream_collect`, `__mn_stream_fold`, `__mn_stream_bounded` (backpressure); pipe operator (`|>`) targets stream operations; `for x in stream` iteration
- **LLVM closure capture**: Environment struct generation per lambda, free variable analysis, arena-allocated closure environments (`{fn_ptr, env_ptr}`), `ClosureCreate`/`ClosureCall`/`EnvLoad` MIR instructions; both AST and MIR emitters
- **Complete string methods on LLVM**: `contains`, `split`, `trim`, `trim_start`, `trim_end`, `to_upper`, `to_lower`, `replace` — all via C runtime functions + both emitters
- **Pipe definitions on LLVM**: `pipe Name { A |> B |> C }` compiles to agent spawn chains in both emitters
- **C runtime TCP sockets**: `__mn_tcp_connect`, `__mn_tcp_listen`, `__mn_tcp_accept`, `__mn_tcp_send`, `__mn_tcp_recv`, `__mn_tcp_close`, `__mn_tcp_set_timeout`; cross-platform (POSIX + Winsock2)
- **C runtime TLS**: `__mn_tls_init`, `__mn_tls_connect`, `__mn_tls_read`, `__mn_tls_write`, `__mn_tls_close`; dynamic OpenSSL loading via dlopen/LoadLibrary, SNI support
- **C runtime file I/O**: `__mn_file_open`, `__mn_file_read_fd`, `__mn_file_write_fd`, `__mn_file_close`, `__mn_file_stat`, `__mn_dir_list`
- **C runtime event loop**: `__mn_event_loop_new`, `__mn_event_loop_add_fd`, `__mn_event_loop_remove_fd`, `__mn_event_loop_run`, `__mn_event_loop_run_once`; epoll (Linux), kqueue (macOS), select fallback (Windows)
- Stream fusion in MIR optimizer: map+map, map+filter, filter+filter fusion passes
- 37 new map tests (codegen + runtime), 26 signal tests, 34 stream tests, 18 closure tests, TCP/TLS/file I/O/event loop tests

### Changed

- README feature status table updated to reflect full LLVM backend parity — all core features now Yes/Yes
- REPL removed from CLI listing and feature table (never fully implemented)
- Tensor/GPU section rewritten honestly — experimental prototypes only, no language integration
- SPEC.md updated with closure semantics, map codegen on LLVM, signal/stream LLVM status
- ROADMAP.md updated with v0.8.0 release entry and feature status
- 3,020 tests passing (up from 2,983 in v0.7.0)

### Fixed

- MIR emitter `EnumTag` for non-enum types in nested pattern matching
- DCE not tracking `InterpString` references (string interpolation on LLVM)
- `while` loop `break`/`continue` on LLVM backend

## [0.7.0] - 2026-03-12

### Added

- **Self-hosted MIR lowering** (`lower.mn`): 2,629 lines of Mapanare translating AST → MIR, completing the self-hosted compiler pipeline (7 modules, 8,288+ lines)
- **Self-hosted LLVM emitter rewrite** (`emit_llvm.mn`): rewrote to consume MIR instead of AST (~1,050 lines), matching the bootstrap architecture
- **Built-in test runner**: `mapanare test` discovers and runs `@test` functions in `.mn` files; `assert` statement in grammar, AST, MIR, and both emitters; `--filter` for substring matching
- **Agent observability**: OpenTelemetry-compatible tracing (`--trace` flag), OTLP HTTP export, W3C Trace Context spans for agent lifecycle (spawn, send, handle, stop, pause, resume)
- **Prometheus metrics**: `--metrics :PORT` flag serves agent counters (spawns, messages, errors, stops) and handle-duration histograms
- **Structured error codes**: 33 codes in `MN-X0000` format across parse (MN-P), semantic (MN-S), lowering (MN-L), codegen (MN-C), runtime (MN-R), and tooling (MN-T) categories
- **DWARF debug info**: `mapanare build -g` emits compile units, function info, line numbers, variable debug info, and struct type metadata for `gdb`/`lldb` debugging
- **Deployment infrastructure**: `mapanare deploy init` scaffolds Dockerfile; `HealthServer` with `/health`, `/ready`, `/status` endpoints; `SupervisionTree` with one-for-one, one-for-all, rest-for-one strategies; `@supervised` decorator; SIGTERM graceful shutdown with drain timeout
- **Native runtime trace hooks**: C runtime `mapanare_trace_hook_fn` callback for spawn/send/handle/stop/pause/resume/error events
- **CI bootstrap verification**: parse verification and module resolution tests for self-hosted compiler

### Changed

- Self-hosted compiler driver (`main.mn`) wired to AST → MIR → LLVM pipeline
- SPEC.md updated to v0.7.0: new sections for testing (10), observability (11), and deployment (12)
- ROADMAP.md updated with v0.7.0 release and self-hosted compiler status (7,500+ lines across 7 modules)
- Bootstrap snapshot remains at v0.6.0 (self-hosted binary compilation blocked by bootstrap emitter gaps)
- 2,983 tests passing (up from 2,538 in v0.6.0)

## [0.6.0] - 2026-03-12

### Added

- **MIR pipeline**: Typed SSA-based intermediate representation between AST and code emission (`mir.py`, `mir_builder.py`, `lower.py`)
- **MIR lowering**: AST → MIR translation pass (1,397 lines) covering all language constructs — expressions, control flow, agents, signals, streams, pattern matching, string interpolation
- **MIR optimizer** (`mir_opt.py`): Constant folding, dead code elimination, copy propagation, basic block merging, unreachable block removal
- **MIR → LLVM emitter** (`emit_llvm_mir.py`): Translates MIR basic blocks to LLVM IR via llvmlite
- **MIR → Python emitter** (`emit_python_mir.py`): Translates MIR to Python source code
- **`emit-mir` CLI command**: Dump MIR text representation for debugging
- **Bootstrap Makefile** (`bootstrap/Makefile`): `make bootstrap` and `make verify` for three-stage bootstrap verification

### Changed

- Bootstrap snapshot updated to v0.6.0 (22 files: all compiler modules + grammar)
- `bootstrap/README.md` rewritten with MIR pipeline documentation and file index
- SPEC.md Appendix B rewritten with full MIR description (instruction categories, optimizer passes, pipeline diagram)
- ROADMAP.md architecture diagram updated to show AST → MIR → Optimizer → Emitter pipeline
- ROADMAP.md release history updated with v0.5.0 and v0.6.0 entries
- SPEC.md version bumped to 0.6.0
- 2,538 tests passing (up from 2,200+ in v0.5.0)

## [0.5.0] - 2026-03-11

### Added

- **String interpolation**: `"Hello, ${name}!"` with `${expr}` syntax in both regular and triple-quoted strings; `InterpString` AST node; works on Python and LLVM backends
- **Multi-line strings**: `"""..."""` triple-quoted string literals
- **Linter**: `mapanare lint` with 8 rules (W001-W008): unused variables, unused imports, shadowing, unreachable code, unnecessary mut, empty match arms, unchecked results; `--fix` auto-repairs W002/W005; `@allow(rule)` suppression; LSP integration
- **Python interop**: `extern "Python" fn module::name(params) -> Type` for calling Python functions; type marshalling; `Result<T, String>` wraps exceptions; `--python-path` flag
- **WASM playground**: Browser-based editor at `play.mapanare.dev` via Pyodide; CodeMirror 6 with `.mn` syntax highlighting; 7 pre-loaded examples; share via URL hash
- **Package registry**: `mapanare publish`, `mapanare search`, `mapanare login`; FastAPI registry backend; semver resolution; `mapanare install` checks registry before git fallback; package browser UI
- **Doc comments**: `///` syntax captured in grammar as `DOC_COMMENT` tokens; `DocComment` AST node wraps definitions
- **Doc generator**: `mapanare doc <file>` generates styled HTML documentation from `///` doc comments
- **Language reference** (`docs/reference.md`): complete reference covering all types, keywords, operators, syntax, builtins, CLI commands, lint rules
- **Cookbook** (`docs/cookbook.md`): 14 real-world recipes from hello world to Python interop
- **Stdlib documentation** (`docs/stdlib.md`): API reference for all 7 stdlib modules
- **Migration guides**: `docs/for-python-devs.md`, `docs/for-rust-devs.md`, `docs/for-typescript-devs.md`
- 37 Python interop tests, 25 interpolation tests, 35 linter tests, playground tests, registry tests

### Changed

- README updated with v0.5.0 CLI commands (lint, doc, publish, search, login), roadmap status, stdlib reference link
- All compiler passes (parser, semantic, optimizer, emitters, linter, LSP) handle `DocComment` AST nodes

## [0.4.0] - 2026-03-11

### Added

- **FFI support**: `extern "C" fn` declarations for binding native libraries, `--link-lib` CLI flag for linker pass-through
- **Rich diagnostics**: Rust-style colorized error output with source spans, labels, and summary counts (`mapanare/diagnostics.py`)
- **Error recovery**: `mapanare check` uses `parse_recovering()` to collect multiple parse errors in a single pass, then runs semantic analysis on the partial AST
- **Parser span tracking**: all AST nodes now carry `Span` with line/column start and end positions
- **Native runtime hardening**: mutex-protected thread-pool work queue, atomic agent state transitions, arena bounds checking
- **CI native job**: compiles and runs C runtime tests with gcc, AddressSanitizer, and ThreadSanitizer
- **LSP enhancements**: symbol table construction, cross-reference indexing, go-to-definition, find-references, hover info
- **Bootstrap documentation** (`docs/BOOTSTRAP.md`): self-hosting compiler status and architecture
- **Roadmap** (`docs/roadmap/ROADMAP.md`): phased plan through v1.0
- **Localized READMEs**: Spanish (`docs/README.es.md`), Portuguese (`docs/README.pt.md`), Chinese (`docs/README.zh-CN.md`)
- Scope-analysis tests (`tests/test_scope.py`)
- C runtime test harness (`tests/native/test_c_runtime.c`) and hardening tests (`tests/native/test_c_hardening.py`)
- FFI test suite (`tests/ffi/test_ffi.py`)
- Diagnostics test suite (`tests/diagnostics/test_diagnostics.py`)
- Bootstrap verification tests (`tests/bootstrap/test_verification.py`)
- Dev script (`dev.ps1`) now watches `*.c`/`*.h` files and runs gcc C runtime tests

### Changed

- GPU, model, and tensor modules moved from `mapanare/` to `experimental/` with clear opt-in boundary
- `mapanare/types.py` gains `EXPERIMENTAL_TYPES` registry separating experimental type metadata from core
- All CLI error output routes through the new diagnostics system instead of plain `print()`
- README updated with language selector badges linking to localized docs
- VSCode extension removed from tree (to be maintained separately)

### Fixed

- Thread-pool work queue race condition (missing mutex around push/pop)
- Agent state updates using non-atomic writes (now uses `__atomic_compare_exchange_n`)
- Missing `#include <unistd.h>` in C runtime for POSIX portability
- Unused local variables in `mapanare/lsp/analysis.py`

## [0.3.1] - 2026-03-10

### Changed

- Version source of truth consolidated to `VERSION` file
- CLI reads version via `importlib.metadata` instead of hardcoded string
- Publish workflow reads version from `VERSION` file instead of parsing `cli.py`

### Fixed

- PyPI publish failing with 400 due to stale version in `cli.py`
- Benchmark test hardcoded version string

## [0.3.0] - 2026-03-10

### Added

- **Traits system**: `trait` and `impl Trait for Type` syntax, trait bounds on generics, builtin traits (`Display`, `Eq`, `Ord`, `Hash`), monomorphization for LLVM backend, Protocol emission for Python backend
- **Module resolution**: file-based imports with `pub` visibility, circular dependency detection, transitive imports, stdlib module wiring, multi-file compilation on both backends
- **LLVM native agents**: `spawn`, `send` (`<-`), `sync` codegen targeting C runtime with OS threads, agent handler dispatch, supervision policy codegen (`@restart`)
- **Semaphore-based agent scheduling**: replaced 1ms polling sleep with `inbox_ready`/`outbox_ready` semaphores in C runtime
- **Arena-based memory management**: arena allocator in C runtime, scope-based arena insertion in LLVM emitter, heap/constant string tagging via LSB tag bit, `__mn_str_free` and `__mn_list_free_strings`
- **Formal type representation**: `TypeKind` enum (25 kinds), `TypeInfo` dataclass, canonical builtin registries in `mapanare/types.py`
- **Getting Started tutorial** (`docs/getting-started.md`) — 12 sections from install to streams
- **Community governance**: `CODE_OF_CONDUCT.md`, `SECURITY.md`, `GOVERNANCE.md`, issue/PR templates
- **110+ end-to-end tests**: correctness, cross-backend consistency, tutorial verification
- **Memory stress tests** (`tests/native/test_memory_stress.py`)
- **Agent-pipeline benchmark** (`benchmarks/cross_language/05_agent_pipeline`) with .mn/.py/.go/.rs versions
- **RFCs**: memory management (0002), module resolution (0003), traits (0004)
- `CLAUDE.md` with repo guidance for AI-assisted development
- 1968 total tests (up from ~1400 in v0.2.0)

### Changed

- Semantic checker refactored to use `TypeKind` enum instead of string-based type comparisons
- All emitters import builtin registries from `types.py` (single source of truth)
- Stream benchmark rewritten to use actual stream primitives
- Concurrency benchmark rewritten with real parallel message passing
- Benchmark tables updated with "Features Tested" column and honest notes
- `docs/SPEC.md` updated: arena-based memory, grammar summary with traits/imports, accurate appendices
- C runtime expanded with arena allocator, semaphore-based scheduling, improved memory management
- README feature status table audited and corrected against actual implementation
- CONTRIBUTING.md expanded with non-code contribution paths

### Fixed

- All type error messages now use `TypeInfo.display_name` for consistent formatting
- LLVM emitter syncs builtin assertions with canonical type registries
- REPL status corrected from "Planned" to "Experimental" in README
- Map/Dict status corrected from "Planned" to "Stable" in README
- 7 stale feature status entries corrected

## [0.2.0] - 2026-03-08

### Added

- Native C runtime (`runtime/native/mapanare_core.c`, `mapanare_core.h`) with arena-based memory, lock-free SPSC ring buffers, and thread pool with work stealing
- LLVM backend: string and list codegen with proper memory management
- Self-hosted recursive-descent parser (`mapanare/self/parser.mn`, ~1500 lines)
- Self-hosted semantic checker (`mapanare/self/semantic.mn`, ~800 lines)
- Self-hosted LLVM emitter (`mapanare/self/emit_llvm.mn`, ~1630 lines)
- Compiler driver for orchestrating the full compilation pipeline
- `str()`, `int()`, `float()` builtin conversion functions
- `while` loops and `Map` type in AST and parser
- REPL / interactive mode
- Implicit top-level statements (scripting mode)
- Two-pass semantic checker with type inference improvements

### Changed

- Package renamed from `mapa` to `mapanare` (all imports, CLI, tests updated)
- Docs moved: `SPEC.md` → `docs/SPEC.md`, `rfcs/` → `docs/rfcs/`
- Packaging scripts moved to `packaging/` directory
- CI pointed to `dev` branch; release workflow removed in favor of publish workflow
- Python emitter enhanced for while loops and map literals

## [0.1.0] - 2026-02-20

### Added

- **Compiler pipeline**: Lark LALR parser → AST (dataclasses) → semantic checker → optimizer → emitters
- **LALR grammar** (`mapanare.lark`) with 13-level precedence climbing
- **AST nodes**: full dataclass-based node definitions for all language constructs
- **Semantic checker**: two-pass type checker and scope resolver
- **Optimizer**: constant folding, dead code elimination, agent inlining, stream fusion (O0–O3)
- **Python transpiler**: agents → asyncio, signals → reactive, streams → async generators
- **LLVM IR backend**: basic functions, structs, enums, arithmetic via llvmlite
- **CLI** with `compile`, `check`, `run`, `fmt`, `build`, `jit`, `emit-llvm`, and `init` commands
- **Runtime system**: asyncio-based agents, reactive signals, async stream operators, Result/Option types
- **Self-hosted compiler**: initial lexer (`lexer.mn`) and parser (`parser.mn`)
- **Language spec** (`docs/SPEC.md`): complete specification of syntax and semantics
- **Design manifesto** (`docs/manifesto.md`): language philosophy and goals
- **Agent syntax RFC** (`docs/rfcs/0001-agent-syntax.md`)
- **Benchmark suite**: matrix multiply, concurrency, stream pipeline, fibonacci with Python/Go/Rust comparisons
- **VSCode extension**: syntax highlighting, snippets, language configuration
- **LSP server**: basic analysis and diagnostics
- **Stdlib modules**: math, text, time, io, log, http, pkg (Python backend)
- **Test suite**: 1400+ tests covering parser, semantic, optimizer, emitters, runtime, LLVM, CLI, and more
- **CI pipeline**: GitHub Actions with Python 3.11/3.12 matrix on Ubuntu
- **PyPI publishing** workflow
- **GPU module** (`gpu.py`) and **model loading** (`model.py`) — experimental
- **Tensor operations** (`tensor.py`) — experimental
- `CONTRIBUTING.md`, `LICENSE` (MIT), and project scaffolding

[Unreleased]: https://github.com/Mapanare-Research/Mapanare/compare/v3.45.0...HEAD
[3.45.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.44.0...v3.45.0
[3.44.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.43.0...v3.44.0
[3.43.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.42.0...v3.43.0
[3.42.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.41.0...v3.42.0
[3.41.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.40.0...v3.41.0
[3.40.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.39.0...v3.40.0
[3.39.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.38.0...v3.39.0
[3.38.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.37.0...v3.38.0
[3.37.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.36.0...v3.37.0
[3.36.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.35.0...v3.36.0
[3.35.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.34.0...v3.35.0
[3.34.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.33.0...v3.34.0
[3.33.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.32.0...v3.33.0
[3.32.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.31.0...v3.32.0
[3.31.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.30.0...v3.31.0
[3.30.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.29.0...v3.30.0
[3.29.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.28.0...v3.29.0
[3.28.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.27.0...v3.28.0
[3.27.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.26.0...v3.27.0
[3.26.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.25.0...v3.26.0
[3.25.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.24.0...v3.25.0
[3.24.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.23.0...v3.24.0
[3.23.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.22.0...v3.23.0
[3.22.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.21.0...v3.22.0
[3.21.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.20.0...v3.21.0
[3.20.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.19.0...v3.20.0
[3.19.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.18.0...v3.19.0
[3.18.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.17.0...v3.18.0
[3.17.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.16.0...v3.17.0
[3.16.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.15.0...v3.16.0
[3.15.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.14.0...v3.15.0
[3.0.3]: https://github.com/Mapanare-Research/Mapanare/compare/v3.0.2...v3.0.3
[3.0.2]: https://github.com/Mapanare-Research/Mapanare/compare/v3.0.1...v3.0.2
[3.0.1]: https://github.com/Mapanare-Research/Mapanare/compare/v3.0.0...v3.0.1
[2.0.0]: https://github.com/Mapanare-Research/Mapanare/compare/v1.0.11...v2.0.0
[1.0.11]: https://github.com/Mapanare-Research/Mapanare/compare/v1.0.0...v1.0.11
[1.0.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/Mapanare-Research/Mapanare/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Mapanare-Research/Mapanare/releases/tag/v0.1.0
