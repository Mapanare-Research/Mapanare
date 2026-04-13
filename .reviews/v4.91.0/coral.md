# Coral — Language Design Review (Arc 12)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

### User-facing optimization model

Mapanare's `-O` levels map cleanly to user expectations:

- **O0:** No optimization. Fastest compile, slowest run. For debugging.
- **O1:** Constant folding + propagation. Safe, predictable speedup on arithmetic-heavy code.
- **O2:** Full pipeline (10 passes). Default for production.
- **O3:** O2 + stream fusion. Aggressive, may increase code size.

This 4-level model is standard (matches GCC/Clang/Rust) and well-documented in the `MIROptLevel` enum. Users don't need to understand individual passes — the levels are self-explanatory.

### Escape analysis as language design

Escape analysis is invisible to users — it's a pure implementation optimization. The language semantics don't change: allocations are logically on the heap, but the compiler may choose to place them on the stack if it can prove safety. This is the gold standard for optimization design: the user's mental model is unchanged, the compiler does the work.

The 4KB promotion limit is sensible. A user creating a 10KB struct won't see it promoted — but they also won't see unexpected stack overflows. The conservative loop guard is similarly user-friendly: no surprising stack growth in tight loops.

### Inlining semantics

Function inlining preserves Mapanare's call semantics: pass-by-value for primitives, pass-by-reference for structs (via sret). The cost model (< 20 instructions, not recursive) is conservative enough that users won't see unexpected code bloat. There's no `@inline` annotation to force inlining — this is fine for now. The compiler's heuristic should be sufficient for most code.

### Benchmark narrative

The TOTAL_RESULTS.md tells an honest story. The O2 geometric mean of 0.992x is presented as "effectively flat" rather than spun as a positive. The 1.1x vs Rust on fib_recursive is highlighted as a legitimate achievement. The 131x string_concat gap is not hidden. This is the kind of transparent communication that builds trust.

### Missing: optimization documentation

There is no user-facing document explaining what optimizations Mapanare performs at each level. The CLAUDE.md and SPEC.md don't describe the optimizer. For a language targeting developers who care about performance (the existence of benchmarks suggests this audience), a "Performance Guide" or "Optimization Guide" would be valuable.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| Optimization guide for users | MEDIUM | What O0/O1/O2/O3 do, what to expect |
| SPEC.md optimization semantics | LOW | Define what optimizations are guaranteed vs. heuristic |

## Score justification

9/10 — the optimization model is clean, user-invisible, and well-structured. Benchmark narrative is honest. Missing user documentation noted but not blocking. The language design choices (conservative heuristics, no user annotations required) are appropriate for the current maturity level.
