# v4.67.0 Session Report — 2026-04-12

## Verdict
- Design-only release. DESIGN.md (8 sections, ~7500 words) written and reviewed.
- No code changes. No functional changes. No test changes.
- 8 key decisions locked for arcs 8+9 (v4.68.0-v4.76.0).

## Completed
- Phase 1: LLVM coroutine spec studied (docs, CoroSplit source, Clang CGCoroutine, Nishanov papers)
- Phase 2: DESIGN.md written with all 8 sections:
  - Section 1: LLVM coroutine spec summary (~1500 words) — `docs/roadmap/v4/v4.67.0/DESIGN.md:36`
  - Section 2: Existing scheduler state (~500 words) — `docs/roadmap/v4/v4.67.0/DESIGN.md:163`
  - Section 3: Target async semantics (~1000 words) — `docs/roadmap/v4/v4.67.0/DESIGN.md:220`
  - Section 4: Lowering strategy (~2000 words) — `docs/roadmap/v4/v4.67.0/DESIGN.md:332`
  - Section 5: Runtime scheduler extension (~800 words) — `docs/roadmap/v4/v4.67.0/DESIGN.md:560`
  - Section 6: Risk register (~500 words) — `docs/roadmap/v4/v4.67.0/DESIGN.md:690`
  - Section 7: Verification plan (~300 words) — `docs/roadmap/v4/v4.67.0/DESIGN.md:769`
  - Section 8: Rejected options (~400 words) — `docs/roadmap/v4/v4.67.0/DESIGN.md:801`
  - Appendix A: Complete IR example — `docs/roadmap/v4/v4.67.0/DESIGN.md:860`
  - Appendix B: Decision summary table — `docs/roadmap/v4/v4.67.0/DESIGN.md:958`
  - Appendix C: References — `docs/roadmap/v4/v4.67.0/DESIGN.md:973`
- Phase 3: Informal review by 4 reviewers (see below)

## Decisions Made

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Coroutine ABI | Switched-resume (`llvm.coro.id`) | Generic handles, HALO elision, C++ precedent |
| 2 | Scheduler model | Option A (inline in main, cooperative) | Simplest, matches agent scheduler, extensible to B/C in v5.x |
| 3 | Future<T> representation | `{i8 state, ptr payload}` | Uniform size across all T, handle reuse |
| 4 | Pass pipeline | Use LLVM default -O1 pipeline | `presplitcoroutine` attribute is sufficient, no explicit pass arguments |
| 5 | `async fn` vs explicit `Future<T>` | Both work | Sugar vs manual construction, semantic pass distinguishes |
| 6 | AST representation | Dedicated `AsyncFnDef` node (not a flag on FnDef) | Cleaner semantic pass context tracking |
| 7 | Debug info for async fns | Deferred to v5.x | Complex, Arc 7 DWARF baseline is solid for sync fns |
| 8 | Self-hosted compiler parity | Lag by 1-2 releases | Dual-closure convention applies |

## Informal Review Feedback

### Rattler (LLVM lens) — APPROVED

**Assessment:** The LLVM coroutine intrinsic coverage is thorough and accurate.
The switched-resume ABI selection is correct for Mapanare's use case. The
pre-split IR pattern in §4.7 matches what Clang produces. The pass pipeline
decision (rely on `-O1` default) is the right call — explicit pass ordering
is fragile across LLVM versions.

**Concerns (non-blocking):**
1. The `Future<T>` payload allocation (`malloc(i64 8)` per result) is an
   overhead that could be avoided with promise-based storage. The promise
   lives at a fixed offset in the coroutine frame and can store the result
   directly. Consider this optimization in v4.73.0+.
2. The `coro.save` / `coro.suspend` separation in §4.7.2 is correct but the
   design should note that the save point must dominate the suspend point in
   the CFG. The emitter must ensure no code path reaches a suspend without
   passing through the corresponding save.
3. The cleanup block should call drop glue BEFORE `coro.free`, not after.
   §4.9 states this correctly but the IR examples in §4.7.3 should be
   verified during implementation.

**Sign-off:** Approved. No veto.

### Anaconda (toolchain lens) — APPROVED WITH NOTES

**Assessment:** The pass pipeline decision is sound. The `-O0`/`-O1` split
(CoroSplit runs at both, CoroElide only at -O1) matches LLVM's actual
behavior.

**Notes:**
1. The `opt` invocation in `emit_llvm_text.py` currently doesn't pass any
   optimization level. Verify that the build pipeline actually reaches the
   opt step with `-O1`. If Mapanare invokes `llc` directly, the coroutine
   passes won't run.
2. The emitter should detect `presplitcoroutine` functions and warn if the
   compilation target is `-O0` that HALO elision is disabled.
3. CI should add a specific test that compiles an async function through the
   full pipeline (not just `llvm-as` validation) to catch pass-ordering issues.

### Coral (language design lens) — APPROVED

**Assessment:** The semantics are clean and well-bounded. The `async fn` /
`await` design follows the Rust/Swift/Kotlin consensus. The decision to make
`await` a semantic error (not parse error) outside async context is pragmatic
— it allows error recovery in the parser.

**Notes:**
1. The `for await` sugar (§3.6) depends on `stream.next()` returning
   `Future<Option<T>>`. The design should specify whether all streams gain
   this method automatically or whether it's opt-in via a trait.
   **Response:** All `Stream<T>` types gain `next()` automatically. It's a
   built-in method, not a trait. Trait-based async iteration is v5.x.
2. Consider whether `await` should be a prefix operator or postfix (`.await`
   like Rust). Prefix is the decision; document why.
   **Response:** Prefix `await` chosen for consistency with other languages
   (JavaScript, Python, C#, Kotlin). Postfix `.await` (Rust) is unusual and
   would require grammar changes to method-call syntax. Prefix is the
   conventional choice.

### Mamba (runtime lens) — APPROVED WITH NOTES

**Assessment:** The runtime scheduler extension (§5) is well-scoped. The
`mapanare_coro_scheduler_t` design is clean and the step algorithm is correct.
The agent scheduler integration (§5.5) correctly identifies the critical
"handler-in-flight" risk.

**Notes:**
1. The `pending_coro_handle` field on `mapanare_agent_t` (§6.5) must be
   initialized to NULL in `mapanare_agent_init`. Add this to the implementation
   checklist for v4.73.0.
2. The O(n) step function (§5.4) should track the count of "waiting" vs
   "ready" entries to avoid scanning the full array every tick. A simple counter
   of ready entries would make the common case (all waiting) O(1).
3. Consider a unified scheduler that handles both agents and coroutines in one
   data structure. The current design has two parallel loops (§5.5) which could
   lead to starvation if one scheduler has many entries. A single round-robin
   across both would be fairer.
   **Response:** Acknowledged. A unified scheduler is architecturally cleaner
   but increases the blast radius of changes to the existing agent scheduler.
   Two parallel schedulers in v4.x; unified scheduler is a v5.x consideration.

## Carry-forward closed
- None (design-only release, no carry-forward items targeted)

## Carry-forward still open
- All items from v4.66.0 remain at their current tracking versions
- 8 action items from v4.66.0 Arc 7 panel remain open (tracked for resolution
  in v4.68.0-v4.70.0 where applicable; some are Arc 8 panel items for v4.71.0)

## Measurements
- IR line count: unchanged (no code changes)
- Golden test count: unchanged
- Stage2 module count: unchanged (11/11)
- Fixed-point diff: unchanged (0 lines)
- Pytest pass count: unchanged (4,845+)
- Culebra findings: unchanged (design-only release)
- DESIGN.md: 8 sections, 3 appendices, ~7500 words, 980 lines

## Verification Results
- No code changes — `git diff --stat` shows only `docs/roadmap/v4/v4.67.0/`
- DESIGN.md has all 8 sections (verified via section headers)
- 4 reviewer sign-offs recorded (Rattler APPROVED, Anaconda APPROVED WITH NOTES,
  Coral APPROVED, Mamba APPROVED WITH NOTES)
- Rattler has no veto — design approved

## Tool discipline retrospective
- LLVM docs read via web fetch (coroutines spec, Clang debugging docs)
- CoroSplit.cpp and CGCoroutine.cpp analyzed via web search summaries
- Runtime scheduler read directly from `runtime/native/mapanare_runtime.c:1195-1335`
- Culebra: not run (no code changes)

## Next Session Should Start With
- Read `docs/roadmap/v4/v4.68.0/PLAN.md` (grammar + AST + parser for async/await)
- Read `docs/roadmap/v4/v4.67.0/DESIGN.md` §3 (semantics) and §4.2-4.3 (grammar + AST)
- Note Rattler concern #1 (promise-based storage optimization for v4.73.0+)
- Note Anaconda concern #1 (verify opt invocation actually passes -O1)
- Address v4.66.0 panel action item #1 (cmd_build -g flag to clang) in v4.68.0
