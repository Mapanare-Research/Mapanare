# Mapanare v4.2.0 — Clean House (Emitter Consolidation)

> One emitter. One pipeline. Zero dead code.
> You can't fix drop glue properly when you have 3 competing emitters.

**Status:** TODO
**Breaking:** Yes (removes `--no-mir`, `--emitter llvmlite` flags)
**Prerequisite:** v4.1.0

---

## Why This Is First

The codebase has 3 LLVM emitters (~8,800 lines) but only `emit_llvm_text.py`
(~3,800 lines) is the default and has correct drop glue. The other two have
known bugs:

- `emit_llvm.py` (AST, llvmlite): Frees ALL tracked strings without comparing
  to return value. Use-after-free risk.
- `emit_llvm_mir.py` (MIR, llvmlite): 36 `_coerce_arg` call sites doing raw
  `alloca+store+load` memory reinterpretation. Missing drop glue for lists,
  maps, signals, streams. Global mutable state breaks cross-compilation.
- `emit_c.mn` (self-hosted, C output): References `MIRTypeInfo`, `MIRBlock`,
  integer opcodes — none exist in current `mir.mn`. Dead since v3.0.0.

Every line of dead emitter code makes it harder to fix memory bugs in v4.3.0
and thread safety in v4.4.0.

---

## Phase 1: Delete Legacy LLVM Emitters

### 1A. Remove `emit_llvm.py` (AST-based, llvmlite)

- [ ] Remove `from mapanare.emit_llvm import LLVMEmitter` from `cli.py`
- [ ] Remove `_compile_multi_module_llvm` function (cli.py ~line 242) or port
      it to use `emit_llvm_text.py` pipeline
- [ ] Remove `--no-mir` CLI flag and all code paths gated on it
- [ ] Delete `mapanare/emit_llvm.py` (2,883 lines)
- [ ] Remove any tests that import `LLVMEmitter` directly — migrate to text emitter
- [ ] Run full test suite, fix any imports

**Files:** `mapanare/emit_llvm.py` (DELETE), `mapanare/cli.py`

### 1B. Remove `emit_llvm_mir.py` (MIR-based, llvmlite)

- [ ] Remove `--emitter llvmlite` CLI flag and deprecation warning
- [ ] Remove `from mapanare.emit_llvm_mir import LLVMMIREmitter` from `cli.py`
- [ ] Delete `mapanare/emit_llvm_mir.py` (~5,000 lines)
- [ ] Remove any tests that import `LLVMMIREmitter` directly
- [ ] Remove `_coerce_arg` and `_coerce_args` (these ONLY exist in the deleted file)
- [ ] Remove llvmlite from `requirements.txt` / `pyproject.toml` if no other
      module imports it (check `jit.py` — may still need it)
- [ ] Run full test suite

**Files:** `mapanare/emit_llvm_mir.py` (DELETE), `mapanare/cli.py`, `pyproject.toml`

### 1C. Remove `emit_python.py` (AST-based Python transpiler)

- [ ] Audit all test files that import `PythonEmitter`
- [ ] Migrate each test to use `PythonMIREmitter` from `emit_python_mir.py`
- [ ] Delete `mapanare/emit_python.py` (~47KB)
- [ ] Update `cli.py` `_compile_to_python` to only use MIR path
- [ ] Run full test suite

**Files:** `mapanare/emit_python.py` (DELETE), `mapanare/cli.py`, `tests/**/*.py`

---

## Phase 2: Delete Broken Self-Hosted Emitter

### 2A. Remove `emit_c.mn`

- [ ] Delete `mapanare/self/emit_c.mn` (770 lines)
- [ ] Remove any imports/references to `emit_c` in `mapanare/self/main.mn`
- [ ] Rebuild self-hosted compiler: `bash scripts/rebuild.sh`
- [ ] Verify golden tests: `/golden`
- [ ] Verify fixed point maintained

**Files:** `mapanare/self/emit_c.mn` (DELETE), `mapanare/self/main.mn`

---

## Phase 3: Clean Up CLI

### 3A. Remove dead flags

- [ ] Remove `--no-mir` flag from argument parser
- [ ] Remove `--emitter` flag (only one emitter now)
- [ ] Remove any `if use_mir:` / `if emitter == "llvmlite":` branches
- [ ] Update CLI help text
- [ ] Update `docs/SPEC.md` if it references emitter selection

### 3B. Port multi-module compilation

- [ ] If `_compile_multi_module_llvm` was not ported in Phase 1A, port it now:
  - Read each module's AST
  - Lower each to MIR
  - Emit each via `emit_llvm_text.py`
  - Link the resulting `.ll` files
- [ ] Test with `mapanare build --multi` or however multi-module is invoked

**Files:** `mapanare/cli.py`, `mapanare/multi_module.py`

---

## Phase 4: Verification

### 4A. Test suite

- [ ] `.\dev.ps1 validate` — full validation passes
- [ ] `pytest tests/ -v -n auto` — all tests pass (some will be deleted/migrated)
- [ ] `/golden` — 40/40 golden tests pass
- [ ] `/rebuild` — self-hosted compiler builds
- [ ] `/stage2` — stage2 validation passes

### 4B. Measure the cleanup

- [ ] Count lines deleted: target ~8,500 lines removed
- [ ] Verify no imports of deleted modules remain: `grep -r "emit_llvm\b" mapanare/`
- [ ] Verify llvmlite not required (unless jit.py needs it)
- [ ] `git diff --stat` to confirm scope

---

## Exit Criteria

| Check | Required |
|-------|----------|
| `emit_llvm.py` deleted | YES |
| `emit_llvm_mir.py` deleted | YES |
| `emit_python.py` deleted | YES |
| `emit_c.mn` deleted | YES |
| `_coerce_arg` gone (was only in `emit_llvm_mir.py`) | YES |
| `--no-mir` flag removed | YES |
| `--emitter` flag removed | YES |
| `_compile_multi_module_llvm` ported or removed | YES |
| Full test suite passes | YES |
| 40/40 golden tests pass | YES |
| Self-hosted rebuild + fixed point maintained | YES |
| ~8,500 lines net deleted | YES |
