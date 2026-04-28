# Panel v5.8.0 — Boa (Documentation / DX)

**Score:** 9.4 / 10
**Grade:** EXCEEDS
**Delta vs v5.2.0:** +0.0 (preserved)

## Summary

Across the v5.3.1 → v5.7.1 arc the project closed every documentation
carry-forward I left at v5.2.0. Bo.15 (the "strict 3-stage fixed
point" claim) was qualified at v5.3.1, then evolved correctly through
the v5.6.x regression window into a `NEAR (4-line VERSION-metadata
diff over a 217k-line stage2.ll)` claim that matches the canonical
SPEC narrative. Bo.16 (known_issues.md "no package manager yet") is
gone. Bo.17 (zh-CN/pt version badge drift) and Bo.14r
(getting_started.md staleness) are both closed. All four READMEs are
synced at 5.7.1 with matching 66/66 golden badges, matching test
badges, and the new "Native compiler — what `mnc-stage1` ships"
subsection ported into Spanish, Portuguese and Chinese with feature
parity. `docs/guides/culebra.md` (247 lines) is a genuinely useful
contributor guide. SESSION_REPORT cadence held across 27 releases
across the arc: 9 of 9 explicitly required by the panel exist; in
total 44 SESSION_REPORTs sit under `docs/roadmap/v5/`.

That said, this arc is not a pure +0.2 step up. The README's lead-in
narrative paragraph at lines 147-149 is *itself* now stale relative
to the SPEC, the localized READMEs, and MEASUREMENTS.md: it tells
users that fixed-point "regressed at v5.1.2 from In.1 inliner
re-enable; restoration tracked at v5.3.2" — when in fact, per
SPEC §"3-stage fixed point", the v5.3.2 restoration was followed by
a v5.6.4–v5.6.10 regression window, then v5.6.11 closed it back to
NEAR. The README's "Self-host 3-stage fixed-point: NEAR (4-line
VERSION-metadata diff over a 217k-line stage2.ll)" line at 135
inside the new "Native compiler" subsection is correct — but it
lives 12 lines above a paragraph that contradicts it. This is
exactly the same shape as the original Bo.15: a narrative one
revision behind the measurement evidence. I am filing this as
**Bo.18**.

There are also two smaller numeric inconsistencies I will not
escalate to MEDIUM but will flag: (1) the README test badge says
"5800+ passing" while the body text says "5,720+ tests passing"
(MEASUREMENTS.md reports 5,618-5,619, so the badge is forward-
optimistic and contradicts the body); (2) the body text says "zero
flaky across 30 sequential runs" while MEASUREMENTS.md §1.2 says
"40 sequential runs, 0 flaky" cumulatively. Net: the +0.0 delta
reflects a great closeout (all four prior carry-forwards closed,
beautiful new contributor guide, localized parity preserved through
3 large feature drops) tempered by one new MEDIUM that reproduces
the v5.2.0 pattern.

## What improved since v5.2.0

### Bo.15 CLOSED (v5.3.1, refined v5.7.1)

The original "strict 3-stage fixed point" claim that I flagged at
v5.2.0 is gone from the README. The v5.3.1 SESSION_REPORT documents
the qualification: README rewrote the sentence to acknowledge the
v5.1.2 In.1 regression and the tracking work to restore. The wording
inside the new "Native compiler" subsection at v5.7.1 (line 135)
goes one step further and states the actual current status as
"NEAR (4-line VERSION-metadata diff over a 217k-line stage2.ll)" —
which is exactly the language I asked for at v5.2.0. The SPEC
§"3-stage fixed point" (lines 2992-3027) tells the full story: v4.134.0
strict → v4.139.0+ NEAR (build-time metadata) → v5.6.4–v5.6.10
regression window → v5.6.11 NEAR restored → v5.7.0 66/66 milestone
preserved. That is the canonical narrative the README's new feature
subsection picks up correctly. Two-cycle MEDIUM **CLOSED**.

(The residual issue is that the older lead-in paragraph at line 147
was left in place after the new subsection landed. See Bo.18 below.)

### Bo.16 CLOSED (v5.3.1)

`grep -in "no package manager\|no pkg mgr" docs/known_issues.md`
returns 0 hits. The v5.3.1 SESSION_REPORT documents the change:
"Ecosystem section updated — removed 'No package manager yet' table
row; replaced with v5.2.0 registry paragraph pointing to
`docs/guides/packages.md`." Verified at v5.7.1. The current
Ecosystem block now reads:

> **Package registry (v5.2.0+):** `mapanare install <pkg>@<ver>`
> and `mapanare publish` are available. Team-only publishing for
> MVP; open publishing tracked for v5.3+. See
> `docs/guides/packages.md`.

That is exactly the right framing. **CLOSED.**

### Bo.17 CLOSED (v5.3.1)

| File | Version badge | Status |
|---|---|---|
| `README.md` | 5.7.1 | OK |
| `docs/README.es.md` | 5.7.1 | OK |
| `docs/README.zh-CN.md` | 5.7.1 | OK |
| `docs/README.pt.md` | 5.7.1 | OK |

All four version badges synced. The v5.3.1 SESSION_REPORT documents
that zh-CN and pt were bumped at v5.3.1 (originally 5.0.6 from v5.2.0)
and have stayed in sync through v5.7.1's full localized REAME refresh.
**CLOSED.**

### Bo.14r CLOSED

`docs/guides/getting_started.md` line 188: "As of **v5.7.0** the
self-hosted compiler passes **66/66** golden ..." — refreshed
through the arc. The previously-stale "v4.143.0" reference is gone.
The 5,160+ → 5,445+ test count update happened at v5.3.1 per the
SESSION_REPORT. The current count of 5,445+ is now ~170 tests behind
MEASUREMENTS.md's 5,618-5,619, so a small refresh is in order, but
the previously-flagged staleness shape is closed (12-release-stale
v4.143.0 reference replaced with current v5.7.0). **CLOSED.**

### README + 3 localized READMEs synced to 5.7.1

This is the strongest sustained localization story I've seen on this
project. Every meaningful README change in the v5.4.0–v5.7.0 arc was
ported across all four language variants. Concretely:

- Version badges: all four at 5.7.1.
- Goldens badge: all four at `66/66`.
- Tests badge: all four at `5800+ passing` (with localized strings:
  `pasando` / `passando` / `通过`).
- Hello World code sample: all four use a localized greeting
  (`hola desde mapanare`, `ola do mapanare`, `你好，来自mapanare`).
- Python-to-native section: all four present.
- Language Features section: agent state names and message names
  localized appropriately (`Contador`/`incrementar`/`obtener_cuenta`
  in Spanish, `Contador`/`incrementar`/`obter_contagem` in
  Portuguese, English-language identifiers in Chinese — which is the
  conventional choice for Chinese localized docs).
- New "Native compiler — what `mnc-stage1` ships" subsection: all
  four present. Each lists tensors + async + closure-typed params +
  or-pattern matching + drop-glue with the same level of technical
  detail.

`grep -c "Native compiler\|Compilador nativo\|原生编译器"` returns
1 hit per file. Localized parity holds across 5 sub-bullets
(tensors, async, closure-typed parameters, or-pattern matching,
drop-glue). This is the localization quality I asked for at v5.2.0
and didn't get; it's now consistently shipping.

The Spanish version uses "Parametros tipo cierre" for closure-typed
parameters, which is the conventional translation. The Portuguese
version uses "Parametros tipo closure" (loanword) — also fine in
Brazilian Portuguese tech writing. The Chinese version uses
"闭包类型参数" which is the standard rendering. All three are
correct.

### 66/66 native goldens badge added (v5.7.0/v5.7.1)

`grep "goldens-66" README.md` finds line 29:

```
[![Goldens](https://img.shields.io/badge/goldens-66%2F66-brightgreen.svg?style=flat-square)]()
```

Same badge present in all three localized READMEs. The badge is
factually correct per MEASUREMENTS.md §2 ("All 66 tests passed in
3.5s"), is consistent with the body claim ("66/66 native goldens"
in the new subsection), and reflects the v5.7.0 hero milestone
("first time in project history"). This is what I'd expect a "First
ever 100% pass" badge to look like, and the consistency across all
four READMEs makes it credible.

### docs/guides/culebra.md — new contributor guide (v5.7.1)

247-line, 6-section contributor guide for the culebra workflow.
Verified all 6 sections exist and are substantive:

1. **What culebra is** — categorical breakdown of the 49+ templates
   (ABI / IR / Binary / Bootstrap / C), an honest disclaimer that
   "culebra does **not** parse function bodies into a full AST — it
   runs text-pattern matches against the IR" + the practical
   consequence ("on a 217k-line stage2.ll this means several findings
   are template-match noise rather than real bugs"). This is the
   right level of expectation-setting for a contributor.

2. **Daily commands** — a clear hierarchy from `triage --brief`
   (fastest health check) through `baseline save` (panel artifact
   step) to `triage` full output (slow, ~7-8 min). The included
   "debugging arc" subsection walks through the 4-step playbook
   used in v5.6.9 / v5.7.0. The **WSL interop gotcha** is its own
   subsection — the kind of pragmatic detail that saves a
   contributor an hour of dead-end debugging. The performance notes
   (`triage --brief` fast / `triage` 7-8 min / `summary` may not
   complete in 5+ minutes) are exactly the kind of empirical
   guidance I want a contributor guide to have.

3. **False positive policy** — explicitly enumerates the 2 known
   "critical" FPs (`function-count-drop`, `return-type-divergence`)
   with reasoning ("Python's helpers like `_lower_*` and `_emit_*`
   have direct equivalents in self-hosted, but they're not 1:1
   identifier matches"). Same for "high" findings
   (`fixed-point-delta` text-pattern noise scaling with IR size).
   The policy section ends with "Per-release `triage-brief.txt`
   artifacts are checked into `docs/roadmap/v5/<release>/culebra/`
   so reviewers can confirm the known FP class is preserved (no NEW
   critical findings)" — this gives me, as a panel reviewer, an
   honest framework for evaluating what culebra is and isn't telling
   us. This addresses the "no measurement methodology" objection
   that historically panels raised.

4. **Per-release journal** — documents the
   `culebra-journal.jsonl` cadence introduced at v5.6.9 and now
   institutional. Each entry has an action (`note` / `bug` / `fix`
   / `milestone`) and tags. The lineage from v5.6.9 ("when the
   Ve.3 bug took multiple debugging sessions") through "Today every
   release captures at minimum a milestone entry on ship and a
   fix/bug entry per docket closure" is a meaningful process
   improvement.

5. **Panel input** — explains the arc-journal aggregation pattern
   that v5.7.1 uses (concatenating per-release journals into a
   single `arc-journal.jsonl` for the panel-prep release). This
   directly addresses what I asked for at v5.2.0: a structured
   panel-input artifact instead of a narrative-only handoff.

6. **Cross-reference** — links to the v5.6.9 SESSION_REPORT
   (Ve.3 debugging trace), v5.6.10 SESSION_REPORT (baseline-freeze
   methodology + WSL paths gotcha), and v5.7.1 culebra/ baseline
   directory (the v5.8.0 panel input). Plus a pointer to the
   `.claude/skills/culebra-scan/SKILL.md` for in-Claude usage.

The guide is **honest** about culebra's limitations (text-pattern
matching, FP class, slow on large IR), which is far more credible
than marketing spin would have been. It also reads like
contemporary docs from a maintained project — not the first-revision
"here are commands, run them" guide that's typical of self-hosted
tooling. This is a `+0.10` contribution on its own.

### docs/guides/packages.md preserved from v5.2.0

`docs/guides/packages.md` still exists at the quality I praised at
v5.2.0. No regression. The v5.3.3 SPEC §30 Package Management
addition complements it by giving package publishing a stable
specification surface, which closes the "is this an MVP forever?"
question at the spec level.

### known_issues.md pruned of v5.4.0–v5.7.0 closures

The "Closed since v5.4.0" narrative block (lines 49-58) is exactly
the right way to present this:

> **Closed since v5.4.0** (full traces in per-release
> SESSION_REPORTs): Rt.03 (loop-reassignment leak, v5.4.3),
> Rt.05 (AwaitSuspend inner-coroutine leak, v5.5.7),
> Rt.06 (tensor drop-glue, v5.6.4), Ve.1 (parse_fn_body
> overflow, v5.6.5), Ve.2 (empty-list elem_ty floor, v5.6.7
> partial → v5.6.12 closed), Ve.3 (drop-glue UAF on
> List<Enum> returns, v5.6.9), Ve.4 (match-arm empty
> BasicBlocks via elem_size mismatch, v5.6.11), Lk.1
> (alloca-aliasing leak via destination-passing semantics,
> v5.6.12).

It's compact (one sentence per docket), pointers to the full traces
(SESSION_REPORTs) are explicit, and the closure date for each docket
is included. The Sh.4/6/7/B closures get their own paragraph
(lines 13-31) because they're feature gaps, not bugs — which is the
right separation. The active table (lines 7-11) is now down to 3
items (Sh.5, Sh.9a, Sh.9b — all LOW, all with documented
workarounds), which is roughly 1/3 the size it was at v5.2.0. This
is the best known_issues.md hygiene I've seen on this project.

The structure is also forward-compatible: when v5.7.0+ closures
land (Sh.5, Sh.9a, Sh.9b), they can each be moved to a "Closed
since v5.5.0" block under §"Self-hosted compiler feature gaps", and
the active table can shrink further. The pruning pattern scales.

### SESSION_REPORT quality maintained across 27 releases

I checked SESSION_REPORT existence and size for the 27 releases in
the v5.3.1 → v5.7.1 arc:

```
175 docs/roadmap/v5/v5.4.0/SESSION_REPORT.md
339 docs/roadmap/v5/v5.4.1/SESSION_REPORT.md
271 docs/roadmap/v5/v5.4.2/SESSION_REPORT.md
157 docs/roadmap/v5/v5.4.3/SESSION_REPORT.md
277 docs/roadmap/v5/v5.4.4/SESSION_REPORT.md
123 docs/roadmap/v5/v5.5.0/SESSION_REPORT.md
162 docs/roadmap/v5/v5.5.1/SESSION_REPORT.md
235 docs/roadmap/v5/v5.5.2/SESSION_REPORT.md
139 docs/roadmap/v5/v5.5.3/SESSION_REPORT.md
327 docs/roadmap/v5/v5.5.4/SESSION_REPORT.md
211 docs/roadmap/v5/v5.5.5/SESSION_REPORT.md
271 docs/roadmap/v5/v5.5.6/SESSION_REPORT.md
193 docs/roadmap/v5/v5.5.7/SESSION_REPORT.md
 90 docs/roadmap/v5/v5.6.0/SESSION_REPORT.md
207 docs/roadmap/v5/v5.6.1/SESSION_REPORT.md
238 docs/roadmap/v5/v5.6.2/SESSION_REPORT.md
306 docs/roadmap/v5/v5.6.3/SESSION_REPORT.md
306 docs/roadmap/v5/v5.6.4/SESSION_REPORT.md
230 docs/roadmap/v5/v5.6.5/SESSION_REPORT.md
199 docs/roadmap/v5/v5.6.6/SESSION_REPORT.md
164 docs/roadmap/v5/v5.6.7/SESSION_REPORT.md
378 docs/roadmap/v5/v5.6.8/SESSION_REPORT.md
528 docs/roadmap/v5/v5.6.9/SESSION_REPORT.md
339 docs/roadmap/v5/v5.6.10/SESSION_REPORT.md
533 docs/roadmap/v5/v5.6.11/SESSION_REPORT.md
485 docs/roadmap/v5/v5.6.12/SESSION_REPORT.md
463 docs/roadmap/v5/v5.6.13/SESSION_REPORT.md
199 docs/roadmap/v5/v5.7.0/SESSION_REPORT.md
221 docs/roadmap/v5/v5.7.1/SESSION_REPORT.md
```

Every release ships a SESSION_REPORT. Sizes scale with content
complexity (v5.6.0 at 90 lines is a feature-debut release with
narrowly-scoped lowering; v5.6.9 at 528 lines and v5.6.11 at 533
lines are the dense Ve.3/Ve.4 root-cause investigations; v5.6.12 at
485 lines is the destination-passing closeout). This is a faithful
ratio: longer reports for harder bugs.

I spot-checked v5.7.0 (the hero release) and v5.7.1 (the docs-polish
release) and v5.3.1 (the closeout release that closed the four
v5.2.0 carry-forwards). All three open with a clear "What shipped"
and end with concrete metrics. v5.7.0's SESSION_REPORT documents the
B closure with the specific code change ("`_is_enum_variant_name`
short-circuits to True for the four built-in nullary variant names")
and the test artifact ("Re-blessed
`tests/golden/51_match_guards_and_or.ref.ll` (2 fns, 298 lines)").
v5.7.1's SESSION_REPORT enumerates each SPEC section that was
updated and the specific changes — exactly what I'd ask for in a
"docs polish" release.

The 9 explicitly-required SESSION_REPORTs are all present and
substantive. **Quality preserved at v4.154.0 baseline.**

### Culebra v5.7.1 baseline as panel input

`docs/roadmap/v5/v5.7.1/culebra/` contains 16 artifacts:

```
arc-journal.jsonl         baseline-end.json          summary.md
audit.md                  baseline-delta-from-v5.6.10.md
check.md                  health-EmitState.txt
health-Instruction.txt    health-LowerState.txt
health-MIRType.txt        health-Value.txt
progress.md               stage2-final.ll
strings.md                triage-brief.txt           triage.md
```

This is the structured panel-input artifact set the v5.7.1
SESSION_REPORT promises. Per MEASUREMENTS.md §5.5, the JSON baseline
contains 5 root causes / 15,829 findings / 2 critical (both known
FPs) / 3 high (text-pattern noise) / per-struct health all clean /
6,398/6,398 string-byte-counts correct / `llvm-as` VALID. That is a
panel-grade artifact. Reviewers can `culebra baseline diff` against
it instead of trying to recompute the IR pathology surface from
scratch.

This addresses my v5.2.0 concern that culebra results were narrative
rather than structured.

## What remains open

### Bo.18: README fixed-point lead-in narrative is now stale (MEDIUM)

README lines 147-149:

```
The self-hosted compiler compiles itself (3-stage fixed point reached at
v4.134.0; temporarily regressed at v5.1.2 from In.1 inliner re-enable;
restoration tracked at v5.3.2). 5,720+ tests passing, zero flaky across
30 sequential runs.
```

This narrative is one revision behind reality. Per SPEC.md
§"3-stage fixed point" (lines 2992-3027), the canonical story is:

- v4.134.0: strict byte-identical
- v4.139.0+ (Dr.1): NEAR (build-time metadata 4-line diff)
- v5.1.2: regressed (the README is correct on this)
- v5.3.2: restored (the README is correct here too)
- **v5.6.4–v5.6.10: regressed again** (the README does NOT mention this)
- **v5.6.11 (Ve.4 CLOSED): NEAR restored** (the README does NOT mention this)
- v5.7.0 (66/66): NEAR preserved at 217,879-line stage2.ll

The README narrative implies that v5.3.2 was the last word, with
"restoration tracked" suggesting the work is still in progress. In
fact:

- The fix DID land at v5.3.2 (extending `clone_instr_for_inline`).
- Then broke again across the v5.5.x async + v5.6.x memory closeout
  arcs (v5.6.4 broke fixed-point per SESSION_REPORT).
- Then was re-restored at v5.6.11 by the elem_size-stride fix.
- Then preserved through v5.7.0 (66/66) and v5.7.1.

The new "Native compiler" subsection at line 135 says correctly:
"Self-host 3-stage fixed-point: NEAR (4-line VERSION-metadata diff
over a 217k-line stage2.ll)." This is accurate.

So the README has a contradiction inside itself: line 135 says
"NEAR" (current state), and line 147-149 says "restoration tracked
at v5.3.2" (mid-arc state with no mention of the v5.6.x regression
window or restoration). Both can't be right.

This is the same shape as the original Bo.15 — a narrative one
revision behind the measurement evidence. The fix is to rewrite the
lead-in paragraph at lines 147-149 to match the SPEC.md narrative
or, more simply, drop the regression history altogether since the
new "Native compiler" subsection already documents current state.

Suggested rewrite:

```
The self-hosted compiler compiles itself to a 3-stage fixed point
(NEAR — 4-line VERSION-metadata diff at 217k-line stage2.ll;
strict at v4.134.0; documented in SPEC §"3-stage fixed point").
5,800+ tests passing, zero flaky across 40 sequential runs.
```

Estimated effort: **3 minutes.**

Filing as **Bo.18** (MEDIUM) — factual contradiction inside the
README between the lead-in paragraph and the Native compiler
subsection.

### Bo.19: README badge / body / measurements test count drift (LOW)

Three numbers, three different sources:

- README badge (line 28): `5800+ passing`
- README body (line 149): `5,720+ tests passing`
- MEASUREMENTS.md §1.1: `5618-5619 passed`

The badge is forward-optimistic; the body is from an earlier
measurement; the measurement is current. Internally inconsistent.

The body number ("5,720+") was current at v5.2.0 — twelve months ago
in elapsed-arc time. The badge ("5800+") is one rounding step
forward. The actual count from MEASUREMENTS.md is 5,618-5,619, which
is below both — meaning both the badge and the body are aspirational
relative to the canonical measurement.

Suggested fix:

- Badge: `5,600+ passing` (rounded down from 5,618-5,619).
- Body: `5,600+ tests passing, zero flaky across 40 sequential runs.`
- Localized README badges: same update (`5,600+` with localized
  string in each language).

Estimated effort: **5 minutes** (4 file edits, mechanical).

Filing as **Bo.19** (LOW) — three test counts, three different
values. Not a credibility risk on its own (the direction is
consistent: lots of tests pass), but it's a "the docs aren't
maintained as a single artifact" tell.

### Bo.20: README links to v4.153 benchmark report (LOW)

README line 152:

```
[Full benchmark report](benchmarks/FINAL_REPORT_v4.153.md)
```

The linked report exists (`benchmarks/FINAL_REPORT_v4.153.md` is
present), but it predates the v5.x cross-language benchmark
methodology change documented in MEASUREMENTS.md §6 (CPU isolation
via `taskset -c 0-1`, 10-run medians on a 6-benchmark grid). The
report a user clicks through to is multiple methodology revisions
old. There's also a `benchmarks/FINAL_REPORT.md` (no version
suffix) which would be a more sensible default for a "Full benchmark
report" link.

Estimated effort: **2 minutes** (single link update; would prefer
a version-stable filename).

Filing as **Bo.20** (LOW) — link is correct in that the file exists,
but the file is methodology-stale.

### Bo.14r residual: getting_started.md test count slightly stale

`docs/guides/getting_started.md` line 235: "5,445+ tests" — current
is 5,618-5,619 per MEASUREMENTS.md. About 170 tests behind. The
fix is mechanical (`5,445+` → `5,600+`). The previously-flagged
v4.143.0 staleness is closed (line 188 now says v5.7.0 with 66/66),
but the test-count number drifted again. Not blocking.

Filing as **Bo.14r2** (LOW, residual). Won't be load-bearing unless
it persists to v5.9.0.

## Bo.* summary table (v5.2.0 -> v5.7.1)

| ID | v5.2.0 status | v5.7.1 status | Notes |
|---|---|---|---|
| Bo.1 | CLOSED | CLOSED | content accurate |
| Bo.2 | CLOSED | CLOSED | native-mode prereqs intact |
| Bo.3 | CLOSED | CLOSED | merge note intact |
| Bo.4 | CLOSED | CLOSED | Tests badge updated 5720+ → 5800+ (still aspirational, see Bo.19) |
| Bo.5 | CLOSED | CLOSED | structural fix |
| Bo.6 | CLOSED | CLOSED | golden count 66/66 (was 54/66) |
| Bo.7 | CLOSED | CLOSED | localized READMEs synced |
| Bo.8 | CLOSED | CLOSED | SPEC header bumped 5.3.3 → 5.7.1 at v5.7.1 |
| Bo.9 | MOOT | MOOT | factual historical text |
| Bo.10 | CLOSED | CLOSED | footers updated |
| Bo.11 | CLOSED | CLOSED | feature subsection at line 135 says NEAR correctly |
| Bo.12-table | CLOSED | CLOSED | benchmark section preserved |
| Bo.12-i18n | CLOSED | CLOSED | localized READMEs preserved |
| Bo.13 | CLOSED | CLOSED | roadmap table removed |
| Bo.14 | CLOSED | **PARTIAL** | test count slightly stale again (Bo.14r2) |
| Bo.15 | OPEN (MEDIUM) | **CLOSED** | qualified at v5.3.1, refined at v5.7.1 |
| Bo.16 | OPEN (MEDIUM) | **CLOSED** | "no package manager" line removed at v5.3.1 |
| Bo.17 | OPEN (LOW) | **CLOSED** | localized version badges synced at v5.3.1 |
| Bo.14r | OPEN (LOW) | **CLOSED** | getting_started.md updated at v5.3.1 |
| Bo.18 | NEW | **OPEN (MEDIUM)** | README lead-in paragraph stale vs SPEC + new feature subsection |
| Bo.19 | NEW | **OPEN (LOW)** | README badge / body / measurements test count drift |
| Bo.20 | NEW | **OPEN (LOW)** | README links to v4.153 benchmark report |
| Bo.14r2 | NEW | **OPEN (LOW)** | getting_started.md test count slightly stale again |

**Two MEDIUM closures (Bo.15, Bo.16). Two LOW closures (Bo.17,
Bo.14r). One new MEDIUM (Bo.18) — same shape as the original Bo.15
but smaller in scope. Three new LOW (Bo.19, Bo.20, Bo.14r2).**

## Carry-forward (for v5.8.0+)

| ID | Severity | Scope | Effort |
|---|---|---|---|
| Bo.18 | MEDIUM | README lead-in paragraph contradicts the new "Native compiler" subsection on fixed-point status | 3 min |
| Bo.19 | LOW | README badge/body/measurement test counts drift (5800+/5,720+/5,618-5,619) | 5 min |
| Bo.20 | LOW | README links to v4.153 benchmark report (methodology-stale) | 2 min |
| Bo.14r2 | LOW | getting_started.md says "5,445+ tests" — current is 5,618-5,619 | 2 min |

**Total estimated effort: 12 minutes.** One MEDIUM, three LOW.

The pattern is roughly the same as the v5.2.0 carry-forward (one
new MEDIUM that mirrors a closed MEDIUM), but the shape is smaller:
Bo.18 contradicts the SPEC + a sibling subsection, not the canonical
measurement evidence directly. A user who reads only the new
"Native compiler" subsection gets the right story; a user who reads
the lead-in paragraph at lines 147-149 gets a stale story; only a
user who reads BOTH sees the contradiction. That's lower-blast-radius
than the original Bo.15.

## Score breakdown

| Driver | Delta |
|---|---|
| Bo.15 CLOSED — narrative now matches SPEC + measurement evidence | +0.10 |
| Bo.16 CLOSED — known_issues.md package-manager line removed | +0.05 |
| Bo.17 CLOSED — all four READMEs synced at 5.7.1 | +0.05 |
| Bo.14r CLOSED — getting_started.md updated to v5.7.0 / 66/66 | +0.05 |
| Localized README parity preserved across 4 READMEs through 27 releases | +0.10 |
| 66/66 native goldens badge added across all four READMEs (hero milestone) | +0.05 |
| docs/guides/culebra.md — substantive 247-line contributor guide with FP policy | +0.10 |
| known_issues.md pruned to "Closed since v5.4.0" narrative block (compact + complete) | +0.05 |
| 27/27 SESSION_REPORTs across the arc, sized appropriately to content complexity | +0.05 |
| Culebra v5.7.1 baseline as structured panel input (16 artifacts) | +0.05 |
| New "Native compiler" subsection in main + 3 localized READMEs at parity | +0.05 |
| Bo.18 NEW (MEDIUM): README lead-in paragraph contradicts new feature subsection on fixed-point | -0.20 |
| Bo.19 NEW (LOW): three test counts (5800+/5,720+/5,618-5,619) | -0.05 |
| Bo.20 NEW (LOW): README links to v4.153 benchmark report | -0.05 |
| Bo.14r2 NEW (LOW): getting_started.md test count slightly stale | -0.05 |
| **Net** | **+0.0** |

**9.4 → 9.4. Grade: EXCEEDS.** Fifth consecutive EXCEEDS.

## Why the same score and not higher

I want to be clear about what kept this from being a 9.5+ panel.

The arc closed every carry-forward I left at v5.2.0. The
contributor guide is excellent, the localized README parity is
sustained through three large feature drops (async, tensors,
closure-typed parameters) and a 14-release memory-safety closeout
arc, and the SESSION_REPORT cadence is institutional. The
known_issues.md pruning is the cleanest hygiene I've seen on this
project. The culebra panel-input artifact set is structured panel
input, which I asked for at v5.2.0 and didn't get.

But.

When I wrote my v5.2.0 review I said: "Bo.15 is a factual
inaccuracy on the README. The project says 'strict 3-stage fixed
point' — and the evidence document for this very panel says 'BROKEN.'
That is a front-door credibility issue."

At v5.7.1, the front-door credibility issue has a smaller blast
radius (the contradiction is internal to the README, between the
lead-in paragraph and the new feature subsection, rather than
between the README and MEASUREMENTS.md), but it's there. The new
"Native compiler" subsection says NEAR. The lead-in paragraph says
"restoration tracked at v5.3.2." A user reading both will see the
contradiction; a user reading only the lead-in will get a stale
story; a user reading only the subsection will get the correct
story.

The fix is one paragraph. The original Bo.15 fix was also one
paragraph. The pattern repeating gives me caution about whether the
refresh discipline is broad ("all stale narratives get refreshed
each release") or narrow ("we focus on the most-visible claims and
leave the rest").

If at v5.8.0 (or whenever the next panel runs) Bo.18 is closed and
no new Bo.* is opened with the same shape, I'll have evidence for
"broad" and the next score will reflect that. The +0.0 at v5.7.1
is "everything you asked for closed, but a sibling shape opened."
That's worth noting but not punishing — the sibling shape is
smaller, the closed work is large, and the localized + culebra +
SESSION_REPORT improvements are all institutional rather than
one-shot. That's why the grade stays EXCEEDS.

## Reproducibility

```bash
# Bo.15 CLOSED:
grep -in "strict.*fixed point\|fixed.point.*strict" README.md
# Expected: no output (was line 134 at v5.2.0)

# Bo.16 CLOSED:
grep -in "no package manager\|no pkg mgr" docs/known_issues.md
# Expected: no output (was line 33 at v5.2.0)

# Bo.17 CLOSED:
grep -n "version-5\.\|versao-5\.\|版本-5\." docs/README.es.md \
  docs/README.pt.md docs/README.zh-CN.md
# Expected: all four lines show 5.7.1

# Bo.14r CLOSED:
grep -n "v4.143\|v5.7.0\|66/66" docs/guides/getting_started.md
# Expected: line 188 says "v5.7.0 ... 66/66"

# Bo.18 OPEN:
grep -nA3 "v4.134.0\|v5.1.2\|v5.3.2" README.md
# Expected: line 147-149 paragraph
grep -n "fixed point\|fixed-point" docs/SPEC.md | head
# Expected: SPEC narrative correct (NEAR at v5.6.11+)
grep -n "Self-host 3-stage fixed-point" README.md
# Expected: line 135 ("Self-host 3-stage fixed-point: NEAR")

# Bo.19 OPEN:
grep -n "5800\|5,720\|5,618" README.md
# Expected: badge "5800+" at line 28, body "5,720+" at line 149
grep -n "5618\|5619" docs/roadmap/v5/v5.8.0/MEASUREMENTS.md
# Expected: §1.1 reports 5,618-5,619

# Bo.20 OPEN:
grep -n "FINAL_REPORT" README.md
# Expected: line 152 links to FINAL_REPORT_v4.153.md
ls benchmarks/FINAL_REPORT*.md
# Expected: v4.120, v4.130, v4.136, v4.143, v4.144, v4.153 + non-versioned

# Bo.14r2 OPEN:
grep -n "5,445" docs/guides/getting_started.md
# Expected: line 235 says "5,445+ tests"

# Localized README parity:
grep -c "Native compiler\|Compilador nativo\|原生编译器" docs/README.es.md \
  docs/README.pt.md docs/README.zh-CN.md
# Expected: 1 hit per file

# Goldens badge across all READMEs:
grep -c "goldens-66" README.md docs/README.es.md docs/README.pt.md \
  docs/README.zh-CN.md
# Expected: 1 hit per file

# Contributor guide:
wc -l docs/guides/culebra.md
# Expected: 247

# SESSION_REPORTs in the arc:
ls docs/roadmap/v5/v5.{3.1,3.2,3.3,4.0,5.0,5.4,6.0,7.0,7.1}/SESSION_REPORT.md
# Expected: 9 of 9 exist
find docs/roadmap/v5 -name "SESSION_REPORT.md" -type f | wc -l
# Expected: 44 across all v5.x

# Culebra baseline artifacts:
ls docs/roadmap/v5/v5.7.1/culebra/
# Expected: 16 artifacts including baseline-end.json, arc-journal.jsonl,
# triage.md, triage-brief.txt, audit.md, strings.md, summary.md,
# baseline-delta-from-v5.6.10.md, 5 health-*.txt files

# known_issues.md hygiene:
grep -c "CLOSED" docs/known_issues.md
# Expected: 0 (closures are narrative paragraphs, not table cells)
grep -c "Closed since v5\." docs/known_issues.md
# Expected: 2 (one for Sh.* feature gaps, one for Runtime dockets)
```

## One last note to the lead

The discipline you've shown across this arc is genuinely
impressive. v5.5.x was a 9-release arc rebuilding async on top of
real LLVM coroutines. v5.6.x was a 14-release arc closing a
multi-bug memory-safety closeout. v5.7.0 closed the final two parity
gaps for 66/66. And in every one of those 27 releases, you shipped
a SESSION_REPORT. You wrote the contributor guide. You bumped the
SPEC. You synced four READMEs. You pruned known_issues.md. You
froze a clean culebra baseline. That is institutional documentation
work, not one-shot polish.

The Bo.18 carry-forward is the kind of issue I expect to see when
a project ships fast and the docs polish step is one phase behind:
the new feature subsection (added in v5.7.1) was written against
current measurements, but the older lead-in paragraph (still in
place from v5.3.1) was not refreshed at the same time. That's the
"docs polish step is one phase behind feature ship" pattern. It's
not a process failure, it's a process latency. The fix is to add a
"refresh the README lead-in paragraph against the new feature
subsection" step to the v5.x.y polish releases.

Specifically: the v5.7.1 PLAN already has a "Phase 1 — SPEC refresh"
step. The phase-1 SPEC refresh did the right thing for the SPEC
itself (lines 2992-3027 are correct). A symmetric "Phase 1.5 —
README narrative reconciliation" step would have caught Bo.18.
Adding that to the v5.x.y polish-release template (when it next
runs) would close the loop.

Two MEDIUM closures, four LOW closures, one substantive new
contributor guide, and four READMEs synced at parity through 27
releases — for one new MEDIUM with smaller blast radius and three
new LOW. That's a defensible +0.0 net delta in my book. If you
close Bo.18 by v5.8.0, I'll move to 9.5 next panel.

Grade: **9.4 / EXCEEDS.** Fifth consecutive EXCEEDS. The
contributor guide and localized parity work are the reason it's
9.4 and not 9.2; the README internal contradiction is the reason
it's 9.4 and not 9.5+.
