# v3.37.0 — "Araguato" — Memory Safety: List COW + Drop Glue

> Fix the two root causes that prevent self-compilation. After this
> version, mnc compiles mnc_all.mn without crashing and no_drop_glue is gone.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.37.0/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.
> Run `/golden` after every compiler change.
> Use Culebra for IR validation. Use valgrind for memory validation.

---

## Context

mnc-stage1 crashes with `corrupted double-linked list` when compiling
mnc_all.mn (760KB). Valgrind shows use-after-free in parser functions.
Root cause: struct copy doesn't increment list refcounts, and drop glue
frees lists embedded in returned structs.

The `no_drop_glue=True` hack disables ALL memory cleanup. This "works"
for single-file compilation but makes the compiler leak everything and
can't compile itself (760KB file = too many leaked allocations).

**Current version:** 3.36.0
**Target version:** 3.37.0

---

## What Needs Doing

### Phase 1: Fix struct copy in text emitter [do first — root cause]

**File:** `mapanare/emit_llvm_text.py` — `_do_copy` method

When copying a struct, clone list fields (call `__mn_list_clone`) so the
refcount is correct. This prevents double-free from aliased pointers.

Steps:
1. In `_do_copy`, detect struct types containing list fields
2. For each list field: extractvalue → __mn_list_clone → insertvalue
3. Handle nested structs recursively (struct → struct → list)
4. Also handle string fields the same way (call __mn_str_clone or similar)

Test: Compile hello.mn with drop glue ENABLED (no_drop_glue=False).
Run under valgrind — should see fewer invalid reads.

### Phase 2: Fix drop glue for returned structs [do second]

**File:** `mapanare/emit_llvm_text.py` — `_emit_drop_glue` method

When the return type is a struct containing list/string fields, DON'T
free those lists/strings. They're now properly refcounted (from Phase 1)
and the caller's drop glue will handle them.

Approach:
1. At return, check if ret_ty is a struct
2. If struct has list/string fields (recursively), mark those variables
   as "transferred to return value"
3. Skip freeing transferred variables

Alternatively (simpler): when returning a struct, skip ALL list/string
drop glue in the function. Conservative but safe — the small leak from
non-returned locals is acceptable for now.

Test: Same as Phase 1 but should now pass valgrind completely.

### Phase 3: Harden C runtime COW [do third]

**File:** `runtime/native/mapanare_core.c`

Add defensive checks:
1. `mn_list_rc()` — validate magic before reading refcount
2. `__mn_list_free()` — check magic, don't free if corrupted
3. `__mn_list_push()` — validate list fields before operating
4. `mn_list_detach()` — check refcount > 0 before decrement

Run ASan + TSan after changes:
```bash
gcc -fsanitize=address -fno-omit-frame-pointer -g \
    tests/native/test_c_runtime.c runtime/native/mapanare_core.c \
    runtime/native/mapanare_runtime.c -o test_asan
ASAN_OPTIONS=detect_leaks=1 ./test_asan
```

### Phase 4: Remove no_drop_glue hack [do after phases 1-3 pass valgrind]

**Files:** `mapanare/emit_llvm_text.py`, `mapanare/multi_module.py`,
`scripts/build_stage1.py`

1. Remove `no_drop_glue` parameter from LLVMTextEmitter.__init__
2. Remove `no_drop_glue` from _emit_with_backend and compile_multi_module_mir
3. Remove `no_drop_glue=True` from build_stage1.py
4. Rebuild: `python3 scripts/build_stage1.py --skip-check`
5. Test: `./mapanare/self/mnc-stage1 tests/golden/01_hello.mn | llvm-as -o /dev/null`
6. All 29+ golden tests must still pass

### Phase 5: Self-compilation test [the big one]

```bash
ulimit -s unlimited
./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll 2>&1
echo "Lines: $(wc -l < /tmp/stage2.ll)"
llvm-as /tmp/stage2.ll -o /dev/null && echo "VALID" || echo "INVALID"
```

If this passes, self-hosting works. Run Culebra to validate:
```bash
culebra scan /tmp/stage2.ll --tags abi
culebra health /tmp/stage2.ll
culebra triage /tmp/stage2.ll --brief
```

### Phase 6: Culebra baseline [final]

```bash
culebra baseline save mapanare/self/main.ll
culebra summary mapanare/self/main.ll
```

---

## Verification Checklist

```bash
# 1. Valgrind clean on simple compilation
valgrind --error-exitcode=1 --max-stackframe=67108864 \
    ./mapanare/self/mnc-stage1 tests/golden/01_hello.mn > /dev/null 2>&1

# 2. Golden tests
/golden

# 3. Self-compilation
./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
llvm-as /tmp/stage2.ll -o /dev/null

# 4. no_drop_glue is gone
grep -r "no_drop_glue" mapanare/ scripts/ && echo "FAIL: still present"

# 5. ASan clean
gcc -fsanitize=address tests/native/test_c_runtime.c \
    runtime/native/mapanare_core.c runtime/native/mapanare_runtime.c \
    -o test_asan && ASAN_OPTIONS=detect_leaks=1 ./test_asan

# 6. Culebra health
culebra health mapanare/self/main.ll

# 7. Benchmarks
bash tests/bench/bench_compile.sh --gate
```

---

## Version Bump

1. Run `/bump-version` to 3.37.0
2. CHANGELOG.md:
   - **Fixed:** Struct copy now clones list fields (COW refcount increment)
   - **Fixed:** Drop glue skips list/string fields in returned structs
   - **Fixed:** C runtime validates COW magic before refcount access
   - **Removed:** `no_drop_glue` hack — proper memory management restored
   - **Added:** Self-compilation works: mnc-stage1 compiles mnc_all.mn
3. Commit: `v3.37.0: "Araguato" — fix list COW + drop glue, self-compilation restored`
