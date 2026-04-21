# Anaconda — Toolchain Review (v4.66.0)

Grade: 7/10
Verdict: PASS WITH NOTES

## Findings
1. **-g UX clean** — consistently wired across run, build, emit-llvm, emit-c.
2. **check_dwarf.sh silently exits on missing tools** — exit 0 when llvm-dwarfdump absent. Regressions go undetected.
3. **check_dwarf.sh not in CI** — llvm-18 is on the CI runner but no step calls the script.
4. **-g + clang -g flag missing** — cmd_build passes -O{N} but NOT -g to clang. Debug metadata in IR is stripped at compile time.
5. **-g + -O interaction undocumented**.
