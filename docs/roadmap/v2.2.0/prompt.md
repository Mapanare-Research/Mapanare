# v2.2.0 — Fixed Point — Continuation Prompt

> Continue the v2.2.0 execution in WSL. Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v2.2.0/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.

---

## Goal

Achieve fixed-point verification: **stage2 == stage3**. The self-hosted compiler
compiles itself identically across generations. Python is no longer needed.

---

## Current State (from previous sessions — 35 commits on `dev`)

### What's DONE

| Phase | Status | Detail |
|-------|--------|--------|
| 1. Opaque pointers | **Done** | `emit_llvm_text.py` fully migrated to `ptr` |
| 2. Stage2 parse errors | **Done** | 0 parse errors in 65K lines stage2 IR |
| 3. mnc-stage2 binary | **Done** | Compiles (clang -O1), links, runs |
| PHI predecessor fix | **Done** | `scripts/fix_stage2_phis.py` fixes all 18 PHI issues |
| Byref parameter passing | **Done** | sret+byref for EmitState, LowerState, MIRModule, etc. |
| List push temp+writeback | **Done** | Matches Python text emitter's pattern exactly |
| String constant `align 2` | **Done** | Fixes `mn_untag` off-by-1 for odd-address constants |
| `print` → `println` | **Done** | `emit_builtin_print` now calls `__mn_str_println` |

### What's WORKING in mnc-stage2

- **Source string passes correctly** from C wrapper: `SRC[0]=102` (f), `SLEN=24`
- **String constants at even addresses**: `align 2` on all `@str.N` globals
- **String comparison works**: `char_at(source, 0) == "f"` returns `EQ=1`
- **List push accumulates**: `LINES=58` (declarations) after emit loop
- **64K lines accumulated** in stage1 (mnc-stage1 running emit_mir_module)
- **490 functions** in MIR module after lowering

### What's BROKEN — the SINGLE remaining issue

**`TOKS=0`**: The tokenizer produces 0 tokens despite string comparisons working.

The `align 2` fix makes individual `__mn_str_eq` calls return correct results
(verified via IR injection). But the tokenizer's control flow doesn't accumulate
tokens. Likely cause: the tokenizer's `for _ in 0..1000000` loop with
`if pos >= slen { return tokens }` hits the known Python lowerer bug where
`return` inside `if` inside `for` is unreliable in the compiled binary.

### The fix path

The tokenizer in `mapanare/self/lexer.mn` uses:
```mn
for _ in 0..1000000 {
    if pos >= slen { return tokens }
    ...
    tokens.push(tok)
    ...
}
```

The `return tokens` inside `if` inside `for` may be dropped. The fix:
use a flag-based pattern (documented in Known Python Lowerer Bugs below),
or restructure the tokenizer to avoid `return` inside `for`.

Once the tokenizer produces tokens → parser produces definitions → lowerer
produces functions → emitter produces IR → **mnc-stage2 outputs full IR**.

Then: `diff stage2.ll stage3.ll` → fixed point.

---

## Tools Available

### Culebra (Rust-based IR diagnostics)

Culebra is installed at `~/.cargo/bin/culebra` on WSL. It provides template-driven
pattern scanning for LLVM IR — a Nuclei-style engine for compiler diagnostics.

**19 commands available.** Templates live in the repo at `culebra-templates/`.
Run `culebra scan` from the repo directory, or copy templates to `~/.culebra/templates/`.

```bash
# Template-driven IR scanning (Nuclei-style)
culebra scan stage2.ll                              # Run all templates
culebra scan stage2.ll --tags abi,string             # Filter by tags
culebra scan stage2.ll --severity critical           # Only critical
culebra scan stage2.ll --id unaligned-string-constant # Specific template
culebra scan stage2.ll --header runtime/native/mapanare_core.c  # Cross-ref C header
culebra scan stage2.ll --autofix --dry-run           # Preview fixes
culebra scan stage2.ll --autofix                     # Apply fixes
culebra scan stage2.ll --format json                 # JSON output
culebra scan stage2.ll --format sarif                # SARIF for GitHub

# Template management
culebra templates list                               # List all templates
culebra templates list --tags abi                     # Filter by tag
culebra templates show unaligned-string-constant      # Show template detail

# Workflows (multi-step pipelines)
culebra workflow run bootstrap                        # Run bootstrap workflow
culebra workflow list                                 # List workflows

# IR analysis (replaces ir_doctor.py for some commands)
culebra strings stage2.ll                            # Validate string byte counts
culebra strings stage2.ll -v                         # Also show duplicates
culebra audit stage2.ll                              # Full pathology audit
culebra check stage2.ll                              # llvm-as validation
culebra phi-check stage2.ll                          # PHI predecessor validation
culebra diff a.ll b.ll                               # Compare two IR files
culebra extract stage2.ll emit_line                  # Extract one function
culebra table stage2.ll                              # Per-function metrics
culebra abi stage2.ll                                # ABI analysis

# Binary analysis
culebra binary ./mnc-stage2                          # Inspect binary
culebra run stage2.ll                                # Compile + run

# Full pipeline
culebra pipeline stage2.ll                           # Full diagnostic pipeline
culebra fixedpoint                                   # Fixed-point verification
culebra xray                                         # Full stage2 build + runtime test
culebra xray --timeout 60                            # With longer timeout

# Project management
culebra status                                       # Project status summary
culebra init                                         # Initialize culebra.toml
culebra test                                         # Run test suite
culebra watch stage2.ll                              # Watch for changes
```

### ir_doctor.py (Python-based, legacy)

```bash
python scripts/ir_doctor.py golden                   # 15/15 golden tests
python scripts/ir_doctor.py stage2                    # Stage2 validation
python scripts/ir_doctor.py audit main.ll             # IR audit
python scripts/ir_doctor.py strings main.ll           # String constant validation
python scripts/ir_doctor.py xray                      # Full stage2 build + runtime test
python scripts/ir_doctor.py phi-check /tmp/stage2.ll  # PHI fix validation
```

### Skills (Claude Code slash commands)

```
/golden          Run golden test suite (15/15)
/stage2          Stage2 validation
/rebuild         Full rebuild cycle
/ir-audit        Audit IR for pathologies
/valgrind-map    Crash analysis with struct mapping
```

### Manual commands

```bash
python3 scripts/build_stage1.py                       # Build mnc-stage1
python3 scripts/concat_self.py                        # Concatenate .mn sources
python3 scripts/fix_stage2_phis.py in.ll out.ll       # Fix PHI predecessors
./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn   # Self-compilation → stage2
llvm-as /tmp/stage2.ll -o /dev/null                   # Validate IR
python -m pytest tests/ -q --tb=short                 # Full test suite (4,248+)
```

---

## Build Pipeline (stage2 → mnc-stage2)

```bash
# 1. Generate stage2 IR
./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll

# 2. Fix PHI predecessors (required for clang -O1)
python3 scripts/fix_stage2_phis.py /tmp/stage2.ll /tmp/stage2_fixed.ll

# 3. Compile to native
gcc -c -O2 -fPIC -I runtime/native runtime/native/mapanare_core.c -o /tmp/rt_core.o
clang -c -O1 -Wno-override-module /tmp/stage2_fixed.ll -o /tmp/stage2.o
gcc -o /tmp/mnc-stage2 /tmp/stage2.o /tmp/rt_core.o /tmp/stage2_main.o \
    -lm -lpthread -no-pie -rdynamic

# 4. Test
ulimit -s unlimited && /tmp/mnc-stage2 /tmp/tiny.mn
```

The C main wrapper (`/tmp/stage2_main.c`) calls `compile_and_print(source, filename)`
which returns `MnCompileResult {success, ir_text, errors}`.

---

## Key Files

| File | Role |
|------|------|
| `mapanare/emit_llvm_text.py` | Python text emitter (opaque pointers, byref) |
| `mapanare/self/emit_llvm.mn` | Self-hosted LLVM emitter (byref, align 2, push writeback) |
| `mapanare/self/emit_llvm_ir.mn` | IR string builders, `resolve_mir_type`, Option erasure |
| `mapanare/self/lower.mn` | MIR lowering, module push helpers, match arm handling |
| `mapanare/self/lower_state.mn` | State management, `lookup_var`, type resolution |
| `mapanare/self/lexer.mn` | **Tokenizer — the current blocker** |
| `mapanare/self/parser.mn` | Parser, `parse_struct_fields_to_list` (N-field fix) |
| `mapanare/self/semantic.mn` | Semantic checker, `resolve_type_expr` (generic arg push) |
| `mapanare/self/mir.mn` | MIR data structures |
| `mapanare/self/main.mn` | Compiler driver |
| `mapanare/self/mnc_all.mn` | All modules concatenated (generated by concat_self.py) |
| `mapanare/self/mnc-stage1` | Native binary (built by build_stage1.py) |
| `scripts/ir_doctor.py` | IR diagnostics (golden, stage2, audit, xray, strings, phi-check) |
| `scripts/fix_stage2_phis.py` | PHI predecessor fix script |
| `scripts/build_stage1.py` | Bootstrap build script |
| `scripts/concat_self.py` | Module concatenation |
| `runtime/native/mapanare_core.c` | C runtime (arena, strings, COW lists, tagged pointers) |
| `docs/roadmap/v2.2.0/PLAN.md` | Progress tracker |

---

## Critical Bugs Found & Fixed (reference for future work)

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| String pointer off-by-1 | `mn_untag` clears bit 0; globals at odd addresses shift by -1 | `align 2` on all string constants |
| For-loop infinite loop | SSA iterator `{i64, i64}` never advances (passed by value) | Counter-based loops with alloca increment |
| Parser 3-field limit | `parse_struct_fields_to_list` hardcoded to 3 fields | Replaced with `for` loop |
| `agent` keyword conflict | Lexer tokenizes `agent` as `KW_AGENT`, not `NAME` | Renamed bindings to `ag` |
| Option type inconsistency | `Option<String>` = `{i1, {ptr,i64}}` vs `{i1, ptr}` | Universal Option erasure to `{i1, ptr}` |
| FieldSet doesn't write back | `insertvalue` creates new value but alloca unchanged | GEP+store for parameter allocas; `find_expr_alloca` in lowerer |
| List push doesn't persist | Direct GEP push + LLVM alias analysis caches stale load | Temp alloca + push + explicit write-back (matches Python emitter) |
| List elem_size=8 for all | `__mn_list_new(8)` truncates >8-byte elements | Default elem_sz=16, bump to 16 when unknown |
| `str_join` returns partial | `str_join` passes list by value, loses 64K entries | Print-based output bypass (direct stdout) |
| PHI predecessor mismatch | Match merge blocks missing entries from void arms | `fix_stage2_phis.py` adds zeroinitializer entries |
| `fresh_tmp` name collision | Same function name in two .mn modules | Renamed to `emit_fresh_tmp` |
| `print` missing newline | Self-hosted emitter calls `__mn_str_print` not `__mn_str_println` | Changed to `__mn_str_println` with `_nl` format strings |

---

## Known Python Lowerer Bugs (workarounds required in .mn code)

| Bug | Pattern to avoid | Workaround |
|-----|-----------------|------------|
| Return dropped | `if cond { return x }` followed by more code | Use boolean flag or extract to helper function with early return |
| Break dropped | `for ... { if cond { break } }` | Use flag: `let mut found = false; if !found { if cond { found = true } }` |
| `<=` dropped | `if x <= 3 { ... }` | Use `if x < 4 { ... }` |
| `&&` unreliable | `if a && b && c { ... }` | Use nested: `if a { if b { if c { ... } } }` |
| FieldSet no write-back | `s.field = value` doesn't update alloca | Extract to helper function: `fn update_field(s) -> S { s.field = val; return s }` |
| Nested match phi | `let x = match y { ... }` inside another match | Extract inner match to helper function |

---

## Metrics (current)

- **15/15 golden tests**
- **4,248 pytest passed**
- **65K lines stage2 IR** (fully validates with llvm-as after PHI fix)
- **64K lines accumulated** in stage1 emit_mir_module
- **490 functions** in MIR module
- **328 sret functions** in stage2 (byref active)
- **35 commits** on `dev`
