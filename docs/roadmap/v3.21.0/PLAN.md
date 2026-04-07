# Mapanare v3.21.0 — "Cascabel II" (DX Polish, Docs, Tests)

> Everything user-facing: error messages, documentation, test infrastructure,
> developer experience. Named after v3.13.0 "Cascabel" (memory safety) — this
> is the DX safety companion.

**Status:** PLANNED
**Estimated scope:** Small-Medium (1-2 sessions)
**Breaking:** No
**Prerequisite:** v3.20.0

---

## Documentation Fixes (5)

### 1. Dead `return "unreachable"` in tutorial
**File:** `docs/getting-started.md:236` | **Reporter:** Coral (M9)
Delete dead code after exhaustive match. Misleads beginners about control flow.

### 2. `for-python-devs.md` missing trait examples
**File:** `docs/for-python-devs.md:176` | **Reporter:** Boa (M3)
Add cross-link to cookbook recipe #13 or inline 5-line trait example.

### 3. JSON example bare `Object(obj)` without enum prefix
**File:** `docs/getting-started.md:584` | **Reporter:** Boa (M4)
Add `JsonValue_` prefix or document unqualified import mechanism.

### 4. Cookbook version `0.5.0`
**File:** `docs/cookbook.md:34` | **Reporter:** Boa (L10)
Update to current version.

### 5. Dead `len() < 0` in self-hosted main.mn
**File:** `mapanare/self/main.mn:520` | **Reporter:** Anaconda (I-3)
Change to `len(source) == 0` for proper file-not-found detection.

---

## DX Improvements (3)

### 6. REPL swallows exception types
**File:** `mapanare/cli.py:531` | **Reporter:** Boa (M1)
`print(f"runtime error ({type(exc).__name__}): {exc}")`

### 7. Test runner lacks colorized PASS/FAIL
**File:** `mapanare/test_runner.py:308-339` | **Reporter:** Boa (M2)
Import from `diagnostics.py` `_Colors`/`_NoColors`. Green PASS, red FAIL.

### 8. GPU kernel stubs -> gate with clear error
**File:** `mapanare/lower.py:204-280` | **Reporter:** Cobra (H2, 3rd version)
`raise NotImplementedError("GPU codegen not yet implemented. @cuda/@vulkan will be available in a future release.")`

---

## Test Infrastructure (2)

### 9. No native C tests for MnMap/MnSignal/MnStream/intern
**File:** `tests/native/test_c_runtime.c` | **Reporter:** Mamba (M3)
Add ~20 test functions: map create/insert/get/iterate/free, signal
create/set/subscribe/propagate/free, stream create/chain/collect/free,
intern insert/lookup/thread-safety.

### 10. WASM TODO stubs silent
**File:** `mapanare/emit_wasm.py:1188,1386,1413` | **Reporter:** Anaconda (I-4)
Emit `(unreachable)` WAT instruction alongside the comment. Log diagnostic warning.

---

## Verification

- [ ] All tutorial code samples compile end-to-end
- [ ] `mapanare test` shows colored PASS/FAIL output
- [ ] `@cuda fn ...` produces clear "not yet implemented" error
- [ ] 20+ new native C tests pass under ASan + TSan
- [ ] WASM programs with unhandled instructions trap at runtime
- [ ] `/golden` — all pass
