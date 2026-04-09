# Mapanare v4.10.0 — Drop Glue Complete (Remove skip_struct_ret)

> Every struct-returning function gets proper cleanup. No more leaks.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.9.0 (semantic.mn must be memory-safe first)

---

## The Problem

`skip_struct_ret` in `emit_llvm_text.py` disables ALL drop glue for
struct-returning functions. This means every string, closure, list,
and map allocated inside a struct-returning function is leaked.

v4.9.0 fixed semantic.mn memory safety. Now it's safe to remove
skip_struct_ret because the escape analysis won't hit freed memory.

---

## Phase 1: Remove skip_struct_ret

- [ ] Delete the `skip_struct_ret` check in `_emit_drop_glue`
- [ ] The existing escape analysis compares tracked values against the
      return value's embedded pointers — this is already correct
- [ ] Rebuild + golden + stage2

## Phase 2: Verify with valgrind

- [ ] Run ALL golden tests under valgrind:
      `for f in tests/golden/*.mn; do python3 scripts/ir_doctor.py valgrind "$f"; done`
- [ ] Zero "definitely lost" on struct-returning golden tests
- [ ] Zero "Invalid free" or "Invalid read"

## Phase 3: String pooling

- [ ] `__mn_str_from_bool`: return constant strings (with proper non-freeable marker)
- [ ] `__mn_str_from_int` for -128..127: use cached strings
- [ ] `__mn_str_free` must NOT free pooled strings
- [ ] Verify with valgrind: no double-free, no use-after-free

---

## Exit Criteria

| Check | Required |
|-------|----------|
| skip_struct_ret removed from emit_llvm_text.py | YES |
| Valgrind: 0 "definitely lost" on struct-return test | YES |
| str(true)/str(false) constant (no heap alloc) | YES |
| Small int str(N) pooled for -128..127 | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
