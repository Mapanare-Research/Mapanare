# v4.95.0 Session Report — 2026-04-13

## Verdict

StringBuilder + O(n^2) string concat fix shipped. Arc 13 release 4.

## What shipped

### C runtime StringBuilder (mapanare_core.c)

- `MnStringBuilder` struct: `{char *buf, int64_t len, int64_t cap}`
- `__mn_sb_create(cap)`: initial capacity (default 64), heap-allocated buffer
- `__mn_sb_append(sb, str)`: amortized O(1) with 2x exponential growth
- `__mn_sb_append_char(sb, c)`: single-char append
- `__mn_sb_to_string(sb)`: zero-copy transfer (consumes builder, returns MnString)
- `__mn_sb_destroy(sb)`: cleanup if not consumed

### Loop-concat MIR optimization (mir_opt.py)

`string_concat_optimization()` pass added to O2 pipeline. Detects
`__mn_str_concat(accumulator, chunk)` inside natural loop bodies and
renames to `__mn_sb_append_concat` for the emitter to handle.
Conservative: only fires when natural loops are detected.

### Explicit StringBuilder builtins

- `sb_create()`, `sb_append(sb, str)`, `sb_to_string(sb)` in types.py
- Lowered to `__mn_sb_create`/`__mn_sb_append`/`__mn_sb_to_string` calls

### AI stdlib refactoring

| Function | File | Before | After |
|----------|------|--------|-------|
| escape_json | llm.mn | O(n^2) concat per char | O(n) sb_append |
| messages_to_json | llm.mn | O(m^2) concat per message | O(m) sb_append |
| tools_to_json | llm.mn | O(k^2) concat per tool | O(k) sb_append |
| escape_json | embedding.mn | O(n^2) concat per char | O(n) sb_append |

### Performance impact (theoretical)

The 10K iteration `string_concat.mn` benchmark:
- **Before:** 10,000 allocations, ~250M bytes total copied (O(n^2))
- **After (with StringBuilder):** 1 allocation + ~14 reallocations (2x growth), ~100K bytes copied (O(n))
- **Expected speedup:** >= 5x for the explicit API; automatic detection is best-effort

Runtime measurements pending library rebuild (same as v4.94.0).

## Files changed

| File | Change |
|------|--------|
| `runtime/native/mapanare_core.c` | MnStringBuilder implementation |
| `runtime/native/mapanare_core.h` | MnStringBuilder type + function declarations |
| `mapanare/mir_opt.py` | string_concat_optimization pass, __mn_sb_* in non-capturing set |
| `mapanare/types.py` | sb_create/sb_append/sb_to_string builtins |
| `mapanare/lower.py` | sb_* builtin lowering |
| `stdlib/ai/llm.mn` | escape_json, messages_to_json, tools_to_json refactored |
| `stdlib/ai/embedding.mn` | escape_json refactored |

## Next session

v4.96.0: Arc 13 panel. Mamba grades the string fix.
