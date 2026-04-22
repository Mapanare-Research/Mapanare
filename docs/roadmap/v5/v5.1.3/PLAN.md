# Mapanare v5.1.3 — "Own.1 Phase 1: Drop-Glue Ownership Enforcement"

> **The "C has to be written perfect" ceiling starts coming down.**
> Viper has flagged Own.1 every panel since v4.99.0 and scored 9.6
> EXCEEDS with an explicit 9.6 ceiling for "a language with manual
> ownership tracking." This release doesn't build a full borrow
> checker — but it closes the specific UAF class at
> `lower.mn::register_struct` / `register_enum` that Viper keeps
> documenting.

**Status:** PLANNED (skeleton)
**Breaking:** Potentially — strict ownership checks may reject code
that previously compiled by accident
**Prerequisite:** v5.1.2 shipped
**Estimated work:** 3-5 sessions

---

## Why this release exists

Viper v4.144.0 line 300+ and v4.154.0 line 222-230:

> `register_struct` / `register_enum` in `lower.mn:315-375` build
> local lists, transfer ownership to module state via
> `module_push_struct`, then return. The local variables' epilogue
> drop-glue fires on buffers already transferred to the module state.
> In Rust, the borrow checker would prevent this. Mapanare's
> assignment semantics run drop-glue on the old value before binding
> the new — this is a double-free scenario that only the allocator's
> behavior masks.

And:

> The ceiling remains 9.6 for a non-Rust language doing manual
> ownership management across 8,000+ lines of C runtime.

Viper's complaint has two tiers:

1. **Specific:** `register_struct` / `register_enum` double-free
   latent bug
2. **General:** no borrow checker in the language at all

Tier 2 is a language-level rewrite — v5.x+ scope at best, probably
v6.0. Tier 1 is a compiler-enforced check — achievable now.

Cobra v4.154.0 line 206-209 agrees:

> The perf arc opened 3 new LOWs (In.1, Li.1, Ea.1) and closed 0
> existing ones. … Net movement in my domain is negative.

Own.1 has been on every panel's carry-forward since v4.99.0. It's
literally **28 releases** since it was first named and still sitting
open. This release starts chipping at it.

## What Own.1 actually is (deep-dive)

The pattern at `mapanare/self/lower.mn:315-375` (approximate — line
numbers drift between releases):

```mapanare
fn register_struct(st: LowerState, name: String, fields: List<FieldInfo>) {
    let entry: StructEntry = make_struct_entry(name, fields)
    module_push_struct(st.module, entry)    // transfers ownership
    // fields is now owned by the module
    // BUT: fields as a local variable still reaches function epilogue
    // epilogue generates drop-glue for `fields` → double-free of
    // the backing buffer
}
```

Runtime accident: the underlying allocator zero-fills the
newly-allocated struct's `data` pointer before drop-glue reads it,
so the free silently no-ops. This is valgrind-invisible in most
layouts but resurfaces as Ge.1r (v4.154.0) when binary layout
changes the allocator's pointer reuse.

The fix is **not** a runtime fix. It's a compiler-enforced check:
when a value is passed by-move to a function that takes ownership,
suppress drop-glue in the caller's epilogue for that local. This
is what Rust's move semantics do at the compiler level without
runtime cost.

## Scope

### Phase 1 — Detect the move pattern

In `mapanare/semantic.mn` or `mapanare/lower.mn`, add a move-by-name
attribution: when an argument is passed to a function annotated
`@takes_ownership` (or by position — if the callee's parameter type
is `@move`), mark the caller's local as "moved." The MIR lowerer
emits a marker instruction; the drop-glue emitter skips moved locals.

Start with a single attribute recognizing site: `module_push_struct`
and `module_push_enum`. Tag their `entry` parameter as
`@takes_ownership`. Callers of these functions get the move check
automatically.

### Phase 2 — Emit drop-glue skip

Currently `emit_llvm.mn::emit_drop_glue` walks all live locals at
function exit and emits `__mn_list_free` / `__mn_string_free` etc.
Add a `moved_locals` set to `EmitState`; the move-marker instruction
populates it; drop-glue checks membership before emitting.

### Phase 3 — Port to Python bootstrap

Mirror into `mapanare/lower.py` + `mapanare/emit_llvm_text.py`.
Critical: Python/self-hosted parity. Don't create a new Cb.15 class.

### Phase 4 — Retrofit known sites

Audit `mapanare/self/lower.mn` for the pattern Viper described —
any function that builds a local aggregate, passes it to a
"push"-style sink, and returns. Tag each such sink parameter.

Candidate sites (grep from Viper's flags across 28 releases):
- `register_struct`, `register_enum` — primary targets
- `register_trait`, `register_impl` — same pattern?
- `emit_state_push_function` — likely same
- Any `..._push_` function in `mir.mn`, `mir_builder.mn`

### Phase 5 — Tests

- `tests/native/test_own1_register_struct.py` — valgrind + ASan on
  a program that registers 1000 structs; assert 0 leaks and 0 UAFs
- `tests/semantic/test_move_semantics.py` — assert compile-time
  errors when a moved local is re-used after the move point
- Re-run the Ge.1r goldens (26/29/30/31); assert valgrind ERRORS stay
  at 0 (they should — Ge.1r and Own.1 are the same class)

### Out of scope

- Full borrow checker / reference-lifetime tracking (v6.0)
- `&mut` exclusivity enforcement
- Compile-time prevention of the COW-refcount single-threaded
  assumption Viper flagged at v4.154.0 line 262-289
- User-facing `@move` annotation in surface syntax (use `@takes_ownership`
  as compiler-internal attribute first; surface later)

## Exit criteria

1. `grep -n '@takes_ownership' mapanare/self/lower.mn` → at least 2
   matches (`module_push_struct`, `module_push_enum`)
2. `tests/native/test_own1_register_struct.py` passes under ASan
   (0 errors) and valgrind (0 ERRORS)
3. Ge.1r goldens (26, 29, 30, 31) stay at 0 valgrind ERRORS — v5.1.1
   closed them; v5.1.3 must not re-open
4. Cross-language benchmark geomean ≤ 1.05× (this release's
   drop-glue skip reduces instruction count in the stage2 binary
   slightly — possibly a small perf win)
5. Strict 3-stage fixed point holds
6. PARITY_GAPS.md: Own.1 moves to a new "Ceiling items, partially
   addressed" section (not Historical — the general borrow checker
   complaint stands)

## Risks

**Risk 1 — suppressing drop-glue creates leaks.**
If the move analysis is too aggressive (marks a local as moved when
the callee doesn't actually take ownership), the caller skips
drop-glue and leaks the buffer.
*Mitigation:* valgrind + ASan must be 0-errors across all goldens
*and* `benchmarks/`. This is the primary safety gate.

**Risk 2 — fixed point breaks.**
New move-marker instructions in MIR, new skip-paths in drop-glue
emission — either could ripple through self-compilation in a way
that breaks stage2==stage3 byte-identical.
*Mitigation:* Python/self-hosted parity must land in the same
release. If Python-only ships first, stage1 and stage2 diverge.

**Risk 3 — existing code relied on the double-free-masked-by-alloc
behavior.**
Some user code might get its state corrupted by the now-enforced
no-drop-after-move. Blast radius unknown but nonzero.
*Mitigation:* the primary change point is internal compiler
functions (`register_struct` etc.) not user-facing APIs. Surface-level
Mapanare code is unaffected unless it also had latent double-frees,
in which case we're surfacing a bug — acceptable.

**Risk 4 — this is bigger than it looks.**
Estimated 3-5 sessions may be optimistic. Viper's been flagging it
for 28 releases because it's genuinely hard. If the phase 1 detection
design turns out to need dataflow analysis beyond the current MIR
framework, the release splits: v5.1.3 does Phase 1 design +
register_struct fix only; v5.1.4+ extends.

## Rollback

If the ownership check proves unstable: revert the `@takes_ownership`
attribute recognition; the drop-glue emitter's new `moved_locals`
check becomes dead code (skips membership on an always-empty set).
Safe revert. Own.1 stays open; v5.1.3 slot reused for v5.1.4's
original Perf.2 content (lazy threads).
