# v5.9.2 — hygiene: pre-existing test regex + stale README line

**Status:** PLANNING
**Breaking:** No — additive bug-fix release.
**Prerequisite:** v5.9.1 shipped (DX.5 default-command change).
**Estimated effort:**
- Phase 1 (Tg.1 — brittle regex in `test_stage1_compile.py`) — 30m
- Phase 2 (Dn.1 — stale README "NEAR" → "STRICT") — 10m
- Phase 3 (validation matrix) — 30m
- **Total:** ~1 hour, single short session

---

## Goal

Ship two pre-existing-but-noticed-during-v5.9.1 fixes that don't fit
the v5.9.1 scope (DX.5 dispatch) and don't justify their own
release. Bundle them into a fast hygiene patch so the v5.9.x line
finishes clean before v5.10.0 (Win.1b bundled toolchain) starts.

After v5.9.2:

- `tests/bootstrap/test_stage1_compile.py` runs 59/59 — the brittle
  regex bug that's been present at HEAD since at least v5.9.0 is
  closed at the source.
- `README.md`'s self-host fixed-point line reads STRICT (matches the
  v5.9.0 milestone) instead of the stale v5.6.x-era NEAR copy.

This is **docs + test only**. Zero changes to the parser, semantic
checker, MIR, lowerer, optimizer, emitters, dispatch layer, or
runtime. No bootstrap seed refresh.

---

## What's broken

### Tg.1 — `test_stage1_compile.py` brittle regex

**Symptom (v5.9.1 HEAD):**

```
FAILED tests/bootstrap/test_stage1_compile.py::TestStage1Compilation::test_cross_module_references_resolved
AssertionError: Unresolved cross-module refs: [', align 8\n@.str.3042 = private constant [1 x i8] c']
```

Confirmed pre-existing: stashing the v5.9.1 source changes and
re-running on v5.9.0 HEAD reproduces the failure with a different
`@.str.NNNN` index (3025 vs 3042). The string-table index drift
means the failure tracks compiler output, not the bug — the regex
itself has been broken for at least a release cycle.

**Cross-reference with source:**

| File:line | Cause |
|---|---|
| `tests/bootstrap/test_stage1_compile.py:135` (`test_no_unresolved_enum_constructors`) | Same regex; same latent bug, doesn't currently fail because the captured-garbage strings happen not to match an enum-prefix list. Will fail any time the IR layout shifts past the latent shape. |
| `tests/bootstrap/test_stage1_compile.py:157` (`test_cross_module_references_resolved`) | Currently failing. |

**Root cause.** The regex is:

```python
re.findall(r'declare\s+(?:external\s+)?.*?@"([^"]+)"', llvm_ir)
```

`[^"]+` matches anything except `"`, **including newlines**. So when
the IR has a `declare ... @"name"` line whose closing quote happens
to land on a later line — or the regex anchors on a `@"` from the
middle of an unrelated construct — the captured group spans
multiple lines, picking up content like `", align 8\n@.str.3042 =
private constant [1 x i8] c"`. The captured "name" is then
classified as an unresolved reference, which it isn't.

The reason the capture spans lines: `.*?` is correctly non-greedy
and excludes `\n` by default, but `[^"]+` is a different character
class with different semantics — it matches everything except `"`,
including newlines.

### Dn.1 — README.md:135 stale fixed-point line

**Symptom.** README line 135 reads:

```
Self-host 3-stage fixed-point: NEAR (4-line VERSION-metadata diff
over a 217k-line stage2.ll).
```

This was the v5.6.x → v5.8.x state. v5.9.0 closed the
VERSION-metadata diff at the source (DX.2 — `__mn_version_string()`
C-runtime export replaces the `__MN_VERSION__` placeholder in the
IR-metadata node), restoring **strict** 3-stage fixed-point for the
first time since v4.139.0. v5.9.1 preserved it (stage2.ll ==
stage3.ll at 226,105 lines, identical md5). The README still
reflects the pre-v5.9.0 state.

The 217k-line figure is also stale: stage2.ll grew to 225,831 at
v5.9.0 and 226,105 at v5.9.1.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Tg.1** | LOW (test bug, not compiler bug) | Replace `[^"]+` with a newline-rejecting class in the two regex sites of `test_stage1_compile.py`. Anchor to start-of-line via `re.MULTILINE` + `^` for extra defense; the test set covers exactly the IR shape that triggered the bug, so any IR-emission rearrangement that re-triggers the latent shape is caught. | 30m |
| **Dn.1** | TRIVIAL (docs) | README.md:135 — replace stale "NEAR (4-line VERSION-metadata diff over a 217k-line stage2.ll)" with "STRICT (stage2.ll == stage3.ll byte-identical at 226k lines, restored v5.9.0)". Bump the line-count figure to current. | 10m |

---

## Phase plan

### Phase 1 — Tg.1 — test regex fix

1. **Fix the regex.** In `tests/bootstrap/test_stage1_compile.py`:
   - Line 135: `re.findall(r'declare\s+(?:external\s+)?.*?@"([^"]+)"', llvm_ir)`
   - Line 157: same pattern.

   Tighten to reject newlines inside the captured group AND anchor
   at start-of-line:

   ```python
   re.findall(
       r'^declare\s+(?:external\s+)?[^@\n]*@"([^"\n]+)"',
       llvm_ir,
       re.MULTILINE,
   )
   ```

   - `^` + `re.MULTILINE` — declare must start the line (LLVM IR
     declares always do).
   - `[^@\n]*` — non-greedy match up to `@`, but stop at newline.
     Avoids the `.*?` cross-construct match shape.
   - `[^"\n]+` — captured group rejects newline so it can't span
     lines.

   Both sites use the same pattern; refactor into a module-level
   helper `_extract_quoted_declares(ir: str) -> list[str]` and
   call from both tests so the next regex tweak only edits one
   place.

2. **Manual verification.** Construct a minimal IR snippet with the
   exact shape that breaks the old regex (a `declare` line with
   a quoted name + a string constant on the next line) and assert
   both old-regex breaks and new-regex passes. One unit test in
   `test_stage1_compile.py::TestRegexHelper` (3 cases: clean
   declare, declare-followed-by-string-constant, declare with
   trailing `, align`).

### Phase 2 — Dn.1 — README docs polish

1. **README.md:135** — replace the stale line. The new line should
   credit v5.9.0 (the structural fix) and v5.9.1 (preserved):

   ```
   Self-host 3-stage fixed-point: STRICT (stage2.ll == stage3.ll
   byte-identical at 226k lines; restored v5.9.0 — DX.2 closed the
   v4.140.0–v5.8.x VERSION-metadata diff at the source).
   ```

2. **No localized README changes** — the es/pt/zh-CN variants don't
   carry a fixed-point status line.

### Phase 3 — Validation matrix

```bash
# Lint
make lint

# Goldens 66/66 (no source/IR changes — must hold byte-identical)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Strict fixed-point (v5.9.0 milestone, preserved at v5.9.1; must hold)
bash scripts/verify_fixed_point.sh --keep
md5sum /tmp/stage2.ll /tmp/stage3.ll  # expected: identical

# CLI tests + bootstrap tests (Tg.1 must close)
pytest tests/test_cli_help.py tests/test_cli_default.py \
       tests/bootstrap/test_stage1_compile.py -v
# expected: 59/59 in test_stage1_compile (was 58/59 at v5.9.1 HEAD)
```

---

## Decisions

### Decision 1: scope discipline — fix two tests or one?

The brittle regex is at two sites (line 135 + line 157). Only line
157 currently fails. Options:

- Fix only the failing site. Smaller diff, but leaves a known
  latent bug for the next IR-layout shift to surface.
- Fix both sites + extract a helper. ~5 LOC bigger; eliminates
  duplication; the next time the regex needs tightening, both
  sites stay in sync.

**Recommend: fix both + extract helper.** Cost is negligible;
duplication-elimination is the right discipline for a hygiene
patch.

### Decision 2: ship as v5.9.2 or fold into v5.10.0?

v5.10.0 (Win.1b — bundled LLVM/clang toolchain) is non-trivial;
folding hygiene into it muddies the release notes and slows the
v5.10.0 ship. v5.9.2 ships in <1 hour and keeps each release's
notes single-purpose.

**Recommend: ship as v5.9.2** standalone before v5.10.0 starts.

### Decision 3: include the build_from_seed.sh SEED-call note?

The PLAN considered including a forward-compat note in
`build_from_seed.sh` for when the seed eventually refreshes
post-v5.9.1 (the SEED→stage1 invocation will need `emit-llvm`).
But that's tracked in v5.9.1's SESSION_REPORT and naturally surfaces
during the next Bb seed refresh (whoever ships Bb.4 will hit it).
Adding a placeholder comment now is speculative — when the seed
refreshes, the line is updated atomically with the seed.

**Recommend: skip.** Don't pre-commit forward-compat code paths;
v5.9.2 stays scoped to the two pre-existing bugs.

---

## What ships in v5.9.2

- **Source changes:**
  - `tests/bootstrap/test_stage1_compile.py` — extract
    `_extract_quoted_declares` helper; tighten regex; add
    `TestRegexHelper` with 3 cases.
  - `README.md:135` — stale "NEAR" → "STRICT" with v5.9.0 credit.
- **No compiler / runtime / dispatch changes** — zero edits to
  `mapanare/self/*.mn`, `mapanare/*.py`, `runtime/`, scripts.
- **No bootstrap seed refresh.**
- **Docs:**
  - `docs/roadmap/v5/v5.9.2/PLAN.md` (this file)
  - `docs/roadmap/v5/v5.9.2/PROMPT.md` (execution prompt)
  - `docs/roadmap/v5/v5.9.2/SESSION_REPORT.md` (closeout)
  - `CHANGELOG.md` `[5.9.2]` block
  - `docs/known_issues.md` last-updated → v5.9.2
  - `CLAUDE.md` release-history bullet
  - `docs/roadmap/ROADMAP.md` Where We Are entry above v5.9.1
- **Version:** 5.9.1 → 5.9.2 at end of Phase 3.

## What does NOT ship

- The implicit-run stderr deprecation note removal — booked for
  v5.11.0; v5.10.0 keeps it as the soak window.
- Any compiler-internals / dispatch / runtime change.
- The unstaged working-tree mods left from v5.9.1 (`AGENTS.md`,
  `.github/workflows/ci.yml`, `docs/roadmap/v5/v5.8.{3,7,8}/*`,
  `tests/golden/BENCHMARKS-windows.md`,
  `tests/native/test_c_runtime.c`) — not v5.9.x's scope; track
  separately if and when whoever owns them ships their own work.

---

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| Tg1.R1 | The new regex catches a different latent shape and starts failing on a future IR rearrangement. | The new pattern is strictly narrower than the old one (anchors `^`, rejects `\n` in two places). It cannot match more shapes; it can only match fewer. Future IR rearrangements that emit unquoted declares are out of scope of either regex. |
| Tg1.R2 | The helper extraction + new TestRegexHelper class collides with an existing class name. | grep before write; the file currently has `TestStage1Compilation` and `TestStage1LLVMEmission` — `TestRegexHelper` is fresh. |
| Dn1.R1 | The README copy ages out again the next time the line count shifts. | The new copy uses "226k lines" (rounded) instead of an exact figure, so it doesn't decay on every micro-release. The "STRICT" status only changes if a bug regresses fixed-point — unlikely without a paired session-report acknowledging it. |
| Va.R1 | Strict fixed-point (the v5.9.0 milestone) regresses. | Phase 3 runs `verify_fixed_point.sh` and gates on strict equality. Zero source changes touch the IR pipeline, so risk is theoretically zero; the gate exists to catch the unexpected. |

---

## Closure checklist

### Phase 1 (Tg.1)

- [ ] `_extract_quoted_declares(ir: str) -> list[str]` extracted
- [ ] Both call sites (line 135, line 157) use the helper
- [ ] `TestRegexHelper` added with 3 cases (clean / declare+string-
      constant / declare+align)
- [ ] `test_no_unresolved_enum_constructors` passes
- [ ] `test_cross_module_references_resolved` passes — closes the
      v5.9.1-HEAD failure

### Phase 2 (Dn.1)

- [ ] `README.md:135` updated; stale "NEAR (4-line VERSION-metadata
      diff over a 217k-line stage2.ll)" replaced with strict
      status credit

### Phase 3 (validation)

- [ ] `make lint` clean
- [ ] Goldens 66/66 byte-identical
- [ ] `bash scripts/verify_fixed_point.sh` reports STRICT (0 diff)
- [ ] `tests/test_cli_help.py` + `tests/test_cli_default.py` +
      `tests/bootstrap/test_stage1_compile.py` 59/59 pass
- [ ] `bash scripts/build_from_seed.sh` clean

### Documentation + release

- [ ] `CHANGELOG.md` `[5.9.2]` block filled in
- [ ] `docs/roadmap/v5/v5.9.2/SESSION_REPORT.md` written
- [ ] `VERSION` bumped 5.9.1 → 5.9.2
- [ ] `runtime/native/libmapanare_rt.a` rebuilt via `make build-rt`
      (per v5.9.1's lesson — the static archive bakes the version
      string; without rebuild, strict fixed-point regresses to NEAR
      with a 1-line metadata diff)
- [ ] `git tag v5.9.2` — pending user approval per project rule

---

## Cross-version coordination

- **v5.10.0** (Win.1b — bundled LLVM/clang). Independent track. v5.9.2
  ships standalone before v5.10.0 begins so each release's notes
  stay single-purpose.
- **v5.11.0** (deprecation-note removal). Booked. The implicit-run
  stderr `note: 'mnc <file.mn>' now runs the program; ...` line
  added in v5.9.1 is removed in v5.11.0; v5.10.0 keeps it as the
  soak window for downstream CI scripts.
