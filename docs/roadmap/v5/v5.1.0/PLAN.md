# Mapanare v5.1.0 — "List IR Inlining"

> **The last lever in the Rust-gap closure arc.** v4.151.0 (E7)
> identified that quicksort's 2.99× Rust ratio is dominated by
> ~130 000 opaque `__mn_list_get/__mn_list_set` calls that LLVM can't
> inline across an extern-C boundary. This release inlines list
> access directly in the LLVM IR emitter, unlocking vectorization
> and SROA. Target: geomean 1.00× Rust across the cross-language
> corpus.

**Status:** SHIPPED (see SESSION_REPORT.md and RESULTS.md)
**Breaking:** No (internal codegen change; ABI-preserving)
**Prerequisite:** v5.0.5 shipped
**Estimated work:** 2-3 sessions

---

## Why this release exists

v4.150.0 closed the async gap (0.85× Go). v4.151.0 closed 4% of the
quicksort gap but honestly reported: "the remaining gap requires
emitter-level changes (inline list operations in LLVM IR)." That's
this release.

Current state (v4.153.0 benchmarks):

| Workload | Mapanare / Rust | Bottleneck |
|---|---|---|
| `fib_recursive` | 1.11× | Subprocess-spawn noise (v4.146.0 E2) |
| `enum_match` | 0.56× (faster) | Unified-return-block win (v4.145.0 E1) |
| `struct_alloc` | 1.06× | Resolved (v4.149.0 ABI.1) |
| `string_concat` | 2.04× | v4.148.0 E4 realloc-growth landed |
| `quicksort` | 2.99× | **List access opaque to LLVM — this release** |
| `prime_sieve` | 1.20× | List-index-heavy — same root cause |
| **Geomean** | **1.17×** | Target: **1.00×** |

## Scope

**In scope:**
- `mapanare/emit_llvm_text.py`: replace `call @__mn_list_get(list,
  idx)` with an inline IR sequence:
  ```
  %hdr = getelementptr {ptr, i64, i64, ...}, ptr %list, i32 0, i32 0
  %data = load ptr, ptr %hdr
  %p = getelementptr i64, ptr %data, i64 %idx
  %val = load i64, ptr %p
  ```
  gated on value-type lists where `elem_size == 8` (the common
  `List<Int>` / `List<Ptr>` case)
- Mirror into `mapanare/self/emit_llvm.mn`
- Keep the runtime `__mn_list_get` / `__mn_list_set` entry points for
  unboxed-capture closures and for debug builds (bounds checks)
- Emit bounds-check sequence inline too, or deliberately skip in
  release builds behind a `__mn_list_get_unchecked` name

**Out of scope:**
- Inlining `__mn_list_push` (v4.151.0 already has a builtin_expect
  fast path)
- `Map` / `Signal` / `Stream` inlining (separate release)
- Bounds-check elision via loop analysis (v5.2.x)

## Exit criteria

- `benchmarks/cross_language/quicksort.mn` ratio drops from 2.99× to
  ≤ 1.50× Rust
- Geomean across the 6-workload corpus ≤ 1.05× Rust
- No regression on any workload > 2%
- Strict 3-stage fixed point holds
- Self-hosted emitter and Python emitter produce byte-identical IR
  on the golden corpus
- No new ASan / valgrind findings

## Risks

**Risk 1 — bounds-check elision breaks memory safety.**
Inlining without bounds checks is fast but unsafe.
*Mitigation:* emit the bounds check inline too for release builds;
measure the cost; if > 5% overhead, add a debug-vs-release flag.

**Risk 2 — fixed-point breaks.**
Emitter changes always risk this.
*Mitigation:* mirror into self-hosted and run `verify_fixed_point.sh`
on every commit. If the fix is emitter-only, fixed point should
trivially hold.

**Risk 3 — LLVM's alias analysis gets confused.**
Inlining exposes `ptr` access that previously was hidden behind an
opaque call. If multiple lists in the same function share a backing
store (post-COW clone), LLVM may hoist loads across mutation points.
*Mitigation:* emit `noalias` + `tbaa` metadata on list data pointers;
test with stress programs that mutate lists across function calls.
