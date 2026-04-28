# LLVM-MinGW SDK Bundle - Required Files

Mapanare v5.12.0 stages a curated LLVM-MinGW UCRT x86_64 SDK into
`dist/mapanare/sdk/` for the default Windows ZIP. This replaces the
v5.10.0 official LLVM-only subset and removes the v5.11.2 double
toolchain shape (`toolchain/` plus `llvm/`).

Pinned upstream release:

- Project: <https://github.com/mstorsjo/llvm-mingw>
- Release: `20260421` (`llvm-mingw 20260421 with LLVM 22.1.4`)
- Asset: `llvm-mingw-20260421-ucrt-x86_64.zip`
- License: LLVM Apache 2.0 with LLVM Exception plus MinGW-w64 and
  winpthreads runtime/import-library licenses.

## Files

`tools/llvm-mingw-bundle/extract_sdk.ps1` copies this subset:

| Path | Purpose |
|---|---|
| `bin/clang.exe` | Primary C/LLVM IR compiler driver |
| `bin/clang-22.exe` | Versioned clang binary used by wrapper shims |
| `bin/x86_64-w64-mingw32-clang.exe` | Target-specific clang driver |
| `bin/ld.lld.exe` | Linker invoked by clang |
| `bin/ld.exe` | Staged copy of `ld.lld.exe` for clang's GNU driver lookup |
| `bin/llvm-ar.exe`, `bin/ar.exe` | Runtime archive creation |
| `bin/llvm-ranlib.exe` | Archive index tool |
| `bin/llvm-strip.exe` | Optional release artifact stripping |
| `bin/libLLVM-22.dll`, `bin/libclang-cpp.dll` | clang runtime DLLs |
| `bin/libwinpthread-1.dll`, `bin/libunwind.dll`, `bin/libc++.dll` | LLVM-MinGW support DLL closure |
| `include/` | MinGW-w64/UCRT Windows and C headers |
| `lib/clang/22/include/` | clang builtin headers |
| `lib/clang/22/lib/windows/libclang_rt.builtins-x86_64.a` | compiler-rt builtins |
| `x86_64-w64-mingw32/bin/` | target runtime DLLs |
| `x86_64-w64-mingw32/lib/` | startup objects, UCRT libs, import libs |
| `x86_64-w64-mingw32/lib/libgcc.a` | Staged copy of compiler-rt builtins for clang's default GNU runtime lookup |
| `x86_64-w64-mingw32/lib/libgcc_eh.a` | Staged copy of `libunwind.a` for clang's default GNU runtime lookup |
| `x86_64-w64-mingw32/share/mingw32/COPYING*` | target license texts |
| `LICENSE.TXT` | upstream LLVM-MinGW license summary |

The first v5.12.0 SDK cut keeps the full `include/` and
`x86_64-w64-mingw32/lib/` trees. Trimming individual Windows headers or
import libraries is deliberately deferred until clean-Windows smoke data
proves the narrower closure for all Mapanare runtime features.

## Validation

The extractor compiles and runs a C smoke program with only the staged
SDK `bin/` plus system directories on PATH:

```powershell
$env:PATH = "<sdk>\bin;C:\Windows\System32;C:\Windows"
Remove-Item Env:LIB -ErrorAction SilentlyContinue
Remove-Item Env:INCLUDE -ErrorAction SilentlyContinue
```

The published ZIP smoke then validates the real release artifact with
`mnc --version`, `mnc run`, `mnc build`, built-exe execution, and
`mnc test` under the same stripped environment.
