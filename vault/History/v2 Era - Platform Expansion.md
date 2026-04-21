---
era: v2
versions: v2.0.0 - v2.2.0
theme: Platform Expansion
releases: 4
tests_end: 4465
---

# v2 Era -- Platform Expansion

Four releases. From "LLVM on Linux" to every device and every accelerator.

## Summary

[[v2.0.0]] shipped the WebAssembly backend (MIR to WAT, WASI support, JS bridge, wasm-ld multi-module linking), GPU compute (CUDA Driver API + Vulkan via dlopen -- no compile-time SDK dependency), and mobile targets (iOS ARM64, Android ARM64, Android x86_64). Nine cross-compilation targets total.

[[v2.0.1]] immediately fixed 40 review issues including a security bug (`system()` call in SPIR-V compilation). [[v2.1.0]] validated stage2 IR -- `llvm-as` accepts the IR produced by mnc-stage1 compiling itself, with 8 root causes fixed. [[v2.2.0]] added Valgrind-based crash diagnostics with automatic struct field offset mapping and produced a 3.8 MB mnc-stage2 ELF binary.

4,465+ tests by end of era.

## Versions

| Version | Highlights |
|---------|------------|
| **v2.0.0** | WASM backend (WAT, WASI, JS bridge, wasm-ld), GPU compute (CUDA + Vulkan), mobile targets (iOS, Android), Python backend deprecated, 4,465+ tests |
| **v2.0.1** | Trust restoration: WASM correctness, GPU security (remove `system()`), toolchain honesty, silent failure elimination |
| **v2.1.0** | Stage2 IR validates (`llvm-as`), 8 root causes fixed, mnc-stage2 reaches lowerer |
| **v2.2.0** | Valgrind crash diagnostics, struct field offset mapping, PHI type recovery, mnc-stage2 binary (3.8 MB ELF) |

## Headline Technologies

- **WebAssembly emitter**: `emit_wasm.py` (~2,785 lines), MIR to WAT text format
- **WASM linker**: wasm-ld integration for multi-module linking, memory layout, import/export
- **WASI support**: file I/O, environment, clock, random via WASI preview 1
- **GPU compute**: CUDA Driver API + Vulkan loaded dynamically at runtime (dlopen, no SDK needed)
- **MIR GpuKernel metadata**: device, PTX/SPIR-V source, grid/block config
- **Mobile runtime**: cooperative agent scheduler, epoll event loop, smaller defaults (4KB arenas, 256-slot ring buffers, 64-slot agent queues)
- **String interning cap**: 4K entries on mobile vs 64K on desktop
- **Valgrind crash diagnostics**: automatic struct field offset mapping

## Key Decisions

1. **GPU via dlopen.** No compile-time SDK dependency means anyone can build the compiler. GPU is opt-in at runtime. This was the right call -- validated by every subsequent version.
2. **WASM needs its own memory model.** Linear memory with bump allocation, not arena-based like the C runtime.
3. **Mobile needs smaller defaults.** 4KB arenas, 256-slot ring buffers, 1ms signal batch vs desktop defaults.

## Lessons Learned

- Review-then-fix loop works at scale. v2.0.1 immediately fixed 40 review issues including a security vulnerability.
- Self-compilation bugs are systemic. Nested if-expression PHI type mismatches, Python lowerer control flow bugs, and COW cloning issues all compound.
- Fixed-point is the hardest milestone. Started in v1.0.6, still in progress through v2.2.0. The compiler's own complexity is the challenge. It would not be achieved until [[v3 Era - Syntax Revolution|v3.3.0]].

## Test Growth

4,465+ tests (major jump from v1's ~3,700 -- WASM, GPU, and mobile test suites added)

## See Also

- [[v1 Era - Stability]] -- previous era
- [[Timeline]] -- full project history
- [[v3 Era - Syntax Revolution]] -- next era
