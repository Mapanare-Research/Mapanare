# Third-Party Licenses

This Mapanare distribution may bundle software from third parties.
Their licenses are summarized below; the full license texts are
shipped alongside the binaries inside each release artifact.

## LLVM Project (Windows release only)

**Components bundled:**

- `clang.exe` — IR compiler + linker driver
- `lld-link.exe` — Microsoft-style linker
- `LLVM-C.dll` — core LLVM library
- `clang_rt.builtins-x86_64.lib` — compiler-rt builtins

**Bundle location inside ZIP:** `mapanare/llvm/`

**Version:** 18.1.8

**License:** Apache License 2.0 with LLVM Exception

**License text:** see `mapanare/llvm/LICENSE.TXT` (shipped inside the
ZIP); upstream copy at
<https://github.com/llvm/llvm-project/blob/llvmorg-18.1.8/LICENSE.TXT>.

The LLVM project is © the LLVM contributors. Mapanare redistributes
compiled binaries of clang, lld-link, and their required runtime
libraries **unmodified**, as permitted by the Apache 2.0 with LLVM
Exception license. No source modifications are made.

The LLVM Exception explicitly permits combining LLVM's *output*
(compiled object files / linked binaries) with non-Apache-licensed
code without copyleft propagation. **Mapanare-emitted binaries that
pass through clang and lld-link are NOT subject to LLVM's license.**

For the source code of LLVM components, see:
<https://github.com/llvm/llvm-project/tree/llvmorg-18.1.8>

## w64devkit (Windows release only)

**Components bundled:** MinGW-w64 gcc, binutils, GNU runtime
libraries (libgcc, libstdc++, libwinpthread).

**Bundle location:** flattened into the PyInstaller bundle so
`mapanare run` / `mapanare build` work out of the box on Windows.

**License:** the GCC runtime exception applies to programs compiled
with the bundled gcc — Mapanare-emitted binaries are not subject to
GPL copyleft. See <https://github.com/skeeto/w64devkit> for the
upstream license text.

## Mapanare itself

Mapanare is licensed under the [Mapanare LICENSE](../LICENSE) in the
project root. The Mapanare runtime (`runtime/native/`) is statically
linked into compiled output and shares Mapanare's license.
