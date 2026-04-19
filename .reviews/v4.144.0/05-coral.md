# Coral -- v4.144.0 language design review

**Score: 8.9/10**
**Grade: MEETS**
**Prior (v4.143.0): 8.5/10 MEETS**
**Delta: +0.4**

---

## Executive summary

v4.144.0 is a narrow release -- five Cobra carry-forward items (Cb.5-tests,
Cb.6, Cb.7, Cb.9a, Cb.10) and a benchmark recalibration that finally tells
the truth about the Rust comparison. No grammar changes, no new primitives,
no SPEC rewrites. The kind of release that moves the needle only if every
prior release set the table for it.

Every prior release did.

My four carry-forward items from v4.143.0 -- Sp.1, Co.1r, Sem.2, Gr.3 --
were all CLOSED *at v4.143.0 itself*, before this release cycle even started.
v4.144.0 inherits those closures. I verified each:

- **Sp.1** (SPEC Python-backend ghost): the four sites at lines 25/37/39/1792
  that I flagged at v4.143.0 are rewritten. The remaining mentions of
  "Python" in the SPEC at lines 39 and 1798 are correctly marked as removed
  features with version tags and canonical-path redirects. The SPEC no longer
  pretends the Python transpiler exists. **Holds.**

- **Co.1r** (SPEC fixed-point wording): Appendix B now says "3-stage fixed
  point" without the "byte-identical" assertion. It names the v4.134.0
  strict checkpoint, the Dr.1 near-fixed-point regime with its bounded
  4-line version-metadata diff, and cites the v4.142.0 md5s honestly. The
  `DIFF_THRESHOLD=100` ratchet is documented. This is the wording I asked
  for at v4.143.0. **Holds.**

- **Sem.2** (E420 diagnostic frame): `parse_recovering` now catches
  `ParseError` from the Lark transformer. Confirmed in the CARRY_FORWARD
  ledger. **Holds.**

- **Gr.3** (`Tensor` keyword collision): the stdlib struct was renamed from
  `Tensor` to `GpuTensor` in `stdlib/gpu/tensor.mn` (63 sites) and
  `kernel.mn` (3 sites). `TensorError` preserved. I verified the source:
  `pub tipo GpuTensor { ... }` at tensor.mn:85, `tensor.GpuTensor` at
  kernel.mn:167/187/207. The `KW_TENSOR` keyword no longer collides with
  user type names in generic position. Coral's Option 2 from v4.143.0,
  executed cleanly. **Holds.**

Four items, four closures, four verified. My carry-forward is empty for the
first time since I started reviewing this project at v4.99.0.

That alone would justify a positive delta. But the benchmark story is what
earns the real credit this cycle.

---

## The benchmark correction: an act of intellectual honesty

At v4.135.0, the README said "1.12x of Rust (within noise)." At v4.143.0,
I flagged this as Mar.1 -- the Rust geomean of 11.769 ms was suspicious,
likely a harness artifact. Bn.1 (v4.143.0) instrumented all 10 Rust
benchmarks with internal `std::time::Instant` wall timing to eliminate the
subprocess-spawn tax that had been inflating Rust's numbers.

The corrected comparison at v4.144.0: **Mapanare is 5.83x slower than Rust.**

Not 1.12x. 5.83x. A factor-of-five correction.

The `FINAL_REPORT_v4.144.md` handles this with exemplary candor:

> The v4.135.0 "Mapanare 1.12x of Rust" was an artifact of the harness
> tax. The corrected comparison at v4.144.0 shows Mapanare is 5.83x slower
> than Rust across the 6-workload corpus.

Per-workload, the honest numbers tell a more nuanced story:

- `fib_recursive`: 0.98x of Rust (parity -- LLVM inliner handles both
  similarly)
- `prime_sieve`: 1.94x (respectable for a young compiler)
- `enum_match`: 5.47x (was 2.3x at v4.125.0 -- the gap "widened" only
  because Rust's real wall is 0.296 ms, not the spawn-inflated 10 ms)
- `quicksort`: 5.76x
- `string_concat`: 36x (Rust `String::push_str` is pre-allocated; fair
  comparison would use arena concat)
- `struct_alloc`: 70.47x (Rust stack-allocates; Mapanare heap-allocates +
  drop-glue -- ABI.1 gap, acknowledged)

This is the kind of honesty that builds trust with the systems-programming
audience Mapanare is courting. A language that says "we are 5.83x slower
than Rust on the geometric mean, here is why per-workload, here is the
perf arc that targets closing it" is more credible than one that says "we
are within noise of Rust" when the measurement methodology is flawed.

**However**: the README still cites the old numbers.

Line 397: `**1.12x of Rust (within noise)**`
Line 398: `**4.86x slower than C (gcc -O2)**`

These are the v4.136.0 numbers that predated Bn.1. The `FINAL_REPORT_v4.144.md`
corrects the Rust number to 5.83x and the C number to 4.57x. The README
points to `FINAL_REPORT_v4.136.md` for methodology -- a file that contains
the pre-Bn.1 data.

This is not malice. It is the same drift pattern I have been flagging since
v4.114.0: the internal evidence pack is updated, the external-facing document
is not. The benchmark table at README lines 408-415 still shows Rust's
`fib_recursive` as 17.32 ms when the corrected number is 21.163 ms, Rust's
`quicksort` as 1.94 ms when the corrected number is 0.414 ms, and so on.

The lead disclosed the correction in the right file. The lead did not
propagate it to the file that matters -- the one a prospective user reads
before deciding to try the language.

I am opening **Mar.1r** (README benchmark numbers stale vs FINAL_REPORT
v4.144.0) as a LOW carry-forward. The fix is a 15-minute copy-paste. The
severity is LOW because the internal report is honest and linked from the
README. But it is a flag because this is the second panel cycle where the
README benchmark section diverges from the evidence pack.

---

## Cb.9a: the right kind of deferral

The `semantic.mn` docstring at lines 517-530 is exactly what I want to see
when a feature gap is deferred rather than hidden:

```
// Cb.9a (v4.144.0): The Python semantic resolver at semantic.py:416-445
// handles qualified type references (e.g., device.DeviceKind) via a
// module_path list on NamedType/GenericType AST nodes. The self-hosted
// AST uses a flattened string ("device.DeviceKind") in TypeExpr::Named,
// so resolve_type_expr below passes the dotted name to make_type() as-is.
// This works for struct fields (the name round-trips through the emitter)
// but will silently mis-classify if someone does `match` on a qualified
// enum. Full cross-module type resolution requires adding a module_path
// field to TypeExpr and mirroring the Python resolver's import-scope
// lookup. Tracked as Cb.9a for v5.x.
```

It names the gap. It names the specific failure mode ("silently
mis-classify if someone does `match` on a qualified enum"). It names the
fix ("adding a module_path field to TypeExpr"). It names the tracking
version. It does not pretend the feature works.

This is acceptable for v5.0.0. The self-hosted semantic checker is not yet
the production path -- the Python bootstrap is. The gap is documented, the
failure mode is narrow (qualified enum match, not qualified type use in
general), and the tracking is explicit. When this is eventually ported, the
docstring will tell the implementer exactly what to do.

---

## The near-fixed-point at 110,127 lines

The SPEC Appendix B cites "109,872 lines at v4.142.0" and the v4.142.0
md5s. The v4.144.0 BASELINE.md reports 110,127 lines with new md5s
(`436d34e...` / `612b352...`). The line count grew by 255 lines (+0.23%) --
consistent with the Cb.7 clear-after-transfer code and the Cb.6 guard
addition in the self-hosted emitter.

The SPEC wording itself is honest: it says "109,872 lines at v4.142.0" --
a dated snapshot, not a claim of current state. But it should be refreshed
to cite the v4.144.0 numbers. This is cosmetic, not a finding -- the SPEC
structure Appendix B uses (dated version checkpoints) is the right
approach. I note it as a minor housekeeping item, not a docket.

---

## The AI-native claim revisited

At v4.143.0 I flagged a demo gap: three of four flagship primitives had
no working example in the repo. The situation at v4.144.0:

| Primitive | Runtime real? | Golden test? | Example runs? | Change since v4.143.0 |
|---|---|---|---|---|
| Agent | Yes | No | `chat_agent.mn` fails Gr.1 | unchanged |
| Signal | Yes | No | none found | unchanged |
| Stream | Yes | Indirect (async) | `async_file_io.mn` OK | unchanged |
| Tensor | Yes | Yes (x4) | `matrix_ops.mn` fails Gr.1 | unchanged |

No change. Gr.1 (multi-line collection literals) is still open. The signal
demo gap persists. v4.144.0 did not target these -- it was a Cobra
carry-forward release, not a demo polish release.

I am not docking for the unchanged state. The demo gap was already
accounted for in my v4.143.0 score. What I credit instead is that Gr.3's
closure (the `GpuTensor` rename) means `stdlib/gpu/tensor.mn` is now one
step closer to compiling -- the keyword collision that was the *first*
parse error is gone. Whether the remaining errors in that file are Gr.1
or something else is future-release scope.

The AI-native pitch remains what it was at v4.143.0: four real primitives,
three demonstrable, one (signals) with no demo. The story holds for v5.0.0
because the language surface is complete and the runtime is real. The demo
surface is a polish question, not a design question.

---

## What v4.144.0 credits

1. **Cb.5-tests (34 tests, 358 lines)**: The enum inline optimization
   that v4.140.0 ported from Python to self-hosted now has dedicated
   unit tests covering eligibility, type predicates, pack/unpack, IR
   shape, and ABI parity. This is the kind of test coverage Rattler and
   Cobra asked for at v4.143.0. The PRE_PANEL_AUDIT verified all 34 pass.

2. **Cb.6 (trailing-`*` typed-pointer guard)**: A single-site guard in
   `emit_llvm.mn:753-756` that rejects typed pointers (`i64*`) in the
   self-hosted emitter's inline-slot eligibility check. The asymmetry
   with the Python emitter (which accepts them for legacy compatibility)
   is explicitly documented in the audit. This is thoughtful divergence
   management between the two emitter paths.

3. **Cb.7 (clear-after-transfer in monomorphization)**: The pattern from
   v4.142.0's Ge.1 `try_monomorphize_enum` is now mirrored in
   `try_monomorphize_struct`. The audit honestly documents why the
   `register_struct` / `register_enum` sites could not be similarly
   treated (the reassignment triggers drop-glue on the transferred
   buffer). This is filed as Own.1 and deferred to v5.x move-semantics
   work. Honest.

4. **Benchmark recalibration**: The Bn.1 harness correction propagated
   to a full benchmark refresh with honest per-workload analysis and an
   explicit correction of the v4.135.0 "1.12x of Rust" claim.

5. **Zero regressions**: 5,187 passed / 0 failed. Goldens 54/66. Fixed
   point holds at NEAR FIXED POINT. All quality gates clean.

---

## New / residual findings

### Mar.1r -- README benchmark numbers stale vs FINAL_REPORT v4.144.0 (LOW)

README line 397 says "1.12x of Rust (within noise)" and "4.86x slower
than C." `FINAL_REPORT_v4.144.md` says 5.83x slower than Rust and 4.57x
slower than C. The benchmark table at lines 408-415 shows pre-Bn.1 Rust
numbers (e.g., `fib_recursive` 17.32 ms vs corrected 21.163 ms). The link
at line 402 points to `FINAL_REPORT_v4.136.md`, not `v4.144.md`.

This is a 15-minute fix: update the paragraph, the table, and the link.
LOW because the internal report is honest and discoverable. But the
front-page story should match the evidence.

### SPEC Appendix B line count stale (housekeeping, not a docket)

SPEC cites "109,872 lines at v4.142.0"; v4.144.0 is 110,127 lines. The
dated citation style is correct -- just refresh the numbers when the SPEC
header bumps.

### Demo gap (unchanged from v4.143.0, already scored)

Signals have no demo. Agent and tensor examples fail Gr.1 (multi-line
collection literals). Unchanged from prior review. Not docking again.

---

## Carry-forward for v5.0.0

| Docket | Severity | Source | Action |
|---|---|---|---|
| **Mar.1r** -- README benchmark numbers cite v4.136.0 pre-Bn.1 data ("1.12x of Rust"); v4.144.0 honest number is 5.83x | LOW | this review | Update paragraph, table, link in README |
| **Demo gap** -- no golden/example for signals; agent + tensor examples fail Gr.1 | LOW | v4.143.0 review | One signal example; fix Gr.1 or rewrite demos to single-line |
| **Gr.1** -- Multi-line collection literal grammar | LOW | v4.129.0 | Grammar work in `mapanare.lark` |
| **Cb.9a** -- Self-hosted `semantic.mn` lacks `module_path` (documented gap) | LOW | v4.144.0 (Cobra) | v5.x AST change |
| **Own.1** -- Self-hosted lowerer lacks compile-time move-semantics enforcement | LOW | v4.143.0 (Viper) | v5.x refactor |

All items are LOW. Zero MEDIUM. Zero HIGH. Zero CRITICAL.

---

## Verdict

**MEETS.** The language surface continues to be ready for v5.0.0. My four
carry-forward items are all closed. The benchmark correction demonstrates
the kind of intellectual honesty that earns trust with the audience this
language is for. The Cobra carry-forward items were closed with care --
the Cb.9a docstring in particular is a model for how to defer work without
hiding it.

The **+0.4** is for:

- **+0.15** for all four Coral carry-forward items verified closed. Sp.1
  (SPEC Python ghost), Co.1r (fixed-point wording), Sem.2 (E420 diagnostic),
  Gr.3 (Tensor keyword collision) -- all closed at v4.143.0, all verified
  holding at v4.144.0. My queue is empty for the first time.

- **+0.15** for the benchmark honesty. Correcting "1.12x of Rust" to
  "5.83x of Rust" in the evidence pack, with per-workload analysis and an
  explicit harness-artifact disclosure, is the right thing to do. Harder
  than leaving the flattering number in place. More valuable to the
  project's credibility.

- **+0.10** for clean execution on Cobra's carry-forward. Cb.5-tests
  (34 unit tests), Cb.6 (typed-pointer guard with documented emitter
  asymmetry), Cb.7 (clear-after-transfer with honest Own.1 limitation
  disclosure), Cb.9a (the model docstring), Cb.10 (golden docstring
  correction). Five items, five closures or honest deferrals.

- **-0.05** for Mar.1r: the README still cites "1.12x of Rust." The
  internal report is honest. The external-facing document is not updated.
  This is the same drift pattern I have flagged since v4.114.0 -- internal
  evidence advances, the front page lags. A 15-minute fix that should not
  survive another release cycle.

- **+0.05** rounding: the overall quality of the release -- zero
  regressions, 5,187 tests passing, clean gates, honest documentation
  of limitations -- merits a slight upward adjustment.

---

## Score history

| Version | Score | Grade | Delta |
|---|---|---|---|
| v4.99.0 | 7.5 | RESERVATIONS | -- |
| v4.114.0 | 8.3 | PASS WITH NOTES | +0.8 |
| v4.120.0 | 8.1 | PASS WITH NOTES | -0.2 |
| v4.136.0 | 8.7 | MEETS | +0.6 |
| v4.143.0 | 8.5 | MEETS | -0.2 |
| **v4.144.0** | **8.9** | **MEETS** | **+0.4** |

The trajectory has recovered from the v4.143.0 dip. The dip was real --
I flagged SPEC drift and a keyword collision that prior audits missed.
Both are now closed. The correction itself (four items closed in one
release, benchmark honesty in the next) is the strongest evidence that the
panel process works as a correction mechanism.

8.9 is one-tenth below the 9.0 threshold. The gap is the README benchmark
drift and the signal demo absence -- both fixable in hours, not days. If
the aggregate across the seven reviewers clears 9.0, this will not be the
vote that blocks v5.0.0.

---

## Reproducibility

```bash
# Sp.1 closure verification (SPEC Python ghost)
grep -n "Python transpiler\|Python backend\|transpiles to Python" docs/SPEC.md
# Expected: line 39 (marked as removed v4.58.0), line 1798 (marked as removed v4.29.0)

# Co.1r closure verification (fixed-point wording)
grep -n "byte-identical\|near fixed point\|NEAR FIXED" docs/SPEC.md
# Expected: Appendix B uses "near fixed point" language

# Sem.2 closure (in CARRY_FORWARD.md)
grep "Sem.2" .reviews/CARRY_FORWARD.md
# Expected: CLOSED v4.143.0

# Gr.3 closure (GpuTensor rename)
grep -c "GpuTensor" stdlib/gpu/tensor.mn    # Expected: ~30+
grep -c "^pub tipo Tensor" stdlib/gpu/tensor.mn  # Expected: 0

# Cb.9a docstring
sed -n '517,530p' mapanare/self/semantic.mn

# Benchmark honesty
grep "1.12" README.md                        # Still there (Mar.1r)
grep "5.83" benchmarks/FINAL_REPORT_v4.144.md  # Corrected number

# Signal demo gap
grep -rl "^signal\|signal(" examples/ tests/golden/  # Expected: empty

# Cb.5-tests
pytest tests/llvm/test_enum_inline.py -v    # Expected: 34 passed
```
