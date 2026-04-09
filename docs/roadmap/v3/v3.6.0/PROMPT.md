# v3.6.0 — Type System + Native Programs — Continuation Prompt

> Fix the type system. Compile the last stdlib module. Run real programs.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.6.0/PLAN.md`.
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
~/.cargo/bin/culebra journal add "description" --action fix --tags "v3.6.0"
~/.cargo/bin/culebra journal show

# Trace variables, dump functions, map symptoms
~/.cargo/bin/culebra trace output.ll --function fn_name --var '%var'
~/.cargo/bin/culebra dump output.ll --function fn_name
~/.cargo/bin/culebra health output.ll --struct-name StructName
~/.cargo/bin/culebra map "symptom keyword"
```

## MANDATORY: Regression testing after EVERY compiler change

```bash
# 1. Save baseline status of ALL 35 stdlib modules BEFORE the change
# 2. Make the change + rebuild
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# 3. Test ALL stdlib modules — diff against baseline
# ANY module that was OK before MUST still be OK after
for f in $(find stdlib -name '*.mn' -not -path '*/wasm/*' -not -path '*/gpu/*'); do
    ./mapanare/self/mnc-stage1 "$f" > /tmp/t.ll 2>/dev/null
    sed -n '/^; ModuleID/,$p' /tmp/t.ll > /tmp/t_clean.ll
    llvm-as /tmp/t_clean.ll -o /dev/null 2>/dev/null && echo "OK $(basename $f)" || echo "FAIL $(basename $f)"
done

# 4. Golden tests
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# 5. If anything regressed: REVERT and try a different approach
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

bash scripts/build_from_seed.sh --verify
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

python3 -m pytest tests/bootstrap/ tests/stdlib/ tests/self_hosted/ \
    tests/test_doc_links.py -q --tb=no
```

---

## Context

v3.5.0 went from 10 to 34 stdlib modules (1,086 functions) by fixing:
- WASM Stackifier (proper structured control flow)
- Keyword-as-variable (soft keywords in parser)
- List concat (emit __mn_list_concat)
- Circular import dedup (at resolve_imports level)
- PHI forward-reference (deferred if_merge + match_merge blocks)
- Map return type (added "map" to call return decoder)
- Result parameterization (look up full MIRType from module.functions)

One module remains: `encoding/toml.mn` — nested match patterns lose
Map type through enum payload extraction. The lowerer's
`infer_variant_payload_type` returns the correct type but the subject
value's `.ty` field is i64 by the time it reaches the inner match.

Two golden tests fail: `11_closure` (missing lambda1 function) and
`24_enum_methods` (impl on enums produces 0 output).

---

## Inherited State

| Component | Status |
|-----------|--------|
| Self-hosted compiler | 25/25 golden (2 fail: closure, enum_methods) |
| Seed binary | v3.5.0 with all fixes |
| Stdlib compiled | 34/35 modules, 1,086 functions |
| Stdlib failing | encoding/toml.mn only |
| Native tests | math 12/12, json 6/6, fs 6/6 = 24/24 |
| CI | 1,455 pass, 0 fail |
| C runtime | 52/52, FS functions implemented |
| WASM | if/else + recursion work, for-loops need range builtins |

---

## Attack Order

### Phase 1: Type System (fix toml.mn → 35/35)

1. Fix enum payload type tracking in nested match contexts
2. Clean up lambda_vars encoding for Result/Option parameterization
3. Fix struct constructor field ordering (Construct AST node)

### Phase 2: Golden Tests (25/25 stage1)

1. Fix closure capture in self-hosted emitter
2. Fix impl methods on enums

### Phase 3: `./mnc test` CLI

1. Add test subcommand to main.mn
2. Port more stdlib tests to native .mn

### Phase 4: Run Real Programs

1. `./mnc build` — compile + link → executable
2. WASM for-loop runtime builtins
3. Demo programs that compile + run natively

---

## Known Issues to Expect

1. **List mutation in for-loops** — pushing to a list inside a for-loop
   can corrupt emitter state (COW semantics). Use helper functions or
   build lists outside loops.

2. **Variable names shadowing keywords** — `di`, `si`, `da`, `en` are
   bilingual keywords. The parser handles `input`, `output`, `agent`,
   `di`, `stream` as soft keywords in expression position, but NOT in
   assignment targets. Use `_idx` suffixes for loop variables.

3. **Module-qualified calls** — `module.func()` is parsed as a method
   call on variable `module`. Use direct `func()` calls since imports
   flatten all definitions.

4. **Struct constructor inline expressions** — complex expressions
   (enum variants, sret calls) inside `new Struct { field: expr }`
   generate ghost values. Extract into local variables.

5. **Err() type inference** — `Err(x)` infers the Ok type from the
   enclosing function's return type, not the variable's declared type.
   Use a helper function with the correct return type.

---

## Verification Commands

```bash
# Rebuild compiler
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# Build from seed
bash scripts/build_from_seed.sh --verify

# Compile a stdlib module
./mapanare/self/mnc-stage1 stdlib/math.mn > /tmp/math.ll
~/.cargo/bin/culebra wrap -- llvm-as /tmp/math.ll -o /dev/null

# Compile + link + run
./mapanare/self/mnc-stage1 program.mn > /tmp/prog.ll
clang -c -O2 /tmp/prog.ll -o /tmp/prog.o
gcc /tmp/prog.o runtime/native/mapanare_core.c \
    -I runtime/native -o /tmp/prog -no-pie -rdynamic -lm -lpthread
/tmp/prog

# Run native tests
./mapanare/self/mnc-stage1 tests/native/test_math.mn > /tmp/t.ll
# (strip debug lines, fix main ret, clang, gcc, run)

# Stdlib scorecard
for mod in $(find stdlib -name '*.mn' -not -path '*/wasm/*' -not -path '*/gpu/*'); do
    echo -n "$(basename $mod .mn): "
    ./mapanare/self/mnc-stage1 "$mod" > /tmp/t.ll 2>/dev/null
    sed -n '/^; ModuleID/,$p' /tmp/t.ll > /tmp/t_clean.ll
    llvm-as /tmp/t_clean.ll -o /dev/null 2>/dev/null && \
        echo "OK ($(grep -c '^define ' /tmp/t_clean.ll) fns)" || echo "FAIL"
done

# Culebra diagnostics
~/.cargo/bin/culebra scan /tmp/prog.ll
~/.cargo/bin/culebra journal show
```
