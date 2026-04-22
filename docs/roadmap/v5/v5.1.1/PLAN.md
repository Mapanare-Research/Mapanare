# Mapanare v5.1.1 — "Stage2 Self-Compile on Windows"

> **Run `./mnc-win-x64.exe mnc_all.mn` in CI, link with clang-mingw,
> verify strict 3-stage fixed point.** v5.0.1 shipped the stage1
> Windows binary; this release turns on the self-hosted parity check.
> Closes the v5.0.1 PLAN's "tracked for v5.1" note.

**Status:** PLANNED (skeleton)
**Breaking:** No
**Prerequisite:** v5.1.0 shipped
**Estimated work:** 1-2 sessions

---

## Why this release exists

v5.0.1 ships `mnc-win-x64.exe` built from the Python bootstrap via
`scripts/build_stage1.py`. This is functionally the compiler but
not the fixed-point-verified binary. The Linux job does:

```
Python bootstrap → mnc-stage1 → (self-compile) → mnc-linux-x64
```

The Windows job skips the self-compile step:

```
Python bootstrap → mnc-stage1.exe → (uploaded as mnc-win-x64.exe)
```

The difference is subtle: stage1 and stage2 produce byte-identical
IR on Linux (strict fixed-point since v4.134.0), so functionally
the binaries are equivalent. But the *claim* "Mapanare compiles
itself on Windows" is not verified. This release verifies it.

## Scope

Plus: **Ge.1r opportunistic closure.** Viper v4.154.0 flagged 4
valgrind ERRORS (goldens 26/29/30/31 — generics monomorphization
residual "Invalid read of size 16|8") that were 0 at v4.144.0 and
resurfaced as binary layout shifted. Root cause class is the same
as Own.1 (uninit struct metadata from monomorphization). This
release has the self-compilation machinery spinning up anyway;
audit the monomorphization path while it's in hand.

**In scope:**
- In `publish.yml`'s `build-native` Windows branch, add a second
  step after `build_stage1.py`:
  ```bash
  ./mapanare/self/mnc-stage1.exe mapanare/self/mnc_all.mn > stage2.ll
  clang --target=x86_64-w64-mingw32 -c -O2 stage2.ll -o stage2.o
  clang --target=x86_64-w64-mingw32 -O2 stage2.o \
    runtime/native/mapanare_core.c \
    runtime/native/mapanare_runtime.c \
    runtime/native/mapanare_gpu.c \
    runtime/native/mapanare_gpu_builtins.c \
    mapanare/self/mnc_main.c \
    -I runtime/native \
    -o mnc-win-x64.exe \
    -lm \
    -Wl,--stack,67108864 \
    -Wl,--defsym=__chkstk=___chkstk_ms
  ```
- Replace the stage1-copied binary from v5.0.1 with this stage2 one
- Add a strict fixed-point check: run the stage2 binary on itself,
  diff the resulting stage3.ll against stage2.ll — byte-identical
  is required for release

- **Ge.1r**: audit `mapanare/self/lower.mn::try_monomorphize_enum`
  and `try_monomorphize_struct`. The v4.142.0 fix handled one UAF
  (moved-ownership before emit); Viper's v4.154.0 data shows there
  are more uninit reads downstream. Add valgrind-clean assertion to
  the CI suite for goldens 26/29/30/31.

**Out of scope:**
- 3-stage fixed-point checks on macOS (separate release — macOS
  already has native binary but the fixed-point check is Linux-only)
- Universal fixed-point binary (stage-N where N is determined by
  convergence detection)
- Own.1 full move-semantics enforcement — Ge.1r is a local patch,
  not the language-level fix Viper ultimately wants

## Exit criteria

- `mnc-win-x64.exe` on the v5.1.1 GitHub Release is the stage2 binary
- CI step `verify_fixed_point_windows` in `publish.yml` passes
- The output diff `stage2.ll` vs `stage3.ll` on Windows is either
  empty or bounded by the same `Dr.1` version-placeholder exception
  the Linux build allows
- Valgrind on goldens 26/29/30/31 reports 0 ERRORS (Ge.1r closure);
  Viper's `VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh`
  reproduction shows `ERRORS = 0`

## Risks

**Risk 1 — Windows stage2 diverges from Linux stage2.**
Likely culprits: the MinGW triple substitution leaves different
attribute orderings in function declarations; w64devkit's clang
version differs from Linux's.
*Mitigation:* the MinGW triple is already substituted at
`build_stage1.py:123-131`. Compare the two platforms' stage2.ll
line-by-line in a test artifact before asserting byte-identical.

**Risk 2 — 32 MB stage2 binary triggers GitHub Release size limits.**
GitHub Releases accept up to 2 GB, so this is unlikely. But MinGW
binaries often carry ~5× the symbol overhead of ELF.
*Mitigation:* `strip` the binary as the Linux build does.
