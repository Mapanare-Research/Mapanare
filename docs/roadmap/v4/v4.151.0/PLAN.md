# Mapanare v4.151.0 — E7: allocation hot path (`List<Int>::push`)

> **The allocator experiment.** Close the `List<Int>::push` throughput
> gap vs Rust's `Vec<i64>::push` by +30–50 % on `benchmarks/system/list_ops.mn`
> and `struct_alloc.mn`. Three concrete levers: (a) `realloc` over
> malloc+memcpy+free, (b) ensure capacity doubles (not linear growth),
> (c) inline the "push to non-full list" fast path. The fix lives in
> `runtime/native/mapanare_core.c::__mn_list_push` and `__mn_list_new`,
> with an optional hot-path inlining hint in `emit_llvm_text.py`.

**Status:** PLANNED
**Breaking:** No (runtime patch + optional emitter inlining hint; no ABI change)
**Prerequisite:** v4.150.0 shipped (E6 scheduler work recorded, win or dead end)
**Estimated work:** 2–3 days
**Theme:** E7 — allocator throughput on the push hot path

---

## Why this release, why now

`List<Int>::push` is the canonical allocation benchmark in the corpus.
Every stdlib collection, every `.collect()`, every loop that builds
a result list hits this path. Rust's `Vec<i64>::push` is the textbook
reference: amortized O(1) with doubling, `realloc`-based growth so
the OS can grow in-place when possible, and `#[inline(always)]` on
the non-full branch so the hot case is a single compare + store.

Mapanare's current shape (see `runtime/native/mapanare_core.c`):
- `__mn_list_new` at line 1054 — allocates a fresh buffer. Comment at
  line 1069–1070 notes: *"Allocate a fresh buffer instead of realloc.
  Struct copies may share the same data pointer (bitwise copy without
  refcount). realloc would..."* — the comment explains a defensive
  choice that predates the v4.131.0 Sh.2 fix. Post-Sh.2 the ownership
  semantics are clean enough that `realloc` is safe for primitive-
  element lists (no pointer aliasing concerns when elements are value
  types like `Int`, `Float`, `Bool`).
- `__mn_list_push` at line 1095 — out-of-line, non-inlined, doubles
  the check surface with a "corrupted list" recovery branch (lines
  1104, 1113) that the optimizer can't remove.

The three levers attack these in order: the `realloc` change is
element-type-aware (safe for value-types, preserve fresh-alloc for
pointer-element types with struct-copy aliasing risk); the doubling
check is a drop-in audit; the inlining hint is a `__attribute__((hot,
always_inline))` on the non-corrupted non-full fast path, letting
LLVM specialize at call sites.

Expected delta: +30–50 % on `list_ops.mn`, +15–25 % on `struct_alloc.mn`.
The 5 % rule floor guards the other 5 cross-language benches.

## Baseline

```bash
echo "4.151.0" > VERSION
make build-rt
python3 scripts/build_stage1.py

# Target workloads — 30 runs for tight medians
python3 benchmarks/cross_language/run_benchmarks.py \
  --only list_ops,struct_alloc --runs 30 \
  --output benchmarks/cross_language/v4.151.0-baseline.json

# Rust comparator (already wired in benchmarks/cross_language/rust/)
python3 benchmarks/cross_language/run_benchmarks.py \
  --only list_ops --runs 30 --language rust \
  --output benchmarks/cross_language/v4.151.0-baseline-rust.json

# Full corpus for 5 % rule floor
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.151.0-full-baseline.json

# Allocation counter — count malloc + realloc + free calls per run
MN_ALLOC_TRACE=1 ./benchmarks/cross_language/out/list_ops 2>&1 \
  | tee docs/roadmap/v4/v4.151.0/alloc-trace-baseline.log
```

Record in `docs/roadmap/v4/v4.151.0/BASELINE.md`:
- `list_ops` median wall, CPU, peak RSS
- `struct_alloc` median wall, CPU, peak RSS
- Rust `Vec<i64>::push` reference (for the target ratio)
- malloc + realloc + free counts per run
- Current capacity-growth trace (log cap at each resize) —
  expected to reveal whether growth is doubling, linear, or something
  else

Expected at v4.150.0 tag: `list_ops` median ≈ N ms, Rust ≈ 0.6 N ms,
ratio ≈ 1.6–1.8× of Rust.

## Hypothesis

1. **`realloc` over malloc+copy+free** — the v4.131.0 Sh.2 arc fixed
   the ownership-transfer hazard that justified the defensive fresh-
   alloc. For lists of value-type elements (Int, Float, Bool, Char),
   `realloc` is safe and lets the allocator grow in place when
   possible, saving the `memcpy(old, new, len * elem_size)` cost on
   common-case grows. Expected lever: 15–30 % on large lists.
2. **Capacity doubling audit** — `__mn_list_push` should double
   capacity at each resize (amortized O(1) push). If it's growing
   linearly (e.g., +16 slots per resize) the asymptotic cost is O(N²)
   on append-heavy loops. Audit + fix if needed. Expected lever: up
   to 2× on 10k+ push loops.
3. **Inline the non-full fast path** — `__mn_list_push`'s hot case
   ("cap > len, just store and increment") should be a single compare
   + store. Today it's an out-of-line call. A `static inline` helper
   + `__attribute__((hot, always_inline))` on the fast path, with the
   slow path kept out-of-line, saves the call + return per push.
   Expected lever: 5–10 % across all list-push workloads.

## Phased work

### Phase 1 — Allocation trace + capacity audit

```bash
# Instrument __mn_list_new and __mn_list_push with a single-line
# trace (compile-time guarded on MN_ALLOC_TRACE):
#
#   fprintf(stderr, "LIST_PUSH len=%lld cap=%lld grew=%d\n", ...);
#
# Run both workloads once, capture the trace, count resizes and
# current growth factor.

grep -c "grew=1" docs/roadmap/v4/v4.151.0/alloc-trace-baseline.log
# Current capacity-growth reveal: doubling / linear / bucketed?
```

Write `docs/roadmap/v4/v4.151.0/IR_DIFF.md` with:
- §1 `__mn_list_push` source (Mapanare) vs `Vec::push` / `RawVec::grow`
  source (Rust stdlib, read-only). Annotate the three lever sites.
- §2 LLVM IR of a simple `let mut xs: List<Int> = []; for i in 0..10000
  { xs.push(i) }` at `-O3`. Show the call-to-`__mn_list_push` shape;
  annotate which call shrinks or disappears after each lever.

### Phase 2 — Hypothesis

`docs/roadmap/v4/v4.151.0/HYPOTHESIS.md` — one paragraph per lever
with patch sketch and expected delta. Rank by safety: doubling (safest,
purely corrective) → inline fast-path (safe, compiler-only) → realloc
(needs element-type gate).

Order of execution: do the safest first so the hot-path inlining
measures on top of correct doubling, not stacked with it.

### Phase 3 — Lever 1: capacity doubling audit (~0.5 day)

Read `runtime/native/mapanare_core.c::__mn_list_push` body around
line 1095–1180. Verify the growth path is:

```c
int64_t new_cap = list->cap == 0 ? 4 : list->cap * 2;
```

and not

```c
int64_t new_cap = list->cap + 16;
```

or similar linear growth. If linear, fix to doubling with minimum
seed (4 or 8). If already doubling, record the audit as a no-op and
move to Lever 2.

Re-measure:

```bash
make build-rt && python3 scripts/build_stage1.py
python3 benchmarks/cross_language/run_benchmarks.py \
  --only list_ops,struct_alloc --runs 30 \
  --output benchmarks/cross_language/v4.151.0-L1.json
```

5 % rule gate.

### Phase 4 — Lever 2: `realloc` for value-type element lists (~1 day)

The current fresh-alloc comment at line 1069 warns about struct-copy
aliasing. That concern is legitimate for **pointer-element** lists
(where struct-copy would share the data pointer) but not for
**value-element** lists (where each element is a direct memcpy of
bytes).

Add a branch on element type to `__mn_list_push`'s grow path:

```c
// runtime/native/mapanare_core.c::__mn_list_push
// E7-L2 (v4.151.0): realloc for value-type elements; keep fresh-alloc
// for pointer-element types where struct-copy aliasing is a concern.
// See v4.131.0 Sh.2 closeout for the ownership-transfer guarantees
// that make value-type realloc safe.
if (LIST_ELEM_IS_VALUE_TYPE(list->elem_size, list->elem_tag)) {
  list->data = __mn_realloc(list->data, new_cap * list->elem_size);
} else {
  // existing fresh-alloc + memcpy + free path
}
```

The `elem_tag` field is added to `MnList` if not present (small ABI
additive — run `check_struct_registry.py` before and after). For
safety, start with `elem_size ∈ {1, 2, 4, 8}` as the value-type
predicate — covers Int, Float, Bool, Char exhaustively.

Re-measure. 5 % rule.

### Phase 5 — Lever 3: inline the fast path (~0.5 day)

Split `__mn_list_push` into two functions:

```c
// runtime/native/mapanare_core.c
__attribute__((hot, always_inline))
static inline void __mn_list_push_fast(MnList *list, const void *elem_ptr) {
  // Hot path: cap > len, no grow needed
  memcpy(list->data + list->len * list->elem_size, elem_ptr, list->elem_size);
  list->len += 1;
}

MN_EXPORT void __mn_list_push(MnList *list, const void *elem_ptr) {
  if (__builtin_expect(list->len < list->cap, 1)) {
    __mn_list_push_fast(list, elem_ptr);
    return;
  }
  // Slow path: grow, then push (all existing corruption-recovery logic)
  ...
}
```

Optionally, emit a direct `__mn_list_push_fast` call from
`mapanare/emit_llvm_text.py` when the compiler can prove the list
has capacity (rare today; LICM-adjacent, ties to E8). Skip that
cross-coupling for this release.

Re-measure. 5 % rule.

### Phase 6 — Record

Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

```
| E7a | list_push doubling audit | no-op / win / dead-end | +X% list_ops | mapanare_core.c:~NNN | v4.151.0 |
| E7b | list_push realloc for value-types | win/dead-end | +X% list_ops | mapanare_core.c:~NNN | v4.151.0 |
| E7c | list_push fast-path inline | win/dead-end | +X% list_ops | mapanare_core.c:~NNN | v4.151.0 |
```

Write `docs/roadmap/v4/v4.151.0/RESULTS.md` and `SESSION_REPORT.md`.

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `BASELINE.md` written with list_ops + struct_alloc numbers + alloc trace | yes |
| 2 | `IR_DIFF.md` written (Mapanare C source + Rust stdlib cross-ref) | yes |
| 3 | `HYPOTHESIS.md` written (three levers ranked) | yes |
| 4 | Each landed lever passes the 5 % rule | yes |
| 5 | `RESULTS.md` written with per-lever deltas | yes |
| 6 | `list_ops` median improves ≥ 30 % vs v4.150.0 baseline (stretch: ≥ 50 %) | target |
| 7 | `struct_alloc` median improves ≥ 15 % | target |
| 8 | No other cross-language workload regresses > 2 % | yes |
| 9 | `PERF_EXPERIMENTS.md` entries added — win or dead end, all three | yes |
| 10 | Golden `30_list_ops.mn` (if present) byte-identical through mnc-stage1 | yes |
| 11 | Non-bootstrap pytest: ≥ 5,160 passed / 0 failed | yes |
| 12 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 13 | Native goldens: 54 / 66 | yes |
| 14 | Valgrind: 0 ERRORS (realloc path is the key canary) | yes |
| 15 | ASan: 0 ASAN_ERROR | yes |
| 16 | Fixed-point: within `DIFF_THRESHOLD=100` | yes |
| 17 | `check_struct_registry.py` green (if `MnList` gains `elem_tag`) | yes |
| 18 | All 8 CI gates green | yes |
| 19 | SESSION_REPORT.md written | yes |
| 20 | Tag `v4.151.0` pushed to origin | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `realloc` reintroduces a struct-copy aliasing bug the Sh.2 arc closed | low | high | Value-type gate (`elem_size ∈ {1,2,4,8}`) is the guard; pointer-element lists stay on fresh-alloc path; full ASan + valgrind sweep after lever lands |
| `MnList` struct grows a field — ABI change breaks golden baselines | medium | medium | Add field at end; run `check_struct_registry.py`; update the ABI snapshot file (Reg.1 gate); bootstrap/stage1 rebuild is required, not optional |
| Capacity doubling was already correct — Lever 1 is a no-op | medium | low | Fine. Record as no-op in PERF_EXPERIMENTS.md; the audit itself has documentation value |
| `__mn_list_push_fast` inline causes binary-size bloat at call sites > 2 % | low | low | `hot` attribute + LLVM's own size budget should prevent explosion; if it happens, drop the `always_inline` and keep only `hot`; re-measure |
| Rust's `Vec` tricks we can't match (e.g., niche-optimized capacity) make ≤ 1.3× Rust unreachable | medium | medium | Document honestly in RESULTS.md; 30 % delta is still arc-worthy even if it doesn't match Rust byte-for-byte |
| A list-owning MIR pass (LICM in E8, say) relies on out-of-line `__mn_list_push` — inlining breaks a future experiment | low | low | E8 is the next release; coordinate. If E8 needs out-of-line calls, gate the inline behind a build flag. Low-probability risk |

## What this release does NOT do

- Does not change `MnString`, `MnMap`, `MnSignal`, or `MnStream`
  allocators. Only `MnList` is in scope.
- Does not add a bump allocator, arena, or slab. Those are v5.x
  architectural changes.
- Does not touch the Python-side list fallback. The emitter emits
  calls to `__mn_list_push` / `__mn_list_new`; the runtime owns the
  implementation.
- Does not re-enable escape analysis or LICM (that's E8 / v4.152.0).
  Stack-allocation of small lists is its own experiment.
- Does not port the optimizations to WASM or mobile runtimes. Native
  desktop only; mobile uses the cooperative scheduler + 4KB arenas
  and has different tradeoffs.

## Carry-forward after v4.151.0

- If all three levers land clean: E7 is a full win. v4.152.0 opens
  on E8 (LICM re-enable) as planned.
- If only the doubling audit + fast-path inline land and realloc is
  rolled back: E7 is a partial win. Rec.1 opens LOW to revisit realloc
  with a finer value-type predicate in v4.153.0 refresh if time permits.
- If Lever 2 introduces a measurable ASan/valgrind regression: roll
  back, open a Vp.-class docket, record as E7b dead end. The arc
  proceeds to E8.
- A `Mn.1` docket may open if the `MnList::elem_tag` ABI addition
  surfaces latent drift in the C header registry. Close in the same
  release.
