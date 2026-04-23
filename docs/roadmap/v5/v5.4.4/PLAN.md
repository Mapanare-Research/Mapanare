# Mapanare v5.4.4 — "Close Rt.04 — struct-return intermediate concats"

> **Close 62_list_output's intermediate-concat leak.** v5.4.1 Phase 4
> introduced a conservative aggregate-return guard that skips ALL
> drops when the return type starts with `%struct.` to avoid UAF on
> escaped fields. Intermediate concats that DON'T escape leak as a
> result. v5.4.4 lands the lowerer Move emission that v5.4.1 §5.2
> originally deferred, and extends drop-glue to honor moved slots
> even under the aggregate-return guard.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.4.3 shipped (Rt.03 closed, free-before-store in
place)
**Estimated work:** 1 session (~3–5 hours). Higher than v5.4.3 because
it touches MIR semantics (new Move emission in lower.mn) + emitter
matching (slot ↔ SSA source tracking).

---

## Why this release exists

v5.4.2's leak sweep proved that struct-returning functions leak
intermediate heap allocations even after v5.4.1's escape detection:

```mapanare
fn add_decl(st: St, name: String, ret: String) -> St {
    let mut s: St = st
    let line: String = "declare " + ret + " @" + name + "()"
    //                       ^t4     ^t6   ^t8     ^t10  ← 4 tracked concats
    return emit_line(s, line)    //  ↑ only %t10 ends up in s.lines
}
```

All 4 concats are in `str_owned`. The return type is `%struct.St`,
so v5.4.1's aggregate-return guard fires and the drop glue skips
every free. Intermediates `%t4` / `%t6` / `%t8` leak; `%t10` stays
valid (referenced by the returned list).

**The correct discriminator** is NOT "is the return aggregate?" but
"was this slot's value moved into an escaping container?". When
`list_push(%t10)` is lowered, %t10's ownership transfers to the list.
The caller's slot should be marked moved, and drop glue should skip
it. All 3 unescaped intermediates get dropped; the escaped final
survives.

This is the **lowerer Move emission** that v5.4.1 PLAN.md §5.2
originally called for and SESSION_REPORT deviation #5 deferred. The
infrastructure has been sitting in `moved_locals` waiting for the
lowerer to populate it.

---

## Scope

### What ships

#### 5.4.4a — Lowerer emits Move after resource-consuming ops

In `mapanare/self/lower.mn` and `mapanare/lower.py`, identify every
operation that consumes ownership of a tracked resource:

| Operation | Move what | Reason |
|---|---|---|
| `list_push(list, val)` | `val` | val is memcpy'd into list buffer; container owns now |
| `map_set(map, k, v)` | `k`, `v` | both consumed by the map |
| `struct_init { ..field: val }` | `val` (per field) | field takes ownership |
| `enum_init(variant, payload)` | each payload | boxed payload owns |
| `option Some(val)` / `result Ok(val)` / `result Err(val)` | `val` | wrapper owns |

For each, immediately after lowering the MIR instruction, emit a
`Move(val)` instruction. Python already wires `_do_move` → existing
`_move_resource(name)`; self-hosted already wires `"move"` kind →
`moved_locals.push(name)`.

#### 5.4.4b — Slot ↔ SSA source mapping

The tracker helpers currently push slot bases (`str_track.N`) to
`str_owned`. The Move instruction carries an SSA name (`t10`). Drop
glue needs to match: "this slot was allocated to track SSA name
`t10`; `t10` is in `moved_locals`; skip this slot".

New parallel list in `EmitState`: `str_owned_source` — indexes
aligned with `str_owned`. Each entry is the bare SSA name the slot
was created for (stripped of `%`). Same for `boxed_owned_source`,
`list_owned_source`.

`emit_track_string(val_name)` pushes `val_name[1:]` (strip leading
`%`) to `str_owned_source` alongside the slot base it pushes to
`str_owned`.

Registry bumps: `EmitState` 19 → 22 fields (v5.4.3 added 1, v5.4.4
adds 3 more — str_owned_source, list_owned_source, boxed_owned_source).
Reg.1 gate bumps accordingly.

#### 5.4.4c — Drop glue honors moved_locals uniformly

`emit_drop_glue_strings` / `_lists` / `_boxed` iterate paired
`owner` + `owner_source` lists. For each slot, check
`list_has_string(s.moved_locals, owner_source[i])`. If match, skip
the free entirely (even emit_line of the load — dead code elim).

With Move emission in place, drop glue can also REMOVE the
aggregate-return guard. The escape-detection logic already handles
the un-moved case (compare returned data ptr to each slot's content).
The moved case is handled by moved_locals. Combined: every legitimately-
escaped resource is protected, every legitimately-dead resource is
freed. The skip-all-on-struct-return guard becomes dead code.

**Conservatism note:** keep the guard for `%enum.*` and Option/Result
for this release — those require deeper payload inspection that
belongs in v5.4.5+. `%struct.*` alone opens up.

#### 5.4.4d — Baseline refresh + Rt.04 docket close

After the fix lands and sweep confirms 62_list_output CLEAN, update
`docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`. Flip
Rt.04 row in `docs/known_issues.md` to `**CLOSED v5.4.4**`.

### What does NOT ship

- **Rt.02** — Mesa/Vulkan third-party, still baseline-gated forever
  (or until v5.4.5+ symbolization work).
- **Enum / Option / Result aggregate-return opening.** Boxed payloads
  need recursive walk that isn't in v5.4.4 scope. Guard stays for
  those types; v5.4.5+ picks up if warranted.
- **Deep nested struct walk.** If struct A contains struct B which
  contains Strings, the fields of B don't get extracted. v5.4.5+ if
  a golden exposes this.
- **LINK_FAIL 7 goldens** (alloca void / br i1 %i64 IR correctness
  bugs). Separate problem class. v5.4.5 or later.

---

## Exit criteria

1. `make leak-check` → **0 regressions vs updated baseline**;
   62_list_output transitions LEAK → CLEAN.
2. **Only baseline-gated entries remaining: 39_gpu_detect +
   40_gpu_tensor** (Rt.02 Mesa/Vulkan, third-party). Mapanare-owned
   leak count: **ZERO**.
3. UAF sweep preserves baseline: 55 CLEAN / 11 CRASH_NO_ASAN.
4. Valgrind 0 new ERRORS.
5. Goldens 54/66 unchanged.
6. stage2 `llvm-as` OK; stage3 empty (Ve.1 preserved).
7. Non-bootstrap pytest 0 failures.
8. `make lint` clean.
9. Registry gate 28/28 (or whatever the new field count is) clean.
10. `docs/known_issues.md` Rt.04 row CLOSED.
11. Own.1 Phase 2 row in PARITY_GAPS advances to **"functional +
    leak-clean + CI-gated — Mapanare-owned zero"** — the genuinely
    100% endpoint.

---

## Design decisions

### D1 — Move instruction, not runtime refcounting

Move is compile-time. It annotates "this value's owner has transferred;
drop glue skips it". No runtime cost. Viable because Mapanare's
ownership is linear-ish (no shared references yet).

### D2 — Parallel source arrays, not paired tuples

`str_owned: List<String>` + `str_owned_source: List<String>` with
index-aligned semantics, rather than `str_owned: List<{slot, source}>`.
Reason: the self-hosted emitter's EmitState uses `List<String>` for
owner slots; switching to a pair-of-Strings type requires a new
struct + serializer. The parallel-list idiom matches existing usage
in the codebase.

### D3 — Keep enum/Option/Result aggregate guard for v5.4.4

Boxed-payload enums have a ptr field. Option has `{i1 tag, ptr payload}`.
Result has `{i1 tag, {T, ptr} payload}`. Extracting the payload
requires either a shape-aware walker OR knowledge that the enum
actually HAS a boxed variant active at runtime. Static `ret_ty`
inspection can only say "this enum might box"; not "this enum IS
boxed at this return". Conservative: skip all drops for enum/Option/
Result returns. v5.4.5+ if needed.

### D4 — Rt.03 from v5.4.3 must already be live

This release builds on v5.4.3's free-before-store. If v5.4.3 was
reverted or shipped with Rt.03 still open, v5.4.4's scope also
rescopes — we may need to land free-before-store AND move semantics
together. Prefer sequencing v5.4.3 first.

---

## Risks

### R1 — UAF on slot whose source SSA was incorrectly moved

**Risk: MEDIUM.** If the lowerer emits Move for a value that's still
used after the move (e.g., `list_push(v); print(v)`), drop glue
skips the slot but the value was actually borrowed-after-move.
Runtime UAF when print reads freed memory? No — print doesn't free,
and drop glue skipped. The UAF would only fire if ANOTHER free
path hit the same memory. Unlikely but possible if refcount-like
patterns creep in.

**Mitigation:** sanitizer HARD GATE. Any new ASAN_ERROR reverts.

### R2 — Move emission misses a site

**Risk: MEDIUM.** If `list_push` is handled but `map_set` isn't, map
tests leak. Either the leak sweep exposes it (post-fix worsen) or
it quietly stays LEAK in the baseline with a docket.

**Mitigation:** the operations table in §5.4.4a is explicit. Work
through it systematically; grep confirms every entry has a Move.

### R3 — Python / self-hosted MIR divergence

**Risk: LOW.** Move is a MIR instruction both emitters already know
about (v5.4.0 wired). Lowerer emits it; both emitters consume it.
Provided both lowerers get matching Move sites, parity is preserved.

**Mitigation:** side-by-side diff of Move emission in Python vs
self-hosted lowerers.

### R4 — stage2.ll size balloons

**Risk: LOW.** Move instructions are one line each, plus parallel
source-array init. Estimate +3–5% stage2.ll lines.

**Mitigation:** measure; investigate if > 10%.

---

## Release sequencing

| Outcome of sweep after Phase 3 | Action |
|---|---|
| 62_list_output CLEAN, no UAF regressions | Proceed to baseline refresh + close |
| 62_list_output still LEAK | Some Move site missed. Grep the lowerer for resource-consuming ops, find the missed one, add. |
| NEW LEAK in a golden previously CLEAN | The guard removal exposed a class we didn't move. Fix it OR re-add the guard for that ret_ty. |
| ANY ASAN_ERROR regression | REVERT. Move emission is removing a drop that was load-bearing. Investigate. |

If v5.4.4 can't cleanly close Rt.04 within the session budget, the
scope rescopes to **"land lowerer Move + slot-source mapping, KEEP
the aggregate-return guard"**. This ships the infrastructure without
the leak fix; v5.4.5 then removes the guard once more emit sites are
covered.

---

## What NOT to do

- **Do not suppress new ASAN_ERROR findings.** Revert and rethink.
- **Do not remove the enum/Option/Result guard.** Out of scope.
- **Do not deep-walk nested struct fields.** One level only.
- **Do not skip Python Move emission.** Both emitters must stay in
  parity or the Python bootstrap's IR diverges from stage1's.
- **Do not bump v5 tag without explicit user approval.** Saved rule.
