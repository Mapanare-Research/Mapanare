# Mapanare v5.6.13 — "Destination passing extension + optional move semantics"

> **Layer 1 extension + conditional Layer 2.** v5.6.12 closes
> Lk.1 + Ve.2 by destination-passing for List let-bindings.
> v5.6.13 extends the same pattern to struct/enum/map
> let-bindings (Layer 1 completion) — purely structural cleanup
> that prevents Lk.1-class bugs from re-surfacing in non-list
> resource types. Optionally adds Layer 2 (move on assignment)
> if a share-then-mutate leak surfaces in the corpus during
> v5.6.12 sanitizer sweep.
>
> **Conditional release.** Skip if v5.6.12 surfaces no new leaks
> and the struct/enum/map cleanup isn't load-bearing. Go directly
> to v5.7.0.

**Status:** PLANNED (CONDITIONAL)
**Breaking:** No
**Prerequisite:** v5.6.12 shipped (Lk.1 closed, Ve.2 residuals closed,
floor dropped).
**Estimated work:** 1 session (~2-3 hours).

---

## Why this release exists

### The two-alloca pattern affects all resource types

v5.6.12 closes Lk.1 for List let-bindings. The same two-alloca
pattern exists for:
- `let mut s: Foo = Foo { ... }` — StructInit's `%t0.addr` +
  let's `%s.addr`
- `let mut e: Bar = Bar::Variant(...)` — EnumInit's two allocas
- `let mut m: Map<K,V> = {...}` — MapInit's two allocas

These don't currently surface a leak because:
1. struct/enum init use the GEP-trick for sizing (no 384-byte
   floor issue)
2. The corpus doesn't exercise their drop-glue under LSan in a
   way that triggers the alloca-aliasing pattern

But the two-alloca pattern is structurally the same. Closing it
prevents:
- Future Lk.1-class bugs in struct-heavy code
- Wasted IR space (2 allocas + 1 copy per let-binding)
- Non-uniform handling between resource types

### Layer 2 (conditional)

If v5.6.12's sanitizer sweep surfaces a share-then-mutate leak
in the corpus (`let b = a; b.push(...)` pattern), Layer 2 closes
it via Rust-style move semantics:
- `let b = a` becomes a *move*: lower-time tracking transfers
  ownership from a to b; subsequent uses of a are flagged.
- drop-glue tracks only the current owner (b after move).

Skip if no leak surfaces. v5.6.12 closes the visible blocker;
Layer 2 is preventive.

---

## Scope

### What ships (CONDITIONAL)

#### 9.13a — Layer 1 extension to struct/enum/map (~60 min)

For each of `lower_struct_init`, `lower_enum_init`,
`lower_map_init`:

1. Add destination-passing variant accepting `dest_alloca:
   Option<Value>`.
2. When `dest_alloca = Some(addr)`, emit the resource init
   directly into the alloca (skip intermediate scratch).
3. Update `lower_let` to route through these variants when
   value is a fresh resource init.

This mirrors v5.6.12's List handling. ~30 LOC per resource type.

#### 9.13b — Layer 2: move on assignment (CONDITIONAL — only if needed)

If v5.6.12 sanitizer sweep flagged a share-then-mutate leak:

1. Add `consumed_locals: List<String>` to LowerState (parallel
   to the existing `moved_locals` in EmitState — but at lower
   time, scoped per function).
2. In `lower_let` for the case `let b = a` where `a` is a known
   resource binding:
   - Add `a` to `consumed_locals`.
   - Emit a memcpy from `a.addr` to `b.addr` (the slice header
     copy).
   - Transfer the tracking entry: `list_owned`/`str_owned`/
     `boxed_owned` swap `a.addr` → `b.addr`.
3. After lowering each function, check `consumed_locals` for
   uses-after-move and emit a diagnostic (warning, not error;
   we're not implementing a borrow checker).

#### 9.13c — Validation gate (~30 min)

Same matrix as v5.6.12:
- Goldens 64/66 preserved.
- `mnc-stage2 /tmp/p3.mn` clean.
- `verify_fixed_point.sh` NEAR or STRICT.
- Full sanitizer matrix clean.
- `make lint` + struct registry clean.

#### 9.13d — Documentation (~15 min)

- `docs/roadmap/v5/v5.6.13/SESSION_REPORT.md`.
- `CLAUDE.md` + `ROADMAP.md` entries.

### What does NOT ship

- **Full borrow checker.** Off the table. Layer 1 + 2 cover
  observable memory-safety holes.
- **Compile-time borrow errors.** Layer 2 emits warnings, not
  errors. We're closing memory leaks, not preventing programs
  from compiling.
- **Sh.7 / B closure work.** v5.7.0.

---

## Exit criteria

1. `mnc-stage1` rebuilds clean.
2. Goldens 64/66 preserved (no regressions).
3. `verify_fixed_point.sh` NEAR or STRICT.
4. ASan UAF: 65 CLEAN / 0 ASAN_ERROR / 1 CRASH_NO_ASAN.
5. Valgrind: 0 ERRORS / 66 WARNINGS_ONLY.
6. LSan baseline gate: PASS.
7. stage2.ll growth: ≤ 1% vs v5.6.12 (likely DECREASE — fewer
   intermediate allocas).
8. `__mn_list_new(i64 384)` site count: 0 (preserved from v5.6.12).
9. Non-bootstrap pytest: 0 failures.
10. `make lint` clean; `check_struct_registry.py` 23/23/91 clean.
11. **If 9.13b shipped**: any share-mutate leak that surfaced in
    v5.6.12 is now CLEAN.

---

## Design decisions

### D1 — Conditional release

This release is OPTIONAL. If v5.6.12 surfaces no new leaks AND
the struct/enum/map two-alloca pattern doesn't matter for
correctness or noticeable IR size, **skip v5.6.13 and go to
v5.7.0 directly**.

The decision point is the v5.6.12 sanitizer sweep. If it shows:
- All sanitizers clean
- stage2.ll size at v5.6.12 is acceptable

Then v5.6.13 is preventive, and the user's preference governs
whether to ship.

### D2 — Layer 1 extension is structural cleanup

The extension to struct/enum/map mirrors v5.6.12's List handling
exactly. No new design decisions; it's a parallel rollout of the
proven pattern.

### D3 — Layer 2 is gated on observed need

Don't ship Layer 2 speculatively. Ship only if a share-mutate
leak surfaces in v5.6.12's sweep. The corpus has no observed
case currently, so Layer 2 may stay unwritten indefinitely.

### D4 — Don't extend to function returns

Function returns via sret already have destination passing
(LLVM sret semantics). Mapanare's emitter uses sret for
aggregate returns. No additional work needed there.

---

## Risks

- **R1 — Layer 1 extension breaks struct/enum lets.**
  struct/enum init is more complex than list init (per-field
  emission, payload boxing). The destination-passing path needs
  to handle all sub-cases. **Mitigation**: phase the changes
  per resource type; goldens-test after each.
- **R2 — Layer 2 surfaces a NEW class of bug.** Move tracking
  is non-trivial. Conditional uses (move inside an if branch)
  need careful analysis. **Mitigation**: skip Layer 2 unless
  forced by observed leak.
- **R3 — Cleanup release ships nothing user-visible.** v5.6.13
  may ship with no behavioral change. That's OK — it's
  structural hygiene. **Mitigation**: document as "optional
  cleanup" in CLAUDE.md.

---

## What NOT to do

- Do not bundle a full borrow checker.
- Do not enforce move semantics as compile-time errors.
- Do not extend to function returns (sret already does this).
- Do not skip v5.6.12 sanitizer sweep before scoping this release.
- Do not commit `/tmp/*` artifacts.
- Do not tag without user approval.
- Do not push without user approval.

---

## Decision tree at v5.6.13 entry

```
v5.6.12 shipped → check sanitizer outputs:

├─ ASan / valgrind / LSan all clean? AND struct/enum/map cleanup
│   not load-bearing?
│   → SKIP v5.6.13. Go to v5.7.0 directly.
│
├─ Share-mutate leak surfaced in corpus?
│   → v5.6.13 with Layer 1 extension + Layer 2.
│
└─ struct/enum/map cleanup desired (user preference) but no
   leak?
   → v5.6.13 with Layer 1 extension only. Layer 2 skipped.
```
