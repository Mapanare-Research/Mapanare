# v4.141.0 Docket Ledger Delta — An.2 CLOSED

> Release-local ledger update for v4.141.0. This file records the An.2
> disposition change that landed after the broader panel-era ledger frozen at
> `docs/roadmap/v4/v4.135.0/DOCKET_LEDGER.md`.

## Closed this release

| Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|
| **An.2** — repo-wide lint debt (`black` + `ruff` + `mypy`) | v4.120.0 panel (Anaconda) | LOW | **CLOSED** | v4.141.0 | `make lint` exits 0; `tests/test_ci.py::TestToolsRunLocally` unskipped and passing; 5th flaky audit clean after VERSION propagation rebuild. |

## Net ledger state

Using the v4.140.0 ledger rollup as the starting point, v4.141.0 closes the
last open `An.*` item:

- 63 dockets opened since v4.99.0
- **47 closed**
- **16 open**
- **0 CRITICAL · 0 HIGH · 8 MEDIUM · 8 LOW**

## What changed

- Anaconda's last carry-forward from the v4.120.0 panel is now closed.
- `tests/test_ci.py` no longer skip-marks the local lint gates.
- The fifth cumulative flaky audit extends the evidence base from 20 to
  **25 sequential runs with zero flaky findings**.

## Reference points

- Historical ledger snapshot: `docs/roadmap/v4/v4.135.0/DOCKET_LEDGER.md`
- Audit evidence: `docs/roadmap/v4/v4.141.0/FLAKY_AUDIT.md`
- Release summary: `docs/roadmap/v4/v4.141.0/SESSION_REPORT.md`
