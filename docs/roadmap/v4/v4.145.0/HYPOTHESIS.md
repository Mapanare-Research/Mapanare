# E1 Hypothesis

**Claim:** After inlining, Mapanare's loop has two switches (one per
function) because the intermediate `{i64, i64, i64}` enum aggregate
survives as a PHI-of-aggregates that LLVM cannot decompose. Rust's
loop has one switch because the enum never materializes as an
aggregate — fields flow as separate scalars.

**Fix:** Unify return points for functions returning inline enums.
Instead of multiple `ret {i64,i64,i64} %val` instructions (one per
arm), store to a function-level result alloca and branch to a single
return block. After inlining, SROA decomposes the alloca into three
i64 allocas → mem2reg creates three scalar PHIs (tag, slot1, slot2) →
InstCombine folds `extractvalue(insertvalue(PHI), 0)` → `tag_PHI` →
SimplifyCFG merges the two switches into one.

**Expected delta:** Eliminating the redundant switch + aggregate
construction/destruction should save ~40–60% of loop time, bringing
`enum_match` from ~4.7× to ~2–3× of Rust.

**IR before (Mapanare -O2, after inlining):**
```llvm
; make_shape's arms build {i64,i64,i64} via insertvalue
if_then0.i:
  %ei.22 = insertvalue {i64, i64, i64} undef, i64 0, 0
  %ei.23 = insertvalue {i64, i64, i64} %ei.22, i64 %val, 1
  %ei.24 = insertvalue {i64, i64, i64} %ei.23, i64 0, 2
  br label %make_shape.exit

make_shape.exit:
  %agg = phi {i64,i64,i64} [%ei.24, %if_then0.i], ...  ; AGGREGATE PHI
  %tag = extractvalue {i64,i64,i64} %agg, 0              ; can't fold through PHI
  switch i64 %tag, label %area.exit [...]                 ; REDUNDANT SWITCH
```

**IR after (expected, with unified-return fix):**
```llvm
; make_shape's arms store to alloca per-field
if_then0.i:
  store i64 0, ptr %ret.tag       ; tag
  store i64 %val, ptr %ret.f1     ; field 1
  store i64 0, ptr %ret.f2        ; field 2
  br label %make_shape.exit

make_shape.exit:
  %tag = phi i64 [0, %if_then0.i], [1, %if_then3.i], ...  ; SCALAR PHI of constants
  ; → SimplifyCFG merges with the first switch → ONE switch total
```

**Files to edit:** `mapanare/emit_llvm_text.py` — `_emit_fn` (add
unified-ret alloca), `_do_ret` (store + branch instead of ret).
**Estimated diff:** ~30 logic lines.
