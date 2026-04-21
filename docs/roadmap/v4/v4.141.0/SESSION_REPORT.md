# v4.141.0 Session Report — An.2 lint debt + 5th flaky audit

**Date:** 2026-04-16
**Theme:** Anaconda's carry-forward emptied — lint gate live, 25 audit runs clean

## Changes

### An.2 — repo-wide lint debt (LOW → CLOSED)

The branch already contained the three mechanical cleanup phases when this
session resumed:

- `v4.141.0 WIP: black auto-format (65 files)`
- `v4.141.0 WIP: ruff auto-fix + manual cleanup (128 -> 0)`
- `v4.141.0 WIP: mypy strict-mode 35 -> 0`

This session closed the remaining release work around those commits:

- `tests/test_ci.py` no longer skip-marks `TestToolsRunLocally`.
- Removing the skip exposed one stale import: `pytest` became unused once the
  decorator disappeared, so the import was removed.
- Final verification shows the local lint gate is genuinely live again:
  `make lint` exits 0 and `python3 -m pytest tests/test_ci.py -v -s`
  reports **16 passed**.

**GitNexus impact pre-edit.**
`npx gitnexus impact TestToolsRunLocally --direction upstream --include-tests`
returned **risk LOW** with **0 direct dependents / 0 affected processes /
0 affected modules**. The edit was isolated to the test-side gate, exactly as
the prompt predicted.

### VERSION propagation sync before the audit

The first audit attempt exposed two deterministic VERSION drift failures:

- `tests/runtime/test_user_agent.py::...::test_user_agent_contains_current_version`
- `tests/self_hosted/test_main_mn.py::...::test_mnc_stage1_version_matches_version_file`

`VERSION` was already `4.141.0`, but the built runtime archive and
`mnc-stage1` still embedded `4.140.0`. The fix was artifact-only:

```bash
make build-rt
python3 scripts/build_stage1.py
```

After the rebuild:

- the runtime archive advertises `Mapanare/4.141.0`
- `mnc-stage1 version` prints `mapanare 4.141.0`
- `mapanare/self/main.ll` updates its four version-bearing literals from
  `4.140.0` to `4.141.0`

The two targeted regression tests immediately re-ran as **2 passed**.

### 5th flaky audit — 5 clean full-suite runs

`docs/roadmap/v4/v4.141.0/FLAKY_AUDIT.md` records the fifth cumulative audit.
All five runs completed with the same summary:

- **5152 passed**
- **115 skipped**
- **9 xfailed**
- **2 warnings**
- **0 failed**

Every sorted `FAILED` list is empty; every adjacent diff is empty.
This extends the cumulative evidence base from **20** to **25** sequential
non-bootstrap pytest runs with **zero flaky findings**.

One environment-specific note: on this WSL checkout, pytest's default capture
path hit `FileNotFoundError` in `_pytest/capture.py` before collection. The
official audit therefore used `-s` / capture disabled. Test selection and
ordering were unchanged.

## Metrics

- **Lint:** `make lint` clean (`ruff`, `black --check`, `mypy` all pass)
- **CI self-tests:** `python3 -m pytest tests/test_ci.py -v -s` -> **16 passed**
- **Flaky audit:** 5 runs, all **5152 / 115 / 9 / 2 / 0**
- **Flaky-audit total wall:** **2436 s (40m 36s)**
- **Goldens through `mnc-stage1`:** **54/66 passed**, 12 known feature-gap failures
- **Fixed point:** `bash scripts/verify_fixed_point.sh --keep` -> **NEAR FIXED POINT**
- **Fixed-point delta:** 4 diff lines out of 109,872, all the known version-metadata artifact
- **stage2.ll md5:** `9995c7416e5810386cf4ef8e291b202a`
- **stage3.ll md5:** `dddf64c3a77ed9236c82de517bc055d1`
- **`libmapanare_rt.a` sha256:** `4447cb2de8ab9ff4f112e6fbe782ab43807050fba37fdede40846ccfe854de21`
- **`mnc-stage1` stripped size:** **3,566,736 bytes**

## Dockets closed

| Docket | Severity | Description |
|--------|----------|-------------|
| An.2 | LOW | Repo-wide lint debt and skipped local lint gate |

## Net ledger state

**63 dockets opened since v4.99.0 -> 47 closed / 16 open.**

Open after v4.141.0: **0 CRITICAL · 0 HIGH · 8 MEDIUM · 8 LOW**.
Anaconda's carry-forward is empty.

## Residual notes

- Fixed-point is still "near fixed point", not strict byte identity. The only
  remaining diff is the known version-metadata placeholder:
  `!0 = !{!"4.141.0"}` vs `!0 = !{!"__MN_VERSION__"}`.
- `scripts/build_stage1.py` temporarily rewrites placeholder-bearing `.mn`
  sources during the build. On this Windows-backed checkout that dirtied
  `mapanare/self/main.mn` via newline normalization only; the file was
  normalized back before closing the session.
