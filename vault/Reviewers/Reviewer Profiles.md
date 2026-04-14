---
aliases: [Reviewers, Panel]
---

# Reviewer Profiles

Seven AI reviewers grade every panel release. Each has a domain lens.

## [[Rattler]] — LLVM / Codegen (PRIMARY)

- **Focus**: IR correctness, codegen quality, optimization pass interactions
- **Tendency**: Most technically rigorous. Catches CRITICAL bugs.
- **Score range**: 6.5 - 9.5
- **Key calls**: Tagged-pointer exploitation at -O2, optimization ROI was zero

## [[Viper]] — Memory Safety

- **Focus**: Thread safety, lifetimes, leaks, UB
- **Tendency**: High volatility. Flags issues others miss.
- **Score range**: 5.5 - 9.5
- **Key calls**: Coroutine frame coupling, tagged-pointer confirmed UB

## [[Anaconda]] — Toolchain / CI

- **Focus**: Pipeline integration, CI gates, build system
- **Tendency**: Flags missing integration tests every panel since Arc 3
- **Score range**: 6.5 - 9.3
- **Key calls**: 0/61 golden pass, async can't link, no sanitizer CI

## [[Cobra]] — C++ / ABI

- **Focus**: Calling conventions, struct layout, fixed-point convergence
- **Tendency**: Structural soundness. Stable across arcs.
- **Score range**: 6.5 - 9.8
- **Key calls**: Byref size heuristic divergence, dissent on tagged-pointer characterization

## [[Coral]] — Language Design

- **Focus**: Grammar coherence, spec compliance, feature completeness
- **Tendency**: Honest on gaps. First 10/10 ever at v4.76.0.
- **Score range**: 7.5 - 10.0
- **Key calls**: else/sino not verified, closure type gaps, keyword collision

## [[Boa]] — Developer Experience

- **Focus**: Documentation, error messages, onboarding
- **Tendency**: Flags doc gaps consistently. Most sensitive to user-facing issues.
- **Score range**: 7.5 - 9.95
- **Key calls**: No async cookbook (3 arcs), binary corruption undisclosed

## [[Mamba]] — C Runtime

- **Focus**: Allocation patterns, thread safety, runtime quality
- **Tendency**: Pragmatic on tradeoffs. Identified string pathology in Arc 4.
- **Score range**: 6.1 - 9.6
- **Key calls**: Tagged-pointer fix is 3-4 hours, string concat O(n^2), scheduler exists in source
