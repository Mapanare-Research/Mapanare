# Mapanare v3.26.0 — "Cunaguaro" (Review Gate)

> Fix all v3.25.0 code review blockers and should-fix items. This is the
> cleanup release that clears the path to the transpiler framework and v4.0.0.
> No new features — only fixes, deprecations, and quality improvements.

**Status:** DONE
**Estimated scope:** Medium (1-2 sessions)
**Breaking:** No
**Prerequisite:** v3.25.0

---

## Motivation

The v3.25.0 code review (7 reviewers, aggregate 9.07/10) identified 6 hard
blockers and 14 should-fix items for v4.0.0. This release resolves all hard
blockers and the highest-priority should-fix items. No new features are added —
this is pure quality debt repayment.

The name "Cunaguaro" (Venezuelan ocelot) reflects precision: targeted fixes,
no wasted motion.

---

## Items

### 1. Fix `TypeKind.ANY` emitter mapping [HIGH]

**File:** `mapanare/emit_llvm_text.py`, `mapanare/emit_llvm_mir.py`
**Reporter:** Rattler (H1), Coral (H1), Viper (M6)
**Fix:** Add `MN_VALUE = "{i32, i32, {ptr, i64}}"` constant. Map `TypeKind.ANY`
to `MN_VALUE` in `_rty()` (text emitter) and `_resolve_mir_type()` (llvmlite
emitter). Add box/unbox call emission in the lowerer for `any`-typed assignments:
emit `__mn_any_box_int`/`__mn_any_box_float`/`__mn_any_box_bool` when assigning
concrete types to `any` variables, and `__mn_any_unbox_*` when reading. Reject
`any + any` arithmetic with a clear error until full runtime dispatch is
implemented. Add `any` section to `docs/SPEC.md` (Section 3, subsection after
Special Types).

### 2. Rebuild `main.ll` + re-bless golden tests [HIGH]

**File:** `mapanare/self/main.ll`, `mapanare/self/main.mn`, `tests/golden/*.ref.ll`
**Reporter:** Rattler (H2), Anaconda (M1)
**Fix:** Fix version string in `main.mn` from `"mapanare 3.16.0"` to
`"mapanare 3.26.0"`. Run `bash scripts/rebuild.sh` to regenerate `main.ll`
with 5-field list ABI, function attributes, and `align 8` string constants.
Run `python scripts/test_native.py --bless` to regenerate all golden reference
files. Commit the regenerated artifacts.

### 3. Fix PHP transpiler `$this` → `self` [HIGH]

**File:** `mapanare/from_php.py` (line ~626)
**Reporter:** Boa (H1)
**Fix:** After `name = tok.value[1:]`, add: `if name == "this": name = "self"`.
Add test assertion: `assert "self.value" in mn` for class method bodies.

### 4. Fix PHP transpiler return type translation [HIGH]

**File:** `mapanare/from_php.py` (lines ~968, ~1015)
**Reporter:** Boa (H2)
**Fix:** After parsing return type hints, pass through `_translate_type()`:
`ret_type = self._translate_type(ret_type)`. Apply in both `_translate_function`
and `_translate_method`. Add test: `assert "-> Int" in mn` for typed functions.

### 5. Fix PHP transpiler `isset`/`empty`/`is_array` mapping [HIGH]

**File:** `mapanare/from_php.py` (lines ~91-97, ~830-838)
**Reporter:** Boa (H3)
**Fix:** Add special-case branches in `_translate_func_call` for pattern-based
mappings: `isset($x)` → `x != None`, `empty($arr)` → `len(arr) == 0`,
`is_array($x)` → `typeof(x) == "List"`, `is_string($x)` → `typeof(x) == "String"`,
`is_int($x)` → `typeof(x) == "Int"`. Add tests for each mapping.

### 6. Fix `emit_c.py` stream operation call signatures [HIGH]

**File:** `mapanare/emit_c.py` (lines ~2264, ~2267, ~2277, ~2282)
**Reporter:** Mamba (H1)
**Fix:** Match call sites to C function declarations in `mapanare_core.h`:
- `__mn_stream_map`: 4 args (source, fn, user_data, out_elem_size)
- `__mn_stream_filter`: 3 args (source, pred_fn, user_data)
- `__mn_stream_collect`: 2 args (stream, elem_size)
- `__mn_stream_fold`: 6 args with correct order (stream, init_ptr, acc_size, fold_fn, user_data, out_ptr)

### 7. Add locking to `__mn_signal_unsubscribe` [MEDIUM]

**File:** `runtime/native/mapanare_core.c` (line ~1823)
**Reporter:** Viper (H2)
**Fix:** Wrap the subscriber array iteration and shift in
`mn_signal_lock()`/`mn_signal_unlock()`, matching the locking pattern in
`__mn_signal_subscribe`.

### 8. Fix `__mn_map_free_deep` value type heuristic [MEDIUM]

**File:** `runtime/native/mapanare_core.c` (line ~1589), `runtime/native/mapanare_core.h`
**Reporter:** Viper (H3)
**Fix:** Add `int64_t val_type` field to `MnMap` struct (MN_MAP_VAL_STR = 1,
MN_MAP_VAL_OPAQUE = 0). Set in `__mn_map_new`. Use in `__mn_map_free_deep`
instead of the `val_size == sizeof(MnString)` heuristic. Update all emitters
that create maps.

### 9. Deprecate llvmlite emitter [MEDIUM]

**File:** `mapanare/emit_llvm_mir.py`, `mapanare/cli.py`
**Reporter:** Viper (H1), Rattler (M5), Cobra
**Fix:** Add deprecation warning when `--emitter llvmlite` is used:
`"Warning: llvmlite emitter is deprecated. Use the default text emitter."`.
Add `# DEPRECATED` header comment to `emit_llvm_mir.py`. Update CLI help text
to indicate text emitter is the default and llvmlite is legacy.

### 10. Wire `cmd_transpile` for PHP + miscellaneous fixes [MEDIUM]

**File:** `mapanare/cli.py` (line ~1399), `docs/cookbook.md` (line ~40),
`docs/SPEC.md`
**Reporter:** Boa (M1, M4), Coral (LOW)
**Fix:** In `cmd_transpile()`, detect `.php` extension and call
`from_php.translate_to_mn()`. Fix cookbook output comment from `v0.5.0` to
current version. Document `di` keyword in spec Section 2.1 keyword table.
Fix "an Mapanare" → "a Mapanare" in CLI help (line ~1640).

---

## What's NOT in This Release

- **No new transpilers.** TypeScript and Go transpilers come in v3.30.0+.
- **No transpiler framework.** The shared `transpiler.mn` module comes in v3.27.0.
- **No self-hosted transpilers.** Porting from Python to `.mn` comes in v3.28.0+.
- **No full `any` runtime dispatch.** Arithmetic on `any` values is rejected with
  a clear error. Full dispatch is deferred to post-v4.0.0.
- **No arena allocation routing.** Arena create/destroy overhead remains.
  Routing allocations through `mn_arena_alloc` is a v4.1 item.

---

## Verification

- [ ] `mapanare compile test_any.mn` with `let x: any = 42` produces valid IR
  (24-byte MnValue alloca, not 8-byte PTR)
- [ ] `mapanare compile test_any.mn` with `x + y` where both are `any` produces
  a clear error message, not corrupt IR
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — all golden pass
- [ ] `main.ll` has 5-field list struct, function attributes, `align 8`
- [ ] PHP: `class Foo { public function bar() { return $this->x; } }` →
  `self.x` (not `this.x`)
- [ ] PHP: `function get(): int` → `fn get() -> Int` (not `-> int`)
- [ ] PHP: `isset($x)` → `x != None` (not `!= None(x)`)
- [ ] C backend: stream programs compile without argument count errors
- [ ] `make lint && make test` — all pass
- [ ] `.\dev.ps1 validate` — full suite green
