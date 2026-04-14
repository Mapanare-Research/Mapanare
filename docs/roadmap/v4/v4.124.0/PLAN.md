# Mapanare v4.124.0 — Rt.1: Unboxed Enum Payloads for Pointer-Fits Variants

> **Post-panel closeout release 4.** The biggest remaining performance
> gap. `enum_match` is 24x slower than C (gcc -O2) and 2x slower than
> Rust. The root cause is payload boxing: every match arm heap-allocates
> to extract the enum payload. The fix: if a variant's payload fits in
> a pointer-sized value (i64), store it inline in the tag+payload
> struct. No heap allocation for Int, Float, Bool payloads. Single-
> variant or Option-like enums benefit the most.

**Status:** PLANNED
**Breaking:** No (enum ABI internal; no stable FFI contract)
**Prerequisite:** v4.123.0
**Delta review:** No
**Full panel:** No (v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Close half the 2x performance gap vs Rust on enum-heavy code.

---

## Scope

The cross-language benchmark suite (v4.118.0) showed `enum_match` at:
- **C (gcc -O2):** baseline (1x)
- **Rust:** ~1.0x
- **Mapanare:** ~24x C, ~2x Rust

The bottleneck is payload boxing. The current enum representation:

```
{ i8 tag, i8* payload_ptr }
```

Every variant construction heap-allocates the payload. Every match arm loads from the heap pointer. For `Option<Int>`, that means a `malloc` for every `Some(42)` and a pointer chase for every `match` arm.

The optimization: if the payload fits in i64 (8 bytes), store it inline:

```
{ i8 tag, i64 payload_inline }
```

No heap allocation. No pointer chase. `Some(42)` becomes `{ 1, 42 }`. `None` is `{ 0, 0 }`. The match arm reads `payload_inline` directly and bitcasts to the correct type.

This applies to:
- `Option<Int>`, `Option<Float>`, `Option<Bool>` — the most common Option instantiations
- `Result<Int, String>` — Int payload is inline, String payload stays boxed (pointer + length > 8 bytes)
- User-defined enums with Int/Float/Bool/pointer-sized payloads

Enums with payloads larger than 8 bytes (e.g., structs with multiple fields) remain boxed. The existing heap path is unchanged for those.

## Phase 1 — Profile enum_match to confirm bottleneck

- [ ] Run the `enum_match` benchmark with perf or valgrind --tool=callgrind
- [ ] Confirm that `malloc`/`free` calls dominate the profile for Mapanare
- [ ] Count: how many heap allocations per iteration of the benchmark loop?
- [ ] Compare with Rust's assembly: Rust stores the payload inline (expected — confirm it)
- [ ] Document: "X% of runtime is in allocation, Y allocations per iteration"

## Phase 2 — Design the unboxed enum representation

- [ ] Define the inline threshold: payload size <= 8 bytes (sizeof(i64))
- [ ] Define the new struct layout for inline payloads:
  ```
  %EnumName = type { i8, i64 }  ; tag + inline payload
  ```
- [ ] For mixed enums (some variants inline, some boxed): use the boxed representation for all variants. Inline optimization only applies when ALL variants fit in i64.
- [ ] Document the decision: which enums qualify for inlining?
  - `Option<Int>`: yes (None=0, Some(Int)=inline)
  - `Option<String>`: no (String is {ptr, len} = 16 bytes)
  - `Result<Int, Int>`: yes (both payloads fit)
  - `Result<Int, String>`: no (String doesn't fit)
  - User enum with all-primitive payloads: yes
- [ ] Alternative: pointer-fits check (payload is a single pointer or smaller) — this would allow `Option<String>` if we only store the pointer. **Defer this to v5.x** — keep the rule simple: payload sizeof <= 8.

## Phase 3 — Implement in emit_llvm_text.py

- [ ] Add a helper: `_enum_payload_fits_inline(enum_type) -> bool` — checks if all variant payloads are <= 8 bytes
- [ ] Modify enum construction emission:
  - If inline: store payload directly into the i64 field (bitcast if needed)
  - If boxed: existing heap allocation path (unchanged)
- [ ] Modify enum match emission:
  - If inline: extract payload from the i64 field (bitcast to correct type)
  - If boxed: existing heap load path (unchanged)
- [ ] Modify enum destruction/drop-glue:
  - If inline: no free needed (no heap allocation)
  - If boxed: existing free path (unchanged)
- [ ] Handle the Option shortcut: `Some(x)` and `None` should use the inline path when the type parameter fits

## Phase 4 — Implement in self-hosted emitter

- [ ] Read `mapanare/self/emit_llvm.mn` — find enum construction and match emission
- [ ] Apply the same inline-vs-boxed logic
- [ ] This may be more complex in the self-hosted emitter (no dynamic type checking) — if too complex, defer to v4.126.0+

## Phase 5 — Re-run enum_match benchmark

- [ ] Run the same `enum_match` benchmark from v4.118.0
- [ ] Record the new Mapanare time
- [ ] Compute the ratio vs C and vs Rust
- [ ] Target: within 1.5x of Rust (was 2x before; closing half the gap)
- [ ] If the improvement is less than expected, profile again to find the next bottleneck

## Phase 6 — Golden suite verification

- [ ] Run all golden tests: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Specifically verify enum-heavy goldens:
  - `tests/golden/07_enum_match.mn` — the primary enum test
  - `tests/golden/14_option.mn` — Option<T> usage
  - `tests/golden/10_result.mn` — Result<T, E> usage
- [ ] `make test` — green
- [ ] `make lint` — clean
- [ ] Valgrind on enum-heavy goldens — no memory errors from the new inline path

## Phase 7 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.124.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Bottleneck confirmed: heap allocation dominates enum_match profile | profiling output |
| 2 | Inline threshold defined (payload <= 8 bytes) | design doc in SESSION_REPORT |
| 3 | `_enum_payload_fits_inline` helper implemented | diff of `emit_llvm_text.py` |
| 4 | Inline enum construction: no malloc for Int/Float/Bool payloads | IR diff showing no `call @malloc` for `Some(42)` |
| 5 | Inline enum match: no pointer load for Int/Float/Bool payloads | IR diff showing direct i64 extract |
| 6 | enum_match benchmark improved (target: within 1.5x of Rust) | benchmark output |
| 7 | `07_enum_match.mn` golden passes | test log |
| 8 | `14_option.mn` golden passes | test log |
| 9 | `10_result.mn` golden passes | test log |
| 10 | Valgrind clean on enum-heavy goldens | valgrind output |

---

## What this release does NOT do

- **Optimize enums with large payloads** — structs with multiple fields stay boxed. Only payloads <= 8 bytes go inline.
- **Change the enum ABI for FFI** — the enum representation is internal to the compiler. No stable FFI contract exists.
- **Implement tagged unions** — the representation is still tag + payload, not a C-style union. Tagged unions are v5.x.
- **Fix enum serialization** — if enum serialization exists, it may need updating. But no serialization code exists yet.
- **Run a panel** — the next panel is v4.130.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Inline representation breaks enums with mixed payload sizes | medium | high | Phase 2 rule: ALL variants must fit for inline. Any oversized variant forces boxed for entire enum. |
| Bitcast from i64 to Float produces wrong values | low | high | Test specifically: `Some(3.14)` stored as i64 bitcast, extracted correctly |
| Drop glue skips free for inline payloads that contain heap pointers | medium | high | Inline threshold excludes types with heap pointers (String, List, etc.) — only pure values inline |
| Self-hosted emitter fix is too complex for one sprint | medium | medium | Phase 4 can be deferred to v4.126.0+ without blocking the benchmark improvement |
| Benchmark improvement is less than expected (< 1.3x improvement) | medium | low | Profile to find next bottleneck; document for future optimization |

---

## After v4.124.0

v4.125.0 is the benchmark refresh + second flaky audit + documentation update. All correctness fixes (v4.121.0, v4.122.0) and performance fixes (v4.124.0) are in. v4.125.0 measures everything, confirms stability with a 5x flaky audit, updates the benchmark report, and prepares documentation for the v4.130.0 panel. No code changes — pure measurement and documentation.
