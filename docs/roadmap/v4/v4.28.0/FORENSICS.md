# v4.28.0 Forensics — "When did the revert happen?"

> Phase 0 of `PLAN.md` is mandatory before the fix phases. The v4.26.0
> panel reported that the matmul carry-forwards were **byte-identical**
> to the pre-v4.0.0 state. The hypothesis was: a revert happened between
> v4.0.0 and v4.26.0 that no review caught. This document tests the
> hypothesis.

## TL;DR

**The hypothesis was wrong, and the actual story is worse.**

- **matmul NULL check / dim validation**: there is no revert. `runtime/native/mapanare_gpu_builtins.c` has **one commit in its entire history** — the one that introduced it. The v3.47.0 panel flagged the hard blockers. The v4.0.0 CHANGELOG *claimed* they were fixed. **They were never committed.** The fix was claimed but never landed. This is a CHANGELOG honesty gap, not a revert.
- **`main.mn:32` version string**: the version string was bumped in-step from v3.46.0 through v4.7.1, then **stopped**. It has been `"mapanare 4.7.1"` for the 19 minor versions since, because the bump step was manual and dropped from the release process at v4.8.0. Not a revert either; a dropped manual step.

Both failures share the same systemic cause and will be closed by different v4.28.0/v4.31.0 items: **manual release steps with no automation or CI enforcement.**

## Finding #1 — `mapanare_gpu_builtins.c`

### What we expected

Based on the v4.26.0 panel's framing ("byte-identical to v3.47.0"), the expectation was:

1. v3.47.0 panel flags matmul shape/dim issues as hard blockers.
2. v4.0.0 commit adds NULL checks and dimension validation.
3. Some later commit between v4.0.0 and v4.26.0 reverts them.

### What `git log --follow` actually shows

```
$ git log --follow --oneline runtime/native/mapanare_gpu_builtins.c
fbd382e v3.46.0 Caimán: GPU Foundation — link mapanare_gpu.c, gpu_* builtins run on RTX 4090
```

**One commit. That's it.** `fbd382e` (2026-04-08) introduced the file. Nothing has touched it since. Not the v3.47.0 "hard blocker" cycle. Not v4.0.0. None of the 26 subsequent releases.

### What the v4.0.0 commit actually changed

```
$ git show --stat 14be7378 | grep gpu
(empty)

$ git show 14be7378 -- runtime/native/mapanare_gpu_builtins.c
(empty diff)
```

v4.0.0 did not touch this file. The CHANGELOG claim that v4.0.0 fixed the matmul hard blockers **was false at the time it was written**.

### What the current code actually does

`runtime/native/mapanare_gpu_builtins.c:161-195`:

```c
MN_EXPORT MnList __mn_gpu_tensor_matmul(const MnList *a, const MnList *b,
                                         int64_t m, int64_t n, int64_t k) {
    mapanare_gpu_init();
    if (!a || !a->data || !b || !b->data) {
        return __mn_list_new((int64_t)sizeof(double));
    }
    mapanare_tensor_t *ta = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
    mapanare_tensor_t *tb = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
    if (!ta || !tb) {
        free(ta); free(tb);
        return __mn_list_new((int64_t)sizeof(double));
    }
    ta->data = a->data;
    ta->ndim = 2;
    ta->shape = (int64_t *)malloc(2 * sizeof(int64_t));  // NOT NULL-checked
    ta->shape[0] = m; ta->shape[1] = k;                   // segfault if malloc failed
    ta->size = m * k;                                     // overflow possible
    ta->elem_size = (int64_t)sizeof(double);
    // ... same for tb ...
```

The panel's complaint is correct:

1. **Shape malloc NULL check missing** (lines 173, 181). If the `ta->shape` or `tb->shape` malloc fails, the next write (`ta->shape[0] = m`) dereferences NULL → segfault.
2. **Dimension validation missing**. The function trusts `m, n, k` from the caller without verifying they are consistent with `a->size` and `b->size`. A caller who passes mismatched dimensions gets undefined behaviour inside the GPU tensor compute path.
3. **Integer overflow on `m * k`**. No `mn_checked_mul` wrapping.

### Why the process lost the fix

v3.47.0 was the release gate for v4.0.0. The CHANGELOG for v4.0.0 says the hard blockers were closed. But nothing in git says `mapanare_gpu_builtins.c` was touched at v4.0.0. The most plausible explanation:

- The v4.0.0 release PR used a patch set that claimed to close the items.
- The patches for the *test* side or the *CHANGELOG* side landed.
- The patch for the `.c` file side was somehow dropped.
- The reviewer who signed off on v4.0.0 didn't cross-reference each CHANGELOG line against a file diff.
- The next 26 reviews only re-noticed the gap at v4.26.0.

**This is the same class of failure as the v4.25.0 `.replace("define internal ", ...)` hack and the v4.18.0-v4.26.0 hollow features**: *CHANGELOG claim without test-backed artifact*. The v4.31.0 CHANGELOG honesty CI gate is the systemic fix.

## Finding #2 — `mapanare/self/main.mn:32` (`"mapanare 4.7.1"`)

### What `git log -p --follow` actually shows

```
$ git log -p --follow mapanare/self/main.mn | grep -E '\+.*mapanare [0-9]|\-.*mapanare [0-9]'
-    return "mapanare 4.7.0"
+    return "mapanare 4.7.1"       <-- commit 8b1ce50 "v4.7.1"
-    return "mapanare 4.6.0"
+    return "mapanare 4.7.0"       <-- commit b166535 "v4.7.0"
-    return "mapanare 4.5.0"
+    return "mapanare 4.6.0"       <-- commit aeca0b6 "v4.6.0"
-    return "mapanare 4.4.0"
+    return "mapanare 4.5.0"       <-- commit ad22b149 "v4.5.0"
-    return "mapanare 4.3.0"
+    return "mapanare 4.4.0"       <-- commit 3f3036f "v4.4.0"
-    return "mapanare 4.2.0"
+    return "mapanare 4.3.0"       <-- commit 7249442 "v4.3.0"
-    return "mapanare 4.0.0"
+    return "mapanare 4.2.0"       <-- commit 1afd929 "v4.3.0 phase 1"
-    return "mapanare 3.47.0"
+    return "mapanare 4.0.0"       <-- commit 14be7378 "v4.0.0"
-    return "mapanare 3.46.0"
+    return "mapanare 3.47.0"      <-- commit c37b9bc "v3.47.0"
-    return "mapanare 3.40.0"
+    return "mapanare 3.46.0"      <-- commit fbd382e "v3.46.0"
```

The pattern is clear:

- From v3.46.0 through v4.7.1 the version string was bumped alongside the release tag. Every release commit touched this line.
- From **v4.7.1 onward**, the line was never touched again.
- The current value `"mapanare 4.7.1"` is 19 versions stale (v4.8.0 through v4.26.0, plus v4.27.0 which intentionally deferred the fix to this release).

### Why the process lost the fix

At v4.7.1 the release process relied on the release author remembering to `sed -i 's/return "mapanare X"/return "mapanare Y"/' mapanare/self/main.mn`. Starting at v4.8.0 that step was dropped. No CI gate enforced it, no release script ran it, no test caught it (the `test_version_string` test that *does* catch it has been failing locally ever since, but it was being run and ignored).

Note: the `VERSION` file itself was kept up to date. `pyproject.toml` reads `VERSION` dynamically (see `version = {file = "VERSION"}`). The Python-side `mnc --version` is always right. The self-hosted `mnc-stage1 version` has been lying for 19 minor versions.

### The fix

Phase 3 of v4.28.0 replaces the hardcoded return with a build-time substitution: `scripts/build_stage1.py` reads `VERSION` and injects it before compilation. Once wired, a future version bump only has to touch `VERSION` and `CHANGELOG.md` — the same files every other release artifact reads.

## Systemic cause (for v4.31.0 process hardening)

Both findings have the same shape:

1. A release deliverable required a manual file edit.
2. The manual edit was not backed by a CI gate or an automated substitution.
3. A reviewer missed the drop.
4. The gap aged across multiple review cycles because no mechanical check ran.

The v4.31.0 phase `Documentation truth + process` is the planned systemic fix. Concrete items that fall out of this forensic:

- **v4.31.0 CHANGELOG honesty CI script** (already in the recovery plan). Every `## [VERSION]` entry must be checkable via `git ls-files`, `pytest`, or `grep` over the source. This would have caught the v4.0.0 matmul claim the day it was written.
- **Version substitution via `VERSION` file** (v4.28.0 Phase 3, this release). Covers the `main.mn` case and any future `.mn` file that wants the version string.
- **No more hardcoded version strings anywhere** (grep check in v4.31.0 CI). Any match fails the build.

## What this does NOT explain

Forensic checks on the other v3.47.0 carry-forwards (`mn_init_tag_strings`, GPU temp file race, Windows `InitOnceExecuteOnce`) are not in scope for this document — they ship in Phase 1.4, 2.3, and 2.4 respectively, and their histories will be audited by the commit message of each fix. The shared root cause still applies: **manual steps without automation.**

---

**Verdict: no revert to bisect. Both failures are dropped manual steps.** Proceed to Phase 3 (version string — directly addressed by the substitution), then Phase 1 (concurrency — not a process failure, a design gap), then Phase 2 (the matmul fix that v4.0.0 claimed).
