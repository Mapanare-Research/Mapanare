---
severity: high
found: "[[v4.17.0]]"
fixed: "[[v4.29.0]]"
status: fixed
tags: [bug, high, bootstrap, fixed-point, ci, verification]
---

# Fixed-Point Verification Unfalsifiable

`verify_fixed_point.sh` had `EXIT=0` hardcoded at the end and `|| true` appended to every critical comparison step. The script always reported success regardless of whether stage1 and stage2 output actually converged. The v4.17.0 bootstrap fixed-point claim was based on this script and was therefore unprovable.

## Root Cause
The script was written defensively during early bootstrap work when failures were expected and the goal was to collect output rather than gate on correctness. The `|| true` guards and hardcoded exit code were never removed as the project matured. No CI job checked the script's exit code meaningfully.

## Fix
Rewrote `verify_fixed_point.sh` with `set -euo pipefail`, removed all `|| true` guards, added a `diff` threshold check between stage1 and stage2 IR output, and a non-empty output assertion. The script now fails loudly on divergence. Fixed in v4.29.0.
