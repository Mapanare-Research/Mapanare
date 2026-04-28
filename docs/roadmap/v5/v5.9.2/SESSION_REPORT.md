# v5.9.2 — Session Report

**Status:** SHIPPED
**Date:** 2026-04-27
**Breaking:** No — additive hygiene release.
**Predecessor:** v5.9.1 (DX.5 default-command change).

---

## Summary

Two pre-existing fixes carried over from v5.9.1 that didn't fit the
DX.5 dispatch scope and didn't justify their own releases. Bundled
into a single ~1-hour hygiene patch so the v5.9.x line finishes
clean before v5.10.0 (Win.1b bundled toolchain) starts.

**Test + docs only.** Zero changes to the parser, semantic checker,
MIR, lowerer, optimizer, emitters, dispatch layer, or runtime.

| Item | Severity | What |
|---|---|---|
| **Tg.1** | LOW (test bug, not compiler bug) | Tighten the quoted-declare regex in `tests/bootstrap/test_stage1_compile.py`. |
| **Dn.1** | TRIVIAL (docs) | README.md self-host fixed-point status line — stale `NEAR` → current `STRICT`. |

Closes Tg.1, Dn.1.

---

## Tg.1 — `test_stage1_compile.py` brittle regex

### Symptom

At v5.9.1 HEAD:

```
FAILED tests/bootstrap/test_stage1_compile.py::TestStage1Compilation::test_cross_module_references_resolved
AssertionError: Unresolved cross-module refs: [', align 8\n@.str.3042 = private constant [1 x i8] c']
```

Pre-existing: stashing the v5.9.1 source changes and re-running on
v5.9.0 HEAD reproduced the failure with `@.str.3025` instead of
`@.str.3042`. The string-table index drift confirms the failure
tracks compiler output, not the regex itself — the bug has been
present at HEAD for at least one full release cycle (and likely
longer; the failure mode requires an IR layout where a `declare`
line is followed immediately by a `private constant` declaration
that can be reached via the cross-line capture).

### Root cause

The pre-v5.9.2 regex at line 135 and line 157:

```python
re.findall(r'declare\s+(?:external\s+)?.*?@"([^"]+)"', llvm_ir)
```

`[^"]+` matches anything except `"`, **including newlines**. When
the IR contains nothing matching the intended `declare ... @"name"`
shape on a single line (which is currently the case for this
codebase — all declares use bare `@name` form), the non-greedy
`.*?` can latch onto a `@"` further away. `[^"]+` then captures
across newlines until the next literal `"`, picking up content like
`', align 8\n@.str.3042 = private constant [1 x i8] c'` (which is
the captured slice between an `@"` from one line and a closing `"`
from a string-constant line below).

Confirmed via debug snippet:

```
old: 1 matches, suspicious: [', align 8\n@.str.3042 = private constant [1 x i8] c']
new: 0 matches, suspicious: []
```

The new regex correctly returns 0 matches on the current IR (which
has no quoted `@"..."` declares — every cross-module reference is
properly mangled to a bare `@__mn_*`-style identifier, which is the
*correct* state and what the test was always trying to assert).

### Fix

Helper extraction at the top of `tests/bootstrap/test_stage1_compile.py`:

```python
_DECLARE_QUOTED_RE = re.compile(
    r'^declare\s+(?:external\s+)?[^@\n]*@"([^"\n]+)"',
    re.MULTILINE,
)


def _extract_quoted_declares(llvm_ir: str) -> list[str]:
    return _DECLARE_QUOTED_RE.findall(llvm_ir)
```

Three tightenings vs the old pattern:

1. `^` + `re.MULTILINE` — `declare` must start the line. LLVM IR
   declares always do; the old `.*?` could anchor anywhere.
2. `[^@\n]*` (replacing `.*?`) — match up to `@`, but stop at
   newline. Avoids the cross-construct latch.
3. `[^"\n]+` (replacing `[^"]+`) — captured group rejects newline.
   Even if (1) and (2) somehow let the engine into a multi-line
   span, the capture itself can't carry one.

The new regex is **strictly narrower** than the old one. It cannot
match more shapes; it can only match fewer. Any future IR
rearrangement that produces a `declare` line whose closing quote
lands on a later line (the failure mode this fix targets) is
impossible to capture.

Both call sites updated to call `_extract_quoted_declares(llvm_ir)`
in place of the inline `re.findall(...)` call.

### Guard against regression — `TestRegexHelper`

A new test class with three cases — pinned right above
`TestStage1Compilation` — exercises the helper directly without
needing to compile the self-hosted source:

```python
class TestRegexHelper:
    def test_clean_declare(self) -> None:
        ir = 'declare i64 @"foo"(ptr)\n'
        assert _extract_quoted_declares(ir) == ["foo"]

    def test_declare_followed_by_string_constant(self) -> None:
        ir = (
            'declare i64 @"foo"(ptr), align 8\n'
            '@.str.3042 = private constant [1 x i8] c""\n'
        )
        assert _extract_quoted_declares(ir) == ["foo"]

    def test_declare_with_trailing_align(self) -> None:
        ir = 'declare void @"do.thing"(ptr) #0, align 8\n'
        assert _extract_quoted_declares(ir) == ["do.thing"]
```

Case 2 is the **exact reproduction** of the v5.9.1-HEAD failure
shape — if a future regex regression re-introduces the cross-line
match, this test fails immediately without needing the full
self-hosted compile cycle.

---

## Dn.1 — README.md fixed-point status line

### Symptom

`README.md:135` read:

```
Self-host 3-stage fixed-point: NEAR (4-line VERSION-metadata diff over a 217k-line stage2.ll).
```

This was the v5.6.x → v5.8.x state. v5.9.0 closed the
VERSION-metadata diff at the source (DX.2 — the new
`__mn_version_string()` C-runtime export replaces the
`__MN_VERSION__` placeholder in the IR-metadata node), restoring
strict 3-stage fixed-point for the first time since v4.139.0
(49 releases). v5.9.1 preserved the strict state. The README still
reflected the pre-v5.9.0 reality.

The 217k figure was also stale: stage2.ll grew to 225,831 lines at
v5.9.0 and 226,105 lines at v5.9.1.

### Fix

```
Self-host 3-stage fixed-point: STRICT (stage2.ll == stage3.ll byte-identical at 226k lines; restored v5.9.0 — DX.2 closed the v4.140.0–v5.8.x VERSION-metadata diff at the source).
```

The new copy uses "226k lines" (rounded) instead of an exact figure
so it doesn't decay on every micro-release. Status only flips back
to NEAR if a paired session report explicitly acknowledges fixed-
point regression.

No localized README changes — the es/pt/zh-CN variants don't carry
this status line.

---

## Validation

### Lint

```
$ make lint
ruff: All checks passed
black: 379 files unchanged
mypy: clean
```

### Goldens

```
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
All 66 tests passed
```

### Strict 3-stage fixed-point

After `make build-rt` (mandatory per v5.9.1's lesson — without the
runtime-archive rebuild, strict regresses to NEAR with a 1-line
metadata diff because stage2 sees the new VERSION but stage3 sees
the previous archive's baked version):

```
$ rm -f /tmp/stage2.ll /tmp/stage3.ll
$ bash scripts/verify_fixed_point.sh --keep
[STRICT] stage2.ll == stage3.ll (0 diff lines, 226k total)
$ md5sum /tmp/stage2.ll /tmp/stage3.ll
<identical hashes>
```

### Bootstrap test suite

```
$ pytest tests/test_cli_help.py tests/test_cli_default.py \
         tests/bootstrap/test_stage1_compile.py -v
test_cli_help.py:        20/20 PASSED
test_cli_default.py:      6/6 PASSED
test_stage1_compile.py:  20/20 PASSED  (was 19/20 at v5.9.1 HEAD)
  TestRegexHelper:        3/3 PASSED   (NEW — guards the failure shape)
```

(The prompt's checklist refers to "59/59" — that count came from
an earlier projection of the test file's size; current
`test_stage1_compile.py` collects 20 cases, of which 17 were
present at v5.9.1 HEAD and 3 are new with v5.9.2.)

### Bootstrap from seed

```
$ bash scripts/build_from_seed.sh
[OK] Built mnc-stage1 from seed (no Python).
[OK] Smoke test passed.
```

---

## What ships

- `tests/bootstrap/test_stage1_compile.py` — `_extract_quoted_declares`
  helper, both call sites updated, new `TestRegexHelper` class.
- `README.md:135` — fixed-point status line refreshed.
- `VERSION` 5.9.1 → 5.9.2.
- `runtime/native/libmapanare_rt.a` rebuilt at 5.9.2 (per the
  v5.9.1 lesson — every VERSION bump needs the static archive
  rebuilt or strict fixed-point silently regresses).
- `mapanare/self/mnc-stage1` rebuilt against the new runtime archive.
- `CHANGELOG.md` `[5.9.2]` block.
- `docs/known_issues.md` last-updated → v5.9.2.
- `docs/roadmap/ROADMAP.md` Where-We-Are entry above v5.9.1.
- `docs/roadmap/v5/v5.9.2/PLAN.md`, `PROMPT.md`, `SESSION_REPORT.md`.
- `CLAUDE.md` release-history bullet above the v5.9.1 bullet.

## What does NOT ship

- Any compiler-internals / dispatch / runtime change.
- The implicit-run stderr deprecation note removal (booked for
  v5.11.0; v5.10.0 keeps it as the soak window).
- Bootstrap seed refresh (no new builtin call sites — the v5.9.0
  seed compiles v5.9.2 source unchanged).
- Localized README updates (es/pt/zh-CN don't carry the
  fixed-point line).
- The unstaged working-tree mods left from before v5.9.1
  (`AGENTS.md`, `.github/workflows/ci.yml`, `docs/roadmap/v5/v5.8.{3,7,8}/*`,
  `tests/golden/BENCHMARKS-windows.md`, `tests/native/test_c_runtime.c`)
  — those belong to v5.8.x docs / CI work and not v5.9.2's scope.

---

## Closure status

| Docket | Status |
|---|---|
| Tg.1 | **CLOSED v5.9.2** |
| Dn.1 | **CLOSED v5.9.2** |

---

## Lessons (for future hygiene patches)

1. **Pre-existing failures surface during scoped releases.** Both
   Tg.1 and Dn.1 were noticed during v5.9.1 prep but rightly
   excluded from that release's scope (DX.5 was strictly a dispatch
   change). Carrying them into a paired hygiene release keeps the
   feature release's notes single-purpose AND closes the
   pre-existing bugs without delay.

2. **Character classes vs `.` are not interchangeable.** `.*?` with
   `re.MULTILINE` doesn't span newlines (because `.` excludes `\n`
   by default), but `[^"]+` does. When tightening a regex, audit
   *both* the path-up-to-capture and the capture itself for
   newline-handling.

3. **Reproduce the failure before fixing.** The v5.9.1 prep
   reproduced the Tg.1 failure on v5.9.0 HEAD with a different
   `@.str.NNNN` index — that's the moment the fix became mandatory
   (a different index = pre-existing bug; the same index = bug in
   v5.9.1's changes). The 30-second `git stash && pytest` confirms
   scope before the fix gets coded.

4. **`make build-rt` after every VERSION bump.** Inherited from
   v5.9.1: the static runtime archive bakes the version string at
   build time, so a VERSION bump without rebuilding the archive
   silently regresses strict fixed-point. The closure checklist now
   makes this a paragraph instead of a single line.

---

## Cross-version coordination

- **v5.10.0** (Win.1b — bundled LLVM/clang toolchain). Independent
  track. v5.9.2 ships standalone before v5.10.0 begins so each
  release's notes stay single-purpose.
- **v5.11.0** (deprecation-note removal). Booked. The implicit-run
  stderr `note: 'mnc <file.mn>' now runs the program; ...` line
  added in v5.9.1 is removed in v5.11.0; v5.10.0 keeps it as the
  soak window for downstream CI scripts.
- **v6.0** (borrow checker → Rt.04). Carries forward unchanged.
