# Mapanare v5 Readiness — Updated for v4.130.0 Panel

> Written at v4.125.0 (2026-04-14) as **informational input** to the
> v4.130.0 panel. Updates the v4.119.0 / v4.120.0 snapshot
> (`docs/roadmap/v4/v4.120.0/V5_READINESS.md`) with the closure status
> of every item from that document plus the new dockets opened by the
> v4.118.0 benchmark report and the v4.120.0 panel itself.
>
> **Stance: neutral.** No advocacy. The panel decides based on this plus
> the FINAL_REPORT_v4.130.md benchmark and the docket ledger.
>
> **Diff from v4.120.0 readiness:** Three of the eight "would embarrass
> v5" items closed (Qs.1, Rt.1 substantially, dead `optimizer.py`). One
> closed structurally (TBAA dead-declaration removed). Test hygiene
> closed (22/22 deterministic failures resolved at v4.121.0). One new
> docket opened (ABI.1 — by-value 24-byte struct return on inline
> enums; replaces ~half of Rt.1 with a smaller follow-up).

---

## Decision rule (the mechanical gate, unchanged from v4.99.0)

- **Aggregate ≥ 9.0** AND **0 NEEDS WORK** → Option A — tag `v5.0.0`
- **Aggregate 8.5 – 9.0** → Option C — tag + continue
- **Aggregate < 9.0** with any NEEDS WORK → Option B — continue v4.131.0+

Panel is not asked for narrative judgment. The decision follows the
aggregate and the NEEDS-WORK count.

---

## What a "v5" tag would be (unchanged)

v5.0.0 is a **major version**: first breaking-change line after v4.x.
A shipped v5 carries the expectation that the language is stable at
this surface, the compiler is self-hosting in production, and the
runtime is safe to link into real programs.

(Same constraints and non-constraints as v4.120.0 readiness. The
inventory below describes what shipped between v4.120.0 and v4.125.0.)

---

## Status matrix — what changed since v4.120.0

Color key: ✅ done · ◐ partial · ⬜ planned · ✖ not implemented · 🆕 new since v4.120.0 readiness · 🔄 updated since v4.120.0 readiness.

### Language core — closeout-arc updates

| Feature | Status | Evidence |
|---|---|---|
| Bounded-generic trait fn (e.g., `fn max<T: Ord>(a: Int, b: Int) -> Int`) | 🔄 ✅ | **v4.121.0** added `_type_params_used_in_signature` in `mapanare/lower.py`; functions whose type params don't appear in signature are no longer mis-deferred to monomorphization. |
| DWARF debug info | 🔄 ◐ | Still SPEC §21.3 deferred to v5.x; **v4.121.0** restored the user-facing `warning: -g / --debug is a no-op; DWARF debug info emission is deferred to v5.x` deferral message in `cli.py::_resolve_debug`. No silent surprise. |
| `List<Int>` indexing in argument position | 🔄 ✅ | **v4.122.0** fixed Qs.1 — `_lower_let` in `mapanare/lower.py` now rebinds `val = Value(name=val.name, ty=declared)` after the empty-list annotation patch, so `IndexGet.dest.ty` resolves to `i64` not `ptr`. Regression test at `tests/golden/65_list_int_indexing.mn` (5 invariants in `tests/llvm/test_emitter_hardening.py::TestListIntIndexingQs1`). |
| Boxed-enum payloads for pointer-fits variants | 🔄 ✅ | **v4.124.0** Rt.1 — `mapanare/emit_llvm_text.py` now stores small enum payloads inline as `{i64, i64, ..., i64}` instead of `{i64, ptr}` + heap allocation for variants where every field is ≤ 8 bytes (Int / Float / Bool / pointer-shaped). enum_match benchmark: 3.026 → 1.308 ms (2.31× speedup, 0.91× of Rust). |

All other language-core rows from the v4.120.0 readiness are unchanged.

### Self-hosted compiler — unchanged

| Milestone | Status | Notes |
|---|---|---|
| Stage1 golden parity | 26/64 literal, 39/64 effective | unchanged from v4.120.0; Sh.8 (None/Some/Ok ctor) still blocks fixed-point self-compilation |
| Sh.4/5/6/7 (async / const / tensor / closure) | open | deferred to v5.x track |
| Self-hosted Rt.1 (inline enum payloads in `self/emit_llvm.mn`) | open | v4.124.0 PLAN decision 3 deferred to avoid destabilising the Sh.8 landing path. v5.x track |

### Runtime — unchanged

All v4.120.0 readiness rows still hold. No runtime code changed in the closeout arc (v4.121.0–v4.125.0). `libmapanare_rt.a` is byte-identical to v4.119.0.

### Test infrastructure — closeout-arc updates

| Item | Status | Evidence |
|---|---|---|
| 22 deterministic test failures (v4.117.0 audit) | 🔄 ✅ | **v4.121.0** closed all 22 — 14 stale CLI tests retired/rewritten against `build`, 4 hygiene assertions re-pinned at `-O0`, 3 DWARF-deferral warnings + 1 bounded-generic trait fixed by code change. |
| `tests/optimizer/test_optimizer.py` (1,029 lines, 9% coverage) | 🔄 ✅ | **v4.123.0** deleted along with the dead `mapanare/optimizer.py` (1,203 lines). MIR-level coverage in `tests/mir/test_mir_opt.py` is the live replacement. Net −1,963 lines across the dead-code sweep. |
| TBAA metadata in module header | 🔄 ✅ | **v4.123.0** removed the TBAA tree (`!1`–`!9`) from `_emit_module`; v4.109.0 forensics had confirmed it was 100% dead. Module version metadata `!mapanare.version` retained. |
| 5-run flaky audit | 🆕 ✅ | **v4.125.0** `docs/roadmap/v4/v4.125.0/FLAKY_AUDIT.md` — pytest 5x sequential, identical pass/fail counts, deterministic failure set. |

### Documentation — unchanged from v4.120.0 readiness

`README.md` performance section refreshed at v4.125.0 with the v4.124.0 enum_match win and updated geomean ratios. Version badge bumped from 4.116.0 → 4.125.0.

### CI / quality gates — unchanged

10 enforcing gates as of v4.120.0; the dead-code sweep (v4.123.0) removed 1 informational coverage gate's underlying module without affecting the gate itself (coverage now reports against the live MIR optimiser). Sanitizer gates (ASan, TSan-async, valgrind) unchanged.

---

## "Would embarrass a v5 label" items — closure walk

The v4.120.0 readiness identified 8 items. The v4.125.0 status:

| # | Item from v4.120.0 readiness | v4.125.0 status |
|---|---|---|
| 1 | **Self-hosted async/tensor/const gaps** (Sh.4/5/6/7) — 13 of 25 self-hosted golden failures | **OPEN** — v5.x track. The v4.124.0 PLAN explicitly deferred mirroring the Rt.1 fix to self-hosted to avoid destabilising Sh.8's landing path. Affects users who run `mnc-stage1`; users of the Python bootstrap are unaffected. |
| 2 | **Fixed-point convergence cannot be proved today** (Sh.8) | **OPEN** — v5.x track. Mitigation: `verify_fixed_point.sh` is honestly named "divergence analysis + byref fix" since v4.114.0; the README "compiles itself" claim was tightened to reflect this in v4.116.0. |
| 3 | **No package manager / registry** | **OPEN** — single biggest ecosystem gap. v5.x deliverable. |
| 4 | **Boxed-enum payload overhead** (Rt.1) — `enum_match` 24× slower than C gcc and 2× slower than Rust | **CLOSED v4.124.0** — `enum_match` now 9.98× of C gcc and **0.91× of Rust** (Mapanare faster). Structural fix: payload type changed from `{i64, ptr}` (heap-allocated) to `{i64, i64, ..., i64}` (inline, register-passed) for pointer-fits variants. Residual 10× to C is by-value 24-byte struct return ABI — opened as new docket **ABI.1**, scoped for v5.x ABI work, not algorithmic. |
| 5 | **`List<Int>` indexing in print context** (Qs.1) — `arr.push(42); print(str(arr[0]))` prints `<?>` | **CLOSED v4.122.0** — single-line fix in `mapanare/lower.py::_lower_let` (rebind val.ty after the empty-list annotation patch). Regression suite at `tests/golden/65_list_int_indexing.mn` plus 5 IR-level invariants in `tests/llvm/test_emitter_hardening.py::TestListIntIndexingQs1`. |
| 6 | **`optimizer.py` at 9% coverage** (likely dead) | **CLOSED v4.123.0** — file deleted (1,203 lines). The `--legacy-optimizer` CLI flag and its argparse registration also gone. `OptLevel` is now an alias for `MIROptLevel`. Total dead-code sweep: −1,963 lines. |
| 7 | **14 stale CLI tests** (pre-rename, asserting on `mapanare compile`) | **CLOSED v4.121.0** — `TestCompile` class deleted; `TestArgparse::test_compile_*` rewritten against `build`; `TestOptLevelFlags` 7 `compile_*` tests rewritten or downgraded to argparse smoke checks. Negative-path coverage retained in `TestCheck`. |
| 8 | **TBAA metadata declared but not wired** (TBAA.1) — comment misleading | **CLOSED v4.123.0** — declaration block removed from `mapanare/emit_llvm_text.py::_emit_module`. Zero behaviour change (load/store sites never referenced the metadata anyway, per v4.109.0 forensics). Comment is gone. |

**Score: 5 of 8 closed (4 with code change, 1 with structural removal). 3 remain open** — all on the v5.x track, none CRITICAL, all sized:

- Sh.4/5/6/7 self-hosted gaps — affects `mnc-stage1` users only; Python bootstrap handles all features
- Sh.8 fixed-point — internal milestone; user-visible correctness unaffected
- Package manager — ecosystem gap; SPEC adequate for single-program work

---

## New dockets opened during the closeout arc (v4.121.0 – v4.125.0)

| # | Docket | Origin | Status | Notes |
|---|---|---|---|---|
| ABI.1 | by-value 24-byte struct return ABI on inline enums | v4.124.0 + v4.125.0 benchmark | **OPEN** — v5.x ABI work | Replaces ~half of Rt.1 (the algorithmic half is closed; the ABI residual is what's left). Closing it requires SRet-aware calling-convention changes or LLVM-optimiser SROA-of-struct-return aggression. Documented; sized; not panel-blocking. |

---

## What would need to change between v4.125.0 and v5.0.0 (if tagged)

**Nothing required.** v4.125.0 is the last release before the v4.130.0 panel. v4.126.0–v4.129.0 are buffer releases for any items the panel surfaces or any items the closeout arc missed; if v4.125.0 found zero issues (current expectation: the 5-run flaky audit is clean), these can address polish, documentation, or remaining v4.120.0 panel carry-forward items.

If the v4.130.0 panel votes Option A, the `v5.0.0` tag would be applied to the v4.129.0 commit (or a successor no-change commit), CHANGELOG `[5.0.0]` would replace `[Unreleased]`, the `VERSION` file would read `5.0.0`, and the `dev` branch would continue as `v5.1.0` development.

No additional engineering work is required to "earn" v5 between now and the panel. The v4.120.0 panel's docket items are largely closed (5 of 8 from the readiness gap list, plus 22/22 from the deterministic test-failure audit). Whether "5/8 + 22/22" plus the 2.31× enum_match speedup plus a clean 5-run flaky audit corresponds to **≥ 9.0 aggregate and 0 NEEDS WORK** is the v4.130.0 panel's judgement.

---

## Author's neutral summary (delta from v4.120.0)

- The closeout arc (5 releases: v4.121.0–v4.125.0) **closed 5 of 8 v4.120.0 readiness gaps** and **all 22 v4.117.0-audit deterministic test failures**.
- The v4.124.0 Rt.1 fix delivered a **2.31× speedup on `enum_match`** — the named v4.120.0 panel performance docket. Mapanare now beats Rust on this workload.
- The geomean closes from 5.46× to 4.52× of C gcc — Mapanare and Rust are statistically tied at the geomean level (4.52× vs 4.51×).
- Net code-line change across the closeout arc: **−1,800 lines** (predominantly v4.123.0's dead-code sweep, partially offset by Rt.1 and Qs.1 fixes).
- One new docket opened: ABI.1 (by-value struct return ABI), v5.x track, panel-acknowledged residual.
- 5-run flaky audit: clean (`docs/roadmap/v4/v4.125.0/FLAKY_AUDIT.md`).

**Whether this is a v5 is for the panel.** The evidence is in the
repository. The decision rule is mechanical. This document states only
what is done, what isn't, and where the reader can verify each item.

## Cross-references

| To verify | Read |
|---|---|
| v4.120.0 readiness baseline | `docs/roadmap/v4/v4.120.0/V5_READINESS.md` |
| v4.118.0 benchmark baseline | `benchmarks/FINAL_REPORT_v4.120.md` |
| v4.125.0 benchmark report | `benchmarks/FINAL_REPORT_v4.130.md` (this release) |
| Closeout-arc release notes | `docs/roadmap/v4/v4.{121,122,123,124,125}.0/SESSION_REPORT.md` |
| Open docket ledger | `.reviews/CARRY_FORWARD.md` |
| 5-run flaky audit log | `docs/roadmap/v4/v4.125.0/FLAKY_AUDIT.md` |
| Language spec | `docs/SPEC.md` |
| Recovery arc narrative | `docs/roadmap/v4/v4.120.0/RETROSPECTIVE.md` |
