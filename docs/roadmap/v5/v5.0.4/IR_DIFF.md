# v5.0.4 IR_DIFF — ABI Classifier Impact on stage2.ll

## Representative function signatures: before → after

| Function | Return type | Size | v5.0.3 | v5.0.4 | Changed? |
|----------|------------|------|--------|--------|----------|
| `make_span` | `%struct.Span` ({i64,i64,i64,i64}) | 32B | by-value | **sret** | YES |
| `new_span` | `%struct.Span` | 32B | by-value | **sret** | YES |
| `new_block` | `%struct.Block` (unregistered) | 256B* | sret | sret | no |
| `make_named_type` | `%enum.TypeExpr` ({i64,ptr}) | 16B | register | register | no |
| `new_fn_entry` | `%struct.FnEntry` (registered) | 8B** | by-value | register | no |
| `lookup_struct_field_types` | `{ptr,i64,i64,i64,i64}` (List) | 40B | by-value | **sret** | YES |

\* Unregistered structs default to 256B in `struct_byte_size` (safe upper bound).
\** Internal compiler structs registered via `make_entry` store `%struct.Name`
as `llvm_type`, which `llvm_aggregate_size` miscounts as 8B. This is a
pre-existing limitation (same result under `is_byref_type_st`), not a
regression.

## Aggregate return type census

| Return type | Size | Count (v5.0.3) | Count (v5.0.4) | Classification |
|-------------|------|----------------|----------------|----------------|
| `{ptr, i64}` (String) | 16B | 147 by-value | 147 register | ≤16B → register ✓ |
| `{ptr, i64, i64, i64, i64}` (List) | 40B | 60 by-value | **0** (→ sret) | >16B → sret ✓ |
| `{i1, ptr}` (Option) | 16B | 35 by-value | 35 register | ≤16B → register ✓ |
| Named structs (various) | varies | 443 by-value | 406 by-value | 37 moved to sret |

## IR shape diff: `make_span` (representative sret change)

### Before (v5.0.3)
```llvm
define %struct.Span @make_span(i64 %line, i64 %column, i64 %end_line, i64 %end_column) nounwind willreturn {
entry:
  ; ... builds %struct.Span aggregate via insertvalue ...
  ret %struct.Span %result
}
; Caller:
  %span = call %struct.Span @make_span(i64 1, i64 0, i64 1, i64 10)
```

### After (v5.0.4)
```llvm
define void @make_span(ptr noalias sret(%struct.Span) %__sret__, i64 %line, i64 %column, i64 %end_line, i64 %end_column) nounwind willreturn {
entry:
  ; ... stores fields directly to %__sret__ pointer ...
  ret void
}
; Caller:
  %sret0 = alloca %struct.Span
  store %struct.Span zeroinitializer, ptr %sret0
  call void @make_span(ptr sret(%struct.Span) %sret0, i64 1, i64 0, i64 1, i64 10)
  %span = load %struct.Span, ptr %sret0
```

## Unchanged patterns (correctly preserved)

- `make_named_type` returns `%enum.TypeExpr` ({i64, ptr} = 16B) →
  stays register (≤16B on SysV) ✓
- `String` returns ({ptr, i64} = 16B) → stays register ✓
- All scalar returns (`i64`, `i1`, `ptr`) → unchanged ✓
- Argument passing → unchanged (still uses 64B `is_byref_type_st` threshold) ✓
