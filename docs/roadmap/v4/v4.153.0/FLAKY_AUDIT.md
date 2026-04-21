# v4.153.0 Flaky Audit — 6th Sequential 5x Pytest

## Summary

**30 cumulative sequential non-bootstrap pytest runs since v4.117.0,
zero flaky findings.** Anaconda score floor confirmed for v4.154.0 panel.

## Audit history

| Audit | Release | Runs | Failed | Flaky |
|---|---|---:|---:|---:|
| A1 | v4.117.0 | 5 | 0 | 0 |
| A2 | v4.125.0 | 5 | 0 | 0 |
| A3 | v4.130.0 | 5 | 0 | 0 |
| A4 | v4.135.0 | 5 | 0 | 0 |
| A5 | v4.141.0 | 5 | 0 | 0 |
| **A6** | **v4.153.0** | **5** | **0** | **0** |
| **Total** | | **30** | **0** | **0** |

## This audit (A6)

| Run | Passed | Failed | Skipped | xfailed | Wall time |
|---|---:|---:|---:|---:|---:|
| 1 | 5302 | 0 | 115 | 9 | 490s |
| 2 | 5302 | 0 | 115 | 9 | 485s |
| 3 | 5302 | 0 | 115 | 9 | 484s |
| 4 | 5302 | 0 | 115 | 9 | 483s |
| 5 | 5302 | 0 | 115 | 9 | 486s |

## Pairwise diffs

All 4 pairwise diffs are empty (identical failure sets — all empty):

- Run1 vs Run2: (empty)
- Run2 vs Run3: (empty)
- Run3 vs Run4: (empty)
- Run4 vs Run5: (empty)

## Artifacts

- `docs/roadmap/v4/v4.153.0/flaky-runs/run{1..5}.log`
- `docs/roadmap/v4/v4.153.0/flaky-runs/run{1..5}.failed.sorted`

## How to reproduce

```bash
for i in 1 2 3 4 5; do
  python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no
done
```
