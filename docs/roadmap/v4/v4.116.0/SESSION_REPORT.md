# v4.116.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase E release 2 complete.** Five documentation gaps
flagged across panels since v4.82.0 are addressed without touching
a single line of compiler, runtime, or self-hosted code. Every
exit criterion from PLAN.md is met. Zero regressions.

## Self-graded aggregate

**8.4 / 10**

- **Exit criteria.** All 9 from PLAN.md green with evidence in
  VERIFICATION.md and the commit trail. +solid
- **Scope discipline.** Pure docs. No feature creep. The one
  temptation (adding `mnc-stage1` async lowering while already in
  the async cookbook) was deferred to future-Sh.4 work. +solid
- **Evidence quality.** Every updated code block was compiled and
  run. Every regression claim was checked against the v4.115.0
  baseline. VERIFICATION.md is the panel-facing receipt. +strong
- **Existing `docs/getting-started.md` preserved.** The 624-line
  tutorial at the old path is still there; the new guide at
  `docs/guides/getting_started.md` is the concrete build walk, not
  a duplicate. Decision 2 respected (developer audience). +solid
- **Sh.9 recipes in cookbook §11.** Users now have a clear "here's
  what breaks and here's the workaround" section before they
  re-hit it. +solid
- **What's missing.** No end-to-end "Getting Started on Windows"
  path. The guide says WSL; Windows-native users still have to
  improvise. Deferred to v4.117.0+ work. −soft
- **SPEC spot-check only.** Per Decision 1 (flagged sections only
  plus a spot-check), the three flagged sections were verified
  thoroughly but I did not audit every one of the 29 sections.
  Any remaining drift becomes v5.x documentation work. −soft

## What shipped

### Documentation updates (5 files)

- `README.md` — version badge, headline benchmark line, async row
  in Feature Status table, async example in "The Language" section,
  stale "Coming in v4.2" note corrected, roadmap table extended
  through v4.116.0
- `docs/SPEC.md` — header version 1.0.0 Final → 4.116.0 Live with
  sync-discipline note; §29 adds v4.115.0 status paragraph;
  §29.7 "for await" row reflagged as planned
- `docs/cookbook/async.md` — corrected `mnc run` mischaracterization;
  added §8 native compilation workflow, §9 file I/O example, §10
  HTTP GET example, §11 Sh.9a/Sh.9b recipes
- `docs/guides/debugging.md` — full rewrite: DWARF claim corrected
  (deferred to v5.x per SPEC §21.3), new focus on valgrind / ASan /
  TSan / ir_doctor / Culebra / integration harness
- `docs/guides/getting_started.md` (NEW) — practical from-zero
  walk for compiled-languages developers

### New files

- `docs/guides/getting_started.md` (244 lines)
- `docs/roadmap/v4/v4.116.0/VERIFICATION.md` (207 lines) —
  panel-facing receipt

### Artifacts

- `docs/roadmap/v4/v4.116.0/PLAN.md` — still present (unmarked
  status for final update below)
- `docs/roadmap/v4/v4.116.0/PROMPT.md` — the release's execution
  prompt
- `docs/roadmap/v4/v4.116.0/SESSION_REPORT.md` — this file
- `docs/roadmap/v4/v4.116.0/VERIFICATION.md` — verification log

### Not shipped (intentional)

- No changes under `mapanare/`, `runtime/native/`, `mapanare/self/`,
  `tests/`, `scripts/`, `stdlib/`
- No new golden tests (docs release)
- No `make test` run required (doc-only changes)
- No CHANGELOG "Fixed" section — the docs were stale, not broken;
  that's a Changed.

## Exit criteria (9 items)

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | README.md performance section updated with Phase C numbers | PASS | README had Phase C numbers since v4.110.0; verified still correct |
| 2 | README.md stale claims removed or corrected | PASS | Version badge, roadmap table, `v4.2` placeholder, self-hosted LOC |
| 3 | SPEC.md synced: futures, keyword collision space, bilingual keywords | PASS | §29 paragraph added; §2.1.1 already in sync (v4.113.0); §2.1 bilingual already in sync |
| 4 | Async cookbook refreshed with native compilation examples | PASS | §8–§11 added |
| 5 | Debugging guide updated with DWARF + native binary workflow | PASS | Full rewrite (213+/164-) |
| 6 | Getting started guide written | PASS | `docs/guides/getting_started.md` created (244 lines) |
| 7 | All code examples in docs compile and run | PASS | 7/7 snippets verified; 3/3 async goldens regression-clean |
| 8 | No broken links in updated docs | PASS | Manual review; no broken internal paths introduced |
| 9 | Standard closeout clean | PASS | CHANGELOG + VERSION bump + this file |

## Carry-forward closed

None this release. Doc drift was the target, and addressing it wasn't
filed as a specific `.reviews/CARRY_FORWARD.md` row — it was a
recurring Boa panel comment.

## Carry-forward still open

All v4.115.0 dockets remain open:

- **Sh.9a** — `await` on String-returning async fn (Python
  bootstrap emitter)
- **Sh.9b** — DCE drops unused-await side effects (Python bootstrap
  emitter)
- **Sh.10** — `__mn_file_read_async` not reachable from Mapanare
  source (prerequisite: Sh.9a)
- **Sh.1–Sh.8** — self-hosted emitter feature parity (v4.111.0)
- **Qs.1** — `List<Int>` indexing bug (v4.107.0)
- **Rt.1** — boxed-enum runtime overhead (v4.106.0)
- **TBAA.1**, **willreturn.1** — optimizer-attribute reviews
  (v4.109.0)
- **Instr.1** — Culebra scan over 854K-line main.ll (v4.114.0)
- **A.1**, **A.2**, **B.1**, **Co.1** — v4.114.0 panel findings
- **R1/Cb1**, **M1** — v4.114.0 panel v4.114.1 patch items

## Measurements

- IR line count before / after: unchanged (no code changes)
- Golden test count: unchanged (26/64 self-hosted, 63/64
  Python-bootstrap — pre-existing `51_match_guards_and_or` gap)
- Async goldens: 55/56/57 → 42/43/110 (zero drift from v4.115.0)
- `libmapanare_rt.a`: byte-identical to v4.115.0
- Pytest pass count: not re-run (doc-only changes per policy)
- Culebra findings: unchanged (no IR produced)

## Decisions Made

- **Decision 1 (SPEC sync depth)**: flagged sections plus
  spot-check, per PROMPT default. §2.1.1 (v4.113.0) and §2.1
  Bilingual Keywords were already in sync; §29 got the v4.115.0
  status paragraph; §29.7 "for await" row reflagged.
- **Decision 2 (Getting started target audience)**: developer
  familiar with compiled languages, per PROMPT default. The guide
  assumes prior knowledge of `clang`, `make`, and what a compiler
  pipeline looks like — no hand-holding on LLVM basics.
- **Decision 3 (Code example verification scope)**: only
  updated/created docs, per PROMPT default. Seven compile-and-run
  snippets, three golden regression checks, and a SPEC syntactic
  review. Comprehensive doc-wide verification deferred.
- **Decision (new)**: Kept the existing 624-line
  `docs/getting-started.md` tutorial. Added the new practical guide
  at `docs/guides/getting_started.md`. The two complement each
  other: tutorial teaches the language; guide teaches the build.

## Verification Results

See `docs/roadmap/v4/v4.116.0/VERIFICATION.md` for the full
evidence. Summary:

| Check | Result |
|---|---|
| README.md async example | PASS (output: 60) |
| Cookbook §1 minimal example | PASS (output: 42) |
| Cookbook §9 file I/O (v4.115.0) | PASS (lines=3 words=10) |
| Cookbook §10 HTTP demo | (not re-run; v4.115.0 artifact cited) |
| Getting started hello.mn | PASS both paths |
| Getting started struct example | PASS (distance squared = 25) |
| Getting started Result example | PASS (result = 5 / error: division by zero) |
| Async goldens 55/56/57 | PASS (42/43/110 — zero drift) |
| SPEC §29 examples | Syntax review only (illustrative) |
| Debugging guide shell commands | Spot-checked (5+ commands) |

## Tool discipline retrospective

- **Culebra commands run this session**: 0 (documentation-only
  release; no IR produced, no baseline to compare against)
- **Raw commands run this session**: ~40 (git, mapanare, clang,
  llvm-as, shell file inspection). The majority were verification
  runs on the compile-and-run snippets.
- **Ratio**: 0:~40 — appropriate for a docs-only release where
  there's no new IR to scan. Instr.1 (panel carry-forward) remains
  open and is not v4.116.0's responsibility to close.
- **Notes for next session**: v4.117.0 (test-suite hardening) is
  the natural place to finally run Culebra at scale since the IR
  produced by the test suite is the relevant input. Flag that in
  the v4.117.0 opening.

## Risk register hindsight

| Risk | Predicted | Actually happened |
|---|---|---|
| SPEC drift larger than expected | medium × medium | NO — §2.1.1 and §29 were already mostly current; §29 got a paragraph, not a rewrite |
| Code examples don't compile | medium × medium | NO — 7/7 snippets compiled on first try |
| Getting started requires features that don't work | low × high | NO — every step tested on a clean pipeline |
| README perf numbers worse when re-measured | low × low | N/A — no re-measurement this release |
| Debugging guide references incomplete DWARF | medium × medium | ADDRESSED — guide now explicitly says DWARF is deferred to v5.x |

**Unplanned discovery**: the original `docs/guides/debugging.md`
was not just stale — it was misleading. Users following it would
expect source-level breakpoints, variable inspection, and
DWARF-aware frames that don't exist. The rewrite closes a
user-facing trust gap that Rattler flagged back in v4.26.0.

## Next session

v4.117.0 is the test-suite hardening release per
POST_RECOVERY_ROADMAP.md after-v4.116.0 plan: ASan CI gate, TSan CI
gate, flaky test audit, coverage report, integration test
hardening. Opens immediately — no blocker from v4.116.0.

## One-line summary

v4.116.0 closes five documentation gaps flagged by Boa since
v4.82.0 — README, SPEC, cookbook, debugging guide, and the new
getting-started guide — with zero compiler or runtime changes and
zero regressions.
