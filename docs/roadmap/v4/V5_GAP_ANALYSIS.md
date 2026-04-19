# v4.x → v5.0.0 Gap Analysis

**As of:** v4.143.0 (2026-04-18) · `v5.0.0-rc1` tag live at v4.136.0 commit
**Panel aggregate:** 8.86/10 (3 EXCEEDS / 4 MEETS / 0 NEEDS WORK) → Option C preserved
**Ledger:** 63 opened · 58 closed (92%) · 0 CRITICAL / 0 HIGH / **0 MEDIUM** / 5 LOW

---

## 1. Delivered themes (the v4.x arcs)

| Range | Arc | One-line summary |
|---|---|---|
| v4.0.0 – v4.7.1 | Production + foundational refactor | v4.0.0 ship; then drop-glue, thread-safety, type-system, self-hosted cleanup. |
| v4.8.0 – v4.17.0 | Deep fixes + fixed-point bootstrap | Workarounds, optimizer unification, MIRType enum, Culebra gate, 3-stage bootstrap groundwork. |
| v4.18.0 – v4.26.0 | Language evolution (hollow) | Tensor shapes, `@gpu` auto-kernels, async, FFI, `const` — panel found 6 hollow features; 9.79 → 8.2. |
| v4.27.0 – v4.31.0 | **Recovery arc** | Honesty pass: Path-B removals of hollow features, docs/test honesty CI gates. Panel 9.343/10. |
| v4.32.0 – v4.61.0 | Arcs 1–6: Feature + debt drain | `?` operator, pattern matching, LSP, tensor completeness, AI/LLM stdlib, dead-emitter deletions. |
| v4.62.0 – v4.76.0 | Arcs 7–9: DWARF + coroutines | DWARF debug info (A2 closed), real `async`/`await` with LLVM coroutine intrinsics (A1 closed). |
| v4.77.0 – v4.96.0 | Arcs 10–13: Integration + perf | Integration test harness, MIR inlining/LICM/escape, real suspension, work-stealing scheduler, StringBuilder. |
| v4.97.0 – v4.99.0 | Arc 14: v5 attempt 1 | **Panel 6.59/10 NEEDS WORK**; tagged-pointer UB, list-indexing, async linking flagged. |
| v4.100.0 – v4.110.0 | Phases A–C: Bug sprint + perf surface | MnString bitfield, Python-emitter drop-glue move-semantics, cross-language benchmarks, StringBuilder auto-wiring. |
| v4.111.0 – v4.120.0 | Phase D–F: Self-hosted golden parity | Goldens 21 → 27 via 4 zero-ROI MIR passes disabled. **Panel 8.21, 1 NEEDS WORK (Anaconda).** |
| v4.121.0 – v4.135.0 | Closeout arc | Sh.2 LIST+STR, fixed-point strict (v4.134.0), An.1 test hygiene, 4 flaky audits. |
| v4.136.0 | **v5 attempt 3** | Panel 8.80, 0 NEEDS WORK → Option C → `v5.0.0-rc1` tag. |
| v4.137.0 – v4.142.0 | Post-rc1 bridge | Ch.1 UAF, Bo.* docs, Gr.2, Cb.5 enum-ABI parity, An.2 lint, Ge.1 valgrind. |
| v4.143.0 | Post-rc1 panel + Option-A bridge | Panel 8.86, 0 NEEDS WORK. Bn.1 + Gr.3 + Reg.1 closed in-release. |

## 2. What shipped since rc1 (v4.137.0 → v4.143.0)

| Release | Summary | Dockets closed |
|---|---|---|
| v4.137.0 | `mapanare_agent_destroy` now `pthread_join`s before teardown; 3 sanitizer classes un-skipped. | **Ch.1** (HIGH) |
| v4.138.0 | Docs sweep; `mapanare --version` reads VERSION file; localized READMEs synced; `known_issues.md` created. | **Bo.1–Bo.7** (MEDIUM bundle) |
| v4.139.0 | Qualified type refs in type position; module-level `let mut` → E420; `__MN_VERSION__` placeholder. | **Gr.2, Sem.1, §0, Co.1, Dr.1** |
| v4.140.0 | Self-hosted `_enum_inline` port → byte-identical enum ABI; Sh.2 extended to MAP/SIGNAL/STREAM. | **Cb.5, SE.1, Cb.3** |
| v4.141.0 | Lint debt 204+65+36 → 0; `TestToolsRunLocally` un-skipped; 5th flaky audit (25/0 cumulative). | **An.2** |
| v4.142.0 | Ge.1 closed via `try_monomorphize_enum` moved-ownership + internal-struct parity fixes; valgrind 5 → 0 ERRORS. | **Ge.1** |
| v4.143.0 | Post-rc1 panel (8.86). Fast-wins: Sp.1, Co.1r, Sem.2, An.6, An.7, An.8, Bo.*-drift. Option-A bridge: Bn.1, Gr.3, Reg.1. | **14 dockets** |

Panel **MEDIUM queue emptied** at v4.143.0.

## 3. Explicitly skipped / removed (Path B decisions)

| Feature | Removed | Status |
|---|---|---|
| `extern "Python" fn` syntax | v4.29.0 | Replaced by `mapanare bind --lang python` (ctypes) |
| `await` identity lowering (no-op) | v4.30.0 | **Real coroutine lowering landed v4.75.0** |
| `@gpu` / `@cuda` / `@vulkan` decorators | v4.27.0 | **Re-added for v2.0.0 GPU backend** (different impl) |
| `const` keyword (parser alias, no semantics) | v4.27.0 | **Real `const` landed v4.126.0** |
| DWARF `-g` / `--debug` flag | v4.29.0 | **Real DWARF landed v4.65.0** |
| llvmlite JIT emitter (`mapanare/jit.py`) | v4.59.0 | Deleted; dependency dropped |
| `PythonMIREmitter` (`emit_python_mir.py`) | v4.58.0 | Deleted (~3,500 LOC) |
| `emit_c.mn` (self-hosted C emitter) | v4.2.0 / re-verified v4.54.0 | Deleted; referenced non-existent MIR types |
| AST-based `emit_llvm.py` + MIR+llvmlite `emit_llvm_mir.py` | v4.2.0 | Deleted (~8,500 LOC of dead emitters) |
| `--no-mir` / `--emitter llvmlite` CLI flags | v4.2.0 | Removed |
| MIR passes: `strength_reduce`, `inline_small_functions`, `licm`, `escape_analysis` | v4.111.0 | Disabled in self-hosted `mir_opt.mn` (zero-ROI per v4.109.0 forensics) |
| TBAA metadata tree | v4.123.0 | Deleted from Python + self-hosted emitter (100% dead, never attached) |
| `mapanare/optimizer.py` (legacy) | v4.123.0 | Deleted (1,203 LOC, 9% coverage) |
| CHANGELOG v4.18.0–v4.26.0 hollow-feature claims | v4.27.0 | Rewritten in stricken form; CI gate added |
| `Tensor` struct in stdlib (grammar collision) | v4.143.0 | Renamed → `GpuTensor` |

## 4. Deferred to v5.x feature track

From `.reviews/v4.136.0/V5_DECISION.md`:

- **Sh.4 / Sh.5 / Sh.6 / Sh.7** — self-hosted async / const / tensor / closure-typed emitter gaps (12 goldens still go through the Python bootstrap).
- **Gr.1** — multi-line list / tensor literal grammar.
- **ABI.1** — 24-byte struct return ABI (residual ~2.3× vs C gcc on `enum_match`).
- **TR.1** — `test_runner` synthetic `main` injection (7 SKIP tests from An.1).
- **Bn.1 residual** — benchmark regeneration (closed harness, but README numbers still cite v4.136.0 pack).
- **Rt.2** — `dir_create` ignores `recursive` flag (1 SKIP).
- **Rt.3** — `tmpfile_path` is a stub (2 SKIP).
- **Tm.1** — memory-stress fixture no-concat (1 SKIP).
- **Own.1** — compile-time move-semantics enforcement in self-hosted lowerer (v4.143.0 Viper).
- **A10** — self-hosted bounded-for sentinels (grammar gap accepted, 10 cycles open).

## 5. Still open on the v4.143.0 ledger (all LOW)

| # | Docket | Owner | Notes |
|---|---|---|---|
| 1 | **Cb.5-tests** | Rattler / Cobra | Dedicated inline-slot eligibility unit tests missing (only `enum_match` checksum covers it). |
| 2 | **Cb.6** | Cobra | Polish item from v4.143.0 Cobra review. |
| 3 | **Cb.7** | Cobra | Polish item from v4.143.0 Cobra review. |
| 4 | **Cb.9** | Cobra | Polish item from v4.143.0 Cobra review. |
| 5 | **Cb.10** | Cobra | Polish item from v4.143.0 Cobra review. |
| (carry) | **Own.1** | Viper | Compile-time move-semantics enforcement in self-hosted lowerer (Ge.1 root-cause pattern). Tagged v5.x refactor. |

`Mar.1` closed implicitly by Bn.1. `Cb.8` does not appear in the v4.143.0 SESSION_REPORT ledger — the Cobra bundle is Cb.6/7/9/10 (four items, not five).

## 6. Gap to clean v5.0.0 — honest answer

**Recommendation: (b) ship v4.144.0 as a LOW-polish release and re-panel for Option A.**

The aggregate is 8.86 with **0 MEDIUM open** for the first time since v4.99.0. The 0.14-point gap to 9.0 is narrow and the only remaining items are 5 LOW dockets + 1 LOW/v5.x carry (Own.1). Shipping Cb.5-tests + the Cb.6/7/9/10 bundle (a day or two of work, no architectural risk) and re-running the panel is the cleanest path — the `v5.0.0` tag would then be earned by the rule, not claimed by override. Option (a) is within the lead's discretion but leaves the asymmetry that the tag says "final" while the panel says "rc1-equivalent"; Option (c) is overkill — Sh.4–Sh.7 are self-hosted emitter gaps, not v5 blockers (the Python bootstrap covers them). The fast path to a defensible v5.0.0 is polish-and-re-panel, not feature work.

## 7. Risk / watch items

1. **WASM backend drift.** No reviewer covers WASM. `emit_wasm.py` (~2,785 LOC) and `wasm_linker.py` last got substantive work in Arc 11/12; CI compiles `examples/wasm/*.mn` but there is no WASM reviewer and no docket ledger — any regression is caught only by CI green, not by panel attention.
2. **GPU stdlib is half-wired.** v4.143.0 Gr.3 closed the `Tensor` keyword collision, but the SESSION_REPORT explicitly notes `stdlib/gpu/tensor.mn` has "pre-existing undefined-symbol errors (`__mn_tensor_*` runtime declarations, `new_alloc_failed` constructor) that surfaced for the first time once the parser could read past the Tensor collision." These are unticketed.
3. **Mobile/Android target rot.** `aarch64-linux-android` / `aarch64-apple-ios` / `x86_64-linux-android` are in the CI matrix but no panel cycle has exercised mobile runtime features (cooperative scheduler, smaller arenas, 4K intern cap) post-v4.99.0. iOS CI is explicitly deferred.
4. **Ecosystem packages (Dato, stdlib/ai/*).** Dato lives in a separate repo; stdlib AI (`llm.mn`, `embeddings.mn`, `rag.mn`) was shipped in Arc 4 (v4.47.0–v4.51.0) and touched again in v4.95.0 (StringBuilder refactor) but has no reviewer and no panel scorecard. Advertised as v5-ready on the README.
5. **Near-fixed-point vs strict.** v4.134.0 hit strict 3-stage byte-identical (`md5 0c00ad07...`); v4.139.0 Dr.1 (`__MN_VERSION__` placeholder) broke strict — current state is 4-line version-metadata diff within `DIFF_THRESHOLD=100`. Documented honestly but a reviewer could reopen this as a regression depending on their read of Cobra's v4.99.0 v5 blocker.
