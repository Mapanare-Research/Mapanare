# v4.106.0 Session Report — 2026-04-14

## Verdict

**Panel complete. Decision: NEEDS WORK → v4.106.1 patch.**

Seven reviewers graded v4.100.0–v4.105.0 (Phase A + Phase B). Aggregate
**7.87 / 10**, zero NEEDS WORK verdicts, but below the 8.0 PASS
threshold per `POST_RECOVERY_MASTER_PROMPT.md §12` ("the lead does
not self-certify arcs"). The mechanical rule applies: the 0.13 gap
triggers a narrowly-scoped patch release.

The panel found the 5 critical / high v4.99.0 docket items all CLOSED
with verifiable evidence and recorded the largest panel-aggregate
improvement since the v4.31.0 recovery close (+1.28 from v4.99.0's
6.59). The blocker for a clean PASS is a single HIGH emitter bug
(**Rt.1**) that the PRE_PANEL_AUDIT initially mis-classified as an
LLVM opt miscompile; Rattler's review correctly re-attributed it to
the Mapanare emitter.

## Self-graded aggregate

**8.0 / 10** on the internal smoke check (not the panel score, which
is the authoritative 7.87):

- Panel execution: 7 reviewers, all returned structured verdicts with
  evidence. Pre-panel audit caught two OVERSTATED claims before
  reviewers saw them. +strong
- Rattler's correction of my mis-attribution (Cl.1 → Rt.1, LLVM bug
  → emitter bug) is exactly the function of a panel: catch the lead's
  incorrect read. Neutral-positive — the cadence is working.
- v4.106.1 scope is narrow and mechanical (2 HIGH items only, not
  scope creep). +good
- Honest application of the rule: 7.87 < 8.0 → NEEDS WORK. No
  rounding up even though 3 reviewers were within 0.2 of 8.0. +good

## Completed

| Phase | Commit | Scope |
|---|---|---|
| 1 | `<prev>` | pre-panel sweep (golden re-run, integration, valgrind, ASan, TSan async, crash breadcrumb demo, CI file) |
| 2 | `<prev>` | `MEASUREMENTS.md` — golden rates, sanitizer counts, docket status, 5443 pytest, 11 CI gates |
| 3 | `<prev>` | `.reviews/v4.99.0/V5_DECISION.md` docket closure update (5/5 items CLOSED) |
| 4 | `<prev>` | `PRE_PANEL_AUDIT.md` — 20 claims audited, 17 VERIFIED, 2 OVERSTATED, 1 with nuance |
| 5 + 5.5 | `<prev>` | 7 reviewer files + `.reviews/v4.106.0/README.md` |
| 6 | (this report) | CHANGELOG, SESSION_REPORT, roadmap, VERSION bump |

## Carry-forward closed

From v4.99.0 docket (all 5 CRITICAL / HIGH):
- **#1 Tagged-pointer UB** — CLOSED v4.100.0 — evidence: `mapanare_core.h:60` bitfield; `mapanare_core.c` uses `s.is_heap` directly; no live `mn_tag_heap` calls.
- **#2 List indexing drop-glue** — CLOSED v4.101.0 + v4.103.0 — evidence: 12 `_move_resource` occurrences in `emit_llvm_text.py`; 62_list_output golden.
- **#3 `libmapanare_rt.a` scheduler exports** — CLOSED v4.102.0 — evidence: `nm` shows 6 `__mn_coro_*` T symbols; 3/3 async goldens native.
- **#4 `else` / `sino`** — CLOSED v4.103.0 — evidence: `63_else_sino.mn` produces expected output through bootstrap + `opt -O2` + clang.
- **#5 Closure type annotations** — CLOSED at the lowering level (v4.103.0). The bootstrap-interpreter and `-O0`/`-O1` paths produce correct output. `-O2` path miscompiles due to Rt.1 (v4.106.1 scope).

## Carry-forward opened

### HIGH (v4.106.1 scope)

| # | Item | Opened by |
|---|---|---|
| Rt.1 | Multi-arg lambda emitter emits `void (ptr, ptr, ptr)` instead of `i64 (ptr, i64, i64)`; LLVM verifier accepts opaque-pointer mismatch silently | Rattler |
| Rt.2 / Ih.1 | Integration-pipeline harness treats exit 0 as PASS regardless of stdout | Rattler + Anaconda |

### MEDIUM (v4.107.0+ scope)

| # | Item | Opened by |
|---|---|---|
| As.1 / Vg.2 / Vg.3 | `__mn_list_free` shared-buffer heap-UAF (~3-4h, ~40 LOC per Mamba's fix sketch) | Mamba / Viper |
| Cb.1 | Option payload ABI unification (`{i1,i64}` vs `{i1,ptr}`) | Cobra |
| Vp.1 | LTO CI job (exercises item #8 LTO fragility) | Viper |
| Vp.2 | Crash handler: make constructor-attribute default or explicit opt-in | Viper |
| Rt.3 | Audit emitter for other verifier-accepted signature mismatches | Rattler |

### LOW

| # | Item | Opened by |
|---|---|---|
| Bo.1 | stage1 async error wording | Boa |
| Bo.2 | stage1 `0:0` source position loss | Boa |
| Bo.3 | per-function breadcrumb from `.mn` | Boa |
| Co.1 | ergonomic `else if` in grammar | Coral |
| Co.2 | document closure ABI in SPEC | Coral |
| Cb.2 | main return type unification (i64 vs i32) | Cobra |
| Cb.3 | byref size heuristic (re-listing #7) | Cobra |
| Cb.4 | publish MnString ABI contract doc | Cobra |

### Still OPEN from v4.99.0

- #7 (byref size heuristic) — re-listed as Cb.3
- #8 (coroutine frame LTO fragility) — PARTIAL; Vp.1 opens LTO CI
- #9 (string concat perf — StringBuilder auto-route)
- #10 (bilingual keyword collision docs)
- #11 (async-specific error messages) — subsumed by Bo.1

## Measurements

| Metric | Value | Delta vs v4.99.0 / v4.105.0 |
|---|---:|---|
| Panel aggregate | **7.87 / 10** | +1.28 vs v4.99.0's 6.59 |
| Reviewers NEEDS WORK | 0 | −3 vs v4.99.0 (3 NEEDS WORK) |
| Reviewers PASS | 1 | +1 vs v4.99.0 (0 unconditional PASS) |
| Critical / high docket closed | **5 / 5** | +5 vs v4.99.0 (0 closed) |
| Golden through mnc-stage1 | 21 / 64 | unchanged from v4.104.0 |
| Golden through integration pipeline | 60 / 64 | unchanged; stdout-diff gate is Rt.2 |
| Async goldens native + TSan-clean | 3 / 3 | unchanged |
| Valgrind ERRORS | 36 / 64 | unchanged; all pre-existing, 7 latent |
| ASan ASAN_ERROR | 17 / 64 | unchanged |
| CI gates total | 11 | +3 sanitizers vs pre-v4.105.0 |
| Pytest collected | 5,443 | — |

## Decisions Made

- **Applied 8.0 threshold mechanically.** Aggregate 7.87 < 8.0 →
  NEEDS WORK, even though no individual reviewer said NEEDS WORK.
  Per `POST_RECOVERY_MASTER_PROMPT.md §12`. No rounding up.
- **Classified Rt.1 as a HIGH emitter bug, not an LLVM optimizer
  bug.** Rattler's IR inspection is authoritative: the emitted IR is
  malformed (signature mismatch) and LLVM's opaque-pointer mode
  silently accepts it. The fix is in `lower.py` / `emit_llvm_text.py`,
  not in waiting for LLVM 19.
- **v4.106.1 scope: 2 HIGH items only.** Rt.1 (emitter) + Rt.2 / Ih.1
  (harness stdout-diff). No creep. Everything MEDIUM / LOW is
  Phase C.
- **Re-panel scope narrowed.** Only 3 domains re-grade after v4.106.1:
  Rattler, Anaconda, Coral. The other 4 carry forward their current
  grades. Minimizes panel overhead.

## Verification Results

- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` → 21/64 pass (re-verified).
- `bash scripts/valgrind_all_goldens.sh` → 0/28/36 (re-verified).
- `bash scripts/run_asan_goldens.sh` → 21/17/26 (re-verified).
- Async TSan: 55=42, 56=43, 57=110, 0 races (re-verified).
- Smoke: 134-line IR, exit 0.
- Crash breadcrumb: demonstrated on 03_function.
- `python3 scripts/check_valgrind_baseline.py …` → OK 36/36.
- `python3 scripts/check_asan_baseline.py …` → OK 17/17.
- `.github/workflows/sanitizers.yml` validates (166 lines, 3 jobs).
- **Rt.1 reproduction** (panel's key finding):
  - `python3 -m mapanare run tests/golden/64_closure_typed.mn` → 10/-3/20/**15** (correct, interpreter)
  - Bootstrap IR + no-opt pipeline → 10/-3/20/**15** (correct)
  - Bootstrap IR + `opt -O2` pipeline → 10/-3/20/**10** (wrong; Rt.1)

## Tool discipline retrospective

- 7 panel agents run in parallel. Each returned a structured review
  under 600 words with in-review evidence (grep output, file:line,
  reproduction commands). No context pollution in main conversation.
- Culebra: `journal add` at start + end. Templates directory still
  unconfigured; `scan` output wasn't informative for this grading.
- Pre-panel audit caught 2 OVERSTATED claims (Claim 10, Claim 13);
  Rattler then *re-corrected* my classification of Claim 10 (LLVM
  opt → emitter bug). Two-stage error correction working as
  designed.

## Next Session Should Start With

- Read `POST_RECOVERY_MASTER_PROMPT.md` (if > 1 week).
- Read `docs/roadmap/v4/v4.106.1/PLAN.md` — needs to be written or
  derived from the existing `v4.106.0` PLAN template. Scope is
  fixed:
  - Rt.1: multi-arg lambda emitter (i64 param/return, not ptr/void)
  - Rt.2 / Ih.1: integration harness stdout-diff
- Read `.reviews/v4.106.0/01-rattler.md` for the full Rt.1
  reproduction steps and IR inspection. `01-rattler.md` is the most
  load-bearing document for v4.106.1 work.
- Run the 3-domain re-grade after v4.106.1 lands. If all 3 return
  PASS (≥ 8.0), Phase B closes and Phase C opens at v4.107.0
  (benchmarks).
- If re-grade falls short, v4.106.2 or extended patch. Do not ship
  Phase C until Phase B graduates.
