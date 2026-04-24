# v5.6.7 — Ve.2 partial — lowerer elem_ty propagation + list_init dispatch fix

**Status:** SHIPPED (partial Ve.2 closure)
**Breaking:** No
**Date:** 2026-04-24

## Headline

**Empty-list element type now propagates from `let` annotations**,
eliminating 95% of the 384-byte fallback allocations that v5.6.5 left
behind: **387 → 18 `__mn_list_new(i64 384)` sites** (−369, −95%).
`emit_list_init_checked`'s struct-reinterpretation heuristic was
misfiring on correctly-typed `List<Struct>` literals — fixed with a
`dest.ty.kind == TK_LIST()` short-circuit.

**Not fully closed:** stage3.ll still empty. stage2 continues to OOM
on non-trivial programs — the garbage-size symptom traces to
`__mn_str_concat` in `llvm_alloca`, a separate memory-read corruption
that survives the elem_ty fix. Not a v5.6.7 regression; same failure
mode as v5.6.4 / v5.6.5 but with shrunken blast radius. Scoped for
v5.6.8+ as Ve.3 (or continued Ve.2 investigation).

## What shipped

### lower.mn — elem_ty propagation

**`lower_list_typed(st, elements, hinted_elem_ty)`** — new variant
of `lower_list` that takes an explicit element-type hint. When the
literal is empty, the hint overrides the default `mir_unknown()`
fallback.

**`extract_list_elem_ty(st, te: TypeExpr) -> MIRType`** — unwraps a
`Generic("List", [inner])` annotation to return `inner` as a MIRType.
Returns `mir_unknown()` for any other shape, so callers fall through
to the default path.

**`lower_let_list_hint(st, value, type_ann)`** — wraps the pattern
check (`value is list_lit AND type_ann is Some(Generic("List", _))`)
into a single helper. Returns the element hint or `mir_unknown()`.

**`lower_let` rewired** (`lower.mn:741-776`): when the pattern matches,
route through `lower_list_typed` with the extracted hint instead of the
generic `lower_expr` → `lower_list` path. The latter sees only the
value expression and produces MIR with `elem_ty.kind=TK_UNKNOWN` for
empty literals, which downstream `resolve_mir_type` maps to `"i64"` —
`emit_list_init` then either allocates 8-byte slots for 16-byte
Strings (corruption) or falls back to 384 bytes (wasteful).

`lower_list` itself is now a one-line wrapper: `return
lower_list_typed(st, elements, mir_unknown())`. All existing callers
(list expressions in non-let contexts) continue unchanged.

### emit_llvm.mn — dispatch fix

**`emit_list_init_checked`** (`emit_llvm.mn:1432-1466`): a latent
bug was exposed by the lowerer fix. Before v5.6.7, empty `List<T>`
literals had `elem_ty.kind=TK_UNKNOWN` and `elem_ty.name=""`, so
`find_struct_entry(st, "")` returned `None` and emission proceeded
normally. With the v5.6.7 hint carrying `elem_ty.name = "IndexItem"`
(or any struct name), the second heuristic in `emit_list_init_checked`
— "if elem_ty.name matches a registered struct, treat as struct_init"
— misfired and dropped the entire ListInit, leaving the destination
`%t5` undefined at every use site (llvm-as rejected with `error: use
of undefined value '%t5'`).

Fix: short-circuit when `dest.ty.kind == TK_LIST()`. The destination
is definitively a list (set by `make_value(s, mir_list(), "t")` in
`lower_list_typed`), so the struct-reinterpretation heuristic — added
to handle cases where the lowerer mis-typed a struct literal — does
not apply.

## Metrics

| Gate | v5.6.5 | v5.6.7 | Δ |
|---|---:|---:|---:|
| `__mn_list_new(i64 384)` hardcoded | 387 | 18 | **−95%** |
| `__mn_list_new(i64 %elem.sz)` dynamic | 49 | ~400 | +8× |
| stage2.ll lines | 207,039 | 207,616 | +0.28% |
| stage2.ll `llvm-as` | OK | OK | — |
| ASan on `mnc_all.mn`: heap-buffer-overflow | 0 | 0 | — |
| goldens harness | 64/66 | 64/66 | — |
| `make lint` | clean | clean | — |
| `check_struct_registry.py` | 23/23/91 | 23/23/91 | — |
| stage3.ll non-empty | ❌ | ❌ | Ve.3 scope |

## What's still blocking fixed-point

The remaining 18 × 384-byte floor sites are `ListInit` instructions
emitted in contexts that don't route through `lower_let` — e.g.,
empty list literals inside struct field defaults, function
argument positions, return expressions. Each would need a similar
hint-propagation fix in its respective lowerer entry point:

- `lower_struct_init` — struct field defaults with empty list
- `lower_call` — empty list argument to a parameter whose declared
  type is `List<T>`
- `lower_return` — empty list return whose function declared return
  type is `List<T>`

These are bounded but non-trivial — each site needs to thread the
expected type down from the context. Scoped for v5.6.8+ once the
stage2 runtime OOM is understood (the OOM blocks validation of
further lowerer fixes via fixed-point, so it's the priority
dependency).

The stage2 runtime OOM (tracked as Ve.3) — `__mn_str_concat` in
`llvm_alloca` reads a corrupted `len` field. Stack:

```
__mn_alloc(corrupt_size)
__mn_str_concat
llvm_alloca           -- mapanare source: "  %X = alloca Y"
emit_mir_by_kind
```

`llvm_alloca` concatenates `"  "`, value name, `" = alloca "`, and
resolved type. One of these strings has a garbage `len`. Root cause
is somewhere upstream — likely a struct field read via the wrong
offset, or a List<T> whose elem_size is inconsistent between writer
and reader.

## Risks — mitigated or deferred

- **R1 — New helper fns break existing callers.** `lower_list` is now
  a one-line wrapper that delegates to `lower_list_typed` with
  `mir_unknown()`. Existing call sites (list expressions outside
  `let`-annotated contexts) get byte-identical behavior. Verified
  by 64/66 goldens preserved.
- **R2 — `emit_list_init_checked` short-circuit misses legitimate
  struct-init mis-lowering cases.** The short-circuit only triggers
  when `dest.ty.kind == TK_LIST()`. If the lowerer correctly typed
  the dest as a struct (`TK_STRUCT`), the struct-init heuristic still
  fires. Only ListInit MIR with list-typed destinations skip the
  heuristic — which is the correct semantics.
- **R3 — stage3.ll still empty.** Not regressed from v5.6.5; same
  status, narrower blast radius. Explicitly scoped for Ve.3 in
  `known_issues.md`.

## What's next

- **v5.6.6** (scheduled) — Rt.04 guard-lift. Unchanged.
- **v5.6.8** (NEW) — **Ve.3 — trace + fix stage2 runtime OOM.** The
  `__mn_str_concat` from `llvm_alloca` reads a corrupted size. Likely
  root causes: (a) MIR Value's String `name` field read at wrong
  offset, (b) List<Struct>'s elem_size inconsistent, (c) a third
  hardcoded-fallback site we haven't hit yet. Investigation starts
  with a valgrind/ASan trace of stage2 on `p1.mn` to identify the
  exact corrupted read.
- **v5.6.9+** (future) — additional `lower_list_typed` routing from
  `lower_struct_init`, `lower_call`, `lower_return` to reduce the
  remaining 18 × 384-byte floor sites to 0.
- **v5.7.0** — Sh.7 + or-pattern → 66/66. Unchanged.

## Key insight

The compounding nature of pre-existing bugs makes self-hosting
stage-2-gated releases fragile. v5.4.4's attempt to close Ve.1
regressed because of layered bugs (fallbacks masking fallbacks
masking fallbacks); v5.6.5 closed one layer; v5.6.7 closed another;
v5.6.8 will close the next. Each release narrows the blast radius
and documents the remaining layers. Per user directive ("no cheap
shit that bites us later"), progress is incremental and honest —
no declaring closure until stage3.ll is genuinely non-empty and
llvm-as-clean.
