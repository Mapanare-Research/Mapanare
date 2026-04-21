# Mapanare v4.139.0 — SPEC + language close (Coral's 8.7 → 9.1 delta)

> Close every Coral carry-forward from v4.136.0. Two parser/grammar
> fixes, one SPEC decision, two one-line SPEC edits. No compiler
> codegen changes; parser + semantic + SPEC only.

**Status:** PLANNED
**Breaking:** No (one grammar extension adds accepted inputs — pure
widening; one SPEC decision that formalizes existing behavior)
**Prerequisite:** v4.138.0 (docs swept)
**Estimated work:** 1 sprint
**Theme:** Coral's carry-forward empty.

---

## Why this release

Coral's review raised 3 open v5.x dockets (Gr.1, Gr.2, Sem.1) plus
two SPEC hygiene items (§0 stale line, Co.1 "compiler compiles
itself" precision). v5.0.0 shouldn't ship with the SPEC describing
dead code paths, and Gr.2 is actively blocking `stdlib/gpu/` module
compilation — the one user-visible gap that a v5 user would trip
on immediately.

---

## Scope

### Gr.2 — qualified type refs in type position (MEDIUM)

**Source**: `.reviews/v4.136.0/05-coral.md`. Blocks
`stdlib/gpu/tensor.mn:90` and `stdlib/gpu/kernel.mn:63`.

`mapanare/mapanare.lark` grammar `type_expr` accepts bare names but
not `module.Name` or `Module.Type`. Examples like `gpu.Device` or
`Kernel.Handle` parse-error.

Fix: extend `type_expr` rule in `mapanare.lark` to accept
`NAME ("." NAME)*`. Corresponding AST node (likely `TypeRef` or
`TypeName`) gains a `module_path: List[str]` field or a `qualified:
bool` flag.

Self-hosted `mapanare/self/parser.mn` and `mapanare/self/ast.mn`
mirror the change.

### Sem.1 — module-level `let mut` (LOW)

**Source**: v4.129.0 EXAMPLES_REPORT Cat. E.

SPEC §2.1 says `let mut` is local-scoped. At module scope it's
currently accepted by the parser but semantically under-specified.

**Decision to make in this release**: either (a) SPEC §2.1 adds
"module-level `let mut` is permitted; initialization evaluates at
program start; concurrent access is the user's responsibility" and
semantic.py / semantic.mn accept it explicitly — OR (b) parser
rejects module-level `let mut` with a named diagnostic pointing at
`const` for module-level immutables.

Recommend (b): it's simpler, and `const` is already the canonical
module-level immutable. `let mut` at module scope is almost always
accidental. Diagnostic: `"E420: 'let mut' is block-scoped. Use
'const <name> = ...' at module scope."` with a fix-it suggestion.

### Coral §0 SPEC stale line (LOW, 1-line fix)

`docs/SPEC.md:6` says "A legacy Python transpiler backend exists."
Appendix B already documents the v4.58.0 deletion. Delete the line.

### Co.1 — "compiler compiles itself" precision (LOW)

After v4.134.0's strict 3-stage fixed point, the README + SPEC can
upgrade the phrasing from "compiles user programs" to "reaches
byte-identical 3-stage fixed point." One paragraph in SPEC §B.
Cross-linked to `FIXEDPOINT_STATUS.md`.

### Dr.1 — self-hosted hardcoded version string (LOW)

`mapanare/self/emit_llvm.mn:3523` emits `!0 = !{!"4.127.0"}`. Update
to `!"4.139.0"` (or parameterize from the VERSION file via Python
build-time injection — preferred, removes the drift class).

---

## Phase 1 — Grammar: Gr.2 qualified type refs

1. `mapanare/mapanare.lark`: extend `type_expr` production.
2. `mapanare/ast_nodes.py`: `TypeRef.module_path: List[str]` or
   `TypeRef.qualified_name: str`.
3. `mapanare/parser.py::_visit_type_expr`: populate the path.
4. `mapanare/semantic.py::_resolve_type_ref`: look up via
   `module_path` when present.
5. `mapanare/lower.py`: pass through.
6. Self-hosted mirror: `mapanare/self/parser.mn`, `ast.mn`,
   `semantic.mn`, `lower_state.mn`.
7. Regression golden: `tests/golden/66_qualified_type_ref.mn`.
8. Unblock `stdlib/gpu/tensor.mn:90` and `kernel.mn:63`.

## Phase 2 — Semantic: Sem.1 module-level `let mut` decision

- SPEC §2.1 update: "`let mut` is block-scoped. Module-level mutable
  state uses `signal` or is disallowed."
- `mapanare/semantic.py::_check_toplevel`: reject module-level
  `let mut` with diagnostic code `E420` and fix-it.
- Update the ~3 tests/examples that were relying on parser-accept-but-
  semantic-undefined behavior (either convert to `const` or to signal).

## Phase 3 — SPEC §0 stale line

One-line delete in `docs/SPEC.md:6`. That's it.

## Phase 4 — Co.1 precision pass

`docs/SPEC.md` Appendix B: add a paragraph on the v4.134.0 strict
3-stage fixed point. Cross-link `docs/roadmap/v4/v4.135.0/FIXEDPOINT_STATUS.md`.
Mirror in `README.md` intro where it says "compiles itself."

## Phase 5 — Dr.1 version string propagation

Either:
- (a) Bump `mapanare/self/emit_llvm.mn:3523` to `!"4.139.0"` (one-line;
  will drift again at v4.140.0).
- (b) **Better**: `scripts/build_stage1.py` injects VERSION from the
  top-level `VERSION` file into the emitted IR's metadata at build
  time, so the hardcoded string is replaced with a token that
  `build_stage1.py` substitutes. Removes Dr.1 as a class.

Prefer (b).

## Phase 6 — Verify

```bash
python3 -m pytest tests/parser/ -v -n auto              # grammar tests
python3 -m pytest tests/semantic/ -v -n auto             # let mut diagnostic
python3 -m pytest tests/test_spec.py -v                  # SPEC crossref
python3 -m pytest tests/ --ignore=tests/bootstrap -q     # full baseline

# New golden
python3 scripts/test_native.py --filter 66_qualified_type_ref -v

# Goldens overall: 53 → 54 (expect +1 from new qualified type ref test)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -5

# Fixed-point
bash scripts/verify_fixed_point.sh --keep

# stdlib/gpu/ compiles now
python3 -m mapanare check stdlib/gpu/tensor.mn
python3 -m mapanare check stdlib/gpu/kernel.mn
```

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | Grammar accepts `gpu.Device` / `Kernel.Handle` in type position | yes |
| 2 | `stdlib/gpu/tensor.mn` + `stdlib/gpu/kernel.mn` compile clean | yes |
| 3 | Module-level `let mut` triggers named diagnostic (or accepted + specified — pick one in SPEC) | yes |
| 4 | SPEC §0 stale "legacy Python transpiler" line deleted | yes |
| 5 | SPEC Appendix B describes v4.134.0 fixed-point | yes |
| 6 | README "compiles itself" wording sharpened | yes |
| 7 | Dr.1 — self-hosted version string either bumped (a) or parameterized (b) | yes |
| 8 | New golden `66_qualified_type_ref.mn` passes through mnc-stage1 | yes |
| 9 | Self-hosted fixed-point holds (md5 may change — regenerate reference) | yes |
| 10 | Non-bootstrap pytest baseline hold + new tests | yes |
| 11 | Gr.2, Sem.1, §0, Co.1, Dr.1 all CLOSED in DOCKET_LEDGER.md | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Grammar change breaks existing single-name type refs | low | high | LALR conflict check; regression tests for `Int`, `List<Int>`, `Option<T>` |
| Self-hosted parser mirror diverges from Python (fixed-point break) | medium | medium | Build-stage1 + verify_fixed_point.sh gate; hold release if md5 diverges |
| Sem.1 rejection breaks real user code | medium | low | Grep repo + stdlib for module-level `let mut`; convert callers first |
| Dr.1 path (b) introduces build-time substitution brittleness | low | low | If complex, ship (a) this release and scope (b) as infra work |

## What this release does NOT do

- Does not touch the runtime.
- Does not close Gr.1 (multi-line literals) — requires lexer work;
  v5.x.
- Does not close Sh.4/Sh.5/Sh.6/Sh.7 — self-hosted emitter features;
  v5.x.
- Does not refactor the type system.

## Score-impact forecast

Coral 8.7 → 9.1 at v4.143.0 panel.
