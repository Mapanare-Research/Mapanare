# Mapanare v4.148.0 — E4: `string_concat` vs Rust

> **Close the string-append gap.** `string_concat` is the worst
> cross-language showing in the v4.144.0 baseline — 5–10× slower than
> Rust, depending on run. The root cause is almost certainly in the
> runtime append path (`__mn_string_concat` or equivalent in
> `runtime/native/mapanare_core.c`): missing amortized capacity
> growth and/or missing small-string inline optimization that Rust's
> `String::push_str` gets for free via `Vec<u8>`. This release fixes
> the append hot path and, if the IR diff points that way, adds a
> StringBuilder lowering in the emitter.

**Status:** PLANNED
**Breaking:** No (runtime ABI is internal; stdlib surface unchanged)
**Prerequisite:** v4.147.0 shipped (E3 recorded)
**Estimated work:** 1–2 days
**Theme:** E4 — `string_concat` append hot path

---

## Why this release, why now

The v4.144.0 benchmark pack shows `string_concat` running 5–10× slower
than Rust — the widest Rust gap in the corpus. Strings are load-bearing
for anything user-facing (HTTP, logging, formatting), so this number
is the one that most undermines the "as fast as Go" claim for real
workloads.

The workload is a tight loop:

```mn
let mut s: String = ""
for i in range(10000) {
    s = s + str(i)
}
```

Each iteration allocates, copies, and frees. Rust's `String::push_str`
uses `Vec<u8>` under the hood — amortized O(1) growth with doubling
capacity, plus SSO (small-string optimization) for ≤ 23-char strings
on 64-bit. Mapanare's current path (best guess, pre-IR-diff) likely
allocates a fresh buffer every concat, making the loop O(n²) in total
allocation cost.

Closing this gap has two legitimate angles:
1. **Runtime side:** `__mn_string_concat` does amortized growth
   in-place when the destination has capacity. This is the biggest win.
2. **Emitter side:** Detect the `s = s + x` pattern and lower it to
   `__mn_string_append_inplace` when the source is unshared, avoiding
   the copy+free round-trip.

The IR diff tells us which side matters more — but either way, this
is a runtime-first release.

## Baseline (measure before touching code)

```bash
echo "4.148.0" > VERSION
make build-rt
python3 scripts/build_stage1.py

python3 benchmarks/cross_language/run_benchmarks.py --only string_concat --runs 20 \
  --output benchmarks/cross_language/v4.148.0-baseline.json

python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.148.0-full-baseline.json

# Allocation diagnostic — count malloc/free per run
valgrind --tool=massif \
  ./benchmarks/cross_language/target/string_concat_mn 2>&1 \
  | tee docs/roadmap/v4/v4.148.0/massif-baseline.log
ms_print docs/roadmap/v4/v4.148.0/massif-baseline.log \
  > docs/roadmap/v4/v4.148.0/massif-baseline.txt
```

Write `docs/roadmap/v4/v4.148.0/BASELINE.md`:
- `string_concat` median wall (Mapanare, Rust, Go, Python)
- Ratio to Rust (baseline target: from 5–10× to ≤ 2×)
- Per-iteration malloc count + peak RSS (from massif)
- Total bytes allocated across the full loop

## Hypothesis

The Mapanare string-concat path is O(n²) in allocation (fresh buffer
per concat, no capacity reuse). Rust's `String::push_str` is amortized
O(1) because `Vec<u8>` doubles capacity on growth.

Concrete IR / runtime-level differences expected:

- **Allocation count per run:** Mapanare ~20,000 allocs (2 per concat
  × 10,000 iter); Rust ~14 allocs (capacity doublings: 1,2,4,...,16384).
- **Copy count per run:** Mapanare copies full-length on every concat;
  Rust copies only the newly appended bytes when capacity suffices.
- **Runtime path:** Mapanare's `__mn_string_concat` likely allocates
  `len(a) + len(b)` fresh and copies both; Rust's `push_str` appends
  in-place when capacity allows.

## Phase 1 — IR + runtime diff

```bash
# Mapanare IR
python3 -m mapanare emit-llvm benchmarks/optimizer/string_concat.mn -O3 \
  -o /tmp/sc.mn.ll

# Rust IR
(cd benchmarks/cross_language/rust/string_concat && \
  RUSTFLAGS="--emit=llvm-ir -C opt-level=3" cargo build --release 2>&1 | tail -3 && \
  cp target/release/deps/string_concat*.ll /tmp/sc.rs.ll)

# Extract inner loop from each
culebra extract /tmp/sc.mn.ll main > /tmp/main_mn.ll

# Read the Mapanare runtime path
grep -n "__mn_string_concat\|__mn_string_append" runtime/native/mapanare_core.c \
  > docs/roadmap/v4/v4.148.0/runtime-string-path.txt
```

Write `docs/roadmap/v4/v4.148.0/IR_DIFF.md` with:
- Inner loop IR (Mapanare vs Rust) — count the `call` instructions
- Annotated runtime path from `mapanare_core.c` — what does
  `__mn_string_concat` actually do?
- `String::push_str` equivalent from Rust std (cite LLVM IR from the
  Rust .ll file; don't cite the source repo)

## Phase 2 — Form hypothesis

Write `docs/roadmap/v4/v4.148.0/HYPOTHESIS.md`:

```markdown
# E4 Hypothesis

**Claim:** `__mn_string_concat` allocates a fresh `(len_a + len_b)`
buffer every call and copies both operands. Rust's `push_str`
amortizes via capacity doubling. Adding capacity-field + amortized-
growth logic to Mapanare's string struct closes ≥ 60 % of the gap.

**Concrete design:**
- Mapanare `String` struct: `{ ptr, len, cap }` (was `{ ptr, len }`?)
- `__mn_string_concat(a, b)`:
  - If `a` is unshared AND `a.cap >= a.len + b.len`: memcpy in-place,
    update len; return a.
  - Else: allocate `max(2 * a.cap, a.len + b.len)`, copy, return new.
- `__mn_string_alloc`: set `cap = max(16, len)` initially.

**Expected delta:** 60–90 % wall reduction on `string_concat`; ≥ 100×
reduction in per-iteration malloc count.
```

Include the precise struct-layout change and a note on whether the
runtime `MnString` ABI is public (it is not — only the
`{ptr, len, maybe-heap-bit}` user-visible layout is; the capacity
is a private detail).

## Phase 3 — Patch

Primary target: `runtime/native/mapanare_core.c`. Specifically:

1. **Struct layout:** Extend `MnString` (or equivalent) with a
   `capacity` field if not already present. Check `MnString` layout
   against what `emit_llvm_text.py` already assumes — if the emitter
   hardcodes `{ptr, i64}` for strings, add a third field and update
   the emitter accordingly.
2. **`__mn_string_concat`:** Amortized growth:
   ```c
   if (!a->shared && a->cap >= a->len + b->len) {
       memcpy(a->ptr + a->len, b->ptr, b->len);
       a->len += b->len;
       return a;  // no alloc, no free
   }
   size_t new_cap = a->cap * 2;
   if (new_cap < a->len + b->len) new_cap = a->len + b->len;
   // ... allocate, copy, free old, return new
   ```
3. **`__mn_string_alloc`:** Initialize `cap = max(16, len)`.
4. **Emitter-side `StringBuilder` lowering (optional):** If the IR
   diff shows the compiler emits `s = concat(s, x)` even when `s` is
   unshared, short-circuit to an in-place append call. This may not
   be needed if the runtime fix alone wins.

Secondary target: `mapanare/emit_llvm_text.py` — update any hardcoded
`MnString` layout assumptions (if present).

Regression tests: `tests/runtime/test_string_growth.py` — verify
amortized growth, capacity doubling, and that existing string
semantics (immutability from user POV, interning, hashing) are
unchanged.

Estimated diff: 50–150 LOC across the runtime + emitter.

## Phase 4 — Re-measure

```bash
make build-rt
python3 scripts/build_stage1.py

python3 benchmarks/cross_language/run_benchmarks.py --only string_concat --runs 20 \
  --output benchmarks/cross_language/v4.148.0-patched.json
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.148.0-full-patched.json

valgrind --tool=massif \
  ./benchmarks/cross_language/target/string_concat_mn 2>&1 \
  | tee docs/roadmap/v4/v4.148.0/massif-patched.log

# Sanitizer sweep — string layout change can trip UB easily
bash scripts/run_asan_goldens.sh 2>&1 | tail -5
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh 2>&1 | tail -5
```

**5 % rule:**
- `string_concat` must improve ≥ 5 % (target: ≥ 60 %; ≤ 2× Rust).
- No non-target bench regresses > 2 %.
- Zero new valgrind ERRORS / ASan ASAN_ERROR.

## Phase 5 — Record

Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

```
| E4 | string_concat: amortized capacity growth | <win/dead-end> | <delta>% wall, <malloc-ratio>× fewer allocs | mapanare_core.c::__mn_string_concat | v4.148.0 |
```

Write `RESULTS.md` and `SESSION_REPORT.md`. The SESSION_REPORT should
document any ABI-visible change to `MnString` (even if the user-visible
surface is unchanged) and any tests that had to be adjusted for the
new capacity field.

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `BASELINE.md` with pre-patch numbers + massif allocation profile | yes |
| 2 | `IR_DIFF.md` with runtime-path analysis and inner-loop comparison | yes |
| 3 | `HYPOTHESIS.md` with concrete design for `MnString` + concat | yes |
| 4 | `__mn_string_concat` amortized growth implemented | yes |
| 5 | `MnString` layout updated with `capacity` field (if not present) | yes |
| 6 | Emitter aligned with new `MnString` layout (if struct changed) | yes |
| 7 | `tests/runtime/test_string_growth.py` ≥ 5 tests, all pass | yes |
| 8 | `string_concat` improves ≥ 5 % (target: ≤ 2× Rust) | yes |
| 9 | No other bench regresses > 2 % | yes |
| 10 | Zero new valgrind ERRORS | yes |
| 11 | Zero new ASan ASAN_ERROR | yes |
| 12 | `RESULTS.md` with before/after wall + allocation count | yes |
| 13 | `PERF_EXPERIMENTS.md` entry added | yes |
| 14 | Non-bootstrap pytest: ≥ 5,178 / 0 (+5 string-growth tests) | yes |
| 15 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 16 | Native goldens: 54 / 66 | yes |
| 17 | Fixed-point: within `DIFF_THRESHOLD=100` | yes |
| 18 | All 8 CI gates green | yes |
| 19 | SESSION_REPORT.md written | yes |
| 20 | CHANGELOG + CLAUDE.md + ROADMAP.md updated | yes |
| 21 | Tag `v4.148.0` pushed to origin | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `MnString` layout change breaks interning / hashing / `len` bit-packing (v4.133.0 An.1 touched `_lenheap` bit-63 masks) | medium | high | Audit every `_lenheap` / `MnString` callsite in the tree before editing the struct; run the full `tests/runtime/` suite after; verify `len` packing still works |
| Amortized growth is correct but interning logic still allocates a fresh intern entry per distinct `s` value — no speedup | medium | medium | Check if `__mn_string_concat` triggers interning; if so, bypass interning for intermediate concat results (only intern at final assignment or at explicit `intern()` call) |
| In-place mutation of `a` breaks aliased reads elsewhere (another var holding the same pointer) | high | CRITICAL | Gate in-place append on a shared/ref-count check (`a->shared == false`). If the runtime doesn't track sharing, use the conservative path (always allocate) and take a smaller win |
| FFI / C stdlib / Dato depends on current `MnString` layout | low | high | Grep the Dato repo + `stdlib/` for `MnString` struct access; keep the existing fields at their current offsets, only append new fields |
| Test suite relies on specific malloc count (some hardening tests) | low | low | Update tests that pin an alloc count; those were pinned against the O(n²) behavior |

## What this release does NOT do

- Does not change the user-visible `String` API or semantics. Strings
  remain immutable from the user's POV; the mutability is an internal
  optimization applied only when the compiler proves the source is
  unshared.
- Does not introduce SSO (small-string inline) — the hypothesis says
  amortized growth is the big win; SSO is a separate experiment if
  the gap isn't closed.
- Does not touch unicode handling, UTF-8 validation, or encoding.
- Does not mirror into `mapanare/self/emit_llvm.mn` (parity follow-up).
- Does not chase `string_concat` below 1.0× Rust — ≤ 2× is the target.

## Carry-forward after v4.148.0

- If win: new Cb.14 or similar opens for self-hosted parity, LOW.
  If SSO was needed on top of amortized growth to hit ≤ 2×, open
  SSO.1 for a later release.
- If dead end (amortized growth alone doesn't close the gap): open
  SSO.1 with HIGH priority and schedule for v4.149.x or v4.150.x.
- If partial: document which runs hit the target and which didn't;
  note allocator-dependent variance.
- All string benchmark numbers republished at v4.153.0.
