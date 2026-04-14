# v4.114.0 — v4.99.0 Docket Audit

> The v4.99.0 panel returned 11 docket items. Phase A closed 5
> (critical/high), Phase C addressed 2 (medium), Phase D closed 4
> (medium/low). This audit walks every item and records closure
> evidence. Each CLOSED item must show (a) the fix still in code,
> (b) a test that exercises the fix, (c) no regression.

Audit performed 2026-04-14 on commit `09ae3df`.

---

## #1 — CRITICAL — Tagged-pointer UB in `mapanare_core.c`

**Status: CLOSED** — v4.100.0

**Code change still present:**
```
runtime/native/mapanare_core.h:60
  uint64_t    is_heap : 1;   /* 1 = heap-owned (freeable), 0 = constant */
```

The bit-tag reading via `mn_tag_heap` is structurally gone; replaced
with a C bitfield inside `MnString`. ABI preserved at 16 bytes.

**Test coverage:** `tests/native/test_string_is_heap.c` exercises the
bitfield; `tests/mn_str/` C tests cover the runtime helpers;
`63_else_sino` golden uses boxed strings end-to-end and passes on the
Python-bootstrap pipeline.

**Regressions:** None. ASan ran clean against the runtime v4.105.0
onward on this code path.

## #2 — CRITICAL — List indexing use-after-free

**Status: CLOSED** — v4.101.0

**Code change still present:**
```
mapanare/emit_llvm_text.py:1256
  def _move_resource(self, name: str) -> None:
```

Six call sites (`:2841, :3561, :3563, :3700, …`) hand off ownership
via move-semantics when heap strings are pushed into lists or stored
as struct fields, preventing the return-time drop glue from freeing
live pointers the container still holds.

**Test coverage:** `08_list` + `16_list_of_structs` goldens pass on
the Python pipeline. Pre-v4.101.0 both failed with `mnc-stage1`
output corruption.

**Regressions:** None. `mnc-stage1` output is `llvm-as`-valid; 26/64
self-hosted golden pass rate has held since v4.111.0 (no regression
attributable to this fix).

## #3 — HIGH — Rebuild `libmapanare_rt.a` with scheduler

**Status: CLOSED** — v4.102.0

**Code change still present:**
```
$ nm runtime/native/libmapanare_rt.a | grep __mn_coro_scheduler
0000000000002dd0 T __mn_coro_scheduler_destroy
00000000000028b0 T __mn_coro_scheduler_init
0000000000002ad0 T __mn_coro_scheduler_register
0000000000002cc0 T __mn_coro_scheduler_run
```

All four scheduler symbols present in the linked archive.

**Test coverage:** CI `integration.yml` compiles + links + runs
`55_async_basic`, `56_async_await`, `57_real_await` against the
archive; all three produce expected outputs (42, 43, 110).

**Regressions:** None. `scripts/test_native.py` Python pipeline
passes 63/64.

## #4 — HIGH — Verify else/sino end-to-end

**Status: CLOSED** — v4.103.0

**Code change still present:**
```
mapanare/emit_llvm_text.py:1661  _emit_drop_glue_boxed
mapanare/emit_llvm_text.py:1908  _extract_ret_ptrs
```

Conservative skip when return has any ptr field that
`_extract_ret_ptrs` cannot reach via struct-walking.

**Test coverage:** `63_else_sino` golden (40 source lines, 268 IR
lines) passes through the Python pipeline and produces expected output.

**Regressions:** None.

## #5 — HIGH — Fix closure type annotations

**Status: CLOSED** — v4.103.0

**Code change still present:**
```
mapanare/lower.py:99   import ClosureCall
mapanare/lower.py:100  import ClosureCreate
mapanare/lower.py:227  # callable variable and emits a ClosureCall.
```

Three changes in `lower.py`: `FnType → MIRType(FN)`, typed-var calls
→ `ClosureCall`, all lambdas → `ClosureCreate`.

**Test coverage:** `11_closure` + `24_enum_methods` goldens pass;
`64_closure_typed` still fails (Sh.7) but that's a separate
self-hosted-only issue not covered by the v4.99.0 docket.

**Regressions:** None.

## #6 — MEDIUM — Disclose binary corruption / perf in README

**Status: CLOSED** — Phase C (v4.107.0–v4.110.0)

**Code change still present:**
```
README.md:365-368
  mean is **50× faster than Python**, **effectively tied with Rust
  (1.06×)**, **2.1× slower than Go**, and **4.85× slower than C
  (gcc -O2)**.
  ... benchmarks/PHASE_C_RESULTS.md ...
```

Performance section rewritten against the Phase C geometric means.
Links to `PHASE_C_RESULTS.md` as the canonical performance document.

**Test coverage:** `benchmarks/cross_language/` harness re-runs these
numbers per release; published table.

**Regressions:** None — numbers refreshed v4.110.0.

## #7 — MEDIUM — Byref size heuristic divergence

**Status: CLOSED** — v4.112.0

**Code change still present:**
```
mapanare/self/emit_llvm.mn:1460  fn is_byref_type_st(st, ty) -> Bool
mapanare/self/emit_llvm.mn:1495  fn struct_byte_size(st, ty) -> Int
```

7 call sites updated to `is_byref_type_st(st|s, ...)`. Resolution
routes through `st.structs` to the inline `{...}` form and uses the
Python bootstrap's `_tsz` algorithm.

**Test coverage:** v4.112.0 verified on `/tmp/byref_test.mn` — 16-byte
`Small` passed by value (`%struct.Small %s`); 80-byte `Large` by
reference (`ptr %l.byref`). Output correct (311). IR validates via
`llvm-as`.

**Regressions:** None. Self-hosted 26/64 golden rate held through
v4.113.0.

**Caveat:** Full fixed-point verification (stage2 == stage3) is
blocked upstream by Sh.8 (different docket, different phase); the
byref fix itself has been verified in isolation.

## #8 — MEDIUM — Coroutine frame layout coupling

**Status: CLOSED** — v4.113.0

**Code change still present:**
```
runtime/native/mapanare_runtime.c:1539
  typedef struct mn_coro_frame_prefix {
    void (*resume_fn)(void *handle);
    void (*destroy_fn)(void *handle);
  } mn_coro_frame_prefix_t;

runtime/native/mapanare_runtime.c:1548
  static inline int mn_coro_is_done(void *handle) {
      const mn_coro_frame_prefix_t *frame = (const mn_coro_frame_prefix_t *)handle;
      return frame->resume_fn == NULL;
  }
```

Hardcoded-offset audit:
```
$ grep -rn "*(void **)" runtime/ mapanare/
runtime/native/mapanare_runtime.c:1536: *     than `*(void **)handle`)  [comment only]

$ grep -rEn "handle\[[0-9]+\]" runtime/ mapanare/
mapanare/emit_llvm_text.py:4941: # handle[8](handle) — the destroy_fn pointer  [comment only]
```

Zero executable code reads into the coroutine frame by raw offset.

**Test coverage:** `55_async_basic`, `56_async_await`, `57_real_await`
all produce expected outputs natively (42, 43, 110). Valgrind shows
0 errors from 0 contexts on all three. ASan shows 0 errors.
Byte-for-byte leak match against the pre-v4.113.0 control rebuild.

**Regressions:** None.

## #9 — MEDIUM — String concat performance

**Status: CLOSED** — v4.108.0

**Code change still present:**
- `mapanare/mir_opt.py:string_concat_optimization` — MIR pass rewritten
  against `BinOp(ADD, String, String) + Copy` inside natural loops.
- Runtime wrappers `__mn_sb_new` + `__mn_sb_finish` still exported
  from the runtime archive.

**Test coverage:** `benchmarks/cross_language/` — `string_concat`
workload went from 94.57 ms (v4.107.0) to 1.36 ms (v4.108.0) = 70×
speedup; 246 MB → 2.3 MB memory = 109× reduction. Numbers verified
again in v4.110.0's `PHASE_C_RESULTS.md`.

**Regressions:** None. `stdlib/ai/llm.mn` / `embedding.mn`
`sb_create`/`sb_to_string` builtins routed through the new wrappers.

## #10 — LOW — Keyword collision SPEC

**Status: CLOSED** — v4.113.0

**Code change still present:**
```
docs/SPEC.md:53  #### 2.1.1 Reserved Keyword Master List
docs/SPEC.md:258 any future change adds or removes a keyword ...
                 both lexers, §2.1.1, and Appendix C must be updated
docs/SPEC.md:2620 see §2.1.1 Reserved Keyword Master List
```

42-row alphabetical table covering every hard-reserved identifier
across both lexers (`mapanare.lark:380-427` and
`self/lexer.mn:59-177`).

**Test coverage:** Cross-reference audit in
`docs/roadmap/v4/v4.113.0/artifacts/keyword-audit.md`. Both lexers
agree on 42 tokens / 51 surface spellings. Procedure is trivially
re-runnable.

**Regressions:** None — doc-only change.

## #11 — LOW — Async error messages

**Status: CLOSED** — v4.113.0

**Code change still present:**
```
$ grep -c "mapanare: async runtime" runtime/native/mapanare_runtime.c
7
```

Seven specific messages across 5 sites (scheduler init thread spawn,
register pre-init guard, deque+overflow full, register_wait overflow
full, file_read_async Future alloc, ctx alloc, thread spawn).

**Test coverage:** Site #2 (scheduler-not-initialised guard)
manually triggered in isolation in v4.113.0 Phase 4; output
matches exactly the text hard-coded in the runtime; exit code 1.
Remaining 4 are wired guards requiring env stress (RLIMIT_NPROC
exhaustion, queue overflow, OOM).

**Regressions:** None. All three async goldens still produce
42/43/110.

---

## Audit summary

**11/11 items CLOSED.** Every item has:
- Code change present at a specific file:line reference
- Test coverage (golden, benchmark, or manual trigger)
- No regression (v4.111.0–v4.113.0 held 26/64 self-hosted, 63/64
  Python pipeline, 42/43/110 async native outputs)

**Zero open items from the v4.99.0 panel.**

**What's open but NOT from v4.99.0:** Sh.1–Sh.8 (self-hosted emitter
limitations opened during Phase D), Qs.1 (v4.107.0 list indexing
in specific harness), Rt.1 (v4.106.0 boxed-enum runtime overhead),
TBAA.1 and willreturn.1 (v4.109.0 optimizer-attribute reviews). All
are for future releases; none reopens a v4.99.0 item.
