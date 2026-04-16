# v4.142.0 Fixed-Point Status

> Generated 2026-04-16 at v4.142.0 after the Ge.1 closure rebuild.

## Verdict

**NEAR FIXED POINT.**

The self-hosted pipeline remains structurally converged, but the
release branch does **not** return to byte-identical `stage2.ll ==
stage3.ll`. The only remaining delta is the known version-metadata
placeholder:

- `!0 = !{!"4.142.0"}`
- `!0 = !{!"__MN_VERSION__"}`

This is the same placeholder-only class documented in the post-v4.139.0
line, not a Ge.1 regression.

## Reproduction

```bash
bash scripts/verify_fixed_point.sh --keep
wc -l /tmp/stage2.ll /tmp/stage3.ll
md5sum /tmp/stage2.ll /tmp/stage3.ll
```

## Live result

| Artifact | Lines | md5 |
|---|---:|---|
| `/tmp/stage2.ll` | **109,872** | `6d4963cdbe060ac1cee85eb58f2fa932` |
| `/tmp/stage3.ll` | **109,872** | `dddf64c3a77ed9236c82de517bc055d1` |

`verify_fixed_point.sh --keep` reports:

- **4 diff lines out of 109,872**
- classification: **NEAR FIXED POINT**
- substantive IR structure: unchanged

## Interpretation

- The Ge.1 fix changes the self-hosted lowering/emission path, so the
  stage2 md5 necessarily moves from the v4.141.0 release value.
- The remaining diff is still metadata-only, not semantic codegen drift.
- La Culebra still bites its tail at the structural level; the only
  non-identity is the version-placeholder substitution boundary.

## Carry-forward

No new fixed-point docket opens here. The standing carry-forward remains
the version-placeholder asymmetry already accepted in the v4.140.0 /
v4.141.0 line.
