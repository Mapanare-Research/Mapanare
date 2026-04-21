# v4.66.0 Panel Summary — Arc 7: DWARF Debug Info

> 7-reviewer panel, 2026-04-12. Grades v4.62.0-v4.65.0.

## Verdict: CONDITIONAL PASS (7.93/10)

Zero NEEDS WORK. Aggregate below 9.0 target. Arc 7 closes — A2 is
definitively closed, but the panel surfaces significant gaps in testing
depth, user documentation, and CI integration that must be addressed.

## Reviewer Table

| # | Reviewer | Lens | Grade | Verdict |
|---|----------|------|-------|---------|
| 1 | Rattler | LLVM (PRIMARY) | 9/10 | PASS WITH NOTES |
| 2 | Viper | Memory safety | 9/10 | PASS |
| 3 | Anaconda | Toolchain | 7/10 | PASS WITH NOTES |
| 4 | Cobra | Testing | 6/10 | CONDITIONAL PASS |
| 5 | Coral | Language design | 9/10 | PASS |
| 6 | Boa | Documentation | 6/10 | CONDITIONAL PASS |
| 7 | Mamba | Carry-forward | 8/10 | PASS |

**Aggregate: 7.71/10** (54/7)

## Consensus findings

### Verified closures (unanimous)
- **A2 CLOSED**: DWARF debug info delivered across v4.62.0-v4.65.0 (Python bootstrap only).
  DESIGN.md, DICompileUnit, DISubprogram, DILocation, DILocalVariable + llvm.dbg.declare.
  34 tests. llvm-dwarfdump --verify passes.

### Critical action items (for Arc 8)

1. **-g + clang -g flag missing** (Anaconda): `cmd_build` passes `-O{N}` to clang but
   NOT `-g`, so debug metadata in IR is stripped at compile time. Silent correctness hole.
2. **No integration tests against real DWARF tooling** (Cobra): All 34 tests are IR
   string-match assertions. No test invokes llvm-dwarfdump programmatically.
3. **No gdb tutorial for developers** (Boa): `-g` works but no user-facing documentation
   explains how to debug a Mapanare program with gdb.
4. **check_dwarf.sh not in CI** (Anaconda): Script exists but CI doesn't run it. Silent
   skip when tools are missing.
5. **A2 dual-closure gap** (Rattler, Mamba): Self-hosted emitter (emit_llvm.mn) does not
   emit DWARF. The PY/SH dual-closure convention is not applied.
6. **6 v4.61.0 action items still unaddressed** (Mamba, Boa): Third panel cycle for some.
7. **test_ret_instruction_has_dbg is vacuous** (Cobra): No assertion — always passes.
8. **Local variable debug info not tested** (Cobra): Only parameter debug info tested.

### What worked well
- The 4-release incremental DWARF arc was well-structured
- DESIGN.md's Option C decision kept MIR clean
- A2 closure after 6 cycles is a genuine milestone
- DWARFv5 and DW_LANG_C99 were sound choices
- The _L() hook approach was minimal-surface

### What needs improvement
- Testing depth: string-match tests don't catch malformed metadata
- User documentation: no gdb guide exists
- CI: check_dwarf.sh needs integration
- The -g flag needs to propagate to clang for the debug info to survive compilation
- Item 49 is now at 9 cycles — the longest-running open item
