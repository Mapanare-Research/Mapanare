# v3.8.1 — Generics + Impl Dispatch — Continuation Prompt

> Generics monomorphization. Impl method dispatch. Trait bounds validation.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.8.1/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.

## MANDATORY: Regression testing after EVERY compiler change

```bash
# 1. Rebuild
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# 2. Golden tests (must be 28/28)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# 3. Native tests (must be 7/7, 104 assertions)
for f in tests/native/test_*.mn; do
    ./mapanare/self/mnc-stage1 test "$f" 2>/dev/null | tail -1
done

# 4. Stdlib scorecard (must be 35/35)
for f in $(find stdlib -name '*.mn' -not -path '*/wasm/*' -not -path '*/gpu/*'); do
    ./mapanare/self/mnc-stage1 "$f" > /tmp/t.ll 2>/dev/null
    sed -n '/^; ModuleID/,$p' /tmp/t.ll > /tmp/t_clean.ll
    llvm-as /tmp/t_clean.ll -o /dev/null 2>/dev/null && echo "OK $(basename $f)" || echo "FAIL $(basename $f)"
done

# 5. Generic struct smoke test (CRITICAL — catches enum layout regression)
cat > /tmp/test_gen.mn << 'EOF'
struct Pair<A, B> { first: A, second: B }
fn main() { let p = new Pair { first: 42, second: true }; print(p.first) }
EOF
./mapanare/self/mnc-stage1 /tmp/test_gen.mn > /tmp/gen.ll 2>/dev/null
grep 'Pair__Int_Bool' /tmp/gen.ll && echo "GENERICS OK" || echo "GENERICS BROKEN"

# 6. Fixed point (stage3 == stage4)
timeout 120 ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll 2>/dev/null
clang -c -O2 /tmp/stage2.ll -o /tmp/stage2.o 2>/dev/null
gcc /tmp/stage2.o runtime/native/mapanare_core.c mapanare/self/mnc_main.c \
    -I runtime/native -o /tmp/mnc-stage2 -no-pie -rdynamic -lm -lpthread 2>/dev/null
ulimit -s unlimited && timeout 120 /tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.ll 2>/dev/null
clang -c -O2 /tmp/stage3.ll -o /tmp/stage3.o 2>/dev/null
gcc /tmp/stage3.o runtime/native/mapanare_core.c mapanare/self/mnc_main.c \
    -I runtime/native -o /tmp/mnc-stage3 -no-pie -rdynamic -lm -lpthread 2>/dev/null
ulimit -s unlimited && timeout 120 /tmp/mnc-stage3 mapanare/self/mnc_all.mn > /tmp/stage4.ll 2>/dev/null
cmp /tmp/stage3.ll /tmp/stage4.ll && echo "FIXED POINT OK" || echo "FIXED POINT BROKEN"

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

v3.8.0 reached:
- Compiler hardening: loop bounds 500/2000/5000, +30 method return types
- Substr semantics fix, 5 native tests added
- Dead PHI root cause identified (MIRType.kind garbage in Python-bootstrapped binary)
- 25/25 golden, 104 native assertions, 35/35 stdlib, fixed point OK

v3.8.1 added:
- Generic function monomorphization (both Python bootstrap and self-hosted)
- Generic struct monomorphization (Pair<A, B> → Pair__Int_Bool)
- Impl method dispatch (obj.method() → Type_method(obj))
- Trait bounds validation (fn max<T: Ord> checks T implements Ord)
- Self-hosted impl Trait for Type parsing + trait definition skip
- Self-hosted bare self parameter parsing
- 28/28 golden (+3 new: generics, impl, traits), fixed point OK

---

## Inherited State

| Component | Status |
|-----------|--------|
| Self-hosted compiler | 28/28 golden, fixed point |
| Seed binary | v3.8.1 |
| Stdlib compiled | 35/35 modules |
| Native tests | 104 assertions across 7 modules |
| CLI | `./mnc`, `./mnc test`, `./mnc build`, `./mnc run`, `./mnc version` |
| Generics | Functions + structs (inferred types only) |
| Impl dispatch | Inherent + trait impls |
| Trait bounds | Validated at call sites (builtin + user-defined) |

---

## CRITICAL: Python Emitter Enum-Field Bug

The Python emitter (`emit_llvm_mir.py`) has a bug accessing enum-typed
fields from structs. This is the #1 blocker for compiler evolution.

**What breaks:**
- Adding new variants to the `Definition` enum → breaks enum payload layout
- Adding functions to `lower_state.mn` that `match` on enum types → IR type mismatch
- `DefResult.defn` field access → `{i64, ptr}` stored as `ptr`
- Dead PHI: `dest.ty.kind` has garbage (pointer values as string length)

**What works (workarounds):**
- Accessor functions receiving enums by value as parameters
- `unwrap_or_default` for Option<String> (avoids match extraction)
- String encoding via `lambda_vars` (for metadata that would need StructDefData)
- `decode_ret_type(unwrap_or_default(find_lambda(s, key), ""))` pattern
- `parse_fn_def_as_data` (parallel fn parse returning FnDataResult, not DefResult)

**Test to catch regression:**
```bash
# If this produces Pair__Unknown_Unknown instead of Pair__Int_Bool, the enum layout is broken
./mapanare/self/mnc-stage1 /tmp/test_gen.mn 2>/dev/null | grep 'Pair__Int_Bool'
```

---

## What's Next (candidate features for continuation)

1. **Fix Python emitter enum-field bug** — Unblocks everything. Deep change to emit_llvm_mir.py type resolution.
2. **Generic type annotations** — `let p: Pair<Int, Bool> = ...`. Blocked by enum-field bug.
3. **Nested generics** — `List<Pair<Int, String>>`, `Option<Pair<Int, Bool>>`.
4. **Generic methods in impl blocks** — `impl<T> Stack<T> { fn push(self, val: T) }`.
5. **Dato v1.0** — Real DataFrame package. Stress tests everything.
6. **More test coverage** — Recursive generics, generic closures, turbofish on methods.
