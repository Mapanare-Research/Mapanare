# v5.32.0 — Nw.\* — ship native `mnc.exe` in the Windows SDK bundle

**Status:** PLANNING
**Type:** Packaging + CI release. Ships a prebuilt native compiler
binary inside the Windows SDK ZIP so end users never hit the Python
bootstrap.
**Breaking:** No. Python entrypoint stays as a fallback; existing
`mnc` invocations resolve to the native binary first, then fall
through to Python if the native binary is missing.
**Prerequisite:** v5.31.0 shipped (banner hotfix). Strict 3-stage
fixed point preserved.
**Estimated effort:** 1–2 sessions. Cross-compile + CI wiring + ZIP
layout + smoke tests. Real validator is the publish workflow run
end-to-end.

---

## Why this exists

v5.12.0 shipped the **Windows SDK toolchain bundle** (LLVM-MinGW
under `bin\sdk\bin\clang.exe`). It works — `mnc run` and `mnc build`
function on clean machines. But the *compiler frontend itself*
(`mnc`) on a Windows SDK install is still the Python module, not a
native binary. Every CLI invocation goes through the Python
bootstrap.

Concrete evidence from a fresh v5.30.0 SDK install:

```text
PS C:\Users\juanh> mapanare --version
[dev mode] Using Python bootstrap compiler. ...
mapanare 5.30.0
PS C:\Users\juanh> mnc --version
[dev mode] Using Python bootstrap compiler. ...
mapanare 5.30.0
```

Both `mapanare` and `mnc` are Python entrypoints. The bundled SDK
contains the *backend* (LLVM toolchain) but not the *frontend*
(`mnc.exe`). v5.31.0 hides the banner; v5.32.0 makes it true that
end users never run Python.

This is the structural fix. v5.31.0 was cosmetic.

---

## Goals

1. **Nw.1** — Cross-compile (or natively compile in CI Windows
   runner) `mnc.exe` from `mapanare/self/*.mn` using the bundled
   LLVM-MinGW toolchain. Produce a single statically-linked
   executable.
2. **Nw.2** — Add a CI step in `.github/workflows/publish.yml` that
   builds `mnc.exe` for the Windows publish job and embeds it in
   `mapanare-${V}-win-x64-sdk.zip` at `bin\mnc.exe`.
3. **Nw.3** — Make the Python entrypoint a fallback. When the
   `mapanare` / `mnc` console-script wrapper runs and detects an
   adjacent `bin\mnc.exe`, it execs that and exits. Falls back to
   Python only when the native binary is missing (dev clones,
   broken installs).
4. **Nw.4** — Smoke test: extract the published ZIP into a clean
   directory in CI, invoke `bin\mnc.exe --version`, `bin\mnc.exe
   init proj`, `bin\mnc.exe run proj\main.mn`. Assert exit codes,
   no Python in process tree, version string matches `VERSION`.
5. **Nw.5** — `mapanare-${V}-win-x64-minimal.zip` (the no-toolchain
   ZIP) also ships `bin\mnc.exe`. Minimal users supply their own C
   compiler but should still get the native frontend.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Nw.1** | HIGH (load-bearing) | **Build `mnc.exe` from `mapanare/self/`.** Two viable approaches: (a) cross-compile from Linux CI runner via `clang --target=x86_64-w64-mingw32` against the same LLVM-MinGW we ship — fastest CI; (b) build natively on a Windows runner using the bundled toolchain — closer to user reality, slower CI. **Recommend (a) for v5.32.0**, switch to (b) in v5.32.1 if cross-compile produces ABI mismatches. Either way: `mnc-stage1` is the artifact (rename to `mnc.exe` for shipping). | 3-5h |
| **Nw.2** | HIGH | **Wire `mnc.exe` into `publish.yml`.** Add a step to the Windows publish job that runs Nw.1 build (or downloads the cross-built artifact from a Linux job dependency) and copies it into the ZIP staging directory at `bin\mnc.exe` *before* PyInstaller / installer build. Update the SDK staging script in `scripts/win/` accordingly. | 2-3h |
| **Nw.3** | MEDIUM | **Native-binary fallback wrapper.** `mapanare/__main__.py` (or the console-scripts entry) gains a 10-LOC preamble: `if (sibling_native := Path(__file__).parent.parent / "bin" / "mnc.exe").exists(): os.execv(sibling_native, sys.argv); return`. The exec is in-process — no subprocess overhead, and signal handling propagates correctly. Skip on `MAPANARE_FORCE_PYTHON=1` for dev/debug. | 1h |
| **Nw.4** | HIGH (gate) | **Tarball smoke job.** New job in `publish.yml` after the Windows ZIP is built: extract to `$RUNNER_TEMP\mn-smoke`, run `bin\mnc.exe --version`, parse stdout, assert it matches `${{ needs.tag.outputs.version }}`. Run `bin\mnc.exe init testproj`, then `bin\mnc.exe run testproj\main.mn`, assert exit 0 and expected output. **Job must fail the publish if any of these break** — non-negotiable gate, the whole release point is "Python is no longer the front door." | 2h |
| **Nw.5** | LOW | **Minimal ZIP ships `mnc.exe` too.** Mirror Nw.2 in the minimal-ZIP staging. The "minimal" promise was "no bundled C compiler"; it never meant "no Mapanare frontend." User-supplied gcc/clang still drives `mnc build`. | 30 min |
| **Nw.6** | LOW | **Doc updates.** `docs/install/windows.md` (or equivalent) gets a "What's in the SDK ZIP" section listing `bin\mnc.exe`. CLAUDE.md "Native-First Philosophy" gets a paragraph about the Python entrypoint being a bootstrap-only fallback now. | 30 min |

---

## Phase plan

- **Phase 0** — Pre-flight. Verify v5.31.0 HEAD: STRICT fixed point;
  goldens 95/95; CI green. Confirm bundled LLVM-MinGW version in
  current SDK ZIP — pin exact version for cross-compile target.
- **Phase 1** — Nw.1 cross-compile. Local proof first: build
  `mnc.exe` on the WSL dev box using clang's mingw target. Run
  it under wine or copy to a Windows VM. Verify `--version` and
  `run hello.mn` work.
- **Phase 2** — Nw.2 wire into `publish.yml`. New job
  `build-mnc-windows-x64`; Windows publish job depends on it and
  pulls the artifact.
- **Phase 3** — Nw.3 Python fallback wrapper. Trivial; lands with
  unit test that mocks `bin/mnc.exe` presence/absence.
- **Phase 4** — Nw.4 smoke job. The release-blocking gate. Tune
  until it's reliable (no flake budget — flakes here mean we ship
  broken Windows installs).
- **Phase 5** — Nw.5 minimal ZIP + Nw.6 docs.
- **Phase 6** — Bump version + CHANGELOG + release notes; tag.

---

## Out of scope

- **Linux/macOS prebuilt binaries.** That's v5.33.0. Doing all
  three platforms in one release is too much CI surface to debug
  simultaneously. Win first because Win is the platform with the
  most acute UX pain (Python startup is slow on Win, terminals are
  worse, and the SDK ZIP user expectation is "shrink-wrapped tool").
- **Removing the Python bootstrap entirely.** Never; clean clones
  need it for the `bash scripts/build_from_seed.sh` path. The
  bootstrap is a *build-time* tool; v5.32.0 makes it stop being
  an *end-user-runtime* tool on Windows.
- **Self-hosting the cross-compile path.** Currently
  `scripts/build_stage1.py` (Python) drives the build. v5.32.0
  keeps that as-is — it's a build-time script, end users don't
  see it. Self-hosting the build script is a separate arc.
- **Tn.1, M.1, A.1, Ra.New1, Pv.8.B** — carry forward.

---

## Risk

1. **Cross-compile ABI drift.** Building `mnc.exe` on Linux and
   running on Windows is the standard mingw use case, but the
   self-hosted compiler exercises edge cases (Win64 calling
   convention — see v5.29.0 Mb.10 for the exact ABI gotcha that
   bit `__mn_indent_to_braces` already). Mitigation: Nw.4 smoke
   gate catches divergence at publish time; if cross-compile is
   too brittle, fall back to native Windows-runner build (slower
   CI, lower risk).
2. **PATH ordering.** If a user has multiple `mnc` on PATH (older
   install, dev checkout), the SDK install's binary should win.
   Mitigation: installer prepends its `bin\` to PATH (already
   does this for clang); confirm during Phase 0 audit.
3. **Console-scripts vs `mnc.exe` collision.** pip's
   console-scripts entry generates `mnc.exe` as a Python launcher
   stub on Windows. SDK install must not let pip's stub shadow
   the native binary. Mitigation: SDK ZIP ships its own `bin\`
   that prepends to PATH ahead of any pip-installed Python's
   `Scripts\`.
4. **Smoke job runs are slow.** Each ZIP-extract-and-run cycle
   adds ~30s to publish. Acceptable — publish is rare.

---

## Success criteria

- ✅ `mapanare-${V}-win-x64-sdk.zip` contains `bin\mnc.exe`.
- ✅ `bin\mnc.exe --version` on a clean Windows VM prints only the
  version string. **No Python in the process tree** (verify via
  `Get-Process` or `tasklist /FI "IMAGENAME eq python*.exe"`).
- ✅ `bin\mnc.exe run hello.mn` compiles and runs end-to-end with
  zero Python invocation.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.
- ✅ Smoke job in `publish.yml` is GREEN.
- ✅ `make ci-gates` GREEN; `make lint` clean.

---

## Carry-forward delta

**Closes:**
- "Python is the front door on Windows release installs" — the
  underlying issue v5.31.0 only papered over.
- v5.12.0 packaging gap (toolchain bundled, frontend not bundled).

**Inherits to v5.33.0:**
- Same shape needed for Linux + macOS. Nw.1's cross-compile
  pattern transfers; Nw.4's smoke job pattern transfers.
- Tn.1 (still overdue; v5.32.0 doesn't pick it up because scope
  is already CI-heavy).
- M.1, A.1, Ra.New1, Pv.8.B.

**Aggregate state entering v5.33.0:** 0 HIGH / 1 MEDIUM (Tn.1) /
~5 LOW. Tn.1 escalates to HIGH at v5.33.0 if not landed there.
