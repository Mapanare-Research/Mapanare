# Arc 10 Panel — v4.81.0

**Arc:** 10 (Integration Tests + Debt Zero)
**Releases graded:** v4.77.0 - v4.80.0
**Panel date:** 2026-04-13
**Aggregate: 9.00/10**
**Verdict: PASS (7 PASS, 0 NEEDS WORK)**

This is the first panel of the post-plan era. Arc 10 is the first arc
that ships zero new language features — it builds infrastructure,
closes debt, and writes documentation.

---

## Verdict Table

| # | Reviewer | Lens | Grade | Verdict |
|---|----------|------|-------|---------|
| 1 | Rattler | LLVM | 9/10 | PASS |
| 2 | Viper | Memory safety | 9/10 | PASS |
| 3 | Anaconda | Toolchain (PRIMARY) | 9/10 | PASS |
| 4 | Cobra | C++/ABI | 9/10 | PASS |
| 5 | Coral | Language design | 9/10 | PASS |
| 6 | Boa | Python/DX (PRIMARY) | 9/10 | PASS |
| 7 | Mamba | C runtime | 9/10 | PASS |

**Aggregate: 9.00/10** (63/70)

---

## Consensus findings

### What Arc 10 delivered

1. **Integration test harness (v4.77.0).** 59 golden tests through the full
   LLVM pipeline for the first time. `emit-llvm -> llvm-as -> opt -O2 -> llc
   -> clang link -> execute -> stdout check`. 47 pass, 5 xfail, 7 skip. CI
   gate on every push to dev. This is the infrastructure every panel since
   Arc 3 has asked for.

2. **Carry-forward ledger at zero (v4.78.0-v4.79.0).** Six items closed
   across two releases: 49 (drop-glue escape analysis, 8 cycles), 50 (agent
   destroy drain, 2 cycles), A10b (const scope, 3 cycles), P2 (pattern
   matching tests, 2 cycles), P3 (guard divergence, 2 cycles), P6
   (unreachable-arm tests, 2 cycles). Zero Mapanare-owned items remain.

3. **Documentation (v4.80.0).** Async cookbook (7 sections), SPEC Futures
   section 29 (7 subsections), gdb/lldb debugging tutorial (9 sections).
   Closes Boa's documentation feedback from 6+ panels.

### Unanimous checkpoints

- 7/7 agree: the integration harness is real infrastructure, not a checkbox
- 7/7 agree: the carry-forward ledger is genuinely at zero (walked every row)
- 7/7 agree: the documentation fills real gaps, not aspirational ones
- 7/7 agree: no hollow features — this arc ships only things that work

### Items noted (not blocking)

| Item | Source | Priority | Notes |
|------|--------|----------|-------|
| Self-hosted integration testing | Rattler, Anaconda | MEDIUM | Wire mnc-stage1 into the harness (future arc) |
| Async cookbook CI verification | Boa | LOW | Async examples need native compiler path, not emit-llvm |
| Full valgrind sweep | Viper | LOW | Code analysis is sound; valgrind confirmation deferred |
| Cross-architecture ABI tests | Cobra | LOW | ARM64 integration testing future work |
| Runtime stress testing | Mamba | LOW | High-volume agent destroy scenario |

---

## Arc 10 retrospective

### What worked

1. **Infrastructure-first arc.** No new features. Every release built
   something that makes the next release safer. This is the correct
   response to a feature-complete compiler.

2. **Carry-forward discipline.** The ledger system introduced after the
   v4.26.0 crisis has paid off. Every item was tracked with severity,
   cycle count, and evidence. Closing the last 6 items in 2 releases
   demonstrates that the tracking works — items don't drift indefinitely.

3. **Documentation as a deliverable.** Treating docs as a versioned
   release (v4.80.0) with the same commit discipline as code releases
   ensures they are written, reviewed, and maintained.

### Metrics

| Metric | Arc 9 end (v4.76.0) | Arc 10 end (v4.81.0) | Delta |
|--------|---------------------|----------------------|-------|
| Golden tests (integration pipeline) | 0 | 47/59 pass | +47 |
| Carry-forward open (Mapanare-owned) | 6 | 0 | -6 |
| Pattern matching test coverage | 0 dedicated tests | 54 unit tests | +54 |
| Documentation chapters | 15 cookbook + 28 SPEC | 16 cookbook + 29 SPEC + 1 guide | +3 |
| Integration CI gate | no | yes | new |

---

## After Arc 10

Arc 10 closes. The lead picks the Arc 11 theme. Panel-noted candidates:
- Self-hosted integration testing (wire mnc-stage1 into the harness)
- Optimizer improvements (raise the 47/59 pass rate)
- Structured concurrency (`spawn` + `join` in async)
- v5.0.0 preparation (tag, migration guide, breaking changes)

The cadence continues. The discipline holds.
