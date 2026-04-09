# Mapanare v4.5.0 — Type System Tightening

> Silent type errors become loud compile errors.

**Status:** TODO
**Breaking:** Yes (programs that relied on UNKNOWN silently compiling will now fail)
**Prerequisite:** v4.4.0 (needs stable memory + concurrency foundation)

---

## The Core Problem

`TypeKind.UNKNOWN` is used as both "inference pending" and "inference failed."
When inference fails, the result flows through the type system as UNKNOWN, which
matches everything via `TypeInfo.matches()` and `TypeInfo.permissive_match()`.
This means wrong argument types, misspelled function names, and invalid
operations compile silently and crash at runtime.

~85 locations in `semantic.py` return `UNKNOWN_TYPE` as a fallback.

Additionally, the self-hosted compiler skips semantic analysis entirely and
never calls its MIR verifier.

---

## Phase 1: Split UNKNOWN in Python Compiler

### 1A. Add UNRESOLVED and ERROR to TypeKind

- [ ] In `mapanare/types.py`, add `TypeKind.UNRESOLVED` (replaces current UNKNOWN
      for "not yet inferred") and `TypeKind.ERROR` (inference failed — emit diagnostic)
- [ ] Keep `TypeKind.UNKNOWN` as deprecated alias for UNRESOLVED during migration
- [ ] Create `ERROR_TYPE = TypeInfo(kind=TypeKind.ERROR)` sentinel
- [ ] Update `TypeInfo.matches()`: ERROR matches nothing (forces error propagation)
- [ ] Update `TypeInfo.permissive_match()`: ERROR still matches nothing

### 1B. Migrate semantic.py

- [ ] Audit all ~85 locations that return `UNKNOWN_TYPE`
- [ ] For each, decide: is this "pending" (use UNRESOLVED) or "failed" (use ERROR + diagnostic)?
- [ ] Replace `UNKNOWN_TYPE` returns with the appropriate variant
- [ ] Where ERROR is returned, also call `self._error()` to emit a diagnostic

### 1C. Post-analysis validation pass

- [ ] After `SemanticChecker.check()` completes, walk all resolved types
- [ ] Any remaining UNRESOLVED type is an error: emit "could not infer type" diagnostic
- [ ] Any ERROR type that wasn't already reported: emit it now
- [ ] New test: program with misspelled function name — must produce compile error,
      not silent UNKNOWN

### 1D. Test

- [ ] Run full test suite — some tests may need updates if they relied on UNKNOWN passing
- [ ] Verify: `mapanare check bad_program.mn` produces useful error for type mismatch
- [ ] Count remaining UNKNOWN_TYPE references — target: 0

**Files:** `mapanare/types.py`, `mapanare/semantic.py`

---

## Phase 2: Wire Self-Hosted Semantic Analysis

### 2A. Call semantic analysis in compile()

- [ ] In `mapanare/self/main.mn`, modify `compile()` to call semantic analysis
      between parse and lower:
      ```
      let program = parse(source, filename)
      let errors = check_semantic(program)   // <-- ADD THIS
      if len(errors) > 0:
          // print errors and exit
      let mir_module = lower(program)
      ```
- [ ] Handle the error list: print each `SemanticError` with line/column info
- [ ] Exit with non-zero status if errors found

### 2B. Verify it catches real errors

- [ ] Write a test `.mn` file with a type error — verify mnc catches it
- [ ] Write a test `.mn` file with an undefined variable — verify mnc catches it
- [ ] Rebuild self-hosted: `bash scripts/rebuild.sh`
- [ ] Verify all golden tests still pass (they should — golden tests are correct programs)

**Files:** `mapanare/self/main.mn`, `mapanare/self/semantic.mn`

---

## Phase 3: Wire Self-Hosted MIR Verifier

### 3A. Call verify_module in compile()

- [ ] In `mapanare/self/main.mn`, after lowering, call `verify_module(mir_module)`
- [ ] The verifier checks: empty functions, unterminated blocks, terminators in
      middle of block, phi nodes after non-phi instructions
- [ ] Print any verification errors and exit non-zero

### 3B. Extend the verifier

- [ ] Add check: every `Branch` instruction's targets must exist as blocks
- [ ] Add check: every `Phi` instruction's sources must exist as predecessor blocks
- [ ] Add check: function return type matches `Return` instruction's value type

**Files:** `mapanare/self/main.mn`, `mapanare/self/lower.mn`

---

## Phase 4: Self-Hosted Diagnostics

### 4A. Emit diagnostics for unknown instructions

- [ ] In `emit_llvm.mn`, replace `return st` fallthrough in `emit_mir_by_kind`
      with an error print: `"ERROR: unknown instruction kind: <kind>"`
- [ ] Exit with error code after printing

### 4B. Emit diagnostics for unknown tokens

- [ ] In `parser.mn`, replace "skip unknown token" with error accumulation
- [ ] Track error count — if > 0, print all errors after parsing and exit

### 4C. Rebuild and verify

- [ ] `bash scripts/rebuild.sh`
- [ ] `/golden` — all pass
- [ ] `/stage2` — passes
- [ ] Feed a deliberately broken `.mn` file to mnc — verify it produces errors

**Files:** `mapanare/self/emit_llvm.mn`, `mapanare/self/parser.mn`

---

## Phase 5: Verification

- [ ] `.\dev.ps1 validate` — full validation
- [ ] `/golden` — 40/40
- [ ] `/rebuild` + `/stage2`
- [ ] Test: misspelled function → compile error (not silent success)
- [ ] Test: wrong arg type → compile error
- [ ] Test: broken `.mn` → mnc produces errors with line numbers
- [ ] Count remaining `UNKNOWN_TYPE` in codebase — target: 0

---

## Exit Criteria

| Check | Required |
|-------|----------|
| `TypeKind.UNRESOLVED` and `TypeKind.ERROR` exist | YES |
| UNKNOWN_TYPE references replaced (~85 locations) | YES |
| Post-analysis validation catches unresolved types | YES |
| Self-hosted `compile()` calls semantic analysis | YES |
| Self-hosted `compile()` calls MIR verifier | YES |
| Unknown instructions produce errors (not silent drop) | YES |
| Unknown tokens produce errors (not silent skip) | YES |
| Misspelled function → compile error (Python compiler) | YES |
| Wrong arg type → compile error (Python compiler) | YES |
| All 40 golden tests pass | YES |
| Self-hosted rebuild + fixed point maintained | YES |
