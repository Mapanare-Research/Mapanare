# Mapanare v3.38.0 — "Turpial" (Fixed-Point Self-Compilation)

> Prove the compiler is correct: stage2 compiles itself to stage3,
> stage3 == stage2 (fixed point). Fix the 4 remaining generic/impl
> type errors. Update the seed binary. The compiler compiles itself
> with zero Python, zero hacks.

**Status:** PLANNED
**Estimated scope:** Medium (1-2 sessions)
**Breaking:** No
**Prerequisite:** v3.37.0 (self-compilation must work)

---

## Motivation

v3.37.0 restored self-compilation: mnc-stage1 can compile mnc_all.mn
without crashing. But we haven't proven CORRECTNESS: does the compiled
compiler produce the same output as the original? That's the fixed-point
test. Also, 4/33 golden tests still fail due to generic/impl type
inference bugs in the self-hosted lowerer.

---

## Items

### 1. Two-Stage Fixed Point [CRITICAL]

```bash
# Stage 1: seed compiles source → stage1 binary (already works)
# Stage 2: stage1 compiles source → stage2.ll
./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll

# Build stage2 binary
clang -c -O2 /tmp/stage2.ll -o /tmp/stage2.o
gcc /tmp/stage2.o mapanare/self/mapanare_core.o mapanare/self/mnc_main.o \
    -o /tmp/mnc-stage2 -no-pie -rdynamic -lm -lpthread

# Stage 3: stage2 compiles source → stage3.ll
/tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.ll

# Fixed point: stage3 must equal stage2
diff /tmp/stage2.ll /tmp/stage3.ll && echo "FIXED POINT" || echo "DIVERGENT"
```

If divergent, use Culebra to identify differences:
```bash
culebra diff /tmp/stage2.ll /tmp/stage3.ll
culebra bisect /tmp/stage2.ll /tmp/stage3.ll
```

### 2. Fix 4 Generic/Impl Type Errors [HIGH]

The failing golden tests:
- `26_generics.mn` — `%b_val8` is `i1` but expected `i64` (Bool→Int coercion missing)
- `27_impl.mn` — `%t4` is `i64` but expected `{ptr, i64}` (impl method returns String, lowered as Int)
- `29_generic_impl.mn` — same as 27_impl
- `31_generic_multi.mn` — same pattern

Root cause: the self-hosted lowerer (`lower.mn`) doesn't correctly resolve
return types for generic/impl method calls. The Python lowerer handles
this via `resolve_generic_type()` but the self-hosted version is incomplete.

**Diagnosis:**
```bash
culebra explain mapanare/self/main.ll return-type-divergence
python3 scripts/ir_doctor.py diff tests/golden/26_generics.mn
python3 scripts/ir_doctor.py diff tests/golden/27_impl.mn
```

Compare the Python bootstrap IR vs mnc-stage1 IR for these tests to find
the exact lowering difference.

### 3. Update Seed Binary [HIGH]

After fixed-point is proven, the stage2 binary becomes the new seed:
```bash
cp /tmp/mnc-stage2 bootstrap/seed/linux-x86_64/mnc
sha256sum bootstrap/seed/linux-x86_64/mnc > bootstrap/seed/linux-x86_64/mnc.sha256
```

### 4. Enable CI Fixed-Point Check [MEDIUM]

Add to `.github/workflows/ci.yml`:
```yaml
- name: Fixed-point verification
  run: bash scripts/verify_fixed_point.sh
```

This verifies that every push maintains the fixed-point property.

### 5. Culebra Regression Gate [MEDIUM]

```bash
culebra baseline save mapanare/self/main.ll
culebra lint-template mapanare/self/main.ll return-type-divergence --reject
culebra lint-template mapanare/self/main.ll option-type-pun-zeroinit --reject
```

Add as CI step: fail if these templates fire (regression).

---

## Verification

- [ ] `scripts/verify_fixed_point.sh` — stage3 == stage2
- [ ] 33/33 golden tests pass (all 4 generic errors fixed)
- [ ] Seed binary updated and checksum verified
- [ ] CI fixed-point check passes
- [ ] Culebra regression gates pass
- [ ] `build_from_seed.sh --verify` — end-to-end no-Python build

---

## Commit

```
v3.38.0: "Turpial" — fixed-point self-compilation, 33/33 golden, seed updated
```
