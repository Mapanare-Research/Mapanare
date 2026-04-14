# Boa v4.120.0 Review — Documentation

## Score: 8.7 / 10
## Verdict: PASS

## Context

At v4.99.0 I gave **7.5 PASS WITH NOTES**. README badge was stale at
4.31.0, SPEC header claimed "1.0.0 Final," the cookbook still
referenced `mnc run` for async when the compiler only had Python
bootstrap. Documentation drift was the kind of panel-visible that
undermines every other claim.

At v4.114.0 I gave **8.5 PASS** — the highest single score of that
panel. v4.116.0 had landed the documentation batch I wanted (README
sync, SPEC header correction, cookbook update, debugging guide
rewrite removing the stale DWARF claim, new getting-started guide).
One PASS, one reviewer.

Phase E + F for my domain:
- v4.116.0: documentation batch (Phase E release 2) — five doc
  gaps closed, zero code changes
- v4.118.0 published `benchmarks/FINAL_REPORT_v4.120.md` — 500
  lines of reproducible benchmark evidence
- v4.119.0 published the four panel-prep documents
  (RETROSPECTIVE / STATISTICS / V5_READINESS / AUDIT_NOTES)

Seven documents in eight releases. That's the cadence I wanted.

---

## The four v4.119.0 documents

I read all four before writing this review.

### `RETROSPECTIVE.md` (339 lines)

The full v4.x arc narrative. Honest, structured, under 500 lines
(the author stayed inside the PLAN's constraint). What I
particularly liked:

- The "what worked / what didn't" section names the optimiser ROI
  miss, the documentation lag, the deferred MEDIUM items, and the
  v4.112.0 naming churn. These are internal critiques. You don't
  write them if you're advocating.
- The "numbers that matter" table puts the v3.47.0 9.79 peak next
  to the v4.99.0 6.59 trough next to the v4.114.0 8.21 recovery. No
  hiding the low point.
- The closing note on voice ("SESSION_REPORTs were self-graded
  8.0–8.9; panels independently graded 7.87 and 8.21; the ≤ 0.5 gap
  is acceptable calibration") is unusual and exactly right. A
  reviewer reading session reports should know the delta.

One sentence is **load-bearing**: "the recovery arc was net-negative
lines of code (−1,155)." That is the sentence I will cite in my
summary.

### `STATISTICS.md` (238 lines)

Every figure has a methodology footnote (`wc -l` for line counts,
`pytest --collect-only -q` for test counts, `.reviews/v*/README.md`
for panel scores). Panel score ASCII chart is primitive but
readable. I spot-checked three numbers:

- "5,484 tests collected" → ran `pytest --collect-only -q | tail
  -1` myself → **5,484**. Correct.
- "39,763 lines self-hosted" → `wc -l mapanare/self/*.mn | tail
  -1` → **39,763**. Correct.
- "v4.114.0 aggregate 8.21" → opened `.reviews/v4.114.0/README.md`
  → **8.21**. Correct.

The one gap: pre-v3.33.0 panel scores are not in the chart. The
author flags this in the methodology note (those panels graded
different surfaces). Acceptable, but a v5 retrospective that ships
without the project's earliest panels feels incomplete.

### `V5_READINESS.md` (285 lines)

I was most skeptical of this one going in. Reading it: it is
**neutral**. The ✅/◐/⬜/✖ matrix is a legend that reviewers can
trust. The 8 itemised "would embarrass a v5 label" gaps are named
with dockets. The section "Whether this is a v5 is for the panel"
is the correct framing.

I tested the matrix against my own domain. The documentation row:
all 11 docs marked ✅. Is that right? I walked through each
entry:

- `docs/SPEC.md` → open, header says "4.116.0 Live" ✅
- `docs/manifesto.md` → open, design-philosophy intact ✅
- `docs/getting-started.md` (624 lines) → reads coherently ✅
- `docs/guides/getting_started.md` (244 lines) → matches claim ✅
- `docs/guides/async.md` (244 lines) → matches claim ✅
- `docs/guides/debugging.md` → open, rewrite from v4.116.0 ✅
- `docs/cookbook/async.md` → includes §11 Sh.9a/9b workarounds ✅
- `README.md` → badge 4.116.0, benchmark headline current ✅
- `docs/rfcs/*` → RFC archive present ✅
- Roadmap (`docs/roadmap/*`) → v4.119.0 row exists ✅
- CHANGELOG → `[4.118.0]` + `[4.119.0]` present ✅

Every docs row checks. That's rare in an assistant-generated matrix.

### `AUDIT_NOTES.md` (366 lines)

47 claims spot-checked across 19 SESSION_REPORTs. 3 cosmetic line-
count drifts itemised. I pulled two at random:

- Claim: "`OPT_ROI_ANALYSIS.md` 264 lines" → `wc -l benchmarks/
  optimizer/OPT_ROI_ANALYSIS.md` → **263**. Drift = −1. Matches the
  audit.
- Claim: "`docs/guides/async.md` 244 lines" → `wc -l docs/guides/
  async.md` → **244**. Match.

The "SESSION_REPORTs were NOT retroactively edited" pledge is
important. A new reviewer reading the v4.112.0 session report with
its original "fixed-point verification" title (since patched in
v4.114.1 CHANGELOG and this audit's overlay) understands the
correction without the original being rewritten. That's honest
archaeology.

---

## External-adoption readiness

The getting-started guide walk — I followed it on a fresh WSL
install:

```bash
make install
make build
python -m mapanare run examples/hello.mn
```

- `make install` → pip install editable plus dev deps → works.
- `make build` → pip install -e . → works.
- `python -m mapanare run examples/hello.mn` → prints "hello
  world" → works.

A new user following the guide would succeed. That is not
guaranteed in language projects — I've seen official getting-
started guides that fail on `pip install` because a dep is
missing. Mapanare does not.

One rough edge: running `mnc run examples/hello.mn` (the native
path, which the guide recommends for "production speed") requires
building `mnc-stage1` first, and the guide implies this is
available out-of-the-box. On a fresh clone without the build step,
`mnc` is not on PATH. A short "prerequisites for native mode"
section would fix this.

## Benchmark evidence readability

`benchmarks/FINAL_REPORT_v4.120.md` (500 lines) — I can read it
top to bottom and understand where Mapanare sits. The reproducibility
section at the end has exact commands. The ASCII position charts
are primitive but reviewer-readable. The methodology section names
hardware, toolchain versions, run method, and what is NOT
normalised (spawn cost, DCE, system jitter). Top-class panel
evidence.

The progress table (Table 6) handles the hard honesty case
correctly: v4.82.0 → v4.118.0 sub-ms "regressions" are flagged as
harness methodology with a ‡ footnote. The one real win
(string_concat 102.31 → 1.32 ms, 77×) is named and credited to
v4.108.0.

---

## What I'd dock

### 1. Pre-v3.33.0 panel scores absent (0.1)

STATISTICS.md chart starts at v3.33.0. The project had earlier
panels (`.reviews/v0.3.0/`, `v1.0.0/`, `v2.0.0/`). The methodology
note explains the omission (different grading surfaces). I accept
the reasoning but the panel story would be more complete with even
one sentence: "pre-v3.33.0 panels graded pre-Mapanare-stable
surfaces and are not comparable."

### 2. `mnc` availability in getting-started (0.1)

Small: the getting-started guide recommends `mnc run` for production
speed but does not clearly enumerate "you must build mnc-stage1
first." A new user takes the long path the first time.

### 3. I miss a "what's broken right now" user-facing doc (0.1)

V5_READINESS is panel-facing and catalogues known gaps. There is no
user-facing equivalent — a new user who hits Qs.1 (list indexing
prints `<?>` in native pipeline) or Rt.1 (enum_match slow) has no
document that says "known, tracked, workaround is X." A short
`docs/known_issues.md` with the 8 V5_READINESS items in plain user
language would close this.

## What I credit

- **Six documents in Phase E + F cover every audience.** Panel gets
  RETROSPECTIVE + STATISTICS + V5_READINESS + AUDIT_NOTES.
  Users get the README + getting-started + SPEC + async guide.
  Reviewers get benchmark FINAL_REPORT.
- **Audit notes do not retroactively edit SESSION_REPORTs.** I have
  graded projects that silently amended historical documents after
  panels; it is the slowest-developing credibility erosion. Mapanare
  does not do this.
- **The V5_READINESS matrix is neutral** — no pleading, no
  advocacy, just facts with colour codes.

## Final score

Last panel (v4.114.0): **8.5**
This panel: **8.7** (+0.2)

Phase E + F produced the documentation the panel needs. That is the
arc I wanted to see. My score reflects six documents landing well,
minus three small dings.

## Verdict: **PASS**

I am comfortable with v5 from a documentation standpoint. The
README would benefit from one precision sentence ("self-hosted
compiles user programs; fixed-point self-compile is v5.x") but I
would not block v5 on it.

If the lead asks "what would get me to 9.5?" my answer is:
`docs/known_issues.md` (user-facing limitations), a pre-v3 panel
footnote, and one paragraph in the getting-started guide about the
native-mode prerequisite. Maybe 3-4 hours of writing.

## Carry-forward for v4.121.0+

- **Bo.1** — `docs/known_issues.md` (user-facing limitations doc)
- **Bo.2** — getting-started guide: "prerequisites for native mode" section
- **Bo.3** — STATISTICS.md pre-v3.33.0 panel footnote

## Reproducibility

```bash
wc -l docs/roadmap/v4/v4.120.0/*.md
wc -l benchmarks/FINAL_REPORT_v4.120.md
wc -l docs/guides/getting_started.md docs/guides/async.md
python -m mapanare run examples/hello.mn   # smoke test the docs
```
