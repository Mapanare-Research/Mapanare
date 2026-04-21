# Mapanare v4.64.0 — DWARF Line Metadata on Instructions

> **Arc 7 release 3.** Every emitted LLVM instruction gets a `!dbg !<N>`
> attachment pointing at a `!DILocation`. Stepping through a `-g` build
> in gdb now shows the correct source line. `addr2line` on a compiled
> binary returns the right `.mn` file and line number.

**Status:** DONE (2026-04-12)
**Session log:** Line metadata implemented via _L() hook. ret void patching and _is_term() fixed for !dbg suffixes. 28 DWARF tests pass. llvm-dwarfdump --verify clean.
**Breaking:** No
**Prerequisite:** v4.63.0 (compile unit + subprograms exist)
**Delta review:** No
**Full panel:** No (v4.66.0)
**Estimated work:** 1.5 sprints
**Theme:** Line-accurate debug info. Source-level stepping works.

---

## Scope

### Metadata emitted

- `!DILocation(line: N, column: M, scope: !<subprogram>)` — one per unique (line, col, scope) tuple, cached
- Every LLVM instruction that came from user source code gets `!dbg !<N>` appended
- Synthesized instructions (drop glue, prologue/epilogue) get the nearest source span or the function header's span

### `addr2line` round-trip test

The load-bearing verification: compile a golden with `-g`, run the binary, record a program counter value via `backtrace_symbols` or similar, feed to `addr2line`, verify the returned source location matches the known `.mn` source line.

---

## Phase 1 — Location metadata builder

- [ ] `mapanare/emit_llvm_text.py` `_emit_location(span: Span, scope: str) -> str`:
  ```python
  def _emit_location(self, span: Span, scope: str) -> str:
      key = (span.line, span.column, scope)
      if key in self._location_cache:
          return self._location_cache[key]
      md_id = self._alloc_metadata_id()
      content = f'!DILocation(line: {span.line}, column: {span.column}, scope: {scope})'
      self._debug_metadata.append((md_id, content, 'distinct' if False else ''))
      ref = f'!{md_id}'
      self._location_cache[key] = ref
      return ref
  ```

## Phase 2 — Instruction attachment

- [ ] Every `_emit_instruction` method in the emitter currently produces a string like:
  ```
  %tmp = add i64 %a, %b
  ```
  v4.64.0 appends `, !dbg !<N>`:
  ```
  %tmp = add i64 %a, %b, !dbg !42
  ```
- [ ] Audit every instruction-emitting method — there are many. Add a helper:
  ```python
  def _dbg_suffix(self, span: Span) -> str:
      if not self._debug_enabled:
          return ""
      return f", !dbg {self._emit_location(span, self._current_subprogram)}"
  ```
- [ ] Every instruction emit call ends with `+ self._dbg_suffix(instr.span)`.
- [ ] `self._current_subprogram` is set when entering a function, cleared when leaving.

## Phase 3 — Synthesized instruction handling

Some instructions don't map to user source:
- **Prologue allocas** (stack slots for parameters) — get the function header's span
- **Drop glue calls** (emitted on function exit) — get the return statement's span, or the function closing-brace span
- **Cleanup blocks from early returns** — get the `return` statement's span
- **PHI nodes** — get the block's entry span (or the branch that led to the PHI)

Rule: **every instruction must have a non-None span at emit time.** If a synthesized instruction doesn't have one, the lowerer has a bug — fix it, don't paper over it.

- [ ] Audit the lowerer for synthesized instructions without spans. Add spans where missing.
- [ ] `tests/llvm/test_dwarf_all_instructions_attached.py` — regression test: compile a golden with `-g`, parse the IR, verify every instruction has a `!dbg` attachment. Zero exceptions.

## Phase 4 — Verification

- [ ] `scripts/check_dwarf.sh` extended:
  ```bash
  # ... existing check_dwarf setup ...

  # Line-accuracy test: compile 01_hello.mn with -g, get addr2line info
  for line_num in 1 5 10; do
      addr=$(objdump -d /tmp/hello | grep -A1 "call.*mn_print" | head -1 | awk '{print $1}')
      source=$(addr2line -e /tmp/hello $addr)
      expected="01_hello.mn:${line_num}"
      # ... match
  done
  ```

  (This is simplified — the actual check walks specific call sites and verifies they resolve to the right source line.)

- [ ] New test: `tests/llvm/test_dwarf_line_info.py`:
  - `test_every_instruction_has_dbg_attachment` — grep IR
  - `test_addr2line_returns_correct_source` — compile, addr2line, assert
  - `test_step_through_in_gdb_hits_right_lines` — if gdb is in the CI environment, script a step-through; otherwise skip honestly

## Phase 5 — Self-hosted mirror

- [ ] `mapanare/self/emit_llvm.mn` — mirror the `_dbg_suffix` helper and the `_emit_location` cache
- [ ] Byte-identity held when `-g` is enabled

## Phase 6 — LOW sweep

2 items.

## Phase 7 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.64.0
- [ ] `CHANGELOG.md [4.64.0]` — Line-accurate DWARF
- [ ] SESSION_REPORT

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `!DILocation` cached by (line, column, scope) | unit test |
| 2 | Every source-origin instruction has `!dbg` attachment | `test_every_instruction_has_dbg_attachment` |
| 3 | Synthesized instructions have spans (no None) | `test_all_instructions_have_spans` |
| 4 | `llvm-dwarfdump --verify` passes | `check_dwarf.sh` clean |
| 5 | `addr2line` on compiled binary returns correct `.mn` source location | `test_addr2line_returns_correct_source` |
| 6 | gdb step-through hits the right lines (if gdb available) | `test_step_through_in_gdb_hits_right_lines` |
| 7 | Prologue allocas get function header span | visual inspection |
| 8 | Drop-glue emissions get return statement span | visual inspection |
| 9 | PHI nodes get block entry span | visual inspection |
| 10 | Self-hosted mirror emits same attachments | byte compare |
| 11 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 12 | Standard closeout clean | CI |

---

## What v4.64.0 does NOT do

- **Variables** — v4.65.0
- **Stepping into functions** — partially works via subprograms + locations; full inlining support is v5.x
- **`llvm.dbg.declare` / `llvm.dbg.value`** — v4.65.0

---

## Reference

- LLVM LangRef `DILocation` — https://llvm.org/docs/LangRef.html#dilocation
- GDB `set debuginfod enabled on` (for remote DWARF fetching — not relevant but worth noting)

---

## After v4.64.0

v4.65.0 adds variable debug info: `DILocalVariable` + `llvm.dbg.declare` / `llvm.dbg.value`. gdb can now inspect local variables by name.
