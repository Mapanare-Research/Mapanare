# v4.153.0 Fixed-Point Status

## Summary

**NEAR FIXED POINT.** 4 diff lines out of 110,127 (0.004%), within
`DIFF_THRESHOLD=100`. Only the known Dr.1 version-metadata placeholder
diff (`"4.153.0"` vs `"__MN_VERSION__"`).

## Measurements

| Artifact | Lines | md5 |
|---|---:|---|
| `stage2.ll` | **110,127** | `cad20b4b3db904b2dcbdea4533dcfc43` |
| `stage3.ll` | **110,127** | `612b352c8c4c86b1a326d967c92a7419` |

## Delta vs v4.142.0

| Metric | v4.142.0 | v4.153.0 | Delta |
|---|---:|---:|---|
| stage2.ll lines | 109,872 | 110,127 | +255 |
| stage3.ll lines | 109,872 | 110,127 | +255 |

The +255 line growth is from the v4.152.0 E8 comment blocks in
`mir_opt.mn` (~39 lines of comments → additional string constants and
metadata in the compiled IR). No functional change.

## Known diff

```
110127c110127
< !0 = !{!"4.153.0"}
---
> !0 = !{!"__MN_VERSION__"}
```

This is the Dr.1 version-metadata placeholder: stage2.ll embeds the
actual version; stage3.ll embeds the `__MN_VERSION__` placeholder
because the self-hosted compiler doesn't do build-time substitution.

## How to reproduce

```bash
bash scripts/verify_fixed_point.sh --keep
md5sum /tmp/stage2.ll /tmp/stage3.ll
```
