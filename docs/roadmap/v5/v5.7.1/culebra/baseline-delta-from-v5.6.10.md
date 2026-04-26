# v5.7.1 Culebra Baseline — Delta vs v5.6.10

Generated as the **v5.8.0 panel-input baseline**. v5.7.1 is a
docs/polish release with **no compiler edits**, so the only
material drift between v5.6.10 and v5.7.1 stage2.ll is the
shipping of the v5.6.11 + v5.6.12 + v5.6.13 + v5.7.0 closures
that took place between the two cuts.

## Methodology

Same as v5.6.10 — Culebra v2.4.0 (Windows PE32+ binary running
through WSL interop, Windows-style paths required). Per the
v5.6.10 SESSION_REPORT, full `triage` on a 217k-line stage2.ll
takes ~7-8 minutes; `triage --brief` and `baseline save` are
the only commands fast enough to run on every release.

## stage2.ll metrics

| Metric | v5.6.10 | v5.7.1 | Delta |
|---|---:|---:|---:|
| Lines | 216,932 | 217,879 | +947 (+0.44%) |
| `llvm-as` | clean | clean | unchanged |
| `__mn_list_new(i64 384)` sites | 7 | 0 | −7 (Ve.2 CLOSED v5.6.12) |
| Total culebra findings | 15,755 | 15,829 | +74 (+0.47%) |
| Critical findings | 2 | 2 | unchanged |
| High findings | 3 | 3 | unchanged |
| Goldens | 64/66 | **66/66** | +2 (Sh.7 + B CLOSED v5.7.0) |
| Self-host fixed-point | regressed (Ve.4) | NEAR | Ve.4 CLOSED v5.6.11 |

## Triage brief — root causes

```
v5.6.10: 5 root causes, 15755 findings: 2 critical (function-count-drop, return-type-divergence), 3 high
v5.7.1:  5 root causes, 15829 findings: 2 critical (function-count-drop, return-type-divergence), 3 high
```

**No NEW critical findings.** Same 5-root-cause shape; the +74
delta is text-pattern noise from the closure-typed-parameter +
or-pattern + destination-passing changes between v5.6.11 and
v5.7.0. Both critical groups (`function-count-drop` /
`return-type-divergence`) are the same known false-positive
classes documented in v5.6.9 SESSION_REPORT.

## Struct health — Mapanare-major aggregates

| Struct | Result |
|---|---|
| Value | clean — no struct health issues |
| MIRType | clean — no struct health issues |
| EmitState | clean — no struct health issues |
| LowerState | clean — no struct health issues |
| Instruction | clean — no struct health issues |

(`culebra health --struct-name <S>` against
`stage2_v5.7.1.ll`.) Five most-touched structs across the
v5.6.x → v5.7.0 arc; none has accumulated PHI-zeroinit /
type-pun / null-load patterns despite the heavy emitter
churn (Sh.4/6/7 closures + drop-glue infrastructure +
destination passing).

## Closures absorbed since v5.6.10

The line-count delta (+947) is small because v5.6.10 → v5.7.1
shipped both _additive_ (Sh.7 closure-typed parameters,
v5.6.4 tensor drop-glue plumbing baked in earlier) and
_subtractive_ (Ve.2 floor closure −431 lines from v5.6.12;
duplicate alloca elimination from Lk.1 destination-passing)
changes that nearly cancel.

| Release | Net stage2.ll | Closure |
|---|---:|---|
| v5.6.10 | 216,932 | (baseline anchor) |
| v5.6.11 | 217,273 | +341 — Ve.4 (elem_size stride fix in `emit_index_get`/`_set`) |
| v5.6.12 | 216,842 | −431 — Ve.2 + Lk.1 (destination passing in `lower_let`) |
| v5.6.13 | 217,268 | +426 — Layer 1 cleanup (struct let-bindings via destination passing) |
| v5.7.0 | 217,879 | +611 — Sh.7 (closure-typed) + B (or-pattern) |
| v5.7.1 | 217,879 | 0 — docs polish, no compiler edits |

## Conclusions

1. **No NEW critical findings vs v5.6.10**. All 5 root-cause
   classes present at v5.6.10 are present at v5.7.1 in
   essentially the same shape.
2. **Both critical findings are known false positives** —
   documented in `docs/guides/culebra.md` §3 and the v5.6.9
   SESSION_REPORT. They flag aggregate-return runtime
   declarations and Python-vs-self-hosted function-count
   drift, neither of which is a real correctness signal.
3. **Struct health clean** for all 5 most-touched aggregates
   despite v5.6.4 → v5.7.0 emitter churn — a strong signal
   that the v5.6.x drop-glue arc + v5.7.0 closure-typed
   plumbing didn't introduce silent corruption.
4. **66/66 goldens** under stage2.ll = 217,879 lines —
   first all-pass corpus the project has ever shipped.

## Recommendations for v5.8.0 panel

1. **Use this baseline as the anchor.** `baseline-end.json`
   captures the exact 15,829 findings the panel will see; any
   v5.8.0 review can `culebra baseline diff` against it to
   surface only what _actually_ changed.
2. **Read `arc-journal.jsonl`** (189 entries, v5.6.9 +
   v5.6.10 + v5.7.0 culebra journals concatenated) for the
   debugging methodology that closed Ve.3 / Ve.4 / Lk.1 /
   Sh.7 / B.
3. **The two critical findings are not bugs.** Don't grade
   them as such. See `docs/guides/culebra.md` for the
   false-positive policy.
