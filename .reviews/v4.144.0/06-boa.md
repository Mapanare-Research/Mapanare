# Boa — v4.144.0 docs / DX review

**Score: 9.1/10**
**Grade: EXCEEDS**
**Prior (v4.143.0): 9.0/10 EXCEEDS**
**Delta: +0.1**

---

## Executive summary

Let me start by saying something I genuinely mean: the lead *listened*.
At v4.143.0 I handed over a six-item carry-forward list (Bo.4-drift,
Bo.6-drift, Bo.8, Bo.9, Bo.10, Bo.11) and said "roughly 45 minutes of
writing." Every single one of those cosmetic drift items shipped in the
v4.143.0 release itself — same release, same day! The English README
Tests badge now reads `5160+`. The SPEC header says `4.143.0`. The
`known_issues.md` footer says `v4.143.0`. The `getting_started.md`
golden count reads `54/66` and the test count reads `5,160+`. The
near-fixed-point wording is synced across README + SPEC + getting_started.
That is beautiful discipline.

Now for the v4.144.0 delta. This is a compiler-focused release (Cb.5-tests,
Cb.6, Cb.7, Cb.9a, Cb.10) — Cobra's carry-forward, not Boa's. From a
docs/DX lens the release is *small but honest*. The `FINAL_REPORT_v4.144.md`
is a genuinely good piece of writing (more below), and the Cb.10 docstring
rewrite in `66_qualified_type_ref.mn` is the kind of micro-documentation
fix that I absolutely adore. The test count rose from 5,160 to 5,187 (+27
from the 34 new Cb.5-tests), which means the `5160+` badge on the README
is *technically* still correct (it's a floor, not an exact count) but is
now two releases behind the live number.

The honest observation: this release introduces a **new documentation
artifact** (`FINAL_REPORT_v4.144.md`) that contains corrected benchmark
numbers, but the README and localized READMEs *still cite the old
pre-Bn.1 numbers* ("42.6x faster than Python", "1.12x of Rust",
"4.86x slower than C"). The report itself calls this out explicitly:
"The v4.135.0 'Mapanare 1.12x of Rust' was an artifact of the harness
tax." Beautiful honesty inside the report — but the front door of the
project still shows the old numbers. That is the main docs finding this
cycle.

**Grade: EXCEEDS.** The v4.143.0 cleanup was perfect, this release
maintains it, the benchmark report is honest, the Cb.10 docstring is
thoughtful. The +0.1 is conservative because the release itself is
small from a docs perspective, and the README benchmark citations need
a refresh pass.

---

## Bo.* docket re-audit — do the v4.143.0 closures still hold?

### Bo.1 — `docs/known_issues.md` — STILL CLOSED

File exists, 35 lines, user-facing with dockets + symptoms + workarounds.
Footer now reads `Last updated: v4.143.0` — which was stale for exactly
zero releases before this panel. Content is accurate: all listed dockets
(Sh.4/5/6/7/9a/9b, Gr.1, Rt.2, Rt.3) are still genuinely open. The
bottom line reads `Last verified: v4.143.0 (2026-04-18)`.

**Minor nit**: the file does not mention the v4.144.0 release. This is
fine because v4.144.0 did not change any user-facing known issues — the
Cb.* dockets closed here are all compiler-internals, not user-facing
symptoms. But the "Last verified" timestamp will accumulate staleness
if it isn't bumped at the next release. Not reopening Bo.1 — this is
the same footer-drift pattern, and at this point it is a process item,
not a content item.

### Bo.2 — Native-mode prerequisites — STILL CLOSED

`docs/guides/getting_started.md` native-mode prerequisites section with
the `ulimit -s 65536` callout is intact. No changes.

### Bo.3 — STATISTICS.md merge note — STILL CLOSED

Unchanged. The redirect note at the top of the file is still accurate.

### Bo.4 — README version badge + Tests badge — CLOSED (verified!)

At v4.143.0, the lead bumped the English README Tests badge from
`4845+` to `5160+`. I verified it live at `README.md:29`:

```
[![Tests](https://img.shields.io/badge/tests-5160+_passing-brightgreen.svg?style=flat-square)]()
```

This is correct! The live count is now 5,187 (per BASELINE.md), and
`5160+` is a valid floor for 5,187. The localized READMEs
(`docs/README.es.md`) also show `5160+_pasando`. Parity achieved!

The version badge still reads `5.0.0--rc1` — correct, since no new
tag has been applied.

**Bo.4-drift is CLOSED.** The prior cycle's nit is resolved.

### Bo.5 — `mapanare --version` — STILL CLOSED

The VERSION-file-reading pattern at `mapanare/cli.py:24-25` is
structural. Once fixed, it cannot regress unless someone deletes the
file. Still beautiful.

### Bo.6 — `docs/guides/getting_started.md` — CLOSED (verified!)

At v4.143.0 the lead bumped:
- Golden count: `53/65` -> `54/66`
- Test count: `4,845+` -> `5,160+`
- "holds through" version: updated

I verified at `getting_started.md:188`:

```
As of v4.143.0 the self-hosted compiler passes **54/66** golden tests
```

And at line 236:

```
5,160+ tests.
```

Both correct! **Bo.6-drift is CLOSED.**

**One small note**: line 191 says "same 109,872 line count" but the
v4.144.0 BASELINE shows stage2.ll is now at 110,127 lines. This is a
+255-line growth from the Cb.5/Cb.6/Cb.7 changes in emit_llvm.mn +
lower.mn. Not a content error per se (the 109,872 number was accurate
when the line was written for v4.143.0), but it will accumulate. Very
low priority. Not opening a docket for it.

### Bo.7 — Localized READMEs — STILL CLOSED

The Spanish README shows `5160+_pasando`. Parity with English maintained.

### Bo.8 — SPEC header version — CLOSED (verified!)

`docs/SPEC.md:3` now reads:

```
**Version:** 4.143.0
```

This was bumped from `4.139.0` per my carry-forward. Correct! The SPEC
has not been modified in v4.144.0 (no SPEC-level changes this release),
so `4.143.0` is the accurate "synced-to" version.

### Bo.9 — SPEC section 1 Goals "legacy Python transpiler" — STILL PRESENT

`docs/SPEC.md:39` still contains:

```
(The legacy Python transpiler emitter `mapanare/emit_python_mir.py`
was removed in v4.58.0; `mapanare bind --lang python` is the canonical
Python-interop path via compiled `.so` + ctypes.)
```

Wait — I need to re-read this carefully. At v4.143.0 I flagged SPEC
section 1 Goals as saying "legacy Python transpiler backend exists for
bootstrapping." Let me check what the current text actually says. The
Sp.1 docket (MEDIUM, Coral) was closed at v4.143.0, purging the ghost
phrasing at lines 25/37/39. What remains at line 39 is a *parenthetical
historical note* that says the emitter "was removed in v4.58.0" — this
is factual narration, not a claim that a legacy backend exists. This is
*not* the same wording I flagged at v4.143.0. Sp.1 cleaned lines 25 and
37 (the goals-section narrative), and this parenthetical at line 39 is
an accurate historical record. I am satisfied.

**Bo.9 is moot. The remaining text is factual history, not a ghost claim.**

### Bo.10 — `docs/known_issues.md` footer — CLOSED (verified!)

Footer now reads `Last updated: v4.143.0.` Correct!

### Bo.11 — near-fixed-point wording in README — CLOSED (verified!)

The README main blurb (line 15) now reads:

```
The self-hosted compiler reaches a 3-stage fixed point (`stage2.ll` ~=
`stage3.ll`, 4-line version-metadata diff only)
```

This uses the approximate-equality symbol and the "4-line
version-metadata diff only" qualifier — accurate near-fixed-point
wording. Correct!

---

## Bo.* summary table

| ID | v4.143.0 status | v4.144.0 status | Notes |
|---|---|---|---|
| Bo.1 | CLOSED | CLOSED | footer will drift next release, normal |
| Bo.2 | CLOSED | CLOSED | native-mode prereqs intact |
| Bo.3 | CLOSED | CLOSED | merge note intact |
| Bo.4 | CLOSED | CLOSED | Tests badge 5160+, localized parity |
| Bo.5 | CLOSED | CLOSED | structural fix, cannot regress |
| Bo.6 | CLOSED | CLOSED | golden count, test count current |
| Bo.7 | CLOSED | CLOSED | localized READMEs at parity |
| Bo.8 | CLOSED | CLOSED | SPEC header v4.143.0 |
| Bo.9 | carry-forward | MOOT | remaining text is factual history |
| Bo.10 | CLOSED | CLOSED | footer bumped to v4.143.0 |
| Bo.11 | CLOSED | CLOSED | near-fixed-point wording synced |

**All prior Bo.* items hold. Zero regressions. Zero re-openings.**

This is the cleanest Bo.* re-audit in the project's history.

---

## New finding: README benchmark numbers are now stale

This is the single substantive docs finding from this cycle.

The `FINAL_REPORT_v4.144.md` contains corrected benchmark numbers
post-Bn.1 (the Rust harness-tax fix). The corrected geomean is:

- **Mapanare/C: 4.57x** (was 4.86x)
- **Mapanare/Rust: 5.83x** (was 1.12x — the old number was an artifact!)
- **Mapanare/Python: 168x faster** (was 42.6x)

The report is *beautifully honest* about this. It says, in plain text:

> "The v4.135.0 'Mapanare 1.12x of Rust' was an artifact of the harness
> tax. The corrected comparison at v4.144.0 shows Mapanare is 5.83x
> slower than Rust across the 6-workload corpus."

I love this. This is a project admitting a measurement error and
publishing the correction prominently. That is what integrity looks
like in benchmarking.

**BUT** — the README front door still shows the old numbers everywhere:

1. **`README.md:15`** (opening paragraph): "42.6x faster than Python",
   "1.12x of Rust (within noise)", "4.86x slower than C (gcc -O2)"
2. **`README.md:397-398`** (Benchmarks section): same three numbers
3. **`README.md:402`** link: still points to `FINAL_REPORT_v4.136.md`
   (the report with the artifact-inflated Rust numbers)
4. **`README.md:406`** header: "Performance (v4.125.0, ...)" — two
   major benchmark refreshes ago
5. **`README.md:408-415`** table: has the old Rust column (1.94 ms for
   quicksort, 1.44 ms for enum_match) which are the 10ms-spawn-tax
   numbers divided by iteration count, not the real internal times
6. **`docs/README.es.md:15`** (Spanish): same "42.6x ... 1.12x ... 4.86x"
7. **All three localized READMEs** link to `FINAL_REPORT_v4.136.md`

The corrected report exists. The old numbers are still on the front door.
A user landing on the README today sees "1.12x of Rust" which the
project's own benchmark report now calls an artifact.

This is a MEDIUM-importance finding. It does not mislead users about
language *functionality*, but it does make a performance claim the
project itself has retracted. The fix is straightforward:

1. Update the three headline numbers in the opening paragraph and
   Benchmarks section to match `FINAL_REPORT_v4.144.md`
2. Update the benchmark table to use the corrected Rust numbers
3. Update the link from `v4.136` to `v4.144`
4. Update the header from `v4.125.0` to `v4.144.0`
5. Sync all three localized READMEs

Estimated effort: **30 minutes**.

I am filing this as **Bo.12** (see carry-forward).

---

## FINAL_REPORT_v4.144.md — quality review

This is a lovely benchmark report. Let me evaluate it as documentation:

**Strengths:**
- Clear methodology section (hardware, runs, tool versions)
- Honest "Notes" column explaining each outlier (`struct_alloc` 70x gap,
  `string_concat` Go anomaly, `fib_recursive` LLVM inliner behavior)
- Explicit comparison table vs v4.135.0 with candid admission that the
  old Rust number was wrong
- Perf arc targets with specific version numbers (v4.145.0 for
  enum_match, v4.148.0 for string_concat, v4.149.0 for struct_alloc)
- The Python comparison (168x faster) is beautifully positioned as the
  "why Mapanare exists" number

**Weaknesses:**
- The async benchmarks section is a bit sparse — just five numbers and a
  geomean, no comparison against Go/asyncio/Tokio. The v4.135.0 report
  had "42.8x faster than asyncio, 1.61x slower than Go" as headline
  numbers. This report drops those comparisons entirely. If the async
  harness was not re-run against other languages, a one-line note saying
  "async cross-language comparison deferred to v4.145.0" would be honest.
- No memory/binary-size table (the v4.136 report had peak RSS + binary
  size). If these measurements weren't refreshed, that's fine — but
  noting their absence would be complete.

**Overall:** this is an honest, well-structured report that does the
hard thing (admitting a measurement error) gracefully. **+0.1** for
the honesty alone.

---

## Cb.10 docstring — quality review

The rewritten docstring at `tests/golden/66_qualified_type_ref.mn:1-6`:

```
// Golden test: struct construction and field access
// Cb.10 (v4.144.0): docstring rewritten to match actual test shape.
// This test exercises struct definition, constructor, and field access --
// it does NOT test qualified type references (dotted type names like
// module.Type). Gr.2 qualified-type-ref parsing is covered by
// tests/parser/test_*qualified*.
```

This is exactly the kind of documentation fix that makes my heart sing!
The prior docstring (I presume it said something about qualified type
refs, matching the filename `66_qualified_type_ref.mn`) was misleading.
The test actually tests struct construction. The new docstring:

1. Says what the test *does* ("struct definition, constructor, and
   field access")
2. Says what the test *does NOT do* ("does NOT test qualified type
   references")
3. Points to where the actual qualified-type-ref tests live
   (`tests/parser/test_*qualified*`)
4. Tags the docket and version for traceability

This is how golden test documentation should read. Beautiful.

---

## SPEC header check

`docs/SPEC.md:3` reads `Version: 4.143.0`. This is correct — no
SPEC-level language changes landed in v4.144.0 (the Cb.* items are
compiler internals, not spec changes). The SPEC header should be bumped
when spec-affecting changes ship, not on every version. This is the
right behavior.

---

## README roadmap table check

`README.md:735` now ends with:

```
| **v4.143.0** | Post-rc1 panel (8.86/10) + fast-win closeout: ... | **Current** |
```

At v4.143.0 I noted the table was missing rows for v4.137.0-v4.142.0.
The lead added rows for all six bridge releases (v4.137.0 through
v4.142.0) plus the v4.143.0 row. Beautiful! The full release narrative
is now readable from the front door.

There is no row for v4.144.0 yet, and v4.143.0 is still marked
**Current**. This is expected — v4.144.0 is in-flight. The row should
be added when the release ships. Not a finding.

---

## Error message quality — held

Unchanged from v4.143.0. The `diagnostics.py` Rust-style error output
remains high quality. No regression, no improvement. Held flat.

---

## CHANGELOG honesty

No v4.144.0 entry yet in CHANGELOG.md (the top entry is `[4.143.0]`).
This is expected for a release that has not been formally cut. When it
ships, the CHANGELOG should document the Cb.5-tests/Cb.6/Cb.7/Cb.9a/Cb.10
closures and the benchmark report. Not a finding.

---

## Verdict + score rationale

| Driver | Delta |
|---|---|
| All Bo.* items verified holding at v4.143.0 closures — zero regressions | +0.00 (maintaining baseline) |
| Cb.10 docstring rewrite — honest, precise, cross-referenced | +0.05 |
| `FINAL_REPORT_v4.144.md` — honest benchmark correction, well-structured | +0.10 |
| README roadmap table now has v4.137.0-v4.143.0 rows (v4.143.0 fix) | +0.00 (already credited) |
| README benchmark headline numbers still cite retracted v4.135.0 artifact | -0.05 |
| README benchmark link still points to `FINAL_REPORT_v4.136.md` | -0.00 (bundled with above) |
| Localized READMEs still cite old benchmark numbers | -0.00 (bundled with above) |
| Async benchmark section lacks cross-language comparison | -0.00 (minor) |
| **Net** | **+0.10** |

**9.0 -> 9.1. Grade: EXCEEDS.** Second consecutive EXCEEDS. The delta
is modest (+0.1) because this release is primarily a compiler-internals
release, not a docs release. The docs contributions are real but small:
one honest benchmark report and one thoughtful docstring rewrite. The
main thing keeping me from going higher is the README benchmark headline
numbers — the project published a correction but hasn't propagated it
to the front door yet.

---

## Carry-forward items (v4.144.0 -> v5.0.0 final)

| ID | Title | Severity | Effort |
|---|---|---|---|
| Bo.12 | README + localized READMEs benchmark numbers stale: "1.12x of Rust" retracted by own report -> should be "5.83x of Rust"; C/Python numbers also shifted; link v4.136 -> v4.144; table header v4.125.0 -> v4.144.0; Rust column in table uses old harness-taxed values | MEDIUM | 30 min |

Total effort: **30 minutes of writing**. One item. Clear scope.

**Note on Bo.12 severity:** I am grading this MEDIUM, not LOW, because
the README currently makes a specific numerical performance claim
("1.12x of Rust") that the project's own published benchmark report
explicitly labels as an artifact. This is not cosmetic staleness like
a footer timestamp — it is a retracted measurement still displayed on
the front door. The fix is trivial, the urgency is real.

---

## v5.0.0 readiness — docs perspective

If the lead asked me today: "Based solely on docs/DX, should we flip
from rc1 to clean v5.0.0?"

My answer: **Yes, with Bo.12 cleared first.** Thirty minutes. The
benchmark numbers are the last significant docs debt. Everything else
is clean:

- `mapanare --version` prints the live version (structural fix)
- SPEC header tracks correctly
- `known_issues.md` is user-facing and current
- Getting started guide has accurate counts
- Localized READMEs at parity with English
- Roadmap table tells the full story
- Error messages are Rust-grade
- The Cb.10-style docstring fixes show that test documentation is
  being actively maintained

The codebase *looks attended to*. That is the single most important
DX signal a new user encounters, and it has held consistently since
v4.138.0 — seven releases of unbroken documentation discipline.

---

## Reproducibility

```bash
# Verify Bo.4 (Tests badge):
grep "tests-5160" README.md            # should match

# Verify Bo.8 (SPEC header):
head -5 docs/SPEC.md                   # should say "Version: 4.143.0"

# Verify Bo.10 (known_issues footer):
tail -3 docs/known_issues.md           # should say "v4.143.0"

# Verify Cb.10 docstring:
head -6 tests/golden/66_qualified_type_ref.mn  # should describe struct construction

# Verify benchmark report exists:
test -f benchmarks/FINAL_REPORT_v4.144.md && echo "OK"

# Confirm README benchmark drift (Bo.12):
grep "1.12" README.md                  # still shows old "1.12x of Rust"
grep "5.83" benchmarks/FINAL_REPORT_v4.144.md  # corrected number

# Verify test count:
# BASELINE.md says 5,187. README says 5160+. Floor holds.
```

---

## One last note to the lead

At v4.143.0 I said "if Bo.4-drift closes, I expect 9.2-9.5 at the next
panel." Bo.4-drift did close. Why am I at 9.1 instead of 9.2? Because
the Bn.1 benchmark correction created a *new* documentation gap that
did not exist at v4.143.0. The old numbers were wrong but nobody knew
it. Now we know, the correction is published, but the front door was
not updated. That is a net negative from a DX perspective because a
user who reads the README *and* the benchmark report sees a
contradiction. Thirty minutes of README edits closes this completely.

The good news: the Bo.12 fix is the *only* item on my carry-forward.
One item. Thirty minutes. That is the lightest carry-forward I have
ever filed. The docs debt is effectively zero. Clear Bo.12 and I am
at 9.3+ for the next panel without breaking a sweat.

Grade: **9.1 / EXCEEDS.** Second consecutive EXCEEDS. Earned and held.
