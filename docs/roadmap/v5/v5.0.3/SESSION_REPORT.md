# v5.0.3 Session Report — macOS Intel Native Binary

**Date:** 2026-04-21
**Scope:** Add `mnc-darwin-x64` to GitHub Release via `macos-13` CI runner

## What changed

1. **`.github/workflows/publish.yml`** — Added `macos-13` entry to `build-native`
   matrix (`artifact: mnc-darwin-x64`, `triple: x86_64-apple-darwin`). Removed
   stale comments ("macOS native binary tracked for v5.x"). Added "macOS Intel"
   row to release body download table (Full CLI column is `—`, native binary
   column has download link).

2. **`VERSION`** — `5.0.2` → `5.0.3`.

3. **`CHANGELOG.md`** — v5.0.3 entry.

4. **`CLAUDE.md`** — One-line v5.0.3 entry at top of roadmap.

5. **`docs/roadmap/ROADMAP.md`** — "Where We Are (v5.0.3 ...)" paragraph.

## Why `macos-13`

GitHub Actions moved `macos-latest` to ARM64 (M1) runners in late 2024.
The `macos-13` runner is the last Intel (x86_64) runner, available through
at least 2026. Using it avoids cross-compilation entirely — the binary is
built natively on x86_64 hardware.

## Why no code changes to `build_stage1.py`

The existing macOS branch (`build_stage1.py:108-122`) handles both
architectures correctly:

- `sys.platform == "darwin"` → sets `host_triple = "{arch}-apple-macos"`
- `arch == "arm64"` → substitutes ARM64 datalayout
- `arch == "x86_64"` → leaves the committed Linux x86_64 datalayout in
  place (SysV ABI is the same layout)

The self-compile step's `-Wl,-z,stack-size=67108864` is a Linux ELF
linker flag that fails on macOS ld64. The existing `2>/dev/null || clang ...`
fallback catches this and links without the stack-size flag.

## Not in scope

- Universal2 (fat) binaries via `lipo` — separate tooling
- macOS notarization / codesigning — v5.x ecosystem scope
- `mapanare-mac-x64.tar.gz` CLI bundle — no clear user demand
- Homebrew formula — separate release
