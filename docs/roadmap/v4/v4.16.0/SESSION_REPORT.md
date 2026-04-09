# v4.16.0 Session Report — 2026-04-09

## Completed
- Constant propagation pass added to `mir_opt.mn`
- Integer constants propagated through Copy and BinOp instructions
- Fixed MIRModule constructor to include `consts` field from v4.15.0
- 41/41 golden, 11/11 stage2

## Deferred
- Dead block elimination: BFS misses while/for header blocks referenced by lowerer patterns
- Copy propagation: deferred to avoid cascading complexity
- IR size measurement: deferred (baseline infrastructure not yet built)

## Issues Found
- Dead block elim BFS doesn't follow all block references from the self-hosted lowerer's while/for patterns, causing dangling labels
- PHI node filtering in emitter caused crashes (EmitState field access corruption) — reverted
- Constant propagation on non-integer types caused crashes — restricted to TK_INT() only

## Next Session Should Start With
- v4.17.0: Fixed-Point Bootstrap
