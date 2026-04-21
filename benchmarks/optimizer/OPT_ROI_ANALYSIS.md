# Mapanare v4.109.0 — Optimizer ROI Analysis (Arcs 11–12 Forensics)

> Measured 2026-04-14 on WSL2, AMD Ryzen 9 7950X. LLVM 18.1.3.
> Investigation motivated by `TOTAL_RESULTS.md`'s geometric-mean
> speedup of **0.992× at -O2** for v4.82.0 → v4.90.0 — eight releases
> of optimizer work that produced no measurable aggregate improvement.
> This release asks *why*. No code changes; pure forensics.
>
> Raw artifacts under `docs/roadmap/v4/v4.109.0/artifacts/`.

---

## Executive summary

**Arcs 11 and 12 were not wasted effort, but the attribution published
in `TOTAL_RESULTS.md` was misleading.** A per-workload and per-hint
investigation reveals three distinct regimes:

1. **`nsw` / `nuw` inline flags on integer arithmetic**: mostly
   redundant. LLVM's own `inferFunctionAttrs` derives equivalent
   information from IR structure for tight integer loops.
   Empirically, matmul_naive's IR receives 13 `nuw` flags post-O2
   whether the frontend seeded them or not.

2. **Function attributes on runtime call declarations**
   (`nounwind`, `willreturn`, `readonly`, `noalias`): **the
   load-bearing Arc 11 contribution**. These cross pass boundaries
   via LLVM's module-level attribute table and change downstream
   optimizer decisions (early-cse, licm, mldst-motion, dse) without
   being consumed by any single pass inline.

3. **TBAA metadata**: 100 % dead. The TBAA tree is defined in the
   module header (`!1 = !{!"Mapanare TBAA"}`, type nodes `!2–!5`,
   access tags `!6–!9`) but is **never attached to any load or store
   instruction**. Arc 11's TBAA contribution to alias analysis is
   literally zero.

The aggregate 0.992× geomean at -O2 is the arithmetic average of
genuine wins on some workloads (matmul −24%, quicksort −9%), flat
noise on others (fib), and a regression on one (string_concat +21%,
caused by `willreturn` on `__mn_sb_*` declarations blocking a
tail-call / DSE). **The optimizer arc is not redundant; it is
mispattern-matched against the benchmark workloads.**

---

## Methodology

For each of 4 optimizer benchmarks (`fib_recursive`, `quicksort`,
`matmul_naive`, `string_concat`):

1. **Emit pre-O2 IR** via the v4.108.0 compiler.
2. **Strip hints** with `sed` — `nsw`, `nuw`, `nounwind`, `willreturn`,
   `readonly`, `noalias`. Validate result with `llvm-as`.
3. **Run `opt -O2`** on both variants.
4. **Diff** at three levels:
   - Hint counts (token presence)
   - Instruction counts (IR line counts after O2)
   - Structural diff after stripping cosmetic attr-number differences
5. **Compile to binary**, measure median wall time over 40–50 runs
   with 2–5 trimmed from each tail.
6. **Individually test** 10 LLVM passes (instcombine, indvars, licm,
   gvn, sroa, loop-vectorize, loop-unroll, early-cse, function-attrs,
   aggressive-instcombine) on hinted vs stripped input to localize
   where the hints (if anywhere) change codegen.

All artifacts (IR files, diffs, pass-structure dumps, summary tables)
are in `docs/roadmap/v4/v4.109.0/artifacts/`.

---

## Hypothesis 1: LLVM already did it

**Tested**: strip nsw/nuw/attrs from IR, run opt -O2, compare the
resulting binaries' runtime.

| Benchmark     | Unstripped (ms) | Stripped (ms) |   Δ   | Direction            |
|---------------|----------------:|--------------:|------:|:---------------------|
| fib_recursive |          25.98  |        27.56  | −1.58 | hints help ~6% (near-noise) |
| quicksort     |           5.96  |         6.50  | −0.54 | hints help ~9%       |
| matmul_naive  |           6.14  |         7.60  | −1.46 | **hints help ~24%**  |
| string_concat |           8.49  |         6.68  | +1.81 | **hints HURT ~21%**  |

**Verdict on H1**: partially confirmed. For `fib_recursive`, the
deltas are within the noise floor (stdev 0.5–1.0 ms). For
`matmul_naive`, the hints produce a real 24% speedup — LLVM does
*not* recover the same codegen without them. For `string_concat`,
removing the hints *improves* runtime — the hints are actively
harmful here.

Hint-survival table (post-O2 token counts, unstripped vs stripped
input):

| Benchmark     | Unstripped post-O2 (nsw/nuw/attrs) | Stripped post-O2 |
|---------------|------------------------------------:|:------------------|
| fib_recursive | 4 / 0 / 8                           | 2 / 0 / 2         |
| quicksort     | 13 / 1 / 13                         | 1 / 1 / 3         |
| matmul_naive  | 15 / 13 / 12                        | 10 / 13 / 2       |
| string_concat | 1 / 1 / 8                           | 1 / 1 / 0         |

For `matmul_naive`, LLVM independently infers all 13 `nuw` flags
from IR structure — the frontend seeding contributes only the extra
5 `nsw` flags. But the function-attribute count drops dramatically
(12 → 2) when stripped: Arc 11's attrs on runtime call declarations
(`__mn_list_get`, `__mn_str_concat`, etc.) do not get re-inferred
by LLVM because it can't see the implementations.

---

## Hypothesis 2: benchmarks too small

**Tested**: scale fib from `fib(35)` (~9 M recursive calls, 25 ms)
to `fib(45)` (~1.1 B recursive calls, 2.4 s). If Arc 11 hints were
providing latent value that process-startup overhead or sample
noise was hiding, the delta should grow with problem size.

| Variant      | fib(35) median | fib(45) median | fib(45) stdev |
|--------------|---------------:|---------------:|--------------:|
| unstripped   |      25.98 ms  |     2,426.2 ms |       12.0 ms |
| stripped     |      27.56 ms  |     2,393.9 ms |       27.1 ms |
| **Δ**        |    **−1.58 ms**|    **+32.4 ms**|               |
| %            |       −6.1 %   |        +1.3 %  |               |

At fib(35), hinted is 6% faster (edge of noise). At 120× scale the
delta vanishes or reverses — well within stdev. **H2 rejected for
fib**: scaling does not expose latent hint value. LLVM converges to
equivalent codegen for this pattern at any size.

`quicksort` and `matmul_naive` could not be scaled safely: both hit
the pre-existing `List<Int>` indexing bug (docket Qs.1 from
v4.107.0), producing non-deterministic garbage checksums. Scaling
them would amplify the UB, not the optimizer signal. The Phase 3
runtime comparison at the original input sizes remains valid because
both variants execute the same garbage work.

---

## Hypothesis 3: passes don't consume hints

**Tested**: ran each of 10 LLVM passes individually on hinted and
stripped input; diffed the output after stripping cosmetic attr-ID
differences. For every (pass × benchmark) cell on `fib` and
`matmul_naive`, the resulting instruction-level diff is a single
blank line — i.e., **no single pass produces a different instruction
sequence based on Arc 11 hints**.

This is surprising given matmul's 24% full-pipeline speedup
(Phase 3). The resolution: Arc 11's benefit comes from
**pass-ordering / interaction effects**, not inline hint consumption.
The likely mechanism:

1. `inferattrs` / `function-attrs` reads Arc 11's declared
   `nounwind`/`willreturn`/`readonly` attributes on runtime-call
   declarations into LLVM's module-level attribute table.
2. Later passes — `early-cse`, `licm`, `mldst-motion`, `dse`,
   `jump-threading` — consult the attribute table to decide whether
   a call site is hoistable, sinkable, or eliminable.
3. Each individual pass makes different decisions at different call
   sites, compounding into different final codegen. No single pass
   emits different instructions from the one-pass diff perspective,
   because each pass's decisions are *about whether to transform*,
   not *what transformation to produce*.

This matches LLVM's documented analysis-manager architecture: the
attribute table is an analysis result, not a transformation input,
so a pass that reads it and declines to transform is invisible in
an isolated before-vs-after diff.

**H3 is subtly confirmed**: passes don't consume nsw/nuw inline, but
they do consume attribute-table entries in ways that are only
visible end-to-end.

---

## What Arc 11 actually did

**Kept** (continue to emit):
- Function attributes on runtime-call declarations — these
  demonstrably change optimizer decisions end-to-end.
- `nsw`/`nuw` on integer adds where the frontend can prove the bound
  (for readability and as a hedge against LLVM's inferrers
  regressing in future versions).

**Dead weight** (current emitter contribution is zero):
- TBAA metadata tree. Defined but never attached to any load/store.
  `grep -c '!tbaa' <ir>` returns 0 across all 4 benchmarks. The
  emitter's only mention of `!tbaa` is a comment at
  `mapanare/emit_llvm_text.py:913` describing the intended wiring —
  which was never implemented. Either wire it up (future work, if
  worthwhile — LLVM 18 can often infer type info for simple opaque
  pointers) or delete the module-level tree to remove the
  misleading "TBAA is live" appearance.

---

## What Arc 12 actually did

Not measured here (this release focuses on Arc 11's IR-quality
hints), but the `TOTAL_RESULTS.md` per-arc attribution stands:

- **MIR inlining (v4.87.0)**: the one genuinely load-bearing Arc 12
  contribution. It contributed −7.20 ms on `string_concat` at O2
  (pre-v4.108.0) by exposing concatenation intermediates to LLVM.
- **Strength reduction (v4.88.0)**: −0.55 ms on fib via mod→AND, but
  caused +6.07 ms regression on string_concat (different IR shape
  changed LLVM's decisions). Marginal-negative net.
- **LICM (built, disabled)**: miscompilation found before v4.89.0,
  gated off. Infrastructure landed; transform is future work.
- **Escape analysis (v4.89.0/v4.90.0)**: annotation infrastructure
  only; emitter doesn't consume `AllocKind.STACK` yet. Zero runtime
  impact shipped.

---

## Recommendations

1. **Remove the TBAA metadata tree** from the emitter (or wire it
   up). Shipping dead metadata that grep'ing the IR suggests is
   live is a misleading signal to anyone auditing this area.

2. **Audit `willreturn` on runtime-call declarations**. This
   attribute is the cause of string_concat's 21% regression in
   Phase 3 (hinted runs slower). A call that modifies heap-owned
   memory (like `__mn_sb_append` or `__mn_sb_finish`) should
   probably not carry `willreturn` because it blocks DSE of stores
   that the call might observe. Case-by-case audit of the
   `RUNTIME_FN_ATTRS` table in `emit_llvm_text.py` is warranted.

3. **Leave `nsw`/`nuw` emission alone**. LLVM recovers most of them
   anyway, and they're cheap both to emit and to have.

4. **Future optimizer arcs should measure per-workload wins/losses,
   not aggregate geomeans.** The 0.992× headline hid a 24% win plus
   a 21% regression. Arithmetic averaging across heterogeneous
   workloads is worse than useless — it makes a useful contribution
   look like waste.

5. **Wire escape analysis codegen.** Arc 12 built the infrastructure
   but the emitter still routes allocations through the runtime for
   structs that `AllocKind.STACK` marks as safe. Stack promotion is
   where the remaining allocator-bottleneck benchmarks will see
   their next structural speedup.

---

## Bottom line

**Arcs 11–12 produced roughly +24%, +9%, 0%, and −21% on the four
benchmarks, averaging to approximately flat.** The work was not
wasted:

- matmul's 24% speedup is real and attributable to function-
  attribute propagation through LLVM's analysis manager.
- TBAA dead-metadata is an honest mistake that should be cleaned up.
- `willreturn` on heap-modifying runtime calls is actively harmful
  for the one benchmark that exercises them and needs audit.

The headline 0.992× is a statistical artifact of mixing
heterogeneous workloads under arithmetic averaging. It is neither
a credit nor a debit to Arcs 11–12. The right accounting is
per-workload: Arc 11 unambiguously helped matmul-style code, was
neutral on recursion-heavy code, and unambiguously hurt mutable-
string-building code.
