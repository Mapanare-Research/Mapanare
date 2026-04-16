# v4.141.0 Flaky-Audit Report — pytest 5× sequential (fifth audit)

> Generated 2026-04-16. Ran `python3 -m pytest tests/ --ignore=tests/bootstrap`
> five times sequentially on the v4.141.0 branch after the An.2 lint cleanup and
> a VERSION-propagation rebuild of `libmapanare_rt.a` + `mnc-stage1`.

## Verdict

**0 flaky failures. 0 failures total. Full per-test identity across all 5 runs.**

All five runs finished with the same summary:
**5152 passed / 115 skipped / 9 xfailed / 2 warnings / 0 failed**.
Every sorted `FAILED` list is empty, and every adjacent pairwise diff is empty.

**Cumulative across 5 audits: 25 sequential pytest runs, zero flaky findings.**

---

## Methodology

```bash
mkdir -p docs/roadmap/v4/v4.141.0/flaky-runs
for i in 1 2 3 4 5; do
    echo "=== Run $i === $(date '+%Y-%m-%d %H:%M:%S')"
    python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no -s \
        > docs/roadmap/v4/v4.141.0/flaky-runs/run$i.log 2>&1
    grep ^FAILED docs/roadmap/v4/v4.141.0/flaky-runs/run$i.log \
        | sort > docs/roadmap/v4/v4.141.0/flaky-runs/run$i.failed.sorted
done

for i in 1 2 3 4; do
    j=$((i+1))
    diff docs/roadmap/v4/v4.141.0/flaky-runs/run$i.failed.sorted \
         docs/roadmap/v4/v4.141.0/flaky-runs/run$j.failed.sorted
done
```

- Sequential, not parallel.
- Bootstrap subset excluded to match the prior four audits.
- `-s` was required on this WSL checkout because pytest's default capture path
  hit `FileNotFoundError` inside `_pytest/capture.py` before collection.
  Disabling capture changed logging, not test selection or execution order.
- Raw logs and sorted `FAILED` lists are preserved in
  `docs/roadmap/v4/v4.141.0/flaky-runs/`.

### Pre-audit setup

An initial trial run surfaced two deterministic VERSION drift failures:

- `tests/runtime/test_user_agent.py::TestUserAgentMatchesVersion::test_user_agent_contains_current_version`
- `tests/self_hosted/test_main_mn.py::TestMainMnPipeline::test_mnc_stage1_version_matches_version_file`

`VERSION` was already `4.141.0`, but the built runtime archive and
`mnc-stage1` still embedded `4.140.0`. Before the official audit, the release
branch was synced with:

```bash
make build-rt
python3 scripts/build_stage1.py
```

Re-running those two regression tests immediately after the rebuild produced
`2 passed`, and the five official audit runs below all completed cleanly.

---

## Per-run results

| Run | Started | Finished | Wall (script) | Wall (pytest) | failed | passed | skipped | xfailed | warnings |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 01:30:26 | 01:38:53 | 507 s | 541.12 s | **0** | 5152 | 115 | 9 | 2 |
| 2 | 01:38:53 | 01:47:18 | 505 s | 537.80 s | **0** | 5152 | 115 | 9 | 2 |
| 3 | 01:47:18 | 01:55:09 | 471 s | 503.00 s | **0** | 5152 | 115 | 9 | 2 |
| 4 | 01:55:09 | 02:03:02 | 473 s | 502.05 s | **0** | 5152 | 115 | 9 | 2 |
| 5 | 02:03:02 | 02:11:02 | 480 s | 512.72 s | **0** | 5152 | 115 | 9 | 2 |

**Total wall: 40 minutes 36 seconds.** Median script-measured wall:
**480 s (8 minutes 0 seconds)**.

---

## Stability analysis

### Failure count

Identical at **0 across all 5 runs**.

### Pass / skip / xfail / warning counts

All five runs were identical:

- passed: **5152**
- skipped: **115**
- xfailed: **9**
- warnings: **2**

No pass-count drift, no flaky skips, no flaky xfails.

### Per-test diff (sorted `FAILED` lists)

```text
diff run1 run2: empty
diff run2 run3: empty
diff run3 run4: empty
diff run4 run5: empty
```

Every `run*.failed.sorted` file is empty.

---

## Comparison to prior audits

| Audit | Release | Runs | Scope | Flaky | Failure count | Source |
|---|---|---:|---|---:|---:|---|
| 1st | v4.117.0 | 5 | subset (9 dirs, 1501 tests) | 0 | 22 | `docs/roadmap/v4/v4.117.0/FLAKY_AUDIT.md` |
| 2nd | v4.125.0 | 5 | full (5054 passed) | 0 | 39 | `docs/roadmap/v4/v4.125.0/FLAKY_AUDIT.md` |
| 3rd | v4.130.0 | 5 | full (5068-5070 passed) | 0 | 39 | `docs/roadmap/v4/v4.130.0/FLAKY_AUDIT.md` |
| 4th | v4.135.0 | 5 | full (5115-5116 passed) | 0 | 0 | `docs/roadmap/v4/v4.135.0/FLAKY_AUDIT.md` |
| **5th** | **v4.141.0** | **5** | **full (5152 passed)** | **0** | **0** | **this file** |

**Cumulative: 25 sequential runs across 5 audits, zero flaky findings.**

---

## Carry-forward

None from the audit itself. The failure set is empty.

The known self-hosted feature-gap goldens remain baseline-honest in the native
golden harness (`54/66` through `mnc-stage1`), but they are not flaky tests and
did not surface in the non-bootstrap pytest audit.
