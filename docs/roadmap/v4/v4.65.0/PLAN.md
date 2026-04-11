# Mapanare v4.65.0 — DWARF `DILocalVariable` + `llvm.dbg.declare`/`value`

> **Arc 7 release 4.** The final DWARF feature for v4.x: local
> variable debug info. After v4.65.0, a user can compile a Mapanare
> program with `-g`, open it in gdb, and inspect local variables by
> name at a breakpoint. The "real gdb experience" is unlocked.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.64.0
**Delta review:** No
**Full panel:** No (v4.66.0)
**Estimated work:** 2 sprints (the hardest DWARF work)
**Theme:** `p x` in gdb returns the user's local variable, at the right stack frame.

---

## Scope

### Metadata emitted

- `!DILocalVariable(name: "x", scope: !<subprogram>, file: !<file>, line: N, type: !<type>)` — one per local
- `!DICompositeType` for struct types — new in v4.65.0 (v4.63.0 used placeholders)
- `!DIDerivedType` for pointers and typedefs
- `call void @llvm.dbg.declare(metadata ptr %alloca, metadata !<var>, metadata !DIExpression())` — at the alloca site
- `call void @llvm.dbg.value(metadata i64 %value, metadata !<var>, metadata !DIExpression())` — at SSA update sites

### The load-bearing test

```bash
$ cat > /tmp/demo.mn << EOF
fn main() {
    let x: Int = 42
    let name: String = "hello"
    print(x)
    print(name)
}
EOF
$ mapanare build -g /tmp/demo.mn -o /tmp/demo
$ gdb /tmp/demo
(gdb) break main
(gdb) run
(gdb) p x
$1 = 42
(gdb) p name
$2 = "hello"
(gdb) next
(gdb) ...
```

If this works end-to-end, arc 7 is done.

---

## Phase 1 — Struct/enum type metadata

v4.63.0 emitted placeholder types for `String` and left user struct / enum types entirely unmapped. v4.65.0 fixes this.

### Phase 1.1: Struct types

- [ ] `_emit_struct_type(ty: MIRType) -> str`:
  ```
  !20 = !DICompositeType(
      tag: DW_TAG_structure_type,
      name: "Point",
      file: !1,
      line: 10,
      size: 128,
      elements: !21,
  )
  !21 = !{!22, !23}
  !22 = !DIDerivedType(tag: DW_TAG_member, name: "x", file: !1, line: 11, baseType: !3 /* Float */, size: 64, offset: 0)
  !23 = !DIDerivedType(tag: DW_TAG_member, name: "y", file: !1, line: 12, baseType: !3, size: 64, offset: 64)
  ```
- [ ] Cache by struct type name
- [ ] Member types reference the v4.63.0 basic types

### Phase 1.2: Enum types

- [ ] Mapanare enums are tagged unions. DWARF has `DW_TAG_variant_part` in v5 for this, which gdb/lldb understand:
  ```
  !30 = !DICompositeType(
      tag: DW_TAG_structure_type,
      name: "Option<Int>",
      size: 128,
      elements: !31,
  )
  !31 = !{!32}
  !32 = !DICompositeType(
      tag: DW_TAG_variant_part,
      file: !1,
      line: 20,
      size: 128,
      elements: !33,
      discriminator: !<discriminator member>,
  )
  !33 = !{!34, !35}
  !34 = !DIDerivedType(tag: DW_TAG_member, name: "Some", ...)
  !35 = !DIDerivedType(tag: DW_TAG_member, name: "None", ...)
  ```
- [ ] **Decision:** full variant-part support is v5.x. For v4.65.0, emit enums as plain `DW_TAG_structure_type` with a discriminator field — gdb can display them, just not as "Some(42)" but as "{tag: 0, payload: 42}". Acceptable MVP.

### Phase 1.3: String type (upgrade from placeholder)

- [ ] `String` as `{ptr, i64}` struct — emit real `DICompositeType` with `data` and `len` members
- [ ] List, Map, etc. get similar treatment

---

## Phase 2 — DILocalVariable emission

- [ ] `_emit_local_variable(name: str, ty: MIRType, scope: str, span: Span) -> str`:
  ```
  !50 = !DILocalVariable(name: "x", arg: 0, scope: !10, file: !1, line: 5, type: !2)
  ```
- [ ] `arg: N` field: for function parameters, N is the 1-indexed parameter number. For locals, `arg: 0` (or omitted).
- [ ] Called from `_lower_let_def` and `_lower_fn_def` (for parameters)

---

## Phase 3 — `llvm.dbg.declare`

- [ ] After emitting an alloca:
  ```
  %x.addr = alloca i64, align 8
  call void @llvm.dbg.declare(metadata ptr %x.addr, metadata !50, metadata !DIExpression()), !dbg !<N>
  ```
- [ ] `llvm.dbg.declare` is an intrinsic the emitter registers at module declaration time:
  ```
  declare void @llvm.dbg.declare(metadata, metadata, metadata) #N
  ```

---

## Phase 4 — `llvm.dbg.value`

The harder part. After `mem2reg` runs (implicit via LLVM optimization), allocas become SSA values. Debug info survives only if `llvm.dbg.value` is emitted at every SSA update:

```
%x = add i64 %x, 1, !dbg !<N>
call void @llvm.dbg.value(metadata i64 %x, metadata !50, metadata !DIExpression()), !dbg !<N>
```

- [ ] Every time an SSA value is reassigned in a way that corresponds to a user-visible variable update, emit `llvm.dbg.value` right after.
- [ ] For pre-`mem2reg` allocas, `llvm.dbg.declare` alone is sufficient. For post-`mem2reg`, we need `llvm.dbg.value` too.
- [ ] **Pragmatic approach:** emit both forms. LLVM's optimizer will drop redundant ones. The extra emission cost is negligible.

---

## Phase 5 — Parameter debug info

- [ ] Function parameters are allocated stack slots in the prologue. At alloca time, emit `llvm.dbg.declare` for the parameter with `arg: N`.
- [ ] Parameter names come from the function signature (v4.33.0+ grammar guarantees named parameters).

---

## Phase 6 — Scope tracking

- [ ] Nested blocks (`if`, `for`, `match` arms) introduce lexical scopes. DWARF represents them as `!DILexicalBlock`:
  ```
  !60 = distinct !DILexicalBlock(scope: !10, file: !1, line: 5, column: 9)
  ```
- [ ] The emitter tracks a scope stack. Local variables introduced inside a block get that block's scope, not the function's scope.
- [ ] `_enter_block` / `_leave_block` push/pop the scope stack.

---

## Phase 7 — gdb integration test

- [ ] `scripts/check_dwarf.sh` extended with a gdb scripted session:
  ```bash
  cat > /tmp/gdbscript << 'EOF'
  break main
  run
  print x
  print name
  continue
  quit
  EOF

  gdb -batch -x /tmp/gdbscript /tmp/hello > /tmp/gdb_out.log 2>&1
  grep -q "\$1 = 42" /tmp/gdb_out.log || { echo "gdb didn't find x"; exit 1; }
  grep -q "\$2 = \"hello\"" /tmp/gdb_out.log || { echo "gdb didn't find name"; exit 1; }
  echo "DWARF gdb smoke test: PASS"
  ```
- [ ] Conditional on gdb availability — skip if CI doesn't have gdb.

---

## Phase 8 — Self-hosted mirror

- [ ] Self-hosted emitter gains the same debug-info emission paths
- [ ] Byte-identity held

---

## Phase 9 — Tests

- [ ] `tests/llvm/test_dwarf_variables.py`:
  - `test_int_local_emitted_as_dilocalvariable`
  - `test_string_local_emitted`
  - `test_struct_local_emitted`
  - `test_parameter_has_arg_index`
  - `test_nested_scope_variables`
  - `test_llvm_dbg_declare_after_alloca`
  - `test_llvm_dbg_value_after_ssa_update`
  - `test_gdb_print_local_variable` — skip if gdb absent

- [ ] `scripts/check_dwarf.sh` runs gdb smoke test — passes

## Phase 10 — LOW sweep

2 items.

## Phase 11 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.65.0
- [ ] `CHANGELOG.md [4.65.0]` — **DWARF complete for v4.x.** Users can debug Mapanare programs in gdb with variables, lines, function names.
- [ ] `.reviews/CARRY_FORWARD.md` — A2 (DWARF debug info) finally CLOSED, 8 cycles after first flagged
- [ ] SESSION_REPORT includes a celebratory note

---

## Exit criteria (16 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `DICompositeType` for user structs | grep IR |
| 2 | Enum type metadata (MVP — plain struct form) | grep |
| 3 | `String` upgraded from placeholder to real composite type | grep |
| 4 | `DILocalVariable` for every local variable | `test_int_local_emitted_as_dilocalvariable` |
| 5 | `DILocalVariable` with `arg: N` for parameters | `test_parameter_has_arg_index` |
| 6 | `llvm.dbg.declare` called after every alloca | `test_llvm_dbg_declare_after_alloca` |
| 7 | `llvm.dbg.value` emitted at SSA updates | `test_llvm_dbg_value_after_ssa_update` |
| 8 | `DILexicalBlock` for nested scopes | `test_nested_scope_variables` |
| 9 | `llvm-dwarfdump --verify` passes | `check_dwarf.sh` clean |
| 10 | gdb smoke test: `print x` returns correct value | `test_gdb_print_local_variable` (or manual if CI lacks gdb) |
| 11 | gdb smoke test: `print name` returns correct string | same |
| 12 | Stepping in gdb hits the right source lines | manual or scripted |
| 13 | Self-hosted mirror compiles same debug info | byte compare |
| 14 | A2 marked CLOSED in `CARRY_FORWARD.md` | ledger diff |
| 15 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 16 | Standard closeout clean | CI |

---

## What v4.65.0 does NOT do

- **Inlined function debug info** (`inlinedAt`) — v5.x
- **Optimized variable debug info** (when a variable is eliminated) — v5.x
- **Full enum variant-part support** — MVP only; gdb shows `{tag, payload}` not `Some(42)`
- **DWARF for closures** — tricky; v5.x
- **DWARF for generics monomorphized instances** — `DISubprogram` per instance; may already work, verify

---

## Reference

- LLVM LangRef `DILocalVariable`, `DICompositeType`, `DIVariant`, `llvm.dbg.declare`, `llvm.dbg.value`
- gdb DWARF support manual

---

## After v4.65.0

v4.66.0 is the **arc 7 panel release** — the seventh 5-minor cadence panel. DWARF work is done. A2 is closed. The next two arcs (8 and 9) are the coroutine foundation and completion.
