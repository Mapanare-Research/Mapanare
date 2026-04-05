# v3.7.0 — Cross-Module Types + Robust Compilation — Continuation Prompt

> Fix imported function return types. Harden the compiler. Unlock stdlib testing.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.7.0/PLAN.md`.
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
~/.cargo/bin/culebra journal add "description" --action fix --tags "v3.7.0"
~/.cargo/bin/culebra journal show

# Trace variables, dump functions, map symptoms
~/.cargo/bin/culebra trace output.ll --function fn_name --var '%var'
~/.cargo/bin/culebra dump output.ll --function fn_name
~/.cargo/bin/culebra health output.ll --struct-name StructName
~/.cargo/bin/culebra map "symptom keyword"

# Field index audit (critical for cross-module types)
~/.cargo/bin/culebra field-index-audit output.ll
~/.cargo/bin/culebra field-index-audit output.ll --struct-filter LowerState
```

## MANDATORY: Regression testing after EVERY compiler change

```bash
# 1. Save baseline status of ALL 35 stdlib modules BEFORE the change
# 2. Make the change + rebuild
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# 3. Test ALL stdlib modules — diff against baseline
for f in $(find stdlib -name '*.mn' -not -path '*/wasm/*' -not -path '*/gpu/*'); do
    ./mapanare/self/mnc-stage1 "$f" > /tmp/t.ll 2>/dev/null
    sed -n '/^; ModuleID/,$p' /tmp/t.ll > /tmp/t_clean.ll
    llvm-as /tmp/t_clean.ll -o /dev/null 2>/dev/null && echo "OK $(basename $f)" || echo "FAIL $(basename $f)"
done

# 4. Golden tests
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# 5. Native tests
for f in tests/native/test_*.mn; do
    ./mapanare/self/mnc-stage1 test "$f" 2>/dev/null | tail -1
done

# 6. Fixed-point check
timeout 120 ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll 2>/dev/null
llvm-as /tmp/stage2.ll -o /dev/null 2>&1 | head -3

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

v3.6.0 reached:
- Fixed point (stage3 == stage4)
- 35/35 stdlib (toml + body fixed)
- 25/25 golden (closure + enum_methods fixed)
- Clean compiler: emit_mir_module returns string, no debug prints, no dead code
- `./mnc test`, `./mnc build`, `./mnc version` CLI commands
- WASM for-loops (range iterator builtins)
- 3 demo programs that compile+link+run natively
- 41 native test assertions across 4 modules
- main() i32 return truncation

The ONE big remaining bug: **cross-module return type inference**.
When `test_text.mn` imports `stdlib/text` and calls `repeat("x", 3)`,
the compiler returns i64 instead of String. This blocks all stdlib
native testing beyond math/json/fs/string_utils.

---

## Inherited State

| Component | Status |
|-----------|--------|
| Self-hosted compiler | 25/25 golden, fixed point |
| Seed binary | v3.6.0, checksum OK |
| Stdlib compiled | 35/35 modules |
| Native tests | 41 assertions: math 12, json 6, fs 6, string_utils 17 |
| CLI | `./mnc`, `./mnc test`, `./mnc build`, `./mnc version` |
| WASM | for-loops work, 180/180 tests |
| CI | 2,517 passed, lint/mypy clean |

---

## Attack Order

### Phase 1: Cross-Module Return Type Inference

1. **Diagnose** — compile test_text.mn, trace the return type of `repeat`:
   ```bash
   ./mnc tests/native/test_text.mn > /tmp/test_text.ll 2>/dev/null
   culebra trace /tmp/test_text.ll --function main --var '%t9'
   culebra dump /tmp/test_text.ll --function main
   ```

2. **Root cause** — check `register_definition` in lower.mn:
   - What does `resolve_return_type_checked(st, fd.return_type)` return for
     imported function `repeat`?
   - What's stored in `lambda_vars` for `"__ret__repeat"`?
   - Does the type annotation `-> String` resolve correctly for imported fns?

3. **Fix** — likely one of:
   - Import processing order (types before functions)
   - resolve_return_type_checked needs state from the imported module
   - lambda_vars encoding loses type info across module boundaries

4. **Verify** — test_text.mn and test_time.mn compile, link, run

### Phase 2: Stack Robustness

1. Convert `lower_if` → `lower_else_clause_inner` → `lower_if` recursion
   to iterative loop for else-if chains
2. Test with body.mn-style deeply nested code without ulimit

### Phase 3: `./mnc run`

1. Add `run` subcommand to mn_main
2. Like `test` but prints output without PASS/FAIL wrapper

### Phase 4: Culebra Stage2 Audit

1. `culebra scan /tmp/stage2.ll --severity critical`
2. `culebra field-index-audit /tmp/stage2.ll`
3. Fix any findings
4. `culebra baseline save` after all fixes

### Phase 5: Native Tests → 80+ assertions

1. Write test_text.mn, test_time.mn (now possible after Phase 1)
2. Write test_csv.mn, test_log.mn
3. Update test framework if needed

---

## Known Issues to Expect

1. **Variable name collisions** — simple names like `r`, `s`, `i` in the
   compiler source can collide with IR names. Use `_idx` suffixes or longer
   names in new code.

2. **`lambda_vars` dual use** — stores both fn return types (`__ret__name`)
   and actual lambda registrations. The `count_actual_lambdas()` function
   filters by checking `!starts_with("__ret__")`.

3. **`emit_mir_module` returns string** — the `compile()` function now
   returns IR text directly. `test`/`build` use `__mn_file_write` + sed for
   main→mn_main rename.

4. **COW list semantics** — pushing to a list inside a for-loop can corrupt
   emitter state. Use helper functions or build lists outside loops.

5. **Module-qualified calls** — `module.func()` is parsed as a method call
   on variable `module`. Use direct `func()` calls since imports flatten.

---

## Verification Commands

```bash
# Rebuild compiler
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# Build from seed
bash scripts/build_from_seed.sh --verify

# Compile + run a program
./mapanare/self/mnc-stage1 build demos/fizzbuzz.mn -o /tmp/fizzbuzz && /tmp/fizzbuzz 20

# Stage2 + fixed point
timeout 120 ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
llvm-as /tmp/stage2.ll -o /dev/null
clang -c -O2 /tmp/stage2.ll -o /tmp/stage2.o
gcc /tmp/stage2.o runtime/native/mapanare_core.c mapanare/self/mnc_main.c \
    -I runtime/native -o /tmp/mnc-stage2 -no-pie -rdynamic -lm -lpthread
ulimit -s unlimited && /tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.ll
diff /tmp/stage2.ll /tmp/stage3.ll && echo "FIXED POINT"

# Culebra diagnostics
~/.cargo/bin/culebra scan /tmp/stage2.ll
~/.cargo/bin/culebra field-index-audit /tmp/stage2.ll
~/.cargo/bin/culebra triage /tmp/stage2.ll --brief
~/.cargo/bin/culebra journal show

# Stdlib scorecard
for mod in $(find stdlib -name '*.mn' -not -path '*/wasm/*' -not -path '*/gpu/*'); do
    echo -n "$(basename $mod .mn): "
    ./mapanare/self/mnc-stage1 "$mod" > /tmp/t.ll 2>/dev/null
    sed -n '/^; ModuleID/,$p' /tmp/t.ll > /tmp/t_clean.ll
    llvm-as /tmp/t_clean.ll -o /dev/null 2>/dev/null && \
        echo "OK ($(grep -c '^define ' /tmp/t_clean.ll) fns)" || echo "FAIL"
done

# Native tests
for f in tests/native/test_*.mn; do
    ./mapanare/self/mnc-stage1 test "$f" 2>/dev/null | tail -1
done
```
