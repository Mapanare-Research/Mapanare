# Mapanare v4.128.0 — Self-Hosted Fixed-Point Refinement

> **Buffer release 3.** Measure the stage2-vs-stage3 diff. Categorize
> every divergence. Fix the cosmetic ones. Record the delta.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.127.0
**Delta review:** No
**Full panel:** No (deferred to v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Continue the fixed-point work from v4.127.0. Attempt strict
stage2-vs-stage3 (Sh.8 closure) if cheap; otherwise continue the
Python-vs-self-hosted proxy on the A/C buckets (next largest after the M
bucket that v4.127.0 closed).

---

## Scope

Fixed-point convergence is a key metric for the v4.130.0 panel. Cobra
(ABI reviewer) asks: "Is the fixed-point real?" Rattler (LLVM reviewer)
asks: "Is the IR correct across self-compilation stages?"

v4.127.0 reduced the Python-vs-`mnc-stage1` proxy divergence from 9,971
to 9,535 unified-diff lines (-4.4%) by closing the **M bucket**
(module-header metadata: TBAA removal, target datalayout/triple,
version sync) and the whitespace-after-`=` builder family. The strict
3-stage stage2-vs-stage3 measurement remains blocked by docket **Sh.8**
(self-hosted `semantic.mn::infer_expr` fails on bare `None` — Python
bootstrap special-cases it as a bare Option variant in
`_lower_identifier`).

This release:

1. **Attempts Sh.8 closure** via a 3-line special-case in
   `semantic.mn::infer_expr`'s `ident` branch (mirrors Python's
   `_lower_identifier` behaviour). Smallest-scope of the three Sh.8
   options documented in v4.127.0's SESSION_REPORT.
2. **If Sh.8 closes**: measures strict stage2-vs-stage3, categorizes
   the diff, fixes top 2 cosmetic categories, records delta.
3. **If Sh.8 does not close**: reverts the fix, continues the
   Python-vs-self-hosted proxy from v4.127.0, targets the A (attributes,
   328 lines) and C (constants, 301 lines) buckets — next largest after
   the M bucket that v4.127.0 closed.

---

## Phase 1 — Sh.8 closure attempt

- [ ] Add 3-line special case to `mapanare/self/semantic.mn::infer_expr`
  ident branch: if `name == "None"` before `scope_lookup`, return
  `make_type("Option")`. Matches Python `mapanare/lower.py::_lower_identifier`
  behaviour.
- [ ] Regenerate `mnc_all.mn` via `bash scripts/concat_self.sh`.
- [ ] Rebuild `mnc-stage1` via `python3 scripts/build_stage1.py`.
- [ ] Run `DIFF_THRESHOLD=999999 bash scripts/verify_fixed_point.sh --keep`.
- [ ] If Stage 1 succeeds (stage2.ll emits, llvm-as validates) and
  Stage 2 succeeds (mnc-stage2 builds, stage3.ll emits, llvm-as
  validates): Sh.8 closed. Proceed to Phase 2.
- [ ] If any stage fails: revert Sh.8 change, pivot to proxy on A/C
  buckets per Phase 1-proxy.

## Phase 1-proxy (fallback) — continue v4.127.0's proxy on A/C buckets

- [ ] Re-run `scripts/measure_divergence.py` to confirm v4.127.0's
  9,535-line baseline still holds on current HEAD.
- [ ] Investigate the A bucket: which 328 lines of function/parameter
  attribute differences are reducible? Likely candidates: attribute
  order, `willreturn` placement.
- [ ] Investigate the C bucket: which 301 lines of string-global
  ordering / format are reducible? Likely candidates: self-hosted
  pre-emits format strings unconditionally (`@.fmt_int`, `@.fmt_int_nl`,
  `@.fmt_float`, `@.fmt_float_nl`, `@.newline`) even when no
  `print(int)` call exists.

## Phase 2 — Strict stage2-vs-stage3 measurement (requires Sh.8 closed)

- [ ] Line-level diff: `diff /tmp/stage2.ll /tmp/stage3.ll | wc -l`.
- [ ] Function-level diff: `python3 scripts/ir_doctor.py diff-ir
  /tmp/stage2.ll /tmp/stage3.ll` — counts divergent functions, ignores
  label renumbering.
- [ ] Record baseline in `docs/roadmap/v4/v4.128.0/STRICT_FP_BASELINE.md`.

## Phase 3 — Categorize divergences

- [ ] For the strict 3-stage case (or proxy if Phase 1 fell back),
  classify each divergence into L / C / A / S / W / M buckets.
- [ ] Identify top 2 categories by frequency.
- [ ] Document in `STRICT_FP_BASELINE.md` (or continuation doc).

## Phase 4 — Fix top 2 cosmetic categories

- [ ] Apply fixes in `mapanare/self/emit_llvm.mn` and/or
  `mapanare/self/emit_llvm_ir.mn`.
- [ ] Re-run phase 2 measurement.
- [ ] Record post-fix delta.

## Phase 5 — Verify + ship

- [ ] `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  — verify no golden regressions vs v4.127.0's 39/65.
- [ ] `make test` green (pytest excluding bootstrap; failure set
  byte-identical to v4.127.0 HEAD baseline of 38 failed / 5,061 passed).
- [ ] `make lint` — no new findings on touched files.
- [ ] `CHANGELOG.md [4.128.0]` entry.
- [ ] `SESSION_REPORT.md` written.
- [ ] `VERSION` bumped in final commit (to 4.129.0).
- [ ] Roadmap status updated: this PLAN's Status → DONE, v4/README.md
  row, ROADMAP.md row, CLAUDE.md current version.

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Sh.8 attempted (closed or explicitly deferred with reason) | commit diff + SESSION_REPORT section |
| 2 | Fixed-point baseline measured (strict 3-stage OR proxy) | STRICT_FP_BASELINE.md (or proxy baseline) |
| 3 | All divergences categorized (L/C/A/S/W/M) | STRICT_FP_BASELINE.md breakdown |
| 4 | At least one cosmetic category reduced | commit diff + post-fix delta |
| 5 | Post-fix delta measured and recorded | post_fix.json + SESSION_REPORT |
| 6 | No regressions in golden tests (39/65 preserved) | `test_native.py` log |
| 7 | Standard closeout clean (pytest + lint + CHANGELOG + SESSION_REPORT + VERSION) | CI logs |

---

## What this release does NOT do

- **Run a panel.** Next panel is v4.130.0.
- **Attempt the remaining S/A/C buckets in a single release.** v4.127.0
  closed M; v4.128.0 targets A or C (one of two). S remains out of
  scope — its size (7,000 lines) reflects systemic differences
  (inline_small_functions on Python, runtime-decl emit-on-demand).
- **Close docket Sh.1** (inline_small_functions in self-hosted). That's
  a separate release's work.
- **Rewrite the emitters.** All fixes are additive / substitutive at
  existing emission sites.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Sh.8 fix breaks existing `none` lowercase handling | low | high | `none` goes through the same `expr_kind == "none_lit"` path (semantic.mn:577); the new `ident` special-case for "None" fires *before* `scope_lookup` so it only affects the uppercase bare-identifier path. `none` is lexed as `KW_NONE` → `Expr::NoneLit`, never hits the `ident` branch. |
| Sh.8 closure surfaces new failures in stage2 or stage3 | medium | medium | Fall back to proxy on A/C buckets. v4.127.0's PLAN anticipated this; the proxy is a valid substitute. |
| A or C bucket fix regresses a golden | medium | high | Run `test_native.py --stage1` after every change. Revert any change that drops the 39/65 count. |
| mnc-stage2 teardown crash triggers false regression | low | low | `verify_fixed_point.sh:123-142` already handles the teardown-crash case documented at v4.29.0. |

---

## After v4.128.0

v4.129.0 — documentation and SPEC sync (originally planned as v4.128.0;
bumped one release because v4.128.0 took the fixed-point refinement
slot per the edited PROMPT). Close documentation gaps before the
v4.130.0 panel.
