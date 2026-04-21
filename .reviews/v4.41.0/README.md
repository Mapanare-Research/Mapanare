# Mapanare v4.41.0 Panel — Arc 2 Close (LSP Maturity)

**Date:** 2026-04-12
**Reviewers:** 7 (independent, parallel)
**Previous Review:** v4.36.0 (9.50/10 aggregate, 6 PASS + 1 PASS WITH NOTES)
**Arc Under Review:** Arc 2 — LSP Maturity (v4.37.0-v4.40.0)

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Delta vs v4.36.0 | Top 3 observations |
|---|----------|--------|---------|-------|-------------------|---------------------|
| 01 | **Viper** | Rust / memory safety | PASS WITH NOTES | 9.5 | 0.0 | Timer leak on close (LOW); AST retained after collection (LOW); zero new memory-safety surface |
| 02 | **Boa** | Python / DX | PASS WITH NOTES | 9.2 | -0.3 | Double diagnostic publish on keystroke (HIGH); debounce timer race on close (HIGH); `receiver_type_at` missing (MEDIUM) |
| 03 | **Cobra** | C++ / ABI | PASS | 9.8 | 0.0 | Zero ABI changes; struct detail strings omit field types (LOW); P3/A10 tracking stale |
| 04 | **Mamba** | C / runtime | PASS | 9.5 | 0.0 | Zero runtime changes; timer doesn't touch runtime; items 49/50 tracked |
| 05 | **Anaconda** | toolchain | PASS | 8.9 | -0.5 | `expr.receiver` attribute bug (HIGH); redundant parse passes (MEDIUM); `receiver_type_at` dead (MEDIUM) |
| 06 | **Rattler** | LLVM / codegen | PASS | 9.4 | 0.0 | Zero codegen changes; P3 guard divergence unchanged; same checker reused |
| 07 | **Coral** | Language design | PASS WITH NOTES | 9.2 | -0.2 | Option/Result methods aspirational (HIGH); keyword list drift (HIGH); method completion kind unmapped (MEDIUM) |

---

## Aggregate

**Aggregate score: 9.36/10** (down from 9.50 at v4.36.0, -0.14 delta)

**Verdicts: 4 PASS + 3 PASS WITH NOTES + 0 NEEDS WORK**

**Arc 2 termination gate: PASS** (aggregate >= 9.0, zero NEEDS WORK)

---

## Consensus

The panel agrees that Arc 2 delivered a functional LSP foundation — the workspace index is well-designed, the parser/semantic reuse is clean, and cross-module go-to-def works. However, the **implementation has rough edges** that the v4.36.0 panel's higher bar did not encounter (Arc 1 was compiler work graded by compiler experts; Arc 2 is LSP work where Boa and Coral are the domain experts and graded more critically).

**Three HIGH-severity findings are real bugs:**
1. **Double diagnostic publish** (Boa H1) — every keystroke publishes twice
2. **`expr.receiver` attribute bug** (Anaconda H1) — reference collection crashes on method calls/field access
3. **Option/Result method completions are aspirational** (Coral H1) — methods don't exist in the compiler

The score drop (-0.14) is appropriate: the arc delivered features, but the finishing quality is below the standard set by Arcs 0-1.

---

## Post-Production Health

**Is the language still healthy 41 minors after v4.0.0?** YES.

- 820 tests pass, zero regressions in compiler/runtime
- LSP has real bugs but they're in the editor layer, not the compiler
- The workspace index is a solid foundation for Arc 3+

---

## Prioritized Action Items

### HIGH (fix in v4.42.0 before moving to Arc 3 features)

| # | Item | Source |
|---|------|--------|
| 1 | Double diagnostic publish — remove immediate `_analyze_and_publish` from `on_change`, keep only debounce | Boa H1, Anaconda |
| 2 | `expr.receiver` → `expr.object` in `_collect_references` walker | Anaconda H1 |
| 3 | Remove aspirational Option/Result/List method completions until methods exist in compiler | Coral H1 |
| 4 | Fix `_KEYWORDS` in rename.py — derive from grammar, add real bilingual keywords, remove phantoms | Coral H2 |

### MEDIUM (track to v4.42.0+)

| # | Item | Source |
|---|------|--------|
| 5 | Implement `receiver_type_at` or remove the field/method completion path | Boa M2, Anaconda |
| 6 | Cancel debounce timer on close + save | Boa H2, Viper V1 |
| 7 | Reduce parse passes — `on_save` runs 3 independent parses | Anaconda |
| 8 | Add missing String/Map methods to completion tables | Coral M1, M2 |
| 9 | Map `"method"` completion kind in server.py | Coral M3 |
| 10 | Extend AST walker for WhileLoop, LambdaExpr, BinaryExpr, PipeExpr | Anaconda, Boa |

### LOW (track but don't block)

| # | Item | Source |
|---|------|--------|
| 11 | WorkspaceIndex retains full ASTs after collection | Viper V2 |
| 12 | Struct/enum detail strings omit field types | Cobra |
| 13 | P3 guard fall-through divergence (3rd cycle) | Cobra, Rattler |
| 14 | A10 bounded-for count stale (442 vs 552) | Cobra |
| 15 | Item 49 drop-glue (10th cycle) | Viper |

---

## Score Trajectory

| Panel | Aggregate | Delta | NEEDS WORK |
|-------|-----------|-------|------------|
| v3.47.0 | 9.79 | — | 0 |
| v4.26.0 | ~8.2 | -1.59 | 4 |
| v4.31.0 | 9.343 | +1.14 | 0 |
| v4.36.0 | 9.50 | +0.157 | 0 |
| **v4.41.0** | **9.36** | **-0.14** | **0** |

The dip is expected — Arc 2 introduced a new domain (editor tooling) where the quality bar is different from compiler work. The aggregate remains well above the 9.0 threshold.

---

## Next

Arc 2 is **CLOSED** (aggregate 9.36 >= 9.0, zero NEEDS WORK). The 4 HIGH items should be fixed early in v4.42.0 before starting Arc 3 features.

v4.42.0 opens **Arc 3 (tensor completeness)**: tensor literals, indexing, broadcasting, slicing. Panel at v4.46.0.
