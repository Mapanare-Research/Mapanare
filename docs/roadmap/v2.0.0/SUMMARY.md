# v2.0.0 Summary — "Beyond the Machine"

**Status:** Not Started
**Theme:** GPU compute, WebAssembly backend, mobile cross-compilation, Python backend removal

---

## Phase Status

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|-----------------|
| 1 | GPU Backend (CUDA + Vulkan) | `Not Started` | C runtime GPU module, PTX emitter, SPIR-V emitter, `@gpu`/`@cuda`/`@vulkan` annotations, Tensor in LLVM |
| 2 | WebAssembly Backend | `Not Started` | `emit_wasm.py`, wasm32/wasm32-wasi targets, linear memory manager, JS bridge, WASI support, wasm-ld linking |
| 3 | Mobile Targets | `Not Started` | iOS (aarch64-apple-ios) cross-compilation, Android (aarch64/x86_64) cross-compilation, mobile runtime tuning |
| 4 | Python Backend Deprecation | `Not Started` | Deprecation warnings, migration guide, archive Python stdlib, archive bootstrap |
| 5 | Integration & Testing | `Not Started` | GPU benchmarks, WASM playground, 9-target CI matrix, mobile app examples |

---

## What shipped

_(nothing yet — v2.0.0 work has not started)_

## What's in progress

_(nothing yet)_

## What's remaining

- **GPU backend:** C runtime GPU module with dlopen for CUDA and Vulkan, PTX kernel emitter, SPIR-V compute emitter, GPU memory management, `@gpu`/`@cuda`/`@vulkan` annotation lowering, Tensor type in LLVM codegen
- **WASM backend:** New `emit_wasm.py` MIR-to-WAT emitter, wasm32-unknown-unknown and wasm32-wasi targets, WASM linear memory arena, JS bridge for browser DOM/fetch, WASI shims for server-side, wasm-ld integration
- **Mobile targets:** iOS cross-compilation (ARM64, static library for Xcode), Android cross-compilation (ARM64 + x86_64 emulator, shared library for JNI), reduced memory defaults, mobile-specific runtime (lazy init, smaller arena, cooperative agents)
- **Python deprecation:** Deprecation warnings in Python emitters, `docs/migration/python-to-llvm.md` guide, archive all `.py` stdlib modules, archive `bootstrap/` directory, remove Python backend from CI
- **Testing & integration:** GPU tensor benchmarks (CUDA vs CPU), native WASM browser playground (replace Pyodide), cross-compilation CI for all 9 targets, iOS/Android example apps, WASM browser/edge examples

---

## Key metrics

| Metric | Value |
|--------|-------|
| New targets added | 5 (wasm32, wasm32-wasi, aarch64-apple-ios, aarch64-linux-android, x86_64-linux-android) |
| Total targets | 9 |
| New emitters | 3 (WASM, PTX, SPIR-V) |
| New C runtime modules | 4 (GPU, CUDA, Vulkan, WASM shim) |
| Python files archived | 7 (stdlib) + 22 (bootstrap) |
| Phases | 5 |

---

## Prerequisites

| Dependency | Required For | Min Version |
|------------|-------------|-------------|
| CUDA Toolkit | GPU (CUDA) | 12.0+ |
| Vulkan SDK | GPU (Vulkan) | 1.3+ |
| wasm-ld | WASM linking | LLVM 17+ |
| wasmtime | WASI testing | 15.0+ |
| Android NDK | Android targets | r26+ (API 34) |
| Xcode | iOS target | 15.0+ |
