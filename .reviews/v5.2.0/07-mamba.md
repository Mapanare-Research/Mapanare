# Panel v5.2.0 — Mamba (C Runtime / Performance)

**Score:** 9.6 / 10
**Grade:** EXCEEDS
**Delta vs v4.154.0:** +0.3

## Summary

All five carry-forwards from v4.154.0 are closed. Every one of them.
Bn.2, Bn.3, Bn.4, Perf.1, Perf.2 — resolved across 12 releases with
correct implementations and honest measurements. Perf.1 (inline list
ops) is the single most impactful codegen change since E5 (ABI.1 sret),
and Perf.2 (lazy coro threads) closes the "not a portable claim"
complaint I have been making since v4.150.0. The C runtime grew +276
lines and +1,560 bytes across 12 releases — disciplined growth for
substantive functionality.

Three stream C runtime tests fail. I traced the root cause live (see
below). It is a real bug, not a test artifact.

## Carry-forward closures (all 5)

### Perf.1 CLOSED (v5.1.0) — Inline list ops: THE BIG WIN

`mapanare/emit_llvm_text.py:4518` — `_tsz(ety) == 8` gate on the
inline path. Verified in source. The codegen at lines 4519-4546
(`_do_idx_get`) and 4584-4610 (`_do_idx_set`) replaces the opaque
`call ptr @__mn_list_get(ptr, i64)` with:

```llvm
%lg.lenp = getelementptr inbounds {ptr, i64, i64, i64, i64}, ptr %la, i32 0, i32 1
%lg.len = load i64, ptr %lg.lenp
%lg.oob = icmp uge i64 %idx, %lg.len
br i1 %lg.oob, label %trap, label %ok
trap:
  call void @abort()
  unreachable
ok:
  %lg.dp = getelementptr inbounds {ptr, i64, i64, i64, i64}, ptr %la, i32 0, i32 0
  %lg.data = load ptr, ptr %lg.dp
  %lg.ep = getelementptr inbounds i64, ptr %lg.data, i64 %idx
  %lg.v = load i64, ptr %lg.ep
```

This is correct. The gate fires for `i64`, `double`, `ptr` — all
8-byte types. String (16B), Bool (1B), and structs correctly remain
on the slow path. The bounds check uses unsigned comparison (`uge`)
which also catches negative indices. The trap calls `abort()` instead
of the runtime's `fprintf + abort` — slightly less diagnostic, but
correct and inlinable.

**Impact:** quicksort 2.99x Rust -> 1.14x Rust (**-62%**). This is
the improvement I predicted at v4.154.0:

> "the remaining gap is architectural (opaque function calls)"
> — Mamba, v4.154.0 review, line 198

The gap was opaque function calls. The fix was inlining them. The
improvement is proportional. LLVM can now see through to the backing
buffer and apply SROA, vectorization, and loop hoisting. The session
report claims are verified by the codegen.

Self-hosted mirror at `mapanare/self/emit_llvm.mn` (+60 lines) exists.
Not verified in detail — I trust the golden test harness (54/66
unchanged).

### Perf.2 CLOSED (v5.1.4) — Lazy coro threads: THE PORTABLE CLAIM

`runtime/native/mapanare_runtime.c:1670-1684` — new struct fields:
`worker_cap`, `live_workers` (atomic), `spawned[]`,
`worker_exited[]` (atomic), `spawn_lock` mutex. Verified in source.

The implementation has four parts:

1. **Pre-create 2 workers** (lines 1876-1900): `prime = 1` when
   `cap >= 2`. Worker 0 is the caller (main thread). Worker 1 is
   eagerly spawned. This matches the `ASYNC_THREADS=2` configuration
   that produced the original 0.85x Go number.

2. **Lazy spawn** (lines 1953-1964): `active_tasks > workers * 8`
   triggers spawn under `spawn_lock`. Double-check pattern: read
   `live_workers` outside lock, re-read under lock before spawning.
   Correct — avoids thundering herd.

3. **Idle exit** (lines 1774-1793): Workers idle > 100 ms exit when
   `live_workers > 1`. Exit sets `worker_exited[id] = 1` under
   `spawn_lock`. Floor of 2 workers is maintained. The floor is
   correct — 1 spawned thread + worker 0 (caller) = 2 participants.

4. **Race-safe teardown** (lines 2029-2043): `spawned[]` array
   iteration. Only joins threads that were actually created. Workers
   that idle-exited have already terminated; `pthread_join` returns
   immediately. Clean.

**Concern addressed:** The `ATOMIC_RELAXED` load at line 1783 inside
`spawn_lock` is safe because the mutex provides the necessary
ordering. The subsequent `fetch_sub` at line 1785 uses `ACQ_REL`.
The `worker_exited` store at line 1788 uses `RELEASE`. The consuming
load at line 1813 (`mn_find_worker_slot`) uses `ACQUIRE`. The
happens-before chain is correct.

**Impact:** Default async geomean 2.3 ms -> 1.19 ms (**0.91x Go**).
TSan: 0 races. Valgrind: 0 leaks. This closes the complaint I made
at v4.154.0 (lines 174-180): the headline now holds at default
settings, on any core count. The env var is preserved as an override
but is no longer required. My exact words were:

> "The alternative — lazy thread creation — is a v5.x scope item."
> — Mamba, v4.154.0 review, line 55

It shipped. It works. It is correct.

### Bn.2 CLOSED (v5.1.2) — geomean arithmetic

`benchmarks/cross_language/run_benchmarks.py:57-67`. Verified:

```python
def geomean(ratios: list[float]) -> float:
    if not ratios or any(r <= 0 for r in ratios):
        return 0.0
    return math.exp(sum(math.log(r) for r in ratios) / len(ratios))
```

Doctests included. JSON output now carries `"geomean_ratios"` field.
The computation lives in the benchmark script, not in external
documents. This resolves the 3-cycle carry-forward (v4.144.0 ->
v4.154.0 -> v5.1.2). The arithmetic was wrong for 3 panels. It is
now correct.

### Bn.3 CLOSED (v5.0.6) — JSON version field

Already verified at PARITY_GAPS.md historical section: `VERSION` file
is read at import time. The `"4.125.0"` hardcode is gone except in
a docstring. 4-cycle carry-forward finally closed.

### Bn.4 CLOSED (v5.1.2) — C struct_alloc benchmark

`benchmarks/cross_language/c/struct_alloc.c` — `grep malloc` returns
only the comment explaining the change (lines 6-8): "of malloc+free
per iteration... Prior version measured malloc throughput." Zero
`malloc` or `free` calls in the hot loop. Struct returned by value.
Matches Rust/Mapanare methodology. The Mn/C geomean is now a
meaningful number.

## What held

- **Sanitizers:** Valgrind 62 WARNINGS_ONLY, 2 ERRORS (GPU dlopen,
  not memory safety — down from 4 ERRORS at v4.154.0). Ge.1r
  generics residuals confirmed CLOSED. TSan 0 races on the new lazy
  scheduler. The C runtime changes are sanitizer-clean.

- **libmapanare_rt.a:** 269,886 bytes (+1,560 from v4.154.0, +0.6%).
  Three patches touched C source across 12 releases (Perf.1 is
  emitter-only). Growth is proportional.

- **Runtime line count:** 14,963 total (+276 from v4.154.0, +1.9%).
  Perf.2 is the majority of the growth. Minimal for the functionality
  delivered.

- **Golden tests:** 54/66 unchanged across 32+ releases. The inline
  list path did not regress any golden. The lazy scheduler did not
  regress any golden.

## What concerns me

### Stream-C — 3 C runtime test failures (NEW, MEDIUM)

Three stream tests fail: `test_stream_from_list_collect`,
`test_stream_map`, `test_stream_filter`. MEASUREMENTS.md classifies
these as "wrong element values." I traced the root cause:

The C test harness at `tests/native/test_c_runtime.c:1034` does:

```c
MnList list = {0};
for (int64_t i = 1; i <= 3; i++) __mn_list_push(&list, &i);
```

`{0}` zero-initializes `elem_size` to 0. The first `__mn_list_push`
hits the slow path (data is NULL) and the Ge.1r fallback at
`mapanare_core.c:1200` sets `elem_size = 256`:

```c
if (list->elem_size <= 0 || list->elem_size > 65536) list->elem_size = 256;
```

Elements are now stored at **256-byte stride**. But the stream
pipeline is created with:

```c
MnStream *s = __mn_stream_from_list(&list, sizeof(int64_t));
```

`elem_size = 8`. The stream's `_stream_list_next` at line 2642 reads:

```c
void *elem = st->list->data + st->index * s->elem_size;
```

Data written at 256B stride, read at 8B stride. The second and third
elements read garbage.

**Before Ge.1r (v5.1.1):** The fallback was `elem_size = 8`, which
happened to match `sizeof(int64_t)`. The tests passed by coincidence.
Ge.1r raised the fallback to 256 (correct for the generics
self-compilation path) and broke the tests.

**The fix is in the test:** use `__mn_list_new(sizeof(int64_t))`
instead of `{0}`. This is a 3-line change across 3 tests. However,
the Ge.1r fallback silently corrupting element stride — rather than
asserting or preserving a caller-specified elem_size — is a design
smell. A `__mn_list_push` on a `{0}`-initialized list should either
abort (caller must call `__mn_list_new`) or use the elem_size derived
from the push argument. It should not silently pick 256.

Severity: MEDIUM. The test failure is cosmetic. The silent stride
corruption is a latent footgun for any C caller that forgets
`__mn_list_new`.

### Fixed-point BROKEN (regression from NEAR)

MEASUREMENTS.md section 3: stage2.ll fails `llvm-as` with
`use of undefined value '%_inl0_6_t4'`. Root cause: v5.1.2
re-enabled `inline_small_functions` and the In.1 rename fix
(`%_inlN_M_dst`) works for golden tests but fails on the
self-compilation path.

This is a quality regression. At v4.154.0 the fixed-point was NEAR
(4 diff, version metadata only). At v4.134.0 it was STRICT. Now it
is BROKEN. The In.1 fix was tested against 54 golden tests + 4
dedicated rename tests — but the self-hosted compiler compiling itself
exercises more complex inlining patterns.

This is not a C runtime issue — it is an MIR optimizer issue. But
it is a regression on my watch because the fixed-point is a
whole-compiler quality signal.

### Lint failures (2 tests) — cosmetic

4 files need `black`, 9 `ruff` errors in v5.2.0 registry code. This
is a process failure (committed without running `make lint`), not a
runtime issue. Not docking — it does not touch my axis.

## Score rationale

Starting from v4.154.0 baseline of 9.3:

- **Perf.1 inline list ops — quicksort 2.99x -> 1.14x Rust**: **+0.4**
  The single largest per-benchmark improvement since E5 (struct_alloc).
  Correct gate, correct codegen, correct slow-path fallback. LLVM
  can now optimize list-heavy code. The geomean moved from 1.30x to
  1.10x Rust — the first time CPU geomean has been under 1.15x.

- **Perf.2 lazy coro threads — 0.91x Go at default**: **+0.2**
  Correct implementation. Race-safe. Floor-2 guarantee. TSan clean.
  Closes my "not a portable claim" complaint. The headline is now
  citable without qualifiers.

- **Bn.2 + Bn.3 + Bn.4 (benchmark reporting cleanup)**: **+0.1**
  Three carry-forwards closed, one of them 4 cycles old. The
  benchmark tooling is now trustworthy. `geomean()` is in the script,
  not in my head.

- **Ge.1r valgrind closure (4 ERRORS -> 2 ERRORS)**: **+0.05**
  Not my docket (Viper's), but the sanitizer improvement is on my
  axis. The remaining 2 are GPU dlopen, not memory safety.

- **Stream-C 3 test failures**: **-0.15**
  Real bug, traced to Ge.1r elem_size fallback. The test fix is
  trivial (use `__mn_list_new`), but the silent 256B stride on
  `{0}`-initialized lists is a latent footgun. MEDIUM because it
  affects C runtime API surface, not just tests.

- **Fixed-point BROKEN (was NEAR)**: **-0.15**
  Quality regression. The inliner re-enable was premature — should
  have gated on stage2 self-compilation success, not just golden
  tests. Not a C runtime issue per se, but the fixed-point is a
  whole-compiler quality signal.

- **12 releases, 19 carry-forward closures, 5/5 Mamba items**: **+0.15**
  The closure rate is the highest in the project's history.
  Every item I flagged was addressed. The implementations are correct,
  not band-aids.

**Net: 9.3 + 0.4 + 0.2 + 0.1 + 0.05 - 0.15 - 0.15 + 0.15 = 9.90.**

Capped at **9.6** because the fixed-point regression and the stream
test failures are real quality signals that prevent a 9.9. The runtime
is excellent. The optimizer's self-compilation path is not.

## Carry-forward (for v5.3.0+)

| Docket | Severity | Scope |
|---|---|---|
| **Stream-C** | MEDIUM | 3 stream C tests fail — test-side fix: `__mn_list_new(sizeof(int64_t))` instead of `{0}`; also consider asserting in `__mn_list_push` when `elem_size == 0 && data == NULL` instead of silent 256B fallback |
| **In.1-stage2** | LOW | Inliner SSA rename breaks stage2 self-compilation — gate inliner enable on stage2 llvm-as success, not just golden tests |
| **Li.1** | LOW | LICM: unit tests pass, live goldens regress — needs fixpoint + preheader insertion |
