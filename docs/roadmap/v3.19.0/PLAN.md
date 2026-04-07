# Mapanare v3.19.0 — "Tragavenado" (Self-Hosted Compiler Completeness)

> Bring the self-hosted compiler closer to expressing its own language.
> Add While/Break/Continue/Assert, fix type inference, restore generic tracking.

**Status:** PLANNED
**Estimated scope:** Medium (2 sessions)
**Breaking:** No
**Prerequisite:** v3.18.0

---

## Items

### 1. Stmt enum missing While/Break/Continue/Assert [HIGH]

**Files:** `mapanare/self/ast.mn:104`, `parser.mn`, `lower.mn`, `emit_llvm.mn`
**Reporter:** Coral (H1)

Self-hosted Stmt has only 6 variants. `while` desugars to `for _ in 0..1000000`.
507 bounded-for occurrences (doubled since v3.10.0). Cannot express `break`.

**Fix:**
```mn
enum Stmt {
    ...existing variants...
    While(Expr, Block),
    Break,
    Continue,
    Assert(Expr, Option<String>),
}
```
- Parse `while`/`break`/`continue`/`assert` in `parse_stmt`
- Lower `While` to conditional branch + loop-back edge
- Lower `Break` to jump to loop exit block
- Lower `Continue` to jump to loop header block
- Convert applicable `for _ in 0..N` patterns to proper `while`

### 2. For-loop variable always typed UNKNOWN [MEDIUM]

**File:** `mapanare/self/semantic.mn:1192`
**Reporter:** Coral (M4)

Loop variables get `unknown_type()` unconditionally.

**Fix:** Extract element type from iterable:
- `List<T>` -> bind loop var as `T`
- `Range` -> bind loop var as `Int`
- Otherwise -> `unknown_type()` (fallback)

### 3. 5 commented-out `.push()` calls [MEDIUM]

**File:** `mapanare/self/semantic.mn:738,794,990,1209,1215`
**Reporter:** Coral (M8)

Generic type argument accumulation commented out. `Option<Int>` and `Option<String>`
are indistinguishable in self-hosted checker.

**Fix:** Uncomment using local-copy pattern (same as `scope_define` fix):
```mn
let mut args: List<TypeInfo> = []
args.push(resolved)
return make_generic_type("Option", args)
```

### 4. No InterpString in self-hosted AST [MEDIUM]

**Files:** `mapanare/self/ast.mn`, `parser.mn`, `lower.mn`
**Reporter:** Coral (M5)

String interpolation parsed as concat chain at parser level. No AST representation.

**Fix:** Add `InterpString(List<InterpPart>)` variant to Expr enum.
Parse `"...${expr}..."` syntax. Lower to concat chain in lowerer.

### 5. Self-hosted emitter zero function attributes [HIGH]

**Files:** `mapanare/self/emit_llvm.mn`, `emit_llvm_ir.mn`
**Reporter:** Rattler (H4)

169K-line `main.ll` has zero `nounwind`/`readonly`. Missed optimization.

**Fix:** Add attribute dictionary mapping runtime function names to attribute
strings. Append to `declare` lines during emission.

### 6. Trait parsing is brace-skip only [MEDIUM]

**File:** `mapanare/self/parser.mn:484-491`
**Reporter:** Coral (M6)

Reads trait name and calls `skip_brace_block`. Method signatures discarded.

**Fix:** Parse method signatures inside trait body. Store in TraitDef AST node
for downstream tools (formatters, doc generators, IDE support).

---

## Verification

- [ ] Self-hosted compiler compiles programs with `while`/`break`/`continue`
- [ ] New golden test for while/break/continue/assert
- [ ] `/golden` — all pass
- [ ] `/stage2` — validates with function attributes in IR
- [ ] `main.ll` shows properly typed loop variables
- [ ] `for _ in 0..1000000` occurrences measurably reduced
- [ ] Trait definitions visible in self-hosted AST dump
