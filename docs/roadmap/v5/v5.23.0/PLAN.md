# v5.23.0 — RC.* — CI recovery + HIGH closures

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.22.0 shipped (Option A panel result;
4 HIGH + 8 MEDIUM + ~12 LOW open in
`.reviews/CARRY_FORWARD.md`).
**Estimated effort:** 1 long session (~3–5 hours).
**Arc context:** First release in the v5.23–v5.24 recovery
arc. See `docs/roadmap/v5/RECOVERY_ARC_v5.23-v5.24.md`.

---

## Why this exists

The v5.22.0 panel applied Option A, but post-panel CI
analysis surfaced **8 silently-failing CI workflows** at
HEAD — 4 the panel flagged, 4 the panel did not see. The
panel's 4 HIGH items must close in the same release as the
4 NEW CI failures because they share root cause class
(structural gate inertia + audit/closure mismatch).

This release is the **"make CI green again"** scope: every
fix is small (≤ 2 hours), every fix is mechanical, and the
release ships only when all 8 listed CI workflows are green.
**Zero compiler edits.** Zero MIR / IR / runtime / `mapanare/
self/*.mn` edits.

---

## Goals

1. Restore `check_struct_registry.py` (Reg.1, HIGH) +
   investigate the 5-release blind window for actual drift.
2. Close `Bo.18r` (HIGH, 3rd consecutive panel) at the actual
   `README.md:188-192` paragraph.
3. Close `Bo.25` (HIGH, NEW) — goldens badge `66/66` → `95/95`
   structurally via `bump_version.py` extension.
4. Close 4 silently-failing CI workflows the panel did not
   surface: CHANGELOG honesty, Docker Smoke, macOS/iOS
   cross-compile, Self-Hosted Compiler stage2 ir_doctor.
5. Close 5 LOW items mechanically (Sh.\* baseline labeling,
   v5.19.0 SR backfill, etc.) so v5.23.1+ can focus on bigger
   work.
6. **Strict 3-stage fixed point preserved at 238,086 lines /
   0 diff** by construction (zero compiler edits).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **RC.1** | HIGH | **Reg.1** — extend `scripts/check_struct_registry.py` `STRUCT_HEADER_RE` regex to accept `struct Name:` colon-form (`r"^(?:pub\s+)?struct\s+([A-Z][A-Za-z0-9_]*)\s*[\{:]"`) + extend `parse_struct_defs` to handle indent-based bodies (read until dedent for colon-form, until `}` for brace-form, mirror of `mapanare/parser.py::_indent_to_braces` indent-tracking). After regex + parser updates, re-run the gate: **investigate every reported drift**. Per v4.143.0 retrospective ("3 real latent drifts on first run"), expect a non-zero count after restore. Close each one (either by updating the registry to match source, or — if source is wrong — opening a separate hotfix). Add `tests/test_ci.py::test_struct_registry_gate_passes` to verify the gate is green post-fix. | 2h |
| **RC.2** | HIGH | **Bo.18r** (3rd consecutive panel) — rewrite `README.md:188-192` benchmarks-section lead-in paragraph. Replace v5.7.1-vintage NEAR / 217k / 5,720+ language with rounded "238k / 13-release strict streak / 5,800+" framing per Boa's suggested diff. Use rounded `238k` lines instead of brittle `238,086` (the v5.9.2 Dn.1 self-immunization pattern). Same edit closes Bo.19 (test count drift) and Bo.20 (FINAL_REPORT_v4.153 link). | 5 min |
| **RC.3** | HIGH | **Bo.25** (NEW) — bump goldens badge `66/66` → `95/95` across `README.md`, `docs/README.es.md`, `docs/README.pt.md`, `docs/README.zh-CN.md`. **Structural fix**: extend `scripts/bump_version.py` to auto-discover `tests/golden/*.mn` count and update the goldens badge in lockstep with the version badge across all 4 READMEs. Same pattern as the v5.11.2 multi-locale label-key fix. | 10 min one-shot, 30 min structural |
| **RC.4** | MEDIUM | **Hollow-feature gate** — add `CompClause` (v5.15.0 Te.2) and `FieldPattern` (v5.20.0 Te.5.D) to `_AST_INFRASTRUCTURE` in `scripts/check_no_hollow_features.py`. Both are sub-nodes held inside parent nodes (Comprehension.clauses, StructPattern.fields), not top-level isinstance dispatch targets. | 5 min |
| **RC.5** | MEDIUM | **`check_docs_drift.py`** — close `docs/SPEC.md:1456` violation. The block `fn id(y) = y` doesn't parse (untyped param). Either (a) annotate `y: Int` to make it parse, or (b) add `<!-- pseudo -->` opt-out marker on the line above the fence. Choose (a) if the example is meant to be runnable; (b) if it's illustrative-only. | 1 min |
| **RC.6** | MEDIUM | **`check_changelog_honesty.py`** — fix v5.21.1 entry's `.reviews/v5.22.0/PRE_PANEL_AUDIT.md` reference. The `.reviews/` directory is gitignored at the directory level; CI's git tree doesn't have the audit file. Three options: (A) `git add -f .reviews/v5.22.0/{PRE_PANEL_AUDIT.md,prompt.md,README.md,V5_DECISION.md,01-rattler.md,...,07-mamba.md}` matching the v5.11.0 / v5.7.1 precedent of tracked panel artifacts (recommended); (B) add `<!-- no-check -->` markers throughout the v5.21.1 + v5.22.0 CHANGELOG entries; (C) add `.reviews/` to `_SEARCH_ROOTS` in the script. **Recommendation: Option A** — track all panel artifacts permanently. | 5 min |
| **RC.7** | MEDIUM | **Docker Smoke** — `runtime/native/libmapanare_rt.a` missing in `publish-docker.yml` `docker-smoke` job because the workflow doesn't build the runtime before copying. Add a "Build runtime" step (`make -C runtime/native libmapanare_rt.a` or equivalent) before line 85's `cp` step. Verify by re-running the workflow and watching the cp succeed. | 15 min |
| **RC.8** | MEDIUM | **macOS / iOS cross-compile** — failing on `__mn_str_eq` / `__mn_str_println` undefined for arm64. Root cause: Python bootstrap on macOS shells out to clang via `mapanare/cli.py` but does NOT pass `-l mapanare_rt -L runtime/native` (or the equivalent). Investigate `mapanare/cli.py::run` / `mapanare/cli.py::build` / `link_with_runtime` for the Darwin-arm64 case. Confirm with a local macOS VM or via `act` if available. Fix: add `libmapanare_rt.a` linkage to the Darwin path of the CLI's clang shell-out. | 1-2h |
| **RC.9** | MEDIUM | **Self-Hosted Compiler stage2 ir_doctor** — `lower.mn` per-module compile fails on `Undefined function 'new_match_arm'`. Root cause: `new_match_arm` is defined in `mapanare/self/parser.mn` (line 206) and imported / cross-module-referenced from `lower.mn`. `scripts/ir_doctor.py stage2 --timeout 30` compiles each module independently, missing the cross-module symbol. Two fix options: (A) make `ir_doctor.py stage2` build `mnc_all.mn` first (the concatenated source) and run modules through it; (B) pass `--link-all` flag that pre-resolves cross-module symbols. Recommendation: A. | 1h |
| **RC.10** | LOW | **`__mn_indent_to_braces`** missing from `runtime/native/mapanare_core.h`. Add `MN_EXPORT MnString __mn_indent_to_braces(MnString source);` near the existing v5.14.1 region (after `__mn_assert_fail` decl). One line, zero behavior change. | 1 min |
| **RC.11** | LOW | **v5.19.0 SESSION_REPORT** — `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` does not exist on disk despite Te.3 having shipped (3 commits in log: db32bd4 + fba8521 + 6adfee7). Backfill retroactively from PLAN.md + PROMPT.md + DOCKER_DESIGN.md + the 3 commits. Brief is fine. | 1h |
| **RC.12** | LOW | **Sh.\* baseline labeling normalization** — "−13.9% off v5.13.0" cited across `docs/roadmap/v5/v5.17.{0,1,2}.0/SESSION_REPORT.md` + `.reviews/CARRY_FORWARD.md` row Sh.H + `CLAUDE.md` preamble actually measures pre-Sh.B-immediate baseline (post-Te.4), not v5.13.0. Replace with either "−3,988 lines (−13.9%) off pre-Sh.B-immediate baseline" or "−2,285 lines (−8.18%) net v5.13.0 → v5.21.1". Both are accurate; pick one and use consistently. | 30 min |
| **RC.13** | LOW | **`tests/bootstrap/test_indent_preprocessor.py` count refresh** — PRE_PANEL_AUDIT.md and CARRY_FORWARD.md cite 142; live collection at HEAD is 201. Update both references. | 5 min |
| **RC.14** | LOW | **Bo.22** — README Hello World + Write-Python-Compile-Native sections: `mapanare run` → `mnc run`, `mapanare init` → `mnc init`, `mapanare build` → `mnc build`, `mapanare check` → `mnc check`, `mapanare lsp` → `mnc lsp`. Add `mapanare` alias note parenthetically: `(mapanare is also installed as an alias for mnc.)`. Matches install.ps1 / install.sh "Get started" output. **2nd consecutive panel.** | 5 min |
| **RC.15** | LOW | **Bo.26** — link `docs/guides/formatter.md` and `docs/guides/init.md` from README. Add 2 link lines after the `mnc fmt` and `mnc init` invocations: `Source canonicalization: docs/guides/formatter.md. New project scaffolding: docs/guides/init.md.` | 3 min |

---

## Phase plan

### Phase 0 — pre-flight verification

Before starting, verify the v5.22.0 baseline holds:

```bash
bash scripts/verify_fixed_point.sh --keep
# expected: stage2.ll == stage3.ll, 238086 lines, 0 diff

python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: All 95 tests passed

cat VERSION
# expected: 5.22.0

# Reproduce each CI failure locally
python3 scripts/check_struct_registry.py; echo "exit: $?"
# expected: exit 1, 23 violations

python3 scripts/check_no_hollow_features.py; echo "exit: $?"
# expected: exit 1, 2 violations

python3 scripts/check_docs_drift.py; echo "exit: $?"
# expected: exit 1, 1 violation at SPEC.md:1456

python3 scripts/check_changelog_honesty.py; echo "exit: $?"
# expected: exit 1, 1 violation on .reviews/v5.22.0/PRE_PANEL_AUDIT.md
```

If any of the expected failures don't reproduce, stop and
investigate before proceeding.

### Phase 1 — RC.1 Reg.1 (HIGH, longest item)

1. Edit `scripts/check_struct_registry.py`:
   - Update `STRUCT_HEADER_RE` to accept `[\{:]`.
   - Extend `parse_struct_defs` to handle colon-form bodies
     (indent-based termination).
2. Run the gate: `python3 scripts/check_struct_registry.py`.
3. **Expected: non-zero violations after regex restoration.**
   These are real latent drifts from the 5-release blind
   window. For each:
   - Determine if registry is wrong or source is wrong.
   - Update whichever is wrong.
4. Re-run gate: must be clean.
5. Update `tests/test_ci.py::test_struct_registry_gate_passes`
   if needed.
6. Document each drift fix in the SESSION_REPORT as a separate
   RC.1.x sub-item.

### Phase 2 — RC.2 Bo.18r + RC.3 Bo.25 + RC.14 Bo.22 + RC.15 Bo.26

Bundled because they all touch README files and want one
careful pass.

1. **RC.2** — rewrite README.md:188-192 paragraph per Boa's diff.
2. **RC.3** — bump goldens badge across all 4 READMEs (one-shot).
3. **RC.3 structural** — extend `scripts/bump_version.py`:
   - Add `_GOLDENS_BADGE_RE` regex.
   - Add `_count_goldens()` helper (`len(list(Path("tests/golden").glob("*.mn")))`).
   - Sweep all 4 READMEs in `do_bump()` parallel to the
     version-badge sweep.
   - Add a unit test in `tests/test_bump_version.py`.
4. **RC.14** — README Hello World `mapanare *` → `mnc *` (5 substitutions).
5. **RC.15** — README guide-link section (2 new link lines).
6. CRLF restoration on touched README files (`sed -i 's/$/\r/'` for files that lost CRLF).

### Phase 3 — RC.4 hollow-feature gate + RC.5 docs drift + RC.6 CHANGELOG honesty

1. **RC.4** — `scripts/check_no_hollow_features.py`: add `CompClause`, `FieldPattern` to `_AST_INFRASTRUCTURE`. Run gate; must be clean.
2. **RC.5** — annotate `docs/SPEC.md:1456`: change `fn id(y) = y` → `fn id(y: Int) -> Int = y` OR prepend `<!-- pseudo -->` on the line above the fence. Run gate; must be clean.
3. **RC.6** — `git add -f .reviews/v5.22.0/{PRE_PANEL_AUDIT.md,prompt.md,README.md,V5_DECISION.md,01-rattler.md,02-viper.md,03-anaconda.md,04-cobra.md,05-coral.md,06-boa.md,07-mamba.md}`. Verify CI tree picks them up. Run `python3 scripts/check_changelog_honesty.py`; must be clean.

### Phase 4 — RC.7 Docker Smoke + RC.8 macOS/iOS cross-compile + RC.9 stage2 ir_doctor

The 3 cross-platform / workflow fixes. Each touches its own
file; can land together.

1. **RC.7** — edit `.github/workflows/publish-docker.yml`. Add a "Build runtime" step before the `cp` at line 85. The build step is `make -C runtime/native libmapanare_rt.a` or `gcc -c runtime/native/mapanare_core.c -o ... && ar rcs runtime/native/libmapanare_rt.a ...` — match what `Makefile` uses if present. Verify by re-running the GHA workflow on push.
2. **RC.8** — investigate `mapanare/cli.py` shell-out path for clang. The Python bootstrap's `run` / `build` commands need to add `-L runtime/native -lmapanare_rt` (or the equivalent static-library path) to the clang command on Darwin. Confirm fix locally with `MAPANARE_HOST=darwin python3 -m mapanare run examples/hello.mn` if reproducible. Otherwise rely on CI re-run.
3. **RC.9** — edit `scripts/ir_doctor.py`. Find the `stage2` subcommand. Either pre-build `mnc_all.mn` and compile per-module-from-mnc_all OR pass a `--link-all` flag that resolves cross-module symbols before per-module compile. Test locally: `python3 scripts/ir_doctor.py stage2 --timeout 30` should report 11/11 OK at HEAD.

### Phase 5 — RC.10 / RC.11 / RC.12 / RC.13 (LOW polish)

1. **RC.10** — add `__mn_indent_to_braces` decl to `runtime/native/mapanare_core.h`.
2. **RC.11** — write `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` retroactively. Use PLAN + PROMPT + DOCKER_DESIGN + git log of the 3 commits as source.
3. **RC.12** — `sed`-replace "−13.9%" / "13.9%" / "13.2%" mentions in v5.17.{0,1,2}/SESSION_REPORT.md + CARRY_FORWARD.md row Sh.H + CLAUDE.md preamble. Pick one canonical phrasing.
4. **RC.13** — refresh "142" → "201" in PRE_PANEL_AUDIT.md + CARRY_FORWARD.md.

### Phase 6 — closeout

1. SESSION_REPORT.md.
2. CHANGELOG `## [5.23.0]` entry.
3. CLAUDE.md release note at top.
4. Bump VERSION 5.22.0 → 5.23.0.
5. `python3 scripts/bump_version.py 5.23.0` (now also updates goldens badge per RC.3 structural).
6. CRLF restoration on README + CHANGELOG + CLAUDE.md.
7. Update `.reviews/CARRY_FORWARD.md` v5.23.0 row marking RC.\* items as closed.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| RC.1 regex restoration surfaces real Ge.1-class drift hidden during 5-release blind window | HIGH | Per v4.143.0 retrospective precedent, expect non-zero. Investigate every flagged drift; either fix at source or update registry. Document each in SESSION_REPORT |
| RC.6 Option A (track .reviews/) explodes git LFS storage | LOW | The 7 reviewer files + README + V5_DECISION + audit + prompt + 11 prior-panel directories are <10 MB total; well under GitHub's recommended limits |
| RC.8 macOS/iOS fix exposes deeper Darwin Mach-O work | MEDIUM | If a one-arg flag in `cli.py` works, ship at v5.23.0. If it surfaces deeper symbol-prefix issues, defer to v5.24.x and unblock by ignoring the macOS lane in CI for 1 release |
| RC.9 ir_doctor.py stage2 fix breaks the Linux stage2 lane (different mode) | LOW | `ir_doctor.py` has a comprehensive test suite; run that before committing |
| Bundling all 15 items into one session bloats scope | MEDIUM | Most are 5 min; only RC.1, RC.7, RC.8, RC.9 are 1-2h. Total worst-case is ~6h. Split if scope creeps but try to land as one |
| Bo.18r 3rd-panel sensitivity — close at the wrong line again | LOW | Boa's exact suggested diff in `.reviews/v5.22.0/06-boa.md` finding #1 names `README.md:188-192`. Use that as the target |

---

## Success criteria

- [ ] All 4 panel-flagged CI gates green: `check_struct_registry`, `check_no_hollow_features`, `check_docs_drift`, `check_changelog_honesty`
- [ ] All 4 NEW CI failures resolved: CHANGELOG honesty (already in panel-flagged via RC.6 — same root cause), Docker Smoke, macOS/iOS cross-compile, Self-Hosted Compiler stage2 ir_doctor
- [ ] Bo.18r CLOSED at `README.md:188-192` (rounded `238k` framing)
- [ ] Bo.25 CLOSED structurally via `bump_version.py` extension
- [ ] Goldens 95/95 preserved
- [ ] Strict 3-stage fixed point preserved at 238,086 / 0 diff
- [ ] `make lint` clean
- [ ] `make ci-gates` (when v5.24.0 ships) will be green at v5.23.0 HEAD with 4 fewer red gates
- [ ] `.reviews/CARRY_FORWARD.md` updated
- [ ] SESSION_REPORT.md written
- [ ] CHANGELOG `## [5.23.0]` entry
- [ ] CLAUDE.md release note
- [ ] VERSION bumped 5.22.0 → 5.23.0
- [ ] `bump_version.py` sweep (badges incl. new goldens)

---

## Out of scope (explicitly held)

- **V.9 indent-preprocessor leak.** v5.23.1 (Mb.1).
- **Te.5 ASan leaks** (88_if_let, 90_while_let, 91_let_else). v5.23.1 (Mb.2).
- **Te.3 hollow-surface** (single-line shape + native mirror). v5.23.2.
- **`make ci-gates` Makefile target.** v5.24.0 (Hy.1).
- **`check_doc_freshness.py`** structural fix. v5.24.0 (Hy.2).
- **Cadence enforcement gate.** v5.24.0 (Hy.3).
- **Pk.1.A** Linux/macOS versioned-tarball smoke gates. v5.24.0 (Hy.5).
- **Manifesto M2** + **SPEC corpus M3** + **Coral L1–L5**. v5.24.1.
- **Compiler / runtime / `mapanare/self/*.mn` edits.** None.

---

## What this release CANNOT do

- Reduce the v5.22.0 panel docket count below the post-RC.\*
  level. v5.23.1 + v5.23.2 + v5.24.0 + v5.24.1 close the
  remaining items.
- Touch v6.0 carry items (Rt.04, Te.3 hard removal,
  stage2-teardown, single-line `if x: y`).
- Ship Option-B-shape recovery work — v5.22.0 panel was Option
  A; this is closure, not recovery.
