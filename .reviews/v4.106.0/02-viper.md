# Viper v4.106.0 Review — Memory Safety

## Score: 7.5/10
## Verdict: PASS WITH NOTES

## Context: v4.99.0 → v4.106.0

At v4.99.0 I was 5.5/10 NEEDS WORK — four open concerns: tagged-pointer UB, coroutine frame coupling, arena lifetimes, and the untested "valgrind clean" claim. Phase A structurally removed the UB, Phase B put the claim under instruments. We went from "we think we're clean" to "we know exactly which 36 tests error, which cluster, which are pre-existing, which are latent, and which are Phase A regressions (none)."

## Tagged-pointer UB (Item #1)

CLOSED. `runtime/native/mapanare_core.h:57-61` defines `MnString` as `{ const char *data; uint64_t len:63, is_heap:1; }` — same 16 bytes, same register-return path, no pointer provenance games. `mn_tag_heap`/`mn_untag_heap`/`mn_is_heap` helpers deleted from `.c`; only comments remain describing the transition (`mapanare_core.c:166-168`, `.h:36`). This is the right kind of fix: structural, not mitigatory. Auditor Claim 1/2 both VERIFIED.

## Valgrind landscape (36 ERRORS)

Not Phase A regressions. The top-frame clustering (`VALGRIND_REPORT.md:43-60`) maps exactly onto two populations: 29 tests that were already CRASH in v4.104.0 Phase 2 (valgrind just confirms the crashes are memory bugs, not assertions), plus 7 latent bugs where output happens to be correct today but the compiler is reading freed / uninit memory to compute it. All 7 latents are new findings and are docketed Vg.1–Vg.7. The WARNINGS_ONLY bucket (28) is intentional arena-pattern "leak at shutdown" — not a bug, explicitly classified. Phase A did not introduce any of these; v4.103.0 baseline (21/64) is identical to v4.105.0 baseline.

## ASan landscape (17 ASAN_ERROR)

Also pre-existing and understood. 12× heap-use-after-free in `mn_list_rc` (shared-buffer double-free — a C-runtime bug in the COW refcount machinery at `mapanare_core.c:970-1204`, As.1). 5× global-buffer-overflow — `strtoll` called on a non-NUL-terminated `[N x i8]` constant from the MIR strength-reduction pass (As.2). Both are distinct from Phase A's scope and correctly deferred to v4.107.0+. 21 CLEAN on the passers is strong evidence the happy path has no heap corruption.

## TSan verdict on async runtime

3/3 async goldens race-free with runtime rebuilt under `-fsanitize=thread` (`TSAN_REPORT.md:21-25`, re-verified in PRE_PANEL_AUDIT Claim 8). This is the single strongest piece of evidence in the release. v4.102.0's scheduler didn't just get a correctness fix — it's now empirically concurrency-safe. Zero data races, zero lost signals, zero unsynchronized atomic reuse.

## Coroutine frame coupling (docket item #8)

PARTIAL. v4.102.0 fixed the immediate `handle[0] == NULL` offset bug — that specific misread is gone. But the broader concern I raised ("LLVM coroutine lowering is fragile; any LTO pass could resplit frames") is not addressed: there is no LTO build in CI, and v4.102.0's own SESSION_REPORT acknowledges the remaining implicit assumption that Future's payload slot can be overwritten in-place (lines 172-176). The honest read is: safe under the exact build pipeline we ship, fragile under anything that re-runs the coroutine splitter. Docket #8 stays open.

## AS-safe crash handler (v4.105.0)

Genuinely AS-safe. `mn_crashdiag_handler` at `mapanare_runtime.c:1882-1912` uses only `write(2)`, hand-rolled int formatters, and `backtrace_symbols_fd` (signal-safety(7)-listed). The grep hits for `fprintf`/`snprintf`/`malloc` in that file are all elsewhere (work queue, tensors, async I/O) — none inside the handler body. The one remaining caveat is documented honestly: glibc `backtrace()`'s first call lazily loads `ld.so`. Accepting this trade-off is the right call.

## Findings

- Sanitizer CI is genuinely wired (`sanitizers.yml`, 3 jobs, baseline-checker scripts committed). PRE_PANEL_AUDIT Claim 20 notes the workflow has not been observed firing from the current clone — reviewers should confirm on GitHub UI.
- Cl.1 (audit's new HIGH: `opt -O2` miscompiles `64_closure_typed`'s typed-closure-through-typed-parameter) is a memory-adjacent finding: wrong output, valgrind-clean binary. Not mine to close, but worth flagging — "valgrind clean" ≠ "semantically correct."
- Ih.1 (integration harness does not diff stdout) is the failure mode that let Cl.1 pass undetected.

## Docket items you would open

- **Vp.1 LOW** — add an LTO build job to exercise the coroutine-frame coupling under post-split re-optimization. Until then docket #8 stays PARTIAL by default.
- **Vp.2 MEDIUM** — the crash handler installer is driver-only (`mnc_main.c`). End-user Mapanare programs linking `libmapanare_rt.a` don't get it unless they call `__mn_install_crash_handler()` themselves. Either auto-install via `__attribute__((constructor))` or document the opt-in.

## Grade justification

The tagged-pointer UB is structurally fixed and ABI-preserved — exactly what I asked for. The async runtime has TSan-proof concurrency, a rarity. The 36 valgrind ERRORS look bad on a raw count but the classification work is thorough: every one is clustered to a frame, bucketed as pre-existing-crash or latent-bug, and has a docket number. That is the trajectory I want to see. I'm holding back 2.5 points because: 36 errors is still 36 errors (the compiler ships memory-unsafe code even if it's documented), the coroutine-frame LTO concern is not closed just deferred, and Cl.1 proves "valgrind clean" is sometimes hiding a wrong-output bug — the verification layer itself has a crack.

## One-line summary

Memory safety moved from vibe-based to evidence-based; every bug we know about has a ticket, none of them are new, and the scheduler is race-free — PASS WITH NOTES, 7.5/10.
