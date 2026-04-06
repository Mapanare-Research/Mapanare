# Mapanare v3.9.0 — Plan + Continuation Prompt

> Read CLAUDE.md for project context.
> Track progress in this file.
> Commit at each milestone. Make decisions autonomously.

---

## Context

v3.8.1 delivered:
- Generic function monomorphization (`fn identity<T>` → `identity__Int`)
- Generic struct monomorphization (`struct Pair<A, B>` → `Pair__Int_Bool`)
- Impl method dispatch (`obj.method()` → `Type_method(obj)`)
- Trait bounds validation (`fn max<T: Ord>` checks at call site)
- Self-hosted `impl Trait for Type` parsing + trait skip
- Compiler hardening (loop bounds, method return types, substr fix)
- 28/28 golden, 104 native assertions, 35/35 stdlib, fixed point OK

---

## Inherited State

| Component | Status |
|-----------|--------|
| Self-hosted compiler | 28/28 golden, fixed point (stage3 == stage4) |
| Seed binary | v3.8.1, 32MB thread |
| Stdlib compiled | 35/35 modules |
| Native tests | 104 assertions across 7 modules |
| Generics | Functions + structs (inferred types only) |
| Impl dispatch | Working (inherent + trait) |
| Trait bounds | Validated at call sites |
| Definition counts | ~760 fn, ~72 struct, ~12 enum in mnc_all.mn |

---

## Known Blockers

### Python Emitter Enum-Field Bug (CRITICAL)

The Python emitter (`emit_llvm_mir.py`) has a bug accessing enum-typed
fields from structs. When extracting a field of enum type (e.g.,
`DefResult.defn` where Definition is an enum), the alloca is created with
`ptr` type instead of `{i64, ptr}`.

**Symptoms:**
1. Cannot add new variants to the Definition enum (breaks payload layout)
2. Cannot add functions to `lower_state.mn` that match on enum types
3. 11 dead PHI lines in stage2/stage3 diff (MIRType.kind has garbage data)
4. Generic type annotations (`let p: Pair<Int, Bool>`) blocked

**Workarounds discovered:**
- Use accessor functions that receive enums by value as parameters
- Use `unwrap_or_default` for Option<String> extraction (avoids match)
- Encode metadata as strings in `lambda_vars` (not always sufficient)
- The `decode_ret_type` and `push_if_fn_def` patterns work

**Root cause location:** `emit_llvm_mir.py` lines 1973-1993 (PHI alloca
handling) and the struct field extraction code that resolves MIR types
for enum-typed struct fields.

---

## Candidate Features (pick what makes sense)

### Option A: Fix the Python Emitter Enum-Field Bug
- Unblocks: generic type annotations, new AST variants, dead PHI gap closure
- Risk: deep change to emit_llvm_mir.py's type resolution
- Reward: removes the #1 blocker for compiler evolution

### Option B: Generic Type Annotations
- `let p: Pair<Int, Bool> = ...` resolves to mangled struct name
- Requires: either fixing the enum-field bug OR a creative workaround
- Currently: only inferred types work (`let p = new Pair { ... }`)

### Option C: Dato v1.0
- Real DataFrame package in .mn — stress tests generics, impl, and compiler
- Tables, aggregations, joins, CSV/JSON I/O
- Repo: github.com/Mapanare-Research/dato

### Option D: Nested Generics
- `List<Pair<Int, String>>`, `Option<Pair<Int, Bool>>`
- Requires monomorphization to handle recursive generic type resolution

### Option E: Generic Methods in Impl Blocks
- `impl<T> Stack<T> { fn push(self, val: T) { ... } }`
- Combines generics with impl dispatch

### Option F: More Test Coverage
- Edge cases: recursive generics, generic closures, turbofish on methods
- Native test module for generics + impl dispatch
- Stress tests with large generic instantiation counts

---

## Verification Commands

```bash
# Rebuild
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# Golden tests (must be 28/28)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Native tests (must be 7/7, 104 assertions)
for f in tests/native/test_*.mn; do
    ./mapanare/self/mnc-stage1 test "$f" 2>/dev/null | tail -1
done

# Stdlib (must be 35/35)
for f in $(find stdlib -name '*.mn' -not -path '*/wasm/*' -not -path '*/gpu/*'); do
    ./mapanare/self/mnc-stage1 "$f" > /tmp/t.ll 2>/dev/null
    sed -n '/^; ModuleID/,$p' /tmp/t.ll > /tmp/t_clean.ll
    llvm-as /tmp/t_clean.ll -o /dev/null 2>/dev/null && echo "OK $(basename $f)" || echo "FAIL $(basename $f)"
done

# Fixed point
timeout 120 ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll 2>/dev/null
clang -c -O2 /tmp/stage2.ll -o /tmp/stage2.o 2>/dev/null
gcc /tmp/stage2.o runtime/native/mapanare_core.c mapanare/self/mnc_main.c \
    -I runtime/native -o /tmp/mnc-stage2 -no-pie -rdynamic -lm -lpthread 2>/dev/null
ulimit -s unlimited && timeout 120 /tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.ll 2>/dev/null
clang -c -O2 /tmp/stage3.ll -o /tmp/stage3.o 2>/dev/null
gcc /tmp/stage3.o runtime/native/mapanare_core.c mapanare/self/mnc_main.c \
    -I runtime/native -o /tmp/mnc-stage3 -no-pie -rdynamic -lm -lpthread 2>/dev/null
ulimit -s unlimited && timeout 120 /tmp/mnc-stage3 mapanare/self/mnc_all.mn > /tmp/stage4.ll 2>/dev/null
cmp /tmp/stage3.ll /tmp/stage4.ll && echo "FIXED POINT OK"

# Generic struct smoke test (must produce Pair__Int_Bool, NOT Pair__Unknown_Unknown)
cat > /tmp/test_gen.mn << 'EOF'
struct Pair<A, B> { first: A, second: B }
fn main() { let p = new Pair { first: 42, second: true }; print(p.first) }
EOF
./mapanare/self/mnc-stage1 /tmp/test_gen.mn > /tmp/gen.ll 2>/dev/null
grep 'Pair__Int_Bool' /tmp/gen.ll && echo "GENERICS OK" || echo "GENERICS BROKEN"

# Full validation
black --check --target-version py311 .
ruff check .
python3 -m pytest tests/ -q --tb=no
```

---

## MANDATORY: Validate locally before commit

```bash
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
for f in tests/native/test_*.mn; do ./mapanare/self/mnc-stage1 test "$f" 2>/dev/null | tail -1; done
```
