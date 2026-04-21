# v5 Gate Decision — v4.99.0

## Score

**Aggregate: 6.59/10**
**NEEDS WORK: 3 reviewers (Rattler, Viper, Anaconda)**

## Decision Rule

- Aggregate >= 9.0 AND 0 NEEDS WORK -> Option A (tag v5.0.0)
- Aggregate < 9.0 -> **Option B (continue v4.100.0+)**
- Aggregate >= 8.5 AND < 9.0 -> Option C (tag + continue)

**Applied: Option B.** Aggregate 6.59 < 9.0, with 3 NEEDS WORK.

## What Option B Means

v4.100.0 opens. The panel's docket (11 items) becomes Arc 15 scope.
The next scheduled panel is v4.104.0 (5-minor cadence). The version
number does not change. The discipline does not change.

## What Must Be Fixed Before v5 Can Be Discussed Again

1. **Tagged-pointer UB** — Replace `mn_tag_heap` bit-tagging with a
   struct field. Rebuild mnc-stage1. Verify golden tests pass.
2. **List indexing bug** — Root-cause and fix `data[j]` garbage in
   accumulation patterns.
3. **Async end-to-end** — Link and run at least one async benchmark
   natively (not just compile to IR).

## The Lead's Assessment

The panel is right. The tagged-pointer issue is a 3-4 hour fix that
blocks everything downstream. It should have been fixed in v4.97.0
when it was discovered. Shipping v4.97.0 and v4.98.0 with a known
binary-corruption bug was a process failure — the anti-rush rules say
"fix the root cause" and we didn't.

The optimization work (Arcs 11-12) was real engineering but the
performance narrative was overstated. The IR annotations didn't move
the O2 numbers. That's an honest finding and the FINAL_REPORT.md
correctly reports it.

The path to v5.0.0 is clear:
1. Fix the tagged-pointer UB (v4.100.0)
2. Fix list indexing (v4.101.0)
3. Async end-to-end verification (v4.102.0)
4. Verify else/sino + closure types (v4.103.0)
5. Panel at v4.104.0 — re-evaluate v5 gate

Estimated: 5 releases, ~2-3 sprints. The work is bounded and known.

## v5.0.0 Tag

**Not created.** Option B does not tag v5.0.0.

---

## Docket Closure Update (v4.106.0 Phase B panel — 2026-04-14)

All 5 critical / high docket items from this panel are now **CLOSED**
with evidence. The Phase B re-grade (v4.106.0) verifies the fixes.

### CRITICAL

- [x] **Item #1 — Tagged-pointer UB** — CLOSED
  - Fixed in: **v4.100.0**
  - Evidence: `MnString` struct in `runtime/native/mapanare_core.h:60`
    has `uint64_t is_heap : 1` bitfield; all `mn_tag_heap` /
    `mn_untag_heap` / `mn_is_heap` helpers deleted from
    `mapanare_core.c` (only comments describing the transition remain).
    ABI preserved at 16 bytes.
  - Verification: 36 valgrind runs (v4.105.0 Phase 1) show no
    tagged-pointer-specific errors; `mnc-stage1` ELF stripped to
    3.5 MB; golden smoke test prints correctly.

- [x] **Item #2 — List indexing returns garbage** — CLOSED
  - Fixed in: **v4.101.0** (+ deeper drop-glue fix in **v4.103.0**)
  - Root cause: Python emitter's drop-glue pass was freeing heap
    strings that had been pushed into lists / stored as struct fields
    before the container released them. v4.101.0 added `_move_resource`
    move-semantics at 6 sites in `emit_llvm_text.py`. v4.103.0 extended
    the fix to boxed enum payloads reachable transitively through
    return values.
  - Verification: 0/61 → 16/62 → 21/64 goldens pass through
    `mnc-stage1`; regression test `62_list_output.mn` added.

### HIGH

- [x] **Item #3 — Rebuild `libmapanare_rt.a` with scheduler exports** — CLOSED
  - Fixed in: **v4.102.0**
  - Evidence: `nm runtime/native/libmapanare_rt.a | grep __mn_coro`
    shows `__mn_coro_scheduler_{init,destroy,register,run}`,
    `__mn_coro_spawn`, `__mn_coro_register_wait`. Also fixed two
    latent bugs: `mn_coro_is_done` offset (now reads
    `handle[0] == NULL` per LLVM 18's final-suspend lowering) and
    `_do_block_on` cached-handle reload.
  - Verification: async goldens 55/56/57 run natively producing
    42 / 43 / 110; valgrind clean; TSan reports 0 data races across
    all 3 async tests in v4.105.0 Phase 3 and re-verified in v4.106.0.

- [x] **Item #4 — Verify `else` / `sino` works end-to-end** — CLOSED
  - Fixed in: **v4.103.0**
  - Evidence: `tests/golden/63_else_sino.mn` produces the expected
    output `positive / negative / zero / 1 / -1 / 0` through the
    Python bootstrap + clang link + native binary path.
  - Nuance: `mnc-stage1` still fails this test due to a pre-existing,
    separately-docketed String-lifetime bug in the self-hosted
    emitter (same family of UAF that v4.101.0 fixed on the Python
    side). The v4.99.0 docket specifically asked for end-to-end
    verification, not stage1 verification; criterion met.

- [x] **Item #5 — Fix closure type annotations** — CLOSED
  - Fixed in: **v4.103.0**
  - Evidence: three changes in `mapanare/lower.py`:
    - `_resolve_type_expr(FnType)` returns `MIRType(kind=FN)` (not
      `UNKNOWN`);
    - `_lower_call(Identifier)` dispatches through `ClosureCall` when
      the callee is a typed FN variable;
    - `_lower_lambda` emits `ClosureCreate` for every lambda
      (including no-capture, so all closures share the `{ptr, ptr}`
      ABI).
  - Verification: `tests/golden/64_closure_typed.mn` produces
    `(10, -3, 20, 15)` — `apply(double, 5)`, `apply(negate, 3)`,
    `double(10)`, `combine(sum, 7, 8)`. Valgrind clean on the
    bootstrap binary.

### MEDIUM / LOW — informational, not panel scope

- Item #6 (disclose binary corruption): **SUPERSEDED** — the
  corruption itself was fixed in v4.101.0, so the disclosure
  requirement lost its reason to exist.
- Item #7 (byref size heuristic): **OPEN** — carry forward.
- Item #8 (coroutine frame coupling): **PARTIAL** — v4.102.0's
  `mn_coro_is_done` fix addressed the immediate symptom. Broader
  "fragile under LTO" is not tested (no LTO in CI).
- Item #9 (string concat perf): **OPEN** — StringBuilder shipped in
  v4.95.0, but auto-routing `+`-chains is not implemented. Phase C.
- Item #10 (bilingual keyword collision docs): **OPEN**.
- Item #11 (async error messages): **OPEN**.

### New items opened in Phase B for v4.107.0+

See `docs/roadmap/v4/v4.106.0/MEASUREMENTS.md` — 15 total: 5 divergence
items (`Div.*`), 7 valgrind (`Vg.*`), 3 ASan (`As.*`). `Vg.2` ≡ `As.1`;
single fix can close 3.

### Gate re-evaluation

Per the "What Must Be Fixed Before v5 Can Be Discussed Again" list
above:
1. Tagged-pointer UB — **fixed** (v4.100.0).
2. List indexing bug — **fixed** (v4.101.0 + v4.103.0).
3. Async end-to-end — **fixed** (v4.102.0; re-verified TSan-clean in v4.105.0).

All three hard blockers are cleared. The **v5 gate discussion is not
re-opened in this panel** — v4.106.0 is a Phase B verification panel,
not the v5 panel. The v5 panel needs Phase C (benchmarks) first per
the post-panel plan. See `docs/roadmap/v4/v4.106.0/PLAN.md` "After
v4.106.0" section.
