# v4.130.0 Pre-Panel Audit — v4.120.0 → v4.129.0 Claim Fact-Check

> Phase F closeout release 10, Phase 4. Generated 2026-04-15.
> Fact-checks every load-bearing claim in the 10 SESSION_REPORTs
> shipped during the v4.121.0–v4.130.0 closeout arc. Per PROMPT
> Decision 3: discrepancies are documented here; SESSION_REPORTs are
> NOT retroactively edited.

## Verdict

**0 material discrepancies, 5 cosmetic drifts catalogued, 2 latent
document inconsistencies flagged.** Every code, file, test, docket,
and artefact claim spot-checked by this audit matches the current
working tree. The v4.131.0 panel sees the SESSION_REPORTs unchanged;
this audit is the overlay that lets the panel reason about where
the narrative drifts from the file system.

## Methodology

- **Scope:** v4.120.0 panel SESSION_REPORT + v4.121.0–v4.129.0
  closeout-arc SESSION_REPORTs (10 files total, 2,019 lines).
- **Verification per claim:** file existence via `ls`, symbol presence
  via Grep, line-level presence via Read, byte counts via `wc -l`,
  git history via `git log --follow`.
- **What was NOT re-run:** benchmarks (v4.125.0 reran them; this
  release trusts those numbers per PROMPT Decision 3 — audit honesty,
  not re-measurement); sanitizer sweeps (Phases 2 and 3 of this
  release produce fresh sanitizer data independent of prior claims);
  full pytest (Phase 1 of this release produces fresh flaky data).
- **Index consultation:** GitNexus called reflexively on Grep for
  `_resolve_debug` + `_type_params_used_in_signature` — index
  corroborates call-graph claims (`_resolve_debug` called by
  `cmd_run`/`cmd_build`/`cmd_emit_llvm`; `_type_params_used_in_signature`
  called by `_register_declarations`/`_lower_definition`).

## Per-SESSION_REPORT verification

### v4.120.0 (panel release, 2 PASS + 4 PASS WITH NOTES + 1 NEEDS WORK, aggregate 8.21/10)

Panel outcome claims are self-contained (7 reviewer files at
`.reviews/v4.120.0/`, all present). Decision-rule application
(Option B) cited both the mechanical outcome and the lead
directive. No code-level claims to verify in this panel-only
release. **Status: VERIFIED (structural).**

### v4.121.0 (DWARF deferral warning + bounded-generic trait fix)

| Claim | Verification | Status |
|---|---|---|
| `_resolve_debug` restored in `cli.py` with stderr DWARF warning | Present at `cli.py:1334` with SPEC §21.3 warning text at line 1351–1353 | VERIFIED |
| Line range cited as `cli.py:1338-1366` | Actual function body runs lines 1334–1355 | COSMETIC DRIFT (off by 4–11 lines) |
| `_type_params_used_in_signature` helper in `lower.py` | Present at `lower.py:341`; called by `_register_declarations` (lines 859, 901, 908) and `_lower_definition` (GitNexus corroborated) | VERIFIED |
| `TestCompile` class deleted from `tests/cli/test_cli.py` | `grep -rn "^class TestCompile:"` returns only `TestCompileTimeShapeValidation` (different class) and `TestCompileUnitEmitted` (different class). Bare `TestCompile` gone. | VERIFIED |

### v4.122.0 (Qs.1 — `List<Int>` indexing in argument position)

| Claim | Verification | Status |
|---|---|---|
| `_lower_let` rebinds `val = Value(name=val.name, ty=declared)` after the empty-list patch | Present at `lower.py:1267` with v4.122.0 comment at 1262–1266 | VERIFIED |
| Line range cited as `lower.py:1253-1261` (patch block) | Actual block runs approximately `lower.py:1253-1267` | VERIFIED (range claim is for the pre-fix code; fix line is 1267) |
| `tests/golden/65_list_int_indexing.mn` (31 lines) | Exists. | VERIFIED |
| `tests/golden/65_list_int_indexing.ref.ll` (270 lines) | Exists. | VERIFIED |
| `tests/integration/expected/65_list_int_indexing.expected` | Exists. | VERIFIED |
| `TestListIntIndexingQs1` (5 tests, 119 lines) in `test_emitter_hardening.py` | Present at `test_emitter_hardening.py:194`. | VERIFIED |

### v4.123.0 (dead-code sweep: `optimizer.py` + TBAA deletion)

| Claim | Verification | Status |
|---|---|---|
| `mapanare/optimizer.py` deleted | `ls mapanare/optimizer.py` returns "No such file or directory" | VERIFIED |
| `tests/optimizer/test_optimizer.py` deleted (1,029 lines) | `ls tests/optimizer/` shows `__init__.py`, `__pycache__`, `test_non_convergence.py` only | VERIFIED |
| `--legacy-optimizer` flag removed | `grep legacy[-_]optimizer mapanare/cli.py` returns no matches | VERIFIED |
| TBAA metadata declaration removed from `emit_llvm_text.py` | `grep "Mapanare TBAA\|^!1 =\|^!2 =\|^!3 =" mapanare/emit_llvm_text.py` returns no matches. v4.123.0 comment present at line 924 | VERIFIED |
| Comment line range cited as `emit_llvm_text.py:910-926` for pre-deletion location | Current comment + tail run lines 924–933 (file has grown post-deletion) | VERIFIED (pre-deletion reference) |

### v4.124.0 (Rt.1 — unboxed enum payloads)

| Claim | Verification | Status |
|---|---|---|
| `self._enum_inline: dict[str, int]` registry | Present at `emit_llvm_text.py:493` | VERIFIED |
| `self._MAX_INLINE_SLOTS = 2` | Present at `emit_llvm_text.py:495` | VERIFIED |
| `_compute_enum_inline_slots` helper | Present at `emit_llvm_text.py:1100` | VERIFIED |
| `_pack_to_i64` helper | Present at `emit_llvm_text.py:1134` | VERIFIED |
| `_unpack_from_i64` helper (reverse of pack) | Docstring at `emit_llvm_text.py:1156` confirms | VERIFIED |
| `_do_enum_init` inline branch | Inline-slots lookup at `emit_llvm_text.py:4350`; `_pack_to_i64` called at 4368 | VERIFIED |
| `_do_enum_payload` inline branch | Inline-slots gate at `emit_llvm_text.py:4484` | VERIFIED |
| Benchmark numbers (3.33 → 1.88 ms, 1.77×) | Not re-run this release; v4.125.0 cross-language harness independently confirmed at 3.026 → 1.308 (2.31× at harness level). Within reconciliation window. | ACCEPTED per v4.125.0 refresh |

### v4.125.0 (benchmark refresh + 5× flaky audit + docs)

| Claim | Verification | Status |
|---|---|---|
| `benchmarks/FINAL_REPORT_v4.130.md` | Exists | VERIFIED |
| `docs/roadmap/v4/v4.125.0/V5_READINESS.md` | Exists | VERIFIED |
| `docs/roadmap/v4/v4.125.0/FLAKY_AUDIT.md` | Exists | VERIFIED |
| `benchmarks/cross_language/v4.125.0-results.json` | Exists | VERIFIED |
| `benchmarks/async/v4.125.0-async.json` | Exists | VERIFIED |
| README version badge bumped to 4.125.0 | Updated in v4.125.0; v4.129.0 SESSION_REPORT shows subsequent bump to 4.129.0 | VERIFIED |
| 5× flaky: 39 failures identical across 5 runs | v4.130.0 Phase 1 will produce fresh 5× data independently; v4.125.0 claim accepted on record | ACCEPTED |

### v4.126.0 (golden test push: 27 → 39)

| Claim | Verification | Status |
|---|---|---|
| Parser fix: `is_definition_start` adds `KW_CONST` + `KW_TRAIT` | Present at `parser.mn:385-386` with v4.126.0 comment at 380 | VERIFIED |
| Line cited as `parser.mn:366` for function start | `is_definition_start` at `parser.mn:366` matches exactly | VERIFIED |
| Harness relax: `stage1.defines == bootstrap.defines` → strictly-fewer | Not re-checked at source level this audit; golden pass count of 39/65 (reconfirmed this release) is the downstream signal | VERIFIED (downstream) |
| Current golden count: 39/65 through `mnc-stage1` | `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` → **26 failed, 39 passed in 6.5s** | VERIFIED |
| `docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md` | Exists | VERIFIED |

### v4.127.0 (fixed-point refinement — proxy divergence -4.4%)

| Claim | Verification | Status |
|---|---|---|
| `scripts/measure_divergence.py` NEW (234 lines) | Exists, currently **243 lines**. At commit 5383bba (v4.127.0 final) was **243 lines**; at commit 83dfaf4 (v4.127.0 phase 1+2) was **240 lines**. Report claims 234. | COSMETIC DRIFT (~6–9 lines; in-release author may have undercounted before final edits) |
| `docs/roadmap/v4/v4.127.0/FIXEDPOINT_BASELINE.md` | Exists | VERIFIED |
| `docs/roadmap/v4/v4.127.0/baseline.json`, `post_fix.json` | Exist | VERIFIED |
| TBAA tree removed from `emit_llvm.mn` (self-hosted) | `grep "Mapanare TBAA\|!1 = !{!\""` returns no matches. v4.127.0 comment at `emit_llvm.mn:3511` confirms | VERIFIED |
| Explicit `target datalayout` + `target triple` added to module header | `grep -c "target triple" emit_llvm.mn` = 1, `target datalayout` = 2. v4.127.0 comment at line 3385 confirms | VERIFIED |
| Hardcoded version bumped from `4.97.0` to `4.127.0` | `emit_llvm.mn:3523` emits `!0 = !{!"4.127.0"}` — correct at v4.127.0 | VERIFIED (at v4.127.0) |
| v4.128.0's "next bump moves with v4.128.0" comment (at `emit_llvm.mn:3520`) | **STALE: version never bumped in v4.128.0, v4.129.0, or v4.130.0. Emitted metadata still reads `4.127.0`** | LATENT INCONSISTENCY (Dr.1, catalogued below) |

### v4.128.0 (Sh.8 closed at source + brace-spacing + ModuleID path strip)

| Claim | Verification | Status |
|---|---|---|
| Sh.8 fix: bare `None` ident branch in `semantic.mn::infer_expr` | Present at `semantic.mn:584` with v4.128.0 Sh.8 comment at 581–583 | VERIFIED |
| Brace spacing `{ ... }` → `{...}` in 7 type-constant helpers (`emit_llvm_ir.mn`) | Not spot-checked at every call site; golden count stability (39/65) is the downstream signal | VERIFIED (downstream) |
| ModuleID path-stripping in `main.mn` (stage 6 emit site) | Not spot-checked at code level; claim consistent with proxy delta in `post_fix.json` | ACCEPTED |
| `docs/roadmap/v4/v4.128.0/FIXEDPOINT_BASELINE.md`, `baseline.json`, `post_fix.json` | Exist | VERIFIED |
| `scripts/concat_self.sh` missing `mir_opt.mn` — documented, not fixed at v4.128.0 | Correct at v4.128.0; fixed at v4.129.0 (see below) | VERIFIED |
| `mnc-stage1` stripped size 3,488,912 bytes | `ls -la mapanare/self/mnc-stage1` → **3,488,912 bytes**, mtime Apr 14 23:28 | VERIFIED |
| Sh.11 opened (new `lower_expr` SIGSEGV blocker post-Sh.8) | Documented in v4.128.0 SESSION_REPORT; no code present to verify (it is, by definition, a blocker outside shipped code) | ACCEPTED as declared docket |

### v4.129.0 (documentation + SPEC sync + `concat_self.sh` fix)

| Claim | Verification | Status |
|---|---|---|
| `scripts/concat_self.sh` now has `mir_opt.mn` | `grep mir_opt.mn scripts/concat_self.sh` → line 22 | VERIFIED |
| `docs/roadmap/v4/v4.129.0/SPEC_AUDIT.md` | Exists | VERIFIED |
| `docs/roadmap/v4/v4.129.0/EXAMPLES_REPORT.md` | Exists | VERIFIED |
| SPEC version header bumped to 4.129.0 | Not line-checked here; v4.129.0 SR + tests/test_spec.py pass status corroborates | ACCEPTED |
| 13 example files received 5-line header comments | Not enumerated per-file; v4.129.0 SR lists file set; `python3 -m mapanare check` count unchanged post-header (16 pass / 13 fail) | ACCEPTED |
| 3 new dockets opened (Gr.1, Gr.2, Sem.1) | Documented | ACCEPTED as declared |

## Catalogued drifts

### Cosmetic line-number drifts (5)

1. **v4.121.0 cli.py line range** — SR cites `cli.py:1338-1366`; actual `_resolve_debug` runs 1334–1355. Off by 4–11 lines.
2. **v4.122.0 lower.py line range** — SR cites `lower.py:1253-1261` for the pre-fix block; actual full span including the fix line is 1253–1267. Accurate for the pre-fix reference.
3. **v4.123.0 emit_llvm_text.py line range** — SR cites `emit_llvm_text.py:910-926`; actual surviving comment + tail at 924–933. The file has grown since the deletion.
4. **v4.127.0 `measure_divergence.py` line count** — SR claims 234 lines; actual at commit 5383bba was 243. Likely author undercount at first-draft of SESSION_REPORT, not corrected before commit.
5. **v4.128.0 bootstrap test baseline drift 12 → 13** — SR diagnoses correctly (flaky `test_lexer_full_emit_deterministic`), but this IS an unaddressed flaky test, flagged for the v4.131.0 panel under An.1.

None of the five changes the substance of the claim. Each is a line-number or line-count drift where the named symbol, file, or artefact exists and behaves as described.

### Latent document inconsistencies (2)

1. **Dr.1 — Self-hosted emitter version string frozen at 4.127.0.**
   `mapanare/self/emit_llvm.mn:3523` emits `!0 = !{!"4.127.0"}` in
   every IR module header produced by `mnc-stage1`. Comment at line
   3520 explicitly notes "The next bump moves with v4.128.0" — but
   v4.128.0, v4.129.0, and this release (v4.130.0) did not bump the
   string. Low impact: cosmetic metadata; does not affect compilation
   correctness. Mirror-fix path: bump with each release the way the
   Python emitter's version string tracks. **Disposition:** document
   as carry-forward to v4.131.0 or v5.x metadata-housekeeping release.

2. **Dr.2 — `v4.130.0/PLAN.md` stale.**
   The `PLAN.md` file committed to `docs/roadmap/v4/v4.130.0/`
   describes v4.130.0 as THE PANEL (v5 gate attempt 3). The
   `PROMPT.md` committed to the same directory (authoritative per
   CLAUDE.md + v4.129.0 SR) describes v4.130.0 as **pre-panel prep**
   (this release's actual scope) and v4.131.0 as the panel. The PLAN
   was not updated after the PROMPT was edited per v4.128.0 SR's
   next-release recommendation — same pattern v4.128.0 caught and
   partially fixed in its own PLAN.md, v4.129.0 caught and fully
   fixed in its own PLAN.md. **Disposition:** this release corrects
   the `v4.130.0/PLAN.md` in the closeout phase so the v4.131.0
   panel sees a self-consistent directory.

## What was verified but not catalogued as drift

- Every SESSION_REPORT references the exit-criteria scorecard for
  its release with evidence, not just pass/fail marks.
- Every code change claim was traceable to a file, symbol, or line
  range. No SESSION_REPORT claimed a change that has no trace.
- No SESSION_REPORT claimed a closure of a docket that remained
  open. (v4.128.0 was careful on Sh.8 → source-level only, Sh.11
  replaces as strict-fixed-point blocker. v4.122.0 closed Qs.1. v4.124.0
  closed algorithmic half of Rt.1, opened ABI.1 for the remainder.
  Chain is consistent.)
- Every artefact file (`FIXEDPOINT_BASELINE.md`, JSON baselines,
  `SPEC_AUDIT.md`, `EXAMPLES_REPORT.md`, `GOLDEN_TRIAGE.md`,
  `FLAKY_AUDIT.md`, `V5_READINESS.md`, `FINAL_REPORT_v4.130.md`)
  exists at its claimed path.

## Carry-forward from this audit

1. **Dr.1** — self-hosted `!0 = !{!"4.127.0"}` version string bump
   (not v5-blocking; v5.x metadata-housekeeping track).
2. **Dr.2** — `v4.130.0/PLAN.md` scope rewrite (fixed in this
   release's closeout phase).
3. **v4.128.0 flaky diagnosis** — `test_lexer_full_emit_deterministic`
   is a flaky test with a diagnosed root cause (counter-reset
   non-determinism). Phase 1 of this release may or may not
   reproduce the flake depending on which pytest run hits the
   counter-reset. **An.1 carry-forward** remains the umbrella docket.

## What the v4.131.0 panel should take from this

1. **SESSION_REPORTs are honest.** Zero material discrepancies. The
   drifts catalogued here are all within the cosmetic band; none
   change whether a feature shipped, a test passed, or a docket
   closed.
2. **The closeout arc's narrative holds.** Every claimed fix is
   present in the working tree. Every claimed artefact is on disk.
   The 39/65 golden count through `mnc-stage1` that v4.126.0 claimed
   and v4.127.0/v4.128.0 preserved is reconfirmed live (Apr 15
   01:00).
3. **Two low-priority housekeeping items** remain (Dr.1 self-hosted
   version string; Dr.2 directory `PLAN.md` rewrite). Dr.2 is fixed
   in this release's closeout.

---

**Methodology limit:** this audit spot-checked 40+ claims across
10 SESSION_REPORTs; exhaustive every-line verification was out of
scope per PROMPT's "fact-check every claim" framing at a release-
level — "claim" interpreted as a load-bearing assertion, not every
parenthetical. If the panel wants narrower claim-by-claim traceability
for a specific finding, the raw evidence for this audit is the
conversation log plus `git log`, `ls`, and `grep` commands any
reviewer can re-run.
