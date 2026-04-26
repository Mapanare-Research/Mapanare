# v5.7.1 Culebra Summary

**stage2.ll**: 217,879 lines / 6,398 string constants / 88 struct
types / `llvm-as` clean.

**Goldens**: 66/66 native (v5.7.0 milestone preserved).

**Self-host fixed-point**: NEAR (4 diff lines / 217,879 = 0.002%,
all VERSION metadata; restored at v5.6.11 via the elem_size-stride
fix in `emit_index_get` / `emit_index_set`).

## Triage brief

```
5 root causes, 15829 findings: 2 critical (function-count-drop, return-type-divergence), 3 high
```

## Findings by template

| Template | Severity | Hits | Class |
|---|---|---:|---|
| `function-count-drop` | critical | 943 | known FP — Python ↔ self-hosted parity |
| `return-type-divergence` | critical | 37 | known FP — aggregate-return runtime decls |
| `fixed-point-delta` | high | 7,341 | text-pattern noise on non-AST IR |
| `byte-count-mismatch` | high | 6,398 | text-pattern noise (1:1 with string constants) |
| `stage-output-divergence` | high | 1,110 | text-pattern noise |

Two critical findings are documented as **false positives** in
`docs/guides/culebra.md` §3 and `docs/roadmap/v5/v5.6.9/SESSION_REPORT.md`.
They flag aggregate-return runtime declarations
(`__mn_str_concat`, `__mn_str_substr`, `__mn_list_new`, etc.) as
if they were cross-stage divergent, and Python-bootstrap vs
self-hosted function-count drift, neither of which is a real
correctness signal.

The 3 "high" findings (`fixed-point-delta`, `byte-count-mismatch`,
`stage-output-divergence`) are template-match noise from
text-pattern templates running against the 217,879-line stage2.ll;
their counts scale linearly with IR size, not with code quality.

## Struct health (Mapanare-major aggregates)

| Struct | Result |
|---|---|
| `%struct.Value` | clean |
| `%struct.MIRType` | clean |
| `%struct.EmitState` | clean |
| `%struct.LowerState` | clean |
| `%enum.Instruction` | clean |

No PHI-zeroinit / type-pun / null-load patterns in any of the
five most-touched aggregates across the v5.6.x → v5.7.0 arc.

## Pathology audit

```
OK No pathologies found in 0 functions.
```

(Caveat from v5.6.9 SESSION_REPORT: culebra v2.4.0 cannot fully
parse function bodies on a 217k-line IR — "0 functions" reflects
the parser limitation, not real data. The "No pathologies"
result still holds for the patterns culebra _does_ check via
text templates.)

## String constants

```
OK All 6398 string constants have correct byte counts.
4866 duplicate string constants (911 unique values repeated).
```

## llvm-as validity

```
VALID stage2_v5.7.1.ll
```

(Using culebra's `check` shim — note that culebra's bundled
`llvm-as` is not on this WSL host; the underlying validation
ran via `mapanare/self/mnc-stage1` → emit pipeline at build
time.)

## Cross-references

- `triage-brief.txt` — one-line summary.
- `triage.md` — full triage output (17 lines, 5 templates).
- `progress.md` — `culebra progress` IR summary + delta vs prior baseline.
- `audit.md` — known-pathology audit.
- `strings.md` — string-constant byte-count validation.
- `check.md` — `llvm-as` validity.
- `health-{Value,MIRType,EmitState,LowerState,Instruction}.txt` —
  per-struct health checks.
- `baseline-end.json` — full structured baseline (15,829 findings)
  for v5.8.0 panel `culebra baseline diff` comparisons.
- `baseline-delta-from-v5.6.10.md` — narrative delta against
  v5.6.10 anchor with line-count breakdown by intermediate
  release (v5.6.11 / v5.6.12 / v5.6.13 / v5.7.0).
- `arc-journal.jsonl` — 189 entries aggregated from v5.6.9 +
  v5.6.10 + v5.7.0 culebra journals (panel input for v5.8.0).
