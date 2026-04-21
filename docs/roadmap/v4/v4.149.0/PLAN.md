# Mapanare v4.149.0 — E5: ABI.1 struct return

> **Close the ABI.1 panel carry.** Mapanare currently returns every
> aggregate via sret (caller-allocated out-pointer), regardless of size.
> System V x86-64 and Win64 both specify that small aggregates (≤ 16
> bytes on SysV, ≤ 8 bytes on Win64) return in registers — Rust and
> Clang follow this rule; Mapanare does not. ABI.1 has been on the
> ledger since v4.125.0 as the residual gap on the `enum_match`
> 24-byte struct return. E5 is the biggest experiment in the arc
> (3–5 days) because ABI work requires cross-calling-convention
> testing and tight coordination between emitter and runtime.

**Status:** PLANNED
**Breaking:** No externally (public API unchanged); internal ABI
breakage is contained behind the LLVM boundary — every Mapanare-
compiled binary uses the new convention uniformly.
**Prerequisite:** v4.148.0 shipped (E4 recorded)
**Estimated work:** 3–5 days
**Theme:** E5 — ABI.1 struct return (System V + Win64 small-aggregate rule)

**Closes docket:** ABI.1 (panel carry from v4.136.0, re-confirmed at v4.143.0 panel)

---

## Why this release, why now

ABI.1 is the oldest open perf docket not yet addressed in the arc, and
the one most directly visible to anyone reading Mapanare IR and
comparing against Clang or rustc. Every function returning an enum
payload, a `Result<T, E>`, or a small tuple currently compiles to:

```llvm
define void @foo(ptr sret(%MyStruct) %0, i64 %n) { ... }
```

…when it should compile to:

```llvm
define { i64, i64 } @foo(i64 %n) { ... }
```

The sret path costs a caller-side stack allocation, a pointer-argument
register, and a store-through-pointer in the callee. The register-
return path costs zero stack, two return registers (rax + rdx on
SysV), and no pointer indirection. On hot functions like `Option<Int>`
getters and small-enum constructors, this is a 10–30 % wall difference
on benchmarks where return-ABI dominates.

Closing ABI.1 also clears the longest-standing perf carry-forward on
the ledger — the v4.125.0 benchmark refresh identified it as the
residual gap on `enum_match` 24-byte struct return, and the v4.136.0
panel flagged it as a MEDIUM item that the v4.143.0 panel
reclassified as LOW but did not close.

## Baseline (measure before touching code)

```bash
echo "4.149.0" > VERSION
make build-rt
python3 scripts/build_stage1.py

# Benchmarks most sensitive to return ABI
python3 benchmarks/cross_language/run_benchmarks.py \
  --only enum_match,struct_alloc,quicksort --runs 20 \
  --output benchmarks/cross_language/v4.149.0-baseline.json

python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.149.0-full-baseline.json

# Count sret functions in a representative IR
python3 -m mapanare emit-llvm mapanare/self/mnc_all.mn -O3 -o /tmp/mncall.ll
grep -c "sret" /tmp/mncall.ll
grep -c "sret" /tmp/sc.rs.ll  # Rust reference — expect near zero for small returns
```

Write `docs/roadmap/v4/v4.149.0/BASELINE.md` with:
- Target bench medians (`enum_match`, `struct_alloc`, `quicksort`)
- sret-instance count in canonical IR (Mapanare vs a Rust-compiled
  reference)
- Ratio to Rust on `enum_match` specifically (the ABI.1-origin
  workload)

## Hypothesis

Small aggregates (total size ≤ 16 bytes on SysV, ≤ 8 bytes on Win64)
should return in registers per the target ABI. Mapanare's unconditional
sret costs an extra stack frame allocation + pointer-through-store per
call. Switching to register-return for eligible aggregates closes
5–15 % wall on return-heavy benchmarks.

Concrete IR-level differences expected:

- **Function signature:** `void @foo(ptr sret(...))` → `{i64, i64} @foo()`
  or `i64 @foo()` or `double @foo()` depending on the aggregate shape.
- **Caller-side:** Replace `call void @foo(ptr %tmp)` + `load` with
  `call {i64, i64} @foo()` + `extractvalue`.
- **Callee-side:** Replace `store` into sret pointer with
  `insertvalue` + `ret {...}`.

## Phase 1 — IR diff vs Clang / Rust

Pick a canonical small-aggregate-returning function (e.g., a
`make_shape` variant or `Option<Int>::some`):

```bash
python3 -m mapanare emit-llvm benchmarks/system/enum_match.mn -O3 \
  -o /tmp/em.mn.ll
rustc -O --emit=llvm-ir <equivalent-rust.rs> -o /tmp/em.rs.ll

# Write a tiny C file that returns {i64, i64} and clang-compile for reference
cat > /tmp/abi_ref.c << 'EOF'
struct S { long a; long b; };
struct S make_s(long n) { struct S r = {n, n*2}; return r; }
EOF
clang -O3 -emit-llvm -S /tmp/abi_ref.c -o /tmp/abi_ref.ll
```

Write `docs/roadmap/v4/v4.149.0/IR_DIFF.md`:
- Mapanare `make_shape` signature + call site
- Clang `make_s` signature + call site (canonical SysV reference)
- Rust equivalent signature + call site
- Annotated table of the 3 styles

## Phase 2 — Form hypothesis

Write `docs/roadmap/v4/v4.149.0/HYPOTHESIS.md`:

```markdown
# E5 Hypothesis

**Claim:** Replacing sret with register-return for aggregates whose
total size ≤ `ABI_SRET_THRESHOLD` (16 bytes SysV, 8 bytes Win64,
16 bytes AArch64, per target) closes 5–15 % wall on return-heavy
benches and eliminates ≥ 60 % of sret uses in canonical IR.

## Eligibility rules (per System V x86-64)

**Use register return when:**
- Aggregate size ≤ 16 bytes.
- Aggregate contains at most two 8-byte "classes" per SysV §3.2.3
  (integer, SSE, etc.).
- No complex types (not relevant for Mapanare since all fields are
  integer or pointer at this layer).

**Use sret when:**
- Aggregate size > 16 bytes.
- Aggregate contains a padding hole that would misclassify under SysV.
- Target is Win64 and size > 8 bytes.

**Target matrix:** Mapanare ships SysV (Linux/macOS x86-64), Win64
(Windows x86-64), AArch64 (Linux/macOS/Android). Each has its own
threshold. E5 covers all three.
```

## Phase 3 — Patch

Primary target: `mapanare/emit_llvm_text.py`. Structure:

1. **ABI helper module.** Add `mapanare/abi.py` (new, ~150 LOC):
   ```python
   def classify_return(struct_ty: MIRType, target: Target) -> ReturnABI:
       """Return REGISTER(ty) or SRET for a struct return on the given target."""
   ```
   Implement SysV, Win64, AArch64 classifications per ABI docs.

2. **Emitter integration.** In the function-header emission, call
   `classify_return`. For REGISTER, emit the register signature and
   insertvalue/ret-aggregate chain. For SRET, keep current path.

3. **Call-site emission.** At every call to an aggregate-returning
   function, check the function's classified ABI and emit the matching
   call shape (register extract vs sret load).

4. **MIR / lower:** No changes expected. MIR already carries struct
   returns abstractly; the ABI is purely an emitter concern.

5. **Regression tests.** `tests/llvm/test_abi_struct_return.py`:
   ```python
   class TestSysVClassification:
       def test_two_int64_returns_in_registers(self): ...
       def test_eight_byte_struct_returns_in_register(self): ...
       def test_twenty_four_byte_struct_uses_sret(self): ...
       def test_option_int_returns_in_registers(self): ...
       def test_result_ok_err_returns_in_registers(self): ...

   class TestWin64Classification:
       def test_two_int64_uses_sret_on_win64(self): ...
   ```

Estimated diff:
- `mapanare/abi.py` (new): ~150 LOC
- `mapanare/emit_llvm_text.py`: ~80–120 LOC (header + callsite paths)
- `tests/llvm/test_abi_struct_return.py` (new): ~100 LOC
- `runtime/native/mapanare_runtime.c`: 0 LOC expected (runtime doesn't
  care about the convention — the LLVM boundary handles it).

## Phase 4 — Re-measure

```bash
make build-rt
python3 scripts/build_stage1.py

python3 benchmarks/cross_language/run_benchmarks.py \
  --only enum_match,struct_alloc,quicksort --runs 20 \
  --output benchmarks/cross_language/v4.149.0-patched.json
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.149.0-full-patched.json

# Confirm sret count dropped
python3 -m mapanare emit-llvm mapanare/self/mnc_all.mn -O3 -o /tmp/mncall.patched.ll
grep -c "sret" /tmp/mncall.patched.ll

# Cross-ABI sanity — need to compile under Win64 target too
python3 -m mapanare emit-llvm --target x86_64-pc-windows-msvc benchmarks/system/enum_match.mn \
  -O3 -o /tmp/em.win64.ll

# Sanitizer sweep
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh 2>&1 | tail -5
bash scripts/run_asan_goldens.sh 2>&1 | tail -5
```

**5 % rule:**
- At least one of `enum_match`, `struct_alloc`, `quicksort` must
  improve ≥ 5 %.
- No non-target bench regresses > 2 %.
- Zero new valgrind / ASan findings.
- `sret` count in canonical IR drops ≥ 60 % (diagnostic target).

## Phase 5 — Record

Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

```
| E5 | ABI.1: register return for small aggregates | <win/dead-end> | enum_match <d>%, struct_alloc <d>%, sret count -<N>% | mapanare/abi.py (new), emit_llvm_text.py | v4.149.0 |
```

Write `RESULTS.md` and `SESSION_REPORT.md` (long-form ~350 LOC — cover
the System V classification algorithm, Win64 divergence, AArch64
notes, and any surprises in testing).

Mark ABI.1 CLOSED in `.reviews/CARRY_FORWARD.md`.

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `BASELINE.md` with pre-patch target benches + sret count | yes |
| 2 | `IR_DIFF.md` comparing Mapanare / Clang / Rust return shapes | yes |
| 3 | `HYPOTHESIS.md` with per-ABI classification rules | yes |
| 4 | `mapanare/abi.py` classification module (new) | yes |
| 5 | Emitter header + callsite paths wired to classifier | yes |
| 6 | `tests/llvm/test_abi_struct_return.py` ≥ 8 tests, all pass | yes |
| 7 | ≥ 1 target bench ≥ 5 % improvement | yes |
| 8 | No other bench regresses > 2 % | yes |
| 9 | sret count in canonical IR drops ≥ 60 % | yes |
| 10 | Zero new valgrind ERRORS | yes |
| 11 | Zero new ASan ASAN_ERROR | yes |
| 12 | Cross-ABI IR spot-check (SysV + Win64 + AArch64) passes | yes |
| 13 | ABI.1 marked CLOSED in `.reviews/CARRY_FORWARD.md` | yes |
| 14 | `PERF_EXPERIMENTS.md` entry added | yes |
| 15 | Non-bootstrap pytest: ≥ 5,186 / 0 (+8 ABI tests) | yes |
| 16 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 17 | Native goldens: 54 / 66 | yes |
| 18 | Fixed-point: within `DIFF_THRESHOLD=100` | yes |
| 19 | All 8 CI gates green | yes |
| 20 | SESSION_REPORT.md written (long-form, ABI algorithm documented) | yes |
| 21 | CHANGELOG + CLAUDE.md + ROADMAP.md updated | yes |
| 22 | Tag `v4.149.0` pushed to origin | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| SysV classification misreads a padded aggregate (e.g., `{i8, i64}` → expected sret, emitted register) | medium | high | Implement §3.2.3 literally; add test cases for known padded shapes; run against Clang-compiled reference C structs |
| Win64 rule divergence missed — benchmark passes on Linux, fails on Windows CI | medium | medium | Emit Win64 IR as part of test suite; run wat2wasm or objdump check on the header |
| AArch64 ABI differs subtly (HFA/HVA rules for SIMD types); breaks mobile target | medium | medium | Mobile test corpus is limited; run `aarch64-linux-android` codegen for a handful of returning functions and spot-check |
| Call site and callee diverge (emitter emits sret at call, register at def, or vice versa) | medium | CRITICAL | Unit test: compile + llvm-as both sides; any mismatch is caught at LLVM verify. Add invariant: classifier called in both paths with identical inputs |
| ABI.1 benchmark delta is already absorbed by LLVM's own sret-to-register peephole at -O3 — no observable win | medium | low | That's a legitimate result; document it; still ship the classifier for Win32 / lower -O levels / cleaner IR |

## What this release does NOT do

- Does not change the runtime `MnString` / `MnList` / `MnMap` struct
  layouts. Internal runtime uses sret throughout; only the Mapanare →
  Mapanare user-function boundary changes.
- Does not address argument-passing ABI. Mapanare's current arg-passing
  happens to already align with SysV for small types; if ABI.2 opens
  on that later, it's a separate release.
- Does not mirror into `mapanare/self/emit_llvm.mn`. Self-hosted
  parity is a LOW follow-up docket.
- Does not touch FFI / C interop. The C calling convention Mapanare
  exposes for FFI is handled in `ffi.py` / wasm bindings; both already
  use target-ABI-compliant emission.
- Does not open a new benchmark; the existing corpus is the measurement.

## Carry-forward after v4.149.0

- **ABI.1 CLOSED.** The ledger's last MEDIUM/LOW panel-carry from the
  v4.136.0 era is off.
- New LOW dockets opened: Cb.15-abi-self-hosted (self-hosted parity for
  `mapanare/self/emit_llvm.mn::emit_fn_header`), scheduled for v4.152.0
  or v4.153.0.
- If E5 was a win on SysV but no-op on Win64 (LLVM peephole absorbs
  it), document the per-target delta in RESULTS.md; ABI.1 still closes
  because the classifier is correct even when the win is small.
- All bench numbers republished at v4.153.0 pre-panel refresh.
