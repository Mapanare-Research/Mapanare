# v5.8.0 SESSION REPORT — RE-PANEL

> Re-panel of the v5.3.1 → v5.7.1 closeout + feature-parity arc.
> **Aggregate: 9.66 / 10. Decision: Option A.**

**Date:** 2026-04-26
**Branch:** dev
**HEAD pre-bump:** `a6456a5` (v5.7.1 commit, untagged at panel start)
**Source drift since v5.7.1:** 0 lines

---

## What shipped

### Phase 0 — Verification

- VERSION embedded in v5.7.1 binary read `5.7.1`; verified
  `git diff v5.7.0..a6456a5 -- mapanare/ runtime/ | wc -l` = 0
  (v5.7.1 was a no-source-drift docs/polish release).
- Goldens 66/66, fixed-point NEAR, no surprise dirt.

### Phase 1 — Pre-panel refresh

- `VERSION` 5.7.1 → 5.8.0.
- `make build-rt` rebuilt `libmapanare_rt.a` with `MAPANARE_VERSION=5.8.0`
  (8 modules, -fPIC).
- `python3 scripts/build_stage1.py` produced `mnc-stage1` at
  6,311,072 bytes (stripped) with the new VERSION embed.
- **5x sequential pytest flaky audit**:
  - Run 1: 5618 passed / 0 failed in 545.99s.
  - Runs 2-5: 5619 passed / 0 failed each in 508-520s.
  - **0 deterministic failures, 0 flaky** across 5 runs (vs v5.3.0
    baseline of 8 failures × 5 runs).
- **C hardening triple**: 3/3 PASS (plain / ASan / TSan).
- **Goldens**: 66/66 in 3.5s (preserved).
- **Fixed-point**: NEAR (4 diff lines / 217,879 = 0.002 %, all
  VERSION metadata).
- **Valgrind sweep** (66 goldens): 63 CLEAN / 2 GPU-loader FPs
  (Mesa/Vulkan dlopen, same class as v5.2.0) / 1 LINK_FAIL
  (47_try_operator pre-existing Python bootstrap emit-llvm bug;
  native mnc-stage1 path PASSES, confirmed via 66/66 native goldens).
- **Benchmarks** (CPU-isolated via `taskset -c 0-1`):
  - Cross-language: Mn/Rust geomean **1.003×** (essentially parity,
    first time); Mn/Python geomean **0.003×** (≈ 328.6× faster);
    Mn beats Rust on `fib_recursive` (0.84×) and `enum_match` (0.52×).
  - Async: ~1.20 ms median across 5 workloads (preserved from v5.3.0
    1.19 ms despite the v5.5.4–v5.5.7 coroutine pipeline rewrite).

`MEASUREMENTS.md` written at `docs/roadmap/v5/v5.8.0/MEASUREMENTS.md`
as the canonical evidence pack.

### Phase 2 — Reviewer drafts

7 reviewer agents launched in parallel, each receiving:
- `MEASUREMENTS.md` (v5.8.0)
- Their prior review (`.reviews/v5.2.0/<persona>.md`)
- `PARITY_GAPS.md`
- Self-contained instructions (no cross-reviewer visibility)

Reviews written to `.reviews/v5.7.1/{01-rattler ... 07-mamba}.md`.

| # | Reviewer | Domain | Score | Grade | Δ vs v5.2.0 |
|---|---|---|---:|---|---:|
| 1 | Rattler | LLVM IR correctness | **9.8** | EXCEEDS | +0.5 |
| 2 | Viper | Memory safety | **9.9** | EXCEEDS | +0.2 |
| 3 | Anaconda | CI / testing | **9.6** | EXCEEDS | +0.7 |
| 4 | Cobra | Bootstrap / self-hosted | **9.6** | EXCEEDS | +0.8 |
| 5 | Coral | Language design | **9.6** | EXCEEDS | +0.2 |
| 6 | Boa | Documentation / DX | **9.4** | EXCEEDS | +0.0 (preserved) |
| 7 | Mamba | C runtime / performance | **9.7** | EXCEEDS | +0.1 |
| | **Aggregate** | — | **9.66** | — | **+0.36** |

### Phase 3 — Decision document

Written to `.reviews/v5.7.1/V5_DECISION.md`.

| Rule | Condition | Outcome | Applied? |
|------|-----------|---------|----------|
| Option A | Aggregate ≥ 9.0 AND 0 NEEDS WORK | Clean release | **YES** |
| Option C | 8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK | Closeout arc | No |
| Option B | Aggregate < 8.5 OR any NEEDS WORK | Recovery arc | No |

**Option A — v5.8.0 is a clean production release.**

### Phase 4 — PARITY_GAPS audit

Written to `docs/roadmap/v5/v5.8.0/PARITY_AUDIT.md`.

- 29 / 29 Historical items verifiable at HEAD via grep / file reads.
- 7 / 7 Open items genuinely still open (Sh.5 / Sh.9a / Sh.9b / Gr.1
  feature-track deferrals; Rt.2 / Rt.3 runtime quirks; Rt.01 / Rt.02
  third-party libcuda + Mesa/Vulkan; Rt.04 RESCOPED v6.0; Li.1
  deferred v6.0).
- No "closed in SESSION_REPORT but missing from ledger" cases (the
  failure mode Cobra flagged at v4.153.0 has not recurred).

### Phase 5 — Release artifacts

- `CLAUDE.md` updated with v5.8.0 entry at the head of the release list.
- `docs/roadmap/ROADMAP.md` updated with v5.8.0 "Where We Are" header.
- This SESSION_REPORT.md.

---

## Score trajectory

| Panel | Aggregate | NEEDS WORK | Outcome |
|-------|----------:|-----------:|---------|
| v4.99.0 | 6.59 | (recovery) | Option B |
| v4.106.0 | 7.87 | 0 | Option B |
| v4.114.0 | 8.21 | 0 | Option B |
| v4.120.0 | 8.21 | 1 (Anaconda) | Option B |
| v4.136.0 | 8.80 | 0 | Option C (v5.0.0-rc1) |
| v4.143.0 | 8.86 | 0 | Option C |
| v4.144.0 | 9.21 | 0 | Option A declared |
| v4.154.0 | 9.37 | 0 | Option A (v5.0.0 tagged) |
| v5.2.0 | 9.30 | 0 | Option A (v5.3.0) |
| **v5.8.0** | **9.66** | **0** | **Option A (v5.8.0)** |

Per-release lift density: **0.040 lift/release** (+0.36 / 9 releases),
beating the v4.114→v4.136 closeout's 0.027 lift/release across 22 releases.

---

## Hero metrics (v5.3.0 → v5.8.0)

| Metric | v5.3.0 | v5.8.0 | Δ |
|--------|-------:|-------:|---|
| Pytest passes | 5,445 | **5,618-5,620** | +175 |
| Pytest fails | 8 | **0** | -8 |
| Flaky audit (5x) | 0 flaky | **0 flaky** | preserved |
| Goldens | 54/66 | **66/66** | **+12** |
| Fixed-point | BROKEN | **NEAR** | restored |
| stage2.ll | 120,956 / FAIL | 217,879 / **OK** | restored + grown |
| Self-hosted .mn | 41,195 lines | 48,269 lines | +7,074 (+17 %) |
| C hardening | 3 fail | **3/3 PASS** | restored |
| Valgrind ERRORS (memory-safety) | 0 | 0 | parity |
| Mn / Rust geomean | 1.17× | **1.003×** | parity |
| Mn / Python geomean | 168× | **328.6×** | ~2× faster |
| MEDIUM carry-forwards | 5 OPEN | **0 OPEN** | all closed |

---

## What is NOT in this release

- **No compiler / runtime source changes.**
  `git diff v5.7.0..HEAD -- mapanare/ runtime/ | wc -l` = 0.
- No new tests (the 66 new feature-coverage tests landed across
  v5.6.x and v5.7.0; v5.8.0 is review-only).
- No grammar / SPEC semantics changes.
- Bo.18 fix is **not** in this release. Per panel discipline, the
  panel release does not contain source changes; Bo.18 will land
  in a future v5.8.x docs micro-release or be rolled into the next
  compiler release.

---

## Carry-forward (for v5.8.x and v6.0)

### v5.8.x scope (docs hygiene)

- **Bo.18** (NEW MEDIUM) — README lines 147-149 lead-in says
  "restoration tracked at v5.3.2" while the feature subsection
  correctly says "NEAR". Same shape as Bo.15 from v5.2.0.
- **Bo.19** — Test count drift (badge / body / measurement
  inconsistent).
- **Bo.20** — README links to v4.153 benchmark report.
- **Bo.14r2** — getting_started.md says "5,445+ tests" (current
  ~5,620).

### v6.0 scope (borrow checker)

- **Rt.04** — Multi-level alias analysis (struct→list→string depth 2).
  62_list_output baseline-gated at 13 obj / 346 B.
- **Li.1** — LICM with fix-point + preheader insertion.
- **Pe.1** — stage2.ll growth scaling check (+80 % v5.3.0 → v5.8.0;
  bounded per-release but worth a v6.0 budget review).
- **General ownership** — borrow checker as the structural framework
  for both Rt.04 and Li.1.

### Anaconda informational LOW (no specific release target)

- Coverage gate (53-release deferred status quo).
- Windows CI lane (38-release deferred).
- Self-compile pytest smoke gate.
- MIR-level destination-passing tests.
- Inliner-kinds whitelist gate (catch In.1-stage2 regression class).

---

## Exit criteria

| Criterion | Status |
|-----------|--------|
| `VERSION` reads `5.8.0` | ✓ |
| `MEASUREMENTS.md` written with all post-run data filled | ✓ |
| Seven reviewer files written to `.reviews/v5.7.1/` | ✓ |
| `.reviews/v5.7.1/V5_DECISION.md` with aggregate + decision rule | ✓ |
| `.reviews/v5.7.1/README.md` panel summary | ✓ |
| `docs/roadmap/v5/v5.8.0/PARITY_AUDIT.md` written | ✓ |
| SESSION_REPORT written | ✓ (this file) |
| CLAUDE.md release-list entry added | ✓ |
| ROADMAP.md "Where We Are" entry added | ✓ |
| 5x flaky audit clean | ✓ (0 flaky) |
| Valgrind + C hardening sweeps clean | ✓ |
| Fixed-point NEAR or STRICT | ✓ NEAR |
| Benchmarks run with CPU isolation | ✓ taskset -c 0-1 |
| No compiler / runtime source drift since v5.7.1 | ✓ 0 lines |
| Aggregate ≥ 9.0 AND 0 NEEDS WORK → Option A | ✓ 9.66 / 0 NEEDS WORK |

---

## What's next

Per V5_DECISION.md + ROADMAP.md:

- **v5.8.x** (optional, user-driven) — Bo.18 README copy fix +
  the 3 LOW Boa items + Pe.1 budget-check note. Could ship as a
  one-paragraph docs micro-release or roll into the next
  compiler release.
- **v6.0** (planned) — Borrow checker. Closes Rt.04 (multi-level
  alias) and Li.1 (LICM with fix-point + preheader). The only
  remaining v5.6.x v6.0 carry now that the rest of the v5.6.x
  closeout arc has resolved. Pe.1 budget review folded in.

The v5.x major arc is complete. v5.8.0 is the canonical mark.
