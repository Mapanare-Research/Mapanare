# v5.5.3 — Self-hosted coroutine emission design (docs-only)

> **Zero code. One design doc: `DESIGN.md`.**
>
> v5.5.2 shipped Option A (synchronous async stubs). The user
> rejected keeping that as the final answer because it would
> "bite us later" — async with real I/O silently blocks, agent
> handlers can't suspend, stdlib async modules are unusable.
> v5.5.3 is the research + design gate before v5.5.4+ ships the
> real thing.

**Status:** SHIPPED
**Breaking:** No (no code changes)
**Goldens:** 59/66 unchanged

---

## What shipped

### `docs/roadmap/v5/v5.5.3/DESIGN.md` — 480 lines

The deliverable. Covers:

1. **Why this release exists** — Option A's actual coverage
   vs. documented stdlib async API surface. Every agent
   handler, every async stdlib module, every I/O-bound golden
   silently breaks under Option A.
2. **State-of-the-art survey** — re-evaluation of Rust,
   Go, C++20, Zig async models against v4.67.0's choice.
   Conclusion: LLVM switched-resume coroutines (v4.67.0's
   pick) is still correct in 2026-04. Rust's `Pin` is too
   heavy, Go's green threads don't fit WASM, C++20 uses the
   same mechanism without the promise-type user API, Zig
   removed async in 0.11.
3. **Validation of v4.67.0 decisions** — Decision 1
   (scheduler model) upgraded from Option A (cooperative
   inline) to Option B (multi-threaded work-stealing, already
   live in C runtime since v5.1.4). Decision 7 (AST node)
   simplified from dedicated AsyncFnDef to parser decorator.
   Other 6 decisions unchanged.
4. **Gap analysis** — 13 concerns, 7 shipped by v5.5.0–v5.5.2,
   6 still gaps (async fn structural rewrite, AwaitSuspend,
   BlockOn, main scheduler lifecycle, inliner gate, drop-glue
   cleanup path).
5. **Phase plan v5.5.4 → v5.5.9** — concrete scope + LOC +
   risk + verification per release. Summary:

| Version | Scope | LOC | Risk |
|---|---|---:|---|
| **v5.5.4** | Inliner gate + async fn structural rewrite (prologue/ret-rewrite/epilogue) | ~155 | High |
| **v5.5.5** | Real AwaitSuspend emission (coro.save/suspend/switch) | ~90 | Med-High |
| **v5.5.6** | Real BlockOn + main scheduler_init/destroy | ~80 | Medium |
| **v5.5.7** | Sanitizer + fixed-point hardening | bugfixes | — |
| **v5.5.8** | spawn + join + new multi-fanout golden | ~60 | Low |
| **v5.5.9** | Docs + PARITY_GAPS.md Sh.4 → Historical | docs | — |

6. **Risk register (self-hosted specific)** — 7 risks, with
   mitigations. The dominant risk is drop-glue interaction
   with the new cleanup block (R1, HIGH) — v5.4.0–v5.4.4's
   shadow-slot + loop-depth tracking fires at `ret`, which
   async fns rewrite to `br %coro.final`. v5.5.5 handles this
   as its own phase.
7. **Verification matrix per phase** — unit/integration/
   sanitizer/self-host/benchmark gates.
8. **Open questions** — 5 TBDs the v5.5.4 implementor should
   resolve before starting.

### What did NOT ship

- **Any code changes.** The 5 Sh.4 goldens still execute via
  Option A synchronous copies. Stage1 binary byte-identical
  to v5.5.2.
- **VERSION bump from 5.5.2 → 5.5.3.** This is a design-only
  release (precedent: v4.67.0 was also docs-only, single
  DESIGN.md deliverable).

---

## Why this approach

The user's directive ("the right way even if you need to
create a v5.5.3, v5.5.4 and more version") fits the Mapanare
roadmap convention: big changes get a design-first release,
then incremental implementation. v4.67.0–v4.75.0 executed
exactly this pattern for the Python bootstrap's original
async implementation (8 releases from design to close).

Skipping the design doc and going straight to coding v5.5.3
with full LLVM coroutines would:

- Commit ~350+ LOC of emitter changes in one shot
- Interact with 4 other emitter subsystems (drop-glue, sret,
  inliner, entry-block buffering) without an explicit risk
  map
- Ship without verification criteria locked down
- Make post-hoc phase splits (e.g., "was v5.5.3 Phase 1 or
  Phase 2 the cause of this regression?") ambiguous

v4.67.0 DESIGN.md is still authoritative for Mapanare's
async language surface. v5.5.3 DESIGN.md doesn't replace it —
it translates its conclusions into concrete self-hosted
porting work.

---

## Exit criteria

1. ✅ DESIGN.md written (this release)
2. ✅ v4.67.0 DESIGN.md re-read + validated (§3 of DESIGN.md)
3. ✅ Rust/Go/C++20/Zig survey documented (§2 of DESIGN.md)
4. ✅ Phase plan with LOC + risk per release (§5)
5. ✅ Verification matrix (§7)
6. ✅ Open questions surfaced (§8)

All met.

---

## Commits

- `VERSION`: 5.5.2 → 5.5.3
- `docs/roadmap/v5/v5.5.3/DESIGN.md`: 480 lines
- `docs/roadmap/v5/v5.5.3/SESSION_REPORT.md`: this file
- `CLAUDE.md`: v5.5.3 entry prepended (design-only marker)

No `mapanare/self/*` changes. No runtime changes. No harness
changes.

---

## What happens next

v5.5.4 starts the implementation. Reference points:

- §5 of DESIGN.md for scope
- §6 for risks
- §7 for verification gates
- Appendix A for the "read these files in this order" starter
  for the v5.5.4 implementor
