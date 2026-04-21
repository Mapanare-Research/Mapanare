# Pre-Panel Audit — v4.81.0 (Arc 10)

## Arc scope

| Version | Theme | Key deliverable |
|---------|-------|-----------------|
| v4.77.0 | Integration test harness | 59 golden tests through full LLVM pipeline; CI gate |
| v4.78.0 | Carry-forward drain (49, 50, A10b) | Drop-glue escape analysis, agent destroy drain, const scope |
| v4.79.0 | Carry-forward drain (P2, P3, P6) | Pattern matching tests, guard divergence, unreachable-arm tests |
| v4.80.0 | Documentation | Async cookbook, SPEC Futures, gdb tutorial |

## Test evidence

### Integration tests (2 runs, stable)

| Metric | Count |
|--------|-------|
| Total | 59 |
| Pass (end-to-end) | 47 |
| Xfail (known) | 5 |
| Skip (external resources) | 7 |
| Fail | 0 |
| Flaky | 0 |

### Pattern matching tests

54 unit tests covering all 25 functions in `pattern_matching.py`. 9 unreachable-arm warning tests (7 unit + 2 integration). All 62 pass.

### Drop glue tests

8 tests including 2 new struct-return drop-glue tests (v4.78.0). All pass. `__mn_str_free` confirmed emitted for heap-allocated locals in struct-return functions.

### Agent destroy drain

2 C tests (`test_agent_destroy_drain.c`). Default `free()` path and custom destructor path both verified. Builds clean with `-Werror`.

## Carry-forward ledger

| Status | Count |
|--------|-------|
| CLOSED (all arcs) | 50+ |
| OPEN (Mapanare-owned) | 0 |
| OPEN (external/accepted) | 2 |

Open items:
- A5: Culebra `list-element-size-undercount` (external, not ours)
- A10: Bounded-for sentinels (accepted grammar gap, not a bug)

## Documentation deliverables

| Document | Sections | Status |
|----------|----------|--------|
| `docs/cookbook/async.md` | 7 | Complete |
| `docs/SPEC.md` section 29 | 7 | Complete |
| `docs/guides/debugging.md` | 9 | Complete |

## Known limitations entering the panel

1. Async examples in the cookbook compile through `mnc` (native) but not through the Python bootstrap's `emit-llvm` (xfailed in integration suite)
2. A10b const scope: source fix applied but compiled binary has a lexer codegen issue
3. P3 guard fall-through: jump-to-next correct for common case; full decision-tree port is future work
4. Integration test pass rate is 47/59 (80%), not 100% — 5 are known xfails (async + try operator + guard+or), 7 are skips (external resources)
