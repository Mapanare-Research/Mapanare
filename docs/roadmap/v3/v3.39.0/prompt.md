# v3.39.0 — "Caricare" — Hardening & v4.0.0 Gate

> Valgrind-clean compilation and programs, memory profiling, Culebra CI,
> documentation. After this, v4.0.0 is a release tag — no new code.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.39.0/PLAN.md`.
> Use Culebra and valgrind for everything. Run `/golden` after every change.

---

## Context

v3.38.0 proved correctness (fixed point, 33/33 golden). v3.39.0 proves
ROBUSTNESS: no memory errors, no leaks, proper CI gates, documentation.

**Current version:** 3.38.0
**Target version:** 3.39.0

---

## What Needs Doing

### Phase 1: Valgrind-clean compiler [do first]

Run valgrind on every golden test compilation. Fix all errors.
```bash
for mn in tests/golden/*.mn; do
    valgrind --error-exitcode=1 --max-stackframe=67108864 \
        ./mapanare/self/mnc-stage1 "$mn" > /dev/null 2>&1 \
        && echo "PASS $(basename $mn)" || echo "FAIL $(basename $mn)"
done
```

### Phase 2: Valgrind-clean compiled programs [do second]

Build each golden test program and run it under valgrind:
```bash
for mn in tests/golden/*.mn; do
    ./mapanare/self/mnc-stage1 build "$mn" -o /tmp/golden_prog 2>/dev/null
    valgrind /tmp/golden_prog 2>&1 | grep -c "ERROR SUMMARY: 0"
done
```

### Phase 3: Memory profiling + optimization [MEDIUM]

```bash
/usr/bin/time -v ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /dev/null
```

Target <512MB. If over, add string interning for common IR patterns.

### Phase 4: Culebra CI + documentation [LOW]

1. Add Culebra regression gates to CI
2. Update CLAUDE.md, SPEC.md, ROADMAP.md
3. Complete v4.0.0 readiness checklist

---

## Verification Checklist

```bash
# 1. Valgrind-clean compiler
python3 scripts/ir_doctor.py valgrind tests/golden/01_hello.mn

# 2. Fixed point
bash scripts/verify_fixed_point.sh

# 3. All golden
/golden   # 33/33

# 4. Memory
/usr/bin/time -v ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /dev/null

# 5. Culebra
culebra scan mapanare/self/main.ll --severity critical
culebra health mapanare/self/main.ll

# 6. Benchmarks
bash tests/bench/bench_compile.sh --gate
```

---

## Version Bump

1. Run `/bump-version` to 3.39.0
2. CHANGELOG.md:
   - **Fixed:** Valgrind-clean on all golden test compilations and programs
   - **Improved:** Peak memory <512MB during self-compilation
   - **Added:** Culebra regression gates in CI
   - **Changed:** Documentation updated for v4.0.0 readiness
3. Commit: `v3.39.0: "Caricare" — valgrind-clean, Culebra CI, v4.0.0 ready`
