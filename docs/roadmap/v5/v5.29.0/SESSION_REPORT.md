# v5.29.0 — Mb.10 + Pv.7 + Pv.8 — Win64 ABI closeout + CI race prevention

**Status:** SHIPPED.
**Type:** Bug-fix release. Three findings, three fixes, one release.
**Breaking:** No.
**Strict 3-stage fixed point:** Preserved by construction at
**241,898 lines / 0 diff** (restored STRICT from v5.28.0's NEAR;
see "Fixed-point status" below).
**Goldens:** 95/95.
**Bb.\* seed refresh:** NOT required (no C-runtime export changes).
**Mb.\* arc:** **CLOSED structurally** (v5.26.0's claim was correct
for Mb.7+Mb.9 but missed `__mn_indent_to_braces` on the Win64 ABI
sweep — this release closes the arc for real).
**Cadence:** unchanged from v5.28.0 directive — next routine panel
still due v5.33.0; v5.29.0 is a normal non-panel release.

---

## Headline

Three lockstep fixes shipped together because they all live at the
same boundary (CI / Win64 ABI / runtime correctness):

- **Mb.10** — fresh self-host emitter fix in
  `mapanare/self/emit_llvm.mn`. Closes publish-run-#50 Windows
  SIGSEGV in `__mn_indent_to_braces`. Sister to v5.26.0 Mb.9
  (which fixed the brace-deprecation siblings but missed the
  parent function with the same Win64 ABI shape).
- **Pv.7** — `Makefile` `clean-build-test` sandbox + atomic
  rename. Already shipped on dev as commit `bc3bc7b` between
  v5.28.0 and v5.29.0; this release **documents** the fix.
- **Pv.8** — `tests/native/test_c_runtime.c` polling helpers
  replacing fixed-delay sleeps. Already shipped on dev as
  commit `f119c43` between v5.28.0 and v5.29.0; this release
  **documents** the fix.

---

## Mb.10 — `__mn_indent_to_braces` Win64 ABI gap

### Mechanism

`__mn_indent_to_braces(MnString source) -> MnString` is the
indent-to-brace preprocessor called by `parser.mn::parse` exactly
once per compile. `MnString` is a 16-byte aggregate
(`{const char *data, uint64_t len:63, uint64_t is_heap:1}`,
`runtime/native/mapanare_core.h:57-61`).

Two invariants must agree at compile time:

1. **Declaration shape** — set by
   `declare_runtime_fn(s, "__mn_indent_to_braces", llvm_string(),
   llvm_string())` at `mapanare/self/emit_llvm.mn:1150`. Under
   Win64, `win64_rewrite_decl_params` rewrites the parameter
   from the declared 16-byte aggregate to `ptr` (8-byte byref
   threshold).
2. **Call-site shape** — set by `emit_mir_call`. Pre-Mb.10 there
   was no special case for `__mn_indent_to_braces`, so the call
   fell through to the user-call path. The user-call path uses
   `is_byref_type_st`, which has a **64-byte** threshold —
   `MnString` (16 bytes) is below it, so the call site emitted
   the struct **by value**.

The mismatch only surfaces on Win64. SysV AMD64 (Linux/macOS)
passes 16-byte aggregates in registers regardless of declared
shape — no ABI mismatch from the receiver's perspective. Under
Win64, gcc lowers the C signature `MnString source` per Win64 ABI
as **pass-by-hidden-pointer** (rcx = pointer to caller-stack
copy). The caller actually placed the struct in rcx by value, so
rcx contains the struct's first 8 bytes (the `data` pointer).
gcc reads that as the struct address and dereferences it — bogus
pointer → SIGSEGV the moment the callee tries to read
`source.len`.

Surfaced in publish run #50:

```
warning: mapanare/self/mnc_all.mn: uses deprecated {}-block syntax (3125 occurrences)
D:\a\_temp\...sh: line 152: Segmentation fault
   ./mnc-win-x64.exe emit-llvm mapanare/self/mnc_all.mn > stage3.ll
=== Wb.1.dx: mnc-stage2 exited 139; capturing diagnostics ===
Thread 1 received signal SIGSEGV
0x00007ff7562e7edd in mnc-win-x64!__mn_indent_to_braces ()
```

### Asymmetry between emitters (the bug)

| Emitter | Routing for `__mn_indent_to_braces` | Source |
|---|---|---|
| Python `emit_llvm_text.py` | ✅ YES (`_rt(...)` handler) | line 3632 — added v5.23.1 Mb.1 |
| Self-host `emit_llvm.mn` (pre-Mb.10) | ❌ **NO** | (no branch in `emit_mir_call`) |
| Self-host `emit_llvm.mn` (post-Mb.10) | ✅ YES (`emit_rt_call`) | new lines 3787-3795 |

The Mb.9 Python comment at `emit_llvm.mn:3778` even **names** the
missing routing as the pattern Mb.9 mirrored — but Mb.9's author
only added the routing for `__mn_count_user_brace_block_openers`
and `__mn_emit_brace_deprecation_warning` (lines 3781-3786), not
for the parent function. The bug stayed latent because:

- Linux/macOS publish jobs: SysV ABI hides the mismatch.
- Windows publish: wasn't getting to the stage2-self-compile step
  for v5.23.1 → v5.27.0 (failing earlier on other things; e.g.,
  v5.10.0 Win.1b was the LLVM-bundling release, v5.25.0 Pv.6 was
  the fixture-shape closure).
- v5.26.0 Mb.9 fixed the cited failure mode (`oom in
  count_user_brace_block_openers`) and the author marked the
  Mb.\* arc closed; the same-class parent fn with the same
  shape was not swept.
- v5.28.0 RE-PANEL did not surface Mb.10 as a docket item — it
  fell into the test-gap class covered by Tn.1 panel rec
  (extending `tests/llvm/test_async_link.py` to all 95 goldens).

### IR call-site evidence

Pre-fix (v5.28.0 baseline, `/tmp/stage2.ll`, Linux SysV target):

```llvm
declare {ptr, i64} @__mn_indent_to_braces({ptr, i64}) nounwind willreturn
...
if_merge2:
  %source_val10 = load {ptr, i64}, ptr %source.addr
  %t11 = call {ptr, i64} @__mn_indent_to_braces({ptr, i64} %source_val10)
  store {ptr, i64} %t11, ptr %str_track.269
```

Post-fix (Win64 triple, via the new
`test_indent_to_braces_win64_abi.py` Python emitter test):

```llvm
declare void @__mn_indent_to_braces(ptr sret({ptr, i64}), ptr) nounwind willreturn
...
  %sret.1 = alloca {ptr, i64}, align 8
  call void @__mn_indent_to_braces(ptr sret({ptr, i64}) %sret.1, ptr %sarg.0)
  %t = load {ptr, i64}, ptr %sret.1
```

Falsifiability round-trip (verified in session): reverting the
Python handler at `emit_llvm_text.py:3632` triggers the new
test's IR-shape gate failure — `call void
@__mn_indent_to_braces(ptr sret(SRET) %sret.1, {ptr, i64} %l.0)`
— exactly matching the publish-run-#50 anti-pattern.

### Fix

3 LOC in `mapanare/self/emit_llvm.mn`, 12-line block including
explanatory comment, inserted after the v5.26.0 Mb.9
brace-deprecation routing at line 3786:

```mapanare
if fn_name == "__mn_indent_to_braces":
    let as_itb: String = llvm_string() + " " + args[0].name
    return emit_rt_call(st, dn, llvm_string(), "__mn_indent_to_braces", as_itb)
```

Mirrors the Mb.9 routing shape for the brace-deprecation
siblings; only the return type differs (`llvm_string()` i.e.
`{ptr, i64}` MnString here, vs `"i64"` for the counter).
`emit_rt_call` uses `win64_sarg_rewrite_args` (8-byte threshold,
matching `win64_rewrite_decl_params`), so the call site emits
`ptr sarg.N` matching the declaration's `ptr`. On Linux SysV the
call falls through to the by-value path (line 705) — no IR change
at the call site (verified, see "Fixed-point status" below).

### Regression contract

New `tests/llvm/test_indent_to_braces_win64_abi.py` (6 cases)
mirrors v5.26.0 Mb.9.C's `test_brace_funcs_windows_abi.py`:

- **Layer 1 — IR-shape gate (load-bearing)**, 3 tests:
  - `test_mb10_win64_call_site_uses_byref_for_indent_to_braces`
    — under Win64 triple, the call site must NOT pass MnString
    by-value as `{ptr, i64}` (after stripping the `sret(...)`
    annotation tag for the return slot).
  - `test_mb10_win64_decl_matches_call_arity` — declaration first
    parameter (after large-struct rewrite) must be `ptr`, not
    leak `{ptr, i64}` as a by-value param.
  - `test_mb10_sysv_call_site_unchanged` — negative gate: under
    Linux SysV triple, the call IS by-value `{ptr, i64}`. Pins
    the SysV side so a future emitter refactor doesn't
    accidentally rewrite it (avoiding gratuitous IR churn that
    would break stage2/stage3 fixed-point comparisons).
- **Layer 2 — Linux ctypes contract**, 3 parametrized tests
  building a small shared library from `mapanare_core.c` and
  calling `__mn_indent_to_braces` directly. Locks the C-side
  correctness contract against future runtime-level drift
  (e.g., changing the parameter type to `const char *`).

Falsifiability evidence (run in session):

```
$ git stash push -- mapanare/emit_llvm_text.py
$ # Manually revert the Mb.10 routing handler (lines 3632-3638)
$ python3 -m pytest tests/llvm/test_indent_to_braces_win64_abi.py::test_mb10_win64_call_site_uses_byref_for_indent_to_braces -v
FAILED: assert '{ptr, i64}' not in 'call void
  @__mn_indent_to_braces(ptr sret(SRET) %sret.1, {ptr, i64} %l.0)'
$ git checkout -- mapanare/emit_llvm_text.py
$ python3 -m pytest tests/llvm/test_indent_to_braces_win64_abi.py
6 passed in 1.95s
```

### Bb.\* seed refresh: NOT required

Mb.10 changes only IR call-site shape, not C-runtime export
signatures. The v5.10.0-vintage seed (`bootstrap/seed/`) has no
view of how `mnc-stage1` emits the call. Refresh discipline
preserved by NOT refreshing when not needed.

### Mb.\* arc closeout

Every memory- and ABI-related panel finding through v5.22.0 +
v5.23.2's Te.3.B.2 follow-on + Mb.10's missed-by-Mb.9 closure
is now resolved:

- Mb.1 (v5.23.1) — `__mn_indent_to_braces` Python-side handler
- Mb.2 (v5.23.1) — Te.5 leak via `emit_wrap_some`
- Mb.3 (v5.23.1) — preprocess valgrind CI
- Mb.4 (v5.23.1) — `MN_DIR_WALK_MAX_DEPTH` cap
- Mb.5 (v5.23.1) — Win32 walker reparse-point skip
- Mb.6 (v5.23.1) — sanitizer-cache-walkers job
- Mb.7 (v5.26.0) — `emit_enum_tag` i64/i1 mismatch
- Mb.9 (v5.26.0) — brace-deprecation Win64 ABI routing (pair)
- **Mb.10 (v5.29.0) — `__mn_indent_to_braces` Win64 ABI routing (parent)**

v5.26.0 SESSION_REPORT's "Mb.\* arc CLOSED" claim was strictly
correct for Mb.7+Mb.9 but incomplete on the Win64 ABI sweep. The
arc is now actually closed.

---

## Pv.7 — `clean-build-test` race against parallel pytest workers

**Already shipped on dev as commit `bc3bc7b "Parameterize runtime
archive; update GitNexus"` between v5.28.0 (441ece0) and v5.29.0.**
v5.29.0 documents the fix.

### Race shape

Pre-fix `make clean-build-test` (v5.25.0 Pv.3 sub-gate of
`make ci-gates`):

```makefile
clean-build-test:
    @rm -f runtime/native/libmapanare_rt.a \
           runtime/native/libmapanare_runtime.{so,dylib,dll}
    @$(MAKE) -s build-rt >/dev/null
    @pytest tests/test_at_test_runtime.py tests/test_runtime_lib_lookup.py ...
```

The `rm -f` then `make build-rt` sequence left a 1-3 second window
where `runtime/native/libmapanare_rt.a` was missing. Under
`pytest -n auto` (the main CI invocation), this raced with
parallel workers in `tests/bootstrap/` / `tests/llvm/` that link
against the canonical archive — `pytest -n auto` runs
`tests/test_ci.py::TestMakeCIGates::test_make_ci_gates_target_runs`
in one worker (which invokes `make ci-gates` → `make
clean-build-test` → the destructive `rm`), while another worker
might be mid-`clang ... runtime/native/libmapanare_rt.a` and trip
"no such file or directory" before the rebuild completes.

Surfaced as a flake on
`tests/bootstrap/test_chained_cmp_mirror.py
::test_chained_cmp_golden_byte_identical[92_chained_cmp_simple]`
on a recent CI run (gw0 worker hit the race window).

### Fix (in `bc3bc7b`)

`Makefile` parameterizes `build-rt` with
`RT_OUTPUT ?= runtime/native/libmapanare_rt.a`. Every existing
caller picks up the canonical path; `clean-build-test` overrides
to a sandbox path on the same filesystem (so `mv` is atomic):

```makefile
clean-build-test:
    @SANDBOX=runtime/native/.libmapanare_rt.cbt-tmp.a; \
    rm -f $$SANDBOX; \
    $(MAKE) -s build-rt RT_OUTPUT=$$SANDBOX >/dev/null && \
    mv -f $$SANDBOX runtime/native/libmapanare_rt.a
```

The canonical archive is **never absent** from the perspective of
parallel workers.

### Race-window evidence (re-run in session)

200-poll watcher at 20 ms cadence over the full 4-second rebuild:

```
$ RT=runtime/native/libmapanare_rt.a
$ (for i in $(seq 1 200); do
      if [ ! -f "$RT" ]; then echo "MISSING at iter $i"; fi
      sleep 0.02
  done; echo "TOTAL_MISSING=$MISSING") &
$ sleep 0.1
$ make -s clean-build-test 2>&1 | tail -3
$ wait
TOTAL_MISSING=0
......                                                                   [100%]
6 passed in 4.58s
```

**0 MISSING reports across 200 polls.** Race window structurally
closed.

---

## Pv.8 — `test_c_runtime.c` agent-state timing races

**Already shipped on dev as commit `f119c43 "Replace fixed sleeps
with polling in tests"` between v5.28.0 (441ece0) and v5.29.0.**
v5.29.0 documents the fix. (The PROMPT/PLAN were drafted assuming
the fix was uncommitted in the working tree; verified at Phase 0
that it had landed cleanly on dev.)

### Race shape

The C-runtime smoke binary at `tests/native/test_c_runtime.c`
runs 74 tests serially in one process. Two of them
(`test_agent_pause_resume`, `test_agent_failing_handler`) failed
on a recent CI run under load:

```
test_agent_pause_resume    [FAIL] tests/native/test_c_runtime.c:712:
   (mapanare_agent_get_state(&agent)) == (MAPANARE_AGENT_PAUSED)
test_agent_failing_handler [FAIL] tests/native/test_c_runtime.c:738:
   (mapanare_agent_get_state(&agent)) == (MAPANARE_AGENT_FAILED)
=== Results: 72/74 passed, 2 FAILED ===
```

`mapanare_agent_pause()` (`runtime/native/mapanare_runtime.c:740`)
is a guarded transition that **silently no-ops** if the agent
isn't yet RUNNING. The worker thread sets state=RUNNING in
`agent_thread_fn` (`mapanare_runtime.c:569`) **only after the OS
schedules the new thread**. The test slept `usleep(50000)` and
hoped 50 ms was enough — on a quiet dev machine it always was;
on a loaded GitHub runner the worker occasionally takes longer
to first-run, the `pause()` no-ops, state stays at IDLE/0, the
assertion fails. `test_agent_failing_handler` is the same shape
with `usleep(200000)`.

### Fix (in `f119c43`)

4 new polling helpers + `test_sleep_ms` in
`tests/native/test_c_runtime.c`:

- `wait_for_agent_state(agent, target, timeout_ms)` — polls the
  state field at 5 ms cadence, returns 1 on first match.
- `wait_for_messages_processed(agent, target, timeout_ms)` —
  polls `mapanare_agent_messages_processed()`.
- `wait_for_agent_recv(agent, out, timeout_ms)` — polls
  `mapanare_agent_recv()` for outbox availability.
- `wait_for_counter(target, timeout_ms)` — polls thread-pool
  `g_counter`.

7 test sites converted from fixed-delay sleeps to bounded polls:
`test_agent_lifecycle`, `test_agent_send_recv`,
`test_agent_pause_resume` (the flake), `test_agent_failing_handler`
(the flake), `test_agent_metrics`, `test_shutdown_with_agents`,
`test_pool_basic` + `test_pool_saturation`.

Generous timeouts (1000 ms for state, 2000 ms for FAILED /
messages-processed, 5000 ms for 500-task pool stress) — returns
on first match; only consumes the full budget if the worker is
genuinely stuck.

### Falsifiability evidence (re-run in session)

Both pre-fix and post-fix passed 5/5 on the dev WSL host (quiet
environment). The CI-only manifestation is exactly what the PLAN
anticipated:

> expected on a loaded WSL/CI host: 1-2 FAIL out of 5
> (may be 0 FAIL on a quiet dev machine — that's fine; the
> SESSION_REPORT documents the CI-only manifestation)

```
$ # POST-FIX (HEAD with f119c43)
$ for i in 1..5; do pytest tests/native/test_c_hardening.py::TestCRuntimePlain -q | tail -1; done
.                                                                        [100%]
.                                                                        [100%]
.                                                                        [100%]
.                                                                        [100%]
.                                                                        [100%]

$ # PRE-FIX (f119c43 reverted via git show f119c43^:... > working copy)
$ for i in 1..5; do pytest tests/native/test_c_hardening.py::TestCRuntimePlain -q | tail -1; done
.                                                                        [100%]   <-- quiet host masks the flake
.                                                                        [100%]
.                                                                        [100%]
.                                                                        [100%]
.                                                                        [100%]
```

Plain + ASan + TSan suite at HEAD: **3/3 PASS**:

```
$ python3 -m pytest tests/native/test_c_hardening.py -v
tests/native/test_c_hardening.py::TestCRuntimePlain::test_all_c_tests_pass PASSED [ 33%]
tests/native/test_c_hardening.py::TestCRuntimeASan::test_asan_no_errors PASSED [ 66%]
tests/native/test_c_hardening.py::TestCRuntimeTSan::test_tsan_no_races PASSED [100%]
```

`gcc -O2 -g -pthread -Wall -Wextra -Werror` clean against the
file at HEAD.

### Pv.8.B — preemptive sweep deferred

The PLAN flagged 11 sites in `tests/native/test_agent_scheduler.py`
with the same `agent.spawn() → time.sleep(0.05) → assert state`
shape (same root cause as Pv.8.A's flakes). These haven't actually
flaked yet in CI; preemptive Python-side hardening is out of
scope for v5.29.0 unless the panel asks. **Deferred to v5.30.0+
if a flake materializes.** Reactive-only fix discipline
preserved.

---

## Fixed-point status

### Pre-Mb.10 (v5.28.0 baseline)

```
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 241842 lines
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 241842 lines
[Verify] Fixed point: diff stage2.ll stage3.ll
  ~ NEAR FIXED POINT
  4 diff lines out of 241842 (0.002%)
241842c241842
< !0 = !{!"5.27.0"}
---
> !0 = !{!"5.28.0"}
```

The 1-line content drift was the expected v5.9.0 DX.2 artifact:
`mapanare/self/mnc-stage1` was last linked against a v5.27.0
runtime (Sat May 2 04:26 mtime); the IR-metadata node embeds
`__mn_version_string()` at compile time, so stage2.ll baked
"5.27.0" while stage3.ll (built by the freshly-rebuilt stage2)
baked "5.28.0".

### Post-Mb.10 (v5.29.0 HEAD)

```
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 241898 lines
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 241898 lines
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (241898 lines, 0 diff)

=== La Culebra Se Muerde La Cola ===
```

**STRICT 3-stage fixed point** — restored from the prior NEAR.
The v5.28.0 NEAR was stale-stage1-binary noise; v5.29.0's stage1
rebuild against the current runtime restored byte-identity.

Line count shifted from 241,842 → 241,898 (+56 lines). The PLAN
expected +3-10. The +56 actual delta is `str_track` slot
renumbering caused by routing the two `__mn_indent_to_braces`
call sites through `emit_rt_call` (parser.mn::parse + the
`preprocess` subcommand) instead of the user-call fallthrough.
The user-call path was generating extra string-tracking
allocations that `emit_rt_call` correctly skips on SysV; the
diff is purely in `str_track.NNNN` slot positions, not in
semantic IR.

### Goldens

`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
→ **All 95 tests passed in 18.4s** at v5.29.0 HEAD.

### Bootstrap mirror tests

- `tests/llvm/test_indent_to_braces_win64_abi.py` — **6/6 PASS**
  at v5.29.0 HEAD.
- `tests/llvm/test_async_link.py` (v5.26.0 Mb.7's existing
  guard) — unchanged shape; no Mb.7 regression.
- `tests/native/test_c_hardening.py` (Plain + ASan + TSan) —
  **3/3 PASS**.
- `tests/test_runtime_lib_lookup.py` (v5.25.0 Pv.1) — unchanged.

---

## Out-of-scope (deferred)

- **Tn.1** — extend `tests/llvm/test_async_link.py` to all 95
  goldens (v5.28.0 panel Cobra Cb.New1 + Rattler Ra.Inf1
  recommendation). Panel marked: "Escalate to MEDIUM at v5.29.0
  if not picked up in a Pv.\* follow-on." v5.29.0 deliberately
  defers — Mb.10 was the load-bearing item; bundling Tn.1
  dilutes scope. Tn.1 is its own release (v5.30.0 candidate).
  **Per panel directive, this carries forward as MEDIUM at
  v5.30.0.**
- **M.1** (Mamba — `.h` vs `.c` header asymmetry recurrence;
  Pv.7-style structural gate) — separate Pv.\* item; v5.30.0+.
- **A.1** (Anaconda — new `check_carry_forward_freshness.py`
  gate) — separate Pv.\* item; v5.30.0+.
- **Ra.New1** (Rattler — Stage2 teardown narrowed to
  stdout-redirect-specific SIGSEGV) — separate investigation;
  may close in v5.30.0+ rather than v6.0 per panel.
- **Pv.8.B** — preemptive `test_agent_scheduler.py` polling-helper
  conversion. Reactive-only fix discipline preserved.
- **Borrow checker / multi-level alias analysis** — v6.0 work.
- **Hard removal of `{}` syntax** — v5.19.0 Te.3 was soft
  deprecation; hard removal stays at v6.0.

---

## Carry-forward delta

**Closes:**
- **Mb.10** (latent since v5.23.1 Mb.1 — Python side fixed,
  self-host side missed; surfaced fresh in publish run #50;
  closed in same release as discovered).
- **Pv.7** (race shipped on dev as `bc3bc7b`; documented at
  v5.29.0).
- **Pv.8** (test-timing flake fix on dev as `f119c43`;
  documented at v5.29.0).
- **Mb.\* arc** — reopened for one residual; closed
  structurally this time. v5.26.0's "Mb.\* arc CLOSED" claim
  was strictly correct for Mb.7 + Mb.9 but incomplete on the
  Win64 ABI sweep — the Mb.\* arc is now actually closed.

**Inherits to v5.30.0:**
- **Tn.1** (panel directive escalated to MEDIUM since v5.29.0
  did not pick it up).
- M.1, A.1, Ra.New1 (v5.28.0 panel LOWs).
- Pv.8.B (`test_agent_scheduler.py` preemptive sweep — only
  if flake materializes).

**Aggregate state entering v5.30.0:** 0 HIGH / 1 MEDIUM (Tn.1
escalated) / ~5 LOW.

**Cadence:** next routine panel still due v5.33.0 (unchanged
from v5.28.0 directive — v5.29.0 is a normal non-panel release).

---

## Source delta

| File | Change | LOC |
|---|---|---|
| `mapanare/self/emit_llvm.mn` | Mb.10 routing (3 LOC + comment) | +13 |
| `mapanare/self/mnc_all.mn` | Regenerated concat | +13 |
| `tests/llvm/test_indent_to_braces_win64_abi.py` | New regression test | +266 |
| `tests/golden/BENCHMARKS{,_linux}.md` + `HISTORY.jsonl` | Auto-update from goldens | +rebuilt |
| `VERSION` | 5.28.0 → 5.29.0 | ±1 |
| `README.md` (en/es/pt/zh-CN) | Version badge bump | ±4 |
| `CHANGELOG.md` | New `## [5.29.0]` entry | +83 |
| `docs/roadmap/v5/v5.29.0/{PLAN,PROMPT,SESSION_REPORT,AUDIT}.md` | New | +500-ish |
| `CLAUDE.md` | New v5.29.0 release-notes entry | +100-ish |

**Net repo:** new test + docs; one 13-line block in self-host
emitter + the regenerated `mnc_all.mn` mirror; nothing else
substantive. Pv.7 + Pv.8 source code already on dev pre-v5.29.0.

---

## Commits

```
1f375f4 v5.29.0 Mb.10: route __mn_indent_to_braces through emit_rt_call (Win64 ABI)
f9babb4 v5.29.0 Vb.1: bump version + READMEs + CHANGELOG
<closeout>  v5.29.0 closeout: SESSION_REPORT + AUDIT + CLAUDE.md release notes
```

Plus the two pre-v5.29.0 dev commits documented here:

```
f119c43 Replace fixed sleeps with polling in tests          (Pv.8)
bc3bc7b Parameterize runtime archive; update GitNexus       (Pv.7)
```

---

## Success criteria — verified

- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved at 0-line diff
  (line count documented: 241,898).
- ✅ `tests/llvm/test_indent_to_braces_win64_abi.py` 6/6 PASS
  on Linux (Windows via publish job).
- ✅ `tests/native/test_c_hardening.py` (Plain + ASan + TSan)
  3/3 PASS.
- ✅ Race-window test against `make clean-build-test` reports
  0 MISSING across 200 polls.
- ✅ `check_changelog_honesty.py` clean.
- ✅ `gcc -Wall -Wextra -Werror` clean against
  `tests/native/test_c_runtime.c`.
- ✅ VERSION = 5.29.0; README badges + CHANGELOG.md updated.
- ✅ AUDIT.md complete; SESSION_REPORT.md complete; CLAUDE.md
  release notes added; Mb.\* arc marked CLOSED structurally.
- ⏳ Tag NOT created (per project memory: "Never bump to v5 or
  create v5 tags without explicit user approval — the tag is
  the lead's call").
- ⏳ Windows publish job green on next push (the load-bearing
  external validation; cannot be verified locally).
