# v4.129.0 Session Report — 2026-04-15

## Verdict

**Shipped. Phase F closeout release 9 — documentation and SPEC
sync.** Six phases delivered:

1. `PLAN.md` rewritten from the stale "Pre-Panel Prep + Third Flaky
   Audit" scope to match the edited `PROMPT.md` ("Documentation +
   SPEC Sync").
2. Targeted SPEC audit of the 10 most-impacted sections, plus a
   light full-file version-reference scan. 8 OK, 4 STALE, 6 WRONG.
3. SPEC fixes applied: 11 edits across §0 header, §2.1 const, §3.2
   generics, §3.6 duplicate heading, §6.3 closures, §27.1 TypeKind
   count, §28 stdlib, Appendix B.
4. All 29 examples verified — 16 pass, 13 fail in 5 named
   categories. Each failure file now carries a header comment
   citing the cause.
5. `README.md` (version badge, binding-generation note, roadmap
   table) + `getting_started.md` (self-hosted compiler status)
   refreshed; other guides audited as current.
6. Latent bug in `scripts/concat_self.sh` (mir_opt.mn missing)
   fixed. Closeout artifacts written.

**Zero compiler / runtime / self-hosted `.mn` code changes.** The
only code line touched is a one-line bash array addition in
`scripts/concat_self.sh`.

## Self-graded aggregate

**8.3 / 10**

- **SPEC audit was honest, not performative**: every classification
  in `SPEC_AUDIT.md` is backed by a concrete file:line reference or
  a grep command. Three WRONG findings (`const` note, §3.6 duplicate
  heading, §27.1 TypeKind count) were not previously documented as
  known issues — they were latent stale claims the v4.116.0
  documentation batch missed. The const note was wrong on three
  independent claims (no ConstDef, no immutability, no compile-time
  evaluation) and had been wrong since v4.55.0. +strong
- **Scope matches PROMPT.md**: did not expand into code fixes or
  flaky audit work. Every deviation from PROMPT.md is documented
  (PLAN.md rewrite was the one exception and it was a prerequisite
  to meaningful planning). +solid
- **Examples verification done correctly the second time**: the
  first check-script had a filter bug that mis-counted 29 failures;
  caught and re-ran with exit-code gating, got honest 16/13 split.
  Documented the method change in the commit. +honest
- **Decision 2 held**: per PROMPT.md, broken examples got header
  comments, not workaround-style rewrites. For `@Counter()` stale
  syntax and `extern "Python"` legacy, a proper rewrite would have
  made the examples work again — but that's a cookbook refresh, not
  a docs-sync scope. The conservative choice preserves intent
  (external readers can see the failure and the reason rather than
  a silently "fixed" facade). +solid
- **Renumbering of §3.6–§3.13 verified safe**: grepped for any §3.x
  cross-reference in docs/ before committing; found zero in current
  docs (hits were all in historical roadmap files, which correctly
  refer to the SPEC version at their time of writing). +solid
- **`concat_self.sh` fix sanity-checked**: produced post-fix output
  and diffed against Python version's output (body byte-identical).
  Not just a text edit; actually ran the script. +solid
- **Three new dockets opened but not closed**: Gr.1 (multi-line
  literals), Gr.2 (qualified type refs in type position), Sem.1
  (module-level let mut). Gr.2 blocks 2 stdlib modules and 3
  examples — non-trivial. Documenting the backlog honestly rather
  than making them go away is correct, but the v4.130.0 panel
  evidence base now includes these. -soft
- **Didn't refresh `docs/guides/async.md` or `docs/cookbook/async.md`
  content lines**: audited and judged current. Cookbook's Sh.9
  workaround section is still accurate. But a stricter reading of
  PROMPT.md's "cookbook updates for v4.121.0–v4.128.0 changes"
  could argue for a refresh-touch on every file. -soft
- **`stdlib/gpu/{tensor,kernel}.mn` parser error was uncovered but
  not fixed**: one-line fix might have closed Gr.2 and 3 examples.
  Tempted, but opted against since fixing stdlib belongs in a code
  release, not a docs-sync release. Defensible but leaves points on
  the table. -soft

## What shipped

### Code changes (production)

- `scripts/concat_self.sh` — added `mir_opt.mn` to the `MODULES`
  bash array, matching `scripts/concat_self.py::MODULE_ORDER`. One
  line changed. No other compiler or runtime code touched.

### Documentation changes

- `docs/SPEC.md` — 11 edits per SPEC_AUDIT.md findings. +115/−44
  lines.
- `README.md` — version badge, binding-generation status note,
  roadmap table.
- `docs/guides/getting_started.md` — §5 self-hosted compiler
  status refreshed.
- `CHANGELOG.md` — `[4.129.0]` entry written.

### Examples changes

- 13 files under `examples/` received a 5-line header comment
  pointing at `EXAMPLES_REPORT.md`. No example logic touched.

### Tooling / documentation artifacts

- `docs/roadmap/v4/v4.129.0/PLAN.md` — rewritten to match the
  edited PROMPT.md scope.
- `docs/roadmap/v4/v4.129.0/SPEC_AUDIT.md` — NEW. Per-section
  classification table + per-finding detail sections.
- `docs/roadmap/v4/v4.129.0/EXAMPLES_REPORT.md` — NEW. 29 examples
  categorized with failure causes and docket references.

### Verification

- `pytest tests/test_spec.py tests/test_readme.py
  tests/test_python_emitter_deleted.py`: **83 passed / 0 failed**
  in 3.8s. No code changed → no broader pytest run required; the
  audited tests directly cover the documentation surface that was
  edited.
- `scripts/concat_self.sh` verified by producing output and diffing
  against Python version — body byte-identical (17,195 lines
  each); header text differs by design.
- `python3 -m mapanare check` re-ran on all 29 examples post-
  header-add: 16 pass / 13 fail, same split as pre-header — comment
  insertion did not affect compilation.
- `libmapanare_rt.a`: not rebuilt (no C runtime changes); byte-
  identical to v4.128.0.

## New dockets opened

| ID | Title | Priority | Blocks |
|---|---|---|---|
| Gr.1 | Multi-line list/tensor literal grammar support | low | 5 examples |
| Gr.2 | Qualified type refs in type position | medium | 2 stdlib modules (`gpu/tensor.mn`, `gpu/kernel.mn`), 3 examples |
| Sem.1 | Module-level `let mut` scoping | low | 1 example (`wasm/dom_app.mn`) |

All three carry forward to v4.130.0 or later.

## Dockets closed (documentation-side)

The v4.120.0 panel's documentation findings are now addressed in
source. Boa's reviewer flags (Bo.2: SPEC currency) and Coral's
flags (Co.2–Co.4: SPEC §29 precision, struct-literal syntax, const
keyword half-life) are resolved at the SPEC level. The underlying
code/compiler state is unchanged.

## What did not ship

- **Compiler or runtime bug fixes.** Phase 3 surfaced 3 real bugs
  (Gr.1, Gr.2, Sem.1). None fixed — each one opens a docket for a
  code release.
- **Cookbook-content refresh on async.md / debugging.md**. Audited
  and judged current; PROMPT.md's scope could be read either way.
  Conservative choice: don't touch what's working.
- **`stdlib/gpu/*.mn` fix**. One-line change would close Gr.2.
  Deferred to the release that also owns the grammar fix (if a
  grammar fix is preferred over stdlib workaround).
- **CLAUDE.md refresh.** The v4.129.0 current-version paragraph is
  added below (Phase 6 closeout). No broader CLAUDE.md sweep.

## Sh.11 — still open

No change to the v4.128.0-opened Sh.11 blocker (`lower_expr`
SIGSEGV during `mnc-stage1` self-compile of `mnc_all.mn`). Reserved
for v4.131.0+ post-panel arc. Fixed-point measurement pivots to the
Python-vs-mnc-stage1 proxy remain valid; v4.127.0 and v4.128.0
closed 5.5% of that surface and no regression shipped here.

## Next release

**v4.130.0** — pre-panel prep. Third flaky audit (5× `make test`
clean), valgrind + ASan sweeps on golden tests, MEASUREMENTS.md
draft for the v4.131.0 panel. Was this release's *original* PLAN
scope before PROMPT.md was edited per the v4.128.0 SESSION_REPORT's
next-release recommendation.

**v4.131.0** — THE PANEL. v5 gate attempt 3. Seven reviewers grade
v4.121.0–v4.130.0. Mechanical rule: aggregate ≥ 9.0 AND 0 NEEDS
WORK → tag v5.0.0; otherwise continue v4.x.

This release's documentation is the primary evidence Boa and Coral
will see.
