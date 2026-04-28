# v5.3.1 — Quick-win closeout (5 MEDIUM items, ~30 min)

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.3.0 shipped
**Estimated work:** 30 minutes

---

## Goal

Clear the five MEDIUM carry-forwards that are pure writing or
one-command fixes. This recovers Anaconda's lint gates (RED → GREEN)
and Boa's documentation accuracy. Together these two reviewers
account for -0.9 of the aggregate dip.

## Items

| ID | Severity | Fix | Effort |
|----|----------|-----|--------|
| **Lint-v5.2.0** | MEDIUM | `black . && ruff check --fix .` | 30 sec |
| **Bo.15** | MEDIUM | README: remove "strict 3-stage fixed point" claim (or qualify as "at v4.134.0; regressed at v5.1.2") | 5 min |
| **Bo.16** | MEDIUM | `known_issues.md`: remove "No package manager yet" line, add v5.2.0 registry entry | 2 min |
| **Bo.17** | LOW | `docs/README.{zh-CN,pt}.md`: bump version badge to 5.3.1 | 2 min |
| **Bo.14r** | LOW | `getting_started.md`: update version ref and test count | 2 min |
| **Stream-C** | MEDIUM | Fix C test init: `MnList list = {0}` → `__mn_list_new(sizeof(int64_t))` in 3 stream tests. Audit Ge.1r `elem_size` fallback — consider `assert` instead of silent 256. | 15 min |
| **An.9r** | LOW | Fix LLVM-version-sensitive test: `test_post_opt_single_switch_in_hot_loop` should allow 0 or 1 switches (LLVM 18 folds further) | 5 min |

## Expected panel impact

- **Anaconda**: +0.3–0.5 (lint gates GREEN, stream tests fixed)
- **Boa**: +0.1–0.2 (docs accurate, no more contradictions)
- **Mamba**: +0.05 (stream tests green)
- **Net aggregate lift**: +0.15–0.25

## Exit criteria

- `black --check . && ruff check .` returns 0
- `python3 -m pytest tests/native/test_c_hardening.py -v` → 0 failures
- `test_post_opt_single_switch_in_hot_loop` passes on LLVM 17 and 18
- README does not claim strict fixed-point
- `known_issues.md` mentions the package registry
