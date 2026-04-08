# v2 — Platform Expansion

**Era:** v2.0.0 through v2.2.0
**Theme:** Every device, every accelerator — GPU, WASM, mobile, self-compilation

---

## Goal

Expand from "LLVM on Linux" to a multi-platform compiler: WebAssembly for browsers, GPU compute for accelerators, mobile targets for iOS/Android. Deprecate and remove the Python backend. Achieve self-hosted fixed-point (the compiler compiles itself to produce an identical binary).

## Headline Techs

- WebAssembly backend: MIR -> WAT, WASI support, JS bridge, wasm-ld multi-module linking
- GPU compute: CUDA Driver API + Vulkan via dlopen, PTX/SPIR-V codegen, @gpu/@cuda/@vulkan annotations
- Cross-compilation: 9 targets (Linux x64, macOS ARM64, Windows x64, wasm32, wasm32-wasi, iOS, Android ARM64, Android x86_64)
- Mobile runtime: cooperative scheduler, epoll event loop, string interning cap, memory profiling
- Self-compilation: stage2 IR validates, mnc-stage2 binary produced (3.8 MB ELF)
- Valgrind-based crash diagnostics with struct field offset mapping

## Versions

| Version | Codename | Highlights |
|---------|----------|------------|
| **v2.0.0** | Beyond the Machine | WASM backend (WAT, WASI, JS bridge, wasm-ld), GPU compute (CUDA + Vulkan), mobile targets (iOS, Android), Python backend deprecated, playground dual-mode, 4,465+ tests |
| **v2.0.1** | Trust Restoration | Fix review blockers: WASM correctness, GPU security (remove system()), toolchain honesty, silent failure elimination |
| **v2.1.0** | Self-Compilation Progress | Stage2 IR validates (llvm-as), 8 root causes fixed, mnc-stage2 reaches lowerer |
| **v2.2.0** | Stage2 Debugging | Valgrind-based crash diagnostics, struct field offset mapping, PHI type recovery, mnc-stage2 binary (3.8 MB) |

## Key Features Delivered

- WebAssembly emitter: emit_wasm.py (~2,785 lines), MIR -> WAT text format
- WASM linker: wasm-ld integration for multi-module linking, memory layout, import/export
- WASI support: file I/O, environment, clock, random via WASI preview 1
- GPU compute: CUDA Driver API + Vulkan compute loaded dynamically (no compile-time SDK dependency)
- MIR GpuKernel metadata with device, PTX/SPIR-V source, grid/block config
- LLVM codegen: PTX string embedding + cuModuleLoadData/cuLaunchKernel
- Mobile runtime: cooperative agent scheduler, epoll event loop, smaller defaults for constrained devices
- 5 new cross-compilation targets (9 total)
- CI matrix expanded: WASM + Android CI jobs
- Self-compilation pipeline: stage1 -> stage2 -> stage3, approaching fixed-point
- Valgrind-based crash diagnostics with automatic struct field offset mapping
- Python backends formally deprecated

## Lessons Learned

1. **GPU via dlopen is the right call** — no compile-time SDK dependency means anyone can build the compiler; GPU is opt-in at runtime
2. **WASM needs its own memory model** — linear memory with bump allocation, not arena-based like the C runtime
3. **Mobile needs smaller defaults** — 4KB arenas, 256-slot ring buffers, 64-slot agent queues, 1ms signal batch vs desktop defaults
4. **Self-compilation bugs are systemic** — nested if-expression PHI type mismatches, Python lowerer control flow bugs, COW cloning issues all compound
5. **Review-then-fix loop** — v2.0.1 immediately fixed 40 review issues including a security bug (system() call in SPIR-V compilation)
6. **Fixed-point is the hardest milestone** — started in v1.0.6, still in progress through v2.2.0; the compiler's own complexity is the challenge

## Test Growth

4,465+ tests (major jump from v1.x's ~3,700 — WASM, GPU, and mobile test suites added)
