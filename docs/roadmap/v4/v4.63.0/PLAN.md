# Mapanare v4.63.0 — DWARF `DICompileUnit` + `DISubprogram`

> **Arc 7 release 2.** First real DWARF emission: module-level
> compile-unit and file metadata, plus a `DISubprogram` for every
> function. `llvm-dwarfdump` will now show function boundaries and
> source-file associations.

**Status:** DONE (2026-04-12)
**Session log:** All phases executed. DICompileUnit + DISubprogram + basic types emitted. llvm-dwarfdump --verify passes. 22 tests.
**Decisions taken:** DW_LANG_C99, FullDebug emissionKind, placeholder ptr type for non-primitive types.
**Breaking:** No (additive)
**Prerequisite:** v4.62.0 (infrastructure)
**Delta review:** No
**Full panel:** No (v4.66.0)
**Estimated work:** 1.5 sprints
**Theme:** `objdump --dwarf=info` on a Mapanare binary now shows the source file and every function name with line numbers.

---

## Scope

### Metadata nodes emitted

- **`!DICompileUnit`** — one per module, at the module top.
- **`!DIFile`** — one per source file touched. Module source file is the primary; imports add more.
- **`!DISubroutineType`** — one per unique function signature. Used as `type:` on `DISubprogram`.
- **`!DIBasicType`** — for primitive types (`Int`, `Float`, `Bool`, `String`). Used as parameter/return type refs.
- **`!DISubprogram`** — one per function. Fields: name, linkageName, scope (the CompileUnit), file, line, type, isLocal, isDefinition, spFlags.

### Not yet emitted (v4.64.0+)

- `!DILocation` line attachments on instructions
- `!DILocalVariable` for locals
- `llvm.dbg.*` intrinsic calls
- `!DICompositeType` for struct/enum types
- `!DIDerivedType` for pointers and typedefs

---

## Phase 1 — Builtin type metadata

- [ ] `mapanare/emit_llvm_text.py` — `_emit_basic_type(ty: MIRType) -> str`:
  - `Int` → `!DIBasicType(name: "Int", size: 64, encoding: DW_ATE_signed)`
  - `Float` → `!DIBasicType(name: "Float", size: 64, encoding: DW_ATE_float)`
  - `Bool` → `!DIBasicType(name: "Bool", size: 8, encoding: DW_ATE_boolean)`
  - `String` → `!DICompositeType(tag: DW_TAG_structure_type, name: "String", ...)` — a struct with `{ptr, i64}` shape; defer the full struct type to v4.65.0, emit a placeholder for now
- [ ] Cache by type kind in `self._debug_type_table`.
- [ ] Return the `!N` reference.

## Phase 2 — File table

- [ ] `_emit_file(path: Path) -> str` — emits `!DIFile(filename: "hello.mn", directory: "/path/to/src")`. Cached by path.
- [ ] The emitter needs access to the source file's absolute path — pass through `_compile_to_llvm_ir`.

## Phase 3 — Compile unit

- [ ] `_emit_compile_unit(main_file: str) -> str`:
  ```
  !0 = distinct !DICompileUnit(
      language: DW_LANG_Mapanare,  // or DW_LANG_C_plus_plus_14 as fallback; DWARF doesn't have DW_LANG_Mapanare
      file: !1,
      producer: "mapanare 4.63.0",
      isOptimized: true,
      runtimeVersion: 0,
      emissionKind: FullDebug,
      splitDebugInlining: false,
  )
  ```
- [ ] **Language code choice:** DWARF doesn't have a `DW_LANG_Mapanare` constant. Options:
  - `DW_LANG_C_plus_plus_14` — gdb recognizes, mangles names C++-style (bad)
  - `DW_LANG_C99` — simpler, gdb treats names as-is (good for Mapanare's naming conventions)
  - `DW_LANG_Rust` — gdb knows it, but may invoke Rust-specific demangling
  - Custom `DW_LANG_lo_user + 1` — gdb warns but continues
- [ ] **Decision: `DW_LANG_C99`**. gdb treats function names as opaque, which matches what we want.

## Phase 4 — Subroutine types

- [ ] `_emit_subroutine_type(param_types, return_type) -> str`:
  ```
  !5 = !DISubroutineType(types: !{!4, !2, !2})
  // where !4 is the return type, !2 is each parameter type
  ```
- [ ] Cache by (return_type, param_types) tuple.

## Phase 5 — DISubprogram per function

- [ ] `_emit_subprogram(fn: MIRFunction) -> str`:
  ```
  !10 = distinct !DISubprogram(
      name: "my_function",
      linkageName: "my_function",
      scope: !0,  // the compile unit
      file: !1,
      line: 42,
      type: !5,  // the subroutine type
      isLocal: false,
      isDefinition: true,
      scopeLine: 42,
      spFlags: DISPFlagDefinition,
      unit: !0,
  )
  ```
- [ ] Emit alongside the function header. LLVM IR syntax:
  ```
  define i64 @my_function(i64 %a, i64 %b) !dbg !10 {
      ...
  }
  ```

## Phase 6 — Module-level metadata

- [ ] At module emit time, produce the full metadata section:
  ```
  !llvm.dbg.cu = !{!0}
  !llvm.module.flags = !{!100, !101, !102}

  !100 = !{i32 2, !"Dwarf Version", i32 5}
  !101 = !{i32 2, !"Debug Info Version", i32 3}
  !102 = !{i32 1, !"wchar_size", i32 4}

  !0 = distinct !DICompileUnit(...)
  !1 = !DIFile(...)
  !2 = !DIBasicType(...)  // Int
  !3 = !DIBasicType(...)  // Float
  !4 = !DIBasicType(...)  // Bool
  !5 = !DISubroutineType(...)
  !10 = distinct !DISubprogram(name: "main", ...)
  !11 = distinct !DISubprogram(name: "foo", ...)
  ...
  ```

## Phase 7 — Verification

- [ ] `scripts/check_dwarf.sh` already exists from v4.62.0. At v4.63.0 it runs against a real `-g` build with `DICompileUnit` + `DISubprogram` emission. Run it:
  ```
  $ bash scripts/check_dwarf.sh
  ...
  Verifying /tmp/hello.bc
  Success: no errors found
  ```
- [ ] New test: `tests/llvm/test_dwarf_compile_unit.py`:
  - `test_compile_unit_emitted` — compile a golden with `-g`, grep for `!DICompileUnit`
  - `test_every_function_has_subprogram` — compile, parse DWARF, verify one `DW_TAG_subprogram` per function in the source
  - `test_file_metadata_absolute_path` — verify the file path is absolute
  - `test_llvm_dwarfdump_verify_passes` — `llvm-dwarfdump --verify` returns 0

## Phase 8 — Self-hosted mirror

- [ ] `mapanare/self/emit_llvm.mn` — mirror the debug metadata emission helpers
- [ ] Byte-identity with Python side — if both emit debug info, the output should match

## Phase 9 — LOW sweep

2 items.

## Phase 10 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.63.0
- [ ] `CHANGELOG.md [4.63.0]` — DICompileUnit + DISubprogram emission
- [ ] SESSION_REPORT

---

## Exit criteria (14 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `!DICompileUnit` emitted at module top | grep IR |
| 2 | `!DIFile` for every source file | same |
| 3 | `!DIBasicType` for Int/Float/Bool/String | same |
| 4 | `!DISubroutineType` cached by signature | unit test |
| 5 | `!DISubprogram` for every function | grep IR |
| 6 | Functions link their subprogram via `!dbg !N` | grep IR |
| 7 | Module flags include Dwarf Version 5 | grep IR |
| 8 | `llvm-dwarfdump --verify` passes | `check_dwarf.sh` clean |
| 9 | `objdump --dwarf=info` shows function names | manual check |
| 10 | `DW_LANG_C99` used as language code | grep IR |
| 11 | Self-hosted mirror emits same structure | byte compare |
| 12 | Fixed-point diff still 0 (debug metadata doesn't affect functional lowering) | verify script |
| 13 | `test_dwarf_compile_unit.py` all cases pass | pytest |
| 14 | Standard closeout clean | CI |

---

## What v4.63.0 does NOT do

- **Line info on instructions** — v4.64.0
- **Variables** — v4.65.0
- **Struct / enum types** — partial (placeholder for String); full in v4.65.0
- **Inlined function metadata** — v5.x
- **Debug info for anonymous functions / closures** — v4.64.0 or v4.65.0

---

## Reference

- LLVM LangRef `DICompileUnit` — https://llvm.org/docs/LangRef.html#dicompileunit
- LLVM LangRef `DISubprogram` — https://llvm.org/docs/LangRef.html#disubprogram
- DWARF v5 §3.3 "Subroutine and Entry Point Entries"

---

## After v4.63.0

v4.64.0 adds `!DILocation` attachments on every instruction so stepping through in gdb actually shows the right source line.
