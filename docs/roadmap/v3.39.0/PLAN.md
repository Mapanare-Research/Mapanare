# Mapanare v3.39.0 — "Caricare" (Hardening & v4.0.0 Gate)

> Final hardening before v4.0.0. Proper drop glue for user programs,
> memory profiling, valgrind-clean compilation, Culebra CI integration,
> documentation. After this version, v4.0.0 is purely a release tag.

**Status:** DONE
**Estimated scope:** Medium (1-2 sessions)
**Breaking:** No
**Prerequisite:** v3.38.0 (fixed-point proven, 33/33 golden)

---

## Motivation

v3.37.0 fixed memory safety. v3.38.0 proved self-compilation correctness.
v3.39.0 hardens the compiler for production:

- Drop glue currently works for the compiler itself but may still leak
  in user programs with unusual patterns. Fix remaining edge cases.
- Valgrind should show ZERO errors for both the compiler and compiled programs.
- Culebra should be integrated into CI for ongoing regression detection.
- Memory usage during self-compilation should be profiled and optimized.
- Documentation should reflect the current architecture accurately.

---

## Items

### 1. Valgrind-Clean Compilation [HIGH]

**Goal:** `valgrind ./mnc-stage1 tests/golden/*.mn` — 0 errors on ALL 33 tests.

Currently 29/33 compile, but valgrind may still report warnings (conditional
jumps on uninitialized values, etc.). Fix all valgrind issues.

```bash
for mn in tests/golden/*.mn; do
    echo "--- $mn ---"
    valgrind --error-exitcode=1 --max-stackframe=67108864 \
        ./mapanare/self/mnc-stage1 "$mn" > /dev/null 2>&1 \
        && echo "PASS" || echo "FAIL"
done
```

### 2. Valgrind-Clean Compiled Programs [HIGH]

Compiled user programs should also be valgrind-clean:
```bash
./mapanare/self/mnc-stage1 run tests/golden/01_hello.mn  # runs the program
# Check: valgrind the COMPILED program, not the compiler
./mapanare/self/mnc-stage1 build tests/golden/01_hello.mn -o /tmp/hello
valgrind /tmp/hello
```

Fix memory leaks in compiled programs:
- String cleanup on program exit
- List cleanup on program exit
- Arena reset before exit

### 3. Drop Glue Edge Cases [MEDIUM]

Test and fix these patterns in user programs:
- Returning struct with nested struct containing list
- Passing list to function by value, then pushing to it
- Early return (multiple return paths with different list lifetimes)
- Loop that creates and discards lists each iteration
- Recursive functions that accumulate list data

Create golden tests for each pattern.

### 4. Memory Profiling [MEDIUM]

Profile memory usage during self-compilation:
```bash
/usr/bin/time -v ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /dev/null
# Maximum resident set size
```

Target: <512MB peak during self-compilation.

If too high, add arena reuse between modules and string interning for
common IR patterns.

### 5. Culebra CI Integration [MEDIUM]

Add Culebra to CI as a regression gate:

```yaml
# In .github/workflows/ci.yml
- name: Culebra health check
  run: |
    culebra scan mapanare/self/main.ll --severity critical --format json > /tmp/culebra.json
    culebra verify mapanare/self/main.ll return-type-divergence
    culebra verify mapanare/self/main.ll option-type-pun-zeroinit
```

Fail CI if any critical finding appears or a previously-fixed issue regresses.

### 6. Documentation Update [LOW]

Update:
- `CLAUDE.md` — reflect current architecture, remove outdated caveats
- `docs/SPEC.md` — memory model section (COW lists, drop glue semantics)
- `docs/roadmap/ROADMAP.md` — mark v3.37-v3.39 complete, v4.0.0 as next

### 7. v4.0.0 Readiness Checklist [LOW]

Before tagging v4.0.0, ALL of these must be true:

- [ ] 33/33 golden tests pass
- [ ] Fixed-point verified (stage3 == stage2)
- [ ] Valgrind-clean on all golden tests (compiler + compiled programs)
- [ ] No critical Culebra findings
- [ ] Memory usage <512MB during self-compilation
- [ ] `build_from_seed.sh --verify` passes (zero-Python bootstrap)
- [ ] All CI jobs green (including Culebra, valgrind, benchmarks)
- [ ] Documentation up to date
- [ ] Seed binary matches latest stage2

---

## Verification

- [ ] All 33/33 golden tests pass
- [ ] Valgrind-clean: 0 errors on all 33 golden test compilations
- [ ] Valgrind-clean: 0 errors on compiled hello program
- [ ] Peak memory <512MB during self-compilation
- [ ] Culebra CI gates pass
- [ ] Fixed-point still holds
- [ ] All benchmarks pass
- [ ] v4.0.0 readiness checklist complete

---

## Commit

```
v3.39.0: "Caricare" — valgrind-clean, memory profiling, v4.0.0 ready
```
