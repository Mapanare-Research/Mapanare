# v5.11.0 — Pk.* — Packaging hygiene + post-bundle cleanup

**Status:** PLANNING
**Breaking:** No (additive — every change is backward compatible
with the v5.10.0 install path; old `mapanare-win-x64.zip` URL keeps
resolving for the soak window).
**Prerequisite:** v5.10.0 shipped. Specifically:
- Win.1b.A–G (bundled LLVM in Windows release) — Pk.1's versioned
  filenames extend the same release artifacts; the bundle layout
  is now stable enough to rename safely.
- v5.9.1 DX.5 (`mnc <file.mn>` defaults to run, with one-release
  deprecation note) — v5.11.0 removes the deprecation message per
  the v5.9.1 PLAN's stated soak window (v5.10.0 carries it; v5.11.0
  drops it).
**Estimated effort:**
- Phase 1 (Pk.1 — versioned artifact names) — 2-3h
- Phase 2 (Pk.2 — drop v5.9.1 deprecation note) — 0.5h
- Phase 3 (Pk.3 — *evaluate* PyInstaller→native swap) — 1-2h
  (decision-only; do not implement here)
- Phase 4 (Pk.4 — macOS/Linux bundle audit + closeout) — 1h
- Phase 5 (validation + release) — 1-2h
- **Total:** 5-9 hours, single session

---

## Goal

Two distinct cleanups deferred from v5.10.0, plus the v5.9.1 soak-
window removal. None of them touch compiler internals.

1. **Pk.1 — versioned artifact filenames.** Today's release
   artifacts (`mapanare-win-x64.zip`, `mnc-linux-x64`, etc.) carry
   no version in the filename. The release URL has `v5.X.Y` in the
   path so disambiguation works *online*, but locally-saved copies
   collide. Add the version everywhere driven by the `VERSION` file.
2. **Pk.2 — drop the v5.9.1 implicit-run deprecation note.** Per
   the v5.9.1 PLAN, the one-line stderr message on the
   `mnc <file.mn>` (no subcommand) path was a soak-window concession
   for downstream CI scripts. v5.10.0 carried it; v5.11.0 removes it.
3. **Pk.3 — *evaluate* (don't implement) the PyInstaller→native
   bundle swap.** Whether `mapanare-win-x64.zip` should switch from
   the PyInstaller-bundled Python CLI to a smaller native-only
   bundle. v5.10.0's bundled LLVM made the Python CLI bundle ~95 MB;
   a native swap could shrink that to ~10 MB + LLVM. **Gate** on
   whether `mnc` (native) has reached parity with the
   PyInstaller-bundled Python CLI's surface (transpile, LSP, WASM
   driver). If not, defer further; the closeout doc captures the
   decision.
4. **Pk.4 — macOS / Linux LLVM bundling audit.** v5.10.0 PLAN
   Decision 4 deferred this with the rationale "macOS/Linux users
   already have system clang." Re-validate that decision against
   v5.10.0's actual install probe data; close out as "still
   deferred" or open a v5.12.x slot.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Pk.1** | MEDIUM (UX hygiene) | Embed the VERSION file's value into every release artifact filename. CI matrix: artifact rename in `.github/workflows/publish.yml`'s `build-cli` and `build-native` jobs. install.ps1 / install.sh: switch from hardcoded artifact names to dynamically-computed `mapanare-${VERSION}-win-x64.zip` / `mnc-${VERSION}-linux-x64`. Release-notes table: update download URLs to use the templated names. **Backward compat:** symlink/rename the old hardcoded names alongside the new versioned ones for ≥2 releases so existing install scripts in user docs / blog posts keep resolving. | 2-3h |
| **Pk.2** | LOW (cleanup) | Drop the v5.9.1 `mnc <file.mn>` (implicit-run) deprecation stderr line. Single-line edit in `mapanare/self/main.mn`'s dispatcher; the v5.10.0 soak window is over per the v5.9.1 PLAN's stated cadence. | 0.5h |
| **Pk.3** | EVALUATE-ONLY | Decide whether to swap `mapanare-win-x64.zip`'s PyInstaller bundle for a small native bundle (`bin/mnc.exe + bin/llvm/`). Audit `mnc` vs `mapanare` CLI surface gap. If no gap → schedule the swap for v5.12.0 with a fresh PLAN. If gap → defer; capture a "what mnc still doesn't do" issue list in `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md`. **Implementation NOT in scope here**, only the decision. | 1-2h |
| **Pk.4** | LOW (closeout-doc) | Document the macOS/Linux bundling deferral. **Closed-by-anticipation** per the v5.10.0 session conversation (2026-04-28): xcode-select / apt clang remain the standard, libstdc++/libc ABI mismatches make a static Linux LLVM bundle ~300 MB which dwarfs the win-x64 95 MB target, no demand signal emerged. v5.11.0's task is just the closeout doc — no re-evaluation needed. | 0.5h |

---

## Phase plan

### Phase 1 — Pk.1 — versioned artifact names

Today's workflow at `.github/workflows/publish.yml`:

```yaml
matrix:
  include:
    - os: ubuntu-latest
      artifact: mapanare-linux-x64
      archive_name: mapanare-linux-x64.tar.gz
```

becomes:

```yaml
env:
  VERSION_TAG: ""  # populated from VERSION at job start

# In each job:
- name: Compute version-suffixed artifact name
  shell: bash
  run: |
    V=$(cat VERSION | tr -d '[:space:]')
    echo "VERSION_TAG=${V}" >> $GITHUB_ENV
    echo "ARTIFACT_VERSIONED=mapanare-${V}-${{ matrix.platform }}" >> $GITHUB_ENV
    echo "ARCHIVE_VERSIONED=mapanare-${V}-${{ matrix.platform }}.${{ matrix.archive_ext }}" >> $GITHUB_ENV
```

Backward compat:

```yaml
- name: Upload versioned + legacy archive names
  shell: bash
  run: |
    cd dist
    cp ${{ env.ARCHIVE_VERSIONED }} ${{ matrix.archive_name }}  # legacy alias
    gh release upload ... ${{ env.ARCHIVE_VERSIONED }} ${{ matrix.archive_name }}
```

`install.ps1` / `install.sh` switch from hardcoded `$Artifact =
"mapanare-win-x64.zip"` to:

```powershell
$Artifact = "mapanare-${Version -replace '^v',''}-win-x64.zip"
```

with a fallback to the legacy filename if the versioned one 404s
(2-release soak window).

### Phase 2 — Pk.2 — drop v5.9.1 deprecation note

`mapanare/self/main.mn`'s `mn_main` dispatch path that handles
bare `mnc <file.mn>` writes a one-line stderr deprecation. v5.9.1
PLAN named v5.11.0 as the removal release. Audit:

```bash
grep -n "deprecated\|deprecation\|implicit-run" mapanare/self/main.mn
```

Delete the message; keep the run behavior (which became the default
in v5.9.1 and is no longer "deprecated" — there's nothing left to
deprecate).

### Phase 3 — Pk.3 — PyInstaller→native swap evaluation

Compare:

```bash
# PyInstaller bundle's full surface:
mapanare --help

# Native binary's surface:
mnc --help
```

Document gaps in `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md`. If
gaps exist: defer the swap, mark each gap as a v5.12.x candidate.
If no gaps: schedule v5.12.0 slot.

### Phase 4 — Pk.4 — macOS/Linux bundle closeout

Pre-decided in the v5.10.0 session conversation. The v5.10.0 PLAN's
Decision 4 deferred this with three reasons; all three still apply:

- **macOS** — every `xcode-select --install` user has clang at
  `/usr/bin/clang`; every Homebrew user has `/opt/homebrew/bin/clang`.
  A bundle would conflict with the user's existing clang and create
  "wrong clang version" reports when their IDE diverges.
- **Linux** — bundled clang's libstdc++/libc dependencies create
  a portability nightmare (binary built against glibc 2.35 won't
  run on glibc 2.31). Static LLVM with bundled libstdc++ is
  ~300 MB — dwarfs the win-x64 95 MB target.
- **No demand signal** has emerged from v5.10.0. Re-open if it does.

Action: just the closeout doc in
`docs/roadmap/v5/v5.11.0/SESSION_REPORT.md`. The conversation
record lives at `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md` so
future-you can audit the decision trail.

### Phase 5 — Validation + release

Standard suite. No new C-runtime exports, so Bb.4 seed refresh is
NOT needed (this is the first release in 5+ to skip seed refresh).
Goldens 66/66 preserved. `make lint` clean. Fixed-point preserved.

---

## What ships

- `.github/workflows/publish.yml` — versioned artifact names
- `packaging/install.ps1` — versioned artifact lookup with legacy
  fallback
- `packaging/install.sh` — same
- `mapanare/self/main.mn` — drop deprecation stderr
- `docs/roadmap/v5/v5.11.0/PLAN.md` (this file)
- `docs/roadmap/v5/v5.11.0/SESSION_REPORT.md`
- `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md` (Pk.3 decision)
- `VERSION`, `CHANGELOG.md`, `CLAUDE.md`, `README.md`

## What does NOT ship

- **PyInstaller→native bundle swap.** Pk.3 is evaluate-only; the
  actual swap (if approved) is v5.12.0.
- **macOS/Linux bundling.** Pk.4 is closeout-only; defer until
  demand signal emerges.
- **Compiler / parser / semantic / MIR / lower / emitter changes.**
  Zero. v5.11.0 is packaging hygiene.
- **LLVM 19 bundle.** v5.10.0 PLAN Decision 1: bump annually after
  the new LLVM stable lands. v5.11.0 stays on 18.1.8.

---

## Decisions

### Decision 1: keep legacy filenames as aliases for how long?

**Recommendation:** 2 minor releases (so v5.13.0 onward can drop
the unversioned aliases). Long enough that every install script
in user docs has been updated, short enough that the artifact list
doesn't bloat indefinitely.

### Decision 2: dotted vs dashed version separators in filenames?

**Recommendation:** dashed (`mapanare-5.11.0-win-x64.zip`), not
dotted (`mapanare-5.11.0.win-x64.zip`). Dashes match Linux/macOS
release-tarball convention and survive shell glob expansion better.
Inside the version field itself, dots stay (`5.11.0`, not
`5-11-0`).

### Decision 3: include the leading `v`?

**Recommendation:** **no.** Tag names use `v5.11.0`; artifact
filenames use `5.11.0`. The leading `v` is git/GitHub convention
for tags; filenames don't need it. Stripping the `v` matches the
output of `cat VERSION` which is `5.11.0` not `v5.11.0`.

---

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| Pk.R1 | Existing install scripts users wrote in blog posts hardcode `mapanare-win-x64.zip`. Versioned-only filename break those overnight. | 2-release legacy alias window per Decision 1. |
| Pk.R2 | The version-string interpolation in install.ps1 differs between PowerShell tag (`v5.11.0`) and `VERSION` file (`5.11.0`). install.ps1 must strip leading `v` consistently. | Test matrix: explicit version (`$env:MAPANARE_VERSION = "v5.11.0"`), explicit version no-v, and "latest". |
| Pk.R3 | Pk.3 evaluation reveals `mnc` is missing critical surface (e.g. transpile). Pressure to delay v5.11.0 release while fixing those gaps. | Pk.3 is **evaluate-only**. Decision goes into v5.12.0+. v5.11.0 ships regardless. |
