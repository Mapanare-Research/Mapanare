# v3.38.0 — "Turpial" — Fixed-Point Self-Compilation

> Prove correctness: stage2 compiles itself to stage3, stage3 == stage2.
> Fix the 4 generic/impl type errors. Update the seed. Zero Python, zero hacks.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.38.0/PLAN.md`.
> Run `/golden` after every change. Use Culebra for regression detection.

---

## Context

v3.37.0 fixed the memory safety bugs — mnc compiles mnc_all.mn without
crashing. But we haven't proven the output is CORRECT. The fixed-point
test (stage3 == stage2) is the ultimate correctness check.

Also, 4/33 golden tests fail because the self-hosted lowerer doesn't
handle generic/impl method return types correctly.

**Current version:** 3.37.0
**Target version:** 3.38.0

---

## What Needs Doing

### Phase 1: Prove fixed point [do first]

```bash
bash scripts/verify_fixed_point.sh
```

If it fails, use Culebra to find divergent functions:
```bash
culebra diff /tmp/stage2.ll /tmp/stage3.ll
culebra bisect /tmp/stage2.ll /tmp/stage3.ll --top 10
```

Fix divergences one at a time. Common causes:
- Different register numbering (cosmetic — normalize before comparing)
- Missing functions in stage2 (lowering gap)
- Wrong types in stage2 (type inference bug)

### Phase 2: Fix generic/impl type errors [do second]

**Files:** `mapanare/self/lower.mn`, `mapanare/self/lower_state.mn`

Diagnosis approach:
```bash
# Compare Python bootstrap IR vs mnc-stage1 IR
python3 scripts/ir_doctor.py diff tests/golden/26_generics.mn
python3 scripts/ir_doctor.py diff tests/golden/27_impl.mn
```

The diffs will show exactly which function has the wrong return type.
Fix the type resolution in the lowerer.

### Phase 3: Update seed + CI [do last]

1. Build final stage2 binary
2. Copy to `bootstrap/seed/linux-x86_64/mnc`
3. Generate checksum
4. Add fixed-point CI step
5. Add Culebra regression gates

---

## Verification Checklist

```bash
# 1. Fixed point
bash scripts/verify_fixed_point.sh

# 2. All golden tests
/golden   # expect 33/33

# 3. No-Python build
bash scripts/build_from_seed.sh --verify

# 4. Culebra clean
culebra triage mapanare/self/main.ll --brief
culebra baseline diff mapanare/self/main.ll

# 5. Benchmarks
bash tests/bench/bench_compile.sh --gate
```

---

## Version Bump

1. Run `/bump-version` to 3.38.0
2. CHANGELOG.md:
   - **Fixed:** Generic/impl method return type resolution (33/33 golden)
   - **Added:** Fixed-point self-compilation verified (stage3 == stage2)
   - **Changed:** Seed binary updated to v3.38.0
   - **Added:** CI fixed-point verification step
   - **Added:** Culebra regression gates in CI
3. Commit: `v3.38.0: "Turpial" — fixed-point self-compilation, 33/33 golden, seed updated`
