# Mapanare v4.8.0 — Self-Hosted Workarounds (Root Cause Fixes)

> Fix the 3 classes of workarounds in emit_llvm.mn. Each has a clear root cause.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.7.1

---

## Scope

8 workaround sites in emit_llvm.mn across 3 root causes:

### 1. substr bug (4 sites)
Lines 1224, 1803, 1818, 1995 — all use char-by-char loops instead of
`substr()` because `__mn_str_substr` has an off-by-one bug in the
compiled binary.

**Root cause investigation:**
- Write minimal test: `"hello".substr(1, 3)` → should be `"ell"`
- Compile with mnc-stage1, run, check output
- The bug is likely in `__mn_str_substr` in mapanare_core.c OR in how
  the emitter generates the call (wrong argument order, off-by-one in
  the length vs end calculation)

### 2. PHI zeroinitializer (2 sites)
Lines 1147, 3047 — avoid if-expressions to prevent the emitter from
generating zeroinitializer PHI nodes that crash stage2.

**Root cause investigation:**
- The Python emitter generates PHI nodes for if-expressions
- When the if-expression produces a struct/string value, the PHI's
  "incoming from block that didn't produce a value" uses zeroinitializer
- This is correct LLVM IR but may cause issues in stage2 compilation

### 3. ABI mismatch (2 sites)
Lines 2272, 2354 — inline operations to avoid calling C runtime functions
with mismatched calling conventions.

**Root cause investigation:**
- Line 2272: lists passed by pointer instead of by value
- Line 2354: range construction inlined instead of calling C runtime
- The issue is struct passing convention: C expects pointer, LLVM IR
  passes by value (or vice versa)

---

## Exit Criteria

| Check | Required |
|-------|----------|
| All 4 substr workarounds removed | YES |
| Both PHI zeroinit workarounds removed | YES |
| Both ABI mismatch workarounds removed | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
| `grep "avoid.*substr\|avoid.*PHI\|avoid.*ABI\|char-by-char.*avoid" mapanare/self/emit_llvm.mn` → 0 | YES |
