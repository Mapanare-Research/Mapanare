# v3.0.1 — Bootstrap Runtime + Syntax Completion — Continuation Prompt

> Continue the v3.0.1 execution in WSL. Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.0.1/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.
> Use Culebra after every fix: `culebra baseline diff`, `culebra journal add`.

---

## Goal

Two tracks that finish what v3.0.0 started:

1. **Bootstrap runtime** — fix MIR type inference so the self-hosted compiler
   actually RUNS through C (not just links). Reach three-stage fixed point.
2. **Syntax completion** — `di` keyword, `+name` pub, `si`-as-match,
   `@Name()` spawn, optional parens, implicit return, `...` empty blocks.

---

## Inherited State (from v3.0.0 — `dev` branch)

### What Works

| Component | Status |
|-----------|--------|
| C emit backend (`emit_c.py`) | 2,239 lines, 15/15 golden tests |
| Bilingual keywords | 17 pairs (pon/let, si/if, da/return, etc.) |
| Indentation syntax | Colon+indent preprocessor, braces still accepted |
| `tipo` / `modo` / `@Agent` | Struct/enum unification, trait alias, agent syntax |
| `mapanare run` | C backend default (gcc), `--release` for LLVM |
| `mapanare migrate --to=v3` | Keyword + structural migration, 99 files migrated |
| Self-hosted emit_c.mn | 770 lines, parses clean |
| `pip install mapanare` | Works without llvmlite |
| mnc-stage1 binary | Compiles and LINKS through C (0 gcc errors, 2MB) |
| 15/15 golden tests | Pass through C backend |
| 4,364 pytest | Pass (65 pre-existing failures) |
| ruff/mypy/black | Clean on mapanare/ runtime/ |

### What's Broken (and why we're doing v3.0.1)

| Problem | Root Cause | Impact |
|---------|-----------|--------|
| mnc-stage1 binary segfaults | `memcpy` size mismatches from type coercion hacks | Can't self-compile |
| MIR marks enums as UNKNOWN | `lower.py` doesn't propagate user-defined type names | C emitter uses wrong types |
| Option<T> inner type lost | `_lower_expr()` doesn't set T on WrapSome/WrapNone | `MnOption_int64_t` instead of `MnOption_BinOpKind` |
| SSA variable reuse | Same `%t0` used for `int64_t` then `TypeResult` | Type declaration conflicts |
| List element type unknown | `_lower_list()` doesn't infer from context | `int64_t` cast for struct elements |
| `di` not a keyword | Would break existing `print()` calls | Can't write `di "hello"` |
| `+name` not supported | Grammar has no `PLUS` visibility prefix | Can't write `+fn`, `+tipo` |
| `si`-as-match deferred | LALR conflict with braces | Need indent to disambiguate |
| CI not green | `ruff check .` fails on scripts/ | PR checks fail |

---

## v3.0.1 Phase Execution Order

### Phase 1: Bootstrap Runtime (CRITICAL PATH)

**1.1 — Fix MIR Type Inference in `lower.py` (~400 lines)**

The root cause of ALL runtime crashes. Fix these specific type propagation gaps:

| Gap | Where | Fix |
|-----|-------|-----|
| Enum constructor return type | `_lower_construct()` | Set `dest.ty` to the enum's `TypeInfo` |
| Option<T> inner type | `WrapSome`/`WrapNone` in `_lower_expr()` | Copy T from the wrapped value's type |
| Function return type | `_lower_call()` | Look up callee in `_fn_return_types` dict |
| List element type | `_lower_list()` | Infer from first element or type annotation |
| SSA variable reuse | `_make_value()` | Generate unique names per type (no `%t0` reuse) |

Key file: `mapanare/lower.py` (~2,570 lines)

Validation after each fix:
```bash
# Re-emit
python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o /tmp/stage1.c

# Check: should need FEWER memcpy hacks
grep -c "memcpy" /tmp/stage1.c  # Should decrease

# Culebra baseline
culebra baseline diff /tmp/stage1.c

# Golden regression check
for f in tests/golden/*.mn; do
    python3 -m mapanare emit-c "$f" -o /dev/null
done
```

**1.2 — Remove C Emitter Workarounds (~-200 lines)**

After `lower.py` propagates types correctly, remove from `emit_c.py`:
- `void*` boxing for forward-referenced fields (revert to direct types)
- `memcpy` in StructInit, FieldGet, EnumPayload, Copy, Return, Call, BinOp
- SSA reuse guards (Const→struct memcpy)
- Argument coercion via `memcpy`
- Type back-propagation from field access
- `_propagate_types()` pass (no longer needed)

The C emitter should be clean: direct assignments, proper types, no casts.

Validation:
```bash
# Must still compile clean
gcc -O0 -I runtime/native /tmp/stage1.c runtime/native/mapanare_core.c \
    -o /tmp/mnc-stage1 -lm -lpthread

# Culebra scan — should have FEWER findings
culebra scan /tmp/stage1.c --tags c
culebra baseline diff /tmp/stage1.c
```

**1.3 — mnc-stage1 Runs**

```bash
echo 'fn main() { print("hello") }' > /tmp/test.mn
/tmp/mnc-stage1 /tmp/test.mn
# Should output C source (or LLVM IR) for hello world, not segfault
```

Use Valgrind if it still crashes:
```bash
culebra wrap -- valgrind /tmp/mnc-stage1 /tmp/test.mn
# Or:
python scripts/ir_doctor.py valgrind-map /tmp/mnc-stage1 /tmp/test.mn
```

**1.4 — Three-Stage Bootstrap**

```bash
# Stage 0: Python → stage1
python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o /tmp/stage1.c
gcc -O1 /tmp/stage1.c runtime/native/mapanare_core.c -o /tmp/mnc-stage1 -lm -lpthread

# Stage 1: stage1 → stage2
/tmp/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.c
gcc -O1 /tmp/stage2.c runtime/native/mapanare_core.c -o /tmp/mnc-stage2 -lm -lpthread

# Stage 2: stage2 → stage3
/tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.c

# Fixed point
diff /tmp/stage2.c /tmp/stage3.c   # Must be empty

# Culebra verification
culebra compare /tmp/stage1.c /tmp/stage2.c --metric calls
culebra diff /tmp/stage2.c /tmp/stage3.c
```

Script: `scripts/verify_fixed_point_c.sh`

---

### Phase 2: Syntax Completion

**2.1 — `di` as Print Keyword (~100 lines)**

- Grammar: `KW_DI: "di"` (only `di`, NOT `print` — avoids breaking `print()`)
- Rule: `di_stmt: KW_DI expr`
- AST: `PrintStmt(expr)` node
- Semantic: validate expression type
- Lowerer: emit `Call(print, [expr])`
- `print("hello")` still works as function call
- `di "hello"` works as statement

Key files: `mapanare.lark`, `parser.py`, `ast_nodes.py`, `semantic.py`, `lower.py`

**2.2 — `+name` Pub Prefix (~80 lines)**

- Grammar: `fn_def: (KW_PUB | PLUS)? KW_FN NAME ...` (same for tipo_def, modo)
- Parser: map `PLUS` to `public=True`
- Migration tool: convert `pub` → `+`

**2.3 — `Y + X:` Impl Syntax (~60 lines)**

- Grammar: `impl_plus_def: NAME PLUS NAME (COLON | LBRACE) ...`
- Parser: create `ImplDef(target=Y, trait=X)`
- Disambiguate from binary `+` by checking LBRACE/COLON after second NAME

**2.4 — `si`-as-Match (~150 lines)**

Post-parse transform approach (avoids LALR conflict):
1. Parse `si expr { ... }` as `if_expr`
2. In transformer, check if body contains `=>` arms
3. If yes, reconstruct as `match_expr`
4. Works with both braces and indent syntax

**2.5 — `@Name()` Spawn (~40 lines)**

Context-based disambiguation:
- Expression position: `@Name(args)` → spawn
- Definition level: `@name fn/tipo/modo` → decorator
- Post-parse or indent preprocessor resolves

**2.6 — Optional Parens (~100 lines)**

- `di "hello"` = `di("hello")`
- `Err "not found"` = `Err("not found")`
- Only for single string/literal/ident arguments
- Required for multi-arg, nested, chained

**2.7 — Implicit Return (~60 lines)**

- Last expression in function = return value
- Semantic checker: if function has return type and last stmt is expr, treat as return
- Lowerer: emit `Return` for last expression
- Explicit `da`/`return` still works

**2.8 — Empty Block `...` (~20 lines)**

- Grammar: `ELLIPSIS: "..."`
- In block position: empty Block
- Like Python's `pass`

---

### Phase 3: CI & Tooling

**3.1 — CI Green (~100 lines)**

- Fix `ruff check .` for scripts/, benchmarks/
- Fix native test WSL segfault (skip or guard)
- Fix dom_app.mn WASM bridge imports

**3.2 — VS Code Extension (~200 lines)**

- Update tmLanguage: bilingual keywords, @agent, ->//<-, | variants
- Update snippets for v3 syntax

**3.3 — Playground (~100 lines)**

- Update examples.js with v3 syntax
- Update mn-lang.js keyword list

---

### Phase 4: Validation

**4.1 — Culebra C Templates (~100 lines)**

- `memcpy-size-mismatch`: detect sizeof issues in generated C
- `void-ptr-deref`: detect void* access without cast
- `ssa-reuse`: detect same variable used for different types

**4.2 — Migration Validation (~50 lines)**

For each golden test: migrate v2→v3, compile C, run, compare output.

**4.3 — C vs LLVM Benchmark (~50 lines)**

Compile time, binary size, runtime perf for each golden test.

---

## Tools Available

### Culebra v2.0.0 (`~/.cargo/bin/culebra`)

**USE AFTER EVERY FIX. The feedback loop is: fix → emit → gcc → culebra diff → golden → commit.**

```bash
# --- START EVERY SESSION ---
culebra journal show                                # Where we left off
culebra summary /tmp/stage1.c                       # Current scan state

# --- After each fix ---
python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o /tmp/stage1.c
gcc -O0 -I runtime/native /tmp/stage1.c runtime/native/mapanare_core.c \
    -o /tmp/mnc-stage1 -lm -lpthread 2>&1 | grep "error:" | wc -l
culebra baseline diff /tmp/stage1.c                 # Fixed/New/Remaining
culebra journal add "description" --action fix --tags "bootstrap"

# --- Scanning ---
culebra scan /tmp/stage1.c --tags c                 # C-specific templates
culebra triage /tmp/stage1.c --brief               # One-line summary

# --- Debugging crashes ---
culebra wrap -- valgrind /tmp/mnc-stage1 /tmp/test.mn
culebra wrap -- gcc -O1 -c /tmp/stage1.c -o /dev/null
culebra learn                                       # Pattern analysis

# --- Fixed-point verification ---
culebra diff /tmp/stage2.c /tmp/stage3.c           # Must be empty
culebra compare /tmp/stage1.c /tmp/stage2.c --metric calls

# --- Baselines ---
culebra baseline save /tmp/stage1.c                # After a good state
culebra baseline diff /tmp/stage1.c                # After changes
```

### Skills (Claude Code slash commands)

```
/golden          Run 15/15 golden test suite
/rebuild         Full rebuild cycle
/culebra-scan    Culebra template scan
/valgrind-map    Crash analysis with struct mapping
```

### Manual Commands

```bash
# C backend pipeline
python3 -m mapanare emit-c file.mn -o output.c
python3 -m mapanare run file.mn                     # C backend (default)
python3 -m mapanare run --release file.mn            # LLVM backend

# Self-hosted bootstrap
python3 scripts/concat_self.py                       # Concatenate .mn sources
python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o /tmp/stage1.c
gcc -O0 -I runtime/native /tmp/stage1.c runtime/native/mapanare_core.c \
    -o /tmp/mnc-stage1 -lm -lpthread

# Testing
python -m pytest tests/parser/ tests/semantic/ tests/emit/ tests/lexer/ \
    tests/mir/ tests/cli/ tests/optimizer/ -q --tb=short   # Core: 878 pass
python -m pytest tests/ --ignore=tests/native/ -q --tb=no  # Full: 4,364 pass

# Linting
python3 -m ruff check mapanare/ runtime/
python3 -m mypy mapanare/ runtime/ --ignore-missing-imports
python3 -m black --check mapanare/ runtime/ --target-version py312
```

---

## Key Files

| File | Role | v3.0.1 Changes |
|------|------|----------------|
| `mapanare/lower.py` | **AST → MIR lowering** | **FIX: type propagation for enums, Options, lists** |
| `mapanare/emit_c.py` | C emitter (2,239 lines) | **CLEAN: remove memcpy hacks after lower.py fix** |
| `mapanare/mapanare.lark` | Grammar | **ADD: di_stmt, PLUS visibility, si-match, ELLIPSIS** |
| `mapanare/parser.py` | Parser + indent preprocessor | **ADD: di/+pub/si-match/spawn handlers** |
| `mapanare/ast_nodes.py` | AST nodes | **ADD: PrintStmt** |
| `mapanare/semantic.py` | Type checker | **ADD: di/implicit return/+pub** |
| `mapanare/mir_opt.py` | MIR optimizer | DCE entry point preservation |
| `mapanare/migrate.py` | Migration tool (373 lines) | **ADD: pub→+, impl→Y+X, di conversion** |
| `mapanare/cli.py` | CLI | emit-c, migrate, run (C default) |
| `mapanare/self/emit_c.mn` | Self-hosted C emitter (770 lines) | Parses clean |
| `mapanare/self/mnc_all.mn` | Self-hosted compiler (11,363 lines) | Target for bootstrap |
| `runtime/native/mapanare_core.c` | C runtime | Unchanged |
| `scripts/verify_fixed_point_c.sh` | **NEW: 3-stage C bootstrap** | |
| `docs/roadmap/v3.0.1/PLAN.md` | Progress tracker | |

---

## Culebra Journal (inherited from v3.0.0)

```
★ Bootstrap gap: 2,921 → 76 gcc errors (97.4%)
✗ 76 errors: enum_as_int(22) arg(18) assign(13) incomplete(8) option(7) other(8)
✓ 76 → 48  Option type from wrapped value
✓ 48 → 44  Phi type propagation
✓ 44 → 33  Arg coercion via memcpy
✓ 33 → 30  Void phi + brace fix
✓ 30 → 23  Circular Option boxing
✓ 23 → 7   void* boxing + memcpy
✓ 7 → 6    EnumInit + IndexGet + Call fixes
✓ 6 → 5    ListInit propagated type
★ 0 gcc compile errors! 2 linker errors remain.
✓ Namespace resolution + main wrapper
★ mnc-stage1 binary LINKS! 2MB, 0 errors. Segfaults at runtime.
```

**v3.0.1 goal: turn that last line into "mnc-stage1 binary RUNS. Fixed point reached."**

---

## Metrics (inherited from v3.0.0)

- **15/15 golden tests** passing through C backend
- **4,364 pytest** passing (65 pre-existing failures)
- **48,356 lines** stage1 C (from 11,363 lines .mn)
- **519 functions** in MIR module
- **2MB** linked binary (0 gcc errors)
- **99 .mn files** migrated to v3 keywords
- **Culebra:** 690 scan findings, 0 regressions across all fixes

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-03 | Fix lower.py instead of more emit_c.py hacks | Root cause > symptoms. memcpy hacks compile but crash at runtime |
| 2026-04-03 | di only (not print) as keyword | Avoids breaking existing print() function calls |
| 2026-04-03 | Post-parse transform for si-match | LALR can't disambiguate if vs match in brace syntax |
| | | |
