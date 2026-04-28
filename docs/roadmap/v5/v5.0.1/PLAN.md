# Mapanare v5.0.1 — "Windows, Natively"

> **The first Windows-native release.** Ship `mnc-win-x64.exe` — the
> small, no-Python-dependency compiler — alongside the Linux binary we
> already publish. Stop making Windows users drop into WSL to get
> native speed.
>
> No compiler source changes. No runtime source changes. This is a
> CI + packaging release: flip the one skipped matrix entry and
> `scripts/build_stage1.py` does the rest — it already has every
> Windows workaround we need.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.0.0 shipped (clean tag, Windows CLI bundle with w64devkit)
**Estimated work:** 1 session (~1-2 hours)
**Theme:** "Windows users get the same one-command native compile as Linux."

---

## Why this release exists

A user downloaded `mapanare-win-x64.zip` from the v5.0.0 release, ran
`mapanare run hello.mn`, and got:

```
[dev mode] Using Python bootstrap compiler. For native speed: mnc run <file.mn>
FileNotFoundError: [WinError 2] The system cannot find the file specified
```

Two things were true at that moment:

1. The CLI bundle works — `check`, `transpile`, `emit-c`, `emit-llvm`
   all succeeded. The bundle just needed a C compiler to finish linking.
   **v5.0.0 fixed this** by vendoring w64devkit + a prebuilt
   `libmapanare_rt.a` into the Windows zip (commit `5c99b11`).

2. But `mnc-win-x64.exe` didn't exist. The release body's Windows row
   under "Native Compiler" said **`—`**. To reproduce the claimed
   168× Python speedup, the user had to install WSL, download the
   Linux binary, install clang in the WSL distro, and link by hand.

The v4 arc spent 6 releases (v4.157–v4.160) adding the Windows
workarounds to `scripts/build_stage1.py`:

| Release | Commit | Fix |
|---------|--------|-----|
| v4.158.0 | `ada890f` | Cross-platform file I/O, skip POSIX-only runtime modules on Windows |
| v4.158.0 | `d8e127a` | Windows `tmpfile` path |
| v4.159.0 | `3bf8589` | MinGW target triple `x86_64-w64-mingw32` |
| v4.159.0 | `3d24473` | Disable clang stack probing on Windows |
| v4.159.0 | `67d6ba3` | Alias `__chkstk` → `___chkstk_ms` |
| v4.159.0 | `04560b0` | Commit message: *"skip Windows native build — POSIX runtime + MinGW __chkstk"* |

That last one is the problem. The Windows workarounds all landed, but
the CI job that *uses* them (`build-native` in `publish.yml`) still
explicitly skips Windows:

```yaml
# publish.yml:336-337
# macOS/Windows native binaries tracked for v5.x.
# Both platforms get the full CLI via PyInstaller.
```

```yaml
# publish.yml:377
if [[ "$RUNNER_OS" == "Windows" ]]; then
  echo "Skipping native build on Windows (needs clang cross-setup)"
```

This release un-skips it.

---

## What already works

| Component | File | Status |
|---|---|---|
| MinGW triple substitution | `scripts/build_stage1.py:123-131` | Complete |
| Skip `__chkstk` via `-mno-stack-arg-probe` | `scripts/build_stage1.py:151-158` | Complete |
| Windows link flags (`--stack`, `--defsym`) | `scripts/build_stage1.py:237-247` | Complete |
| Skip POSIX-only runtime modules | `scripts/build_stage1.py:181-186` | Complete |
| w64devkit vendoring on Windows runner | `publish.yml:250-265` | Complete (for `build-cli`) |
| Prebuilt `libmapanare_rt.a` on Windows | `publish.yml:267-285` | Complete (for `build-cli`) |
| `toolchain.py` compiler discovery | `mapanare/toolchain.py` | Complete |
| `mapanare run`/`build` smoke test on Windows | `publish.yml:300-306` | Complete |

The runtime and build script are Windows-ready. The CI workflow is
not. This release is a ~40-line YAML change.

---

## Scope

**In scope:**
- Add `windows-latest` entry to `build-native` matrix in `publish.yml`
- Reuse the w64devkit vendoring block from `build-cli`
- Run `python scripts/build_stage1.py` on the Windows runner
- Copy output `mapanare/self/mnc-stage1.exe` → `mnc-win-x64.exe`
- Smoke test: `mnc-win-x64.exe --version`
- Upload to the GitHub Release
- Update release body table: Windows row's "Native Compiler" column
  gains a download link (was `—`)
- Bump VERSION to 5.0.1

**Explicitly out of scope:**
- Self-compile to stage2 on Windows (stage1-built binary is functionally
  the same compiler; stage2 fixed-point validation is a v5.1+ concern)
- macOS native binary (separate release)
- Native Windows `mapanare_io.c`/`mapanare_db.c`/`mapanare_html.c`
  (Win32 port of POSIX file-I/O + dlopen — v5.x feature track)
- Any change to `scripts/build_stage1.py`, `runtime/native/*.c`,
  or `mapanare/self/*.mn`

---

## The 3 phases

### Phase 1 — Wire CI (~30 min)

Edit `.github/workflows/publish.yml`:

1. Add to the `build-native` matrix:
   ```yaml
   - os: windows-latest
     artifact: mnc-win-x64.exe
     triple: x86_64-w64-mingw32
   ```
2. Add a `Stage portable toolchain (Windows)` step to `build-native`
   (copy from `build-cli` lines 250-265). This vendors w64devkit so
   `clang.exe` and `gcc.exe` are available.
3. Add a Windows branch to the install step: we still need
   `pip install -e .` so `scripts/build_stage1.py` can import
   `mapanare.multi_module`.
4. Add a Windows branch to the build step:
   ```yaml
   if [[ "$RUNNER_OS" == "Windows" ]]; then
     export PATH="$PWD/toolchain/bin:$PATH"
     python scripts/build_stage1.py
     cp mapanare/self/mnc-stage1.exe "${{ matrix.artifact }}"
   else
     # existing Linux flow
   fi
   ```
5. Update the smoke test + upload steps to handle the `.exe` extension.

### Phase 2 — Update release body (~10 min)

In the `release` job's body template (around `publish.yml:112`):

```diff
-| **Windows** x86_64 | [Download](…/mapanare-win-x64.zip) | — |
+| **Windows** x86_64 | [Download](…/mapanare-win-x64.zip) | [Download](…/mnc-win-x64.exe) |
```

### Phase 3 — Docs + version (~20 min)

1. Bump `VERSION`: `5.0.0` → `5.0.1`
2. Add "Where We Are (v5.0.1 ...)" entry to `docs/roadmap/ROADMAP.md`
3. `CLAUDE.md` — add a one-line note under "Current Version & Roadmap"

---

## Exit criteria

1. `gh release view v5.0.1` shows `mnc-win-x64.exe` as an asset
2. Downloading that `.exe` on a clean Windows 11 box and running
   `mnc-win-x64.exe --version` prints `mapanare 5.0.1`
3. `mnc-win-x64.exe examples/hello.mn > hello.ll` emits LLVM IR
   that `llvm-as` accepts without errors
4. Release body table's Windows row links to the native binary
5. All existing CI jobs stay green (ci-gate, build-cli all 3 OSes,
   build-native Linux, checksums, update-release)

---

## Risks and rollback

**Risk 1 — `build_stage1.py` fails on Windows runner.**
The script has the Windows workarounds but has never actually run in
CI. Possible issues:
- `-Werror` catches a MinGW-only warning we haven't seen
- `pip install -e .` on Windows picks up a broken transitive dep
- `subprocess.run([..., '-Werror', ...])` hits a path-quoting issue

*Mitigation:* first push lands only the workflow change; if CI fails,
we iterate on the same PR branch. `fail-fast: false` means Linux
native keeps building regardless.

**Risk 2 — The produced `mnc.exe` segfaults on real input.**
w64devkit's clang is fresh; the `__chkstk` alias was tested once in
v4.159.0 commits but never exercised on a full self-hosted run.

*Mitigation:* the Phase 1 smoke test (`--version` + compile
`examples/hello.mn`) catches this before the asset uploads. If it
fails, the matrix entry is removed and we ship v5.0.1 without the
Windows native binary — the Linux experience is unchanged.

**Risk 3 — Runtime crashes because `mapanare_io.c` was skipped.**
The self-hosted compiler does call `__mn_read_file` (source input)
and `__mn_file_exists` (import resolution). Both are defined in
`mapanare_core.c` (line 1511 for `__mn_file_exists`), which *is*
linked on Windows. But any codepath that reaches `__mn_dir_*` or
`__mn_http_*` will link-error — those live in `mapanare_io.c`.

*Mitigation:* the smoke test must actually *compile* a small .mn
file, not just `--version`. If there's a dangling external symbol
from the self-hosted source that lives in `mapanare_io.c`, we learn
it before publishing.

**Rollback:**
- Revert the single commit
- The matrix entry goes away; CI still builds Linux native
- v5.0.1 re-released without the Windows native binary
- `mapanare-win-x64.zip` (CLI bundle with w64devkit) still works —
  Windows users lose nothing vs v5.0.0
