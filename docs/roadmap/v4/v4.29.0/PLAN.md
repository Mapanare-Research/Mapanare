# Mapanare v4.29.0 — Build Infrastructure + Test Honesty

> **Recovery release #3.** v4.27.0 fixed CRITICALs, v4.28.0 fixed
> concurrency + carry-forwards, v4.29.0 fixes the build infrastructure and
> test infrastructure that were silently allowing the previous regressions
> to ship. Still **zero new features.**

**Status:** PLANNED
**Breaking:** Possibly — `extern "Python" fn` decision may delete a feature
**Prerequisite:** v4.28.0
**Estimated work:** 1 day
**Theme:** If CI can't fail, claims about CI passing are meaningless.

---

## The Problem

Three classes of infrastructure failure let v4.18.0–v4.26.0 ship hollow
features without any review or CI catching them:

### Class A: Orphaned runtime files

Two C runtime files are 1,942 lines combined and **not built by anything**:

| File | Lines | Status |
|------|-------|--------|
| `runtime/native/mapanare_db.c` | 1,130 | Not in `build_stage1.py`, not in CI, not in `_RUNTIME_FN_ATTRS` |
| `runtime/native/mapanare_html.c` | 812 | Same |

Stdlib `.mn` files that import `db` or `html` will fail to link in any
non-developer build. (Anaconda HIGH)

### Class B: Tests silently disabled

| File | Issue | Reporter |
|------|-------|----------|
| `tests/conftest.py` | `extern "Python" fn` xfailed since v4.2.0 — 79 tests skipped silently | Boa H4 |
| `tests/llvm/test_*` | 38 tests `@pytest.mark.skip` for missing DWARF debug info | Rattler #4 |
| `tests/self_hosted/test_main_mn.py::test_version_string` | Fixed in v4.28.0 — verify still un-skipped here | (cross-ref) |
| `--no-check` | Bypasses semantic analysis, no warning, no output | Anaconda HIGH |

### Class C: Verification gates that cannot fail

| Gate | File:Line | Why it can't fail |
|------|-----------|-------------------|
| `verify_fixed_point.sh` | line 104 | `EXIT=0` unconditional regardless of diff |
| `verify_fixed_point.sh` | header | `set -uo pipefail` (no `-e`); `\|\| true` everywhere |
| `.github/workflows/ci.yml` | 558-568 | `fixed-point` job has no `exit 1` propagation |
| `stage3.ll` | (file mtime) | Zero-byte file from March 21, predates v4.20.0 |
| `Makefile` `build-rt` | enumeration | 4th carry-forward cycle, missing 4 of 5 v3.47.0 runtime files plus the 2 new orphans |

---

## Phase 1: Wire orphaned runtime files

### Phase 1.1: `mapanare_db.c`

- [ ] `Makefile` `build-rt` — add `mapanare_db.c` to the source list
- [ ] `scripts/build_stage1.py` — add `mapanare_db.c` to the runtime build
- [ ] `mapanare/emit_llvm_text.py` `_RUNTIME_FN_ATTRS` — declare exports for
      every public function in `mapanare_db.c`
- [ ] `tests/runtime/test_db_smoke.c` — NEW. Open an in-memory SQLite-style
      DB, insert one row, read it back, close. Compile and run as part of
      `make test`
- [ ] CI: add `test_db_smoke` to the C runtime test step

### Phase 1.2: `mapanare_html.c`

- [ ] Same as Phase 1.1 for `mapanare_html.c`
- [ ] `tests/runtime/test_html_smoke.c` — NEW. Parse a 5-line HTML
      fragment, query an element, free
- [ ] CI

### Phase 1.3: Makefile build-rt enumeration (4th cycle)

- [ ] `Makefile` `build-rt` — list all `runtime/native/*.c` files
      explicitly. Anaconda's review noted this is on its 4th carry-forward
      cycle. Fix it for real this time.
- [ ] Add a CI step that diffs the Makefile's enumeration against
      `ls runtime/native/*.c`. If they don't match, the CI step fails with
      a message naming the missing files.

---

## Phase 2: Test honesty

### Phase 2.1: `extern "Python" fn` decision

The 79 xfailed tests in `tests/conftest.py` are a regression from v3.47.0
that the panel missed at the time. The feature was working at v3.47.0.
`emit_python.py` was deleted in v4.2.0 as part of the emitter consolidation,
which broke `extern "Python"`. The xfail decorator was added silently.

**Decision required:**

#### Path A: Restore `extern "Python" fn`

- [ ] Restore the Python interop path against the current LLVM emitter
- [ ] This is non-trivial: the previous implementation went through
      `emit_python.py` which is gone. The new path has to lower
      `extern "Python" fn` to a runtime call into a CPython embedded interpreter
      OR generate a ctypes-style shim
- [ ] Estimated 1-2 days of work
- [ ] Un-skip the 79 tests, run them, fix any that don't pass

#### Path B: Delete the feature

- [ ] Remove `extern "Python" fn` syntax from `mapanare/mapanare.lark`
- [ ] Remove from self-hosted parser
- [ ] Delete the 79 xfailed tests (they test a non-feature)
- [ ] Document in `docs/SPEC.md` that Python interop is via the FFI path
      (`mapanare bind --lang python` from v4.25.0/v4.27.0)
- [ ] Add a CHANGELOG entry under "Removed"

**Default: Path B.** v4.27.0's FFI fix gives Python interop a real,
maintained path. `extern "Python" fn` was a v0.5.0-era convenience that
cost more to keep alive than it earned. The panel was clear: silent xfail
must go either way.

### Phase 2.2: DWARF debug info decision

38 LLVM tests are `@pytest.mark.skip` waiting for DWARF debug info that
was claimed in some version of the v4.x roadmap but never shipped.

**Decision required:**

#### Path A: Implement DWARF emission

- [ ] Add `llvm.dbg.compile_unit`, `llvm.dbg.subprogram`, `llvm.dbg.declare`
      metadata to `emit_llvm_text.py`
- [ ] Source line + column tracking for every emitted instruction
- [ ] Estimated 2-3 days
- [ ] Un-skip the 38 tests

#### Path B: Strike the claim

- [ ] Search README, SPEC, ROADMAP, CHANGELOG for any "debug info" claim;
      strike each one
- [ ] Convert the 38 tests to a single TODO test that asserts a NotImplemented
      diagnostic when `--g` (debug flag) is passed
- [ ] Document in `docs/SPEC.md` that debug info is a v5.x feature

**Default: Path B for v4.29.0; Path A becomes the v4.32.0 PLAN if there's
appetite for it.** DWARF emission is a multi-day feature; v4.29.0 is a
recovery release.

### Phase 2.3: `--no-check` warning

- [ ] `mapanare/cli.py:145,169,1890` — `--no-check` currently silently
      bypasses semantic analysis
- [ ] Print a warning to stderr when `--no-check` is used:
      `WARNING: --no-check bypasses semantic analysis. Diagnostics will not be reported.`
- [ ] Consider renaming to `--unsafe-no-check` (not required, but the rename
      makes the intent harder to miss); document the alias for backward compat
- [ ] Add a test that verifies the warning appears in stderr when the flag
      is used

### Phase 2.4: Audit `tests/conftest.py` for silent skips

- [ ] Read every `pytest.mark.skip` and `pytest.mark.xfail` in
      `tests/conftest.py`
- [ ] For each: is it tracking a known issue (with a link to a roadmap
      entry), or is it silent debt?
- [ ] Anything that's silent debt: either fix it now, file it as a v4.30.0
      task, or delete the test if it tests a non-feature
- [ ] Add a CI step that fails if a new `pytest.mark.skip` is added without
      a comment naming the tracking version

---

## Phase 3: Verification gates

### Phase 3.1: `verify_fixed_point.sh` teeth

- [ ] `scripts/verify_fixed_point.sh` — add `set -e`
- [ ] Replace every `|| true` with explicit error handling. If a step is
      allowed to fail, document why; otherwise propagate the failure.
- [ ] Replace `EXIT=0` (line 104) with `EXIT=$DIFF_LINES` or threshold:
      `EXIT=$([ "$DIFF_LINES" -lt 70 ] && echo 0 || echo 1)` (the threshold
      is arbitrary — pick the value that matches today's near-fixed-point
      state)
- [ ] Test the script: deliberately introduce a 1-line diff; verify the
      script returns non-zero

### Phase 3.2: CI fixed-point job propagation

- [ ] `.github/workflows/ci.yml:558-568` — the `fixed-point` job runs
      `verify_fixed_point.sh` but does not propagate its exit code as a
      job failure
- [ ] Fix the propagation. After Phase 3.1, the script's exit code is
      meaningful; the CI job must respect it.
- [ ] Verify by pushing a deliberately-broken branch: the CI job should
      fail red, not green

### Phase 3.3: Regenerate or delete `stage3.ll`

- [ ] `mapanare/self/stage3.ll` (or wherever the file lives) — currently
      a zero-byte file from March 21
- [ ] Option A: regenerate it as part of `verify_fixed_point.sh`. Wire its
      production into CI so it cannot go stale.
- [ ] Option B: delete it; it's not authoritative anyway since
      `verify_fixed_point.sh` produces fresh artifacts each run
- [ ] **Default: Option B.** Anything that's a stale on-disk artifact is a
      lie waiting to happen. Delete it and update any reference to it in
      the docs.

### Phase 3.4: CI hollow-feature gate

- [ ] Add a CI step that fails if any source file contains
      `raise NotImplementedError` (excluding test fixtures and stub files
      that are explicitly placeholders)
- [ ] The grep is one line:
      `git grep -l "raise NotImplementedError" mapanare/ runtime/ | grep -v "tests/"`
      should return zero results
- [ ] Document the rule in `CONTRIBUTING.md` (or wherever development
      conventions live): "If you find yourself writing
      `raise NotImplementedError`, the feature is not ready to merge."

---

## Exit Criteria

| # | Check | Required |
|---|-------|----------|
| 1 | `mapanare_db.c` built by `Makefile`, in CI, in `_RUNTIME_FN_ATTRS` | YES |
| 2 | `mapanare_html.c` same | YES |
| 3 | `test_db_smoke` and `test_html_smoke` exist and pass | YES |
| 4 | `Makefile build-rt` enumerates all `runtime/native/*.c` | YES |
| 5 | CI step diffs Makefile vs `ls runtime/native/*.c`; fails on mismatch | YES |
| 6 | `extern "Python" fn` decision executed (Path A or Path B) | YES |
| 7 | Zero `pytest.mark.xfail` left for `extern "Python"` | YES |
| 8 | DWARF decision executed (Path A or Path B) | YES |
| 9 | `--no-check` prints warning to stderr; test verifies | YES |
| 10 | Every `pytest.mark.skip` in `tests/conftest.py` has a tracking comment | YES |
| 11 | `verify_fixed_point.sh` returns non-zero on a deliberate diff | YES |
| 12 | CI `fixed-point` job propagates the script exit code | YES |
| 13 | `stage3.ll` regenerated OR deleted (no zero-byte stale artifact) | YES |
| 14 | CI gate fails if `raise NotImplementedError` appears in source | YES |
| 15 | 46/46+ golden, 11/11 stage2 | YES |
| 16 | black/ruff/mypy clean | YES |
| 17 | `docs/roadmap/v4/v4.29.0/SESSION_REPORT.md` written | YES |

---

## What v4.29.0 explicitly does NOT do

- `await` coroutine implementation (→ v4.30.0)
- Agent dispatch wiring (`_emit_agent_wrap`) (→ v4.30.0)
- Optimizer non-convergence ICE (→ v4.30.0)
- Self-hosted dead block elim with `clean_phis_in_block` (→ v4.30.0)
- Stale emitter carry-forwards (i64*, void()*, list bitcast) (→ v4.30.0)
- SPEC update, Spanish README sync (→ v4.31.0)
- User-Agent string bump (→ v4.31.0)
- Dead code removal (→ v4.31.0)

---

## Verification commands

```bash
# Phase 1 orphans
make build-rt
nm libmapanare_rt.a | grep -E "(mn_db_|mn_html_)" | head
python3 -m pytest tests/runtime/test_db_smoke.py -v
python3 -m pytest tests/runtime/test_html_smoke.py -v
diff <(grep -E "\.c$" Makefile | sort) <(ls runtime/native/*.c | xargs -n1 basename | sort)

# Phase 2 honesty
git grep "extern.*Python" mapanare/  # (depends on Path A vs B)
git grep "pytest.mark.xfail" tests/conftest.py | wc -l  # should drop dramatically
python3 -m mapanare --no-check tests/golden/06_struct.mn 2>&1 | grep -c WARNING  # 1

# Phase 3 gates
bash scripts/verify_fixed_point.sh; echo $?  # 0 if fixed point holds
# (intentionally break and rerun: must be non-zero)
git grep -l "raise NotImplementedError" mapanare/ runtime/ | grep -v tests/  # 0 results

# Full validation
.\dev.ps1
```

---

## Definition of done

- All 17 exit criteria check YES
- CI fails red on a deliberately-broken fixed-point branch
- `extern "Python"` is either real or absent — no silent xfail
- Orphaned runtime files are gone (linked or deleted)
- `docs/roadmap/v4/v4.29.0/SESSION_REPORT.md` written
- VERSION bumped to `4.29.0` only after all checks pass
