# Mamba — C Runtime Review (Arc 11)

**Grade: 8/10**
**Verdict: PASS WITH NOTES**

## Assessment

The benchmark infrastructure is well-designed: 5 workloads, 3 opt levels, median-of-5 with warmup, cross-language comparison, JSON output. The `run_baseline.py` harness is clean and reproducible.

**The honest negative result is the most important finding.** The runtime is the bottleneck, not the IR. Every benchmark that calls runtime functions (`__mn_list_get`, `__mn_str_concat`, `__mn_list_push`) shows flat performance regardless of IR annotations. LLVM cannot optimize across the FFI boundary.

**string_concat is 2.7x slower than Python** and 146x slower than Rust. This is a runtime allocation design issue: `__mn_str_concat` allocates a new string on every call. Python's CPython has an optimization that reallocs in place for `str +=`. Mapanare has no equivalent.

**The agent_fanout benchmark is misleading.** It simulates agent work with pure functions — no actual agents, no ring buffers, no thread scheduling. The real agent overhead is not measured.

## Score justification

8/10 — excellent benchmark methodology and honest analysis. One point deducted because the agent benchmark doesn't exercise the actual runtime scheduler, and the string_concat regression was identified but not addressed. The runtime needs Phase 2 work.
