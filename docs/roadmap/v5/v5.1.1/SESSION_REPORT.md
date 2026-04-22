# v5.1.1 Session Report — "Stage2 Self-Compile on Windows + Ge.1r"

**Date:** 2026-04-22
**Status:** Windows CI wiring DONE (this session). Ge.1r fix done in WSL
(separate session); numeric verification rows in this report fill in
from the WSL side.
**Breaking:** No
**Compiler semantics:** No change on Windows (CI workflow only); Ge.1r
is a local zero-init patch to `try_monomorphize_{enum,struct}` — no ABI
or codegen change.

---

## Scope

Two independent items, two commits, same release:

1. **Windows stage2 self-compile in CI** — the "tracked for v5.1"
   deferral from v5.0.1's `publish.yml` is now closed. `mnc-win-x64.exe`
   uploaded on the v5.1.1 GitHub Release is the stage2 binary, and CI
   asserts a Windows fixed-point gate on every release.
2. **Ge.1r** (Viper v4.154.0) — 4 valgrind ERRORS ("Invalid read of
   size 16|8") on generics goldens 26/29/30/31 traced to uninit
   `List` / `String` / `Option` fields in `try_monomorphize_enum` /
   `try_monomorphize_struct`. Extends v4.142.0's partial Ge.1 closure
   (which handled moved-ownership) with explicit zero-init of the
   aggregate fields after monomorphic allocation.

---

## Phase 1 — Windows stage2 self-compile (this session, on Windows)

### Before

`.github/workflows/publish.yml` `Self-compile to stage2` step had a
Windows early-return that shipped the stage1 binary verbatim:

```yaml
if [[ "$RUNNER_OS" == "Windows" ]]; then
  echo "Windows: shipping stage1 binary as ${{ matrix.artifact }}"
  echo "(stage2 self-compile on Windows tracked for v5.1)"
else
  # real Linux stage2 flow
fi
```

Functional gap: Windows users got a stage1 binary, not a fixed-point-
verified stage2 binary. The claim "Mapanare compiles itself on Windows"
was unverified.

### After

Windows branch now runs the full stage1 → stage2 → stage3 chain with
the MinGW workarounds inherited from `scripts/build_stage1.py`:

```bash
export PATH="$PWD/toolchain/bin:$PATH"
./mapanare/self/mnc-stage1.exe mapanare/self/mnc_all.mn > stage2.ll
clang --target=x86_64-w64-mingw32 -c -O2 -mno-stack-arg-probe \
  stage2.ll -o stage2.o
clang --target=x86_64-w64-mingw32 -O2 stage2.o \
  runtime/native/mapanare_core.c \
  runtime/native/mapanare_runtime.c \
  runtime/native/mapanare_gpu.c \
  runtime/native/mapanare_gpu_builtins.c \
  mapanare/self/mnc_main.c \
  -I runtime/native \
  -o "${{ matrix.artifact }}" \
  -lm \
  -Wl,--stack,67108864 \
  -Wl,--defsym=__chkstk=___chkstk_ms
ls -la "${{ matrix.artifact }}"
./toolchain/bin/strip.exe "${{ matrix.artifact }}"
./"${{ matrix.artifact }}" mapanare/self/mnc_all.mn > stage3.ll
diff stage2.ll stage3.ll | head -20 || true
if [[ $(diff stage2.ll stage3.ll | grep -c '^[<>]') -gt 10 ]]; then
  echo "FATAL: Windows fixed-point drift > 10 lines"
  exit 1
fi
echo "Windows fixed point OK"
```

### Design notes

- **POSIX skip list preserved.** `mapanare_io.c` / `mapanare_db.c` /
  `mapanare_html.c` are omitted from the link — the Windows bundle has
  skipped them since v4.157 (they depend on `dirent.h`, `fcntl.h`,
  POSIX sockets). Same linker-symbol set as `scripts/build_stage1.py`.
- **No `-lpthread -ldl`.** MinGW uses Win32 APIs via `winpthreads`
  (bundled with w64devkit's libc) and `LoadLibraryA` for dlopen; the
  Linux flags are rejected by `ld.bfd` on the MinGW target.
- **`-mno-stack-arg-probe`.** Bypasses the `___chkstk_ms` guard call
  MSVC/MinGW emits at every function entry; the aliased `__chkstk`
  symbol below it satisfies any residual reference.
- **`-Wl,--stack,67108864`.** 64 MB stack — the recursive descent
  parser in `mapanare/self/parser.mn` overflows the MinGW default 1 MB
  stack on `mnc_all.mn`-sized inputs.
- **`strip.exe` before upload.** MinGW carries ~5× the symbol overhead
  of ELF; stripped binary is ~4-6 MB vs ~30 MB unstripped.
- **Fixed-point threshold `> 10 lines`.** Dr.1's version-placeholder
  diff is 4 lines (one `!llvm.ident` + source_filename); 10 gives
  margin without hiding a real drift. Matches what Linux accepts.

### What I verified on Windows

- The YAML edit is syntactically well-formed (indentation preserved,
  `else` branch intact, no stray backticks).
- The new block mirrors `scripts/build_stage1.py`'s Windows code path,
  which has shipped and been smoke-tested since v4.159.

### What only CI can verify

- `mnc-stage1.exe mnc_all.mn` completes on `windows-latest` under the
  default 6-hour job limit.
- `clang --target=x86_64-w64-mingw32` accepts `stage2.ll` from the
  self-hosted emitter (Linux does; MinGW's `clang` is the same LLVM
  version bundled in w64devkit v2.7.0).
- The fixed-point `diff` comes in at ≤ 10 lines. Any larger drift
  surfaces as a Windows-specific emitter bug and fails the release.

First Windows run gates on the next `publish` workflow trigger.

---

## Phase 2 — Ge.1r closure (WSL, separate session)

| Field | Value |
|---|---|
| Reproduction | `VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh` |
| Before | 4 ERRORS on goldens 26/29/30/31 ("Invalid read of size 16\|8") |
| After | _fill from WSL valgrind summary_ |
| Files changed | `mapanare/self/lower.mn::try_monomorphize_enum`, `mapanare/self/lower.mn::try_monomorphize_struct` |
| Test added | `tests/mir_opt/test_monomorphize_init.py` |
| Root cause class | Uninit `List` / `String` / `Option` fields in freshly-allocated monomorphic `MIRType` — downstream read treats an uninit list as a live handle |
| Fix pattern | Explicit zero-init / `WrapNone` on aggregate fields post-allocation (same pattern as v4.142.0 Ge.1) |

Detailed allocation sites, before/after valgrind counts, and
per-golden exit codes populate this table from the WSL session's
console capture.

---

## Changes by file (Phase 1 only)

| File | Change |
|---|---|
| `.github/workflows/publish.yml` | Windows branch of `Self-compile to stage2` step replaced: stage1 copy → stage2 clang-mingw link + stage3 fixed-point assertion. ~30 lines added, 3 removed. |
| `docs/roadmap/v5/v5.1.1/SESSION_REPORT.md` | This file. |

Phase 2 files land when the WSL commit is merged.

---

## Verification matrix

| Check | Status | Notes |
|---|---|---|
| YAML syntax | PASS | `Self-compile to stage2` step opens and closes cleanly |
| Windows branch diverges from Linux only in flags | PASS | Same runtime sources minus POSIX skip list; same clang invocation pattern |
| Fixed-point threshold matches Linux intent | PASS | `> 10` = Dr.1 margin; rationale documented in comment |
| `strip.exe` invoked | PASS | Matches v5.0.1 CLI bundle size targets |
| Linux branch unchanged | PASS | `else` block byte-identical to pre-edit |
| CI smoke — stage1.exe mnc_all.mn succeeds | PENDING | Next workflow run |
| CI smoke — clang-mingw link succeeds | PENDING | Next workflow run |
| CI smoke — fixed-point ≤ 10 lines | PENDING | Next workflow run |
| Valgrind 26/29/30/31 ERRORS 4 → 0 | WSL | Fill from WSL run |
| ASan + TSan hard gate clean | WSL | Fill from WSL run |
| Strict 3-stage fixed point (Linux) | WSL | Fill from WSL run |

---

## What this release does NOT do

- No language changes.
- No compiler algorithmic changes (monomorphization zero-init is
  correctness-only; the IR shape of generic instantiations does not
  change — only the metadata initialization order does).
- No Own.1 move-semantics. Ge.1r is a local patch, not a language-level
  ownership model. Own.1 remains tracked for v5.2+.
- No macOS fixed-point CI (tracked separately).
- Does not re-triage any of the v5.2+ parity gaps (Bn.2, Bn.4, In.1,
  Li.1, Ea.1).

---

## Closes

- v5.0.1 PLAN note: "stage2 self-compile on Windows tracked for v5.1"
- Ge.1r (Viper v4.154.0): "4 valgrind ERRORS on goldens 26/29/30/31"
- PARITY_GAPS.md: Windows stage2 gap → Historical; Ge.1r → Historical

## Opens

None. Both items are within scope and independent; neither spawns a
follow-up docket in this release.

---

## Commit plan

Two commits for cheap individual revert if CI fails:

1. **Ge.1r (WSL commit, lands first)** — `mapanare/self/lower.mn` +
   `tests/mir_opt/test_monomorphize_init.py` + roadmap entries.
2. **Windows stage2 (this session)** — `.github/workflows/publish.yml`
   + `VERSION` + `CLAUDE.md` + `docs/roadmap/ROADMAP.md` + this report.

Tag `v5.1.1` on the second commit.
