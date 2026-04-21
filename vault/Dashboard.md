---
aliases: [Home, MOC]
---

# Mapanare Knowledge Vault

## Current State

| Field | Value |
|-------|-------|
| **Version** | `4.108.0` |
| **Branch** | `dev` |
| **Last Panel** | [[v4.99.0]] — 6.59/10 (3 NEEDS WORK) |
| **Next Panel** | [[v4.106.0]] — "Does the native binary work?" |
| **v5 Status** | Not tagged. Option B: continue v4.100.0+ |
| **Golden Tests** | 62 programs (16/62 passing mnc-stage1 as of v4.101.0) |
| **Total Tests** | 5,374 pytest |

## Active Docket (v4.99.0 Panel)

| # | Item | Severity | Fix Version | Status |
|---|------|----------|-------------|--------|
| 1 | [[tagged-pointer-ub]] | CRITICAL | [[v4.100.0]] | Partial (UB removed, corruption was separate) |
| 2 | [[list-indexing-bug]] | CRITICAL | [[v4.101.0]] | Fixed (move-semantics gap, 6 sites) |
| 3 | [[async-linking]] | HIGH | [[v4.102.0]] | Planned |
| 4 | [[else-sino-verification]] | HIGH | [[v4.103.0]] | Planned |
| 5 | [[closure-type-annotations]] | HIGH | [[v4.103.0]] | Planned |
| 6 | [[binary-corruption-disclosure]] | MEDIUM | [[v4.108.0]] | Planned |
| 7 | [[byref-size-heuristic]] | MEDIUM | [[v4.112.0]] | Planned |
| 8 | [[coroutine-frame-coupling]] | MEDIUM | [[v4.113.0]] | Planned |
| 9 | [[string-concat-perf]] | MEDIUM | [[v4.108.0]] | Planned |
| 10 | [[keyword-collision-spec]] | LOW | [[v4.113.0]] | Planned |
| 11 | [[async-error-messages]] | LOW | [[v4.113.0]] | Planned |

## Release Phases (v4.100.0 -> v4.120.0)

| Phase | Versions | Theme | Panel |
|-------|----------|-------|-------|
| **A** Bug Sprint | [[v4.100.0]] - [[v4.103.0]] | Critical docket fixes | -- |
| **B** Rebuild + Verify | [[v4.104.0]] - [[v4.106.0]] | Golden 64/64, valgrind, ASan | [[v4.106.0]] |
| **C** Benchmark Truth | [[v4.107.0]] - [[v4.110.0]] | Go+C benchmarks, string fix, opt ROI | -- |
| **D** Self-Hosted + Testing | [[v4.111.0]] - [[v4.114.0]] | Fixed-point, medium items | [[v4.114.0]] |
| **E** Polish + Docs | [[v4.115.0]] - [[v4.117.0]] | Async I/O, docs, sanitizer CI | -- |
| **F** Gate | [[v4.118.0]] - [[v4.120.0]] | Final benchmark, retrospective | [[v4.120.0]] |

## Panel Score Trajectory

```
v3.47.0  9.79  -- baseline
v4.26.0  8.20  -- CRISIS (4 NEEDS WORK, 6 hollow features)
v4.31.0  9.34  -- recovery
v4.36.0  9.50  -- peak (Arc 1)
v4.41.0  9.36  -- Arc 2
v4.46.0  8.99  -- Arc 3
v4.51.0  8.90  -- Arc 4
v4.56.0  9.00  -- Arc 5
v4.61.0  8.71  -- Arc 6
v4.66.0  7.71  -- Arc 7 (lowest non-crisis)
v4.71.0  8.29  -- Arc 8
v4.76.0  8.86  -- Arc 9 (first 10/10 ever)
v4.99.0  6.59  -- v5 gate FAIL
```

## Quick Links

- [[Benchmarks Overview]] — performance across versions
- [[Reviewer Profiles]] — 7 reviewers, focus areas, score trends
- [[Architecture Decisions]] — key ADRs
- Roadmap: `docs/roadmap/ROADMAP.md`
- Reviews: `.reviews/`
- Carry-forward: `.reviews/CARRY_FORWARD.md`

## Tags

`#critical` `#high` `#medium` `#low` `#panel` `#benchmark` `#decision` `#bug` `#fixed` `#open` `#phase-a` `#phase-b` `#phase-c` `#phase-d` `#phase-e` `#phase-f`
