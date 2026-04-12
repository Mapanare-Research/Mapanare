# Mapanare v4.36.0 — Arc 1 Panel Release

> **First 5-minor cadence panel since v4.31.0.** Deliberately quiet
> scope: the panel needs a stable target. No new features; no new
> syntax; no new runtime primitives. v4.36.0 is the consolidation
> release where the work from v4.32.0–v4.35.0 gets polished and the
> external panel runs against the tagged artifact.

**Status:** DONE (2026-04-12)
**Breaking:** No
**Prerequisite:** v4.35.0 (match guards + or-patterns, fixed-point still 0)
**Delta review:** No (zero new syntax)
**Full panel:** **YES** — first 5-minor cadence panel per `REVIEW_CADENCE.md`
**Estimated work:** 1 sprint for the release + external panel run
**Theme:** Quiet close of Arc 1 (error handling + pattern matching). Panel runs against a stable target.

---

## Why panel releases are quiet

The v4.18.0–v4.26.0 regression happened in part because versions piled new features on top of unverified previous versions. The 5-minor cadence panel is the correction: every 5th release, the lead ships only stabilization work so the external panel has something stable to grade. Panel releases are not the place to ship new features — they are the place to prove that the previous four releases work.

At v4.36.0 the panel is fact-checking:
- `?` operator (v4.33.0) end-to-end
- Match decision-tree rewrite + exhaustiveness (v4.34.0) with A6 closed
- Match guards + or-patterns (v4.35.0) with byte-identity preserved
- Arc-end closure items from v4.32.0 actually holding
- The 9 LOW items swept across v4.32.0–v4.35.0 staying closed

---

## Phase 1 — LOW item sweep (the residual tail)

v4.31.0's panel surfaced 25 action items. v4.32.0 closed 9 (HIGH + MEDIUM). v4.33.0–v4.35.0 each closed 3 LOW items (9 more). That leaves ~7 items from the original docket that need homes.

### Phase 1.1: `cuda_matmul` upload rc check (v3.47.0 #3, LOW)

- [ ] `runtime/native/mapanare_gpu.c:1693-1694` — the matmul fix landed in v4.28.0 for `__mn_gpu_tensor_matmul` (the CPU-validated path) but the GPU upload path at `cuda_matmul` never got its return-value check.
- [ ] Fix: check the `cuMemcpyHtoD` / `cuMemcpyDtoH` return values; abort or return empty on non-success; document the error.
- [ ] Test: `tests/runtime/test_cuda_upload_error.py` — skip if no CUDA device; otherwise force an invalid device pointer and verify the program exits cleanly instead of silently corrupting.

### Phase 1.2: Self-hosted bounded-for sentinels (Cobra Issue #15, 10th cycle)

- [ ] Grep: `grep -n "0\.\.1000000\|0\.\.5000" mapanare/self/*.mn`. Expected sites: `semantic.mn:255`, `semantic.mn:273`, `emit_llvm.mn:3260`, `mir_opt.mn:413`, `mir_opt.mn:438`.
- [ ] These are pseudo-`while` loops because the self-hosted grammar lacks `loop { ... break }`. Each uses a large-bound `for _ in 0..N` with an internal `break`.
- [ ] **Fix option A (cheap):** accept them, add a comment at each site naming the maximum legitimate iteration count. Document in `CARRY_FORWARD.md` that they're not a bug — they're a grammar gap that a `loop` construct would close in a later release.
- [ ] **Fix option B (real):** add `loop { ... }` to the self-hosted grammar. That's a new syntactic form; it would need a delta review; it's arguably out of scope for a panel release.
- [ ] **Decision: Option A for v4.36.0.** Add the comments, document the grammar-gap item as a tracked carry-forward (`A10`: "self-hosted `loop` construct missing — `for _ in 0..N` sentinels are the workaround"). Option B can land in v4.37.0+ if appetite.
- [ ] `.reviews/CARRY_FORWARD.md` — row for A10, tracked to v4.37.0+ if user wants a real `loop`, otherwise OPEN indefinitely.

### Phase 1.3: Remaining LOW items audit

- [ ] Read `.reviews/v4.31.0/README.md` §Prioritized Action Items LOW section (items 10–25).
- [ ] For each LOW item, check status:
  - Closed opportunistically in v4.32.0–v4.35.0? Mark closed with evidence in `CARRY_FORWARD.md`.
  - Still open? Either close it in v4.36.0 Phase 1.4 (if small), or re-track it with a future tracking version.
- [ ] Items expected still open going into v4.36.0:
  - SPEC §3.10 tensor "not yet implemented" status line → tracked to **v4.44.0** (tensor broadcasting release has the natural place to update this)
  - `examples/` agents/signals/streams demos → tracked to **v4.50.0** (the AI/LLM demos arc)

### Phase 1.4: Tiny opportunistic cleanups

- [ ] Anything with a 5+ cycle history in the ledger that can be closed in under 15 minutes gets closed now. Specific candidates (audit at release time — this list is illustrative):
  - Any remaining TODO/FIXME comments older than v4.20.0 that have stopped being relevant
  - Dead imports flagged by `ruff check`
  - `black --check` drift that accumulated during the feature releases
  - `mypy` warnings that have piled up

---

## Phase 2 — Carry-forward ledger drain

The `CARRY_FORWARD.md` file is the canonical queue. Every release appends to it. v4.36.0 is the first consolidation point — review and clean up.

- [ ] Read `.reviews/CARRY_FORWARD.md` top to bottom.
- [ ] For every row closed in v4.32.0–v4.35.0, verify the evidence pointer actually resolves (file exists, symbol is greppable, test name exists).
- [ ] For every row still OPEN, verify the tracking version is still valid. Re-point if needed.
- [ ] For every row with cycles ≥ 5 that has NOT been closed, either (a) close it, (b) justify why it's open with a fresh note, or (c) escalate to HIGH and fix in v4.36.0.
- [ ] The Python-vs-self-hosted asymmetry columns from v4.32.0 Phase 1.3 get re-verified. Any drift since v4.32.0 is flagged.
- [ ] Write `docs/roadmap/v4/v4.36.0/LEDGER_AUDIT.md` — a one-page summary of the ledger state at arc 1 close. This becomes part of the panel's reading list.

---

## Phase 3 — Documentation polish

Arc 1 shipped four new features (`?` operator, match decision-tree, guards, or-patterns). The cookbook + SPEC + reference must document each cleanly, with parseable code blocks, before the panel runs.

- [ ] `docs/cookbook.md` — re-read the chapters v4.33.0/v4.34.0/v4.35.0 added:
  - §Error Handling — the `?` operator walkthrough
  - §Pattern Matching — the decision-tree-era patterns
  - §Pattern Matching — guards subsection
  - §Pattern Matching — or-patterns subsection
- [ ] Verify every code block parses via `scripts/check_docs_drift.py` — already CI-enforced, but run locally before the panel.
- [ ] Cross-references: the `?` operator doc should link to the pattern matching doc (since `?` desugars to match); the guards doc should link to or-patterns (they're commonly combined).
- [ ] `docs/SPEC.md` §Error Handling and §Pattern Matching — same audit.
- [ ] `docs/reference.md` — operator precedence table includes `?`; pattern syntax section includes guards + or-patterns.
- [ ] `docs/getting-started.md` — if the tutorial uses match or error handling, update to show the new idioms.
- [ ] Spanish README already got badge bumps in v4.31.0. Check if any arc-1 feature is worth mentioning in the intro paragraph. If yes, update; otherwise leave for the v4.50.0 documentation pass.

---

## Phase 4 — Measurement refresh

The panel will want fresh metrics. Generate them.

- [ ] `culebra summary mapanare/self/main.ll` — record function count, instruction count, type count. Expected: ~761 functions (same as v4.31.0, maybe +5 from new match helpers), ~168,300 instructions (likely smaller from the decision-tree rewrite).
- [ ] `culebra baseline save mapanare/self/main.ll -o .culebra/v4.36.0-baseline.json` — save the arc-end baseline for future `baseline diff` runs.
- [ ] `bash scripts/verify_fixed_point.sh` — record the diff line count. Target: **0** (A6 closed in v4.34.0, preserved through v4.35.0).
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — record pass count. Target: **48/48** (44 at v4.31.0, +1 in v4.33.0 = 45, +1 in v4.34.0 = 46, +3 in v4.35.0 = 49 — actual count depends on renames). Verify against the actual directory listing.
- [ ] `python -m pytest tests/ -q` — record pytest count. Target: +~40 new tests from arcs 1 (parser/semantic/llvm for `?`, match exhaustiveness, match guards, or-patterns).
- [ ] `python scripts/ir_doctor.py stage2 --timeout 60` — record the 11/11 status.
- [ ] Lint: black, ruff, mypy all clean.
- [ ] Write the numbers into `docs/roadmap/v4/v4.36.0/MEASUREMENTS.md` — a one-page metric snapshot the panel reads first.

---

## Phase 5 — Pre-panel audit

The lead fact-checks every SESSION_REPORT claim from v4.32.0–v4.35.0 against the shipping code at the v4.36.0 tag. This is the recovery-arc discipline: catch drift before it reaches the panel.

- [ ] Read `docs/roadmap/v4/v4.32.0/SESSION_REPORT.md` end-to-end. For every backticked file path, `ls` it. For every test name, `pytest --collect-only -q` it. For every `grep` pattern the session report cites, run the grep.
- [ ] Same for v4.33.0, v4.34.0, v4.35.0.
- [ ] Any claim that doesn't hold up is either:
  - A typo (fix the session report)
  - A regression introduced by a later release (fix the regression; if the regression needs investigation, slip v4.36.0 and open v4.36.1 for the fix)
  - An honest deviation that was worth taking (add a note in the session report explaining; do NOT silently adjust the claim)
- [ ] Audit output lives at `docs/roadmap/v4/v4.36.0/PRE_PANEL_AUDIT.md`. The panel reviewers will see it, which is the point: if the lead's own audit caught something, the panel knows to trust the rest.

---

## Phase 6 — Panel run

The panel runs against the v4.36.0 tag per `REVIEW_CADENCE.md` rule #1 (5-minor cadence). Retarget the prompt, create the review directory, spawn the reviewers, write the summary.

### Phase 6.1: Prep

- [ ] `cp .reviews/prompt.md .reviews/v4.36.0-prompt-backup.md` (keep an audit trail)
- [ ] Edit `.reviews/prompt.md`: retarget the version string from `v4.31.0` to `v4.36.0` everywhere. Update the "arc being reviewed" context to say "v4.32.0 → v4.36.0 (arc 1: error handling + pattern matching)." Keep the recovery-arc prompt framing mostly intact — it still applies. Reviewers fact-check the arc's claims.
- [ ] `mkdir -p .reviews/v4.36.0/`
- [ ] Pre-populate with:
  - `culebra_summary.md` — copy from the Phase 4 measurement
  - `arc_journal.jsonl` — concatenate any per-release culebra journals from v4.32.0–v4.35.0 if they exist
  - `MEASUREMENTS.md` — the Phase 4 metric snapshot
  - `LEDGER_AUDIT.md` — the Phase 2 ledger state
  - `PRE_PANEL_AUDIT.md` — the Phase 5 fact-check
- [ ] These prepopulated files are the panel's reading list. A reviewer who opens `.reviews/v4.36.0/` sees the state before they open any source file.

### Phase 6.2: Spawn reviewers

- [ ] Spawn 7 reviewers in parallel per the v4.31.0 panel procedure:
  - 01-viper.md (Rust / memory safety)
  - 02-boa.md (Python / DX)
  - 03-cobra.md (C++ / ABI)
  - 04-mamba.md (C / runtime)
  - 05-anaconda.md (GNU/GCC toolchain)
  - 06-rattler.md (LLVM / codegen)
  - 07-coral.md (language design)
- [ ] Each reviewer reads their v4.31.0 file (`.reviews/v4.31.0/NN-codename.md`) first — for continuity and to see the arc 1 they're now grading the close of.
- [ ] Each reviewer fact-checks the claims in the arc's SESSION_REPORTs + their own previous-release findings.
- [ ] The prompt specifically asks reviewers to evaluate:
  - Did the `?` operator ship as claimed? Does it actually desugar cleanly? Any regression cases?
  - Did the decision-tree match rewrite actually close A6 to 0 lines of fixed-point diff?
  - Do guards and or-patterns work as specified? Is the byte-identity invariant still preserved?
  - Are the 9 LOW items from v4.31.0 that were swept in v4.32.0-v4.35.0 actually closed at code level?

### Phase 6.3: Write the README

- [ ] After all 7 reviews land, write `.reviews/v4.36.0/README.md`:
  - Verdict table (7 rows)
  - Overall consensus + aggregate score
  - Post-production health gate (is the language still healthy 36 minors after v4.0.0?)
  - Prioritized action items from the panel
  - Disagreements
  - Improvements + regressions since v4.31.0
  - Score trajectory appendix

### Phase 6.4: Address findings

- [ ] If the panel returns **PASS / PASS WITH NOTES with aggregate ≥ 9.0**: arc 1 officially closes. v4.37.0 opens with arc 2 (LSP).
- [ ] If the panel returns **NEEDS WORK**: the recovery protocol re-engages. v4.37.0 becomes a v4.36.0-docket-closure release (recovery style). Arc 2 slides to v4.38.0 onward. No shame; this is the cadence working.
- [ ] File the panel findings as rows in `CARRY_FORWARD.md`.

---

## Phase 7 — Closeout

- [ ] `VERSION` — `4.35.0` → `4.36.0`
- [ ] `CHANGELOG.md` `[4.36.0]` entry — short, honest: "arc 1 close + panel run. No new features. Panel verdict linked."
- [ ] `docs/roadmap/v4/v4.36.0/SESSION_REPORT.md` — written, including the panel verdict summary and links.
- [ ] `docs/roadmap/ROADMAP.md` — v4.36.0 row added.
- [ ] `docs/roadmap/v4/README.md` — v4.36.0 row added, arc 1 marked as complete (assuming panel PASS).
- [ ] `.reviews/CARRY_FORWARD.md` — updated from Phases 1-2-6.
- [ ] Standard full-validation suite: black, ruff, mypy, pytest, golden, stage2, fixed-point, all 4 CI gates.

---

## Exit criteria (14 items)

| # | Check | Evidence |
|---|---|---|
| 1 | LOW items from v4.31.0 docket: 7 remaining items audited, closed or re-tracked | `LEDGER_AUDIT.md` written |
| 2 | `cuda_matmul` upload rc check + test (Phase 1.1) | `tests/runtime/test_cuda_upload_error.py` passes (or skips honestly) |
| 3 | Self-hosted bounded-for sentinels documented / tracked as A10 | `.reviews/CARRY_FORWARD.md` row A10 exists |
| 4 | Documentation polish: cookbook + SPEC + reference for arc 1 features | `scripts/check_docs_drift.py` clean |
| 5 | `MEASUREMENTS.md` written with fresh metrics | file exists in `.reviews/v4.36.0/` |
| 6 | `LEDGER_AUDIT.md` written | file exists in `docs/roadmap/v4/v4.36.0/` |
| 7 | `PRE_PANEL_AUDIT.md` written: every SESSION_REPORT claim from v4.32.0–v4.35.0 fact-checked | file exists; any failed checks remediated |
| 8 | `.reviews/prompt.md` retargeted to v4.36.0 | diff shows version-string updates |
| 9 | `.reviews/v4.36.0/` pre-populated with measurements, ledger, audit, culebra files | `ls .reviews/v4.36.0/` shows all 5 files |
| 10 | 7 reviewers spawn + return individual reviews | 01-viper.md through 07-coral.md exist |
| 11 | `.reviews/v4.36.0/README.md` written with verdict table + consensus | file exists |
| 12 | Panel verdict is PASS / PASS WITH NOTES with aggregate ≥ 9.0 (target) | README.md verdict |
| 13 | If panel returns NEEDS WORK, v4.37.0 is re-scoped as recovery release | separate PLAN.md at v4.37.0 reflecting the docket |
| 14 | `SESSION_REPORT.md` written | file exists |

---

## What v4.36.0 explicitly does NOT do

- **No new language features.** Panel releases never ship new features.
- **No grammar changes.** If a grammar tweak is needed for polish (e.g., a disambiguation), slip to v4.37.0.
- **No new LLVM emitter behavior.**
- **No new stdlib modules.**
- **No speculative work** on arc 2 (LSP) — that's v4.37.0+.

If a LOW item turns out bigger than a 15-minute fix during Phase 1.4, defer it to v4.37.0. Panel release discipline trumps opportunistic cleanup.

---

## Reference

- [`docs/roadmap/v4/POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 1 — the arc narrative
- [`.reviews/REVIEW_CADENCE.md`](../../../../.reviews/REVIEW_CADENCE.md) §Full-panel triggers — rule #1, 5-minor cadence
- [`.reviews/v4.31.0/README.md`](../../../../.reviews/v4.31.0/README.md) — the arc-starting panel
- [`.reviews/prompt.md`](../../../../.reviews/prompt.md) — the panel prompt to retarget

---

## After v4.36.0

v4.37.0 opens **arc 2 (LSP maturity)**. First release: workspace index + go-to-definition + hover types. No new language syntax; pure editor-tooling work on top of the existing parser + semantic checker. See [`v4.37.0/PLAN.md`](../v4.37.0/PLAN.md).

If the v4.36.0 panel returned NEEDS WORK, v4.37.0 instead becomes a recovery-style closure release and arc 2 slides to v4.38.0+.
