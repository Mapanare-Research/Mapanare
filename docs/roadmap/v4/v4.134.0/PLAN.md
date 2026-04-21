# Mapanare v4.134.0 — Sh.11 fix: lower_expr SIGSEGV unblocks fixed-point

> **Single-focus release.** Sh.11 was opened in v4.128.0 when Sh.8
> closed at source level — the strict 3-stage fixed-point script hit
> a new blocker: `lower_expr` SIGSEGV at `lower__lower_expr+0xc8ff`
> during MIR lowering of `mnc_all.mn`. This has blocked strict
> stage2-vs-stage3 convergence for v4.128.0 through v4.133.0. Fixing
> it unblocks the fixed-point metric that the v4.136.0 panel needs
> as evidence.

**Status:** PLANNED
**Prerequisite:** v4.133.0
**Estimated work:** 1 sprint (may extend to 2 if the bug is structural)
**Theme:** The last-mile blocker on "the compiler can compile itself end-to-end."

---

## Why v4.134.0 exists

The v4.120.0 panel flagged fixed-point as a blocker for v5. v4.128.0
reported progress by pivoting to a proxy measurement (Python-bootstrap
output vs mnc-stage1 output on 39 passing goldens). That proxy is
informative but **not** equivalent to strict fixed-point. The panel at
v4.136.0 will want the strict metric OR a credible case that the
proxy is sufficient.

Cobra (v4.120.0 panel, self-hosted reviewer): "A self-hosted compiler
that cannot reach 3-stage fixed-point is not v5.0.0 material."

## What we know about Sh.11

- Opened: v4.128.0 SESSION_REPORT, after Sh.8 (self-hosted `semantic.mn`
  None/Some/Ok constructor registration) closed at source level
- Site: `lower__lower_expr+0xc8ff` in mnc-stage1 built by Python
  bootstrap, triggered when mnc-stage1 tries to lower `mnc_all.mn`
- Comment at `mapanare/self/lower.mn:2856-2858` warns about "stale
  registers from caller's sret return" affecting list operations — may
  be related (v4.126.0 triage noted the L-family lower_expr crashes
  are "same family as Sh.2")
- Untried in the Sh.2 arc because the Sh.2 fixes (v4.131.0 List,
  v4.132.0 String) may or may not affect the lower_expr path — that's
  the first investigation step

## Phase 1 — Does the v4.131.0 + v4.132.0 Sh.2 arc already close Sh.11?

**First step: verify.** Rebuild stage1 with post-v4.132.0 fixes (done),
then run the fixed-point script:

```bash
bash scripts/verify_fixed_point.sh --keep 2>&1 | tail -20
```

If stage2 now compiles mnc_all.mn without crashing: Sh.11 was a
side-effect of Sh.2 and this release becomes a measurement release
(capture delta + document). Likely outcome given the overlap between
Sh.2 and L-family crashes.

If stage2 still crashes: continue to Phase 2.

- [ ] Run fixed-point script post-v4.132.0
- [ ] Capture stage2 output state (stderr, stdout, IR artifacts)
- [ ] If closed: write evidence report, skip to Phase 4
- [ ] If still crashing: proceed to Phase 2

## Phase 2 — Narrow the lower_expr crash

If the crash persists, use the v4.131.0 methodology:

- [ ] Rebuild stage2: `./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll 2> /tmp/stage2.stderr`
- [ ] If it segfaults: run under valgrind/ASan on mnc_all.mn
  ```bash
  timeout 600 valgrind --track-origins=yes --num-callers=30 \
    ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn 2> /tmp/sh11_valgrind.log
  ```
- [ ] Map frame 0 offset (0xc8ff) in current binary via `addr2line -e mapanare/self/mnc-stage1`
- [ ] Identify the specific expression form that triggers the crash
- [ ] Minimize to the smallest `.mn` reproducer

Hypothesis carry-overs from v4.126.0 and v4.131.0:
- Likely another extracted-alias-with-drop-glue bug, in a code path
  that isn't Copy (e.g., IndexGet, FieldGet with List element)
- Could be the lower.mn:2856-2858 "stale registers" warning being real
- Could be a fresh bug class discovered only by running through
  mnc_all.mn (which is 17K+ lines and exercises paths no golden does)

## Phase 3 — Implement the fix

Depends on Phase 2 findings. Three likely shapes:

- **Shape A (extracted alias, Sh.2 family)**: extend the v4.131.0 /
  v4.132.0 pattern to additional tracking types (Map, Signal, Stream)
  or additional extraction points (IndexGet, EnumPayload directly).
  ~20-40 lines in `emit_llvm_text.py`.
- **Shape B (self-hosted lowering bug)**: the bug is in `mapanare/self/lower.mn`,
  not in the Python emitter. Fix at the source; rebuild; retest.
- **Shape C (structural)**: the bug requires architectural changes.
  Ship findings, document, descope the fix to v4.134.1 or v5.x.

- [ ] Implement the fix based on Phase 2 shape
- [ ] Rebuild mnc-stage1
- [ ] Re-run fixed-point script — stage2 must produce IR (not crash)
- [ ] Compare stage2 vs stage3 — measure diff (new metric)

## Phase 4 — Measurement and documentation

- [ ] Produce `docs/roadmap/v4/v4.134.0/FIXEDPOINT.md` with:
  - Strict 3-stage result (stage2 == stage3 or diff stats)
  - Comparison with v4.128.0 proxy metric
  - Any remaining divergence categories (similar to v4.127.0 FIXEDPOINT_BASELINE)
- [ ] Golden sweep through mnc-stage1 — no regression
- [ ] Sanitizer sweeps — no regression
- [ ] Pytest — no regression

## Phase 5 — Closeout

- [ ] `SESSION_REPORT.md`
- [ ] `CHANGELOG.md [4.134.0]` entry
- [ ] Roadmap status updates
- [ ] Bump to 4.135.0

---

## Exit criteria

| # | Check | Target | Stretch | Downside |
|---|---|---|---|---|
| 1 | Sh.11 crash reproduces OR does not | determined | — | mandatory |
| 2 | Strict 3-stage fixed-point runs to completion | yes | stage2 == stage3 | stage2 crashes → ship Phase 2 findings |
| 3 | Fixed-point diff metric published | yes | ≤ 5000 lines (v4.128.0 baseline was 9,425) | no metric → Sh.11 structural, defer fix |
| 4 | No golden regression | 53+/65 | — | mandatory |
| 5 | No sanitizer regression | v4.132.0 baseline | — | mandatory |
| 6 | No pytest regression | v4.133.0 baseline | — | mandatory |

---

## Two realistic outcomes

**Optimistic (Shape A or B closes Sh.11 in one sprint):**
- Strict fixed-point runs, even if diff is not zero
- Panel gets a real fixed-point number (even "diff size N") instead of
  "blocked by Sh.11"
- v4.135.0 proceeds to pre-panel refresh as planned

**Realistic if Sh.11 is structural:**
- Phase 2 finds the bug is not localized (multi-site ownership semantics
  issue in self-hosted lower.mn)
- Phase 3 descopes; Phase 4 documents findings with minimal reproducer
- v4.134.1 or v4.135.0 continues the fix
- v4.136.0 panel sees "Sh.11 documented, partial fix, v5.x track" —
  still better than v4.135.0 if the investigation is thorough

---

## What this release does NOT do

- Rewrite the self-hosted `lower.mn` for ownership semantics (v5.x if needed)
- Close unrelated open dockets (ABI.1, Gr.1/Gr.2/Sem.1, Dr.1 — all v5.x)
- Panel anything

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Sh.11 turns out to be already-closed by Sh.2 arc | medium | low | Phase 1 verifies; this is net-positive (release becomes measurement-only) |
| Bug is structural, requires self-hosted rewrite | medium | high | Shape C: ship findings + minimal reproducer; descope |
| Fix reveals downstream Sh.12 (next blocker) | low | medium | Document chain; either continue or panel with "fixed-point has [N] remaining blockers" |
| Fixing Sh.11 opens pytest regressions | low | high | Full sweep; revert if necessary |

---

## After v4.134.0

- v4.135.0 — Pre-panel refresh (flaky audit #4, fresh valgrind/ASan,
  benchmark refresh, MEASUREMENTS.md finalization)
- v4.136.0 — THE PANEL
