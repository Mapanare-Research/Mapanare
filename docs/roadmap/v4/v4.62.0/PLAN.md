# Mapanare v4.62.0 — DWARF Design + Infrastructure

> **Arc 7 release 1.** Design-heavy release. No user-visible DWARF
> emission yet — but the foundation all subsequent DWARF releases
> build on. Produces DESIGN.md, adds `Span` threading through MIR,
> and adds the `_emit_debug_metadata` infrastructure in the emitter.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.61.0 (arc 6 panel PASS)
**Delta review:** No (no new syntax; design + infrastructure)
**Full panel:** No (v4.66.0)
**Estimated work:** 2 sprints (design is the hard part)
**Theme:** Read the LLVM DWARF spec. Decide how Mapanare's MIR carries source-position info. Lay the groundwork for v4.63.0-v4.65.0's real DWARF emission.

---

## Why arc 7 is four releases

DWARF is not a small feature. The LLVM DWARF spec alone runs to ~200 pages. The `!DI*` metadata graph has ~30 node kinds. Getting `llvm-dwarfdump --verify` to pass requires every edge in the graph to be well-formed, and the pass-pipeline ordering matters (some DWARF-emitting transformations must run before or after specific optimizations).

Splitting into 4 releases:
- **v4.62.0**: design + infrastructure (no user-visible DWARF)
- **v4.63.0**: `DICompileUnit` + `DISubprogram` (the skeleton — function boundaries)
- **v4.64.0**: line metadata on every instruction (`!dbg` attachments — step-through debugging works)
- **v4.65.0**: `DILocalVariable` + `llvm.dbg.declare`/`value` (variable inspection in gdb)

Each release delivers a verifiable slice. `llvm-dwarfdump --verify` is the exit gate at every step.

---

## Scope — v4.62.0 specifically

### The DESIGN.md

`docs/roadmap/v4/v4.62.0/DESIGN.md` — this is the main deliverable. It should cover:

1. **LLVM DWARF primer.** A ~500 word summary of the relevant metadata types:
   - `!DICompileUnit`, `!DIFile`
   - `!DISubprogram`
   - `!DISubroutineType`, `!DIBasicType`, `!DICompositeType`, `!DIDerivedType`
   - `!DILocation`
   - `!DILocalVariable`
   - `llvm.dbg.declare`, `llvm.dbg.value`
   - Link to the LangRef sections.

2. **Mapanare's current state.** Does MIR carry source positions? Audit `mapanare/mir.py`:
   - `Instruction` has a `span: Span`? If yes, check every `_lower_*` method sets it
   - `BasicBlock` has source info? Usually only the first instruction's span is used
   - `Function` has source info? The function header's span

3. **The design decision: how do we represent debug info through the pipeline?** Options:
   - **Option A**: Debug info flows through MIR as a separate graph. The emitter reads MIR + debug graph and produces both LLVM IR and `!DI*` metadata.
   - **Option B**: Debug info is attached to MIR nodes directly (e.g., `Instruction.debug_info: Optional[DebugMetadata]`). The emitter threads it through.
   - **Option C**: Debug info is recomputed from `Span` at emission time by looking up file + line directly.

   Pick one. **Recommendation: Option C.** Spans already exist. The emitter owns the file table. Recomputing at emission time keeps MIR small and doesn't require a new graph type. The cost is a small lookup per instruction.

4. **Pass pipeline placement.** Where do DWARF metadata nodes get emitted?
   - `DICompileUnit` / `DIFile`: once per module at `emit_llvm_text.py` module top
   - `DISubprogram`: once per function, as the function is being emitted
   - `DILocation`: once per source position, cached by `(file, line, col)` tuple
   - `DILocalVariable`: at let binding / parameter emission
   - `llvm.dbg.declare`: after alloca emission
   - `llvm.dbg.value`: at SSA value update points

5. **Versioning and flags.** DWARF has a version number (we'll emit DWARFv5). The `-g` flag gates emission. The `_resolve_debug` helper from v4.29.0 (currently prints "debug info deferred to v5.x") gets rewritten to pass through.

6. **Risk register.** Known hard problems:
   - `mem2reg` and other SSA transformations drop `llvm.dbg.declare` unless `llvm.dbg.value` is also emitted. Must emit both.
   - Inlining destroys source locations unless `!DILocation` has `inlinedAt` metadata. v4.62.0-v4.65.0 are MVP — don't tackle inlining-debug until v5.x.
   - Tail-call optimization can lose debug info. Mapanare doesn't use TCO currently; flag if it's added.

7. **Verification plan.** At each release in the arc, `llvm-dwarfdump --verify` on a representative golden must pass. Plus a gdb smoke test (v4.65.0).

8. **Rejected options.** What we considered and rejected:
   - Source maps (JavaScript-style) — rejected; not a DWARF replacement
   - DWARF via llvmlite — rejected; llvmlite was deleted in v4.59.0
   - Skip DWARF, emit `.map` files — rejected; gdb doesn't read them

### Infrastructure additions

- [ ] `mapanare/mir.py` — verify `Span` propagation through every MIR instruction. Add tests for span preservation through optimization passes.
- [ ] `mapanare/emit_llvm_text.py` — new helper `_emit_debug_metadata(key, shape)` that knows how to emit `!<n> = !{...}` metadata with a counter. No actual DWARF yet.
- [ ] `mapanare/emit_llvm_text.py` — `_debug_enabled` flag that gates metadata emission.
- [ ] `scripts/check_dwarf.sh` — new script, runs `llvm-dwarfdump --verify` on a `-g` build of `tests/golden/01_hello.mn`. At v4.62.0 this passes trivially (nothing to verify).

---

## Phase 0 — Study

- [ ] Read LLVM DWARF documentation end-to-end: https://llvm.org/docs/SourceLevelDebugging.html
- [ ] Read Clang's debug info emission code (selected paths): `clang/lib/CodeGen/CGDebugInfo.cpp`
- [ ] Run `clang -g -S -emit-llvm hello.c -o hello.ll` and read the generated `!DI*` metadata to internalize the shape

## Phase 1 — Write DESIGN.md

- [ ] `docs/roadmap/v4/v4.62.0/DESIGN.md` — written per the scope above
- [ ] Informal review by Rattler (LLVM lens) before any code ships

## Phase 2 — Span audit

- [ ] `mapanare/mir.py` — verify every MIR instruction has a `span` field and it's populated during lowering
- [ ] Audit `mapanare/lower.py` — every `_lower_*` method that creates an instruction must thread the source span through
- [ ] Fix any gaps: instructions with `span = None` or default span
- [ ] `tests/semantic/test_mir_span_preservation.py` — for each golden, verify every MIR instruction has a non-None span

## Phase 3 — Emitter infrastructure

- [ ] `mapanare/emit_llvm_text.py` `LLVMTextEmitter`:
  - `self._debug_enabled: bool` — set from `-g` flag
  - `self._debug_metadata_counter: int` — for `!N` IDs
  - `self._debug_file_table: dict[Path, int]` — cache file IDs
  - `self._debug_location_table: dict[tuple[int, int], int]` — cache locations
  - `_alloc_metadata_id() -> int` — returns next free ID
  - `_emit_debug_metadata(content) -> str` — returns `!<id>` reference
- [ ] Module emission: if `_debug_enabled`, the module is suffixed with a metadata section. Empty at v4.62.0; filled in v4.63.0+.

## Phase 4 — Flag wiring

- [ ] `mapanare/cli.py` `_resolve_debug` helper — rewritten:
  - v4.29.0 version: prints "DWARF deferred to v5.x"
  - v4.62.0 version: returns `True` if `-g` passed, `False` otherwise. No more deferral warning.
- [ ] `_compile_to_llvm_ir` takes a `debug: bool` parameter and passes it to the emitter.

## Phase 5 — `check_dwarf.sh`

- [ ] `scripts/check_dwarf.sh` — new script:
  ```bash
  set -euo pipefail
  python -m mapanare emit-llvm -g tests/golden/01_hello.mn -o /tmp/hello.ll
  llvm-as /tmp/hello.ll -o /tmp/hello.bc
  clang /tmp/hello.bc -o /tmp/hello
  llvm-dwarfdump --verify /tmp/hello > /tmp/dwarf_verify.log
  if grep -q "error:" /tmp/dwarf_verify.log; then
      echo "DWARF verification failed:"
      cat /tmp/dwarf_verify.log
      exit 1
  fi
  ```
- [ ] At v4.62.0: `-g` doesn't emit any DWARF metadata yet (the emitter infrastructure is empty). `llvm-dwarfdump --verify` should pass trivially.
- [ ] CI step (conditionally — only runs if `llvm-dwarfdump` is in the CI environment)

## Phase 6 — Tests

- [ ] `tests/llvm/test_dwarf_infrastructure.py`:
  - `test_debug_flag_enables_emission` — `-g` flag sets `_debug_enabled`
  - `test_emit_debug_metadata_returns_id` — infrastructure smoke test
  - `test_file_table_deduplication` — requesting the same file twice returns the same ID
  - `test_location_table_deduplication`
  - `test_empty_dwarf_emission_passes_verify` — the degenerate case

## Phase 7 — LOW sweep

2 items.

## Phase 8 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.62.0
- [ ] `CHANGELOG.md [4.62.0]` — DWARF design + infrastructure
- [ ] SESSION_REPORT

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | DESIGN.md written with all 8 sections | file exists |
| 2 | Rattler informal review sign-off | review notes in SESSION_REPORT |
| 3 | Every MIR instruction has a non-None span | `test_mir_span_preservation.py` |
| 4 | Emitter infrastructure helpers exist | grep `_emit_debug_metadata` |
| 5 | `_debug_enabled` flag wired through CLI | `-g` flag works without error |
| 6 | `_resolve_debug` no longer prints deferral warning | stderr check |
| 7 | `scripts/check_dwarf.sh` exists | file exists |
| 8 | `check_dwarf.sh` passes on `01_hello.mn` (empty DWARF) | script exits 0 |
| 9 | Infrastructure unit tests pass | `test_dwarf_infrastructure.py` |
| 10 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 11 | Self-hosted mirror compiles (no MIR shape change) | `test_native.py --stage1` |
| 12 | Standard closeout clean | CI |

---

## What v4.62.0 does NOT do

- **Emit any actual DWARF metadata** — v4.63.0
- **Emit `DICompileUnit`** — v4.63.0
- **Line-info attachments** — v4.64.0
- **Variable debug info** — v4.65.0
- **gdb backtraces** — v4.65.0

---

## Reference

- LLVM Source Level Debugging — https://llvm.org/docs/SourceLevelDebugging.html
- LLVM LangRef §Metadata — https://llvm.org/docs/LangRef.html#metadata
- DWARF v5 spec — https://dwarfstd.org/doc/DWARF5.pdf
- Clang's `CGDebugInfo.cpp` (reference implementation) — `clang/lib/CodeGen/CGDebugInfo.cpp`

---

## After v4.62.0

v4.63.0 emits the first real DWARF metadata: `!DICompileUnit`, `!DIFile`, `!DISubprogram` for every function. `llvm-dwarfdump` on a `-g` build will show function names with file+line info.
