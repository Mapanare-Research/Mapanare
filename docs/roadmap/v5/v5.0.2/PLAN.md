# Mapanare v5.0.2 — "Reactive Patch"

> **Fix whatever v5.0.1 CI caught.** This release is reserved for the
> issues that will surface the first time `build-native` runs
> end-to-end on `windows-latest`. Scope is defined by CI output, not
> by ambition.

**Status:** RESERVED (skeleton)
**Breaking:** No
**Prerequisite:** v5.0.1 shipped (at least one GitHub Actions run of
the new Windows build-native entry)
**Estimated work:** 1 session (~30 min – 2 hours, depending on what broke)

---

## Why this slot exists

v5.0.1 flips a CI matrix entry that has never run. It bundles months
of Windows workaround commits (v4.157–v4.159) that have never been
exercised in a single workflow. Something will break. Reserving a
slot for the reactive patch keeps v5.0.1 shippable without
over-engineering a preventive rewrite.

## Known candidate issues

These are the most likely failure modes, ranked by probability:

| # | Symptom | Root cause | Fix sketch |
|---|---|---|---|
| 1 | `FileNotFoundError: mapanare/self/mnc-stage1` after link step | `scripts/build_stage1.py:236` hard-codes `mnc-stage1` but MinGW `gcc -o foo` appends `.exe` | `binary = SELF_DIR / ("mnc-stage1.exe" if sys.platform == "win32" else "mnc-stage1")` |
| 2 | `strip` fails on MinGW output | w64devkit's `strip` may reject clang-emitted debug sections | Gate strip behind a platform check or add `|| true` |
| 3 | `-Werror` trips on a MinGW-only warning | `-Wmissing-field-initializers` in `mapanare_core.c` struct literals | Remove `-Werror` on Windows or add `-Wno-missing-field-initializers` |
| 4 | `__chkstk` alias still undefined at link time | w64devkit 2.7.0 may ship a different libgcc variant than the flag assumes | Try both `___chkstk_ms` and `__chkstk_ms` (one underscore less) |
| 5 | Smoke test `--version` prints `4.xxx.x` instead of `5.0.1` | `MAPANARE_VERSION` macro not propagated from `VERSION` file on Windows | Check the `-DMAPANARE_VERSION=...` flag reaches the MinGW invocation |

Any subset of these (or a new item) becomes v5.0.2 scope.

## Exit criteria

- `build-native` Windows job green on two consecutive pushes to `dev`
- `mnc-win-x64.exe` available on the v5.0.2 GitHub Release
- `mnc-win-x64.exe --version` prints `mapanare 5.0.2`
- `mnc-win-x64.exe examples/hello.mn` produces IR that `llvm-as` accepts

## Rollback

If no real issue surfaces — v5.0.1's CI is miraculously green — bump
VERSION to 5.0.2 anyway as a measurement-only release and move the
reactive-patch slot to v5.0.3. Don't force-invent work.
