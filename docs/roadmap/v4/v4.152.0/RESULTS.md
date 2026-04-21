# v4.152.0 E8 Results

## Per-pass verdicts

| Pass | v4.111.0 comment | v4.152.0 outcome | Evidence |
|---|---|---|---|
| E8a: strength_reduce | "Zero-ROI per v4.109.0; corroborates with inliner in verifier crashes" | **SAFE, ZERO-ROI — rolled back** | Goldens 54/66 (no regression), golden IR byte-identical, stage2.ll +1 line (just the call instruction), md5 changed only from register renumbering. Pass runs, finds 0 mod-by-power-of-2 patterns. |
| E8b: inline_small_functions | "Produces invalid MIR, crashes lower__verify_block" | **SAFE ON GOLDENS, BREAKS SELF-COMPILATION — rolled back** | Goldens 54/66 (pass), BUT llvm-as rejects stage2.ll: "multiple definition of local value named '%t4'" at line 261. Inliner renames inlined body variables with `_inl0_6_` prefix but the caller's destination register where the result is assigned back reuses the original name. Bug is in rename_instructions (mir_opt.mn:700-766). Opens In.1 for v5.x. |
| E8c: licm | "block_successors crashes; zero instruction-level effect at -O2" | **NO CRASH, BUT 3 GOLDEN REGRESSIONS — rolled back** | Build succeeds (block_successors crash gone). BUT goldens drop 54 → 51: `05_for_loop`, `21_list_ops`, `33_break_continue` (all loop-heavy). hoist_instruction moves instruction to header but leaves it in the original block too → duplicate definitions. Opens Li.1 for v5.x. |
| E8d: escape_analysis | "Crashes at +0x3f3 offset; scaffold, not production" | **SAFE, ZERO-ROI (STUB) — rolled back** | +0x3f3 crash gone (Ge.1 closure fixed underlying struct bug). Goldens 54/66 (no regression). stage2.ll byte-identical to baseline (md5 `39b68cd7333a4c0f69f58bcc9f8e8280`). The function always returns input unchanged — it's a stub ("future hook" at lines 1200-1204). |

## stage2.ll delta

- Baseline: 110,127 lines (md5 `39b68cd7333a4c0f69f58bcc9f8e8280`)
- Post-E8 (all passes rolled back): 110,127 lines (md5 identical)
- Diff: **0 lines (no-op)**

No pass earned ROI. All rolled back. stage2.ll is byte-identical to pre-E8 baseline.

## Build time delta

- Baseline: 102s (1m42s)
- Post-E8 (all rolled back): ~109s (varies by rebuild cycle)
- The comments added to mir_opt.mn increase the source size by ~40 lines,
  which adds ~5s to the concat+compile step. No net improvement.

## Benchmark delta

No benchmarks were re-run post-rollback because no pass survived to keep.
Cross-language and async baselines are unchanged (benchmarks measure
runtime perf; the dormant passes only affect compile-time MIR transforms
that LLVM -O2 would redo anyway).

## Python/self-hosted parity

| Pass | Python (mir_opt.py) | Self-hosted (mir_opt.mn) | Divergence |
|---|---|---|---|
| strength_reduce | ENABLED (line 2390) | DISABLED | Tolerable — pass finds nothing; LLVM instcombine covers |
| inline_small_functions | ENABLED (line 2382) | DISABLED | Structural — Python inliner works, self-hosted has rename bug (In.1) |
| licm | DISABLED (line 2387) | DISABLED | **Parity holds** — both sides agree |
| escape_analysis | ENABLED (line 2395) | DISABLED | Structural — Python version modifies alloc_kind, self-hosted is stub (Ea.1) |

All three divergences are inherent (self-hosted passes have bugs or
missing codegen the Python versions don't). No Python-side changes needed.

## New dockets opened

| ID | Severity | Description |
|---|---|---|
| In.1 | LOW | Self-hosted MIR inliner rename bug — caller destination register not renamed after inlining, produces duplicate SSA names. Fix in rename_instructions (mir_opt.mn:700-766). |
| Li.1 | LOW | Self-hosted LICM hoist_instruction leaves instruction in source block — produces duplicate definitions in loop-heavy tests. Fix in hoist_instruction (mir_opt.mn:1040-1069). |
| Ea.1 | LOW | Self-hosted escape_analysis is a stub — function body always returns input unchanged. Needs stack-promotion codegen in emit_llvm.mn to be useful. |

## Honest story

In v4.111.0, with goldens at 21/64 and the verifier still fragile, we
disabled four MIR optimizer passes — strength reduction, function
inlining, LICM, and escape analysis — because all four either crashed
the compiler or were proven zero-ROI by v4.109.0's forensic analysis.
The rationale was simple: LLVM's -O2 pipeline does the same work, so
skipping the self-hosted passes costs nothing.

Seven months and 41 releases later, with goldens at 54/66 and the Sh.2,
Sh.8, Sh.11, Sh.12, and Ge.1 arcs all closed, we re-evaluated all four
under current conditions. The crashes are largely gone — only LICM still
corrupts output (3 loop-heavy test regressions), while the other three
run without error. But "doesn't crash" is not the same as "earns its
keep." Strength reduction finds zero patterns to reduce. Escape analysis
is a stub that always returns its input unchanged. The inliner produces
valid golden IR for small programs but introduces SSA name collisions
when compiling the full self-hosted stack (38K+ lines), breaking
self-compilation at the llvm-as stage.

The v4.109.0 rationale holds: LLVM's -O2 subsumes all four passes. The
self-hosted MIR optimizer runs passes 1-3 (constant folding, constant
propagation, dead block elimination) — these are the passes that earn
ROI by cleaning up MIR before it reaches the LLVM backend. Passes 4-7
remain dormant, each with an updated v4.152.0 comment documenting the
exact failure mode and what would need to change for re-enablement
(In.1, Li.1, Ea.1 dockets). The experiment is a full dead end — four
passes evaluated, zero kept — but it's a credible negative result that
refreshes stale v4.111.0 comments with 2026-era evidence.
