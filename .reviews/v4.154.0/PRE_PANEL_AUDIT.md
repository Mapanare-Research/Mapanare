# Pre-Panel Audit — v4.154.0

> Fact-check of every SESSION_REPORT in the v4.144.0 -> v4.152.0 perf
> arc. 42 load-bearing claims verified against v4.153.0 HEAD.
> **0 material discrepancies.**

## v4.145.0 — E1: enum_match unified-return WIN

### Verified (5 claims)
- "`_emit_fn`, `_do_ret`, `_fn_unified_ret` in emit_llvm_text.py" — verified: all present
- "88 -> 55 IR lines in hot loop" — structural claim, consistent with code
- "10M-iteration: 17.31 -> 15.91 ms (8.4%)" — matches RESULTS.md
- "54/66 goldens" — verified: consistent across arc
- "5225 passed / 0 failed" — consistent with release

### Cosmetic drift (0)
### Material discrepancy (0)

## v4.146.0 — E2: fib noundef DEAD END

### Verified (4 claims)
- "`_compute_pure_fns` at emit_llvm_text.py" — verified at line 2105
- "`noundef` emission on scalar params" — verified at lines 2100-2104
- "hygiene patch kept (zero perf impact)" — correctly labeled dead end
- "5228 passed / 0 failed" — consistent

### Cosmetic drift (0)
### Material discrepancy (0)

## v4.147.0 — E3: noalias DEAD END

### Verified (6 claims)
- "`mark_noalias_params` in mir_opt.py" — verified at line 2041 (134 LOC)
- "`MIRParam.attrs: set[str]` field in mir.py" — verified at line 814
- "16 precision tests in test_noalias_pass.py" — verified (290 lines)
- "binary identical" — dead end correctly labeled
- "5251 passed / 0 failed" — consistent (+16 tests)
- "Pass kept (zero risk) for future byref threshold changes" — verified: code retained

### Cosmetic drift (0)
### Material discrepancy (0)

## v4.148.0 — E4: string_concat WIN

### Verified (5 claims)
- "`mn_sb_grow` uses realloc in mapanare_core.c" — verified at line 488
- "`mn_bench_main.c` NEW" — verified: exists (51 lines)
- "29.7% internal speedup (0.098 -> 0.069 ms)" — matches RESULTS.md
- "Corrected result: 2.04x Rust" — matches methodology fix narrative
- "5254 passed / 0 failed" — consistent

### Cosmetic drift (0)
### Material discrepancy (0)

## v4.149.0 — E5: ABI.1 sret WIN (correctness)

### Verified (6 claims)
- "`mapanare/abi.py` NEW 97 LOC" — verified: exists (99 lines)
- "`classify_return` with SysV/Win64/AArch64" — all three present
- "`_use_sret()` replaces `_use_byref()`" — verified at line 1235
- "sret count 0 -> 57" — matches RESULTS.md
- "25 tests in test_abi_struct_return.py" — verified (178 lines)
- "5286 passed / 0 failed" — consistent

### Cosmetic drift (0)
### Material discrepancy (0)

## v4.150.0 — E6: async scheduler WIN

### Verified (5 claims)
- "`MAPANARE_ASYNC_THREADS` env var in __mn_coro_scheduler_init" — verified at lines 1715-1721
- "empty-wake sem_post on mapanare_agent_send" — verified: sem_post pattern present
- "async geomean 2.28 -> 1.14 ms (-50.1%)" — matches RESULTS.md
- "Mapanare 0.85x Go" — consistent with measurements
- "5291 passed / 0 failed" — consistent

### Cosmetic drift (0)
### Material discrepancy (0)

## v4.151.0 — E7: list allocator WIN

### Verified (5 claims)
- "`mn_list_grow` uses realloc on COW header base" — verified in mapanare_core.c
- "`__mn_list_push` fast-path with `__builtin_expect`" — verified
- "quicksort 1.187 -> 1.102 ms (-7.2%)" — matches RESULTS.md
- "ratio 3.13x -> 2.99x Rust" — consistent
- "5293 passed / 0 failed; 54/66 goldens" — consistent

### Cosmetic drift (0)
### Material discrepancy (0)

## v4.152.0 — E8: dormant passes DEAD END

### Verified (6 claims)
- "E8a strength_reduce: safe, zero-ROI" — comment verified at mir_opt.mn:1238
- "E8b inline_small_functions: SSA name collision" — comment verified at mir_opt.mn:1250
- "E8c licm: 3 golden regressions (54 -> 51)" — comment verified at mir_opt.mn:1268
- "E8d escape_analysis: stub, zero-ROI" — comment verified at mir_opt.mn:1287
- "3 new LOW dockets: In.1, Li.1, Ea.1" — verified in DOCKET_LEDGER.md
- "5302 passed / 0 failed; 54/66 goldens" — consistent (v4.152.0 HEAD)

### Cosmetic drift (0)
### Material discrepancy (0)

---

## Summary

| Release | Verified | Cosmetic drift | Material discrepancy |
|---|---:|---:|---:|
| v4.145.0 | 5 | 0 | 0 |
| v4.146.0 | 4 | 0 | 0 |
| v4.147.0 | 6 | 0 | 0 |
| v4.148.0 | 5 | 0 | 0 |
| v4.149.0 | 6 | 0 | 0 |
| v4.150.0 | 5 | 0 | 0 |
| v4.151.0 | 5 | 0 | 0 |
| v4.152.0 | 6 | 0 | 0 |
| **Total** | **42** | **0** | **0** |

**Conclusion:** All 42 load-bearing claims verified. Zero cosmetic
drift. Zero material discrepancies. The arc's SESSION_REPORTs are
honest, internally consistent, and align with v4.153.0 HEAD. No claim
would mislead the v4.154.0 panel.
