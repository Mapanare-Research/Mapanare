# Mapanare v3.37.0 — "Araguato" (Memory Safety: List COW + Drop Glue)

> Fix the two root causes that prevent self-compilation: (1) struct copy
> doesn't increment list refcounts, (2) drop glue frees lists embedded
> in returned structs. After this version, `no_drop_glue` is gone and
> `mnc-stage1` can compile `mnc_all.mn` without crashing.

**Status:** DONE
**Estimated scope:** Large (2-3 sessions)
**Breaking:** No (ABI-compatible — same struct layouts, same runtime functions)
**Prerequisite:** v3.36.0

---

## The Problem

Two bugs, one root cause: the text emitter doesn't manage list/string
ownership correctly across struct boundaries.

**Bug A — Struct copy doesn't increment refcount:**
```mn
fn foo(state: State) -> State {  // state.defs is a List
    let mut s = state            // Struct copy: memcpy, NO refcount++
    s.defs.push(new_def)         // COW detach allocates new buffer
    return s                     // Drop glue frees original state.defs
}                                // Caller's copy now has dangling pointer
```

The emitter generates a raw `insertvalue` / struct copy for `let s = state`.
The list's data pointer is aliased but the refcount stays at 1. When `s`
is pushed to, COW detach sees refcount == 1 and doesn't copy. When the
original `state` goes out of scope, drop glue frees it — but the caller
still holds the same pointer.

**Bug B — Drop glue frees lists in returned structs:**
```mn
fn parse() -> Program {
    let mut defs: List<Definition> = []
    // ... push to defs ...
    return start(defs)           // Returns Program { definitions: defs }
}                                // Drop glue frees defs — but it's IN the return value!
```

The drop glue tracks `defs` as a local list. At the return site, it extracts
the return value's list pointer and compares — but only for bare `List`
return types, not structs containing lists. So `defs` gets freed.

**Combined effect on large files:**
After ~10K struct copies without refcount management, freed pointers alias
new allocations. Eventually `__mn_list_push` writes to corrupted memory,
glibc detects `corrupted double-linked list`, crash.

---

## Items

### 1. Fix struct copy to clone list fields [CRITICAL]

**File:** `mapanare/emit_llvm_text.py` — `_do_copy` method (~line 1501)

When copying a struct that contains list fields, the emitter must call
`__mn_list_clone(ptr)` for each list field. `__mn_list_clone` increments
the COW refcount so both copies share the buffer safely.

Current code:
```python
def _do_copy(self, i: Copy):
    sv, st = self._get(i.src)
    self._put(i.dest, sv, st)  # Raw value copy — lists aliased, no refcount
```

Fixed code:
```python
def _do_copy(self, i: Copy):
    sv, st = self._get(i.src)
    if st.startswith("{"):
        sn = self._struct_name_for_llvm_type(st)
        if sn and sn in self._structs:
            for idx, (fname, ft) in enumerate(self._structs[sn]):
                if ft == LIST:
                    # Extract list field, clone it, put it back
                    lf = self._f("copy.lf")
                    self._L(f"{lf} = extractvalue {st} {sv}, {idx}")
                    cloned = self._rt("__mn_list_clone", LIST, ["ptr"], [(lf, "ptr")])
                    sv_new = self._f("copy.sv")
                    self._L(f"{sv_new} = insertvalue {st} {sv}, {LIST} {cloned}, {idx}")
                    sv = sv_new
    self._put(i.dest, sv, st)
```

This also needs to handle nested structs (struct field is a struct
containing a list). Use `_clone_nested_struct_lists` or a recursive walk.

**Validation:** `culebra health mapanare/self/main.ll` — no PHI zeroinit
on list fields.

### 2. Fix drop glue for structs containing lists/strings [CRITICAL]

**File:** `mapanare/emit_llvm_text.py` — `_emit_drop_glue` method (~line 889)

Current: only skips freeing when `ret_ty == LIST` (bare list return).
Needed: also skip when returning a struct that contains list/string fields.

The fix added in v3.36.0 (extracting struct field pointers) is on the
right track but incomplete — it only handles top-level fields, not:
- Nested structs (struct → struct → list)
- Constructor patterns where the list is passed to a function that
  builds the returned struct

**Conservative fix:** when returning a struct type, check if ANY field
(recursively) is a list or string. If so, skip ALL list/string cleanup
for that return. This may leak some locals, but prevents all UAF.

**Better fix:** track which specific list variables flow into the return
value (via the constructor call chain) and skip only those.

**Validation:** `valgrind ./mapanare/self/mnc-stage1 /tmp/tiny.mn` — no
"Invalid read" errors.

### 3. Add magic validation to C runtime [HIGH]

**File:** `runtime/native/mapanare_core.c`

The COW refcount is stored at `list->data[-1]` (header before the buffer).
Currently `mn_list_rc()` dereferences this without checking the magic
value. If the buffer was freed or corrupted, this reads garbage.

Add validation:
```c
static int64_t *mn_list_rc(MnList *list) {
    if (!list->data || !list->managed) return NULL;
    int64_t *header = ((int64_t *)list->data) - 2;
    if (header[0] != MN_COW_MAGIC) return NULL;  // Corrupted!
    return &header[1];
}
```

And update all callers (`__mn_list_free`, `mn_list_detach`, `__mn_list_clone`)
to handle NULL return from `mn_list_rc`.

**Validation:** `gcc -fsanitize=address` — no heap-buffer-overflow.

### 4. Remove `no_drop_glue` hack [HIGH]

**File:** `mapanare/emit_llvm_text.py`, `mapanare/multi_module.py`,
`scripts/build_stage1.py`

After fixes 1-3, re-enable drop glue for the self-hosted compiler build.
Remove the `no_drop_glue` parameter and all code paths that reference it.

If the compiler still crashes with drop glue enabled, the fix is incomplete.
Do NOT re-add the hack — fix the underlying issue.

**Validation:**
```bash
python3 scripts/build_stage1.py --skip-check  # no_drop_glue=False
./mapanare/self/mnc-stage1 tests/golden/01_hello.mn | llvm-as -o /dev/null
```

### 5. Verify self-compilation [HIGH]

**File:** `scripts/build_stage1.py`, `mapanare/self/mnc_all.mn`

The ultimate test: `mnc-stage1` compiles `mnc_all.mn` (760KB) without
crashing. This exercises all the memory management fixes under real load.

```bash
ulimit -s unlimited
./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
llvm-as /tmp/stage2.ll -o /dev/null  # Valid IR
```

If this works, self-hosting is restored.

### 6. Culebra validation pass [MEDIUM]

Run the full Culebra diagnostic suite on the regenerated IR:

```bash
culebra scan mapanare/self/main.ll --tags abi
culebra health mapanare/self/main.ll
culebra field-index-audit mapanare/self/main.ll
culebra triage mapanare/self/main.ll --brief
culebra baseline save mapanare/self/main.ll
```

Fix any critical/high findings. Save baseline for regression tracking.

---

## Verification

- [ ] `valgrind ./mapanare/self/mnc-stage1 /tmp/tiny.mn` — 0 errors
- [ ] All 29/33 golden tests pass (same 4 generic failures OK)
- [ ] `mnc-stage1` compiles `mnc_all.mn` without crashing
- [ ] `no_drop_glue` parameter removed from codebase
- [ ] `culebra health` — no critical findings on list structs
- [ ] ASan/TSan clean for C runtime tests
- [ ] `bash tests/bench/bench_compile.sh --gate` — all gates pass

---

## Commit

```
v3.37.0: "Araguato" — fix list COW + drop glue, self-compilation restored
```
