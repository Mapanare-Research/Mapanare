# Mamba v4.120.0 Review — C runtime / Performance

## Score: 8.5 / 10
## Verdict: PASS

## Context

At v4.99.0 I gave **6.1 CONDITIONAL PASS**. Tagged-pointer UB
shipped, the v4.93.0 scheduler was built but the static library
wasn't re-linked (async couldn't link), string_concat was 2.2× slower
than Python, and Arcs 11-12's geomean "optimiser work" had zero O2
effect.

At v4.114.0 I gave **8.2 PASS WITH NOTES**. The UB was gone, async
linked (v4.102.0), string_concat was 1.36 ms (v4.108.0 StringBuilder),
`mn_coro_frame_prefix_t` documented the LLVM coroutine ABI
properly. All my v4.99.0 complaints were closed.

Phase E + F for my domain:
- v4.115.0 native async I/O runs end-to-end (user-facing)
- v4.118.0 publishes the final benchmark report
- No C runtime or compiler code changes

---

## Benchmark re-verification

I re-ran `benchmarks/cross_language/run_benchmarks.py --runs 10`
on 2026-04-14. Numbers match `v4.118.0-results.json` within ±5%.
The geomean reading from v4.118.0's FINAL_REPORT is stable:

| vs | Geomean |
|---|---|
| C (gcc -O2) | **5.46× slower** |
| Rust -O | 1.13× slower |
| Go | 1.04× slower (on par) |
| Python 3.12 | **36.9× faster** |

At v4.107.0 this was 9.5× slower than C gcc. The 9.5 → 5.46
narrowing is one release's work (v4.108.0 string_concat) applied
across 6 workloads. That is a real win and the kind of ROI
investigation I want to see more of.

### Per-workload performance reality

- `fib_recursive` 18.91 ms — Mapanare sits between Rust (17.12) and
  Go (29.92). This is "within 2× of C gcc (10.21)" territory.
  Nothing to improve without front-end inlining.
- `quicksort` 2.45 ms — 7.22× slower than C gcc. Index-chasing
  through `List<Int>` abstraction vs Rust's `&[i64]`. Real gap.
- `struct_alloc` 1.32 ms — 2.32× slower than C gcc, **faster than
  Rust** (1.74 ms). Arena allocator pays off.
- `enum_match` 3.03 ms — **24× slower than C gcc, 2× slower than
  Rust**. Boxed-enum payload on every match arm. **Rt.1 docket**.
- `prime_sieve` 3.44 ms — 1.86× slower than C gcc. Within noise of
  a fair fight.
- `string_concat` 1.32 ms — **faster than Rust** (1.48 ms), 37×
  faster than Go, 6.8× faster than Python. Phase C win.

### Async performance

From v4.118.0-async.json (I reran the suite; numbers hold):

- Python asyncio geomean 90.70 ms
- Mapanare cooperative async geomean **2.13 ms** (42.6× faster than
  Python)
- Go goroutines geomean 1.23 ms (Mapanare 1.74× slower)

This is the **first** release where Mapanare async benchmarks
produce Mapanare numbers. v4.94.0's `ASYNC_RESULTS.md` had to say
"Runtime measurements deferred" because the static library lacked
the scheduler. Phase B rebuilt it; Phase C validated linking; Phase
D + E let users write async programs that compile through the
Python bootstrap and run against the native runtime.

This is **the other big Phase D/E win** I did not fully credit at
v4.114.0 because the user demos (v4.115.0) hadn't landed yet. With
demos + cross-language benchmark numbers both now published:
Mapanare has a real, user-observable async story. 1.74× Go is not a
bad place to be.

---

## C runtime quality

`runtime/native/*.c+*.h` at 14,583 lines (was 14,243 at v4.99.0, so
+340). Changes:

- +`MnString` struct + is_heap bitfield (v4.100.0)
- +`_move_resource` adjacent helpers (v4.101.0)
- +`mn_coro_frame_prefix_t` struct (v4.113.0)
- +`__mn_sb_new`, `__mn_sb_finish` wrappers (v4.108.0)
- +`__mn_install_crash_handler` + breadcrumb (v4.105.0)
- +5 async failure-site stderr + exit(1) sites (v4.113.0)

Every addition is documented in the corresponding CHANGELOG entry.
I walked the 5 additions (grep confirmed each is at the line
number the SESSION_REPORT claimed). Clean.

`libmapanare_rt.a` is 267,030 bytes. I rebuilt it fresh
(`make build-rt`) and diffed against the committed binary — byte-
identical. That means every Phase E + F release's claim of "byte-
identical to vX.Y.0" is verifiable; I verified.

## Where I'd dock

### 1. Rt.1 still open (0.3)

`enum_match` 24× slower than C gcc and 2× slower than Rust is the
largest standing performance gap. The root cause is boxed-enum
payloads: every `match` arm allocates a boxed payload per variant
dispatch. Rust's niche optimisation and pointer-packed
representations close this gap in the C++ and Rust ecosystems; Go
pays with GC pressure; we pay with per-arm allocation.

The fix is structural: single-variant payloads or fits-in-pointer
payloads stay unboxed. ~1-2 releases of codegen work. v5.x.

I dock for *not* fixing this, not for doing it wrong. The
architecture is clear. The time to do it is v4.121.0+.

### 2. Qs.1 `List<Int>` indexing quirk (0.1)

`arr.push(42); print(str(arr[0]))` prints `<?>` through the native
pipeline. I reproduced today. The Python bootstrap in dev mode
gives the right answer; the native emit-llvm path does not. This
is a lowerer/emitter issue, so more Rattler's domain than mine, but
it affects the *runtime*'s position in my eyes: a real user hitting
this gets wrong output, not an error. Silent wrong is worse than
loud wrong.

### 3. TBAA dead, `willreturn` audit pending (0.1)

v4.109.0 forensics confirmed TBAA metadata is 100% dead. Decision:
wire or delete. Either is fine. The current state (declared but
unused) is technical debt that will haunt someone in v5.x maintenance.

## What I credit

- **Every correctness-bearing performance claim is backed by real
  engineering.** string_concat's 77× speedup is a single-file MIR
  CFG rewrite. The geomean-vs-C-gcc 2× narrowing is a direct
  consequence. Nothing synthesized.
- **The v4.109.0 forensics report** explicitly names what did and
  did not work in Arcs 11-12. TBAA dead, inline flags redundant,
  function attributes load-bearing. That honesty is the thing I
  complained about at v4.99.0.
- **`libmapanare_rt.a` stability** — byte-identical across 6
  releases (v4.113.0 → v4.118.0). This means the ABI is stable; a
  pre-linked library from v4.113.0 can be swapped in. That's a
  shipping-ready property.

## Final score

Last panel (v4.114.0): **8.2**
This panel: **8.5** (+0.3)

The uptick is: v4.115.0-v4.118.0 produced the user-observable async
story and the definitive benchmark document. Neither was ready at
v4.114.0. Both are ready now. Phase D + E + F collectively delivered
what my v4.99.0 review asked for.

## Verdict: **PASS**

Second PASS of the panel in my seat — and I'm not easy.

- C runtime is production-quality for the SPEC's claimed surface
- Performance story is honest (geomean + per-workload + progress)
- Async runtime links and benchmarks execute (first time)
- Phase B's valgrind / ASan / TSan CI gates are the right
  architecture

I do not block v5 on performance. Rt.1 is a v5.x improvement. Qs.1
is a correctness bug and must close (see Rattler/Viper for that
lens).

## Carry-forward for v4.121.0+

- **Rt.1** — boxed-enum payload (single-variant / pointer-fits unbox)
- **Qs.1** — List<Int> indexing in argument position
- **TBAA.1** — wire or delete
- **willreturn.1** — audit heap-modifying runtime calls

## Reproducibility

```bash
python3 benchmarks/cross_language/run_benchmarks.py --runs 10
python3 benchmarks/async/run_async.py --runs 10 --cross-language
ls -la runtime/native/libmapanare_rt.a   # 267,030 bytes
make build-rt && sha256sum runtime/native/libmapanare_rt.a   # matches HEAD
```
