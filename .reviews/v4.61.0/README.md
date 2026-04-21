# v4.61.0 Panel Summary — Arc 6: Deprecation + Deletion

> 7-reviewer panel, 2026-04-12. Grades v4.57.0-v4.60.0.

## Verdict: PASS (8.71/10)

Zero NEEDS WORK. Arc 6 closes. Two 5-cycle carry-forwards (A3, A4) definitively
closed. ~1,820 lines removed from the package, llvmlite dependency dropped.
The tree is the cleanest it's been since the recovery arc.

## Reviewer Table

| # | Reviewer | Lens | Grade | Verdict |
|---|----------|------|-------|---------|
| 1 | Viper | Memory safety / type soundness | 9/10 | PASS WITH NOTES |
| 2 | Anaconda | Toolchain (PRIMARY) | 9/10 | PASS WITH NOTES |
| 3 | Coral | Language design | 9/10 | PASS WITH NOTES |
| 4 | Rattler | LLVM | 8/10 | PASS WITH NOTES |
| 5 | Cobra | Testing | 8/10 | PASS WITH NOTES |
| 6 | Boa | Documentation | 8/10 | PASS WITH NOTES |
| 7 | Mamba | Carry-forward | 8/10 | PASS WITH NOTES |

**Aggregate: 8.71/10** (61/7)

## Consensus findings

### Verified closures (unanimous)
- **A3 CLOSED**: `emit_python_mir.py` deleted (1,236 lines), `cmd_compile`/`cmd_repl` removed, 6 regression gate tests
- **A4 CLOSED**: `jit.py` deleted (285 lines), `cmd_jit`/`--release` removed, llvmlite dropped, 5 regression gate tests
- **v4.60.0 reconciliation verified**: 8 past-due items re-tracked, CLOSED evidence valid

### Action items (for Arc 7)

1. **cmd_build clang pre-check** (Rattler, Anaconda): Add `shutil.which("clang")` check before subprocess call in `cmd_build`. User currently gets raw `FileNotFoundError`.
2. **E2E test coverage gap** (Cobra, Viper): Deleted e2e tests covered language features that still exist on LLVM backend. No LLVM-equivalent e2e replacements added. Should be tracked.
3. **24 dormant HAS_LLVMLITE guards** (Viper, Coral, Mamba): Add a CARRY_FORWARD entry for migrating these to clang-based compilation.
4. **CLAUDE.md self-hosted line counts** (Boa): v4.56.0 action item still open — `semantic.mn` and `main.mn` line counts stale in the module table.
5. **v4.56.0 const action items** (Mamba): Items 2+3 (const type-mismatch test, Float/String fold test) have no ledger row. Add to CARRY_FORWARD.
6. **Bootstrap test clang skip guards** (Rattler): `test_stage1_compile.py` tests hard-fail without clang/llvm-as instead of skipping.

### What worked well
- The deprecate-then-delete pattern for the Python emitter (v4.57.0 warn, v4.58.0 delete)
- Thorough migration guides with FAQ and timeline
- Regression gate tests that prevent re-introduction of deleted code
- The v4.60.0 dead-code audit was genuinely clean (Vulture found 0 real dead code)
- CARRY_FORWARD reconciliation was honest — past-due items re-tracked, not hidden

### What needs improvement
- E2E test coverage needs rebuilding on the LLVM backend
- clang dependency should be programmatically checked, not just documented
- Module line counts in CLAUDE.md have been stale since v4.56.0 (2 panel cycles)
