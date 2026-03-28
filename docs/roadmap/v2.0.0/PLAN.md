# Mapanare v2.0.0 — "Beyond the Machine"

> v1.x gave Mapanare a stable, self-hosted, native compiler with a full stdlib,
> data engine, web framework, crawler, and vulnerability scanner — all in `.mn`,
> all compiled via LLVM, no Python at runtime.
> v2.0.0 breaks the platform boundary. GPU compute via CUDA and Vulkan. WebAssembly
> for browsers and edge runtimes. iOS and Android cross-compilation. And the Python
> backend finally goes away.
>
> Core theme: **Every device. Every accelerator. No Python.**

---

## Scope Rules

1. **GPU is first-class** — `@gpu`, `@cuda`, `@vulkan` annotations lower to real kernel launches, not library wrappers
2. **WASM is a real backend** — `emit_wasm.py` generates WAT/WASM directly from MIR, not transpiled through C or JS
3. **Mobile targets are cross-compiled** — same LLVM pipeline, different target triple; no special runtime
4. **Python backend is removed** — `emit_python.py` and `emit_python_mir.py` are archived, not maintained
5. **C runtime adapts per platform** — GPU module via dlopen (CUDA/Vulkan), WASM shims for browser APIs, mobile-sized arena defaults
6. **Tensor type gets real GPU backing** — `Tensor<T>` maps to device memory, operations dispatch to GPU kernels

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

| Phase | Name | Status | Effort | Platform |
|-------|------|--------|--------|----------|
| 1 | GPU Backend (CUDA + Vulkan) | `Done` | X-Large | WSL/Linux |
| 2 | WebAssembly Backend | `Done` | X-Large | Any |
| 3 | Mobile Targets | `In Progress` | Large | macOS + Linux |
| 4 | Python Backend Deprecation | `Done` | Medium | Any |
| 5 | Integration & Testing | `In Progress` | Large | All |

---

## Phase 1 — GPU Backend (CUDA + Vulkan)
**Status:** `Done`
**Effort:** X-Large
**Platform:** WSL/Linux (CUDA), Linux/Windows (Vulkan)

The GPU backend gives Mapanare native access to GPU compute. No Python wrappers,
no NumPy — tensors and annotated functions compile to GPU kernels that launch
from the C runtime via dlopen.

### 1.1 C Runtime GPU Module

- [x] `runtime/native/mapanare_gpu.h` — GPU abstraction API (init, alloc, free, copy, launch)
- [x] `runtime/native/mapanare_gpu.c` — Dispatcher: detects CUDA/Vulkan at runtime via dlopen
- [x] CUDA backend integrated in `mapanare_gpu.c`: `libcuda.so` / `nvcuda.dll` via dlopen
  - [x] `cuInit`, `cuDeviceGet`, `cuCtxCreate`, `cuMemAlloc`, `cuMemcpyHtoD/DtoH`
  - [x] `cuModuleLoadData`, `cuModuleGetFunction`, `cuLaunchKernel`
- [x] Vulkan compute backend integrated in `mapanare_gpu.c`: `libvulkan.so` via dlopen
  - [x] Instance/device creation, compute queue selection
  - [x] Buffer allocation (`VK_BUFFER_USAGE_STORAGE_BUFFER_BIT`)
  - [x] SPIR-V shader module loading, compute pipeline creation
  - [x] Command buffer recording and queue submission
- [x] Tests: GPU init, memory alloc/free, host-device copy, error handling when no GPU

### 1.2 CUDA PTX Kernel Compilation

- [!] PTX emitter as standalone `mapanare/emit_ptx.py` — Skipped: PTX kernels embedded as string constants in `mapanare_gpu.c` (tensor_add/sub/mul/div/matmul in sm_52 assembly)
- [x] `@cuda` annotation: marks a function as a CUDA kernel
  - [x] Semantic checker validates annotation (single device annotation per function)
  - [x] Lowering emits MIR with `GpuKernel` metadata
  - [x] LLVM emitter generates PTX string constant + `cuModuleLoadData` + `cuLaunchKernel` call
- [x] Launch configuration via `launch(kernel, grid, block, args)` in `stdlib/gpu/kernel.mn`
- [x] Tests: PTX kernel templates, CUDA dispatch tests

### 1.3 Vulkan SPIR-V Compute Pipeline

- [!] SPIR-V emitter as standalone `mapanare/emit_spirv.py` — Skipped: GLSL compute shaders embedded in `mapanare_gpu.c`, compiled to SPIR-V at runtime
- [x] `@vulkan` annotation: marks a function as a Vulkan compute shader
  - [x] Same validation as `@cuda` in semantic pass
  - [x] LLVM emitter generates SPIR-V blob constant + Vulkan pipeline setup calls
- [x] Tests: SPIR-V pipeline tests, Vulkan dispatch tests

### 1.4 GPU Memory Management

- [x] `gpu_buffer_alloc` / `gpu_buffer_free` / `gpu_buffer_upload` / `gpu_buffer_download` in C runtime
- [x] Backend-agnostic device memory allocation (CUDA or Vulkan)
- [x] Host → device and device → host transfers
- [x] CPU fallback when no GPU is available
- [x] Tests: alloc/free cycle, copy correctness, memory transfer patterns

### 1.5 GPU Annotation Lowering

- [x] `@gpu` — auto-selects CUDA or Vulkan based on runtime detection
- [x] `@cuda` — forces CUDA backend (error if unavailable)
- [x] `@vulkan` — forces Vulkan backend (error if unavailable)
- [x] `@metal` — reserved for future macOS/iOS Metal support (not implemented in v2.0.0)
- [x] Semantic pass validates GPU function constraints (max 1 device annotation per function)
- [x] MIR lowering: decorators stored in `MirFunction.decorators`
- [x] LLVM emitter: `@gpu`/`@cuda`/`@vulkan` functions auto-dispatch tensor ops to C runtime GPU calls

### 1.6 Tensor Type — GPU Stdlib

- [x] `stdlib/gpu/tensor.mn` — Tensor struct with shape/ndim/size/device metadata (~700 lines)
  - [x] Creation: `zeros()`, `ones()`, `full()`, `from_list()`, `identity()`
  - [x] Device transfer: `to_device()`
  - [x] Element-wise: `add()`, `sub()`, `mul()`, `div()` (all `@gpu` annotated)
  - [x] Unary: `negate()`, `abs()`, `sqrt()`, `exp()`, `log()`
  - [x] Matrix: `matmul()`, `dot()`, `transpose()`
  - [x] Reduction: `sum()`, `mean()`, `max()`, `min()`
- [x] `stdlib/gpu/device.mn` — Device detection, init, sync (~243 lines)
- [x] `stdlib/gpu/kernel.mn` — Kernel struct, launch config, PTX/SPIR-V loading (~236 lines)
- [x] `experimental/gpu.py` — Python-side GPU detection and dispatch (~922 lines)
- [x] C runtime tensor ops: `cuda_elementwise_op`, `cuda_matmul`, `vulkan_elementwise_op` with CPU fallback
- [x] Tests: tensor creation, GPU transfer, matmul, reduction, kernel tests

**Remaining gaps:**
- [x] LLVM emitter auto-dispatch: `@gpu`-annotated functions now route tensor ops to C runtime GPU calls
- [x] `Tensor<T>` as first-class type in LLVM codegen (`emit_llvm_mir.py` maps `Tensor<T>` → `{T*, i64, i64*, i64}`)

---

## Phase 2 — WebAssembly Backend
**Status:** `Done`
**Effort:** X-Large
**Platform:** Any (output runs in browser or WASI runtime)

A new emitter that produces WebAssembly directly from MIR. Combined with wasm-ld,
this lets Mapanare programs run in browsers, Cloudflare Workers, Deno, and any
WASI-compatible runtime.

### 2.1 WASM Emitter (`emit_wasm.py`)

- [x] `mapanare/emit_wasm.py` — MIR → WAT (WebAssembly Text Format) emitter (~2,245 lines)
  - [x] Module structure: types, imports, functions, memory, data, exports
  - [x] All MIR ops → WASM instructions (i32/i64/f32/f64 arithmetic, control flow)
  - [x] Function calls (direct + indirect via table)
  - [x] Local variables, parameters, return values
  - [x] WAT → WASM binary compilation via `wat2wasm`
- [x] CLI integration: `mapanare emit-wasm <source.mn> [-o OUTPUT] [--binary] [--opt-level 0-3]`
- [x] Tests: 98 test cases covering WAT output for all feature categories

### 2.2 WASM Targets in Compiler

- [x] `wasm32-unknown-unknown` target in `targets.py` — browser/standalone WASM
- [x] `wasm32-wasi` target in `targets.py` — WASI-compatible WASM
- [x] Target selection flows through to emitter choice (LLVM vs WASM)
- [x] `emit_wasm.py` activated when target is `wasm32*`
- [x] Tests: target resolution, correct emitter dispatch (63 target tests)

### 2.3 WASM Linear Memory Management

- [x] Bump allocator implemented in WASM
  - [x] `memory.grow` for expanding linear memory
  - [x] Bump allocation with reset
  - [x] String storage in linear memory (length-prefixed)
  - [x] List/map heap layout matching C runtime conventions
- [x] Stack frame management for local variables
- [x] Tests: allocation, growth, string round-trip

### 2.4 JavaScript Bridge for Browser Integration

- [x] `stdlib/wasm/bridge.mn` — Mapanare-side FFI declarations for JS interop (~487 lines)
  - [x] `js_call(func_name: String, args: List<String>) -> String`
  - [x] `dom_query(selector: String) -> JsHandle`
  - [x] `dom_set_text(handle: JsHandle, text: String)`
  - [x] `dom_on(handle: JsHandle, event: String, callback: Fn())`
  - [x] `console_log(msg: String)`, `console_warn`, `console_error`
  - [x] `fetch(url: String) -> Result<String, BridgeError>` with custom method/body/headers
  - [x] Timers: `set_timeout`, `set_interval`, `clear_interval`
  - [x] Error handling: `BridgeError` enum with 5 variants
- [x] JS glue code: `playground/src/wasm-runtime.js` (~513 lines)
  - [x] Memory sharing between JS and WASM (BumpAllocator class)
  - [x] String marshaling (UTF-8 in linear memory ↔ JS strings)
  - [x] Callback registration for event handlers (HandleRegistry class)
  - [x] 40+ import handler functions (DOM, fetch, math, tensors)
- [x] `playground/src/wasm-worker.js` — Web Worker host (~305 lines)
- [x] Tests: stdlib parse validation, signature checks

### 2.5 WASI Support

- [x] `stdlib/wasm/runtime.mn` — WASI stdlib shim wrapping WASI imports (~307 lines)
  - [x] `fd_write` / `fd_read` — stdout/stderr/file I/O
  - [x] `args_get` / `args_sizes_get` — CLI argument access (`wasi_args()`)
  - [x] `environ_get` / `environ_sizes_get` — environment variables (`wasi_environ()`)
  - [x] `clock_time_get` — time (`wasi_clock_ns()`)
  - [x] `proc_exit` — exit code (`wasi_exit()`)
  - [x] `path_open` / `fd_close` — filesystem access (`wasi_open`, `wasi_close`)
- [x] JS runtime WASI preview 1 stubs (browser sandbox limitations apply)
- [x] Tests: WASI stdlib parse validation

### 2.6 wasm-ld Integration

- [x] Linker configured: `targets.py` sets `linker="wasm-ld"` for both WASM targets
- [x] Linker invocation: `wasm-ld` for combining multiple `.o` files into final `.wasm`
- [x] Import/export table management
- [x] Memory layout: stack size, heap start, data segment placement
- [x] `--export-all` vs explicit exports for library vs executable mode
- [x] Tests: multi-module linking, correct export list, memory layout validation

### 2.7 WASM Examples

- [x] `examples/wasm/hello.mn` — Basic arithmetic, strings, fibonacci, control flow
- [x] `examples/wasm/dom_app.mn` — Interactive counter with DOM manipulation, events
- [x] `examples/wasm/wasi_app.mn` — Factorial, prime sieve, WASI environment access

**Remaining gaps:**
- [x] Signal computed/subscribe reactivity in WASM (compute fn call + subscriber list management)
- [x] Stream operators in WASM (eager evaluation: map, filter, take, skip, collect, fold)
- [x] Closure indirect call dispatch (`call_indirect` via function table with env_ptr)
- [x] `wasm-ld` multi-module linking

---

## Phase 3 — Mobile Targets
**Status:** `In Progress`
**Effort:** Large
**Platform:** macOS (iOS), Linux (Android)

Cross-compilation to iOS and Android using the existing LLVM pipeline with
mobile-specific target triples and runtime adjustments.

### 3.1 iOS Cross-Compilation (aarch64-apple-ios)

- [x] `aarch64-apple-ios` target in `targets.py` with iOS 17+ triple
- [x] Cross-compilation workflow:
  - [x] Emit LLVM IR with iOS target triple and data layout (via `--target aarch64-apple-ios`)
  - [x] Compile to `.o` via llvmlite with iOS target
  - [x] Link with `clang -target aarch64-apple-ios17.0` or `libtool -static` for `.a`
- [x] Xcode integration guide:
  - [x] Generate `.a` static library: `mapanare build --target aarch64-apple-ios --lib -o libmapanare_app.a`
  - [x] C bridging header for FFI boundary (`examples/mobile/ios/mapanare_app-Bridging-Header.h`)
  - [x] Swift wrapper example (`examples/mobile/ios/ViewController.swift`)
- [ ] Tests: cross-compile hello world, verify Mach-O format, symbol visibility (requires macOS)

### 3.2 Android Cross-Compilation (aarch64-linux-android)

- [x] `aarch64-linux-android` target in `targets.py` with API 34 triple
- [x] `x86_64-linux-android` target for emulator testing
- [x] Cross-compilation workflow:
  - [x] Emit LLVM IR with Android target triple and data layout (via `--target aarch64-linux-android`)
  - [x] Compile to `.o` via llvmlite with Android target
  - [x] Link with NDK clang: `aarch64-linux-android34-clang` (with `-shared` for `.so`)
- [x] Android NDK integration guide:
  - [x] Generate `.so` shared library: `mapanare build --target aarch64-linux-android --lib -o libmapanare_app.so`
  - [x] Kotlin JNI wrapper example (`examples/mobile/android/MainActivity.kt`)
  - [x] Mapanare app example (`examples/mobile/android/app.mn`)
- [ ] Tests: cross-compile hello world, verify ELF format, JNI loading (requires NDK)

### 3.3 Mobile-Specific Runtime Adjustments

- [x] `runtime/native/mapanare_platform.h` — Platform detection and tunable defaults
- [x] Reduced default arena size for mobile (4 KB blocks vs 8 KB, via `MAPANARE_DEFAULT_ARENA_BLOCK`)
- [x] Configurable defaults via compile-time `-D` flags (all `MAPANARE_DEFAULT_*` macros)
- [x] Smaller agent queues on mobile (64 slots vs 256, via `MAPANARE_DEFAULT_AGENT_QUEUE`)
- [x] Signal batching: smaller batch window for UI responsiveness (1ms vs 16ms, via `MAPANARE_DEFAULT_BATCH_MS`)
- [x] C runtime conditional compilation:
  - [x] `#ifdef __APPLE__` + `TARGET_OS_IOS` for iOS-specific paths
  - [x] `#ifdef __ANDROID__` for Android-specific paths
- [x] Agent scheduler: cooperative only on mobile (no preemption)
- [x] Event loop backend selection: no epoll on iOS (kqueue), no kqueue on Android (epoll)
- [x] Tests: arena size override, thread pool opt-in, event loop backend selection

### 3.4 Reduced Memory Footprint

- [x] Smaller default ring buffer on mobile (256 slots vs 1024, via `MAPANARE_DEFAULT_RING_CAPACITY`)
- [x] Profile memory usage of C runtime on mobile targets
- [x] Lazy initialization of subsystems (`mapanare_ensure_pool()` — thread pool created on first agent spawn via atomic CAS)
- [x] String interning pool with configurable cap
- [ ] Static analysis pass: warn on programs that exceed mobile memory budget
- [x] Tests: memory usage benchmarks, lazy init verification

---

## Phase 4 — Python Backend Deprecation
**Status:** `Done`
**Effort:** Medium
**Platform:** Any

The Python transpiler has been legacy since v0.8.0. v2.0.0 removes it from the
active codebase and archives it for historical reference.

### 4.1 Deprecation Warnings

- [x] `emit_python.py`: emit deprecation warning on every invocation
- [x] `emit_python_mir.py`: emit deprecation warning on every invocation
- [x] CLI: `mapanare run` now uses LLVM/JIT directly (no Python transpiler)
- [x] `mapanare test` now uses LLVM/JIT directly (no Python transpiler)
- [!] `mapanare check --compat` — Skipped: no external users yet

### 4.2 Migration Guide

- [!] `docs/migration/python-to-llvm.md` — Skipped: no external users yet, project is pre-release
- [!] `mapanare migrate` CLI command — Skipped: no external users yet
- [!] `mapanare check --compat` — Skipped: no external users yet

### 4.3 Remove Python-Only Stdlib Modules

- [x] Archive `stdlib/http.py` → `archive/stdlib/http.py` (replaced by `stdlib/net/http.mn`)
- [x] Archive `stdlib/io.py` → `archive/stdlib/io.py` (replaced by native I/O)
- [x] Archive `stdlib/math.py` → `archive/stdlib/math.py` (replaced by native math)
- [x] Archive `stdlib/text.py` → `archive/stdlib/text.py` (replaced by `stdlib/text/string_utils.mn`)
- [x] Archive `stdlib/time.py` → `archive/stdlib/time.py` (replaced by native time)
- [x] Archive `stdlib/log.py` → `archive/stdlib/log.py` (replaced by native logging)
- [x] Archive `stdlib/pkg.py` → `archive/stdlib/pkg.py` (replaced by native package manager)
- [x] Update `stdlib/__init__.py` — updated docstring, no Python imports to remove
- [x] Tests: verify all stdlib tests pass on LLVM backend only (all 21+ test files use `skipif(not HAS_LLVMLITE)`)

### 4.4 Archive Bootstrap

- [x] `bootstrap/` directory marked as `ARCHIVED — v0.6.0 snapshot, do not modify`
- [x] `bootstrap/README.md` updated with archival notice
- [x] Remove bootstrap from CI matrix (not explicitly referenced in CI)
- [x] `bootstrap/` excluded from linting and type checking (`pyproject.toml`: ruff, black, mypy)
- [x] Tests: CI config validates bootstrap is excluded

---

## Phase 5 — Integration & Testing
**Status:** `In Progress`
**Effort:** Large
**Platform:** All

End-to-end validation across all new backends and targets. Benchmarks that prove
the GPU backend is worth using. A browser playground that runs natively. CI that
tests every target triple.

### 5.1 GPU Tensor Benchmarks

- [x] `benchmarks/gpu/bench_matmul.py` — matrix multiply: CPU (numpy) vs CUDA
  - [x] 256x256, 512x512, 1024x1024, 2048x2048, 4096x4096 matrices
  - [x] Report GFLOPS for each backend
- [x] `benchmarks/gpu/bench_reduction.py` — sum reduction: CPU vs GPU (shared memory kernel)
- [x] `benchmarks/gpu/bench_transfer.py` — host↔device copy bandwidth (1MB–256MB)
- [x] `benchmarks/gpu/bench_elementwise.py` — element-wise ops throughput (add, mul, scale)
- [x] `benchmarks/gpu/_cuda_helpers.py` — CUDA Driver API wrapper via ctypes (dlopen)
- [x] `benchmarks/gpu/_bench_utils.py` — Shared measurement utilities (warmup, IQR, CV)
- [x] Results logged to `benchmarks/results_gpu.json`
- [x] Auto-generated `benchmarks/GPU_REPORT.md` with comparison tables
- [x] `benchmarks/gpu/run_gpu_benchmarks.py` — Runner aggregating all suites

### 5.2 WASM Browser Playground

- [x] WASM runtime integration exists (`playground/src/wasm-runtime.js`, `wasm-worker.js`)
- [~] Replace Pyodide-based playground with native WASM playground
  - [ ] Compile Mapanare compiler to WASM (self-hosted → WASM) — blocked on cross-module compilation
  - [ ] `playground/src/compiler.wasm` — the compiler itself running in browser
  - [x] User types `.mn` code → compiled in-browser → executed in-browser (via Pyodide+WASM hybrid)
  - [~] No server roundtrip, no Python, fully client-side — Pyodide still used for compilation, WASM for execution
- [x] Update `playground/src/worker.js` to load WASM compiler (dual-mode: Pyodide compile → WASM execute)
- [x] Update `playground/src/main.js` for new compilation pipeline (shows backend in status)
- [x] Update `playground/index.html` with "Powered by WASM" badge
- [ ] Tests: playground compiles and runs hello world in headless browser

### 5.3 Cross-Compilation CI Matrix

- [x] GitHub Actions matrix expansion:
  - [x] `x86_64-linux-gnu` — Ubuntu (existing)
  - [ ] `aarch64-apple-macos` — macOS ARM64 runner (deferred: needs macOS runner)
  - [x] `x86_64-windows-msvc` — Windows (existing in publish workflow)
  - [x] `wasm32-wasi` — compile + run on wasmtime
  - [x] `wasm32-unknown-unknown` — compile only (no runtime in CI)
  - [ ] `aarch64-apple-ios` — cross-compile only (deferred: needs macOS runner)
  - [x] `aarch64-linux-android` — cross-compile with NDK
  - [x] `x86_64-linux-android` — cross-compile with NDK
- [x] CI artifacts: upload `.wasm`, `.o` for WASM and Android targets
- [ ] Release matrix: build binaries for all 9 targets on tag push
- [x] Tests: CI workflow validates all targets compile successfully

### 5.4 Mobile App Examples

- [x] `examples/mobile/ios/` — minimal iOS app embedding Mapanare
  - [x] Swift wrapper calling Mapanare static library (`ViewController.swift`)
  - [x] Agent-based background task example (`app.mn`)
  - [x] C bridging header (`mapanare_app-Bridging-Header.h`)
- [x] `examples/mobile/android/` — minimal Android app embedding Mapanare
  - [x] Kotlin/JNI wrapper calling Mapanare shared library (`MainActivity.kt`)
  - [x] Agent-based background task example (`app.mn`)
  - [x] Build instructions (`README.md`)
- [x] `examples/wasm/browser/` — standalone browser examples
  - [x] `hello.mn` — arithmetic, strings, fibonacci
  - [x] `dom_app.mn` — interactive counter with DOM, events
  - [x] `wasi_app.mn` — WASI environment access
- [x] `examples/wasm/cloudflare-worker/` — edge compute example
  - [x] HTTP handler compiled to WASM (`worker.mn`), JS glue (`worker.js`), Wrangler config
- [x] Tests: examples compile for their respective targets (`tests/test_examples.py`)

### 5.5 Documentation

- [x] Website: `Targets.tsx` — all 9 supported targets with setup instructions
- [x] Website: `GPU.tsx` — GPU programming guide (annotations, tensor API, kernel writing)
- [x] Website: `WebAssembly.tsx` — WASM guide (browser, WASI, JS bridge)
- [x] Website: `Mobile.tsx` — mobile guide (iOS, Android, memory tuning)
- [x] Website: sidebar "Platform" section and routing for all 4 new pages
- [x] Update `docs/SPEC.md` with GPU (§23), WASM (§24), and mobile (§25) sections
- [x] Update `docs/reference.md` with GPU decorators, `emit-wasm`, `--lib`/`--target` flags, tensor ops
- [x] Tests: doc links are valid, code examples in docs compile (`tests/test_doc_links.py`)

---

## Dependencies & Prerequisites

| Dependency | Required For | Version |
|------------|-------------|---------|
| CUDA Toolkit | Phase 1 (CUDA) | 12.0+ |
| Vulkan SDK | Phase 1 (Vulkan) | 1.3+ |
| wasm-ld | Phase 2 (WASM linking) | LLVM 17+ |
| wasmtime | Phase 2 (WASI testing) | 15.0+ |
| Android NDK | Phase 3 (Android) | r26+ (API 34) |
| Xcode | Phase 3 (iOS) | 15.0+ |
| llvmlite | All phases | 0.43+ |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| CUDA dlopen fails on non-NVIDIA systems | Phase 1 blocked | Vulkan fallback, graceful degradation |
| WASM emitter is large effort | Phase 2 delayed | Start with WAT text format, binary encoding later |
| iOS cross-compilation needs macOS CI | Phase 3 CI gaps | Cross-compile only, no device testing |
| Self-hosted compiler too large for WASM | Phase 5 playground | Ship pre-compiled stdlib, compile user code only |
| Android emulator flaky in CI | Phase 5 CI gaps | x86_64 emulator target, retry policy |

---

## Success Criteria

1. **GPU:** `@cuda` matrix multiply runs on NVIDIA GPU, produces correct result, 10x faster than CPU
2. **WASM:** All 15 golden tests compile to `.wasm` and run on wasmtime
3. **Mobile:** Hello world cross-compiles to `.a` (iOS) and `.so` (Android) with correct format
4. **Python removal:** Zero Python files in `stdlib/` (all archived), CI runs without Python backend
5. **Playground:** Browser playground compiles and runs `.mn` code without server roundtrip
6. **CI:** All 9 targets build successfully in GitHub Actions
