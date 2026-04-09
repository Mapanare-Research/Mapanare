# Mapanare v3.9.1 — CI Green + Test Infrastructure

> Fix all CI failures. Generate missing golden reference files.
> Update stale CI comments. Clean up untracked test artifacts.
> Zero tolerance for red CI — this is the gate to v4.0.

**Status:** COMPLETE
**Estimated scope:** Small (1 session)
**Breaking:** No

---

## Why This Version Exists

v3.9.0 shipped with CI potentially red. The `ci` job runs `pytest tests/ -v`
which hits test files that segfault or skip on missing native libraries.
The self-hosted CI job says "25/25" golden but we have 31. Reference `.ref.ll`
files only exist for tests 1–15. This version fixes all of it.

---

## Phase 1: Fix CI Test Suite

### 1.1 — Fix ctypes segfault in io_bridge.py [DONE]

`runtime/io_bridge.py` loads `libmapanare_io.so` via `ctypes.CDLL` at import
time. If the `.so` is corrupt or incompatible, this segfaults the entire Python
process (uncatchable by try/except). Same issue in `native_bridge.py`.

**Fix:** Added `_probe_library()` function that test-loads the library in a
subprocess before the main process calls `ctypes.CDLL`. If the probe crashes,
the library is skipped gracefully. Applied to both `io_bridge.py` and
`native_bridge.py`.

### 1.2 — Update CI workflow [DONE]

- Updated "25/25" comment to "31/31" in `.github/workflows/ci.yml`
- `ir_doctor.py golden` uses `glob("*.mn")` — auto-detects all tests

### 1.3 — Run CI locally and verify green [DONE]

- `pytest tests/ -v`: **4479 passed, 89 skipped, 0 failures**
- `black --check .`: clean
- `ruff check .`: clean
- `mypy mapanare/ runtime/`: clean
- WASM emission: both examples pass
- C runtime: 52/52 tests pass

---

## Phase 2: Golden Test Reference Files

### 2.1 — Generate `.ref.ll` for tests 16–31 [DONE]

`python3 scripts/test_native.py --bless` generated `.ref.ll` for all 31 tests.

### 2.2 — Clean up untracked `.ll` artifacts [DONE]

- Removed 6 stray `.ll` build artifacts from git tracking
  (`01_hello.ll`, `10_result.ll`, `11_closure.ll`, `12_while.ll`,
   `14_nested_struct.ll`, `26_generics.ll`)
- Added `.gitignore` rule: `tests/golden/*.ll` with `!tests/golden/*.ref.ll`

---

## Phase 3: CI Workflow Cleanup [DONE]

- CI golden test count updated to 31/31
- WASM emission passes on all examples
- All linters green

---

## Exit Criteria

- [x] `pytest tests/ -v` passes (no segfaults, no unexpected failures)
- [x] All CI jobs green locally (linters + tests + WASM + C runtime)
- [x] `.ref.ll` files exist for all 31 golden tests
- [x] Untracked `.ll` files resolved (gitignored + removed from tracking)
