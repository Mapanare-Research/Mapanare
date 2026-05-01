# v5.20.1 — Te.5.F — bootstrap mirror (patch)

**Status:** PLANNING
**Breaking:** No. Pure additive: `mnc-stage1` learns to parse and
lower the four Te.5 surface forms (field shorthand, struct
update `..base`, let destructuring, if-let / while-let / let-else)
exactly matching what the Python bootstrap shipped in v5.20.0.
Code that uses none of the new forms continues to compile
unchanged.
**Prerequisite:** v5.20.0 shipped (Python parser/semantic/lower
for all four features, 11 new goldens at `tests/golden/81-91`,
`STRUCT_ERGO_DESIGN.md` 10 locked decisions, `SESSION_REPORT.md`
explicit "Phase 5 — Te.5.F deferred to v5.20.1").
**Estimated effort:** 6–10h, two or three sessions. Slightly
larger than v5.15.1 (~5–8h) because Te.5 ships four features,
not one. Per-feature ordering smallest-first lets each session
end at a strict-fixed-point checkpoint.

---

## Why this exists

v5.20.0 shipped four ergonomic struct/let surface forms in the
Python bootstrap. By explicit decision (`v5.20.0/PLAN.md` Te.5.F
and `v5.20.0/SESSION_REPORT.md` "Deferred to v5.20.1"), the
**bootstrap mirror was deferred**: `mnc-stage1` rejects all four
new forms today.

| Form | Python bootstrap (v5.20.0) | Native `mnc-stage1` (v5.18.0 source) |
|---|---|---|
| `Point { x, y }` shorthand | ✅ parses, lowers, IR-identical | ❌ parse error (expects COLON) |
| `Point { x: 5, ..base }` | ✅ parses, lowers, IR-identical | ❌ parse error (unexpected RANGE) |
| `let Point { x, y } = p` | ✅ parses, type-checks, lowers | ❌ parse error (expects NAME after KW_LET) |
| `if let / while let / let else` | ✅ parses, desugars to match | ❌ parse error (KW_LET unexpected after KW_IF) |

The 11 new goldens at `tests/golden/81-91` compile through
`mapanare emit-llvm` (Python bootstrap) and IR-validate via
`clang -c`, but **fail through `mnc-stage1`** today. v5.20.1
closes this gap — same algorithm, same identifier-naming
convention, same IR-equivalence properties.

That gap is acceptable in v5.20.0 because:

1. The Python bootstrap is the canonical reference compiler in
   dev workflows. v5.20.0 delivers all four forms to
   `mapanare run` / `mapanare emit-llvm` on day one.
2. None of the new forms appear in `mapanare/self/*.mn` itself
   — the bootstrap source remains v5.17.x-style, so the strict
   3-stage fixed point at the v5.18.0 milestone (232,281 lines
   / 0-line diff) is **preserved by construction** by v5.20.0
   not editing self/.
3. Touching `mapanare/self/{ast,parser,lower,semantic}.mn` is
   the only way to break that fixed point; v5.20.0 deliberately
   avoided the risk.

The gap stops being acceptable when **v5.21.0 (Te.6 — small
ergonomic wins) wants to extend the surface further**. For
v5.21.0 to compose cleanly, the bootstrap must already accept
every Python-bootstrap-acceptable surface form, so v5.21.0's
incremental additions can land against a stable reference.
Ship v5.20.1 between v5.20.0 and v5.21.0; "soon after v5.20.0"
is the most honest place because the lowering design is fresh.

---

## Goal

1. `mnc-stage1` parses and lowers all four Te.5 surface forms
   exactly matching v5.20.0's Python behavior:
   - **Te.5.B** field shorthand `Point { x, y }`.
   - **Te.5.C** struct update `Point { x: 5, ..base }`.
   - **Te.5.D** let destructuring with nested patterns, rest
     patterns, and per-field mutability.
   - **Te.5.E** `if let` / `while let` / `let else` with
     divergence enforcement (D5/D6) on `let else`.
2. The bootstrap implementations **mirror** the Python lowering
   strategies — same desugaring shapes, same identifier-naming
   convention (`__mn_base_N`, `__mn_dst_N`), same lowering paths
   (existing match/while/let machinery for Te.5.E).
3. The 11 new goldens at `tests/golden/81-91` re-run through
   `mnc-stage1` and pass. Full corpus 80/80 → 91/91.
4. **Strict 3-stage fixed point preserved.** The new `.mn`
   lowering code, when compiled into stage1 and used to build
   stage2, must produce IR byte-identical to stage3 — same as
   every release since v5.9.0 (currently at the v5.18.0
   milestone of 232,281 lines / 0-line diff).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.5.F.B** | HIGH | **Field shorthand mirror.** Relax `parse_field_init` in `mapanare/self/parser.mn` to allow value-omitted shorthand — when `:` is absent, synthesize an `Ident` value with the same name as the field. Mirror `mapanare/parser.py:1022`. No `ast.mn` change (FieldInit shape is unchanged). | 30m–1h |
| **Te.5.F.C** | HIGH | **Struct update mirror.** Add `StructUpdate` variant on `Expr` in `ast.mn`. Extend `parse_construct_expr` to accept trailing `, ..expr` plus the all-from-base `new T { ..expr }` form. Implement `lower_struct_update` in `lower.mn` — resolve struct field list from `_struct_fields`, lower base into a synthesized `__mn_base_N` tmp, fill overrides + per-field accesses for unmentioned fields. New `_struct_update_counter` field on `LowerState` (mirror Python `self._struct_update_counter`) so synthesized base tmps don't perturb the global `%tN` sequence. | 2–3h |
| **Te.5.F.D** | HIGH | **Let destructuring mirror.** Add `StructPattern(name, fields, has_rest)`, `FieldPattern(name, mutable, sub_pattern)`, and `LetDestructure(pattern, mutable, type_annotation, value)` to `ast.mn`. Extend `parse_let_stmt` to look ahead for `KW_LET KW_MUT? NAME LBRACE` and dispatch to `parse_let_destructure`. Implement `lower_let_destructure` + `emit_destructure_pattern` recursive helper in `lower.mn`. Add scope-binding logic in `semantic.mn` (`check_let_destructure` walks pattern, defines each leaf binding). Optimization: when RHS is a bare Ident already in scope, skip the synthesized base tmp. | 3–4h |
| **Te.5.F.E** | HIGH | **if-let / while-let / let-else mirror.** Add `IfLetExpr(pattern, scrutinee, then_block, else_block)`, `WhileLetStmt(pattern, scrutinee, body)`, `LetElseStmt(pattern, scrutinee, else_block)` to `ast.mn`. Extend `parser.mn` for `KW_IF KW_LET ...`, `KW_WHILE KW_LET ...`, and `KW_LET <constructor_pattern \| wildcard_pattern> ASSIGN expr KW_ELSE block`. Implement `lower_if_let`, `lower_while_let`, `lower_let_else` in `lower.mn` — synthesize equivalent MatchExpr / WhileLoop / LetBinding ASTs and dispatch to existing `lower_match` / `lower_while` / `lower_let`. Port `_block_diverges` / `_stmt_diverges` divergence helpers for D5/D6 enforcement on let-else. Pattern restriction: ConstructorPattern with 0 or 1 args (single ident or wildcard), or top-level wildcard — multi-binding deferred to v5.21.0+. | 4–6h |
| **Te.5.F.G** | HIGH | **Cross-bootstrap test.** New `tests/bootstrap/test_te5_mirror.py` re-runs the 11 v5.20.0 goldens through `mnc-stage1` and asserts byte-identical stdout vs. Python bootstrap. Safety net for the per-feature commits and a regression guard for v5.21.0+. | 1h |
| **Te.5.F.H** | LOW | **Bb.* seed refresh** if any new C-runtime export is required. **None expected** — all four features lower to existing IR ops (StructInit, FieldGet, FieldAccessExpr through MatchExpr, etc.); no new runtime functions. | — |

---

## Phase plan

**Phase 0 — Pre-implementation audit.** Run the existing v5.20.0
goldens at `tests/golden/81-91` directly against `mnc-stage1` and
record exact failure shape (parse error location and token).
Expected: each form fails at the first token that the v5.18.0-
era stage1 grammar can't accept. Write the baseline to
`docs/roadmap/v5/v5.20.1/AUDIT.md` — acceptance criterion is
that all 11 pass through `mnc-stage1` after Te.5.F.G.

Audit also confirms the bootstrap parser uses the Python
bootstrap's `_filter` / `_KEEP` token-set semantics or its own
recursive-descent equivalent. The Python parser uses Lark with
custom transformers; the bootstrap is hand-written recursive
descent. This means the LALR-disambiguation tricks the Python
side uses (e.g., the `let_dest_stmt` lookahead) translate to
explicit `peek_token()` calls in the bootstrap parser. Per-
phase guidance below documents the exact shape.

**Phase 1 — Field shorthand (Te.5.F.B).** Smallest, ship first.
Edit `parse_field_init` in `mapanare/self/parser.mn`: after
parsing `NAME`, peek for `COLON`. If present, parse value;
if absent (next token is COMMA or RBRACE), synthesize
`Ident(name)` as the value. No new AST node; `FieldInit`
shape is unchanged.

```bash
python scripts/build_stage1.py
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh --keep
```

After Phase 1: golden `81_struct_shorthand` passes through
`mnc-stage1`; goldens 82-91 still fail. Existing 80 goldens
still pass.

**Phase 2 — Struct update (Te.5.F.C).** Add `StructUpdate`
variant to `Expr` enum in `ast.mn`. Extend
`parse_construct_expr` in `parser.mn` — after parsing
field_init list, peek for `COMMA RANGE`; if present, parse
the base expression and return `StructUpdate(name, overrides,
base)` instead of `ConstructExpr`. Also accept the bare
`LBRACE RANGE expr RBRACE` form (all-from-base copy).

In `lower.mn`, add `lower_struct_update` mirroring
`mapanare/lower.py::_lower_struct_update`:
- Look up struct field list via `_struct_fields` (or imported
  equivalent).
- Validate override field names; error on unknown fields.
- Increment `_struct_update_counter` (new field on `LowerState`,
  reset in the per-fn-reset block alongside `_tmp_counter` and
  `_block_counter`).
- Synthesize `__mn_base_N` name; lower base into a Value
  registered under that name.
- Build a synthetic `ConstructExpr` filling overrides explicitly
  + `FieldAccessExpr(Ident(__mn_base_N), fname)` for unmentioned
  fields.
- Dispatch to `lower_construct` for the actual emission.

Goldens 82, 83 should now pass.

```bash
bash scripts/verify_fixed_point.sh --keep
```

**Phase 3 — Let destructuring (Te.5.F.D).** Largest single
piece. Add three AST nodes (StructPattern, FieldPattern,
LetDestructure). Extend `parse_let_stmt` with single-token
lookahead after `KW_LET KW_MUT? NAME`:

- `LBRACE` → dispatch to `parse_let_destructure`.
- `COLON` or `ASSIGN` → continue to existing `parse_let_stmt`.

Implement `parse_struct_dest_pat`, `parse_field_dest_list`,
`parse_field_dest`. The `field_dest_list` accepts both the
`field_dest (COMMA field_dest)* (COMMA RANGE)? COMMA?` form
and the `RANGE COMMA?` rest-only form.

In `lower.mn`, add `lower_let_destructure`:
- If RHS is bare Ident already in scope, skip the synthesized
  base tmp and run accesses directly on the source name (IR
  byte-identical to `let x = p.x; let y = p.y`).
- Else, lower RHS into `__mn_dst_N` via a synthetic `LetBinding`
  (reuses `lower_let`'s type-annotation patching).
- Recursive helper `emit_destructure_pattern`: per leaf
  FieldPattern, emit `let [mut] <name> = base.<field>`; per
  nested sub-pattern, emit a fresh `__mn_dst_M` then recurse.

In `semantic.mn`, add `check_let_destructure` that defines
each leaf binding in the current scope with mutability
propagated. Field-name validation deferred to lower time.

Goldens 84, 85, 86, 87 should now pass.

```bash
bash scripts/verify_fixed_point.sh --keep
```

**Phase 4 — if-let / while-let / let-else (Te.5.F.E).** Three
new AST nodes; three new lowering paths; the let-else
divergence helper. Hardest phase because of the let-else
divergence semantics; easiest because the lowerings desugar
to existing primitives.

For each form, the parser change is small (extend `parse_if_expr`
to detect `KW_IF KW_LET`, extend `parse_while_stmt` for
`KW_WHILE KW_LET`, extend `parse_let_stmt` for the
`KW_LET <pattern> ASSIGN expr KW_ELSE` shape). The `let_else`
pattern is restricted to ConstructorPattern or WildcardPattern
to avoid LALR-equivalent ambiguity with the simple `let_stmt`
(`let x = expr else { ... }` would be ambiguous if x is a bare
ident).

Lowering — for each form, synthesize an equivalent
MatchExpr/WhileLoop/LetBinding AST and dispatch to the existing
`lower_match` / `lower_while` / `lower_let`. No new MIR ops.

Divergence helper — port the Python `_block_diverges` /
`_stmt_diverges` / `_expr_or_block_diverges` to `lower.mn` (or
a new `divergence.mn` if cleaner). Recognizes ReturnStmt,
BreakStmt, ContinueStmt, calls to `panic`/`abort`/`exit`, and
nested if/match where every leaf branch diverges. The
function's implicit return does NOT satisfy divergence.

Goldens 88, 89, 90, 91 should now pass. Full corpus 91/91.

```bash
bash scripts/verify_fixed_point.sh --keep
bash scripts/build_from_seed.sh
```

**Phase 5 — Cross-bootstrap test (Te.5.F.G).** Add
`tests/bootstrap/test_te5_mirror.py` mirroring the v5.15.1
`test_comprehension_mirror.py` shape. Each of the 11 v5.20.0
goldens runs through both Python (`mapanare emit-llvm` →
`clang` → run) and native (`mnc-stage1` → `clang` → run); the
test asserts byte-identical stdout. Catches semantic drift
between the two compilers and acts as regression guard for
v5.21.0+.

**Phase 6 — Closeout.** SESSION_REPORT, CHANGELOG entry,
CLAUDE.md release-notes entry. Drop the v5.20.0 "deferred to
v5.20.1" note from `STRUCT_ERGO_DESIGN.md` and replace it with
a "shipped in v5.20.1" link. SPEC.md needs no change (the
language specification is bootstrap-agnostic).

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Strict 3-stage fixed point breaks during Phase 2/3/4 | MEDIUM | Per-phase validation is explicit. If a phase breaks fixed point, isolate by reverting that phase and re-running — earlier phases alone don't fire the new code paths because `mapanare/self/*.mn` source uses none of the new forms. |
| Bootstrap synthesizer diverges from Python on an edge case | MEDIUM | Te.5.F.G cross-bootstrap test catches this. The 11 v5.20.0 goldens give the oracle. |
| New `_struct_update_counter` not reset between functions | MEDIUM | Per-function reset in `lower.mn` already resets `_tmp_counter` + `_block_counter`; add the new counter to the same block. Mirror Python lines `mapanare/lower.py:984-987`. |
| Bootstrap parser lacks single-token-lookahead idiom needed for `let_stmt` / `let_dest_stmt` disambiguation | LOW | Bootstrap parser is recursive descent; `peek_token()` is the standard idiom and is already used elsewhere. The Python LALR disambiguation collapses to `if peek == LBRACE: parse_dest else: parse_simple`. |
| `let else` pattern restriction (ConstructorPattern \| Wildcard only) leaks into source-level error messages awkwardly | LOW | Phase 4 includes a clear error message: "let-else: pattern must be a constructor pattern (Some/Ok/Err/...) or wildcard". |
| Divergence helper recursion infinite-loops on cyclic AST | LOW | The Python helper has no recursion guard but trusts the AST is acyclic (which it is — Mapanare AST is a tree). Bootstrap port preserves this assumption. |
| `lower_match` synthesis from `lower_let_else` produces non-deterministic IR | MEDIUM | Mirror Python's exact AST construction order: success arm first, wildcard arm second. Pattern arg ordering uses list iteration (deterministic). If non-determinism surfaces, audit `LowerState` field iteration for hash-ordered access. |
| Bootstrap `lower_let` doesn't yet handle a synthetic `value=MatchExpr` for the `let-else` desugaring | LOW | `lower_let` calls `lower_expr` on `let.value`; `MatchExpr` is already a recognized expr kind. The phi-result type from match becomes the let's value type; if type inference falls short, add the same type-annotation-patching path Python uses (`lower.py:1310-1325`). |
| `parse_construct_expr` ambiguity between `, ..expr` and end-of-fields | LOW | Single-token lookahead at COMMA: if next token is RANGE, it's the base; otherwise it's another field_init. Mirror `mapanare.lark` rule `(COMMA field_init)* (COMMA RANGE expr)?`. |
| Bb.* seed refresh required | LOW | None of Te.5 introduces a new C-runtime export. The Python bootstrap added zero new runtime functions per `v5.20.0/SESSION_REPORT.md` "Zero new MIR ops, zero new runtime functions, zero new IR shapes". Bootstrap mirror should also add zero. |

---

## Out of scope (deferred)

- **Multi-binding `let else` patterns** (`let Pair(a, b) = pair
  else { ... }`) — same as v5.20.0; deferred to v5.21.0+.
- **`if let` chains** (`if let X = a && let Y = b`) — Te.5
  D7 deferred indefinitely.
- **Default-value shorthand** (`Point { x = 0, y }`) — Te.5
  D10 deferred.
- **Tuple destructuring** (`let (x, y) = t`) — Mapanare tuples
  are surface-only; not in v5.20.0 either.
- **Self-host source rewrites** to use any of the new forms —
  v5.20.1 only adds parser/lower capability; `mapanare/self/*.mn`
  source remains Te.5-form-free, which is what preserves the
  v5.18.0 fixed-point milestone by construction.
- **Match-side struct patterns at parity with `let`** — D3 said
  "ships in v5.20.0 too" but with lower test coverage; v5.20.1
  doesn't widen this. Match-side StructPattern parity ships in
  v5.21.0+ if gaps surface.
- **Native `mnc fmt --to-terse` rewriter for the new forms** —
  Te.5.H (deferred from v5.20.0). The new forms cannot be
  safely auto-migrated from old → new (requires semantic
  knowledge); leave the formatter as-is.

---

## Success criteria

- `mnc-stage1` compiles every Te.5 form the Python bootstrap
  accepts. Cross-bootstrap test (Te.5.F.G) green on all 11
  v5.20.0 goldens.
- Goldens 81-91 pass through `mnc-stage1`. Full corpus
  80/80 → 91/91.
- **Strict 3-stage fixed point preserved.** stage2.ll ==
  stage3.ll at every per-phase commit. v5.18.0 milestone
  (232,281 lines / 0-line diff) preserved or expanded by the
  Te.5.F additions.
- `bash scripts/build_from_seed.sh` succeeds.
- `make lint` clean.
- The 11 v5.20.0 goldens that fail through stage1 today now
  pass.

---

## What it unblocks

- **v5.21.0 (Te.6)** can land small ergonomic wins (chained
  comparisons, etc.) with confidence that the bootstrap already
  accepts every v5.20.0 surface form.
- **v5.21.0+ Te.5 follow-ups** — multi-binding let-else, if-let
  chains, etc. — can be added on either compiler in tandem
  rather than forking the surface.
- **Future self-host rewrites** that introduce any of the four
  Te.5 forms into `mapanare/self/*.mn` (none planned for
  v5.21.0; explicit follow-up work) can use either compiler as
  the bootstrap.
- **`mnc fmt --to-terse`** stays purely whitespace-conservative
  per v5.13.0 design; v5.20.1 adds no auto-rewrite (and v5.20.0
  already locked the "no auto-migrate from old → new" rule).
