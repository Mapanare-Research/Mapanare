# Mapanare v3.0.1 — Bootstrap Runtime + Syntax Completion

> v3.0.0 built the pipeline. v3.0.1 makes it run.

**Status:** DRAFT
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No (additive only — all v3.0.0 syntax remains valid)

---

## Why v3.0.1

v3.0.0 shipped the C emit backend, bilingual keywords, indentation syntax, and
the migration tool. The self-hosted compiler compiles and links through C (0 gcc
errors, 2MB binary). But the binary segfaults at runtime because the C emitter
uses `memcpy` hacks to work around type inference gaps in the MIR lowerer.

v3.0.1 fixes the root cause (MIR type propagation), completes the deferred
syntax features, and gets CI green.

---

## Part 1: Bootstrap Runtime (Critical Path)

### 1.1 — Fix MIR Type Inference in `lower.py` (~400 lines)

The root cause of all bootstrap runtime crashes. The MIR lowerer marks
user-defined enum/struct types as `TypeKind.UNKNOWN`, which forces the C emitter
to use `memcpy`-based coercion with mismatched sizes.

**What to fix:**

| Gap | Location | Fix |
|-----|----------|-----|
| Enum constructor return type | `_lower_construct()` | Set dest type to the enum's `TypeInfo` |
| Option<T> inner type | `_lower_expr()` for `WrapSome`/`WrapNone` | Propagate T from the wrapped value |
| Function return type across calls | `_lower_call()` | Look up callee return type from `_fn_return_types` |
| List element type | `_lower_list()`, `_lower_method_call()` for push | Infer from first element or annotation |
| SSA variable reuse | `_make_value()` | Use unique names per block (no %t0 reuse) |

**Validation:** After fixing, remove ALL `memcpy` coercion hacks from
`emit_c.py`. The C output should compile clean WITHOUT any type casting
workarounds. Then run the binary on a simple `.mn` program.

### 1.2 — Remove C Emitter Workarounds (~200 lines removed)

Once `lower.py` propagates types correctly, remove from `emit_c.py`:
- `void*` boxing for forward-referenced fields
- `memcpy` in StructInit, FieldGet, EnumPayload, Copy, Return, Call, BinOp
- SSA reuse guards (Const→struct memcpy)
- Argument coercion via `memcpy`
- Type back-propagation from field access

The C emitter should be clean: direct assignments, proper types, no casts.

### 1.3 — mnc-stage1 Runs (~0 lines, just testing)

With proper types:
1. `python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o stage1.c`
2. `gcc -O1 stage1.c runtime/native/mapanare_core.c -o mnc-stage1 -lm -lpthread`
3. `echo 'fn main() { print("hello") }' | ./mnc-stage1 /dev/stdin`
4. Output should be LLVM IR or C source for "hello world"

### 1.4 — Three-Stage Bootstrap (~100 lines scripts)

```bash
# Stage 0: Python bootstrap → stage1
python3 -m mapanare emit-c mapanare/self/mnc_all.mn -o /tmp/stage1.c
gcc -O1 /tmp/stage1.c runtime/native/mapanare_core.c -o /tmp/mnc-stage1 -lm -lpthread

# Stage 1: stage1 compiles itself → stage2
/tmp/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.c
gcc -O1 /tmp/stage2.c runtime/native/mapanare_core.c -o /tmp/mnc-stage2 -lm -lpthread

# Stage 2: stage2 compiles itself → stage3
/tmp/mnc-stage2 mapanare/self/mnc_all.mn > /tmp/stage3.c

# Fixed point
diff /tmp/stage2.c /tmp/stage3.c  # Must be empty
```

Script: `scripts/verify_fixed_point_c.sh`

---

## Part 2: Syntax Completion

### 2.1 — `di` as Print Keyword (~100 lines)

Currently `print` is a function call (parsed as `ident + call_expr`). Making
`di` a keyword requires:

1. Add `KW_PRINT` terminal (only matches `di`, NOT `print` — avoids breaking
   existing `print()` calls)
2. Add `di_stmt: KW_PRINT expr` rule to grammar
3. Parser transformer creates a `PrintStmt` AST node
4. Semantic checker validates the expression
5. MIR lowerer emits `Call(print, [expr])`
6. `print("hello")` still works as a function call
7. `di "hello"` works as a statement (no parens needed)

### 2.2 — `+name` Pub Prefix (~80 lines)

1. Add `PLUS` as optional visibility prefix in struct/fn/tipo definitions
2. Grammar: `fn_def: (KW_PUB | PLUS)? KW_FN NAME ...`
3. Parser transformer maps `PLUS` to `public=True`
4. Update migration tool to convert `pub` → `+`

### 2.3 — `Y + X:` Impl Syntax (~60 lines)

1. Grammar: `impl_plus_def: NAME PLUS NAME LBRACE ... RBRACE`
   (or with colon for indent syntax)
2. Parser transformer creates `ImplDef(target=Y, trait=X)`
3. Distinguish from binary `+` by checking LBRACE after second NAME
4. Update migration tool

### 2.4 — `si`-as-Match with Indentation (~150 lines)

With indentation syntax, `si` can handle both `if` and `match`:

```
si shape:                     # match: body has => arms
    Circle(r) => 3.14 * r * r
    Rect(w, h) => w * h

si x > 0:                    # if: body has statements (no =>)
    print("positive")
```

**Implementation:**
1. The indent preprocessor already converts `si expr:` → `si expr {`
2. Add a new rule: `si_match_expr: KW_IF expr LBRACE match_arms RBRACE`
3. Lark can't disambiguate `si expr { stmts }` vs `si expr { arms }` in LALR
4. **Solution:** Post-parse transform. Parse as `if_expr`, then in the
   transformer check if the block body contains `=>` tokens. If so,
   reconstruct as `match_expr`.

### 2.5 — `@Name()` Spawn (~40 lines)

1. Differentiate `@Name(args)` (spawn) from `@name` (decorator) by context
2. In expression position: `@Name(args)` → spawn
3. At definition level: `@name fn ...` → decorator
4. The indent preprocessor can help: `@Name(args)` on its own line in a
   function body → spawn. `@name` followed by `fn`/`tipo`/`modo` → decorator.
5. **Solution:** Lexer callback or post-parse transform.

### 2.6 — Optional Parens (~100 lines)

Single-argument calls without parens: `di "hello"`, `Err "not found"`.

Rules:
- Only for single string/literal/ident arguments
- Not for multi-arg, nested calls, or chained expressions
- `di x` = `di(x)`, `Err msg` = `Err(msg)`
- Grammar: add optional no-paren call rule after atoms

### 2.7 — Implicit Return (~60 lines)

Last expression in a function = return value. `da`/`return` only for early exits.

1. Semantic checker: if function has return type and last statement is an
   expression statement, treat it as the return value
2. MIR lowerer: emit `Return` for the last expression
3. Doesn't affect existing code (explicit `da`/`return` still works)

### 2.8 — Empty Block `...` (~20 lines)

1. Grammar: `ELLIPSIS: "..."`
2. In block position: `...` → empty block (like Python's `pass`)
3. Parser transformer creates an empty Block

---

## Part 3: CI & Tooling

### 3.1 — CI Green (~100 lines)

| Check | Status | Fix |
|-------|--------|-----|
| `black --check .` | PASS | Already clean |
| `ruff check .` | FAIL | Fix scripts/, benchmarks/ lint issues |
| `mypy mapanare/ runtime/` | PASS | Already clean |
| `pytest tests/` | PARTIAL | Fix native test segfault on WSL |
| WASM emission | PARTIAL | Fix dom_app.mn bridge imports |

### 3.2 — VS Code Extension (~200 lines)

1. Update `editors/vscode/syntaxes/mapanare.tmLanguage.json`:
   - Add bilingual keywords (pon, da, si, sino, cada, en, mien, sal, sigue, nada, yo, usa, tipo, modo)
   - Add `@Name` agent syntax highlighting
   - Add `-> / <-` channel operators
   - Add `|` variant prefix highlighting in tipo blocks
2. Update snippets for v3 syntax

### 3.3 — Playground Update (~100 lines)

1. Update `playground/src/examples.js` with v3 syntax examples
2. Update `playground/src/mn-lang.js` keyword list
3. Ensure WASM backend handles v3 keywords

### 3.4 — tree-sitter Grammar (~300 lines)

Update the tree-sitter grammar for editor integrations:
- Bilingual keywords
- Indentation blocks
- tipo/modo/@ agent syntax

---

## Part 4: Quality & Validation

### 4.1 — Culebra C Backend Templates (~100 lines)

1. Add templates for common C emitter issues:
   - `memcpy-size-mismatch`: detect sizeof mismatches in generated C
   - `void-ptr-deref`: detect void* dereference without cast
   - `ssa-reuse`: detect same variable used for different types
2. `culebra scan stage1.c` as CI step
3. `culebra compare stage1.c stage2.c` for fixed-point validation

### 4.2 — Migration Validation (~50 lines)

Automated test: for each golden test:
1. Migrate from v2 → v3
2. Compile with C backend
3. Run and compare output with v2 version
4. Must be identical

### 4.3 — Benchmark: C vs LLVM (~50 lines)

Measure for each golden test:
- Compile time: emit_c + gcc vs emit_llvm + clang
- Binary size
- Runtime performance
- Report in `benchmarks/C_VS_LLVM.md`

---

## Phase Summary

| Phase | Description | Est. Lines | Priority |
|-------|-------------|-----------|----------|
| 1.1 | Fix MIR type inference | ~400 | CRITICAL |
| 1.2 | Remove C emitter workarounds | -200 | CRITICAL |
| 1.3 | mnc-stage1 runs | testing | CRITICAL |
| 1.4 | Three-stage bootstrap | ~100 | CRITICAL |
| 2.1 | `di` print keyword | ~100 | HIGH |
| 2.2 | `+name` pub prefix | ~80 | HIGH |
| 2.3 | `Y + X:` impl syntax | ~60 | HIGH |
| 2.4 | `si`-as-match | ~150 | HIGH |
| 2.5 | `@Name()` spawn | ~40 | MEDIUM |
| 2.6 | Optional parens | ~100 | MEDIUM |
| 2.7 | Implicit return | ~60 | MEDIUM |
| 2.8 | Empty block `...` | ~20 | LOW |
| 3.1 | CI green | ~100 | HIGH |
| 3.2 | VS Code extension | ~200 | MEDIUM |
| 3.3 | Playground update | ~100 | LOW |
| 3.4 | tree-sitter grammar | ~300 | LOW |
| 4.1 | Culebra C templates | ~100 | MEDIUM |
| 4.2 | Migration validation | ~50 | HIGH |
| 4.3 | C vs LLVM benchmark | ~50 | LOW |

### Dependency Chain

```
Part 1 (bootstrap runtime) — CRITICAL PATH
  1.1 Fix lower.py type inference
    → 1.2 Remove emit_c.py workarounds
      → 1.3 mnc-stage1 runs
        → 1.4 Three-stage bootstrap

Part 2 (syntax) — PARALLEL
  2.1 di keyword
  2.2 +name pub
  2.3 Y + X impl
  2.4 si-as-match
  2.5 @spawn
  2.6 Optional parens
  2.7 Implicit return
  2.8 ...

Part 3 (tooling) — PARALLEL
  3.1 CI green
  3.2 VS Code
  3.3 Playground
  3.4 tree-sitter

Part 4 (validation) — AFTER Part 1
  4.1 Culebra templates
  4.2 Migration validation
  4.3 Benchmarks
```

Critical path: **1.1 → 1.2 → 1.3 → 1.4** (~700 lines, ~1-2 weeks)

---

## Success Criteria

### Must Ship

- [x] mnc-stage1 compiles AND RUNS through C ✓ (2026-04-03)
- [x] mnc-stage1 SELF-COMPILES: 77K lines LLVM IR, parses ✓ (2026-04-03)
- [ ] Stage2 IR validates (5 verification errors: merge-block-in-entry-block)
- [ ] Three-stage bootstrap reaches fixed point (stage2.c == stage3.c)
- [x] `di "hello"` works as keyword statement ✓ (2026-04-03)
- [x] `+fn`, `+tipo` work as pub prefix ✓ (2026-04-03)
- [x] Implicit return ✓ (2026-04-03)
- [x] `...` empty block ✓ (2026-04-03)
- [ ] `si expr:` with `=>` arms works as match
- [ ] CI green on push to dev
- [ ] VS Code extension highlights v3 syntax
- [ ] All golden tests pass through C backend (already done in v3.0.0)

### Nice-to-Have (v3.1)

- [ ] Optional parens (`di "hello"` without parens)
- [ ] `@Name()` spawn syntax
- [ ] TCC integration
- [ ] Playground updated
- [ ] tree-sitter grammar
- [ ] C vs LLVM benchmarks

---

## Known Issues (inherited from v3.0.0)

| Issue | Severity | Workaround |
|-------|----------|------------|
| ~~Binary segfaults at runtime~~ | ~~Critical~~ | FIXED — runs, outputs IR |
| ~~String truncation in emitted IR~~ | ~~Medium~~ | FIXED — aligned string constants |
| 33 remaining memcpy size warnings | Medium | From unreachable match defaults + remaining Option<T> mismatches |
| 4/15 golden tests fail through stage1 | Medium | Struct field indices (2), enum sizing (1), Result types (1) |
| Self-hosted parser: English only | Medium | Bilingual keywords (si/pon/sino) not supported in self-hosted parser |
| O0 bootstrap: 8 compile errors | Medium | Use O2 (0 errors, links) |
| dom_app.mn WASM fails | Low | Pre-existing, not v3 regression |
| KV/Redis/AI stdlib tests fail | Low | Pre-existing module resolution |
| String concat display issue | Low | Runtime works, display truncated |
| `ruff check .` fails on scripts/ | Low | Pre-existing, mapanare/ is clean |

---

## v3.0.1 Phase 1 Final Status (2026-04-03)

### Achieved
- mnc-stage1 (Python→C→gcc) self-compiles: 77K lines LLVM IR
- Stage2 IR validates with llvm-as (via auto-fix script)
- Stage2 binary links and runs (simple programs)
- 11/15 golden tests pass through stage1+llvm-as
- 59→15 gcc warnings
- 832 core tests pass, 0 regressions

### Remaining Blockers for Three-Stage Bootstrap
1. **Stage2 parser limitations**: can't parse complex type annotations
   (Option<TypeExpr>, nested generics) in the self-hosted source
2. **Stack overflow**: stage2 needs 64MB+ stack for large functions
3. **COW state threading**: merge block instructions in entry block
   (auto-fixed by scripts/fix_stage2_ir.py)
