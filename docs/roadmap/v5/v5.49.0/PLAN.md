# v5.49.0 — Wn.\* — Windows native binary smoke-test diagnostic + fix

**Status:** PLANNING
**Type:** Targeted Windows native-binary fix release. Diagnoses
and closes the `mnc.exe run hello.mn` OOM regression that the
`publish.yml` Windows SDK smoke step (line 596) trips on the
release tarball's `dist/mapanare/mnc.exe`.
**Breaking:** No. Pure bug fix. The user-facing Windows surface
is supposed to work; today it aborts at startup of `run`.
**Prerequisite:** v5.48.0 shipped (Te.3.D colon-block migration)
or explicitly deferred. v5.49.0 doesn't depend on Te.3.D
semantically; the order is just calendar (run them in PLAN-id
order so the carry-forward ledger stays linear).
**Estimated effort:** 1 session. The bug is well-localized
(Windows-only; reproduces deterministically on `macos-latest`'s
`mnc.exe run` with a 1-line `print("hi")` source). The Wb.1.dx
gdb instrumentation already documented in `publish.yml:802-825`
provides the diagnostic shape — Wn.0 ports it to the SDK smoke
step.

---

## Why this exists

The `publish.yml` Windows SDK smoke step (lines 564-604) runs
the staged `dist/mapanare/mnc.exe` through three checks:

1. `mnc.exe --version` — passes (prints `mapanare 5.47.5`,
   doesn't spawn Python; v5.32.0 Nw.4 native-dispatch gate holds).
2. `mnc.exe run hello.mn` — **fails**. Aborts with:
   ```
   mapanare: out of memory (requested 7011361785666170466 bytes)
   ```
3. `mnc.exe build hello.mn -o hello.exe` — never reached.

The garbage size `7011361785666170466` decodes to bytes
`0x22 0x1A 0x00 0x00 0x55 0x61 0x55 0x61` (little-endian),
i.e. `"\x22\x1A\0\0UaUa"` — looks like a path or string region
read where a `size_t` was expected. This is the same failure
class the `publish.yml:856-858` comment block already names:

> "Manifests as garbage `size_t` from a path-string to
>  `__mn_alloc` (e.g. `...M\eranb...` → OOM)."

That comment lives next to Wb.1.dx, which captures gdb
backtraces on the **stage2** OOM. The smoke step at line 596
hits the **same failure mode** but doesn't have Wb.1.dx wired
in, so the call site is invisible from CI logs.

The `--version` check passing rules out PyInstaller-copy
regressions (Nw.4 territory). The native binary loads cleanly;
the bug is in the `run` subcommand's dispatch path on Windows.

This needs a release because:

- The Windows SDK ZIP is the **default** Windows install since
  v5.12.0 (Mc.6 / Wk.\*); shipping a binary that aborts on
  `run` is a public-facing regression.
- `publish.yml` only runs on push to `main` or
  `workflow_dispatch`, so the failure is visible in the
  pre-release smoke but not on every dev push. Without a
  dedicated release the bug lingers until the next attempted
  publish.
- Phase 0 audit will determine whether Linux + macOS are
  affected (they aren't, per local repro and per the
  `dist/mapanare/mnc` Linux/macOS smoke at `publish.yml:1132+`
  and `:1224+` which both pass) — so the fix is plausibly
  Windows-only and shouldn't drag in a broad refactor.

The Wn.\* prefix continues the existing Wb.\* (Windows
bootstrap) and Nw.\* (native Windows) arc; "Wn" reads as
"Windows native" and disambiguates from the v5.32.0 Nw.\*
ZIP-shape work and the v5.8.x Wb.\* bootstrap-cycle work.

---

## Goals

1. **Wn.0** — **Phase 0 audit.** Port the Wb.1.dx gdb-backtrace
   wrapper from `publish.yml:802-825` to the Windows SDK smoke
   step at `publish.yml:596`. Re-trigger the smoke; capture the
   backtrace into the action log; localize the call site that
   passes the garbage size to `__mn_alloc`. Output:
   `docs/roadmap/v5/v5.49.0/PRE_PHASE_AUDIT.md` with the
   captured backtrace, the call-site `.mn` location, and the
   sized fix proposal.
2. **Wn.1** — **Root-cause fix.** Apply the fix indicated by
   Phase 0. Likely candidates (Phase 0 confirms which):
   (a) `cmd_run` path-string handling on Windows (Win64 ABI
       sret/sarg shape mismatch on a function that returns or
       accepts a `String`/`{ptr,i64}` aggregate).
   (b) An emit-side regression in the v5.46.0 / v5.47.0 lower
       work that surfaces only on Win64's parameter-passing
       conventions.
   (c) An alloca-aliased read of stack garbage in the path
       handling — the Wb.1.dx-named pattern.
3. **Wn.2** — **Self-host mirror discipline.** If Wn.1 lands in
   `mapanare/self/*.mn`, stage1 rebuild + STRICT 3-stage fixed
   point preservation per the v5.45.0 / v5.46.0 / v5.47.0
   pattern. If Wn.1 is C-runtime-only or
   `mapanare/emit_llvm_text.py`-only, STRICT preserved by
   construction (no `mapanare/self/*.mn` touches).
4. **Wn.3** — **Smoke-step hardening.** Keep the gdb-backtrace
   wrapper from Wn.0 as a permanent part of `publish.yml:596`
   so any future regression in this same class surfaces with
   the call site in the action log instead of just an OOM
   number. Mirrors the Wb.1.dx instrumentation pattern that
   v5.8.3 paid forward.
5. **Wn.4** — **Falsifiability test.** A new pytest case under
   `tests/integration/` (or `tests/native/`) that reproduces
   the `mnc.exe run hello.mn` failure shape on Windows runners.
   The test xfails pre-Wn.1, passes post-Wn.1. Integration-tier
   because it needs the staged `dist/mapanare/mnc.exe` artifact;
   skips automatically on non-Windows hosts.
6. **Wn.5** — **Closeout artifacts.** Bump VERSION to 5.49.0;
   CHANGELOG `### Fixed` entry; CLAUDE.md release-notes;
   SPEC.md sync block; SESSION_REPORT.md; PRE_PHASE_AUDIT.md
   already landed at Wn.0.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Wn.0** | HIGH (gate) | **Phase 0 audit.** Port Wb.1.dx gdb wrapper to publish.yml:596. Re-run Windows SDK smoke. Extract backtrace. Localize call site. Decide compiler vs runtime fix. Output: `PRE_PHASE_AUDIT.md`. | 2h |
| **Wn.1** | HIGH | **Root-cause fix.** Apply Phase-0-indicated fix in `mapanare/lower.py` / `mapanare/emit_llvm_text.py` / `runtime/native/*.c` / `mapanare/self/*.mn` as Phase 0 directs. Estimated ≤ 50 LOC; if Phase 0 finds a deeper structural issue the scope splits to a Wn.x patch. | 3h |
| **Wn.2** | HIGH (gate) | **Self-host mirror.** Only triggers if Wn.1 touches `mapanare/self/*.mn`. Stage1 rebuild after each mirror edit; STRICT 3-stage fixed point preserved at v5.48.0's line count. | 1h conditional |
| **Wn.3** | MEDIUM | **Smoke-step hardening.** Permanent gdb-backtrace wrapper at `publish.yml:596` — mirror of `publish.yml:802-825` Wb.1.dx pattern. Cheap; runs only on failure. | 30min |
| **Wn.4** | HIGH (gate) | **Falsifiability test.** New `tests/integration/test_windows_native_smoke.py` (or `tests/native/test_native_run.py`). Pre-Wn.1 it fails with the OOM signature; post-Wn.1 it passes. Skips on non-Windows. | 1h |
| **Wn.5** | HIGH (gate) | **Closeout.** Bump VERSION to 5.49.0; CHANGELOG `### Fixed`; CLAUDE.md release-notes; SPEC.md sync; SESSION_REPORT.md. | 1h |

---

## Phase plan

- **Phase 0** — Wn.0 only. Land the gdb wrapper PR; trigger
  publish.yml via `workflow_dispatch` on `dev`; capture
  backtrace; write PRE_PHASE_AUDIT.md.
- **Phase 1** — Wn.1 fix.
- **Phase 2** — Wn.2 self-host mirror (conditional).
- **Phase 3** — Wn.3 smoke-step hardening (keep the Phase 0
  wrapper).
- **Phase 4** — Wn.4 regression test.
- **Phase 5** — Wn.5 closeout.

---

## Out of scope

- **macOS JSON corpus runtime crash** (skipped on Darwin in
  v5.47.x dev-branch maintenance). Different platform,
  different failure mode — handled in a parallel v5.49.x
  patch if and when the runtime-side investigation surfaces
  a fix.
- **Linux ASan leak gate baselining for goldens 100/101/102**
  (already landed on dev as a baseline update; not a v5.49.0
  scope item).
- **Borrow checker.** v6.0 thesis. Not v5.49.0 scope.
- **Hard removal of `{}`.** v6.0. Soft deprecation since
  v5.19.0 holds; v5.48.0 Te.3.D extends colon canonical form.
- **Wb.1.dx → universal Wb.\* sweep.** Covering every
  Windows OOM-class smoke point would be a structural
  refactor; v5.49.0 fixes the one we caught and ports the
  diagnostic to one more site (`publish.yml:596`).

---

## Risk

1. **Phase 0 gdb wrapper doesn't capture useful info.** Mitigation:
   the existing Wb.1.dx pattern at `publish.yml:813-825`
   captures `bt 30` against `mnc-stage1.exe` and is known to
   surface call sites. The smoke step uses the same binary
   shape; the same pattern should work. If the backtrace is
   truncated or unhelpful, fall back to running the smoke
   under a Windows ASan build (the v4.105.0+ ASan build job
   already exists for the compiler self-test) and re-extract.
2. **Fix turns out to be a Win64 ABI issue.** v5.26.0 Mb.\*
   and v5.29.0 Mb.10 already addressed Win64 sret/sarg
   shapes. If the Phase 0 root cause is a *new* Win64 ABI
   shape that emit_llvm_text.py / emit_llvm.mn miss, the
   fix scope grows. Mitigation: explicit Phase 0 sizing —
   if > 100 LOC, defer Wn.1 to v5.49.1 and ship v5.49.0 with
   Wn.0 + Wn.3 (the diagnostic infrastructure) only.
3. **STRICT preservation if Wn.1 touches self-host.** Same
   risk profile as v5.47.0 Cl.5: stage1 rebuild after each
   mirror edit; halt if STRICT diverges. The 50-release
   strict streak (v5.7.1 baseline → v5.47.0 HEAD at 244,654
   lines / 0 diff) is load-bearing for the v6.0 PLAN
   STRICT-gate carve-out.
4. **The bug is environmental, not a regression.** The
   `publish.yml` Windows SDK smoke runs on `windows-latest`;
   the runner image refresh schedule is outside our control.
   Phase 0 must distinguish "our binary is broken" from
   "the runner image changed". Repro on a clean Windows
   sandbox (or via the Wb.1.dx gdb backtrace pointing at
   our code) makes the distinction explicit. If the bug is
   environmental, v5.49.0 still ships Wn.0 + Wn.3 (the
   diagnostic infrastructure) and re-classifies Wn.1 as a
   carry-forward to whichever release picks up the runner-
   image follow-up.

---

## Success criteria

- ✅ `publish.yml` Windows SDK smoke step at line 596
  passes (`mnc.exe run hello.mn` exits 0).
- ✅ `publish.yml` Windows SDK smoke step at line 598
  (`mnc.exe build hello.mn -o hello.exe`) also passes —
  it's downstream of `run` so it was never reached pre-Wn.1.
- ✅ `publish.yml:596` carries a permanent gdb-backtrace
  wrapper mirroring Wb.1.dx (Wn.3).
- ✅ New regression test under `tests/integration/` or
  `tests/native/` reproduces the bug shape and is GREEN.
- ✅ STRICT 3-stage fixed point preserved (Wn.2 conditional).
- ✅ CHANGELOG `### Fixed` entry naming the call site Phase 0
  identified.
- ✅ CLAUDE.md release-notes entry; check_doc_freshness GREEN.
- ✅ SPEC.md header re-synced.
- ✅ `make ci-gates` GREEN; `make lint` clean; `pytest tests/`
  GREEN on Linux + macOS + Windows.

---

## Carry-forward delta

**Closes:**
- `mnc.exe run hello.mn` Windows SDK smoke OOM (newly-named
  carry from v5.47.x dev-branch CI hardening session;
  documented in v5.47.x SESSION_REPORT or PR_BODY when the
  Windows-publish failure was first observed).

**Inherits to v5.49.x patches:**
- Whatever Phase 0 surfaces that doesn't fit in v5.49.0 scope.
  Worst case: Wn.1 splits to v5.49.1 and v5.49.0 ships only
  the diagnostic infrastructure (Wn.0 + Wn.3).

**Inherits to v6.0:**
- macOS notarization (carry from v5.33.0 Nu.2; paid Apple
  Developer cert dependency).
- Ai.1 `_specialize_fn` body-walk (carry from v5.40.0;
  structural compiler work).
- Borrow checker (the v6.0 thesis).
- Hard removal of `{}` (carry from v5.19.0).
- Multi-level alias analysis.
- macOS JSON corpus runtime investigation (parallel v5.49.x
  patch candidate).

**Aggregate state entering v6.0:**
- Tensor closeout arc CLOSED (v5.45.0).
- Manifesto arc CLOSED (v5.43.0).
- Package-system runway CLOSED (v5.44.0).
- v5.43.0 lowerer-bug closeout CLOSED at v5.46.0.
- Pre-panel hygiene cleanup CLOSED at v5.47.0.
- v5 closeout panel CLOSED at v5.47.5 (9.76 / Option A;
  v6.0 green-lit).
- Te.3.D colon-block migration CLOSED at v5.48.0.
- Windows native smoke regression CLOSED at v5.49.0.
- 0 HIGH carries; ≤ 2 MEDIUM carries (the structural items
  legitimately deferrable to v6.0); ≤ 4 LOW carries.
