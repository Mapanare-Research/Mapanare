# Mapanare v4.51.0 Panel — Arc 4 Close (Stdlib AI/LLM)

**Date:** 2026-04-12
**Reviewers:** 7 (independent, parallel)
**Previous Review:** v4.46.0 (8.99/10 aggregate, CONDITIONAL PASS)
**Arc Under Review:** Arc 4 — Stdlib AI/LLM (v4.47.0-v4.50.0)

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Delta vs v4.46.0 | Top 3 observations |
|---|----------|--------|---------|-------|-------------------|---------------------|
| 01 | **Viper** | Rust / memory safety | PASS WITH NOTES | 9.0 | -0.4 | Quadratic string concat in HTTP recv (MEDIUM); rscalar null check missing (MEDIUM); carry-forward stagnation (1/11 closed) |
| 02 | **Boa** | Python / DX | PASS | 9.5 | +0.1 | `chat_stream` not real streaming (HIGH); `extract_text` returns String not T (HIGH); best API ergonomics in the project |
| 03 | **Cobra** | C++ / ABI | PASS | 9.30 | -0.15 | 13 functions duplicated between llm.mn and embedding.mn (MEDIUM); `__struct_meta` well-designed; TLS lifecycle correct |
| 04 | **Mamba** | C / runtime | PASS | 7.5 | -1.0 | ~7,000 string allocs per chat() call (HIGH); 200 lines duplicated (MEDIUM); vector store over-allocates SearchResult |
| 05 | **Anaconda** | toolchain | PASS | 9.3 | +0.1 | `__struct_meta` missing struct-type validation (MEDIUM); 77% tests are grep-based (MEDIUM); self-hosted tensor stub at 5th cycle |
| 06 | **Rattler** | LLVM / codegen | PASS WITH NOTES | 8.6 | +0.6 | v4.46.0 CRITICAL bugs CLOSED; `__struct_meta` constant-folding correct; slice alloca in wrong block (MEDIUM) |
| 07 | **Coral** | Language design | PASS | 9.1 | +0.1 | `__struct_meta` principled within constraints (8.5/10); AI stdlib coherent but extract returns String not T; P5 CLOSED |

---

## Aggregate

**Aggregate score: 8.90/10** (down from 8.99 at v4.46.0, -0.09 delta)

**Verdicts: 5 PASS + 2 PASS WITH NOTES + 0 NEEDS WORK**

**Arc 4 termination gate: CONDITIONAL PASS** — aggregate 0.10 below the 9.0 threshold. Zero explicit NEEDS WORK. Mamba's 7.5 (string allocation pathology) is the primary outlier. The issues are library-quality problems, not architectural failures.

---

## Consensus

The panel agrees that **Arc 4 delivered the "AI-native" claim as a real, usable library surface.** The API design (Boa: "most Pythonic code in the codebase") is strong. The `__struct_meta::<T>()` builtin is principled (Coral: 8.5/10, Rattler: architecturally correct, Anaconda: clean pipeline integration). The v4.46.0 CRITICAL bugs are fully resolved.

**Two systemic issues prevent a clean 9.0+ PASS:**

### Issue 1: String allocation pathology (HIGH — Mamba, Viper, Cobra)

The AI stdlib builds HTTP requests, JSON bodies, and response strings via character-by-character concatenation (`result = result + ch`). Mamba measured ~7,000 allocations per `chat()` call. `escape_json` alone does 500 mallocs for a 500-char message. This is O(n^2) time and O(n) allocations.

**Fix:** Use `StringBuilder` or batch `substr` operations. Not an API change — internal optimization.

### Issue 2: Code duplication between llm.mn and embedding.mn (MEDIUM — Cobra, Viper, Mamba)

13 functions are copy-pasted between the two modules, including the entire HTTP client, JSON parser, and TLS lifecycle. The copies have already diverged (`jget_str` unescape behavior differs). A proper `stdlib/net/http.mn` exists but is not used.

**Fix:** Extract shared HTTP/JSON helpers into a common module. Not an API change.

---

## Post-Production Health

**Is the language still healthy 51 minors after v4.0.0?** YES.

The AI stdlib is well-designed and properly integrated. The issues found are library implementation quality (string performance, code duplication) not architectural problems. The compiler changes (+105 lines) are clean and follow established patterns.

---

## Prioritized Action Items

### HIGH (fix in v4.52.0)

| # | Item | Source |
|---|------|--------|
| 1 | String allocation pathology: replace char-by-char concat with substr/batch in HTTP/JSON builders | Mamba, Viper |
| 2 | `chat_stream` rename or doc clarification (not real streaming until v4.74.0) | Boa H1 |
| 3 | Extract shared HTTP/JSON helpers from llm.mn + embedding.mn | Cobra, Viper, Mamba |

### MEDIUM

| # | Item | Source |
|---|------|--------|
| 4 | `__struct_meta` validate T is struct type (currently silently produces empty schema for Int/Bool) | Anaconda M1 |
| 5 | `extract_text` → chain with `decode_to::<T>()` for true typed extraction | Coral M1, Boa H2 |
| 6 | Nested struct support in `__struct_meta` (recursive schema) | Coral M2 |
| 7 | Slice alloca in entry block instead of current block (loop stack growth) | Rattler BUG-4 |
| 8 | Make `jget_str`/`jget_int` public for user-facing JSON field access | Boa |
| 9 | rscalar macro null check on tensor parameter | Viper V2 |

### LOW

| # | Item | Source |
|---|------|--------|
| 10 | Self-hosted emit_tensor_init stub (5th cycle) | Anaconda L1 |
| 11 | Port-based TLS detection → scheme-based | Cobra |
| 12 | jget 100k iteration cap truncates large JSON | Viper V4 |
| 13 | Carry-forward stagnation: #49 at 14th cycle, tensor attrs at 3rd cycle | Viper |

---

## Disagreements

None. All reviewers agree:
- `__struct_meta::<T>()` is the right design for now
- The API surface is well-designed (Boa 9.5)
- String performance is the main quality gap (Mamba, Viper, Cobra)
- P5 examples/ carry-forward is CLOSED

---

## Improvements Since v4.46.0

- v4.46.0 CRITICAL bugs (slicing inttoptr, scalar-tensor sub/div) fully resolved
- Rattler score recovered +0.6 (8.0 → 8.6)
- AI stdlib: 3,482 lines across 4 modules, 87 tests, 4 demos, cookbook chapter
- `__struct_meta::<T>()` — first compile-time reflection primitive
- P5 examples/ carry-forward CLOSED after 3 cycles
- README "Hello AI" snippet ships the AI-native story

---

## Regressions Since v4.46.0

- Aggregate: 8.99 → 8.90 (-0.09)
- Mamba dropped -1.0 (string allocation quality)
- Viper dropped -0.4 (carry-forward stagnation)

---

## Panel Recommendation

**CONDITIONAL PASS.** The aggregate (8.90) is 0.10 below the 9.0 threshold, driven by string allocation pathology in the new library code. Zero NEEDS WORK verdicts. The API design and compiler work are clean.

**Recommendation:** v4.52.0 opens Arc 5 (compiler debt drain) as planned. The string optimization and code deduplication are Arc 5's exact mandate (debt drain). This is not a recovery scenario — the issues are implementation quality in new library code, not regression.
