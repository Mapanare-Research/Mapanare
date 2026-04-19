# v4.153.0 Docket Ledger — v4.144.0 -> v4.152.0

## Summary

| Metric | Count |
|---|---:|
| Opened in arc | 3 |
| Closed in arc | 0 |
| Open at v4.153.0 | 8 |
| — CRITICAL | 0 |
| — HIGH | 0 |
| — MEDIUM | 0 |
| — LOW | 8 |

The perf arc (v4.144.0-v4.152.0) focused on experiments, not docket
closure. No existing dockets were closed. Three new LOW dockets were
opened by E8 (dormant pass re-evaluation).

## Dockets opened in arc

| ID | Opened | Severity | Description | Evidence |
|---|---|---|---|---|
| In.1 | v4.152.0 | LOW | Self-hosted MIR inliner rename bug — caller destination register not renamed after inlining | `docs/roadmap/v4/v4.152.0/RESULTS.md` |
| Li.1 | v4.152.0 | LOW | Self-hosted LICM hoist_instruction leaves instruction in source block | `docs/roadmap/v4/v4.152.0/RESULTS.md` |
| Ea.1 | v4.152.0 | LOW | Self-hosted escape_analysis is a stub — no codegen path | `docs/roadmap/v4/v4.152.0/RESULTS.md` |

## Open dockets at v4.153.0

| ID | Opened | Severity | Description |
|---|---|---|---|
| Sh.4 | v4.120.0 | LOW | Feature-gap: mutable views |
| Sh.5 | v4.120.0 | LOW | Feature-gap: stepped slices |
| Sh.6 | v4.120.0 | LOW | Feature-gap: tensor reshape |
| Sh.7 | v4.120.0 | LOW | Feature-gap: advanced closures |
| Sh.9a | v4.120.0 | LOW | Feature-gap: async in self-hosted |
| In.1 | v4.152.0 | LOW | Self-hosted inliner rename bug |
| Li.1 | v4.152.0 | LOW | Self-hosted LICM hoist duplicate |
| Ea.1 | v4.152.0 | LOW | Self-hosted escape analysis stub |

All 8 open dockets are LOW severity. Zero CRITICAL, HIGH, or MEDIUM
on the ledger.

## Total ledger (since v4.99.0)

- 66 dockets opened (63 pre-arc + 3 in arc)
- 58 closed (all pre-arc)
- 8 open (all LOW)
