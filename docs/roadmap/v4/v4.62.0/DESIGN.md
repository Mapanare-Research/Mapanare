# DWARF Debug Info Design — v4.62.0

> This document describes how Mapanare emits DWARF debug information
> through the LLVM IR text emitter. It covers the LLVM metadata types,
> the pipeline design, and the decisions made for v4.62.0-v4.65.0.

---

## 1. LLVM DWARF Primer

LLVM encodes debug information as metadata nodes in the IR. The key types:

- **`!DICompileUnit`** — one per module. Names the source file, language,
  producer, DWARF version. Referenced by `!llvm.dbg.cu`.
- **`!DIFile`** — source file descriptor (filename + directory).
- **`!DISubprogram`** — one per function. Links function name, file, line,
  scope, and type signature. Attached to `define` via `!dbg !N`.
- **`!DISubroutineType`** — function type for `DISubprogram`. Lists
  parameter and return `DIBasicType`/`DICompositeType` references.
- **`!DIBasicType`** — primitive types (i64, f64, i1). Names the type and
  its size in bits.
- **`!DICompositeType`** — structs and enums. Contains `!DIDerivedType`
  members for struct fields or `!DIEnumerator` for enum variants.
- **`!DIDerivedType`** — struct member (name, offset, size, underlying type).
- **`!DILocation`** — source position (line, column, scope). Attached to
  instructions via `!dbg !N`.
- **`!DILocalVariable`** — local variable or parameter. Links name, scope,
  file, line, and type.
- **`llvm.dbg.declare`** — intrinsic that binds a `DILocalVariable` to an
  alloca (address-taken variable).
- **`llvm.dbg.value`** — intrinsic that binds a `DILocalVariable` to an
  SSA value (after mem2reg).

References:
- [LLVM Source Level Debugging](https://llvm.org/docs/SourceLevelDebugging.html)
- [LLVM LangRef §Metadata](https://llvm.org/docs/LangRef.html#metadata)

---

## 2. Mapanare's Current State

### MIR source positions

`mapanare/mir.py` defines `SourceSpan` (line, column, end_line, end_column,
file). The `Instruction` base class has `span: SourceSpan | None`.
`MIRFunction` has `span: SourceSpan | None` for the function header.

### Lowering

`mapanare/lower.py` threads AST `Span` objects through to MIR `SourceSpan`
during lowering. The AST `Span` has `line`, `column`, `end_line`,
`end_column`. The lowerer converts these when creating MIR instructions.

### Current emitter behavior

`emit_llvm_text.py` accepts `debug: bool = False` in the constructor but
does nothing with it. The v4.29.0 `_resolve_debug` helper prints a
deferral warning when `-g` is passed.

---

## 3. Design Decision: Option C — Recompute from Span at Emission Time

**Chosen: Option C.** Debug info is recomputed from `SourceSpan` at
emission time.

### Rationale

- **No new graph type.** MIR stays small. The emitter already knows the
  source file (from the module name / compile arguments).
- **Spans already exist.** The lowerer already threads AST spans to MIR
  instructions. No new lowering work needed.
- **Single responsibility.** The emitter owns the metadata numbering,
  file table, and location cache. All DWARF decisions live in one place.
- **Cost is acceptable.** One dict lookup per instruction to check the
  location cache. For a 3,000-instruction module this is ~0.1ms.

### What Option C requires

1. The emitter maintains a `_debug_file_table: dict[str, int]` mapping
   source paths to `!DIFile` metadata IDs.
2. The emitter maintains a `_debug_location_cache: dict[tuple[int,int,int], int]`
   mapping `(file_id, line, col)` to `!DILocation` metadata IDs.
3. At function emission, the emitter looks up the function's `SourceSpan`
   to create `!DISubprogram`.
4. At instruction emission, the emitter appends `, !dbg !N` using the
   instruction's `SourceSpan` and the location cache.

### Rejected alternatives

- **Option A** (separate debug graph): Over-engineered for a language
  that doesn't have inlining or link-time optimization.
- **Option B** (debug info on MIR nodes): Pollutes MIR with DWARF-specific
  data. MIR should remain backend-agnostic.

---

## 4. Pass Pipeline Placement

| Metadata | When emitted | Where in emitter |
|----------|-------------|-----------------|
| `!DICompileUnit` + `!DIFile` | Once per module | `_emit_module_header` |
| `!DISubprogram` | Once per function | `_emit_function_header` |
| `!DISubroutineType` | Once per function type | Cached by signature |
| `!DIBasicType` | Once per primitive | Cached by type name |
| `!DILocation` | Once per unique (file, line, col) | Location cache |
| `!DILocalVariable` | At let binding / parameter | `_emit_alloca` |
| `llvm.dbg.declare` | After alloca emission | `_emit_alloca` |
| `llvm.dbg.value` | At SSA value update | `_emit_instruction` |

All metadata nodes are collected during emission and written as a block
at the end of the module (after all function definitions).

---

## 5. Versioning and Flags

- **DWARF version:** DWARFv5 (`!{i32 7, !"Dwarf Version", i32 5}`).
  DWARFv5 is the LLVM default and has better variant-part support for
  Mapanare enums.
- **Debug Info Version:** LLVM's current metadata version
  (`!{i32 2, !"Debug Info Version", i32 3}`).
- **Language code:** `DW_LANG_C99` (0x000c). gdb treats function names
  as opaque — no demangling surprises. Mapanare doesn't need
  language-specific gdb pretty-printers (yet).
- **Producer:** `"Mapanare <version>"`.
- **Flag gating:** The `-g` / `--debug` CLI flag sets
  `LLVMTextEmitter(debug=True)`. When `debug=False` (default), zero
  metadata is emitted — no performance or binary-size cost.

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `mem2reg` drops `llvm.dbg.declare` without matching `llvm.dbg.value` | High | Debug vars lost | Emit both declare and value |
| Inlining destroys source locations without `inlinedAt` | Medium | Wrong stack frames | MVP doesn't inline; flag if TCO added |
| `opt -O2` strips debug metadata | Low | Lost debug info | Use `-O0` for debug builds; clang preserves at `-Og` |
| Large metadata section bloats IR | Low | Slow compile | Metadata is ~5% of IR size in Clang; acceptable |
| `llvm-dwarfdump --verify` fails on partial metadata | Medium | CI gate red | Each arc release adds a complete slice; verify at each step |

---

## 7. Verification Plan

Each release in Arc 7 must pass:

1. **`llvm-as`** — IR is syntactically valid (already a gate).
2. **`llvm-dwarfdump --verify`** — DWARF metadata is structurally valid.
3. **`objdump --dwarf=info`** — sanity check that the expected DIEs appear.
4. **gdb smoke test** (v4.65.0 only) — `break main`, `run`, `bt` shows
   Mapanare function names and source lines.

The verification script is `scripts/check_dwarf.sh`.

### Per-release verification milestones

| Release | What `llvm-dwarfdump` should show |
|---------|----------------------------------|
| v4.62.0 | Empty (no metadata yet) — passes trivially |
| v4.63.0 | `DW_TAG_compile_unit` + `DW_TAG_subprogram` per function |
| v4.64.0 | Line info on every instruction (`.debug_line` populated) |
| v4.65.0 | `DW_TAG_variable` for locals + gdb `info locals` works |

---

## 8. Rejected Options

| Option | Why rejected |
|--------|-------------|
| **Source maps (JS-style `.map` files)** | gdb doesn't read them. DWARF is the standard for native debuggers. |
| **DWARF via llvmlite** | llvmlite was deleted in v4.59.0 (A4). |
| **Skip DWARF, emit `.debug_pubnames` only** | Insufficient for step-through debugging. |
| **DWARFv4** | DWARFv5 is LLVM's default. Better variant-part support for enums. No reason to target an older version. |
| **`DW_LANG_Rust`** | Would trigger Rust-specific demangling in gdb. `DW_LANG_C99` is safer. |
| **Custom `DW_LANG_lo_user+1`** | Requires custom gdb plugin. Not worth the maintenance burden for MVP. |
