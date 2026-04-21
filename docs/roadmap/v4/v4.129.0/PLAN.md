# Mapanare v4.129.0 — Documentation + SPEC Sync

> **Buffer release 4 of the v4.131.0 closeout arc.** Audit SPEC.md
> against reality. Fix stale sections. Verify examples. No new
> content — just make existing documentation honest.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.128.0
**Delta review:** No
**Full panel:** No (this release prepares evidence for v4.130.0+)
**Estimated work:** 1 sprint
**Theme:** Make documentation honest. Audit, fix, verify. No new code
paths, no new features.

> **Scope note (2026-04-15):** This PLAN.md was originally titled
> "Pre-Panel Prep + Third Flaky Audit." The PROMPT.md was edited to
> "Documentation + SPEC Sync" per the v4.128.0 SESSION_REPORT's
> next-release recommendation; PLAN.md was left stale. Rewritten in
> this session to match PROMPT.md. The pre-panel prep + flaky audit
> work moves to v4.130.0.

---

## Why v4.129.0 exists

Since the last documentation sync (v4.116.0), 12 releases (v4.117.0
through v4.128.0) have changed observable behavior:

| Release | Change | Docs surface affected |
|---|---|---|
| v4.121.0 | DWARF deferral warning; bounded-generic trait fix | SPEC §21.3, CLI flags |
| v4.122.0 | Qs.1 — `List<Int>` indexing fixed in emitter | SPEC lists section, cookbook |
| v4.123.0 | Dead-code sweep — `optimizer.py` (1,203 lines) and TBAA metadata deleted; `--legacy-optimizer` flag removed | SPEC optimizer section, CLI docs, cookbook |
| v4.124.0 | Enum payload unboxing (up to 2 inline slots for pointer-fits variants) | SPEC enums section, ABI docs |
| v4.125.0 | Benchmark refresh, V5 readiness snapshot | README benchmark numbers |
| v4.126.0 | Parser fix — `const` and `trait` now recognized at module level; native golden 27 → 39 | SPEC const section, feature status |
| v4.127.0 | Self-hosted whitespace normalization, TBAA removed from self-hosted emitter | SPEC IR notes |
| v4.128.0 | Sh.8 closed (bare `None` recognition), brace-spacing normalized, ModuleID path-stripped | SPEC async/option sections |

The v4.131.0 panel has two documentation-grading reviewers (Boa: DX,
8.7 @ v4.120.0; Coral: language design, 8.1 @ v4.120.0). Both flagged
carry-forward items pointing to SPEC currency and example
verification. This release closes those gaps before the v4.130.0
panel opens.

---

## Phase 1 — SPEC.md audit (targeted + light)

### 1a — Targeted audit (top 10 impacted sections)

For each of the 10 areas most affected by v4.120.0–v4.128.0 changes,
run `gitnexus query` to locate the implementing code, compare SPEC
text against implementation, classify as **OK / STALE / WRONG**:

1. Enum representation + pattern matching (v4.124.0 inline unboxing)
2. List indexing (v4.122.0 Qs.1 fix)
3. Optimizer architecture (v4.123.0 deleted `--legacy-optimizer`,
   removed `optimizer.py`)
4. String concat / StringBuilder (v4.108.0+v4.122.0)
5. Async surface — `async fn`, `await`, `block_on`, scheduler
   (v4.113.0–v4.115.0)
6. Coroutine frame / drop glue (v4.113.0)
7. Closures — environment capture, typed closures (v4.103.0)
8. `const` keyword (v4.126.0 parser fix — was silently dropped
   before)
9. DWARF / debug info (v4.121.0 deferral warning; SPEC §21.3)
10. Keyword table (SPEC §2.1.1; reflects bilingual + v4.68.0 hard
    reservations)

### 1b — Light scan (remaining sections)

Remaining SPEC sections: title + first paragraph check for obvious
staleness. Flag if:
- Mentions a version number older than v4.100.0
- References a CLI command or flag that no longer exists
- Describes a feature marked as "v4.x" that has actually shipped
- References `mapanare compile` (removed — use `build`)

### 1c — Output: `SPEC_AUDIT.md`

Per-section table with classification. Commit checkpoint:
`v4.129.0 phase 1: SPEC audit — N sections OK, M stale, P wrong`.

---

## Phase 2 — Fix SPEC divergences

- **WRONG sections** get rewritten to match current implementation
  (with code-pointer footnotes where useful).
- **STALE sections** get an explicit "**Status:** planned" or
  "**Status:** partial" line preserving design intent. The SPEC is a
  design document as well as a reference — deletion loses intent.
- **OK sections** get no changes.

Commit checkpoint: `v4.129.0 phase 2: fix SPEC divergences (WRONG +
STALE sections)`.

---

## Phase 3 — Verify all examples compile and run

Inventory `examples/` tree (root + subdirs `ai/`, `bind/`, `cli/`,
`experimental/`, `gpu/`, `network/`, `packages/`, `tensor/`,
`transpile/`, `wasm/`). For each `.mn` file:

1. `python -m mapanare check <file>` — parse + semantic
2. For non-library examples: `python -m mapanare run <file>` (native)
   or `check` only if runtime depends on network/GPU/stdin

Record per-example status in `EXAMPLES_REPORT.md`. For any failure
caused by a known compiler bug (not a documentation issue): add a
comment header at the top of the example citing the docket ID
(e.g., `// Known issue: Sh.2 (__mn_str_starts_with NULL deref in
emit_mir_call)`). **Do not work around bugs in example code.**

Commit checkpoint: `v4.129.0 phase 3: verify examples — N/M compile
and run`.

---

## Phase 4 — Sync cookbook + guides

Check `docs/guides/` (async.md, debugging.md, getting_started.md) and
`docs/cookbook/` for references to:

- `--legacy-optimizer` flag (removed v4.123.0)
- TBAA metadata emission (removed v4.123.0)
- `mapanare compile` (removed in v3.x; use `build`)
- Qs.1 `List<Int>` indexing workaround (fixed v4.122.0; remove
  workaround notes)
- Stale benchmark numbers (refresh from v4.125.0's FINAL_REPORT)
- `optimizer.py` module references (deleted v4.123.0)
- Version strings older than v4.100.0

Commit checkpoint: `v4.129.0 phase 4: sync cookbook + guides`.

---

## Phase 5 — Fix `scripts/concat_self.sh` (mir_opt.mn missing)

v4.128.0 SESSION_REPORT flagged: `scripts/concat_self.sh` lists 10
modules but omits `mir_opt.mn`; `scripts/concat_self.py` correctly
includes it. One-line fix — add `mir_opt.mn` after
`emit_llvm_ir.mn` in the bash `MODULES` array (matches the Python
version's ordering). The bash version would produce a broken
`mnc_all.mn` if anyone used it. Tagged for v4.129.0+ in the v4.128.0
closeout.

Commit checkpoint: folded into phase 4 commit (one-line fix).

---

## Phase 6 — Closeout

- [ ] `make test` (core compiler subset) — all green
- [ ] `make lint` — clean on touched Python files (no Python
      behavior changes in this release, so no new lint debt)
- [ ] `VERSION` bumped to `4.130.0` in final commit
- [ ] `CHANGELOG.md [4.129.0]` entry
- [ ] `SESSION_REPORT.md` written
- [ ] Roadmap status updated: this PLAN's Status → DONE;
      `docs/roadmap/v4/README.md` row added; `docs/roadmap/ROADMAP.md`
      row added; CLAUDE.md current-version paragraph updated.

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | SPEC audit complete with per-section classification | `SPEC_AUDIT.md` |
| 2 | All WRONG sections fixed; critical STALE sections tagged "planned" or "partial" | SPEC.md diff |
| 3 | All `examples/` inventoried with compile+run status | `EXAMPLES_REPORT.md` |
| 4 | Cookbook + guides scrubbed for v4.117.0–v4.128.0 stale references | docs/guides diff |
| 5 | `scripts/concat_self.sh` fixed (mir_opt.mn added) | scripts diff |
| 6 | `make test` green, `make lint` clean on touched files | CI logs |
| 7 | Standard closeout (CHANGELOG + SESSION_REPORT + VERSION bump + roadmap status) | commits |

---

## What this release does NOT do

- **Change compiler or runtime code.** One-line fix to a build script
  is the only code change (Phase 5).
- **Fix compiler bugs surfaced by example verification.** Bugs get
  docket entries and comment headers on the affected examples — the
  fixes themselves belong in code releases.
- **Refresh benchmarks.** v4.125.0's FINAL_REPORT is current enough;
  a benchmark refresh belongs in the v4.130.0 prep slot.
- **Run the flaky audit, valgrind sweep, or ASan sweep.** All three
  move to v4.130.0 (was this PLAN's original scope before PROMPT.md
  was edited).
- **Run the panel.** The panel is v4.131.0 under the new schedule.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| SPEC audit finds a WRONG section whose "fix" requires a code change | medium | medium | Open a docket, add a "**Status:** known issue (v4.x fix)" note, keep SPEC honest. Do not let docs-sync scope-creep into code work. |
| Example verification reveals new runtime bugs | medium | medium | Add comment header with docket ID, defer fix. Do not work around bugs. |
| Cookbook references features that were planned but never shipped | low | low | Mark "planned" with docket ID; preserve design intent. |
| Scripts/concat_self.sh fix breaks stage1 build | very low | high | Verify via `bash scripts/concat_self.sh && diff mnc_all.mn <(python3 scripts/concat_self.py && cat mnc_all.mn)` before committing. |
| Scope creep into v4.130.0's flaky/valgrind/ASan work | medium | medium | Hard stop at Phase 6 closeout. Those exits are v4.130.0's job. |

---

## After v4.129.0

**v4.130.0** — pre-panel prep + third flaky audit + valgrind/ASan
sweeps + MEASUREMENTS.md finalization. Was this PLAN's original
scope; the work itself didn't go away, just got re-slotted one
release later.

**v4.131.0** — THE PANEL (v5 gate attempt 3). Seven reviewers grade
v4.121.0–v4.130.0. Documentation from v4.129.0 is Boa's + Coral's
primary evidence.
