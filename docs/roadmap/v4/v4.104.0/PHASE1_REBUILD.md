# v4.104.0 Phase 1 — Clean rebuild of mnc-stage1 at -O2

**Date:** 2026-04-13
**Optimization level used:** `-O2` (default in `scripts/build_stage1.py`)

## What was done

1. Removed stale build artifacts: `mapanare/self/mnc-stage1`, `mapanare/self/*.o`, `mapanare/self/main.ll`, `mapanare/self/lower.ll`.
2. Ran `python3 scripts/build_stage1.py` (full pipeline: IR gen → -O2 clang → runtime `.c` at -O2 → link).
3. Verified binary exists as an ELF and smoke-tested against a trivial `.mn`.

## Measurements

| Metric | Value |
|---|---|
| Build time | 1 min 21 s (wall) |
| IR lines (`main.ll`) | 857,645 |
| Compiled object (`main.o`) | 3,906,240 bytes |
| Linked binary (unstripped) | 3,973,848 bytes |
| Linked binary (stripped) | 3,501,200 bytes (-12%) |
| Build warnings | 1 (see below) |

**Warnings during build:**
- `/usr/bin/ld: warning: -z stacksize=67108864 ignored` — pre-existing GNU ld quirk on Linux; the flag is harmless. Not caused by any Phase A fix.

## Smoke test

Trivial program `/tmp/smoke.mn`:
```mapanare
fn main() -> Int {
    println("hello, phase B")
    return 0
}
```

- `./mapanare/self/mnc-stage1 /tmp/smoke.mn` → emitted 134 lines of LLVM IR
- `llvm-as /tmp/smoke.ll -o /tmp/smoke.bc` → **OK** (no IR errors)
- `clang /tmp/smoke.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o /tmp/smoke`
  - 1 warning: module target triple override (cosmetic)
- `./tmp/smoke` → prints `hello, phase B`, exit 0

## IR self-validation

Direct `llvm-as mapanare/self/main.ll` succeeds: 12.5 MB bitcode, zero errors.
The compiler's own IR is clean under the -O2 clang frontend.

## Exit criterion (Exit #1)

- [x] mnc-stage1 rebuilt with `-O2`, binary is clean (smoke test → correct output).
