---
severity: critical
found: "[[v4.26.0]]"
fixed: "[[v4.27.0]]"
status: fixed
tags: [bug, critical, runtime, linker, fpic]
---

# Runtime Not Compiled with -fPIC

`libmapanare_rt.a` was compiled without `-fPIC`, causing `dlopen` failures when the runtime was loaded into position-independent executables or shared libraries. On systems with ASLR (effectively all modern Linux), linking against the static runtime from a shared object produced relocation errors at load time.

## Root Cause
The Makefile for `runtime/native/` used plain `gcc -c` without `-fPIC`. The static library worked fine for fully-static executables but broke when any downstream consumer needed position-independent code, including the `dlopen`-based GPU and FFI paths.

## Fix
Added `-fPIC` to all `runtime/native/` compilation targets in the Makefile. Verified that `libmapanare_rt.a` can be linked into both static binaries and shared objects. Fixed in v4.27.0.
