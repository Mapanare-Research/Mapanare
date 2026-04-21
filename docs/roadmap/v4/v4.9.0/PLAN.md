# Mapanare v4.9.0 — semantic.mn Memory Safety

> Fix the self-hosted semantic checker so it doesn't read freed memory.
> This unblocks skip_struct_ret removal and string pooling.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.8.0

---

## The Problem

Valgrind trace when `check()` is enabled in compile():
```
Invalid read of size 8
    at ast__expr_ident_name
    by semantic__check_call_resolved
    by semantic__check_call_expr
    by semantic__infer_expr
    by semantic__check_let_stmt
```

The self-hosted semantic checker reads invalid memory in AST accessor
functions. This corrupts state and causes crashes in subsequent lowering.

---

## Phase 1: Audit AST accessor functions

- [ ] Read `ast.mn` — list all `expr_*`, `stmt_*`, `def_*` accessor functions
- [ ] For each: verify it correctly bounds-checks before accessing struct fields
- [ ] Run under valgrind with a simple test program that has a function call
- [ ] Identify which specific accessor reads out of bounds

## Phase 2: Fix the memory corruption

- [ ] Fix the identified accessor(s)
- [ ] Rebuild + valgrind clean on simple test
- [ ] Enable `check()` in `main.mn compile()` as BLOCKING (not warnings)
- [ ] Rebuild + golden + stage2

## Phase 3: Verify

- [ ] 40/40 golden with check() enabled
- [ ] 11/11 stage2 with check() enabled
- [ ] Valgrind: no invalid reads in semantic functions
- [ ] Test: deliberately broken .mn file produces error from mnc-stage1

---

## Exit Criteria

| Check | Required |
|-------|----------|
| check() enabled in compile() (blocking, not warnings) | YES |
| Valgrind: no invalid reads in semantic functions | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
