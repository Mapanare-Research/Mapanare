# v4.8.0 Session Report — 2026-04-09

## Completed
- [x] 4 substr workarounds removed (`emit_llvm.mn` lines 1224, 1803, 1818, 1995)
  - `strip_colon_suffix`: char-by-char loop replaced with `s.substr(0, colon_pos)`
  - `extract_after_colon`: char-by-char loop replaced with `s.substr(start, slen - start)`
  - `parse_field_index`: removed stale "substr bug" comment
  - `find_list_field_index`: removed "char-by-char builders" comment
  - Root cause: substr bug was stale — `substr()` already works in other callsites
- [x] 2 PHI zeroinit workarounds removed (`emit_llvm.mn` lines 1147, 3047)
  - `strip_percent`: converted to early return pattern
  - `emit_fn` visibility: converted to if-expression
  - Root cause fixed in `lower.py:2790-2792` — PHI type was unconditionally overridden to function return type; now only falls back when expression type is void/unknown
- [x] 2 ABI mismatch workarounds clarified (`emit_llvm.mn` lines 2272, 2354)
  - GPU tensor: alloca+store+pass-ptr IS correct (C takes `MnList*`)
  - Range: inline `{i64, i64}` IS correct (superior to C's heap-allocated `void*`)
  - Comments updated to explain why, not label as workarounds
- [x] Version bumped to 4.8.0

## Still TODO
- Nothing — all exit criteria met

## Issues Found
- PHI type override bug in `lower.py` was a real semantic bug affecting ALL if-expressions
  in struct-returning functions, not just the two workaround sites. The fix benefits the
  entire compiler, not just the self-hosted code.

## Decisions Made
- substr workarounds removed by direct replacement (bug was stale, no C runtime fix needed)
- PHI zeroinit fix applied in Python lowerer (root cause), not in self-hosted emitter
- ABI "workarounds" kept as-is (correct implementations) — only comments updated
- GPU tensor ptr-passing is the correct C ABI bridge, not a workaround
- Range inline construction is superior to calling C's heap-allocating `__mn_range`

## Next Session Should Start With
- Read `docs/roadmap/v4/v4.9.0/PLAN.md` and `PROMPT.md`
- v4.9.0: Semantic Safety — fix `ast__expr_ident_name` memory corruption
- Baseline: 40/40 golden, 11/11 stage2
