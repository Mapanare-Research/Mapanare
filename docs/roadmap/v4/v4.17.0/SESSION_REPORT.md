# v4.17.0 Session Report — 2026-04-09

## Completed
- Three-stage bootstrap: stage1→stage2→stage3 all produce valid LLVM IR
- mnc-stage2 (self-compiled binary) compiles the full 15,000+ line compiler
- Near fixed-point: 69 diff lines out of 111,246 (0.062%)
- Updated `scripts/verify_fixed_point.sh` with actual LLVM pipeline
- 41/41 golden, 11/11 stage2

## Fixed-Point Status
- **stage2.ll**: 111,246 lines (valid, produced by stage1)
- **stage3.ll**: 111,256 lines (valid, produced by stage2)
- **Diff**: 69 lines (0.062%) — all in PHI node codegen for unreachable match arms
- **Root cause**: match expressions where all arms terminate (return/break) generate different codegen between stages — stage2 uses PHI with zeroinitializer, stage3 uses dummy alloca+load

## Issues Found
- Stack size: `-Wl,-z,stacksize=67108864` ignored by linker on WSL. Fixed with `ulimit -s 65536`.
- `sed` main→mn_main rename breaks string constants containing "@main(". Fixed with Python regex.
- Stage2 exits with code 10 (semantic warnings) despite producing valid output. Script handles this.

## Next Session Should Start With
- v4.18.0: Tensors + @gpu
