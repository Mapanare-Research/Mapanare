# v4.35.0 Session Report — Match Guards + Or-Patterns

**Date:** 2026-04-12
**Scope:** Two new syntactic forms for pattern matching + 3 LOW runtime items
**Breaking:** No (additive syntax; existing matches unchanged)
**Delta review:** Required (Coral + Rattler)

---

## What shipped

### Match guards (`if cond`)

A `match` arm can now have an optional `if <expr>` clause between the pattern and `=>`:

```mapanare
match opt {
    Some(x) if x > 0 => print("positive"),
    Some(x) => print("nonpositive"),
    None => print("absent"),
}
```

**Semantics:**
- Guard expression must be `Bool` (compile-time error otherwise)
- Guard can reference names bound by the pattern
- Guards count toward exhaustiveness (Rust semantics — pattern coverage, not guard truth)
- Guard failure falls through to the decision tree of remaining rows (O(n^2) simple approach)

**Implementation:**
- Grammar: `match_arm: pattern guard? FAT_ARROW (expr | block)` + `guard: KW_IF assign_expr`
- AST: `MatchArm.guard: Expr | None = None`
- Parser: `guard` transformer extracts the expression; `match_arm` detects 3-item case
- Semantic: type-check guard after `_bind_pattern`, before body
- Lowering: `Branch(guard_val, body_bb, fallback_bb)` with fallback decision tree from remaining rows via `_emit_decision_tree` helper
- Self-hosted: mirror in ast.mn, parser.mn, semantic.mn, lower.mn

### Or-patterns (`A | B | C`)

A pattern can be a disjunction of alternatives separated by `|`:

```mapanare
match token {
    Plus | Minus => "additive",
    Star | Slash | Mod => "multiplicative",
    Eof => "end",
    _ => "other",
}
```

**Semantics:**
- All alternatives must bind the same set of variable names
- Alternatives with different bindings produce a compile-time error
- Or-patterns expand to multiple rows in the Maranget pattern matrix (shared action_idx)
- Exhaustiveness covers all alternatives

**Implementation:**
- Grammar: `?pattern -> or_pattern`, `or_pattern: pattern_alt (BAR pattern_alt)*`
- AST: new `OrPattern(Pattern)` with `alternatives: list[Pattern]`
- Parser: `or_pattern` transformer wraps only when >1 alternative
- Semantic: `_bind_pattern` handles `OrPattern` via `_collect_pattern_names` (excludes enum variant names)
- Pattern engine: `expand_or_patterns` called at top of `build_decision_tree`
- Lowering: `_bind_match_arm` delegates to first alternative
- Self-hosted: `OrPat(List<Pattern>)` variant, `parse_pattern` / `parse_pattern_alt` split

### LOW items closed (3)

| Item | Fix | Evidence |
|------|-----|----------|
| `s_net_initialized` (5th cycle) | `pthread_once` / `InitOnceExecuteOnce` | `runtime/native/mapanare_io.c` |
| `ssl_load_library` (3rd cycle) | `pthread_once` replacing atomic CAS | `runtime/native/mapanare_io.c` |
| `s_bcrypt` (3rd cycle) | `InitOnceExecuteOnce` | `runtime/native/mapanare_io.c` |

---

## Test evidence

- 21 new tests (5 parser/guards, 7 parser/or-patterns, 5 semantic/guards, 4 semantic/or-patterns)
- 3 new golden tests: `49_match_guards.mn`, `50_match_or_patterns.mn`, `51_match_guards_and_or.mn`
- 723 tests pass (parser + semantic + LLVM + test_runner)
- `runtime/native/mapanare_io.c` compiles clean with `gcc -fsyntax-only`

---

## Design decisions

1. **Combined release** — guards and or-patterns shipped together (PLAN default). No reviewer split request.
2. **Simple guard fall-through** — O(n^2) re-run from remaining rows. Arm counts are small in practice (<20).
3. **Strict or-pattern bindings** — same names, same types across alternatives (Rust, not Swift).
4. **`guard: KW_IF assign_expr`** — not `expr`, to avoid `=>` being consumed as lambda arrow.
5. **No `|` precedence conflict** — Mapanare has no bitwise OR in expressions; `BAR` only used in `tipo_variant`.

---

## Files changed

| File | Lines | What |
|------|-------|------|
| `mapanare/mapanare.lark` | +5 | Guard rule, or_pattern/pattern_alt restructure |
| `mapanare/ast_nodes.py` | +8 | `MatchArm.guard`, `OrPattern` |
| `mapanare/parser.py` | +15 | `guard`, `or_pattern` transformers, `match_arm` update |
| `mapanare/semantic.py` | +45 | Guard type-check, or-pattern binding check, `_is_enum_variant_name` |
| `mapanare/pattern_matching.py` | +25 | `expand_or_patterns`, `OrPattern` handling |
| `mapanare/lower.py` | +35 | Guard fall-through, `_emit_decision_tree`, `OrPattern` in `_bind_match_arm` |
| `mapanare/self/ast.mn` | +5 | `guard` field, `OrPat` variant |
| `mapanare/self/parser.mn` | +30 | Guard parsing, `parse_pattern`/`parse_pattern_alt` split |
| `mapanare/self/semantic.mn` | +10 | Guard check, OrPat binding |
| `mapanare/self/lower.mn` | +30 | Guard fall-through, OrPat expansion |
| `runtime/native/mapanare_io.c` | +40/-20 | pthread_once for 3 LOW items |
