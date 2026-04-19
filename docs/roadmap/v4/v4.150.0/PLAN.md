# Mapanare v4.150.0 — E6: async agent pipeline vs Go

> **The Go-parity experiment.** Close the 1.61× Go gap on the async
> geomean to ≤ 1.2× by attacking the scheduler hot path in
> `runtime/native/mapanare_runtime.c`. This is the deepest experiment
> in the arc — Go's runtime scheduler is a decade of tuning, and the
> architectural differences (preemptive worker-pool + work-stealing
> vs Go's LIFO-G run queues + global queue) are real. The honest
> outcome may be a 1.4× story rather than 1.2×, and the 5% rule +
> `PERF_EXPERIMENTS.md` discipline apply as usual.

**Status:** PLANNED
**Breaking:** No (runtime patch, no public API change)
**Prerequisite:** v4.149.0 shipped (E5 ABI.1 closeout recorded)
**Estimated work:** 3–5 days (largest experiment in v4.150–v4.154)
**Theme:** E6 — async agent pipeline vs Go

---

## Why this release, why now

The v4.144.0 baseline shows Mapanare ≈ 5.82 ms on the async geomean
vs Go ≈ 3.6 ms — **~1.61× slower**. That number is what the "as
concurrent as Go" half of the v5.1.0 story rests on, and it's the
single largest unclosed gap in the arc. E1–E5 attacked CPU/ABI codegen
gaps; E6 is the one scheduler-layer experiment, and it's where the
bulk of the async story comes from.

Go's runtime is a mature target. Its scheduler uses per-P LIFO-G run
queues with a global overflow queue, cooperative preemption at safe
points, and a tuned spin-then-park pattern on idle workers. Mapanare's
scheduler (`runtime/native/mapanare_runtime.c`) uses a simpler shape:
per-worker SPSC ring inbox + `sem_post` wake, preemptive (pthread-
backed), no work-stealing across agents' inboxes. The Ch.1 close in
v4.137.0 put the destroy path on firm ground, but the hot path
(agent-send → ring-push → sem_post → worker-wake → ring-pop → dispatch)
has never been profiled under the perf-arc methodology.

This release is intentionally scoped wider than E1–E4. The 5% rule
still applies — target ≥ 5 % improvement on the async geomean, no
non-target regression > 2 % — but the hypothesis fan-out is larger,
and a full 3–5 day sprint is budgeted to let the experiment loop
iterate over (a) per-message malloc batching, (b) inline small-message
payloads, and (c) tighter spin-wait before park. If none of the three
hits the 5% threshold cleanly, we ship the honest number and the dead-
end record, and the arc continues to E7.

## Baseline / measurement before work

```bash
echo "4.150.0" > VERSION
make build-rt
python3 scripts/build_stage1.py

# Async geomean — the arc's canonical target metric for E6
python3 benchmarks/async/run_async_benchmarks.py --runs 30 \
  --output benchmarks/async/v4.150.0-baseline.json

# Per-workload breakdown — agent_pipeline is the hot sub-bench
python3 benchmarks/cross_language/run_benchmarks.py \
  --only 02_concurrency,05_agent_pipeline --runs 30 \
  --output benchmarks/cross_language/v4.150.0-baseline.json

# Full-corpus snapshot for the 5 % rule non-target floor
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.150.0-full-baseline.json

# Per-message malloc counter — use the v4.124.0 malloc-counting harness
MN_MALLOC_TRACE=1 ./benchmarks/cross_language/out/05_agent_pipeline 2>&1 \
  | tee docs/roadmap/v4/v4.150.0/malloc-trace-baseline.log
```

Record in `docs/roadmap/v4/v4.150.0/BASELINE.md`:
- Mapanare async geomean (median + p95 wall)
- Go, Rust async, asyncio reference numbers
- `05_agent_pipeline` median wall + per-message malloc count
- SPSC ring push/pop count per run (instrument or infer from counters)
- `sem_post` call count per run

Expected at v4.149.0 tag: async geomean ≈ 5.80 ms, ratio ≈ 1.61× Go,
`05_agent_pipeline` ≈ 2.1 ms, per-message malloc count ≈ one alloc
per message (no batching).

## Hypothesis

Go closes the gap through three levers Mapanare currently misses:

1. **Scheduler wake-up cost.** Go's worker-wake uses a short spin-
   then-park pattern on the P's idle queue. Mapanare does an
   unconditional `sem_post` per send, which round-trips to the kernel
   even when the worker is still draining its last ring batch.
2. **SPSC ring fast-path cost.** Mapanare's ring push/pop each
   touches head+tail cache lines with full fences on both sides.
   Go's run-queue hot path uses CAS-based enqueue only on overflow;
   the common path is a simple relaxed load.
3. **Per-message allocation.** `mapanare_agent_send` currently mallocs
   a message envelope per send. Go-go-channel-equivalent code on Go
   side uses a stack slot or a pre-allocated slab for small payloads.

Expected concrete changes:
- Replace `sem_post`-per-send with `sem_post` only when the ring was
  observed empty before the push (classical "wake one when empty" pattern).
- Add a tight spin-before-park loop (~50–100 pause cycles) to the worker
  on an empty ring before sleeping.
- Batch small-message inline payloads (≤ 16 bytes) into the ring slot
  itself, avoiding the per-message malloc for the common case.

## Phased work

### Phase 1 — Profile the hot path

```bash
# perf record a single long-running agent_pipeline invocation
perf record -g -F 2000 \
  ./benchmarks/cross_language/out/05_agent_pipeline --duration 5

perf report --stdio --sort=overhead \
  > docs/roadmap/v4/v4.150.0/perf-baseline.txt

# Flame graph for the narrative
perf script | ~/FlameGraph/stackcollapse-perf.pl \
  | ~/FlameGraph/flamegraph.pl \
  > docs/roadmap/v4/v4.150.0/flame-baseline.svg
```

Map the top 10 overhead functions to source locations. Expected top
offenders: `mapanare_agent_send`, ring push/pop, `sem_post`, `malloc`
(per-message envelope).

### Phase 2 — IR/C-level diff vs Go

```bash
# Go's scheduler source (read-only, for hypothesis)
# src/runtime/proc.go::runqput, findrunnable, schedule
# — annotate the matching Mapanare function per lever in IR_DIFF.md

# Mapanare side
culebra scan runtime/native/mapanare_runtime.c \
  > docs/roadmap/v4/v4.150.0/culebra-runtime.txt
culebra abi runtime/native/mapanare_runtime.c \
  > docs/roadmap/v4/v4.150.0/abi-runtime.txt
```

Write `docs/roadmap/v4/v4.150.0/IR_DIFF.md` with the three levers
side-by-side (Go source on left, Mapanare equivalent on right). No
IR in this one — the gap is at the C/scheduler layer, not the LLVM
layer.

### Phase 3 — Form hypothesis

`docs/roadmap/v4/v4.150.0/HYPOTHESIS.md` — one paragraph per lever,
with a line-level patch sketch for each. Ranked by expected ROI:

1. Empty-wake `sem_post` (lowest risk, highest expected ROI)
2. Inline small-message payloads (medium risk, medium ROI)
3. Spin-before-park on empty ring (highest risk, context-dependent ROI)

Implement Phase 4 in that order; stop early if the geomean hits
≤ 1.2× Go after any single lever.

### Phase 4 — Patch (one lever at a time)

For each lever L in [empty-wake, inline-payload, spin-before-park]:

```bash
# 1. Apply the lever
# 2. Rebuild runtime + stage1
make build-rt && python3 scripts/build_stage1.py

# 3. Re-measure
python3 benchmarks/async/run_async_benchmarks.py --runs 30 \
  --output benchmarks/async/v4.150.0-${L}.json
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.150.0-${L}-full.json

# 4. Apply 5 % rule:
#    - async geomean improves ≥ 5 % vs baseline? keep
#    - any non-async workload regresses > 2 %? roll back
# 5. Record in PERF_EXPERIMENTS.md regardless (win or dead end)
```

Target files:
- `runtime/native/mapanare_runtime.c` — scheduler body (agent send,
  worker loop, wake, park). Expected diff per lever: 20–60 logic lines.
- `runtime/native/mapanare_runtime.h` — possible new struct fields
  (e.g., `_Atomic int was_empty`, inline-payload slot).
- `mapanare/emit_llvm_text.py` — **only if** the inline-payload lever
  requires an ABI change on the agent-send lowering (small-payload
  inline vs boxed). If it does, mirror the v4.140.0 Cb.5 inline-slot
  pattern. If it doesn't, leave the emitter untouched.

### Phase 5 — Sanitizer + correctness re-sweep

Scheduler-layer changes land in the sanitizer gate dead zone if not
re-swept. Run the full sanitizer sweep after **every lever** that is
kept, not just at the end:

```bash
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh
bash scripts/run_asan_goldens.sh
python3 -m pytest tests/native/test_c_hardening.py -v  # Ch.1 gate
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no
```

Ch.1's TSan class is the canary here — if the spin-before-park lever
introduces a race on the empty-ring flag, TSan will catch it. Do not
ship a lever that moves TSan off clean.

### Phase 6 — Record

Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

```
| E6a | empty-wake sem_post | win/dead-end | +XX% async | mapanare_runtime.c:~NNN | v4.150.0 |
| E6b | inline small-msg payload | win/dead-end | +XX% async | mapanare_runtime.c:~NNN | v4.150.0 |
| E6c | spin-before-park | win/dead-end | +XX% async | mapanare_runtime.c:~NNN | v4.150.0 |
```

Write `docs/roadmap/v4/v4.150.0/RESULTS.md` with before/after numbers
per lever and `SESSION_REPORT.md` narrating the experiment (use
v4.142.0 Ge.1 SESSION_REPORT as length template; this one may be
longer due to three sub-levers).

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `BASELINE.md` written with async geomean + per-message malloc count | yes |
| 2 | `perf-baseline.txt` + flame graph committed | yes |
| 3 | `IR_DIFF.md` written (3 levers, Go src vs Mapanare C) | yes |
| 4 | `HYPOTHESIS.md` written (one paragraph per lever) | yes |
| 5 | Each landed lever passes the 5 % rule (target ≥ 5 %, no non-target > 2 %) | yes |
| 6 | `RESULTS.md` written with per-lever before/after | yes |
| 7 | Async geomean improves ≥ 5 % vs v4.149.0 baseline (target: ≤ 1.2× Go; acceptable: ≤ 1.4× Go with honest narrative) | yes |
| 8 | No cross-language CPU workload regresses > 2 % | yes |
| 9 | `PERF_EXPERIMENTS.md` entries (E6a/E6b/E6c) added — win or dead end, all recorded | yes |
| 10 | Valgrind: 0 ERRORS | yes |
| 11 | ASan: 0 ASAN_ERROR | yes |
| 12 | TSan `test_agent_metrics` classes still passing (Ch.1 canary) | yes |
| 13 | Non-bootstrap pytest: ≥ 5,160 passed / 0 failed | yes |
| 14 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 15 | Native goldens: 54 / 66 | yes |
| 16 | Fixed-point: within `DIFF_THRESHOLD=100` | yes |
| 17 | All 8 CI gates green | yes |
| 18 | `SESSION_REPORT.md` written | yes |
| 19 | CHANGELOG + CLAUDE.md + ROADMAP.md updated | yes |
| 20 | Tag `v4.150.0` pushed to origin | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Spin-before-park introduces a TSan race on the empty-ring flag | medium | high | Spin flag is `_Atomic int` with release/acquire ordering; full sanitizer sweep after every lever; Ch.1 `test_agent_metrics` TSan class is the gate |
| Inline-payload lever breaks ABI for existing `.mn` code that passes large messages | medium | medium | Fallback path is the current heap-allocated envelope — inline only triggers for `sizeof(payload) ≤ 16`; golden `21_agent_stream.mn` covers boxed path |
| Go scheduler architectural gap is simply deep and 1.2× doesn't close | medium | high | Document honestly; ship the 1.4× story in `RESULTS.md`; v5.1.0 perf-panel narrative is "as concurrent as Go for most workloads," not "faster than Go" |
| Scheduler patch regresses a non-async workload > 2 % (e.g., `fib_recursive` indirect via sem_post linkage) | low | medium | 5 % rule auto-triggers rollback; keep lever diff tight; test full cross-language corpus after each lever |
| Per-message malloc removal surfaces latent UAF in the agent destroy path (the payload was being freed on message_dtor) | low | high | Ch.1's `message_dtor = free` default is the v4.137.0 canary; audit the envelope-free path before inlining; ASan sweep required |
| 3–5 day budget slips past 1 week | medium | low | Ship what landed. If only one lever lands cleanly, the other two go to v4.150.1 or the `PERF_EXPERIMENTS.md` dead-end ledger. Arc continues to E7 on time |

## What this release does NOT do

- Does not rewrite the scheduler. Mapanare's per-worker SPSC + pthread
  model stays. Levers are hot-path tweaks, not architectural shifts.
- Does not add work-stealing across agent inboxes (that's a v5.x
  refactor; out of scope for this arc).
- Does not port the levers into the self-hosted compiler or the
  cooperative mobile scheduler. Native preemptive only.
- Does not touch the agent public API (`mapanare_agent_send`,
  `mapanare_agent_destroy` signatures unchanged).
- Does not chase Go parity on workloads outside the async corpus.
  Cross-language CPU benches are only for 5 % rule enforcement, not
  for tuning targets in this release.

## Carry-forward after v4.150.0

- If all three levers land clean and async geomean reaches ≤ 1.2× Go:
  E6 is a full win. v4.151.0 opens on E7 (allocator hot path) as planned.
  Cb.11-async-parity docket opens LOW for v4.153.0 to mirror
  scheduler-layer learnings into `stdlib/async/*.mn` where relevant.
- If one or two levers land and geomean sits in the 1.3–1.4× Go range:
  E6 is a partial win. Document the honest story in RESULTS.md. Dead-
  end ledger records the rejected lever(s). v4.151.0 proceeds on time.
- If no lever clears the 5 % threshold: E6 is a dead end. The async
  geomean stays at 1.61× Go. `PERF_EXPERIMENTS.md` records the full
  hypothesis + why it didn't materialize; the v4.154.0 panel reads
  that record as a credible negative result. The "as concurrent as
  Go" claim rephrases to "within 2× of Go on async workloads,
  on par on sub-workloads like X/Y/Z."
