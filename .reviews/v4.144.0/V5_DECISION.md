# v5 Gate Decision — v4.144.0

> **v5 gate attempt 4.** Panel aggregate 9.21/10, 0 NEEDS WORK.
> Mechanical rule → **Option A — tag `v5.0.0`.**

## Score

**Aggregate: 9.21 / 10**
**Grade distribution: 6 EXCEEDS / 1 MEETS / 0 NEEDS WORK**

## Decision Rule

From `.reviews/v4.136.0/V5_DECISION.md` (precedent):

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| **Option A** | **Aggregate ≥ 9.0 AND 0 NEEDS WORK** | **Tag `v5.0.0`** | **YES: 9.21 ≥ 9.0, 0 NEEDS WORK** |
| Option C | 8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK | rc holds or advances | No |
| Option B | Aggregate < 8.5 OR any NEEDS WORK | Recovery cycle | No |

**Applied: Option A.** Tag `v5.0.0`.

## History of v5 gate attempts

| Attempt | Release | Aggregate | NEEDS WORK | Outcome |
|---|---|---:|---:|---|
| 1 | v4.99.0 | 6.59 | — | Option B (fail) |
| 2 | v4.120.0 | 8.21 | 1 (Anaconda) | Option B (fail) |
| 3 | v4.136.0 | 8.80 | 0 | Option C → `v5.0.0-rc1` |
| post-rc1 | v4.143.0 | 8.86 | 0 | Option C (rc1 holds) |
| **4** | **v4.144.0** | **9.21** | **0** | **Option A → `v5.0.0`** |

Score trajectory: **6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 → 9.21**

The 8.21 plateau (v4.114.0 → v4.120.0) took 16 releases to break.
The 8.86 plateau (v4.143.0) took 1 release to break. The difference:
v4.144.0 closed the *specific* findings each reviewer named, not a
broad sweep. Polish-scale work with review-targeted scope.

## Per-reviewer scores

| Reviewer | Domain | v4.143.0 | v4.144.0 | Δ | Grade |
|---|---|---:|---:|---:|---|
| Rattler | LLVM IR correctness | 9.1 | **9.3** | +0.2 | **EXCEEDS** |
| Viper | Memory safety | 9.6 | **9.6** | +0.0 | **EXCEEDS** |
| Anaconda | CI / testing | 9.1 | **9.3** | +0.2 | **EXCEEDS** |
| Cobra | Bootstrap / self-hosted | 9.0 | **9.2** | +0.2 | **EXCEEDS** |
| Coral | Language design | 8.5 | **8.9** | +0.4 | MEETS |
| Boa | Documentation | 9.0 | **9.1** | +0.1 | **EXCEEDS** |
| Mamba | C runtime / performance | 8.7 | **9.1** | +0.4 | **EXCEEDS** |
| **Aggregate** | — | **8.86** | **9.21** | **+0.35** | — |

## What v5.0.0 means

The `v5.0.0` tag certifies:

1. **The v4.x engineering arc is complete.** 144 releases from the v4.0.0
   production gate. 63+ docket closures. Zero CRITICAL, HIGH, or MEDIUM
   items on the ledger at the time of tagging.

2. **The self-hosted compiler compiles itself** to a near-fixed-point
   (4-line version-metadata diff, 110,127 lines, `DIFF_THRESHOLD=100`
   accepted).

3. **Memory safety is clean.** Valgrind 0 ERRORS, ASan 0 ASAN_ERROR
   across 66 golden tests. TSan gate live since v4.137.0 (Ch.1 closure).

4. **Test infrastructure is mature.** 5,187 non-bootstrap pytest passing,
   25+ sequential flaky-audit runs with 0 findings, 8 CI gates green.

5. **The benchmark evidence pack is honest.** Bn.1 corrected the harness
   tax; v4.144.0 published corrected numbers with explicit disclosure of
   the v4.135.0 retraction.

## What v5.0.0 does NOT mean

- It does not mean Mapanare is faster than Rust. The corrected geomean
  is 5.83× slower. The perf arc (v5.1.x) targets ≤ 1.5×.
- It does not mean the language surface is frozen. New features may land
  in v5.1.x+ with appropriate panel review.
- It does not mean zero open items. Own.1 (move-semantics), Cb.9a
  (module_path), ABI.1 (struct return), and Sh.4/5/7 (self-hosted feature
  gaps) are tracked for v5.x.

## Next steps

1. `VERSION` → `5.0.0`
2. Rebuild `libmapanare_rt.a` + `mnc-stage1` with new version
3. Full verification sweep
4. Git tag `v5.0.0`
5. Push to origin
6. `CHANGELOG.md` entry for v5.0.0
7. Begin perf arc at v5.1.0 (was v4.145.0 in the perf arc plan)

---

**The rule is the rule. The numbers are the numbers. v5.0.0 is real.**
