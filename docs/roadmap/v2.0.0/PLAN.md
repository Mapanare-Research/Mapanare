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
| 1 | GPU Backend (CUDA + Vulkan) | `Not Started` | X-Large | WSL/Linux |
| 2 | WebAssembly Backend | `Not Started` | X-Large | Any |
| 3 | Mobile Targets | `Not Started` | Large | macOS + Linux |
| 4 | Python Backend Deprecation | `Not Started` | Medium | Any |
| 5 | Integration & Testing | `Not Started` | Large | All |

---

## Phase 1 — GPU Backend (CUDA + Vulkan)
**Status:** `Not Started`
**Effort:** X-Large
**Platform:** WSL/Linux (CUDA), Linux/Windows (Vulkan)

The GPU backend gives Mapanare native access to GPU compute. No Python wrappers,
no NumPy — tensors and annotated functions compile to GPU kernels that launch
from the C runtime via dlopen.

### 1.1 C Runtime GPU Module

- [ ] `runtime/native/mapanare_gpu.h` — GPU abstraction API (init, alloc, free, copy, launch)
- [ ] `runtime/native/mapanare_gpu.c` — Dispatcher: detects CUDA/Vulkan at runtime via dlopen
- [ ] `runtime/native/mapanare_cuda.c` — CUDA backend: `libcuda.so` / `nvcuda.dll` via dlopen
  - [ ] `cuInit`, `cuDeviceGet`, `cuCtxCreate`, `cuMemAlloc`, `cuMemcpyHtoD/DtoH`
  - [ ] `cuModuleLoadData`, `cuModuleGetFunction`, `cuLaunchKernel`
- [ ] `runtime/native/mapanare_vulkan.c` — Vulkan compute backend: `libvulkan.so` via dlopen
  - [ ] Instance/device creation, compute queue selection
  - [ ] Buffer allocation (`VK_BUFFER_USAGE_STORAGE_BUFFER_BIT`)
  - [ ] SPIR-V shader module loading, compute pipeline creation
  - [ ] Command buffer recording and queue submission
- [ ] `build_gpu.py` — Build script for GPU runtime (detects CUDA/Vulkan availability)
- [ ] Tests: GPU init, memory alloc/free, host-device copy, error handling when no GPU

### 1.2 CUDA PTX Kernel Compilation

- [ ] PTX emitter in `mapanare/emit_ptx.py` — MIR → PTX string for CUDA kernels
  - [ ] Thread indexing: `threadIdx.x`, `blockIdx.x`, `blockDim.x`
  - [ ] Shared memory declarations
  - [ ] Basic arithmetic, control flow, memory load/store
  - [ ] Kernel entry point with `.entry` directive
- [ ] `@cuda` annotation: marks a function as a CUDA kernel
  - [ ] Semantic checker validates kernel signature (no return value, args are tensors/scalars)
  - [ ] Lowering emits MIR with `GpuKernel` metadata
  - [ ] LLVM emitter generates PTX string constant + `cuModuleLoadData` + `cuLaunchKernel` call
- [ ] Launch configuration: `kernel<<<blocks, threads>>>(args)` syntax or `launch(kernel, grid, block, args)`
- [ ] Tests: PTX generation for vector add, matrix multiply, reduction

### 1.3 Vulkan SPIR-V Compute Pipeline

- [ ] SPIR-V emitter in `mapanare/emit_spirv.py` — MIR → SPIR-V binary for Vulkan compute shaders
  - [ ] SPIR-V header, capability declarations (Shader, Int64, Float64)
  - [ ] `OpEntryPoint GLCompute`, `OpExecutionMode LocalSize`
  - [ ] Storage buffer bindings, push constants
  - [ ] Basic ALU ops, control flow
- [ ] `@vulkan` annotation: marks a function as a Vulkan compute shader
  - [ ] Same validation as `@cuda` but targets SPIR-V output
  - [ ] LLVM emitter generates SPIR-V blob constant + Vulkan pipeline setup calls
- [ ] Tests: SPIR-V generation, compute dispatch, buffer readback

### 1.4 GPU Memory Management

- [ ] `GpuBuffer` type in the type system — represents device-side memory
- [ ] `gpu_alloc(size: Int) -> GpuBuffer` — allocate device memory
- [ ] `gpu_free(buf: GpuBuffer)` — free device memory
- [ ] `gpu_copy_to(src: List<T>, dst: GpuBuffer)` — host → device
- [ ] `gpu_copy_from(src: GpuBuffer, dst: List<T>)` — device → host
- [ ] Automatic copy insertion for `@gpu` functions (copy args to device, launch, copy results back)
- [ ] Tests: alloc/free cycle, copy correctness, double-free detection

### 1.5 GPU Annotation Lowering

- [ ] `@gpu` — auto-selects CUDA or Vulkan based on runtime detection
- [ ] `@cuda` — forces CUDA backend (error if unavailable)
- [ ] `@vulkan` — forces Vulkan backend (error if unavailable)
- [ ] `@metal` — reserved for future macOS/iOS Metal support (not implemented in v2.0.0)
- [ ] Semantic pass validates GPU function constraints:
  - [ ] No heap allocation inside kernels
  - [ ] No string operations
  - [ ] No agent/signal/stream usage
  - [ ] Args must be numeric tensors or scalars
- [ ] MIR lowering: `@gpu` functions become `MirGpuKernel` nodes with backend tag
- [ ] LLVM emitter: generates kernel compilation + launch sequence

### 1.6 Tensor Type in LLVM Codegen

- [ ] `Tensor<T>` as a first-class type in LLVM (not experimental/Python-only)
  - [ ] Struct: `{ T* data, i64* shape, i64 ndim, i64 len, i8 device }` (device: 0=CPU, 1=CUDA, 2=Vulkan)
  - [ ] `tensor_create(shape: List<Int>) -> Tensor<T>` — CPU allocation
  - [ ] `tensor_to_gpu(t: Tensor<T>) -> Tensor<T>` — moves to device
  - [ ] `tensor_to_cpu(t: Tensor<T>) -> Tensor<T>` — moves to host
- [ ] Element-wise operations: add, sub, mul, div (dispatch to GPU kernel if on device)
- [ ] Matrix multiply: `matmul(a: Tensor<Float>, b: Tensor<Float>) -> Tensor<Float>`
- [ ] Reduction: `sum`, `mean`, `max`, `min` over axis
- [ ] Tests: tensor creation, GPU transfer, matmul correctness, reduction accuracy

---

## Phase 2 — WebAssembly Backend
**Status:** `Not Started`
**Effort:** X-Large
**Platform:** Any (output runs in browser or WASI runtime)

A new emitter that produces WebAssembly directly from MIR. Combined with wasm-ld,
this lets Mapanare programs run in browsers, Cloudflare Workers, Deno, and any
WASI-compatible runtime.

### 2.1 WASM Emitter (`emit_wasm.py`)

- [ ] `mapanare/emit_wasm.py` — MIR → WAT (WebAssembly Text Format) emitter
  - [ ] Module structure: types, imports, functions, memory, data, exports
  - [ ] All MIR ops → WASM instructions (i32/i64/f32/f64 arithmetic, control flow)
  - [ ] Function calls (direct + indirect via table)
  - [ ] Local variables, parameters, return values
  - [ ] WAT → WASM binary compilation via `wat2wasm` or built-in encoder
- [ ] CLI integration: `mapanare build --target wasm32 -o output.wasm`
- [ ] Tests: WAT output for all 15 golden test programs

### 2.2 WASM Targets in Compiler

- [ ] `wasm32-unknown-unknown` target in `targets.py` — browser/standalone WASM
- [ ] `wasm32-wasi` target in `targets.py` — WASI-compatible WASM
- [ ] Target selection flows through to emitter choice (LLVM vs WASM)
- [ ] `emit_wasm.py` activated when target is `wasm32*`
- [ ] Tests: target resolution, correct emitter dispatch

### 2.3 WASM Linear Memory Management

- [ ] Arena allocator implemented in WASM (port of C runtime arena)
  - [ ] `memory.grow` for expanding linear memory
  - [ ] Bump allocation with reset
  - [ ] String storage in linear memory (length-prefixed)
  - [ ] List/map heap layout matching C runtime conventions
- [ ] Stack frame management for local variables
- [ ] Tests: allocation, growth, string round-trip, OOM handling

### 2.4 JavaScript Bridge for Browser Integration

- [ ] `stdlib/wasm/js_bridge.mn` — Mapanare-side FFI declarations for JS interop
  - [ ] `js_call(func_name: String, args: List<String>) -> String`
  - [ ] `dom_query(selector: String) -> JsHandle`
  - [ ] `dom_set_text(handle: JsHandle, text: String)`
  - [ ] `dom_on(handle: JsHandle, event: String, callback: Fn())`
  - [ ] `console_log(msg: String)`
  - [ ] `fetch(url: String) -> Result<String, String>`
- [ ] JS glue code generator: produces `.js` loader that instantiates WASM module
  - [ ] Memory sharing between JS and WASM
  - [ ] String marshaling (UTF-8 in linear memory ↔ JS strings)
  - [ ] Callback registration for event handlers
- [ ] Tests: DOM manipulation, fetch, console output, event handling

### 2.5 WASI Support

- [ ] WASI imports for `wasm32-wasi` target:
  - [ ] `fd_write` / `fd_read` — stdout/stderr/file I/O
  - [ ] `args_get` / `args_sizes_get` — CLI argument access
  - [ ] `environ_get` / `environ_sizes_get` — environment variables
  - [ ] `clock_time_get` — time
  - [ ] `proc_exit` — exit code
  - [ ] `path_open` / `fd_close` — filesystem access
- [ ] WASI stdlib shim: `stdlib/wasm/wasi.mn` wraps WASI imports with Mapanare types
- [ ] Tests: hello world on wasmtime, file I/O on wasmer, CLI args on wasm3

### 2.6 wasm-ld Integration

- [ ] Linker invocation: `wasm-ld` for combining multiple `.o` files into final `.wasm`
- [ ] Import/export table management
- [ ] Memory layout: stack size, heap start, data segment placement
- [ ] `--export-all` vs explicit exports for library vs executable mode
- [ ] Tests: multi-module linking, correct export list, memory layout validation

---

## Phase 3 — Mobile Targets
**Status:** `Not Started`
**Effort:** Large
**Platform:** macOS (iOS), Linux (Android)

Cross-compilation to iOS and Android using the existing LLVM pipeline with
mobile-specific target triples and runtime adjustments.

### 3.1 iOS Cross-Compilation (aarch64-apple-ios)

- [ ] `aarch64-apple-ios` target in `targets.py` with iOS 17+ triple
- [ ] Cross-compilation workflow:
  - [ ] Emit LLVM IR with iOS target triple and data layout
  - [ ] Compile to `.o` via `llc` or llvmlite with iOS target
  - [ ] Link with `clang -target aarch64-apple-ios17.0`
- [ ] Xcode integration guide:
  - [ ] Generate `.a` static library for embedding in Swift/ObjC app
  - [ ] C header generation for FFI boundary
  - [ ] `mapanare build --target aarch64-apple-ios --lib -o libmapanare_app.a`
- [ ] Tests: cross-compile hello world, verify Mach-O format, symbol visibility

### 3.2 Android Cross-Compilation (aarch64-linux-android)

- [ ] `aarch64-linux-android` target in `targets.py` with API 34 triple
- [ ] `x86_64-linux-android` target for emulator testing
- [ ] Cross-compilation workflow:
  - [ ] Emit LLVM IR with Android target triple and data layout
  - [ ] Compile to `.o` via `llc` or llvmlite with Android target
  - [ ] Link with NDK clang: `aarch64-linux-android34-clang`
- [ ] Android NDK integration guide:
  - [ ] Generate `.so` shared library for JNI loading
  - [ ] JNI bridge header generation
  - [ ] `mapanare build --target aarch64-linux-android --lib -o libmapanare_app.so`
- [ ] Tests: cross-compile hello world, verify ELF format, JNI loading

### 3.3 Mobile-Specific Runtime Adjustments

- [ ] Reduced default arena size for mobile (4 MB instead of 64 MB)
- [ ] Configurable arena via `MAPANARE_ARENA_SIZE` environment variable
- [ ] No thread pool by default on mobile (opt-in via `MAPANARE_THREADS`)
- [ ] Agent scheduler: cooperative only on mobile (no preemption)
- [ ] Signal batching: smaller batch window for UI responsiveness (1ms vs 16ms)
- [ ] C runtime conditional compilation:
  - [ ] `#ifdef __APPLE__` + `TARGET_OS_IOS` for iOS-specific paths
  - [ ] `#ifdef __ANDROID__` for Android-specific paths
  - [ ] No epoll on iOS (kqueue), no kqueue on Android (epoll)
- [ ] Tests: arena size override, thread pool opt-in, event loop backend selection

### 3.4 Reduced Memory Footprint

- [ ] Profile memory usage of C runtime on mobile targets
- [ ] Lazy initialization of subsystems (don't init thread pool until first agent spawn)
- [ ] Smaller default ring buffer (256 slots instead of 4096)
- [ ] String interning pool with configurable cap
- [ ] Static analysis pass: warn on programs that exceed mobile memory budget
- [ ] Tests: memory usage benchmarks, lazy init verification

---

## Phase 4 — Python Backend Deprecation
**Status:** `Not Started`
**Effort:** Medium
**Platform:** Any

The Python transpiler has been legacy since v0.8.0. v2.0.0 removes it from the
active codebase and archives it for historical reference.

### 4.1 Deprecation Warnings

- [ ] `emit_python.py`: emit deprecation warning on every invocation
  - [ ] `"WARNING: Python backend is deprecated and will be removed in v2.1.0. Use --target to select LLVM or WASM backend."`
- [ ] `emit_python_mir.py`: same deprecation warning
- [ ] CLI: `mapanare run` without `--target` prints migration hint
- [ ] `mapanare check --compat` — new flag that reports Python-only features in user code
- [ ] Tests: deprecation warning appears, `--compat` flag works

### 4.2 Migration Guide

- [ ] `docs/migration/python-to-llvm.md` — comprehensive migration guide
  - [ ] Feature parity checklist (what works on LLVM that didn't before)
  - [ ] Known differences in behavior (floating point, string encoding)
  - [ ] How to update `mapanare.toml` to target LLVM
  - [ ] How to replace Python FFI with C runtime FFI
- [ ] `mapanare migrate` CLI command — automated migration suggestions
  - [ ] Scan source for Python-only patterns
  - [ ] Suggest LLVM-compatible alternatives
- [ ] Tests: migration tool detects known patterns

### 4.3 Remove Python-Only Stdlib Modules

- [ ] Archive `stdlib/http.py` → `archive/stdlib/http.py` (replaced by `stdlib/net/http.mn`)
- [ ] Archive `stdlib/io.py` → `archive/stdlib/io.py` (replaced by native I/O)
- [ ] Archive `stdlib/math.py` → `archive/stdlib/math.py` (replaced by native math)
- [ ] Archive `stdlib/text.py` → `archive/stdlib/text.py` (replaced by `stdlib/text/string_utils.mn`)
- [ ] Archive `stdlib/time.py` → `archive/stdlib/time.py` (replaced by native time)
- [ ] Archive `stdlib/log.py` → `archive/stdlib/log.py` (replaced by native logging)
- [ ] Archive `stdlib/pkg.py` → `archive/stdlib/pkg.py` (replaced by native package manager)
- [ ] Update `stdlib/__init__.py` to remove Python module imports
- [ ] Tests: verify all stdlib tests pass on LLVM backend only

### 4.4 Archive Bootstrap

- [ ] `bootstrap/` directory marked as `ARCHIVED — v0.6.0 snapshot, do not modify`
- [ ] `bootstrap/README.md` updated with archival notice
- [ ] Remove bootstrap from CI matrix (no longer tested)
- [ ] `bootstrap/` excluded from linting and type checking
- [ ] Tests: CI config validates bootstrap is excluded

---

## Phase 5 — Integration & Testing
**Status:** `Not Started`
**Effort:** Large
**Platform:** All

End-to-end validation across all new backends and targets. Benchmarks that prove
the GPU backend is worth using. A browser playground that runs natively. CI that
tests every target triple.

### 5.1 GPU Tensor Benchmarks

- [ ] `benchmarks/gpu/bench_matmul.mn` — matrix multiply: CPU vs CUDA vs Vulkan
  - [ ] 256x256, 1024x1024, 4096x4096 matrices
  - [ ] Report GFLOPS for each backend
- [ ] `benchmarks/gpu/bench_reduction.mn` — sum reduction: CPU vs GPU
- [ ] `benchmarks/gpu/bench_transfer.mn` — host↔device copy bandwidth
- [ ] `benchmarks/gpu/bench_tensor_ops.mn` — element-wise ops throughput
- [ ] Results logged to `benchmarks/results_gpu.json`
- [ ] Auto-generated `benchmarks/GPU_REPORT.md` with comparison tables
- [ ] Tests: benchmark harness runs, results are valid JSON

### 5.2 WASM Browser Playground

- [ ] Replace Pyodide-based playground with native WASM playground
  - [ ] Compile Mapanare compiler to WASM (self-hosted → WASM)
  - [ ] `playground/src/compiler.wasm` — the compiler itself running in browser
  - [ ] User types `.mn` code → compiled in-browser → executed in-browser
  - [ ] No server roundtrip, no Python, fully client-side
- [ ] Update `playground/src/worker.js` to load WASM compiler
- [ ] Update `playground/src/main.js` for new compilation pipeline
- [ ] Update `playground/index.html` with "Powered by WASM" badge
- [ ] Tests: playground compiles and runs hello world in headless browser

### 5.3 Cross-Compilation CI Matrix

- [ ] GitHub Actions matrix expansion:
  - [ ] `x86_64-linux-gnu` — Ubuntu (existing)
  - [ ] `aarch64-apple-macos` — macOS ARM64 runner
  - [ ] `x86_64-windows-msvc` — Windows (existing)
  - [ ] `wasm32-wasi` — compile + run on wasmtime
  - [ ] `wasm32-unknown-unknown` — compile only (no runtime in CI)
  - [ ] `aarch64-apple-ios` — cross-compile only (no device in CI)
  - [ ] `aarch64-linux-android` — cross-compile + Android emulator test
  - [ ] `x86_64-linux-android` — cross-compile + run on Android emulator
- [ ] CI artifacts: upload `.wasm`, `.a`, `.so` for each target
- [ ] Release matrix: build binaries for all 9 targets on tag push
- [ ] Tests: CI workflow validates all targets compile successfully

### 5.4 Mobile App Examples

- [ ] `examples/mobile/ios/` — minimal iOS app embedding Mapanare
  - [ ] Swift wrapper calling Mapanare static library
  - [ ] Agent-based background task example
  - [ ] Signal-driven UI update pattern
- [ ] `examples/mobile/android/` — minimal Android app embedding Mapanare
  - [ ] Kotlin/JNI wrapper calling Mapanare shared library
  - [ ] Agent-based background task example
  - [ ] Signal-driven UI update pattern
- [ ] `examples/wasm/browser/` — standalone browser app
  - [ ] HTML + JS + WASM: interactive counter with signals
  - [ ] DOM manipulation via JS bridge
- [ ] `examples/wasm/cloudflare-worker/` — edge compute example
  - [ ] HTTP handler compiled to WASM, deployed to Cloudflare Workers
- [ ] Tests: examples compile for their respective targets

### 5.5 Documentation

- [ ] `docs/targets.md` — all 9 supported targets with setup instructions
- [ ] `docs/gpu.md` — GPU programming guide (annotations, tensor API, kernel writing)
- [ ] `docs/wasm.md` — WASM guide (browser, WASI, JS bridge)
- [ ] `docs/mobile.md` — mobile guide (iOS, Android, memory tuning)
- [ ] Update `docs/SPEC.md` with GPU, WASM, and mobile additions
- [ ] Update `docs/reference.md` with new CLI flags and annotations
- [ ] Tests: doc links are valid, code examples in docs compile

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
