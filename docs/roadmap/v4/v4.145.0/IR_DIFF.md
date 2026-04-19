# v4.145.0 IR Diff — `area()` and `make_shape()`

## Summary

The PLAN hypothesized that Mapanare emits cascaded `icmp eq`/`br i1`
chains for `match` while Rust emits a single `switch`. **This was
wrong.** The v4.34.0 decision-tree compiler already emits `switch i64`
for flat enum matches.

The actual gap: after LLVM -O2 inlines both functions into `main()`,
**Rust has ONE switch; Mapanare has TWO.** Rust's LLVM fuses `make_shape`
and `area` into a single dispatch because the enum never materializes as
an intermediate aggregate. Mapanare's emitter constructs a `{i64, i64, i64}`
aggregate via `insertvalue` chains, merges them through a PHI of
aggregates, then `extractvalue`s the tag and switches again. LLVM cannot
fold `extractvalue` through a PHI of aggregates.

## Mapanare `main()` loop — post-`opt -O2` (two switches)

```llvm
while_body1:
  %i = phi i64 [ 0, %pre_entry ], [ %i.26, %area.exit ]
  %total = phi i64 [ 0, %pre_entry ], [ %i.20, %area.exit ]
  %trunc = trunc i64 %i to i32
  %rem = urem i32 %trunc, 6
  switch i32 %rem, label %if_merge14.i [          ; ← SWITCH 1 (make_shape)
    i32 0, label %if_then0.i
    i32 1, label %if_then3.i
    i32 2, label %if_then6.i
    i32 3, label %make_shape.exit
    i32 4, label %if_then12.i
  ]

; ... each arm builds {i64, i64, i64} via insertvalue ...

make_shape.exit:
  %common.ret.op.i = phi { i64, i64, i64 } [ ... ] ; ← AGGREGATE PHI
  %s.fca.0.extract.i = extractvalue { i64, i64, i64 } %common.ret.op.i, 0
  %s.fca.1.extract.i = extractvalue { i64, i64, i64 } %common.ret.op.i, 1
  %s.fca.2.extract.i = extractvalue { i64, i64, i64 } %common.ret.op.i, 2
  switch i64 %s.fca.0.extract.i, label %area.exit [ ; ← SWITCH 2 (area) REDUNDANT
    i64 0, label %match_arm1.i
    i64 1, label %match_arm2.i
    i64 2, label %match_arm3.i
    i64 5, label %match_arm6.i
    i64 4, label %match_arm5.i
  ]

match_arm1.i:                                       ; Circle: r*r*3
  %i.11.i = mul nsw i64 %s.fca.1.extract.i, %s.fca.1.extract.i
  %i.16.i = mul nsw i64 %i.11.i, 3
  br label %area.exit

; ... more arms ...

area.exit:
  %result = phi i64 [ %i.16.i, %match_arm1.i ], ...
  %i.20 = add nsw i64 %result, %total
  %i.26 = add nuw nsw i64 %i, 1
  %exitcond = icmp eq i64 %i.26, 100000
  br i1 %exitcond, label %while_exit2, label %while_body1
```

## Rust `main()` loop — post-`rustc -O` (one switch)

```llvm
bb11:
  %iter = phi i64 [ 0, %start ], [ %_38.0, %area.exit ]
  %total = phi i64 [ 0, %start ], [ %9, %area.exit ]
  %_38.0 = add nuw nsw i64 %iter, 1
  %_2.i = urem i64 %iter, 6
  switch i64 %_2.i, label %bb2.i5 [               ; ← SINGLE SWITCH (fused)
    i64 0, label %bb7.i
    i64 1, label %bb6.i10
    i64 2, label %bb5.i8
    i64 3, label %area.exit
    i64 4, label %bb3.i
  ]

bb7.i:                                              ; Circle: r*3*r
  %_4.i = urem i64 %iter, 50
  %r = add nuw nsw i64 %_4.i, 1
  %mul1 = mul nuw nsw i64 %r, 3
  %mul2 = mul nuw nsw i64 %mul1, %r                ; r*3*r via lea
  br label %area.exit

; ... more arms, each computes area directly ...

area.exit:
  %result = phi i64 [ %mul2, %bb7.i ], ...
  %9 = add i64 %total, %result
  %exitcond = icmp eq i64 %_38.0, 100000
  br i1 %exitcond, label %bb12, label %bb11
```

## Key differences

| Aspect | Mapanare -O2 | Rust -O |
|---|---|---|
| Switch count in hot loop | **2** (make_shape + area) | **1** (fused) |
| Enum materialized as aggregate | Yes — `{i64,i64,i64}` via `insertvalue`, merged in PHI | No — fields flow as separate scalars |
| Tag extraction | `extractvalue` on aggregate PHI (LLVM can't fold) | No extraction needed — tag is the switch discriminant |
| Payload extraction | `extractvalue` on aggregate PHI per arm | Direct scalar from switch arm |
| Division by 2 | `sdiv i64 %x, 2` | `lshr i64 %x, 1` (shift, `nuw nsw` proves non-negative) |
| Arithmetic flags | `nsw` only | `nuw nsw` (enables more opts) |

## Root cause

LLVM's `InstCombine` can fold `extractvalue (insertvalue ..., val, idx), idx → val`,
but NOT `extractvalue (PHI (insertvalue ...), (insertvalue ...)), idx` — it does not
distribute `extractvalue` into PHI arms. When `make_shape` returns an aggregate
and `area` extracts its tag, the PHI blocks the fold, keeping both switches alive.

Rust avoids this because `rustc` generates separate scalar flows that LLVM's
SROA + mem2reg decompose into scalar PHIs. The Mapanare emitter builds
aggregates that survive inlining as aggregate PHIs.
