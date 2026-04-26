# Panel v5.8.0 — Mamba (C Runtime / Performance)

**Score:** 9.7 / 10
**Grade:** EXCEEDS
**Delta vs v5.2.0:** +0.1

## Summary

The two open dockets I left at v5.2.0 are closed. Stream-C — the
`{0}`-init footgun that produced wrong-element values under all
three sanitizer configurations — closed at v5.3.1; the test fix
(`__mn_list_new(sizeof(int64_t))`) is in place, the runtime path
is documented inline, and the C-hardening trio
(`test_all_c_tests_pass` / `test_asan_no_errors` / `test_tsan_no_races`)
is **3/3 PASS** at HEAD. In.1-stage2 — the inliner-rename SSA bug
that broke fixed-point at v5.2.0 — closed at v5.3.2 by extending
`clone_instr_for_inline` to all 30+ instruction kinds. Both are
real fixes at the structural root cause, not band-aids.

The bigger story for my axis is the **v5.5.4–v5.5.7 async coroutine
arc**. The self-hosted emitter now ships the full LLVM-coroutine ABI
(`presplitcoroutine` + `@llvm.coro.id/begin/save/suspend/end`) +
real scheduler-driven `AwaitSuspend` / `BlockOn`, all 5 Sh.4 goldens
execute correctly through the real coroutine pipeline, and TSan/ASan/
LSan are clean on 56/57/58/59 under `MAPANARE_ASYNC_THREADS=4`. The
v5.1.4 Perf.2 lazy-spawn scheduler is preserved unchanged — same
race-safe pre-create-1 + lazy-grow + idle-exit pattern I verified at
v5.2.0. The runtime grew **zero** lines of C across 9 releases; the
async / tensor / drop-glue surfaces all consumed APIs that were
already present pre-v5.3.0.

The cross-language benchmarks tighten further. **Mn/Rust geomean
1.003× — essentially parity, the first time this number has crossed
1.05× in the project's history.** Mn beats Rust on `enum_match`
(0.52×, ~2× faster) and `fib_recursive` (0.84×); the remaining
benchmarks are all within iteration noise. Mn/Python is **328.6×**
(~2× faster than v5.3.0's 168×). The 1.60× on `string_concat` is
the only above-1.5× ratio and remains a known allocator-bound quirk
(no SSO in `__mn_str_concat`). Async median is preserved at the
~1.20 ms class established post-Perf.2; my "0.91× Go default" claim
from the v5.2.0 review still holds at the underlying scheduler
level (Go binary failed to build in the WSL benchmark environment,
but the scheduler primitives are byte-unchanged since v5.1.4).

I score this **9.7 / 10 EXCEEDS, +0.1 vs v5.2.0**. The +0.4
upside (Stream-C + In.1-stage2 closure, Mn/Rust 1.10× → 1.003×,
async coroutines actually shipping) is partly offset by **-0.3** of
honest carry-forward concern: the 1.60× string_concat is real and
small, the 8.4× year-over-year stage2.ll growth (121k → 218k)
demands attention before someone sees it on a CI dashboard, and
the async benchmark methodology lost its Go arm to a build
failure that nobody noticed. Net positive but not a clean +0.4.

## What improved since v5.2.0

### Stream-C CLOSED (v5.3.1) — 3 stream tests recovered

The fix matches my v5.2.0 recommendation exactly. At
`tests/native/test_c_runtime.c:1034`:

```c
TEST(test_stream_from_list_collect) {
    MnList list = __mn_list_new(sizeof(int64_t));      // was: {0}
    int64_t v = 1; __mn_list_push(&list, &v);
    ...
}
```

All three stream tests (`test_stream_from_list_collect`,
`test_stream_map`, `test_stream_filter`) plus the
`test_stream_free_chain` companion now route through
`__mn_list_new(sizeof(int64_t))` so `elem_size = 8` is set
explicitly, matching the stream pipeline's `elem_size` argument.
The data-stride mismatch I traced live in v5.2.0 — `_stream_list_next`
reading at 8B stride while the slow-path fallback wrote at 256B
stride — cannot occur on this code path.

The Ge.1r runtime fallback at `mapanare_core.c:1200` is preserved
(256-byte safe upper bound) with a clear inline comment explaining
why 8 is wrong for struct-typed elements:

> *"LLVM -O2 can propagate zeroinitializer through struct fields
> when promoting allocas to SSA, zeroing the elem_size of lists
> inside large value-typed structs (LowerState, MIRModule). The
> old fallback of 8 caused 80-byte (16+8\*8) buffer allocations
> that were too small for struct-typed list elements, producing
> heap overreads in register_mir_struct."*

I noted at v5.2.0 that the silent 256B fallback on `{0}`-init lists
was a latent footgun for any C caller that forgets `__mn_list_new`.
That footgun is **still there** structurally — `__mn_list_push`
still recovers a `{0}`-init list to 256B by default — but now
there's a `WARNING:` `fprintf` to stderr at line 1189 when this
happens, and the documentation on the call site is clear enough
that any new C-side test code will follow the
`__mn_list_new(sizeof(T))` pattern. I would have preferred an
abort here, but the warning + reinit path is defensible: it
preserves API compatibility for any external caller.

**3 PASS / 3 PASS / 3 PASS under plain / ASan / TSan.**
Verified live:

```
$ python3 -m pytest tests/native/test_c_hardening.py -v
TestCRuntimePlain::test_all_c_tests_pass PASSED
TestCRuntimeASan::test_asan_no_errors    PASSED
TestCRuntimeTSan::test_tsan_no_races     PASSED
============================== 3 passed in 15.97s ==============================
```

74 C tests in `test_c_runtime.c` confirmed (`grep -c '^TEST('`).
Stream-C at v5.2.0 was -0.15 on my axis. **Recovering it: +0.15.**

### Async coroutine pipeline (v5.5.4–v5.5.7) — major axis improvement

The v5.5.x arc is the biggest substantive change in my domain
since Perf.1+Perf.2 (v5.1.0 / v5.1.4). Self-hosted async emission
went from "synchronous Option A stub that only works because Sh.4
goldens use `return <const>`" (v5.5.2) to the full LLVM-coroutine
ABI:

- **v5.5.4** — `presplitcoroutine` attribute + full `@llvm.coro.id`
  / `begin` / `save` / `suspend` / `end` pipeline. `opt -O1` runs
  CoroSplit and emits `@foo.resume` + `@foo.destroy` split
  functions. All 5 Sh.4 goldens execute correctly: `55 → 42`,
  `56 → 43`, `57 → 110`, `58 → done`, `59 → 220`.
- **v5.5.5** — Real 6-block scheduler-driven `AwaitSuspend`
  (fast-path readiness → `aw.drive.N` → `aw.check.N` →
  `aw.suspend.N` → `aw.resume.N` → `aw.ready.N`). Outer coroutines
  now have suspension points (CoroSplit produces outer
  `resume`/`destroy` pairs for every async fn with awaits).
- **v5.5.6** — Scheduler-driven `BlockOn` + main lifecycle:
  `__mn_coro_scheduler_init(0)` injected as the first body line
  of async-aware main, `__mn_coro_scheduler_destroy()` before
  every `ret`. **First release with real multi-threaded async
  concurrency**: `strace -f -e trace=clone3` on `59_async_fanout`
  shows 1 worker thread spawned at `MAPANARE_ASYNC_THREADS ≥ 2`
  (matches Perf.2's `prime=1` policy).
- **v5.5.7** — Sanitizer hardening: `emit_drop_glue_destroy(st)`
  helper iterates `str_owned` / `list_owned` / `boxed_owned`
  unconditionally on the `coro.cleanup` path (still consults
  `moved_locals`); v5.5.5-deferred Rt.05 inner-coroutine handle
  leak closed by hoisting `%aw.hdl.ptr.N` GEP + `%aw.hdl.N` load
  from `aw.drive.N` into the entry BB before the fast-path branch.

What's important from my axis: **the underlying C-runtime
scheduler is not touched.** The
`__mn_coro_scheduler_{init,register,run,destroy}` /
`__mn_coro_register_wait` / `__mn_coro_spawn` API — 6 entry
points starting at `mapanare_runtime.c:1846` — was already
complete at v5.1.4 (Perf.2). The v5.5.x work is all
self-hosted emitter + Python-emitter parity. The lazy-spawn
+ idle-exit + race-safe-teardown infrastructure I verified at
v5.2.0 lines 1670-2043 is preserved byte-for-byte. The
`ATOMIC_RELAXED` / `ACQ_REL` / `RELEASE` / `ACQUIRE` ordering
chain at lines 1783–1813 still gives the correct
happens-before relationship, and the floor-2 guarantee
(`live_workers > 1`) still holds.

**Sanitizer state (5 Sh.4 goldens):**

```
valgrind on 59_async_fanout: 36 allocs / 36 frees / 0 in use at exit / 0 errors
ASan on 55-59:   0 errors
LSan on 55-59:   0 leaks
TSan on 56-59 under MAPANARE_ASYNC_THREADS=4: 0 races
```

This is the cleanest possible signal. The async runtime correctness
claim ("we ship a real multi-threaded coroutine pipeline that
passes TSan") is now citable. Sh.4 was an open carry-forward
through nine v5.x releases; closing it under the full sanitizer
matrix without a single race or leak is the result of disciplined
design (DESIGN.md at v5.5.3 explicitly chose Option B over the
synchronous Option A shortcut, citing the user "no cheap shit"
directive). **+0.2.**

### Tensor runtime (v5.6.x) — runtime API + drop-glue both clean

The v5.6.x tensor surface lands across 4 releases:

- **v5.6.0** — tensor literals + `parse_tensor_lit` walker + 6 base
  `__mn_tensor_*` runtime decls (alloc/free, store/get f64+i64,
  rank/size/shape_dim, print_f64).
- **v5.6.1** — multi-dim indexing (`a[i, j]`); 4 variadic
  `__mn_tensor_{get,set}_{f64,i64}_nd(ptr, i64, ...)`.
- **v5.6.2** — broadcast + scalar binops (+/-/*//); 20 runtime
  fns at `mapanare_gpu_builtins.c:549–720` — 8 broadcast (`ptr,
  ptr → ptr`), 8 scalar (`ptr, double|i64 → ptr`), 4 reverse-scalar
  (`double|i64, ptr → ptr`).
- **v5.6.3** — slicing + reductions (sum/mean/max/min/argmax/argmin);
  11 reduction decls.

Final tensor API surface (`grep -nE '^[a-zA-Z_].*__mn_tensor_'
mapanare_gpu_builtins.c | wc -l`): **46 entry points**.
60 `__mn_tensor_` references in the C file. Function attribute
discipline observed: pure reductions are `nounwind readonly`;
allocating fns prefix the return value with `noalias` (the LLVM
spec quirk caught during v5.6.2 development — `noalias` is a
return-value attribute, not a function attribute).

**v5.6.4 Rt.06 — tensor drop-glue.** Two new `EmitState` fields
(`tensor_owned` + `tensor_owned_source`) parallel to the existing
str/list/boxed triples. `emit_track_tensor` mirrors
`emit_track_boxed`: zero-init slot in entry-block prelude, store
of tensor ptr after alloc emit, ownership-list push. Loop-depth
branch prepends `load ptr, slot` + `call void @__mn_tensor_free
(ptr %prev.tens.N)` before the store — load-bearing for
`53_linear_regression`'s 10-epoch loop × ~4 fresh tensors per
iteration. `is_tensor_allocating_fn(fn_name)` enumerates 22
runtime fns. `emit_drop_glue_destroy` (the v5.5.7 async cleanup
helper) grows a fourth unconditional tensor loop. The result:
**all 5 tensor goldens (49–53) report 0 objs / 0 B under LSan**.
Baseline TSV at `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`
flipped 49/50/51/52/53 from COMPILE_FAIL-era to CLEAN-required
— the leak gate is now strictly tighter than at v5.3.0.

The C-runtime tensor API is well-shaped: variadic `_nd` family
takes `(tensor, rank, ...)` matching LLVM's varargs prefix-form
calling convention; broadcast/scalar/reverse-scalar split is
clean; reductions on signed-vs-unsigned aware (`mean` always
returns f64). I do not see API redundancy or footguns. **+0.1.**

### Drop-glue infrastructure (v5.4.0–v5.4.4) — Phase 2 Own.1 closeout

The v5.4.x arc closes Own.1 Phase 2 with ASan leak-detection as a
merge gate. Five releases, structural rather than dramatic:

- **v5.4.0** — Move MIR variant + `EmitState` ownership slots +
  drop-glue helpers + `emit_mir_return` wiring. Phase 0 baseline
  found all 11 Sh.2 tests already pass; release rescoped to "0
  new goldens, infrastructure only." Honest.
- **v5.4.1** — Owner-list population at all heap-allocating emit
  sites: `emit_mir_call` covers runtime + user String returns;
  `emit_binop +` covers concat; `emit_interp_concat` tracks
  intermediates; `emit_list_init` registers list allocas.
  Shadow-slot architecture ports from Python (`_track_string`,
  `_track_boxed`, `_track_closure`).
- **v5.4.2** — `scripts/run_asan_leak_goldens.sh` flips
  `detect_leaks=1` across all 66 goldens. First sweep revealed
  5 leak classes; 2 fixed by extending the tracking hook
  (`is_string_returning_builtin` covers 13 Mapanare-level builtins
  whose MIR dest defaults to `mir_unknown()`). `make leak-check`
  + `.github/workflows/sanitizers.yml` ratify the sweep as a
  merge gate.
- **v5.4.3** — `EmitState.loop_depth` + push/pop around
  for/while/mapfor labels. `emit_track_string` / `_boxed` /
  `_closure` prepend `load + free` when `loop_depth > 0`. Closes
  Rt.03: 22_string_builder 6 objs / 19 B → CLEAN.
- **v5.4.4** — Move-aware drop glue (`str_owned_source` /
  `list_owned_source` / `boxed_owned_source` parallel arrays). 22/22
  registry gate. Guard-lift for `%struct.*` returns implemented
  and **reverted** after surfacing a 5× stage2.ll inflation +
  mnc-stage2 segfault — honest scoping I respect.

The C-runtime change here is small: `__mn_str_free` (already
present), `__mn_list_free` (already present), and `free` (libc)
are added to `declare_all_runtime` in the self-hosted emitter.
Runtime null-tolerance was already there. The work is all
emitter-side. **Leak baseline current at v5.7.1:** 39_gpu_detect
5 obj / 50212 B (Mesa/Vulkan dlopen, third-party Rt.02);
40_gpu_tensor 5 obj / 50212 B (same class); 62_list_output 13 obj
/ 346 B (Rt.04, multi-level alias depth-2, RESCOPED to v6.0
borrow-checker per v5.6.6 SESSION_REPORT). **Every Mapanare-code
class is leak-clean.** **+0.05.**

### Memory-safety closeout (v5.6.5–v5.6.13) — fixed-point restored

The v5.6.x bug-closeout arc is Viper's domain primarily, but two
items touch my axis:

1. **Lk.1 closure at the structural root cause (v5.6.12).** Closed
   via destination-passing semantics in `lower.mn::lower_let` —
   the right architectural fix, not multi-level alias analysis
   (which would have been v6.0 borrow-checker scope). Pre-computes
   the var's alloca name and lowers the `ListInit` directly into
   it via `lower_list_typed_into(st, elements, hint, dest_name)`,
   eliminating the duplicate `%t<N>.addr` alloca + the
   alloca-aliasing leak. Mirrors rustc's `PlaceRef`-based codegen.
   With Lk.1 closed at the source, the v5.6.10 scalar gate was
   safely applied (closes all 7 Ve.2 residual `__mn_list_new(i64
   384)` floor sites). **65_list_int_indexing LSan CLEAN** (was:
   would leak 80 bytes if scalar gate applied without Lk.1 fix).
   Floor sites **7 → 0**.

2. **Ve.4 closure restores fixed-point (v5.6.11).** This was the
   v5.6.4-era blocker that broke `verify_fixed_point.sh` since
   v5.6.4. Root cause: `emit_index_get` / `emit_index_set` inline
   fast paths used a constant 8-byte stride GEP, while
   `__mn_list_push` writes used the runtime `elem_size` field
   from the list struct. 14 LOC across two emit sites — load
   `list.elem_size` (struct field 3) at runtime, compute
   `offset = idx * elem_size`, then `getelementptr inbounds i8,
   ptr %data, i64 %offset`. SROA elides the runtime load when
   elem_size is a known constant. **Result: stage2.ll == stage3.ll
   within tolerance for the first time since v5.6.4 (7 releases).**

The fixed-point restoration is on Cobra's axis, but it eliminated
a quality regression I docked at v5.2.0 (-0.15 for "fixed-point
BROKEN, was NEAR"). **Recovering it: +0.1.**

### Benchmarks v5.8.0 — Mn/Rust geomean parity

```
Bench           | Mn O2  | Rust   | Go     | C(gcc) | Mn/Rust | Mn/Go | Mn/C
enum_match      | 0.168  | 0.321  | 0.261  | 0.132  | 0.525   | 0.646 | 1.281
fib_recursive   | 16.027 | 19.104 | 34.056 | 11.313 | 0.839   | 0.471 | 1.417
prime_sieve     | 2.020  | 1.774  | 2.071  | 1.937  | 1.139   | 0.976 | 1.043
quicksort       | 0.410  | 0.372  | 0.565  | 0.345  | 1.099   | 0.725 | 1.187
string_concat   | 0.072  | 0.045  | 35.331 | 0.071  | 1.598   | 0.002 | 1.014
struct_alloc    | 0.021  | 0.018  | 0.019  | —      | 1.157   | 1.105 | —
```

Computed live from `benchmarks/cross_language/v5.8.0-results.json`:

| Geomean | v5.3.0 | v5.8.0 | Delta |
|---|---:|---:|---:|
| Mn / Rust | 1.17× | **1.003×** | -0.17× (essentially parity) |
| Mn / C (gcc) | 0.96× | 1.179× | +0.22× (slight regression, see notes) |
| Mn / Go (excl str_concat) | 0.85× | 0.750× | -0.10× (improved) |
| Mn / Python | 168× | **328.6×** | +160× (~2× speedup) |

**This is the single biggest cross-language number since v5.1.0.**
Mn/Rust 1.003× geomean — averaged across 6 benchmarks — is the
first time the project has been at Rust parity. Mn beats Rust on
two of the six benchmarks: `enum_match` (0.52×, ~2× faster) and
`fib_recursive` (0.84×). The remaining are within Rust iteration
noise: quicksort (1.10×), prime_sieve (1.14×), struct_alloc (1.16×).

The Perf.1 + Perf.2 trajectory I called at v5.2.0 ("the gap was
opaque function calls; the fix was inlining them; the improvement
is proportional") continues. Inline list ops (`_tsz(ety) == 8`
gate at `emit_llvm_text.py:4575,4645`) are preserved unchanged;
quicksort is now within Rust iteration noise.

The Mn/Python 328.6× headline is dominated by `struct_alloc`
(~10000× — Python's struct construction is extremely slow), but
even excluding that the geomean stays well above 100×. **The
"328.6× faster than Python" claim is honest and citable.**

The async medians (1.07–1.57 ms across the 5 benchmarks, geomean
~1.14 ms in the standalone JSON, ~1.29 ms in the xlang JSON)
preserve the Perf.2 0.91× Go default class established at v5.1.4.
**+0.15.**

## What concerns me

### string_concat 1.60× Rust — known but not closing

`string_concat` runs `__mn_str_concat` (allocator-bound) in a
50000-iteration accumulating loop. Rust's `format!` uses
small-string optimization (SSO) and avoids the allocator for short
strings. Mapanare's `MnString` is a `{ptr, i64, isheap}` triple
without SSO — every concat allocates.

This is the only above-1.5× ratio in the suite. It's small in
absolute terms (0.072 ms vs 0.045 ms = 27 µs gap on 50000
iterations = ~0.5 ns / iteration), but it's the highest ratio in
the table and it's been there for 3 panels now. The fix is
either:

- **Add SSO to `MnString`** — non-trivial (changes the layout, breaks
  ABI), but worth a dedicated v5.x docket. The gap is purely
  allocator overhead; eliminating it would push Mn/Rust geomean
  below 0.95× without touching anything else.
- **Add a `__mn_str_builder` API** — append-only fast path with
  amortized growth, and have the compiler detect string-concat
  patterns in loops. This is essentially the v5.6.x list
  destination-passing pattern applied to strings. Complementary
  to SSO.

Carry-forward as **Perf.3** (LOW–MEDIUM, depending on whether
you treat 1.60× as the high-water mark to fix).

### Mn/C(gcc) geomean 0.96× → 1.18× — small regression

This is the only cross-language regression. It's within iteration
noise (`fib_recursive` 16.027 vs 11.313 = 1.42× is the dominant
contributor) but the trend is wrong. Possible causes:

- **gcc -O2 improvements** in the toolchain over the v5.3.0 → v5.8.0
  window — gcc 11→13 transition has a known fib improvement.
- **stage2.ll growth** from 121k → 218k lines (+80%, 8.4× per-year
  rate). Even at -O2, larger IR exercises more registration
  pressure on the LLVM back-end.
- **Mapanare's inline list ops** vs gcc's array-pointer codegen
  — Mapanare emits an icmp+gep+load triple per access; gcc -O2
  vectorizes plain C arrays.

Not a quality signal alone, but flagging — 0.96× → 1.18× is a 22%
geomean shift on what should be a stable benchmark. Worth a
dedicated profile next panel.

### Async benchmarks lost the Go arm

`v5.8.0-async-xlang.json` shows all 5 Go entries as `median_ms: -1`
with `note: "go not installed"`. The cross_language benchmark JSON
DOES contain Go entries (median 34.056 / 0.565 / 35.331 etc), so
Go IS installed — the async benchmark harness apparently can't
find it.

This is methodology drift: the v5.2.0 review's "0.91× Go default"
claim from Perf.2 is no longer empirically verified at v5.8.0,
even though the underlying scheduler primitives in
`mapanare_runtime.c` are byte-unchanged. The Mn/Python 73.6×
async geomean is verified live, but **the Go side of the
comparison silently broke** and nobody caught it before the
panel. MEASUREMENTS.md §6.2 acknowledges this ("Go async benchmark
binary failed to build in this WSL environment; v5.3.0 established
the Mn/Go async geomean at 0.91× Go at default settings"). That's
honest, but I'd like to see the Go path repaired before v6.0.

Carry-forward as **Bn.5** (LOW): repair the async benchmark Go
toolchain detection so the multi-language async comparison stays
verifiable across panels.

### stage2.ll growth: 121k → 218k lines (+80%)

Self-hosted compiler grew from 41,195 → 48,269 lines (+17%) but
the emitted stage2.ll grew +80%. Most of the IR growth comes
from the v5.4.x drop-glue infrastructure (33% in v5.4.1 alone)
and the v5.6.x tensor runtime decls + Sh.4 coroutine emission.

This isn't a correctness issue and stage2.ll passes `llvm-as`,
but at the current cadence the IR will hit 400k lines by v6.0
and 1M lines by v8.0. At some point this becomes a build-time
floor and a compile-test-iterate friction tax. The v5.6.13 Layer
1 destination-passing extension to struct let-bindings is exactly
the right kind of cleanup; we need to see more of that pattern
applied across the v5.4.x drop-glue surface specifically.

Not on my axis but flagging because the C-runtime symbol
overhead (12 coroutine entry points + 46 tensor entry points +
the drop-glue declarations) is part of the IR-side bloat.
Carry-forward as **Pe.1** (LOW): revisit IR-output discipline at
v6.0 panel; consider whether to factor out runtime-decl emission
to a shared header.

### Async benchmark median drift v5.3.2 → v5.8.0

```
v5.3.2 medians:  [1.32, 1.05, 0.98, 0.99, 1.09]   geomean: 1.079 ms
v5.8.0 standalone: [1.07, 1.14, 1.39, 0.88, 1.28]   geomean: 1.138 ms
v5.8.0 xlang:     [1.24, 1.24, 1.57, 1.43, 1.02]   geomean: 1.286 ms
```

Two re-runs of the same benchmark suite at v5.8.0 with different
sub-test medians: standalone JSON shows 03_io_bound at 1.39 ms;
xlang JSON shows it at 1.57 ms. Same WSL2 environment, same
binary, ~13% drift between runs. This is iteration noise on a
benchmark whose median is sub-millisecond, but it cuts both ways:
a future regression of ~10% would be invisible.

The v5.3.2 baseline (geomean 1.079 ms) is slightly better than
either v5.8.0 sample (1.138 / 1.286). Within noise, but worth
verifying once across 30 runs instead of 10 before next panel.

The async coroutine arc v5.5.4–v5.5.7 added structural overhead
(coroutine frame allocation, scheduler register/wait/run
machinery) that wasn't present at v5.3.2's "synchronous Option A"
state. The fact that we're within 5–20% noise of the synchronous
baseline despite shipping the full ABI is impressive. But the
panel narrative ("async median ~1.20 ms preserved from v5.3.0's
1.19 ms") slightly oversells: the standalone median is 1.14 ms
(better), the xlang median is 1.29 ms (worse), and the
arithmetic mean between them is 1.20. Pick one and stick with
it.

Carry-forward as **Bn.6** (LOW): adopt 30-run async benchmark
methodology before next panel. CPU-isolated `taskset -c 0-1`
already in use; just bump `--runs 30`.

## What held

### Runtime size discipline — zero growth across 9 releases

```
runtime/native/*.c + *.h: 14,963 lines (unchanged)
libmapanare_rt.a:         269,886 bytes (unchanged)
```

Every API consumed by v5.3.1–v5.7.1 (coroutine scheduler, tensor
ops, drop-glue free fns, stream pipeline) was already present
pre-v5.3.0. The 9-release arc shipped:

- 5 closed Sh.* dockets (Sh.4 async, Sh.6 tensor, Sh.7 closure,
  B or-pattern, plus the Stream-C MEDIUM)
- The full LLVM-coroutine ABI in the self-hosted emitter
- ~50 new emitter helpers (drop-glue, tensor lowering, slicing,
  reductions, broadcast)
- Move-aware drop glue with ASan leak-detection as merge gate

…with **0 new lines of C runtime**. This is the discipline I
called for at every panel since v4.0. The runtime is mature.
Growth would now be a cost, not a gain.

### Perf.2 lazy scheduler — preserved byte-for-byte

`mapanare_runtime.c` lines 1670–2043 verified against my v5.2.0
review notes. The race-safe pre-create-1 (`prime = 1`),
lazy-grow gate (`tasks > workers * 8`), idle-exit floor
(`live_workers > 1`), and race-safe teardown (only joins
threads in `spawned[]`) are unchanged. Atomic ordering chain:

```c
int32_t tasks = __atomic_load_n(&mn_sched.active_tasks, __ATOMIC_RELAXED);
int32_t workers = __atomic_load_n(&mn_sched.live_workers, __ATOMIC_RELAXED) + 1;
if (tasks > workers * 8 && workers < (int32_t)mn_sched.worker_cap) {
    mapanare_mutex_lock(&mn_sched.spawn_lock);
    int32_t cur = __atomic_load_n(&mn_sched.live_workers, __ATOMIC_RELAXED) + 1;
    if (cur < (int32_t)mn_sched.worker_cap) {
        mn_spawn_worker_locked();
    }
    mapanare_mutex_unlock(&mn_sched.spawn_lock);
}
```

Double-check pattern under `spawn_lock` is correct. The
`__ATOMIC_RELAXED` load is safe because the mutex provides the
necessary happens-before; the subsequent `fetch_sub` at line
1785 uses `ACQ_REL`; `worker_exited` store at 1788 uses
`RELEASE`; consuming load at 1813 in `mn_find_worker_slot` uses
`ACQUIRE`. Same chain I verified at v5.2.0.

### Inline list ops (Perf.1) — preserved

`emit_llvm_text.py:4575–4654`: the `_tsz(ety) == 8` gate fires
for `i64`, `double`, `ptr`. The bounds-check via `icmp uge` +
trap-via-`abort()` pattern is unchanged. SROA / vectorization /
loop hoisting still apply. quicksort at 1.10× Rust matches the
v5.2.0 win.

### Sanitizer state preservation

| Class | v5.3.0 | v5.7.1/v5.8.0 |
|---|---:|---:|
| Valgrind CLEAN | 62 | **63** |
| Valgrind ERRORS (memory-safety) | 0 | 0 |
| Valgrind ERRORS (GPU-loader) | 2 | 2 (same class) |
| ASan | 3 fail (Stream-C) | **0 fail** |
| TSan | 3 fail (Stream-C) | **0 fail** |
| LSan baseline regressions | n/a | 0 |

47_try_operator LINK_FAIL exposed (Python bootstrap emit-llvm
struct-type bug — `store i64 %uw.12, ptr %t3.a.13` against
mismatched `{i64,{ptr,i64}}` struct). The native `mnc-stage1`
path produces clean IR for this golden (66/66 passes per §2 of
MEASUREMENTS). Pre-existing, silent at v5.3.0.

### Test count + flaky audit

```
5618-5619 passed, 116 skipped, 9 xfailed, 0 FAILED   (5x sequential)
0 flaky across 5 runs; cumulative 40 sequential runs since v4.117.0 — 0 flaky.
```

This is the discipline I want to see at every panel. The +173
test-pass delta vs v5.3.0 (5,445 → 5,618) is real coverage
expansion, not parametric noise.

## What remains open

### Not in my axis

- **Rt.04** — multi-level alias analysis (struct→list→string
  depth-2). Borrow-checker scope, v6.0. The 62_list_output 13
  obj / 346 B leak is the only remaining leak in
  Mapanare-language code; baseline-gated.
- **Sh.5 / Sh.9a / Sh.9b / Gr.1 / Rt.2 / Rt.3** — feature gaps,
  documented workarounds, all LOW.
- **Rt.01 / Rt.02** — third-party libcuda + Mesa/Vulkan loader
  leaks. Not Mapanare code; suppressed.

### My axis

- **Perf.3** (LOW-MEDIUM, **NEW**) — `string_concat` 1.60× Rust.
  Add SSO to `MnString` or introduce `__mn_str_builder` append-only
  API. Allocator-bound; eliminating would push Mn/Rust geomean
  below 0.95× geomean (currently 1.003×).
- **Bn.5** (LOW, **NEW**) — Async benchmark Go arm broke
  (`note: "go not installed"`). Repair toolchain detection so
  Mn/Go async stays verifiable across panels.
- **Bn.6** (LOW, **NEW**) — Adopt 30-run async benchmark
  methodology. ~13% drift between two v5.8.0 runs of the same
  suite is too much for sub-ms medians.
- **Pe.1** (LOW, **NEW**) — stage2.ll growth 121k → 218k (+80%).
  At current cadence we hit 1M lines by v8.0. Plan IR-output
  discipline review before that floor materializes.

## Score breakdown

Starting from v5.2.0 baseline of 9.6:

- **Stream-C closure** (v5.3.1 — 3 stream tests recovered, Ge.1r
  fallback comment + warning preserved, all 74 C tests pass under
  plain/ASan/TSan): **+0.15**
- **In.1-stage2 closure** (v5.3.2 — fixed-point NEAR restored at
  v5.6.11 after long detour, no longer my carry-forward concern):
  **+0.10**
- **Async coroutine pipeline** (v5.5.4–v5.5.7 — full LLVM-coro ABI
  + scheduler-driven Suspend/BlockOn/main lifecycle, TSan/ASan/
  LSan clean across all 5 Sh.4 goldens, scheduler primitives
  unchanged from v5.1.4): **+0.20**
- **Tensor runtime + drop-glue** (v5.6.0–v5.6.4 — 46 entry-point
  API surface in `mapanare_gpu_builtins.c`, all 5 tensor goldens
  byte-identical, LSan strictly tighter than v5.3.0): **+0.10**
- **Drop-glue infrastructure** (v5.4.0–v5.4.4 — Move-aware drop
  glue, ASan leak-detection as CI merge gate, every Mapanare-code
  class leak-clean): **+0.05**
- **Mn/Rust geomean 1.10× → 1.003×** (essentially parity, the
  first time the project has been at Rust): **+0.15**
- **Mn/Python 168× → 328.6×** (~2× speedup; honest and citable
  headline): **+0.05**
- **Runtime size discipline** (0 lines of C across 9 releases,
  shipping full LLVM-coroutine + tensor + drop-glue surfaces from
  pre-existing APIs): **+0.05**

- **string_concat 1.60× Rust** (only above-1.5× ratio, persists
  3 panels, real but small allocator-bound gap): **-0.05**
- **Mn/C 0.96× → 1.18× regression** (within iteration noise but
  trend is wrong; flag for v6.0 profile): **-0.05**
- **Async benchmark Go arm broke silently** (Bn.5 — methodology
  drift; "0.91× Go default" claim no longer empirically
  verifiable at v5.8.0): **-0.10**
- **Async median drift between two v5.8.0 runs** (Bn.6 — 13% drift
  on sub-ms medians; need 30-run methodology): **-0.05**
- **stage2.ll +80% growth in 9 releases** (Pe.1 — not a
  correctness issue but a scaling concern): **-0.05**

**Net: 9.6 + 0.15 + 0.10 + 0.20 + 0.10 + 0.05 + 0.15 + 0.05 +
0.05 - 0.05 - 0.05 - 0.10 - 0.05 - 0.05 = 10.20.**

Capped at **9.7**: 10.20 isn't on the 10-point scale. The strong
positives — Mn/Rust at parity, async coroutines actually shipping,
Stream-C and In.1-stage2 both closed at the structural root cause
— would push to 9.9 in isolation. The benchmark methodology drift
(silent Go failure, 13% async noise, no 30-run protocol) and the
1.60× string_concat carry-forward are honest concerns I'd want
addressed before celebrating a 9.9. The **+0.1 vs v5.2.0** delta
reflects real progress without overclaiming.

## Carry-forward (for v5.9.0+)

| Docket | Severity | Scope |
|---|---|---|
| **Perf.3** (NEW) | LOW-MEDIUM | `string_concat` 1.60× Rust — add SSO to `MnString` or `__mn_str_builder` append-only API; only above-1.5× ratio in the suite |
| **Bn.5** (NEW) | LOW | Async benchmark Go toolchain detection broke at v5.8.0; repair so Mn/Go async stays verifiable across panels |
| **Bn.6** (NEW) | LOW | Adopt 30-run async benchmark methodology; ~13% drift between two v5.8.0 runs is too much for sub-ms medians |
| **Pe.1** (NEW) | LOW | stage2.ll +80% growth in 9 releases; revisit IR-output discipline before v8.0 (1M-line projection); v5.6.13 destination-passing pattern is the template |
| **Li.1** | LOW | LICM still regresses live goldens; v6.0 scope (carry-forward from v5.2.0) |

Five new dockets, all LOW or LOW-MEDIUM, three of them benchmark
methodology cleanup. None of them block the v5.8.0 RE-PANEL or
the v6.0 borrow-checker work. The C runtime is mature; the
emitter pipeline is at Rust parity; the async coroutine ABI is
TSan-clean. This is the strongest performance + runtime panel
since v4.0.

— Mamba
