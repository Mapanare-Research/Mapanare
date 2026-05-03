# v5.15.1 — Phase 0 Audit

**Date:** 2026-04-29
**Goal:** Document the v5.15.0-HEAD failure shape that v5.15.1 must
close, plus prerequisite checks for Phase 3 (lowerer port).

---

## Baseline state

- VERSION = `5.15.0`.
- Goldens through `mnc-stage1`: **68/68 PASS** (matches v5.15.0
  release notes; corpus unchanged).
- Strict 3-stage fixed point: holds (the v5.9.0 milestone).
- `tests/test_comprehensions.py`: 11 cases, **Python-only**.

## Failure shape on `mnc-stage1`

List comprehension:

```
$ cat /tmp/list.mn
fn main() {
    let xs: List<Int> = [1, 2, 3, 4, 5]
    let doubled: List<Int> = [x * 2 for x in xs]
    print(str(len(doubled)))
}
$ mapanare/self/mnc-stage1 emit-llvm /tmp/list.mn -o /tmp/x.ll
parse error: expected RBRACKET but got KW_FOR
```

Map comprehension:

```
$ cat /tmp/map.mn
fn main() {
    let m: Map<Int, Int> = #{ k: k * 2 for k in 0..5 }
    print(str(len(m)))
}
$ mapanare/self/mnc-stage1 emit-llvm /tmp/map.mn -o /tmp/x.ll
parse error: expected RBRACE but got KW_FOR
```

Both match the PLAN's expectation: `parse_list_lit` rejects the
`for` after the first element; `parse_map_lit` rejects the `for`
after the first `k: v` pair. Acceptance criterion for v5.15.1: every
case in `tests/test_comprehensions.py` (11 total — 4 parse-only,
5 e2e via LLVM, 1 IR-shape, 1 nested) compiles through `mnc-stage1`.

## Prerequisite checks (Phase 3)

Confirmed present in `mapanare/self/lower.mn`:

- `lower_let` (line 743) — has `lower_let_list_hint` integration; sets
  up alloca + Store for the bound name. **Has** the empty-`ListLit`
  annotation patch path already (via `lower_let_list_hint` →
  `lower_list_typed_into`).
- `lower_assign` (line 3856) — handles `tk == "index"` by emitting
  `IndexSet` (line 3923-3932). This is the same path used for map
  writes `m[k] = v`, so the synthesized `Assign(Index(__r, k), "=", v)`
  for map comp will lower correctly.
- `lower_for` (line 1033) — counter-based loop on Range; what we use
  for the synthesized `for __i in 0..len(xs)`.
- `lower_stmt` (line 687) — dispatches `for` and `let` correctly.
- `fresh_tmp` (lower_state.mn:60), `tmp_counter` field on
  `LowerState` (lower_state.mn:15) — ready for accumulator naming.
- `define_var` / `lookup_var` (lower_state.mn:176/185) — for binding
  and recovering the accumulator after the synthesized loop runs.

### Gap requiring patch in Cb.5

The bootstrap **does not** have an empty-`MapLit` annotation patch
analogous to the Python v5.15.0 path at `lower.py:1289-1301`. For
list comp, the synthesized init is `ListLit([])` and is already
covered by `lower_let_list_hint`. For map comp, the synthesized
init is `MapLit([])` and the bootstrap's `lower_map` (line 3698)
falls back to `mir_string()` / `mir_unknown()` for empty maps. We
need a parallel hint path keyed on `Map<K, V>` annotation when the
RHS is `Comprehension(kind="map", ...)`.

The simplest implementation: add a `comp_type_hint: Option<TypeExpr>`
field to `LowerState`; have `lower_let` set it before recursing into
a Comprehension RHS; the new `lower_comprehension` reads it back to
patch the synthesized inner Let's annotation; clear it on entry so
nested comprehensions don't inherit. After the synthesized inner
Let runs, post-hoc patch the `MapInit` instruction's `key_type` /
`val_type` from the type-hint args (mirror of Python lower.py:1295-1301).

### Map-of-`Comprehension`: re-use synthesizer

For the empty-MapLit patch we will inject inside `lower_comprehension`
itself (since we already know the kind == "map" and the synthesized
init is `MapLit([])`). No need to also patch `lower_let` for the
MapLit(empty)+Map<K,V> case in general — that case can still occur
without comprehensions, but it is **not** in v5.15.1 scope (no
existing test exercises it; the real corpus uses non-empty MapLits).

## Map iteration in `mnc-stage1`

Confirmed: `lower_for` already detects `iter_r.value.ty.kind ==
TK_MAP()` and dispatches to `lower_for_map`. The non-range branch
of `_wrap_comp_for` emits `for __i in 0..len(xs) { ... }` — never
hits map-iteration in the synthesizer, since maps as iterables in
comprehensions go through `for k in m_keys`-style sources. Not
load-bearing here; just confirming no edge in the new code.

## Items that route through C runtime

None expected. Comprehension synthesis only constructs:
- `ListLit([])` / `MapLit([])` (existing)
- `MethodCall(Ident, "push", [...])` (existing)
- `Assign(Index(...), "=", ...)` (existing)
- `For(target, Range(0, Call("len", [src])), body)` (existing)
- `Let(name, mut, type_ann, value)` (existing)
- `If(cond, body, None)` (existing)

No new builtins, no new C runtime exports, no Bb.* seed refresh.

## Acceptance summary

- Phase 1 (Cb.1) keeps fixed point: adding an unused enum variant.
- Phase 2 (Cb.2/Cb.3) keeps fixed point: new branches fire only on
  comprehension syntax; `mapanare/self/*.mn` source uses none.
- Phase 3 (Cb.4/Cb.5) keeps fixed point: synthesizer threads
  through existing lowerers; no edits to shared helpers.
- Phase 4 (Cb.6) — cross-bootstrap test re-runs the 11 v5.15.0
  cases via stage1.
- Phase 5 (Cb.7) — three new goldens 69/70/71. Corpus 68 → 71.
