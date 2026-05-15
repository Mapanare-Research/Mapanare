# v5.55.0 — Ai.1 + Nu.2 — `_specialize_fn` body-walk fix + macOS notarization

**Status:** PLANNING
**Type:** Final v5.x drain release. Closes the two remaining MEDIUM
carries before v6.0 PLAN entry. **Ai.1** unblocks the manifesto-arc
tail (the v5.40.0 `ask` keyword sugar that v5.41.0 deferred); it's a
Python-bootstrap lowerer fix per v5.40.0 SESSION_REPORT.md:147+.
**Nu.2** closes the v5.33.0 macOS notarization carry — the `dist/mapanare/mnc`
Mach-O arm64 binary currently ships with ad-hoc signing, which
triggers macOS Gatekeeper warnings on first run. Both items are
unrelated; bundling them in one release because each is too small
for its own release and v5.55.0 is the explicit "close the docket"
slot before v6.0.
**Machine requirements:** Ai.1 is Windows-or-Mac (Python-bootstrap
edit). **Nu.2 requires Mac access** + an Apple Developer cert
(personal or organizational) + an app-specific password for
notarytool. If Mac access is not available, ship v5.55.0 with Ai.1
alone and defer Nu.2 to v5.55.1 or v6.0 PLAN.
**Breaking:** No. Ai.1 is a lowerer fix; existing user code that
compiled correctly continues to compile correctly (the bug was
miscompiled output, not rejection). Nu.2 is build-system / signing
change with no source impact.
**Prerequisite:** v5.54.0 ships (Cl.2 + Cl.3 + Cl.4r closed).
**Estimated effort:** 1-1.5 sessions. Ai.1 is ~30 LOC + tests; Nu.2
is ~50 LOC YAML in `.github/workflows/publish.yml` + Apple Developer
secrets configuration.

---

## Why this exists

**Ai.1 — `_specialize_fn` body-walk.** v5.40.0 SESSION_REPORT.md:135
captured the root cause:

> `mapanare/lower.py::_specialize_fn` substitutes parameter and
> return types when monomorphizing a generic function, but does not
> walk the body to rewrite nested `CallExpr.type_args`. Confirmed
> empirically: a user-level `fn process<T>(x: T) -> T { return
> identity::<T>(x) }` monomorphizes `process<Int>` with
> parameter/return rewritten to Int but the `identity::<T>` call
> inside the body keeps `<T>` literal instead of `<Int>`.

This blocks the v5.41.0 `ask` keyword sugar (Ai.1 + Ai.2 in the
v5.40.0 docket): the `ask` syntax desugars to a generic-typed
intrinsic call whose `type_args` need rewriting through the
substituted body. Without the body-walk, every user-level generic
that calls a generic intrinsic miscompiles the inner call's
type_args.

Fix shape (per v5.40.0 SESSION_REPORT's gloss): extend
`_specialize_fn` to recursively rewrite `CallExpr.type_args`
through the substituted body via an `_rewrite_type_args` helper
that walks every Call / FieldAccess / Constructor node and
substitutes T → concrete-type when T appears in `type_args`.

**Nu.2 — macOS notarization.** v5.33.0 Nu.2 SESSION_REPORT.md:92
shipped `mnc-darwin-arm64-native` as a workflow artifact with
ad-hoc signing. v5.33.0 SESSION_REPORT.md:328+ flagged this as
LOW → MEDIUM by user-visibility: macOS users hit Gatekeeper's
"unidentified developer" dialog on first `mnc` invocation, work
around with `xattr -dr com.apple.quarantine`, file occasional
GitHub issues. Notarization closes the loop:

1. `codesign --deep --force --options runtime --timestamp` against
   an Apple Developer ID Application certificate.
2. Submit to Apple notary service via `xcrun notarytool submit`.
3. Staple notarization ticket via `xcrun stapler staple`.
4. CI verifies via `spctl --assess --type execute`.

`.github/workflows/publish.yml`'s `build-native` macOS job adds
these steps. Apple Developer ID secrets stored in GitHub Actions
encrypted secrets: `APPLE_ID`, `APPLE_TEAM_ID`,
`APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_DEVELOPER_ID_CERT`,
`APPLE_DEVELOPER_ID_CERT_PASSWORD`.

---

## Items in scope

### Ai.1 — `_specialize_fn` body-walk fix

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Ai.1.0** | MEDIUM (gate) | Phase 0 audit. Reproduce the miscompile on a synthesized test case (e.g., `fn process<T>(x: T) -> T { return identity::<T>(x) }; process::<Int>(5)`). Localize `_specialize_fn` in `mapanare/lower.py`; identify the body-walk insertion point; estimate LOC. Per v5.40.0 SESSION_REPORT.md's gloss this is ≤ 30 LOC predicted. Output: `PRE_PHASE_AUDIT.md` with the reproducer + sized fix. | 1h |
| **Ai.1.1** | MEDIUM | Apply the fix. Extend `_specialize_fn` with `_rewrite_type_args(body, type_subst_map)` helper that walks every Call / FieldAccess / Constructor node and substitutes T → concrete-type in `type_args`. | 1-1.5h |
| **Ai.1.2** | MEDIUM | Self-host mirror in `mapanare/self/semantic.mn` or `mapanare/self/lower.mn` (wherever the equivalent of `_specialize_fn` lives). Per v5.46.0 Lf.\* precedent the self-host may already have the fix or may need an analogous extension. | 0-1.5h |
| **Ai.1.3** | MEDIUM | Falsifiability test in `tests/llvm/test_generic_specialization.py` or new `tests/llvm/test_specialize_fn_body_walk.py`. Module docstring names the revert signature (the inner Call's `type_args` literal-T at IR level). | 0.5h |

### Nu.2 — macOS notarization

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Nu.2.0** | MEDIUM (gate) | Phase 0 audit. Confirm Apple Developer account access + cert available. Decide cert provisioning: personal Apple ID + free dev cert (limited; may not pass notary), or paid Apple Developer Program ($99/year + Developer ID Application cert). Free cert path may NOT enable notarization — Apple notary requires a paid Developer ID. If paid cert unavailable, defer Nu.2 to v5.55.1 / v6.0. Output: `PRE_PHASE_AUDIT.md` with cert decision + secrets list. | 1h (mostly waiting on Apple) |
| **Nu.2.1** | MEDIUM | GitHub Actions secrets configuration. Store `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_DEVELOPER_ID_CERT` (base64-encoded p12), `APPLE_DEVELOPER_ID_CERT_PASSWORD` in the repo's encrypted secrets. | 0.5h |
| **Nu.2.2** | MEDIUM | Extend `.github/workflows/publish.yml` `build-native` macOS job. Add three steps after the existing build: (1) `codesign --deep --force --options runtime --timestamp --sign $APPLE_DEVELOPER_ID dist/mapanare/mnc`; (2) `xcrun notarytool submit dist/mapanare/mnc --apple-id $APPLE_ID --team-id $APPLE_TEAM_ID --password $APPLE_APP_SPECIFIC_PASSWORD --wait`; (3) `xcrun stapler staple dist/mapanare/mnc`. ~50 LOC YAML. | 1h |
| **Nu.2.3** | MEDIUM | Verification step. Add `spctl --assess --type execute --verbose dist/mapanare/mnc` to `macos-tarball-smoke` job; expected output `accepted source=Notarized Developer ID`. Falsifiability anchor: revert Nu.2.2 → smoke fails with `rejected`. | 0.5h |
| **Nu.2.4** | LOW | Docs refresh. `docs/INSTALL.md` macOS section: remove the `xattr -dr com.apple.quarantine` workaround paragraph; replace with "macOS releases from v5.55.0 are notarized — no first-run dialog." | 0.25h |

---

## Phase plan

- **Phase 0** — Ai.1.0 + Nu.2.0 in parallel. Combined
  `PRE_PHASE_AUDIT.md` covers both. Critical gate: Nu.2.0 verifies
  Apple Developer access — if unavailable, Nu.2 splits to v5.55.1
  and v5.55.0 ships Ai.1 alone.
- **Phase 1** — Ai.1.1 + Ai.1.3 (Python bootstrap + falsifiability).
- **Phase 2** — Ai.1.2 (self-host mirror, conditional).
- **Phase 3** — Nu.2.1 (secrets config). **Machine: Mac required**
  for cert export to p12.
- **Phase 4** — Nu.2.2 + Nu.2.3 (workflow + verification).
- **Phase 5** — Nu.2.4 (docs refresh).
- **Phase 6** — Closeout. VERSION 5.54.0 → 5.55.0; CHANGELOG
  `### Fixed` for Ai.1 (with v5.40.0-carry citation); CHANGELOG
  `### Changed` for Nu.2 (Mac users no longer see Gatekeeper
  dialog); CLAUDE.md release-notes; SPEC.md re-sync;
  SESSION_REPORT.md; **v5.x drain CLOSED** narrative paragraph
  appended to `docs/roadmap/v5/CLOSEOUT_ARC.md`.

STRICT preserved by construction (Ai.1 may shift line count by
~30 if Ai.1.2 fires; Nu.2 is YAML-only). Goldens 103/103.

---

## Out of scope

- **Ai.2 — `ask` keyword sugar.** Ai.1 unblocks Ai.2 but Ai.2 is
  v5.55.x or v6.0 scope. v5.55.0 only fixes the lowerer; the
  keyword grammar work is the next step the user can elect.
- **Ai.8 — compile-time schema embedding.** v5.40.0 SESSION_REPORT
  scoped this with Ai.1 + Ai.2; defer with Ai.2.
- **macOS x86_64 native binary.** v5.33.0 scope-reduced to arm64
  only. Notarization for x86_64 is v5.55.x / v6.0 if x86_64 ships.
- **Apple Developer Program enrollment.** If the user is not
  enrolled, Nu.2 defers cleanly to a later release; v5.55.0 ships
  Ai.1 alone.
- **Windows code-signing.** Authenticode signing on Windows is a
  separate item (W.\* arc, never opened formally); v5.55.0 does
  not touch.
- **Borrow checker.** v6.0 thesis.

---

## Risk

1. **Ai.1 root-cause wider than predicted.** If `_specialize_fn`
   has more bugs than the body-walk gap (e.g., handles
   `FieldAccess.type_args` but not `Constructor.type_args`),
   Phase 0 surfaces them. Mitigation: scope the v5.55.0 fix to
   the load-bearing case (Call.type_args) and file remaining
   gaps as v5.55.x patches.
2. **Self-host mirror is significant work.** If `mapanare/self/`
   doesn't have the equivalent of `_specialize_fn`, the mirror
   is non-trivial (~100+ LOC). Mitigation: Phase 0 audit
   determines need before commitment; if > 50 LOC mirror,
   split to v5.55.1.
3. **Apple Developer cert provisioning delay.** First-time cert
   request via the Apple Developer portal can take 24-48h plus
   business-day approval. Mitigation: start Nu.2.0 audit early;
   if cert not provisioned in time, defer cleanly.
4. **Notarization rejection.** Apple notary can reject for
   unsigned dylib dependencies (the runtime archive linkage),
   missing entitlements, or hardened-runtime conflicts. Phase 0
   should run a manual notarization dry-run on a v5.54.0 binary
   to surface any architectural blockers before YAML lands.

---

## Success criteria

1. **Ai.1.** Synthetic test
   `fn process<T>(x: T) -> T { return identity::<T>(x) };
   process::<Int>(5)` compiles + executes via stage1 and prints
   the correct value; pre-fix the inner `identity::<T>` call
   emits `<T>`-typed IR causing miscompile or stage1 reject.
2. **Ai.1 self-host mirror.** Self-host `mnc-stage1` compiles
   the same test correctly via its own `_specialize_fn`
   equivalent.
3. **Nu.2 binary.** Downloaded macOS arm64 release tarball:
   `spctl --assess --type execute dist/mapanare/mnc` →
   `accepted source=Notarized Developer ID`.
4. **Nu.2 user experience.** Manual smoke on a fresh Mac:
   `mnc --version` runs without Gatekeeper dialog; no
   `xattr` workaround needed.
5. **Goldens 103/103** on Linux + Windows + macOS.
6. **STRICT** preserved at v5.55.0 baseline.
7. **Aggregate state entering v6.0 PLAN drafting:** **0 HIGH** /
   **0 MEDIUM** / **~2 LOW** (Lf.4 variant-name collision,
   defer-to-v6.0; any residual surfaced by Phase 0 but
   explicitly scoped out).
8. **v5.x drain narrative.** `docs/roadmap/v5/CLOSEOUT_ARC.md`
   appends a "v5.x docket drained at v5.55.0" paragraph naming
   the three drain releases (v5.53.0, v5.54.0, v5.55.0) and
   the docket items closed.

---

## Carry-forward to v6.0 PLAN drafting

After v5.55.0 ships, v6.0 PLAN drafting can begin per
`.reviews/v5.47.5/V5_TO_V6_CARRY.md`'s 9-item docket:

1. Borrow checker / multi-level alias analysis (closes Rt.04, Lk.1)
2. **Hard removal of `{}`** (only ~14 first-party residuals + stdlib
   + examples remain after v5.53.0)
3. STRICT 3-stage fixed-point gate carve-out
4. Tensor surface unification
5. Distributed-supervision orchestration
6. Registry-side package signing
7. `_specialize_fn` body-walk fix → **CLOSED at v5.55.0**
8. PRE_PHASE_AUDIT.md mandatory at every v6.x release
9. Convergent-recommendation pattern explicit

v6.0 enters from a clean docket. The v5.47.5 closeout panel's
Option A (v5 ships clean; v6.0 green-lit) preserves.
