---
severity: medium
found: "[[v4.26.0]]"
fixed: "[[v4.28.0]]"
status: fixed
tags: [bug, medium, self-hosted, version, build-system]
---

# Version String Stale

`main.mn` in the self-hosted compiler hardcoded the string `"mapanare 4.7.1"` as the version output. This value was never updated across 19 subsequent releases, so `mnc --version` reported v4.7.1 regardless of the actual compiler version. Debugging version-specific issues was impossible when the binary lied about its own identity.

## Root Cause
The version string was a string literal in `main.mn` rather than being injected from the `VERSION` file at build time. No build step substituted the value, and no test compared `mnc --version` output against the expected version.

## Fix
Replaced the hardcoded string with a build-time substitution: `scripts/build_stage1.py` reads the `VERSION` file and patches the version constant in the concatenated `.mn` source before compilation. Added a CI check that `mnc --version` matches the `VERSION` file. Fixed in v4.28.0.
