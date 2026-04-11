# Mapanare v4.31.0 — Documentation Truth + Process Hardening

> **Recovery release #5 — final.** v4.27–v4.30 closed the panel's
> CRITICAL and HIGH items. v4.31.0 closes the documentation drift, the
> MEDIUM/LOW carry-forwards, and adds the process discipline that
> prevents the v4.18.0–v4.26.0 regression from recurring. Still **zero new
> features.**

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.30.0
**Estimated work:** 1 day
**Theme:** Make the docs match the code. Make the process catch the next regression at PR time, not 8 versions later.

---

## The Problem

After v4.27.0–v4.30.0, the code is healthy. The remaining gap is
**documentation drift** and **process debt**:

### Class A: Documentation 26 versions stale

| Item | Last touched | Reporter |
|------|--------------|----------|
| `docs/SPEC.md` | v3.47.0 | Coral HIGH |
| `docs/README.es.md` | 5+ review cycles stale | Coral |
| `docs/SPEC.md` line 121 | `di` mislabeled, 5th cycle from v3.47.0 | Coral |
| Bilingual keywords table missing from SPEC | 3rd cycle | Coral |
| `mapanare/emit_c.py` docstring | 27 versions stale | Mamba M3 |
| User-Agent string `Mapanare/3.42` | 5+ minor versions stale | Mamba, Viper |

### Class B: Dead code from old workarounds

| Item | File:Line | Reporter |
|------|-----------|----------|
| `__mn_list_oob_buf` 4KB workaround | `mapanare_core.c:972` | Mamba M4 |

The bug it papered over (break-in-if-in-for) was fixed in v4.14.0 with
regression tests. The workaround and its comment survived two cleanup
passes.

### Class C: Process debt (the meta-fix)

The v4.18.0–v4.26.0 regression happened because no process step caught
hollow features. v4.29.0 added CI gates for the technical class
(`raise NotImplementedError`, `pytest.mark.skip` audit, fixed-point
propagation). v4.31.0 adds the editorial class:

- Pre-release CHANGELOG honesty check
- Pre-release "every claim has a test" check
- Pre-release docs-vs-code drift detector
- Recovery review cadence (when does the next 7-reviewer panel run?)

---

## Phase 1: Documentation truth

### Phase 1.1: SPEC sync (26 versions stale)

- [ ] `docs/SPEC.md` — read end-to-end. Note every claim that doesn't match
      the current code.
- [ ] Sections that need rewriting (estimated):
      - Tensor syntax: pick `Tensor<Float>[N, N]` (grammar form) and update
        every code block to match
      - `const` keyword section: matches v4.27.0 outcome (Path A or Path B)
      - `@gpu` section: matches v4.27.0 outcome
      - `async`/`await` section: matches v4.30.0 outcome
      - FFI section: reflects v4.27.0 working state, not v4.25.0 broken
        state
      - Section 23 (GPU): reflects current `gpu_tensor_*` builtins reality
- [ ] `docs/SPEC.md` line 121 — fix the `di` mislabel (Coral has been
      flagging this for 5 cycles)
- [ ] Add the bilingual keywords table to SPEC (3rd cycle ask from Coral)

### Phase 1.2: Spanish README sync

- [ ] `docs/README.es.md` — sync with `README.md` content. The badge was
      bumped in v4.26.0; the body has not been touched in 5+ cycles.
- [ ] Same for `docs/README.zh-CN.md` and `docs/README.pt.md` if they
      diverged similarly

### Phase 1.3: Stale docstring sweep

- [ ] `mapanare/emit_c.py` — docstring claims things 27 versions stale.
      Either update the docstring or delete `emit_c.py` if it's no longer
      reachable from any CLI path
- [ ] `git grep -l "v3\." mapanare/` — find every `v3.*` reference in
      docstrings; update to current state or strike

### Phase 1.4: User-Agent bump

- [ ] `runtime/native/mapanare_io.c` (or wherever) — User-Agent string
      `Mapanare/3.42` should match the current VERSION
- [ ] Wire it to a `MAPANARE_VERSION` macro that's set at build time from
      the `VERSION` file (so this doesn't drift again)
- [ ] Add a smoke test: spin up a local HTTP server, make a request, parse
      the User-Agent header, assert it equals the contents of `VERSION`

---

## Phase 2: Dead code removal

### Phase 2.1: `__mn_list_oob_buf` workaround

- [ ] `runtime/native/mapanare_core.c:972` — the 4KB out-of-bounds read
      workaround for break-in-if-in-for
- [ ] The bug was fixed in v4.14.0. The workaround is dead code.
- [ ] Delete the buffer, the comment, and any code that references it
- [ ] Run the v4.14.0 regression test (it should still pass)

### Phase 2.2: Other dead code

- [ ] Run `culebra triage stage2.ll --brief` and look for "dead code"
      findings
- [ ] Run `python3 -m vulture mapanare/` for Python dead code
- [ ] Anything that's dead AND undocumented as "kept for reference":
      delete
- [ ] Anything that's kept for reference: add an explicit comment saying
      so, with the version it became dead and a tracking issue link

---

## Phase 3: Process hardening

### Phase 3.1: CHANGELOG honesty check

- [ ] Add `scripts/check_changelog_honesty.py`:
      - Parse the most-recent CHANGELOG entry
      - For every claim mentioning a test file: assert the file exists
      - For every claim mentioning a syntax: try to parse it via the Lark
        grammar
      - For every claim mentioning a function/method/keyword: grep the
        source for it
      - Exit non-zero if any check fails
- [ ] Wire to CI as a required check on every PR that modifies CHANGELOG.md

### Phase 3.2: Docs-vs-code drift detector

- [ ] Add `scripts/check_docs_drift.py`:
      - For every code block in `docs/SPEC.md` and `docs/getting-started.md`,
        feed it through the parser
      - Any block that doesn't parse cleanly fails the check
      - Skip blocks marked with a `<!-- pseudo -->` comment
- [ ] Wire to CI

### Phase 3.3: Recovery review cadence

- [ ] Document in `.reviews/prompt.md` (or a new `REVIEW_CADENCE.md`):
      - Run a 7-reviewer panel at least every 5 minor versions
      - Run a 7-reviewer panel before any release tagged `>=` a previous
        major (e.g., before `v5.0.0`)
      - Run a "delta review" (1 reviewer, focused) on any version that
        adds new language syntax
- [ ] Add a calendar reminder or GitHub issue template for the next
      scheduled review

### Phase 3.4: Hollow-feature lint

- [ ] Add `scripts/check_no_hollow_features.py`:
      - For every function decorated with a language feature decorator
        (`@gpu`, `@cuda`, `@vulkan`, `@async`, etc.) in `tests/golden/`,
        verify the feature has a real lowering path
      - For every grammar rule that maps to a non-trivial AST node, verify
        the AST node has a corresponding lowering case in `lower.py` and
        `mapanare/self/lower.mn`
      - Anything that parses but has no lowering is a hollow feature
- [ ] Wire to CI as a required check
- [ ] Include the existing v4.29.0 `raise NotImplementedError` gate as a
      sub-check of this script

### Phase 3.5: Carry-forward queue file

- [ ] Add `.reviews/CARRY_FORWARD.md`:
      - One row per open carry-forward item
      - Columns: Item, First reported, Most recent review, Severity, Owner,
        Tracking version
      - Anything older than 3 review cycles is bolded
      - The file is updated by every recovery release's SESSION_REPORT
- [ ] Initialize the file with the current state from
      `.reviews/v4.26.0/README.md`'s carry-forward debt section

---

## Phase 4: Run the next review

After Phase 3 is done and v4.31.0 ships:

- [ ] Update `.reviews/prompt.md` to target `v4.31.0`
- [ ] Run the 7-reviewer panel on the v4.31.0 tag
- [ ] If aggregate score >= 9.0 and no NEEDS WORK verdicts, the recovery
      arc is complete
- [ ] If not, identify which items the panel still flags and add them to
      a v4.32.0 PLAN

The recovery arc is "complete" only when an external verification (the
panel) confirms it. v4.31.0 cannot self-certify completion.

---

## Exit Criteria

| # | Check | Required |
|---|-------|----------|
| 1 | `docs/SPEC.md` synced; every code block parses | YES |
| 2 | SPEC line 121 `di` label fixed | YES |
| 3 | Bilingual keywords table added to SPEC | YES |
| 4 | `docs/README.es.md` synced with current README.md | YES |
| 5 | `mapanare/emit_c.py` docstring updated or file deleted | YES |
| 6 | User-Agent wired to `VERSION`; smoke test passes | YES |
| 7 | `__mn_list_oob_buf` workaround deleted; v4.14.0 test still passes | YES |
| 8 | Other dead code identified and deleted or annotated | YES |
| 9 | `scripts/check_changelog_honesty.py` exists; passes; in CI | YES |
| 10 | `scripts/check_docs_drift.py` exists; passes; in CI | YES |
| 11 | `scripts/check_no_hollow_features.py` exists; passes; in CI | YES |
| 12 | `.reviews/CARRY_FORWARD.md` initialized | YES |
| 13 | `.reviews/REVIEW_CADENCE.md` written | YES |
| 14 | 46/46+ golden, 11/11 stage2 | YES |
| 15 | black/ruff/mypy clean | YES |
| 16 | `.reviews/prompt.md` retargeted to v4.31.0 | YES |
| 17 | `docs/roadmap/v4/v4.31.0/SESSION_REPORT.md` written | YES |
| 18 | Next 7-reviewer panel run on v4.31.0; results filed | YES |

---

## Verification commands

```bash
# Phase 1 docs
python3 scripts/check_docs_drift.py
git grep "v3\." docs/SPEC.md  # only historical refs allowed
diff <(grep -A 2 "Version" README.md) <(grep -A 2 "Version" docs/README.es.md)

# Phase 2 dead code
git grep "__mn_list_oob_buf" runtime/  # 0 hits
python3 -m vulture mapanare/ --min-confidence 80

# Phase 3 process scripts
python3 scripts/check_changelog_honesty.py
python3 scripts/check_docs_drift.py
python3 scripts/check_no_hollow_features.py

# Phase 4 review
ls .reviews/v4.31.0/  # must contain README.md and 7 reviewer files

# Full validation
.\dev.ps1
```

---

## What v4.31.0 explicitly does NOT do

- New language features (none — recovery arc terminates here)
- DWARF debug info (deferred to v4.32.0+ if there's appetite)
- `await` Path A coroutines (deferred to v5.0.0)
- `extern "Python" fn` restoration (decided in v4.29.0)
- Distributed agent routing, JIT HMR, LSP improvements (v5.x growth features)

---

## Definition of done

- All 18 exit criteria check YES
- 7-reviewer panel re-runs on v4.31.0 with aggregate >= 9.0 and zero
  NEEDS WORK verdicts
- The recovery arc (v4.27.0 → v4.31.0) is complete

If the panel does not give >= 9.0, the recovery arc continues into
v4.32.0 with whatever the panel surfaces. **The recovery arc terminates
when the panel says it terminates, not when the lead says it does.**
