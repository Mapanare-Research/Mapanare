# Mapanare v3.7.0 — Cross-Module Types + Robust Compilation

> Fix imported function return types. Make the compiler robust on large inputs.
> Unlock full stdlib testing from native .mn programs.
> Track progress in this file.

**Status:** PLANNED
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No

---

## The Goal

v3.6.0 reached fixed point (stage3 == stage4), 35/35 stdlib, 25/25 golden,
41 native test assertions, and WASM for-loops. But cross-module return type
inference is broken — functions imported from stdlib return `i64` instead of
their declared type. This blocks native testing of text, time, crypto, and
most stdlib modules.

v3.7.0 fixes the type system for imported functions, hardens the compiler
against stack overflow on large inputs, and adds `./mnc run` for quick
compile-and-execute.

---

## Inherited State (from v3.6.0)

| Component | Status |
|-----------|--------|
| Self-hosted compiler | 25/25 golden, fixed point (stage3 == stage4) |
| Seed binary | v3.6.0 |
| Bootstrap | `bash scripts/build_from_seed.sh --verify` passes |
| Stdlib compiled | 35/35 modules |
| Native tests | 41 assertions: math 12, json 6, fs 6, string_utils 17 |
| CLI | `./mnc`, `./mnc test`, `./mnc build`, `./mnc version` |
| WASM | for-loops work, 180/180 tests |
| CI | 2,517 passed, lint/mypy clean |
| Demos | 3 programs compile+link+run natively |

---

## Phase 1: Cross-Module Return Type Inference

### 1.1 The bug

When module A imports module B, functions from B are lowered with correct
parameter types but their **return types default to `mir_unknown()` (i64)**.

Example: `stdlib/text.mn` exports `pub fn repeat(s: String, n: Int) -> String`.
When `test_text.mn` imports it via `usa stdlib::text`, the lowerer registers
`repeat` with return type `unknown` instead of `string`.

**Root cause:** `register_definition` in `lower.mn` stores return types in
`lambda_vars` using `"__ret__" + fn_name` entries. But imported function
definitions from `resolve_imports` go through the same path. The return type
is resolved via `resolve_return_type_checked(st, fd.return_type)`, which
should work — but the type expression might not resolve correctly for
imported functions if the enum/struct types aren't registered yet.

### 1.2 Investigation plan

1. Compile `test_text.mn` and trace the return type of `repeat`:
   - Check what `resolve_return_type_checked` returns for `repeat`'s type annotation
   - Check what's stored in `lambda_vars` for `"__ret__repeat"`
   - Check what `lower_call_by_name` resolves when calling `repeat(...)`

2. Use Culebra to compare the IR:
   ```bash
   # Compile text.mn standalone
   ./mnc stdlib/text.mn > /tmp/text_only.ll
   # Compile test_text.mn (with import)
   ./mnc tests/native/test_text.mn > /tmp/test_text.ll
   # Compare
   culebra diff /tmp/text_only.ll /tmp/test_text.ll
   culebra trace /tmp/test_text.ll --function main --var '%t9'
   ```

3. The fix will likely be in one of:
   - `register_definition` — ensuring imported fn return types are resolved correctly
   - `lower_call_by_name` — ensuring the lambda_vars lookup finds imported fn return types
   - `resolve_imports` — ensuring type definitions are imported before function definitions

**Files:** `mapanare/self/lower.mn`, `mapanare/self/main.mn`

**Test:** `test_text.mn` and `test_time.mn` compile and run natively.

### 1.3 Expected impact

Once fixed, all stdlib functions with simple return types (String, Int, Bool,
List, Map) will be callable from other modules with correct types. This
unblocks:
- `test_text.mn` — repeat, pad_left, reverse, count_char, is_blank
- `test_time.mn` — format_duration, is_leap_year, days_in_month
- `test_csv.mn`, `test_crypto.mn` — encoding/decoding roundtrips

---

## Phase 2: Stack Robustness

### 2.1 The problem

The compiler segfaults on `mnc_all.mn` (13K lines) without `ulimit -s unlimited`.
The 64MB stack flag (`-Wl,-z,stacksize=67108864`) is ignored on WSL Linux.

### 2.2 Fix options

A. **Iterative if-else chains** — the parser and lowerer use deep recursion
   for `else if` chains. Convert to iterative processing.
B. **Reduce per-frame size** — LowerState is copied on every function call.
   Use references or reduce struct size.
C. **Runtime stack check** — detect stack depth and bail with error instead
   of segfault.

**Recommended:** Option A for the lowerer (iterative else-if), Option C as a
safety net.

**Files:** `mapanare/self/lower.mn` (lower_if / lower_else_clause)

---

## Phase 3: `./mnc run`

Add `run` subcommand — compile, link, and execute in one step:
```bash
./mnc run program.mn           # compile + link + run
./mnc run program.mn -- arg1   # pass args to program
```

Like `test` but without PASS/FAIL reporting.

**Files:** `mapanare/self/main.mn`

---

## Phase 4: Culebra Stage2 Audit

Run Culebra diagnostics on the current stage2 IR and fix findings:
```bash
culebra scan /tmp/stage2.ll --severity critical
culebra field-index-audit /tmp/stage2.ll
culebra triage /tmp/stage2.ll --brief
culebra health /tmp/stage2.ll
```

Fix any `field-index-always-zero`, `return-type-divergence`, or
`option-type-pun-zeroinit` findings.

---

## Phase 5: Native Test Expansion

With cross-module types fixed, write native tests for:
- `stdlib/text.mn` — repeat, pad_left, pad_right, reverse, count_char, is_blank
- `stdlib/time.mn` — format_duration, is_leap_year, days_in_month
- `stdlib/encoding/csv.mn` — parse_line, format_line roundtrips
- `stdlib/log.mn` — format_log_entry, log level names

Target: 80+ native assertions across 8+ modules.

---

## Success Criteria

- [ ] Cross-module return types resolve correctly for all stdlib modules
- [ ] Compiler handles 13K+ line files without stack overflow (no ulimit needed)
- [ ] `./mnc run` works
- [ ] Culebra stage2 audit: 0 critical findings
- [ ] 80+ native test assertions across 8+ modules
- [ ] Fixed point maintained (stage3 == stage4)
- [ ] CI green (2,500+ tests)

---

## Non-Goals

- New language features
- Package manager / dependency resolution
- IDE integration / LSP
- Self-hosting without the C runtime
