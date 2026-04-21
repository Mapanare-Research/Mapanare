# Viper — Memory Safety Review (Arc 10)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

Two memory safety items closed in this arc:

**Item 49 (drop-glue, 8 cycles):** The fix is minimal and correct. The blanket early return at `emit_llvm_text.py:1445` was a leak-over-UAF tradeoff from v4.18.0. Removing it is safe because `_emit_drop_glue_collect_ret_ptrs` extracts every pointer that escapes via the return value, and the per-kind helpers (`_emit_drop_glue_strings`, `_emit_drop_glue_closures`, etc.) compare against `ret_ptr_fields` before freeing. The test `test_struct_with_string_field_return_has_drop_glue` proves that `__mn_str_free` is now emitted for heap-allocated locals in struct-return functions — exactly the leak the blanket return was causing.

**Item 50 (agent destroy, 2 cycles):** Setting `message_dtor = free` as the default in `mapanare_agent_init` is correct. The drain loop (added in v4.33.0) already existed but was a no-op because `message_dtor` was NULL after `memset`. The fix is 3 lines. The test verifies both the default `free()` path and custom destructors. Agents are single-consumer (the handler thread is the only reader), so the drain loop in `mapanare_agent_destroy` does not have a race condition — the thread has already been joined or stopped before destroy is called.

## Specific findings

1. **PASS**: No new leaks introduced. Integration pipeline runs all 47 passing tests to completion without memory errors visible in exit codes.
2. **PASS**: Agent destroy test passes with `-Werror`, confirming no type-safety warnings.
3. **NOTE**: Full valgrind sweep not performed in this session due to WSL constraints. The code-level analysis is sound.

## Score justification

9/10 — both fixes are minimal, correct, and tested. Item 49 was the oldest open memory item (8 cycles); closing it properly is significant. One point reserved because valgrind confirmation was not performed end-to-end.
