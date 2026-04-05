# v3.8.0 — Compiler Hardening — Continuation Prompt

> Eliminate dead PHIs. Raise loop bounds. Complete method return types. Fix substr.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.8.0/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.

## MANDATORY: Use Culebra for ALL IR debugging

```bash
# Wrap ALL gcc/clang/llvm-as commands through Culebra
~/.cargo/bin/culebra wrap -- clang -c -O2 output.ll -o output.o
~/.cargo/bin/culebra wrap -- llvm-as output.ll -o /dev/null

# Scan for IR pathologies
~/.cargo/bin/culebra scan output.ll
~/.cargo/bin/culebra triage output.ll --brief

# Before ANY compiler change: save baseline
~/.cargo/bin/culebra baseline save mapanare/self/main.ll

# After ANY compiler change: diff against baseline
~/.cargo/bin/culebra baseline diff mapanare/self/main.ll

# Track progress
~/.cargo/bin/culebra journal add "description" --action fix --tags "v3.8.0"
~/.cargo/bin/culebra journal show

# Dead PHI analysis (Phase 1 — the primary target)
~/.cargo/bin/culebra scan /tmp/stage2.ll --id dead-phi-chain
~/.cargo/bin/culebra scan /tmp/stage2.ll --id match-phi-zeroinit-corruption
~/.cargo/bin/culebra scan /tmp/stage2.ll --id phi-operand-type-mismatch
~/.cargo/bin/culebra bisect /tmp/stage2.ll /tmp/stage3.ll
~/.cargo/bin/culebra diff-ir /tmp/stage2.ll /tmp/stage3.ll

# Method return types (Phase 3)
~/.cargo/bin/culebra scan /tmp/stage2.ll --id return-type-divergence
~/.cargo/bin/culebra explain /tmp/stage2.ll return-type-divergence --function lower_method_call

# Substr analysis (Phase 4)
~/.cargo/bin/culebra scan /tmp/stage2.ll --id substr-empty-result

# Full audit (Phase 5)
~/.cargo/bin/culebra scan /tmp/stage2.ll --severity critical
~/.cargo/bin/culebra field-index-audit /tmp/stage2.ll
~/.cargo/bin/culebra health /tmp/stage2.ll
~/.cargo/bin/culebra compare /tmp/stage2.ll /tmp/stage3.ll --metric calls
~/.cargo/bin/culebra baseline save /tmp/stage2.ll
```

## MANDATORY: Regression testing after EVERY compiler change

```bash
# 1. Rebuild
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# 2. Golden tests (must be 25/25)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# 3. Stdlib scorecard (must be 35/35)
for f in $(find stdlib -name '*.mn' -not -path '*/wasm/*' -not -path '*/gpu/*'); do
    ./mapanare/self/mnc-stage1 "$f" > /tmp/t.ll 2>/dev/null
    sed -n '/^; ModuleID/,$p' /tmp/t.ll > /tmp/t_clean.ll
    llvm-as /tmp/t_clean.ll -o /dev/null 2>/dev/null && echo "OK $(basename $f)" || echo "FAIL $(basename $f)"
done

# 4. Native tests (must be 7/7, 99 assertions)
for f in tests/native/test_*.mn; do
    ./mapanare/self/mnc-stage1 test "$f" 2>/dev/null | tail -1
done

# 5. Stage2/stage3 diff (GOAL: 0 lines)
timeout 120 ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll 2>/dev/null
clang -c -O2 /tmp/stage2.ll -o /tmp/stage2.o 2>/dev/null
gcc /tmp/stage2.o runtime/native/mapanare_core.c mapanare/self/mnc_main.c \
    -I runtime/native -o /tmp/mnc-stage2 -no-pie -rdynamic -lm -lpthread 2>/dev/null
ulimit -s unlimited && timeout 120 /tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.ll 2>/dev/null
diff /tmp/stage2.ll /tmp/stage3.ll | head -20
echo "Diff lines: $(diff /tmp/stage2.ll /tmp/stage3.ll | wc -l)"

# 6. Fixed point (stage3 == stage4, must hold)
clang -c -O2 /tmp/stage3.ll -o /tmp/stage3.o 2>/dev/null
gcc /tmp/stage3.o runtime/native/mapanare_core.c mapanare/self/mnc_main.c \
    -I runtime/native -o /tmp/mnc-stage3 -no-pie -rdynamic -lm -lpthread 2>/dev/null
ulimit -s unlimited && timeout 120 /tmp/mnc-stage3 mapanare/self/mnc_all.mn > /tmp/stage4.ll 2>/dev/null
diff /tmp/stage3.ll /tmp/stage4.ll && echo "FIXED POINT OK" || echo "FIXED POINT BROKEN"

# 7. If anything regressed: REVERT and try a different approach
```

## MANDATORY: Validate locally before commit

```bash
black --check --target-version py311 .
ruff check .
python3 -m mypy mapanare/ runtime/ --ignore-missing-imports
gcc -O2 -Wall -Wextra -Werror -pthread tests/native/test_c_runtime.c \
    runtime/native/mapanare_core.c runtime/native/mapanare_runtime.c \
    -o /tmp/test_c_runtime && /tmp/test_c_runtime

for f in examples/wasm/hello.mn examples/wasm/wasi_app.mn; do
    python3 -m mapanare emit-wasm "$f" -o /tmp/t.wat && wat2wasm /tmp/t.wat -o /dev/null
    python3 -m mapanare emit-wasm --wasi "$f" -o /tmp/t.wat && wat2wasm /tmp/t.wat -o /dev/null
done

python3 -m pytest tests/bootstrap/ tests/stdlib/ tests/self_hosted/ \
    tests/test_doc_links.py tests/semantic/ tests/parser/ tests/llvm/ \
    tests/wasm/ tests/e2e/ -q --tb=no
```

---

## Context

v3.7.0 reached:
- Cross-module imports (directory-based module resolution)
- 32MB compiler thread (self-compilation without ulimit)
- `./mnc run` subcommand
- 99 native assertions across 7 modules
- 35/35 stdlib, 25/25 golden, fixed point (stage3 == stage4)
- C runtime: `__mn_clock_monotonic_ns`, `__mn_sleep_ms`

The compiler works. Now make it bulletproof.

---

## Inherited State

| Component | Status |
|-----------|--------|
| Self-hosted compiler | 25/25 golden, fixed point |
| Seed binary | v3.7.0, 32MB thread |
| Stdlib compiled | 35/35 modules |
| Native tests | 99 assertions across 7 modules |
| CLI | `./mnc`, `./mnc test`, `./mnc build`, `./mnc run`, `./mnc version` |
| Definition counts | 725 fn, 69 struct, 12 enum |
| Stage2/stage3 diff | 11 dead PHI lines |

---

## Attack Order

### Phase 1: Dead PHI Elimination (Stage2 == Stage3)

The stage2/stage3 diff has exactly 11 lines — all dead PHI nodes with
`zeroinitializer` entries that are never consumed. These come from 7
functions where match expressions produce void/unknown results.

**The 11 dead PHIs (all present in stage2, absent in stage3):**

```
has_explicit_main:       phi i64 [zeroinit, zeroinit]
parse_expr:              phi i64 [zeroinit, zeroinit]
check_impl_body:         phi %struct.SemState [zeroinit, %t17]
register_extern_fn:      phi i64 [zeroinit, zeroinit]
lower_identifier:        phi i64 [zeroinit] (single entry)
lower_assign:            phi i64 [zeroinit] chain (3 PHIs)
emit_list_init_checked:  phi i64 [zeroinit] + phi i64 [zeroinit]
```

**Root cause:** The Python text emitter (`mapanare/emit_llvm_mir.py`)
generates PHI nodes for match expressions even when all arms are
void/side-effect-only. The self-hosted emitter (`emit_llvm.mn`) correctly
skips these dead PHIs.

**Fix approach:**
1. **Diagnose** — use Culebra to trace each of the 7 functions:
   ```bash
   culebra explain /tmp/stage2.ll match-phi-zeroinit-corruption --function has_explicit_main
   culebra trace /tmp/stage2.ll --function has_explicit_main --var '%match_result25'
   ```

2. **Locate** in Python emitter — find where match PHIs are emitted in
   `emit_llvm_mir.py`. Look for the merge block PHI generation after
   match arms. The code likely doesn't check if the PHI result is dead.

3. **Fix** — add a check: if all PHI entries are `zeroinitializer` and
   the result name is unused in subsequent instructions, skip the PHI.
   OR: if all match arms return void, don't emit a merge PHI at all.

4. **Verify** — `diff /tmp/stage2.ll /tmp/stage3.ll` must produce
   empty output. Use `culebra bisect` to confirm 0 divergent functions.

**Files:** `mapanare/emit_llvm_mir.py` (match lowering, PHI emission)

### Phase 2: Loop Bound Hardening

Raise bounds in `mapanare/self/lower.mn` and `mapanare/self/emit_llvm.mn`:

| Current | New  | Loops affected | Rationale |
|---------|------|----------------|-----------|
| 200     | 500  | 25 loops in lower.mn | Struct fields, enum variants, args, methods, match arms. 200 is tight for large imported modules. |
| 2000    | 5000 | 4 loops in lower.mn | Definition registration, function lookups. 725 fns now, will grow with monorepo. |
| 600     | 2000 | 3 loops in lower.mn | Statements, list/map elements. 600 limits large function bodies. |

Also raise bounds in `emit_llvm.mn` — grep for `for _ in 0..` and apply
the same logic.

**Important:** After raising bounds, verify:
1. All tests still pass (no behavior change)
2. Compile time doesn't regress significantly
3. Fixed point still holds

### Phase 3: Method Return Type Completeness

**3a. Expand `str_method_return_type` (lower.mn:1414)**

Add these missing methods:

```mapanare
// Currently missing — return mir_unknown()
if method == "len" { return mir_int() }       // used everywhere
if method == "join" { return mir_string() }   // text.mn
if method == "strip" { return mir_string() }  // parsing
if method == "upper" { return mir_string() }  // alias
if method == "lower" { return mir_string() }  // alias
if method == "index" { return mir_int() }     // alias for find
if method == "slice" { return mir_string() }  // slicing
if method == "is_empty" { return mir_bool() } // text.mn
if method == "reverse" { return mir_string() }
if method == "repeat" { return mir_string() }
if method == "center" { return mir_string() }
if method == "pad_start" { return mir_string() }
if method == "pad_end" { return mir_string() }
```

**3b. Add `list_method_return_type` (new function)**

```mapanare
fn list_method_return_type(method: String) -> MIRType {
    if method == "push" { return mir_void() }
    if method == "pop" { return mir_unknown() }  // element type unknown
    if method == "len" { return mir_int() }
    if method == "is_empty" { return mir_bool() }
    if method == "contains" { return mir_bool() }
    if method == "reverse" { return mir_list() }
    if method == "sort" { return mir_list() }
    return mir_unknown()
}
```

**3c. Wire up in `lower_method_call`**

After the string check (line 1458), add:
```mapanare
if obj_r.value.ty.kind == "list" {
    ret_ty = list_method_return_type(method)
}
```

**Verify with Culebra:**
```bash
culebra scan /tmp/stage2.ll --id return-type-divergence
```

### Phase 4: Substr Semantics Fix

1. **Write native test** for substr edge cases:
   ```mapanare
   // test in tests/native/test_text.mn or separate file
   check_eq_str("substr(0,3)", "hello".substr(0, 3), "hel")
   check_eq_str("substr(2,3)", "hello".substr(2, 3), "llo")
   check_eq_str("substr(0,0)", "hello".substr(0, 0), "")
   check_eq_str("substr(4,1)", "hello".substr(4, 1), "o")
   ```

2. **Verify C runtime** — the implementation at `mapanare_core.c:400`
   takes `(string, start, count)`. Confirm it handles:
   - count=0 → empty
   - start+count > len → clamp to len
   - start=0, count=1 → single char
   - start > 0, count > 0 → mid-string extraction

3. **Fix misleading comment** in lower.mn:1339:
   ```
   // substr(start, END) not substr(start, LENGTH)
   ```
   This is WRONG — the C runtime uses (start, count/LENGTH).
   The code `substr(colon+1, len(ret_encoded))` works by accident
   because count is clamped to `s.len`. Fix the comment.

4. **Evaluate emit_llvm.mn workarounds** — if substr works correctly,
   replace char-by-char loops with direct substr calls where possible.

### Phase 5: Culebra Full Audit + Baseline Lock

After all fixes:

```bash
# Generate fresh stage2
timeout 120 ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll

# Full diagnostic suite
culebra scan /tmp/stage2.ll
culebra triage /tmp/stage2.ll --brief
culebra field-index-audit /tmp/stage2.ll
culebra health /tmp/stage2.ll

# Stage comparison (should be clean now)
culebra bisect /tmp/stage2.ll /tmp/stage3.ll
culebra compare /tmp/stage2.ll /tmp/stage3.ll --metric calls

# Lock clean baseline
culebra baseline save /tmp/stage2.ll
culebra journal add "v3.8.0: compiler hardening complete" --action milestone --tags "v3.8.0"
```

### Phase 6: Seed + Bootstrap

```bash
# Update seed
cp mapanare/self/mnc-stage1 mapanare/self/mnc-seed
sha256sum mapanare/self/mnc-seed | awk '{print $1}' > mapanare/self/mnc-seed.sha256

# Full bootstrap verification
bash scripts/build_from_seed.sh --verify

# Confirm stage2 == stage3 (gap should be closed)
diff /tmp/mapanare_stage1.ll /tmp/mapanare_stage2.ll | wc -l
# Expected: 0 or very small
```

---

## Known Issues to Expect

1. **PHI emission order** — Python emitter and self-hosted emitter may
   generate PHI entries in different orders for the same block. This is
   semantically equivalent but breaks `diff`. Normalize before comparing.

2. **`lambda_vars` dual use** — stores both fn return types (`__ret__name`)
   and actual lambda registrations. The `count_actual_lambdas()` function
   filters by checking `!starts_with("__ret__")`.

3. **COW list semantics** — pushing to a list inside a for-loop can corrupt
   emitter state. Use helper functions or build lists outside loops.

4. **`emit_mir_module` returns string** — the `compile()` function returns
   IR text directly. `test`/`build`/`run` use `__mn_file_write` + sed for
   main→mn_main rename.

5. **The `check_impl_body` PHI** (line 31914 in stage2) is special — it
   has type `%struct.SemState` with one zeroinit arm and one real arm.
   This may require different handling than the all-zeroinit cases.

---

## Verification Commands

```bash
# Rebuild compiler
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# Quick regression
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
for f in tests/native/test_*.mn; do ./mapanare/self/mnc-stage1 test "$f" 2>/dev/null | tail -1; done

# Stage diff (THE KEY METRIC — must be 0 after Phase 1)
diff /tmp/stage2.ll /tmp/stage3.ll | wc -l

# Fixed point
diff /tmp/stage3.ll /tmp/stage4.ll && echo "FIXED POINT"

# Culebra quick check
culebra triage /tmp/stage2.ll --brief
culebra field-index-audit /tmp/stage2.ll

# Full validation
black --check --target-version py311 . && ruff check . && python3 -m mypy mapanare/ runtime/ --ignore-missing-imports
python3 -m pytest tests/ -q --tb=no
```
