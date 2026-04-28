# Third-Party Licenses

This Mapanare distribution may bundle software from third parties.
Their licenses are summarized below; the full license texts are
shipped alongside the binaries inside each release artifact.

## LLVM-MinGW SDK (Windows SDK release only)

**Components bundled:**

- LLVM/Clang compiler driver and support DLLs
- `ld.lld.exe`, `llvm-ar.exe`, `llvm-ranlib.exe`, `llvm-strip.exe`
- MinGW-w64/UCRT Windows headers, startup objects, import libraries,
  and runtime libraries
- compiler-rt builtins for `x86_64-w64-mingw32`
- `libmapanare_rt.a`, built from Mapanare's native runtime sources
  during release packaging

**Bundle location inside ZIP:** `mapanare/sdk/`

**Version:** LLVM-MinGW `20260421` with LLVM `22.1.4`, UCRT x86_64
target.

**Licenses:**

- LLVM Project components: Apache License 2.0 with LLVM Exception.
- MinGW-w64 runtime/import libraries and headers: see the upstream
  MinGW-w64 license texts shipped under
  `mapanare/sdk/x86_64-w64-mingw32/share/mingw32/`.
- winpthreads runtime components: see the upstream winpthreads license
  text in the same SDK license directory.

**License text:** see `mapanare/sdk/LICENSE.TXT` and
`mapanare/sdk/x86_64-w64-mingw32/share/mingw32/COPYING*` inside the
Windows SDK ZIP. Upstream source and license references:

- <https://github.com/mstorsjo/llvm-mingw/releases/tag/20260421>
- <https://github.com/mstorsjo/llvm-mingw>
- <https://github.com/llvm/llvm-project/tree/llvmorg-22.1.4>
- <https://github.com/mingw-w64/mingw-w64>

Mapanare redistributes the LLVM-MinGW SDK files unmodified except for
selecting a smaller x86_64/UCRT subset for the release ZIP. The LLVM
Exception permits combining LLVM's output with non-Apache-licensed code
without copyleft propagation. Mapanare-emitted binaries that pass
through clang/lld are not subject to LLVM's license.

## Mapanare itself

Mapanare is licensed under the [Mapanare LICENSE](../LICENSE) in the
project root. The Mapanare runtime (`runtime/native/`) is statically
linked into compiled output and shares Mapanare's license.
