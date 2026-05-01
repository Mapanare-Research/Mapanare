# Boa — Documentation / DX Review of Mapanare v5.22.0

**Reviewer:** Boa 🐍✨
**Personality:** Happiest reviewer in the room — wraps every real finding in so much positivity that you almost miss the severity. Every codebase is "beautiful." Every failure mode is "delightful." But the smile is honest, and the findings still bite.
**Previous Version Reviewed:** v5.11.0 (I scored 8.9 / 10 — load-bearing -0.5 delta on docs-surface drift).
**Score:** 9.0 / 10
**Grade:** EXCEEDS
**Delta vs v5.11.0:** **+0.1**
**Verdict:** PASS WITH NOTES
**Confidence:** 9 / 10
**Files Reviewed:** `README.md`, `docs/README.es.md`, `docs/README.pt.md`, `docs/README.zh-CN.md`, `docs/SPEC.md` (header + §4.0 + §1009 + §6.x + sync block), `examples/chained_cmp.mn`, `docs/guides/{formatter,lsp,init,docker,getting_started}.md` (presence + linkage), `CHANGELOG.md` v5.13.0–v5.21.1 entries, `mapanare/format.py` (H.8 closure), `tests/bootstrap/test_chained_cmp_mirror.py` (H.11 closure), `tests/test_format.py` chained-cmp idempotence cases (H.8 closure), `.reviews/CARRY_FORWARD.md` (H.10 closure), `.reviews/v5.11.0/06-boa.md` (my prior review), `.reviews/v5.22.0/PRE_PANEL_AUDIT.md`, packaging/install.{ps1,sh}, scripts/check_changelog_honesty.py output, scripts/bump_version.py.

---

## Executive Summary

Oh sweet sugar plum, where do I even **start**?! I'm so happy I could weep into my keyboard! 🐍✨

The v5.13–v5.21 terseness arc is the single most beautiful documentation
arc I have ever reviewed on this project. The lead **wrote a pre-panel
hygiene release** — v5.21.1 Mc.7 — and structured it explicitly around
the four findings I docked -0.5 for at v5.11.0. That is the kind of
panel-feedback-acted-on discipline I reward generously and unconditionally!
Bo.21 (version badges) — **STAYS CLOSED** at all four READMEs (`5.21.1`
across English / es / pt / zh-CN). Bo.17r (localized READMEs) — **CLOSED
STRUCTURALLY**: the Spanish, Portuguese, and Chinese READMEs all carry the
v5.21.0 corpus claim ("95/95 goldens nativos / nativos / 原生 goldens"),
the STRICT 238,086-line fixed-point status, AND a properly localized
**"Sintaxis terse (arco v5.13–v5.21)" / "Sintaxe terse (arco v5.13–v5.21)"
/ "简洁语法（v5.13–v5.21 弧线）"** subsection that names every
Te.1 → Te.6 feature with native-language examples. The H.6 SPEC §4.0 Te.3
soft-deprecation rewrite is genuinely **gorgeous** — three paragraphs that
explain colon-as-canonical, brace-as-deprecated, the warning shape, the
`MAPANARE_NO_BRACE_WARNING=1` opt-out, AND the `mnc fmt --keep-braces`
escape hatch. The H.7 broken-promise rescope at SPEC:1056 is the **honest**
closure — `if x: y` deferred to v6.0 with rationale. The new
`examples/chained_cmp.mn` H.4 example exercises 3-element + 4-element +
side-effecting middle term in 30 lines. The H.10 ledger append is honest
and complete. Twelve closures across one release! That's what a healthy
project looks like!

But.

Sweetie pie, I need to wrap this part in an extra-warm hug, and it has to land:
**Bo.18r is open for the THIRD CONSECUTIVE PANEL.** The lead's H.1 closure
bumped `README.md:176` to STRICT 238,086 with a beautiful 13-release
carry-trail — but the **Benchmarks-section lead-in paragraph at
`README.md:188-192`** still reads the **exact same words I flagged at
v5.8.0 and v5.11.0**: "*restored to NEAR at v5.6.11, preserved through
v5.8.0 — 4-line VERSION-metadata diff over a 217k-line stage2.ll). 5,720+
tests passing*". Same paragraph. Same shape. **Three panels.** v5.21.1
H.1 only refreshed the line-176 sibling — it walked right past the
benchmarks paragraph that has been the load-bearing Bo.18 finding since
v5.8.0. And the goldens badge — `[![Goldens](...goldens-66%2F66...)]()`
on line 29 — is **66/66** while the body at line 168 explicitly reads
"95/95". Internal contradiction, on the front-door surface, across all
four READMEs.

The H.* closures are real. They closed a different surface from the one
Bo.18r occupies. **The lead's H.* numbering and my Bo.* numbering only
partially intersect.** v5.21.1 closed H.1 by patching the line I had not
flagged, and missed the line I had flagged twice. This is the same shape
as v5.9.2 → v5.11.0, where Dn.1 closed line 139 (sibling) and missed
lines 151-155 (the actual Bo.18 paragraph). The fix shape is mechanical
in both cases: a 3-minute edit on a single paragraph. The pattern is
informational: when the lead writes a hygiene release against an audit
they wrote *themselves*, they fix what *they* see; when the audit doesn't
cite the panel review's exact line numbers, the panel-flagged shape can
slip past the patch. That's a process observation, not a malice claim!

Score impact: **+0.1 (8.9 → 9.0)**. The +0.5 from v5.21.1's twelve closures
sits on top of, not in place of, the **-0.4 carry from Bo.18r-three-panels +
Bo.19 + Bo.20 + Bo.22 + the new goldens-badge contradiction**. Three
consecutive panels flagging the same paragraph is the sort of regression
class that should *trend toward* a downgrade, not an upgrade — and yet the
H.*-class structural closures (especially H.3 localized READMEs and H.6
SPEC §4.0 rewrite) are large enough that I'm net-positive. If the same
paragraph is open at v5.27.0, I will not be smiling. 🐍

---

## Score: 9.0 / 10

---

## Progress Since Last Review (v5.11.0 → v5.22.0)

### What I genuinely love about this arc 💚

**The pre-panel hygiene release is itself a *gift to the panel*.** Reading
v5.21.1's PROMPT explicitly forbid editing grammar / `mapanare/self/*.mn`
/ Lark / parser.py / lower.py — and naming the closures docs-only — is
**exactly** the discipline I asked for at v5.11.0 ("front-door-surface
refresh as a closeout step"). Mc.7's framing ("doc-surface-only release
closing the 12 H.\* findings flagged in PRE_PANEL_AUDIT.md") is the
release-pattern I most want to see at this point in the project's life.
Same posture as v5.7.1 → v5.8.0 (project-record 9.66 panel). 🌸

**H.3 — localized READMEs structurally re-synced.** The Spanish / Portuguese /
Chinese READMEs **DO** tell the Te.1 → Te.6 story now. Line 125 in each
locale: `"Sintaxis terse (arco v5.13–v5.21)" — bloques con dos puntos (Te.1),
comprensiones... interpolación de strings (Te.4), ergonomía de structs (Te.5:
shorthand de campos, ..base, destructuring, if-let / while-let / let-else),
comparaciones encadenadas (Te.6: 0 < x < 10)`. Line 127 in each locale: STRICT
238,086 with the carry trail summarizing the 13-release streak. That's a
**massive recovery** of the Bo.17r damage from v5.11.0. The Spanish-README
sync was the strongest single finding in my v5.8.0 review; v5.21.1 H.3
recovers ~80% of that strength at scale. (See finding #4 below for the
remaining 20%.)

**H.6 — SPEC §4.0 rewrite for v5.19.0 Te.3.** The new §4.0 is *gorgeous*.
"Mapanare accepts colon-style as **canonical** (since v5.19.0). Brace-style
is **soft-deprecated**: it parses but emits a warning at parse time, and
`mnc fmt` (no flag) auto-migrates `{}` → `:` per file. Hard removal is
scheduled for **v6.0**. Both styles still produce identical AST and
identical IR until hard removal." Three paragraphs, every load-bearing
detail named: warning text, opt-out env var, `mnc fmt --keep-braces` flag,
v5.14.1 bootstrap mirror equivalence. This is the SPEC language I would
write if you put me in charge of SPEC for an afternoon. 💚

**H.7 — `if x: y` broken-promise rescope.** SPEC:1056-1059 reads "**Single-line
`if x: y` form is not supported.** The v5.14.0 SPEC originally promised this
for v5.21.0; that promise was rescoped at v5.21.1 to coincide with the v6.0
`{}` hard removal. Until v6.0, put the body on the next line." That is the
**honest** path. Path B was the right call (per v5.21.1 SESSION_REPORT
Phase 0). Forward promises are sacred and a broken one needs explicit
deferral, not silence. The Decision-1 lock is the kind of process artifact
I cheer for.

**H.4 — `examples/chained_cmp.mn`.** A 30-line example that covers `in_range`
helper, 3-element chain, 4-element chain, AND side-effecting middle term
demo all in one file. The `// Output: "M" then "true" — never two "M"s`
comment at line 28 is exactly the *documentation* I ask for around
once-evaluation semantics. This is what an example file should look like.
Sub-finding: the example needs to be linked from somewhere accessible —
SPEC §2.2 references it (line 60-something in the sync block) but the
README does not. (See finding #5.)

**H.8 — `mapanare/format.py` chained-cmp documentation.** The new module
docstring block at lines 22-31 explains *why* the formatter has no
ChainedCompare arm (because line-based whitespace canonicalization
preserves chain expressions verbatim — they're token-shaped like ordinary
binary comparisons). Plus 4 new idempotence tests in `test_format.py`
(`test_chained_cmp_idempotent_3_element`, `_4_element`, `_mixed_ops`,
`_mixed_direction`). 888/888 + 144 skipped passing. Smells fresh and
clean!

**H.10 — `.reviews/CARRY_FORWARD.md` arc append.** The new "Items resolved
in the v5.13.0 → v5.21.1 terseness arc" table is **19 rows**, each with a
release pointer + evidence pointer. That's *exactly* the ledger discipline
the canonical convention wants. The bolded "Bo.18r-style two-consecutive-
panel regression" caveat at line 199 is *self-aware* — the lead is
explicitly trying to prevent the same shape that hit Boa twice. (Finding:
the new entries are fine; what's missing is whether *Bo.18r itself* closed
this cycle. See findings #1 and #6.)

**H.11 — `tests/bootstrap/test_chained_cmp_mirror.py`.** 10 cases exactly
mirroring the v5.20.1 `test_te5_mirror.py` shape. Cross-bootstrap
byte-identical stdout assertion. This is *durable* test infrastructure —
load-bearing for v5.22.0+ regression detection.

**H.12 — `BENCHMARKS-windows.md` "last sync v5.8.8" admonition.** Per-platform
split was already structural (closed Rattler #1 from v5.11.0). v5.21.1
adds a staleness flag at the top. That's the right pattern: when content
*has* drifted but you can't refresh it in scope, *make the staleness
visible*. Excellent honesty.

**`bump_version.py` exists and lives at the source.** Per v5.11.2, the
script now updates VERSION + all four README badges (English `version-`,
Portuguese `versao-`, Chinese `版本-`) + CHANGELOG comparison links **in
one shot**. The v5.11.0-Boa-flagged bump-version skill bug is closed at the
source — `scripts/bump_version.py` is the canonical entry point. That's a
+0.1 on its own.

### What carried forward from v5.11.0

| ID | v5.11.0 status | v5.21.1 status | Notes |
|---|---|---|---|
| Bo.21 (HIGH) — version badges across 4 READMEs | OPEN | **CLOSED** | 5.8.7 → 5.21.1 across all 4. `bump_version.py` now load-bearing. |
| Bo.18r (MEDIUM) — README internal contradiction on fixed-point status | OPEN (regressed) | **STILL OPEN, third consecutive panel** | Line 176 closed by H.1 (✅); lines 188-192 — the actual paragraph I flagged at v5.8.0 + v5.11.0 — STILL says "restored to NEAR at v5.6.11, preserved through v5.8.0 — 4-line VERSION-metadata diff over a 217k-line stage2.ll". |
| Bo.17r (MEDIUM) — Localized READMEs frozen at v5.7.1 content | OPEN | **CLOSED STRUCTURALLY** | H.3 closure: line 125 Te.1–Te.6 story + line 127 STRICT 238,086 + line 118 95/95 corpus across all 3 locales. ~80% recovery. |
| Bo.22 (MEDIUM) — README Hello World uses `mapanare run` not `mnc run` | OPEN | **STILL OPEN** | README:84-99 still uses `mapanare run` / `mapanare build` / `mapanare check` / `mapanare lsp`. Install scripts still use `mnc init` / `mnc run` / `mnc build`. Internal contradiction. |
| Bo.23 (MEDIUM) — `mnc init` time bomb at v5.12.x bundle swap | OPEN | **CLOSED via Mc.3** | v5.18.0 shipped `mnc init` natively (`mapanare/templates/init/` + 10/10 tests). The time bomb defused at the source. 🌸 |
| Bo.24 (LOW) — Localized READMEs lack v5.10.0 bundled-LLVM + v5.9.1 BREAKING blockquote | OPEN | **STILL OPEN as subset of Bo.17r remainder** | Localized READMEs now sync the corpus + fixed-point + Te.* arc, but the v5.10.0 bundled-LLVM install copy and v5.9.1 BREAKING migration blockquote are still absent in es/pt/zh-CN. (See finding #4.) |
| Bo.19 (LOW) — README test-count drift (badge 5800+, body 5,720+) | OPEN | **STILL OPEN** | Same shape. Body still 5,720+ at line 191. |
| Bo.20 (LOW) — README links to `benchmarks/FINAL_REPORT_v4.153.md` | OPEN | **STILL OPEN** | Line 194 still links the v4.153 report. |
| Bo.14r2 (LOW) — getting_started.md test count slightly stale | unverified | not re-verified | Out of scope at this panel. |

Net: **2 closed (Bo.21 + Bo.23 via Mc.3), 1 closed structurally (Bo.17r), 4 still open
(Bo.18r + Bo.22 + Bo.19 + Bo.20), and 1 new internal contradiction (the goldens-badge 66/66 vs body 95/95 across all four READMEs).** Bo.18r is now open for the third consecutive panel — same paragraph, same shape, same fix size each time.

---

## What is preserved from v5.11.0

- **SESSION_REPORT cadence held across the entire 16-release arc** (v5.13.0
  → v5.21.1). Every release has a substantive, dated, validation-block-
  bearing SESSION_REPORT.md. v5.21.1's report explicitly enumerates H.1–H.13
  with closure evidence per finding. That is the artifact I asked for at
  v5.11.0.
- **install.ps1 / install.sh continue to ship `mnc` as canonical** — the
  Get-started block at install.ps1:172-175 + install.sh:193-196 says
  `mnc init myproject` / `mnc run main.mn` / `mnc build main.mn`. v5.18.0
  Mc.3 made this *actually work* natively, defusing my Bo.23 time bomb. 💚
- **CHANGELOG.md is beautifully maintained.** Every v5.13.0–v5.21.1 entry
  enumerates the lettered (Te.\*, Sh.\*, Mc.\*, Dk.\*) sub-findings, calls
  out deferred items, and `check_changelog_honesty.py` is **clean** for the
  current section. (Sub-finding: the script only checks the latest section
  per invocation. Coverage of earlier sections is implicit, but only by
  habit. Worth a re-run pass at v5.22.0+.)
- **`docs/guides/` exists and grew during the arc.** New entries: `docker.md`,
  `formatter.md`, `init.md`, `lsp.md`. (Sub-finding: only `docker.md` and
  `lsp.md` are linked from README. `formatter.md` and `init.md` are
  invisible. See finding #5.)
- **The `bump_version.py` skill replacement** at `scripts/bump_version.py`
  is structurally clean — handles the four locale-specific label keys
  (`version-` / `versao-` / `版本-`) that bit the v5.11.0 panel.

---

## Issues Found

### 1. **HIGH** — Bo.18r STILL OPEN — third consecutive panel — README lines 188-192 still carry the same v5.8.0-vintage Benchmarks-section paragraph

This is genuinely painful because **it's the same paragraph I flagged at
v5.8.0 (Bo.18) and at v5.11.0 (Bo.18r), with the same suggested fix shape
both times**. v5.21.1 H.1 closure bumped `README.md:176` (the
"Native compiler" subsection status line) to **STRICT 238,086 lines /
13-release streak**, which is *gorgeous*. But the **Benchmarks-section
lead-in paragraph 12 lines below** is untouched.

Reproduce:

```bash
$ grep -nE "238,086|217k|5,720|FINAL_REPORT_v4" README.md
176:Self-host 3-stage fixed-point: STRICT (stage2.ll == stage3.ll byte-identical at 238,086 lines; restored v5.9.0 — DX.2 closed the v4.140.0–v5.8.x VERSION-metadata diff at the source; held through v5.17.0's mechanical brace → colon rewrite, v5.20.0's struct ergonomics, and v5.21.0's chained comparisons — longest streak in project history at 13 consecutive releases).
191:4-line VERSION-metadata diff over a 217k-line stage2.ll). 5,720+
194:[Full benchmark report](benchmarks/FINAL_REPORT_v4.153.md)
```

```bash
$ sed -n '188,194p' README.md
The self-hosted compiler compiles itself (3-stage fixed point reached
at v4.134.0; temporarily regressed at v5.1.2 from In.1 inliner
re-enable; restored to NEAR at v5.6.11, preserved through v5.8.0 —
4-line VERSION-metadata diff over a 217k-line stage2.ll). 5,720+
tests passing, zero flaky across 30 sequential runs.

[Full benchmark report](benchmarks/FINAL_REPORT_v4.153.md)
```

A user reading the README top-to-bottom hits the **correct** STRICT
status at line 176 ("13 consecutive releases", "238,086 lines"), then
**12 lines later** reads a paragraph that says "**restored to NEAR at
v5.6.11, preserved through v5.8.0 — 4-line VERSION-metadata diff over a
217k-line stage2.ll**". This is the v5.7.1-vintage state (NEAR), 14
releases ago, when fixed-point was actually NEAR. The DX.2 closure at
v5.9.0 made it STRICT (0-line diff at 226k lines). Te.5/Te.6 grew it to
238,086 lines. Three panels' worth of feedback have failed to migrate
this paragraph.

The escalation pattern is:
- **v5.8.0 panel (Bo.18, MEDIUM)** — flagged this paragraph; "single-paragraph copy edit" recommended.
- **v5.9.2 Dn.1** closed *the line-139 sibling* — beautifully — but missed this paragraph.
- **v5.11.0 panel (Bo.18r, MEDIUM, regressed)** — flagged again; same paragraph, same fix.
- **v5.21.1 H.1** closed *the line-176 successor* — beautifully — but missed this paragraph.
- **v5.22.0 panel (this review)** — flagging *again*. Same paragraph. Third consecutive panel.

I am bumping the severity from MEDIUM to **HIGH** because three consecutive
panels with the *same shape* is structural drift, not a one-time miss. A
casual visitor reading the README from the top down hits two *different*
fixed-point status claims within 15 lines, and the second contradicts the
first by *14 releases of project history*. That's brand-damaging in
exactly the same way the v5.11.0 version-badge drift was.

**The H.* numbering / Bo.* numbering mismatch is the process observation.**
The lead's PRE_PANEL_AUDIT.md cited line 168 (or thereabouts) for the
"80/80 → 95/95" goldens claim and the line-176 fixed-point status line.
The v5.11.0 panel review (`.reviews/v5.11.0/06-boa.md`, finding #1) cited
**lines 151-155** for the Bo.18r-shape paragraph. The two reviews didn't
share line numbers (Bo numbered the paragraph by the v5.11.0 README; the
audit numbered by the v5.21.0 README, where the same paragraph slid down
~37 lines from intervening insertions). When the lead drafts a hygiene
release from their own audit, the audit's line numbers are what get
patched — and the panel-review line numbers slip past.

Suggested fix (closes Bo.18r + Bo.19 + Bo.20 in one keystroke):

```diff
-The self-hosted compiler compiles itself (3-stage fixed point reached
-at v4.134.0; temporarily regressed at v5.1.2 from In.1 inliner
-re-enable; restored to NEAR at v5.6.11, preserved through v5.8.0 —
-4-line VERSION-metadata diff over a 217k-line stage2.ll). 5,720+
-tests passing, zero flaky across 30 sequential runs.
-
-[Full benchmark report](benchmarks/FINAL_REPORT_v4.153.md)
+The self-hosted compiler compiles itself to a strict 3-stage fixed
+point (stage2.ll == stage3.ll byte-identical at 238k lines; strict
+since v5.9.0, held through 13 consecutive releases — see "Native
+compiler" above). 5,800+ tests passing, zero flaky across 40+
+sequential runs.
+
+[Full benchmark report](benchmarks/FINAL_REPORT.md)
```

That's a **3-minute, single-paragraph, single-file** fix that closes
Bo.18r AND Bo.19 (test count) AND Bo.20 (FINAL_REPORT link). And replaces
the brittle exact-line-count `238,086` with the rounded `238k` (the
v5.9.2 Dn.1 self-immunization pattern that prevented the line-139 surface
from re-decaying). **This same paragraph has been a 3-minute fix for three
consecutive panels.**

Process suggestion: **the next pre-panel audit should cite panel-review
finding IDs and line numbers as anchors**, not just line numbers from the
current HEAD. v5.21.1's PRE_PANEL_AUDIT.md cites H.* findings the lead
identified themselves; the panel-review (Bo.18r) findings were not
cross-referenced into the H.* table. A two-column "Audit-finding /
Prior-panel-finding" header in the PRE_PANEL_AUDIT.md would have caught
this.

### 2. **HIGH** — NEW Bo.25 — Goldens badge stuck at `66/66` across all four READMEs while body says `95/95`

This is a fresh internal contradiction in the *exact same shape* as Bo.18r,
but on the goldens-count surface instead of the fixed-point surface.

```bash
$ grep -nE "goldens-[0-9]+|95/95 native goldens|95/95 goldens" \
    README.md docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
README.md:29:[![Goldens](https://img.shields.io/badge/goldens-66%2F66-brightgreen.svg?style=flat-square)]()
README.md:168:The self-hosted compiler runs the full corpus (95/95 native goldens at v5.21.0):
docs/README.es.md:29:[![Goldens](https://img.shields.io/badge/goldens-66%2F66-brightgreen.svg?style=flat-square)]()
docs/README.es.md:118:El compilador auto-hospedado corre el corpus completo de v5.21.0 (95/95 goldens nativos):
docs/README.pt.md:29:[![Goldens](https://img.shields.io/badge/goldens-66%2F66-brightgreen.svg?style=flat-square)]()
docs/README.pt.md:118:O compilador auto-hospedado roda o corpus completo da v5.21.0 (95/95 goldens nativos):
docs/README.zh-CN.md:29:[![Goldens](https://img.shields.io/badge/goldens-66%2F66-brightgreen.svg?style=flat-square)]()
docs/README.zh-CN.md:118:自托管编译器可运行完整的 v5.21.0 测试集（95/95 原生 goldens）：
```

All four READMEs: **goldens badge 66/66, body 95/95**. The body refresh
(per H.1 + H.3) bumped the corpus claim from 80/80 to 95/95 across all
four locales. The badge was missed across all four locales. `tests/golden/`
contains 95 `*.mn` files.

This is the **same systematic-skill-gap shape** as v5.11.0 Bo.21 (version
badge drift): a single front-door-surface metadata field is updated by
hand on the body but the corresponding badge has a separate update path
that doesn't fire. v5.11.2's `bump_version.py` closed the version-badge
shape; the goldens badge has no analogous tool — it's bumped by hand on
each release and was missed for the 66 → 80 → 95 transitions.

This is a casual-visitor metadata field. A user lands on the GitHub repo
page, sees "goldens 66/66", reads "95/95 in the body" 130 lines later,
and infers either (a) the badge is stale, (b) the body is aspirational,
or (c) the project has internal contradiction. Three releases of badge
lag (v5.20.0 added 81-91, v5.21.0 added 92-95) on a load-bearing
metadata surface.

I'm filing as **HIGH severity** because (a) it's a front-door metadata
contradiction, (b) it spans all four READMEs, (c) it has the *same
systematic-skill-gap fingerprint* as Bo.21 (which I filed HIGH at v5.11.0
for the same reason), and (d) the v5.11.0 panel's lesson was "audit the
bump-version skill against the four-README badge surface" — which the
lead beautifully closed for `version-` but did not extend to `goldens-`.

Suggested fix:

```bash
# 1-minute fix: bump goldens badge in all four READMEs.
sed -i 's|goldens-66%2F66-brightgreen|goldens-95%2F95-brightgreen|g' \
  README.md docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
```

**Structural fix (recommended):** extend `scripts/bump_version.py` to
auto-discover the goldens count (`ls tests/golden/*.mn | wc -l`) and
update the goldens badge across all four READMEs in lockstep with the
version badge. Same pattern as the v5.11.2 multi-locale label-key fix.
That closes the systematic-skill-gap class permanently.

Filing as **Bo.25** (HIGH).

### 3. **MEDIUM** — Bo.22 STILL OPEN — README Hello World still uses `mapanare run` not `mnc run`, contradicting v5.9.0 DX.7 + install scripts + 18 months of project posture

v5.9.0 DX.7 closed "getting-started uses `mnc` consistently". v5.9.1 DX.5
made `mnc <file.mn>` run by default. The whole DX.\* arc was "**mnc** is
canonical".

Yet README:80-99 still uses `mapanare`:

```bash
$ sed -n '80,100p' README.md
## Hello World

```bash
mapanare init hello && cd hello
mapanare run main.mn
```

`mapanare init` scaffolds a runnable project (terse `main.mn`,
`mapanare.toml`, `.gitignore`, `README.md`). For a one-liner:

```mn
fn main():
    print("hello from mapanare")
```

```bash
mapanare run hello.mn        # compile + run
mapanare build hello.mn      # produce a native binary
mapanare check hello.mn      # type-check, no codegen
mapanare lsp                 # start the language server (stdio)
```
```

Compared to install.ps1:172-175 + install.sh:193-196:

```
Get started:
  mnc init myproject
  cd myproject
  mnc run main.mn       # compile and run
  mnc build main.mn     # build native binary
  mnc --help            # see all commands
```

A user installs via `irm install.ps1 | iex`, sees "use **mnc**" in
the install-script output, opens README.md as the canonical project
documentation, sees "use **mapanare**". Six release cycles of carry-forward
on this exact contradiction.

Why MEDIUM and not HIGH: the `mapanare` alias *does work* (install.ps1
copies `mapanare.exe` → `mnc.exe`), so a user who copy-pastes from
README does not hit a hard error. But:

1. v5.9.1 DX.5 made `mnc <file.mn>` *run* by default. The README still
   pre-dates that change in posture.
2. v5.18.0 Mc.\* shipped native `mnc init` / `mnc fmt` / `mnc check` /
   `mnc lsp`. The README's `mapanare init` / `mapanare lsp` invocations
   are pre-Mc.\* idioms.
3. The v5.21.1 H.* findings list does NOT include this — it's *invisible*
   to the audit while being one of the first 5 code blocks any new user
   sees.

Suggested fix: rewrite Hello World + Write-Python-Compile-Native sections
to use `mnc init` / `mnc run` / `mnc build` / `mnc check` / `mnc lsp`,
with the `mapanare` alias mentioned parenthetically (matching install
scripts' "(`mapanare` is also installed as an alias for `mnc`.)" line):

```diff
-mapanare init hello && cd hello
-mapanare run main.mn
+mnc init hello && cd hello
+mnc run main.mn
```

```diff
-mapanare run hello.mn        # compile + run
-mapanare build hello.mn      # produce a native binary
-mapanare check hello.mn      # type-check, no codegen
-mapanare lsp                 # start the language server (stdio)
+mnc run hello.mn             # compile + run
+mnc build hello.mn           # produce a native binary
+mnc check hello.mn           # type-check, no codegen
+mnc lsp                      # start the language server (stdio)
+# (`mapanare` is also available as an alias for `mnc`.)
```

**5-minute fix.** Filing as **Bo.22** (still open MEDIUM, second consecutive panel).

### 4. **LOW** — Bo.24 STILL OPEN — Localized READMEs lack v5.10.0 bundled-LLVM install copy + v5.9.1 BREAKING migration blockquote + Te.\* features missing native examples

H.3 closed the **load-bearing prose body** of the localized READMEs — the
fixed-point status line + Te.1–Te.6 feature subsection + 95/95 corpus
claim are all present in es / pt / zh-CN at line 125-127. That is *most*
of the recovery I asked for at v5.11.0.

But the **install section** and **build-from-source section** are still
absent in the localized READMEs:

```bash
$ wc -l README.md docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
   336 README.md
   197 docs/README.es.md
   197 docs/README.pt.md
   197 docs/README.zh-CN.md
```

The localized READMEs are ~140 lines shorter than English. The missing
sections include:
- The "Quick start with Docker" subsection (English README:60-77).
- The v5.9.1 BREAKING migration blockquote (English README:209-213).
- The native compiler feature bullets (English README:170-174 — tensors,
  async, closure-typed parameters, etc.).
- The full bundled-LLVM install copy with `MAPANARE_NO_BUNDLED_TOOLCHAIN=1`
  opt-out (English README:42-58).

These are *user-load-bearing* paragraphs. A Spanish-speaking CI script
that pipes `mnc file.mn > out.ll` will break with no migration aid. A
Portuguese-speaking Windows user will not learn about the bundled-LLVM
default. A Chinese-speaking developer will not learn about the Docker
multi-stage pattern.

Severity LOW because (a) H.3 closed the *most-load-bearing* surface, (b)
the gap is content-additive not content-contradictory (localized READMEs
are *short*, not *wrong*), and (c) the alternative is asking the lead to
maintain four READMEs in lockstep across 22 surface sections, which is
itself drift-prone.

**Estimated effort:** 1-2 hours for full sync of the install + build-from-
source sections to es / pt / zh-CN at v5.22.0+. Recommend this be a
**v5.22.x or v5.23.0 follow-up**, not a hygiene blocker.

### 5. **LOW** — NEW Bo.26 — `docs/guides/formatter.md` and `docs/guides/init.md` exist but are not linked from README, SPEC, or any localized README

Discoverability gap. Both guides are first-class output of the v5.13.0
(formatter) and v5.18.0 (init) Mc.\* arc. Both ship beautiful prose. But:

```bash
$ grep -nE "guides/(formatter|init)" \
    README.md docs/SPEC.md docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# (no output)
```

`docker.md` and `lsp.md` are linked from `README.md:76` and `:105`. The
formatter and init guides — equally first-class — have no link from any
README or SPEC. A user discovers them only by `ls docs/guides/`.

Suggested fix: add 2 link lines to README.md after the `mnc fmt` and
`mnc init` invocations:

```diff
 mapanare lsp                 # start the language server (stdio)
 ```

+VS Code users: install [the official extension](...). Neovim/Helix in
+[`docs/guides/lsp.md`](docs/guides/lsp.md). New project scaffolding in
+[`docs/guides/init.md`](docs/guides/init.md). Source canonicalization in
+[`docs/guides/formatter.md`](docs/guides/formatter.md).
```

**3-minute fix.** Filing as **Bo.26** (LOW).

### 6. **LOW** — NEW Bo.27 — Audit-to-panel-finding cross-reference convention not yet load-bearing in PRE_PANEL_AUDIT.md

This is the *process observation* underlying findings #1 and #2.
PRE_PANEL_AUDIT.md is excellent — 13 H.\* findings, every one with
specific line-number / file claim, every one with closed-in-v5.21.1
evidence. But there is **no column** in the audit table mapping H.\*
findings to prior-panel finding IDs (Bo.18r → H.1? Bo.21 → ??? Bo.17r →
H.3? Bo.22 → ???).

The audit's H.1 was *adjacent to* but not *coextensive with* Bo.18r. H.1
fixed line 176 (the line the lead saw on their pre-panel audit pass);
Bo.18r occupies lines 188-192 (the line the v5.11.0 panel saw on a
top-down read). When the audit doesn't bind to the panel-finding IDs, the
hygiene-release closures patch what the audit cites and walk past the
shape the panel cites.

H.\* never includes Bo.22 (the README/install-script `mnc` vs `mapanare`
contradiction) or Bo.20 (FINAL_REPORT_v4.153.md link) — the lead's
self-audit didn't surface those. They were docketed at v5.11.0; they
were absent from the audit.

Suggested fix: at v5.27.0 pre-panel audit, add a column:

| # | Severity | Finding | Closes prior-panel ID | Closed in vX.Y.Z |
|---|---|---|---|---|
| H.1 | HIGH | README.md:168 reads "80/80 native goldens at v5.17.1" | (none — fresh) | bumped to 95/95 |
| H.1.B | HIGH | README.md:188-192 lead-in paragraph still v5.7.1-vintage | **Bo.18 (v5.8.0) / Bo.18r (v5.11.0)** | rewritten |
| ... |

That binds the hygiene-release line items to panel-history line items,
making the "audit didn't surface this" case visible at a glance. A panel
review would catch a missing prior-panel-ID column the way I caught the
missing closure here.

**Estimated effort:** 5 minutes per pre-panel audit (cross-walking
prior panel docket against new audit findings). Filing as **Bo.27**
(LOW, process observation).

### 7. **LOW** — Bo.19 STILL OPEN — test-count drift on README

Body 5,720+ at line 191; badge 5800+ at line 28. CLAUDE.md says 5,400+.
Three different numbers. Closes with finding #1 on the same paragraph
rewrite.

### 8. **LOW** — Bo.20 STILL OPEN — README links to `benchmarks/FINAL_REPORT_v4.153.md`

Line 194 still: `[Full benchmark report](benchmarks/FINAL_REPORT_v4.153.md)`.
v4.153 is methodology-stale relative to the v5.x cross-language grid.
Replace with `benchmarks/FINAL_REPORT.md`. Closes with finding #1's same
paragraph rewrite.

---

## Recommendations

Prioritized:

1. **(HIGH, 3 min)** Close Bo.18r at the actual paragraph (README:188-192)
   per finding #1. Use the rounded `238k` lines + "13 consecutive
   releases" framing to self-immunize against the next decay cycle. **This
   is the third consecutive panel flagging this paragraph** — the fix
   should be load-bearing in the next closeout flow.

2. **(HIGH, 1 min one-shot, 10 min structural)** Close Bo.25 at the
   goldens-badge surface across all four READMEs per finding #2.
   *Structural* fix: extend `scripts/bump_version.py` to auto-discover
   `tests/golden/*.mn` count and update the goldens badge across all four
   READMEs in lockstep with the version badge. This closes the
   systematic-skill-gap class.

3. **(MEDIUM, 5 min)** Close Bo.22 at README Hello World + Write-Python-
   Compile-Native sections per finding #3. Replace `mapanare run` /
   `mapanare build` / `mapanare check` / `mapanare lsp` with `mnc run` /
   `mnc build` / `mnc check` / `mnc lsp`. Add the `mapanare` alias note
   parenthetically (matches install scripts).

4. **(LOW, 3 min)** Close Bo.26 at README guide-link section per finding
   #5. Add 2 lines linking to `docs/guides/formatter.md` and
   `docs/guides/init.md`.

5. **(LOW, 1-2 hr deferred)** Close Bo.24 at localized README install +
   build-from-source surfaces per finding #4. Recommend deferral to
   v5.22.x or v5.23.0; H.3 already closed the load-bearing prose body.

6. **(LOW, 5 min process)** Bo.27 — at the next pre-panel audit, add a
   "Closes prior-panel ID" column per finding #6. This is the structural
   fix for the H.\*/Bo.\* mismatch class that has bitten this project at
   v5.9.2 → v5.11.0 → v5.21.1 → v5.22.0 panel cycles.

**Total estimated effort across items 1-4 + 6: ~17 minutes.** Item 5 is
the deferred one. Items 1-4 close on a single PR.

---

## Post-Production Health Assessment

**The codebase is HEALTHY.** 22 minor versions after the v5.0.0 release-
gate, the doc-surface side of Mapanare is *substantially better-managed*
than at v5.11.0 — the v5.21.1 hygiene release is a milestone. The
H.1–H.13 closures are real, large, and structurally sound. The
PRE_PANEL_AUDIT.md → hygiene-release → panel cycle is *exactly* the
release pattern I want to see at this point in the project's life. The
Te.1–Te.6 arc shipped six additive language features in 10 releases with
**zero new MIR ops, zero new IR shapes, zero runtime function additions**
— and that discipline is *visible* in the documentation surface (every
SPEC §6.x entry cites the desugaring target; every CHANGELOG entry calls
out "no new MIR ops"). 13 consecutive releases of strict 3-stage fixed
point is a *celebration-worthy* milestone. The localized-README sync at
H.3 recovers ~80% of the v5.7.1-state strong sync.

But:

- **Bo.18r is open for the third consecutive panel.** Same paragraph,
  same shape, same fix size each time. That is a pattern worth flagging
  even when the score is +0.1 net positive.
- **The goldens badge at Bo.25 is the same systematic-skill-gap shape as
  the v5.11.0 version badge.** v5.11.2's `bump_version.py` closed the
  version-badge surface; the goldens-badge surface has no analogous tool.
  Same lesson, applied unevenly.
- **The H.\*/Bo.\* numbering mismatch surfaced via Bo.18r and the new
  Bo.25.** When the lead's self-audit doesn't reference panel-review
  finding IDs, the hygiene release patches what the audit cites and walks
  past the panel-flagged shape.

If at v5.27.0 panel cycle (~5 minor releases hence) Bo.18r + Bo.22 +
Bo.25 are all closed and the next pre-panel audit cross-references panel
finding IDs (Bo.27), my next score moves to 9.6+. The capability is
*unquestionably* present — v5.21.1's H.1–H.13 closure proved it. What's
missing is the *closure of the cross-reference layer* between
panel-flagged surfaces and audit-flagged surfaces.

What MUST be done before the next panel:

- Bo.18r — **must close**. Three consecutive panels.
- Bo.25 — **must close**. Same shape as v5.11.0 Bo.21 (HIGH).
- Bo.27 — **process suggestion**, not blocking. But adoption would
  prevent the same-class pattern at v5.27.0.

If those three close before the next panel, my next score moves to
9.4-9.6. If only Bo.18r + Bo.25 close, ~9.3. If none close, ~8.7 (the
trajectory matters — three consecutive panels with the same paragraph is
a downgrade signal even if the rest of the work is +0.4 net positive).

---

## Bo.\* summary table (v5.11.0 → v5.22.0)

| ID | v5.11.0 status | v5.22.0 status | Notes |
|---|---|---|---|
| Bo.21 | OPEN HIGH (4 README badges 5.8.7) | **CLOSED** | All 4 READMEs at 5.21.1; `bump_version.py` load-bearing (closed at source per v5.11.2). |
| Bo.18r | OPEN MEDIUM (line 151-155 stale) | **STILL OPEN** (HIGH severity escalation) | 3rd consecutive panel. v5.21.1 H.1 closed sibling line 176; Bo.18r paragraph at lines 188-192 untouched. |
| Bo.17r | OPEN MEDIUM (localized READMEs frozen) | **CLOSED STRUCTURALLY** (~80% recovery) | H.3 closure: line 125 Te.1-Te.6 + line 127 STRICT 238k + line 118 95/95. ~20% remainder = Bo.24 (install+build sections). |
| Bo.22 | OPEN MEDIUM (README mapanare vs mnc) | **STILL OPEN** | README:80-99 still uses `mapanare`; install scripts use `mnc`; v5.18.0 Mc.\* native `mnc init`/`fmt`/`check`/`lsp` shipped, README pre-dates Mc.\* posture. |
| Bo.23 | OPEN MEDIUM (mnc init time bomb) | **CLOSED via Mc.3 (v5.18.0)** | Native `mnc init` shipped; install-script getting-started block now backed by real `mnc init` implementation. 💚 |
| Bo.24 | OPEN LOW (localized install+build) | **STILL OPEN** | H.3 closed prose body; install + build-from-source sections still absent in es/pt/zh-CN. |
| Bo.19 | OPEN LOW (test-count drift) | **STILL OPEN** | Same shape. Closes with Bo.18r same-paragraph rewrite. |
| Bo.20 | OPEN LOW (FINAL_REPORT_v4.153) | **STILL OPEN** | Same shape. Closes with Bo.18r same-paragraph rewrite. |
| Bo.25 | n/a | **NEW HIGH** | Goldens badge 66/66 across all 4 READMEs while body says 95/95. Same systematic-skill-gap shape as v5.11.0 Bo.21. |
| Bo.26 | n/a | **NEW LOW** | `docs/guides/formatter.md` + `init.md` not linked from README/SPEC. |
| Bo.27 | n/a | **NEW LOW process** | PRE_PANEL_AUDIT.md needs prior-panel-finding-ID cross-reference column. |

**Three closed (Bo.21 + Bo.23 via Mc.3 + Bo.17r ~80%), four still open
(Bo.18r escalated to HIGH + Bo.22 + Bo.19 + Bo.20), three new (Bo.25 HIGH,
Bo.26 LOW, Bo.27 LOW process).** Net: a **net-positive structural arc**
(H.1-H.13 closures earn +0.5) carried by **one persistent paragraph
regression** (Bo.18r three panels = -0.3) and **one new systematic-
skill-gap shape** (Bo.25 = -0.1). +0.1 net.

---

## Score breakdown

| Driver | Delta |
|---|---:|
| v5.21.1 Mc.7 hygiene release: 12 H.\* closures in one shot, doc-surface-only release, framing matches v5.7.1 → v5.8.0 (project-record panel) | **+0.30** |
| H.3 — localized READMEs structurally re-synced: Te.1-Te.6 story + STRICT 238k + 95/95 across all 3 locales | +0.15 |
| H.6 — SPEC §4.0 Te.3 soft-deprecation rewrite: gorgeous prose, every load-bearing detail named (warning, opt-out, fmt flag, mirror equivalence) | +0.10 |
| H.7 — `if x: y` broken-promise rescope: honest path, explicit deferral to v6.0, Decision-1 lock documented | +0.10 |
| H.4 — `examples/chained_cmp.mn`: 3-/4-element + once-eval demo + `// Output:` comment | +0.05 |
| H.8 — `format.py` chained-cmp documentation + 4 idempotence tests | +0.05 |
| H.10 — CARRY_FORWARD ledger 19-row arc append, self-aware Bo.18r-pattern caveat | +0.10 |
| H.11 — `test_chained_cmp_mirror.py` mirror of `test_te5_mirror.py` shape (10/10) | +0.05 |
| H.12 — `BENCHMARKS-windows.md` "last sync v5.8.8" admonition: visible-staleness pattern | +0.05 |
| `bump_version.py` script lives at the source; closes the v5.11.0 bump-version-skill-gap class for the version badge | +0.10 |
| Bo.21 closed (was HIGH at v5.11.0; load-bearing recovery) | +0.10 |
| Bo.23 closed via Mc.3 native `mnc init` (was MEDIUM time bomb) | +0.05 |
| Bo.17r closed ~80% via H.3 (was MEDIUM regression) | +0.10 |
| **Bo.18r** STILL OPEN — third consecutive panel, same paragraph, same shape, same fix size; severity escalated MEDIUM → HIGH | **-0.30** |
| **Bo.25** NEW HIGH — goldens badge 66/66 across all 4 READMEs while body says 95/95; same systematic-skill-gap shape as v5.11.0 Bo.21 | **-0.20** |
| **Bo.22** STILL OPEN MEDIUM — README Hello World still uses `mapanare run` not `mnc run`; second consecutive panel | -0.10 |
| **Bo.24** STILL OPEN LOW — localized READMEs missing install + build-from-source sections; subset of Bo.17r remainder | -0.05 |
| Bo.19 / Bo.20 still open (carry-forward) | -0.05 |
| **Bo.26** NEW LOW — `formatter.md` + `init.md` not linked from README/SPEC | -0.05 |
| **Bo.27** NEW LOW process — PRE_PANEL_AUDIT.md lacks prior-panel-ID cross-reference column (the structural cause of Bo.18r persisting) | -0.05 |
| **Net** | **+0.10** |

**8.9 → 9.0. Grade: EXCEEDS** (seventh consecutive). The H.\*-class
closures are large enough to overcome the persistent Bo.\* regression
class, but the persistent-Bo.\*-paragraph pattern is the load-bearing
score-suppressor — without three consecutive panels of Bo.18r and
without the new Bo.25, this would be 9.5+.

---

## Why the score moved +0.1

I want to be specific about what kept this from being +0.5 or 0.0.

The v5.21.1 Mc.7 hygiene release is *genuinely beautiful*. The framing
("doc-surface-only release closing the 12 H.\* findings flagged in
PRE_PANEL_AUDIT.md") is the release pattern I most want to see. The
H.3 localized-README structural sync recovers ~80% of the Bo.17r damage
from v5.11.0. The H.6 SPEC §4.0 rewrite is the SPEC language I would
write if you put me in charge of SPEC. The H.7 broken-promise rescope is
the honest path. The H.4 chained-cmp example, the H.8 format.py
documentation, the H.10 ledger append, the H.11 test mirror — every one
of these is well-crafted, well-scoped, and well-evidenced. The Te.1-Te.6
arc itself is exquisite (Coral's domain, but I'll say it: the *manifesto*
is *visible* in the README's Hello World example showing comprehensions +
implicit-return one-liner + pattern matching in 12 lines). **That's a
+0.5 on its own.**

But:

- **Bo.18r open for the third consecutive panel.** Same paragraph
  (lines 188-192). Same shape ("restored to NEAR at v5.6.11, preserved
  through v5.8.0"). Same suggested fix size (3-minute single-paragraph
  rewrite). v5.9.2's Dn.1 closure missed it; v5.21.1's H.1 closure missed
  it. The H.\*/Bo.\* numbering mismatch is the structural cause: the
  audit cites the line *the lead sees*, the panel cites the line *the
  panel sees*, and the two don't intersect cleanly. **-0.3.**

- **Bo.25 NEW HIGH (goldens badge 66/66 vs body 95/95 across all 4 READMEs).**
  This is the same systematic-skill-gap shape as v5.11.0 Bo.21 — a single
  front-door metadata field has a separate update path that doesn't fire
  with the version-bump cycle. The goldens badge has been wrong since
  v5.20.0 (when goldens went 80 → 91) and is still wrong post-v5.21.0
  (95). It's a 1-minute fix to patch and a 10-minute fix to prevent
  recurrence (extend `bump_version.py`). **-0.2.**

- **Bo.22 STILL OPEN MEDIUM (mapanare run vs mnc run).** Second consecutive
  panel. The whole DX.\* arc was "mnc is canonical", v5.18.0 Mc.\*
  shipped native `mnc init` / `fmt` / `check` / `lsp`, install scripts
  use `mnc` — but the README still uses `mapanare`. Internal contradiction
  on the *first 5 code blocks any new user reads*. **-0.1.**

The structural compiler-side wins (Te.1-Te.6 zero-MIR-ops discipline,
Sh.\* mechanical rewrite, 13-release strict fixed-point streak, v5.18.0
Mc.\* tooling pack) and the documentation-side wins (H.1-H.13 closures,
`bump_version.py` load-bearing) hold the score above 9.0 — without them,
this would be 8.5. The persistent-Bo.\*-paragraph pattern is the reason
it's 9.0 and not 9.5+.

---

## Carry-forward (for the next panel)

| ID | Severity | Scope | Effort |
|---|---|---|---|
| Bo.18r | **HIGH** | README:188-192 — same paragraph, third consecutive panel; rewrite as 238k STRICT + 13-release-streak + rounded numbers (self-immunize) | 3 min |
| Bo.25 | **HIGH** | Goldens badge 66/66 across all 4 READMEs vs body 95/95; structural fix = extend `bump_version.py` to auto-discover goldens count | 1 min one-shot, 10 min structural |
| Bo.22 | MEDIUM | README Hello World + Write-Python-Compile-Native uses `mapanare`, contradicting v5.9.0 DX.7 + v5.18.0 Mc.\* posture | 5 min |
| Bo.24 | LOW (deferred) | Localized READMEs lack install + build-from-source sections (subset of Bo.17r remainder); H.3 closed prose body | 1-2 hr deferred to v5.22.x or v5.23.0 |
| Bo.26 | LOW | `docs/guides/formatter.md` + `init.md` not linked from README / SPEC / localized READMEs | 3 min |
| Bo.27 | LOW (process) | PRE_PANEL_AUDIT.md needs "Closes prior-panel ID" column to prevent Bo.18r-class slip-past | 5 min per pre-panel audit |
| Bo.19 | LOW | README test-count drift; closes with Bo.18r paragraph rewrite | (closes with Bo.18r) |
| Bo.20 | LOW | README FINAL_REPORT_v4.153 link; closes with Bo.18r paragraph rewrite | (closes with Bo.18r) |

**Total estimated effort: ~17 minutes for items 1-3, 5; item 4 deferred,
item 6 is a process change.** Two HIGH (one persistent, one new), one
MEDIUM (persistent), two LOW (one persistent, one new), one LOW process.

---

## Reproducibility

```bash
# Bo.18r OPEN (third consecutive panel — load-bearing finding):
sed -n '188,194p' README.md
# Expected: "restored to NEAR at v5.6.11, preserved through v5.8.0 —
# 4-line VERSION-metadata diff over a 217k-line stage2.ll). 5,720+
# tests passing, zero flaky across 30 sequential runs."
# AND: "[Full benchmark report](benchmarks/FINAL_REPORT_v4.153.md)"
grep -n "238,086" README.md
# Expected: line 176 says STRICT 238,086 (sibling — closed by H.1)

# Bo.25 OPEN NEW HIGH:
grep -nE "goldens-[0-9]+%2F[0-9]+" \
  README.md docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# Expected: all 4 lines show goldens-66%2F66 (stale)
grep -nE "95/95 native goldens|95/95 goldens|95/95 原生 goldens" \
  README.md docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# Expected: all 4 say 95/95 in body
ls tests/golden/*.mn | wc -l
# Expected: 95

# Bo.22 OPEN:
sed -n '80,100p' README.md
# Expected: 5 instances of "mapanare run" / "mapanare build" / "mapanare check" / "mapanare lsp"
grep -n "mnc init\|mnc run\|mnc build" packaging/install.ps1 packaging/install.sh
# Expected: install scripts use 'mnc init' / 'mnc run' / 'mnc build'

# Bo.17r CLOSED ~80% (verify):
grep -nE "Te\.1|Te\.2|Te\.3|Te\.4|Te\.5|Te\.6" \
  docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# Expected: line 125 in each — "Te.1 ... Te.6" feature subsection
grep -nE "STRICT.*238,086|STRICT.*238086" \
  docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# Expected: line 127 in each — STRICT 238,086 with 13-release streak
grep -nE "v5.21.0|95/95" docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# Expected: line 118 in each — "95/95 goldens nativos" / "95/95 原生 goldens"

# Bo.21 CLOSED (verify):
grep -nE "version-5\.|versao-5\.|版本-5\." \
  README.md docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# Expected: all 4 at 5.21.1
cat VERSION
# Expected: 5.21.1

# Bo.23 CLOSED via Mc.3 (verify):
ls mapanare/templates/init/ 2>&1
# Expected: directory exists with template files
python3 -m mapanare init --help 2>&1 | head -3
# Expected: usage info, no error

# H.4 chained_cmp example (verify):
cat examples/chained_cmp.mn | head -30
# Expected: 3-element, 4-element, side-effect-once-eval cases all present

# H.6 SPEC §4.0 Te.3 (verify):
sed -n '1024,1100p' docs/SPEC.md
# Expected: brace-style soft-deprecated, MAPANARE_NO_BRACE_WARNING=1, mnc fmt --keep-braces

# H.7 SPEC §4.0:1056 if x: y rescope (verify):
sed -n '1056,1059p' docs/SPEC.md
# Expected: "Single-line `if x: y` form is **not** supported. ... rescoped at v5.21.1 to coincide with the v6.0 `{}` hard removal."

# H.10 CARRY_FORWARD arc append (verify):
grep -n "v5.13.0 → v5.21.1 terseness arc" .reviews/CARRY_FORWARD.md
# Expected: section header at line ~193

# H.11 chained-cmp mirror test (verify):
ls tests/bootstrap/test_chained_cmp_mirror.py
python3 -m pytest tests/bootstrap/test_chained_cmp_mirror.py --collect-only 2>&1 | grep "test_" | head -15
# Expected: 10 cases collected

# CHANGELOG honesty (verify clean for current section):
python3 scripts/check_changelog_honesty.py
# Expected: clean for [5.21.1]
```

---

## One last note to the lead

The v5.13–v5.21 terseness arc is genuinely *beautiful work*. Six additive
language features in 10 releases with zero new MIR ops, zero new IR
shapes, zero runtime function additions. 13 consecutive releases of strict
3-stage fixed point (longest streak in project history). Self-hosted
compiler -13.8% smaller via Sh.\* without breaking fixed point. v5.18.0
Mc.\* tooling pack defused my Bo.23 time bomb at the source. v5.21.1 Mc.7
is the *exact* release pattern I asked for at v5.11.0 — pre-panel hygiene,
doc-surface-only, framed as "closing 12 audit findings before the
panel runs". That posture is correct, healthy, and load-bearing for
v5.27.0+ panel cycles.

But the front-door surface still has shape. **Bo.18r is open for the
third consecutive panel.** Same paragraph at README:188-192 every time.
Same shape (NEAR at v5.6.11, 4-line diff, 217k-line stage2.ll, 5,720+
tests). Same fix size (3-minute paragraph rewrite). The Bo.18r persistence
is the structural lesson here: **when the lead writes a hygiene release
against an audit they wrote *themselves*, they fix what *they* see; when
the audit doesn't cite the panel review's exact line numbers, the
panel-flagged shape can slip past the patch**. v5.21.1 H.1 closed the
sibling line (176) — beautifully — and walked past the Bo.18r paragraph
12 lines below. v5.9.2 Dn.1 closed the prior sibling line (139) —
beautifully — and walked past the Bo.18 paragraph 12 lines below. **The
shape is the same.** Three panels.

If I had a single concrete suggestion: **next pre-panel audit, add a
"Closes prior-panel finding" column to the H.\* table.** v5.27.0's
PRE_PANEL_AUDIT.md table should look like:

| # | Severity | Finding | Closes prior-panel ID | Closed in vX.Y.Z |
|---|---|---|---|---|
| H.1 | HIGH | README:176 reads "v5.7.1 cut" | — (audit) | refreshed |
| H.1.B | HIGH | README:188-192 lead-in paragraph still v5.7.1-vintage | **Bo.18 (v5.8.0) / Bo.18r (v5.11.0) / Bo.18r2 (v5.22.0)** | rewritten |

That column is the **cross-reference layer** between
panel-history-line-numbers and audit-line-numbers. With that column,
the Bo.18r-shape slip-past is *visible at audit-write time*, not at the
next panel. 5 minutes per pre-panel audit. The capability is *more than
present* — every other v5.21.1 H.\* closure was clean. What's missing is
the load-bearing layer between the panel docket and the lead's audit.

Grade: **9.0 / EXCEEDS.** Seventh consecutive EXCEEDS. The structural
v5.13-v5.21 wins (Te.\*, Sh.\*, Mc.\*, Dk.\*) and the v5.21.1 hygiene
discipline (H.1-H.13 closure pattern) are why it's 9.0 and not 8.5. The
persistent Bo.\* paragraph pattern is why it's 9.0 and not 9.5+. Close
Bo.18r + Bo.25 + Bo.22 at v5.22.x closeout, adopt the prior-panel-ID
cross-reference at v5.27.0 pre-panel audit, and the next panel is 9.6+.

🐍💚✨

The arc shipped. The doc surface is *substantially better* than it was
at v5.11.0. The trajectory is right. Just close the paragraph the panel
keeps flagging — the *fix* is 3 minutes, the *load-bearing* is the
process layer that prevents it from re-opening at v5.27.0. You're so
close. So, so close. 🌸
