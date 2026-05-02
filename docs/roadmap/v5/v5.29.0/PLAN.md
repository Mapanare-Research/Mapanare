# v5.29.0 — Mb.10 + Pv.7 + Pv.8 — Win64 ABI closeout + CI race prevention

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.28.0 shipped (RE-PANEL Option A; v5.23-v5.27 arc
graded 9.72/10; cadence reset to v5.33.0 for next panel).
**Estimated effort:** 1 session (~3–4 hours; Pv.7 already shipped on
dev as commit `bc3bc7b`; Pv.8 already implemented in dev tree;
Mb.10 is a fresh ~5 LOC self-host emitter edit + stage1 rebuild +
fixed-point validation).
**Arc context:** Reopens the **Mb.\*** arc (declared closed at
v5.26.1) for one residual Win64 ABI gap — closes structurally this
time. Adds two **Pv.\*** items (Pv.7 + Pv.8) as continuation of
v5.25.0's CI prevention infrastructure. **Three findings, three
fixes, one release.**

---

## Why this exists

### Mb.10 — `__mn_indent_to_braces` Win64 ABI gap (latent since v5.23.1)

Publish run #50 surfaced a Windows-only SIGSEGV in
`build-native (windows-latest, mnc-win-x64.exe, x86_64-w64-mingw32)`:

```
warning: mapanare/self/mnc_all.mn: uses deprecated {}-block syntax (3125 occurrences)
D:\a\_temp\...sh: line 152: Segmentation fault
   ./mnc-win-x64.exe emit-llvm mapanare/self/mnc_all.mn > stage3.ll
=== Wb.1.dx: mnc-stage2 exited 139; capturing diagnostics ===
Thread 1 received signal SIGSEGV
0x00007ff7562e7edd in mnc-win-x64!__mn_indent_to_braces ()
```

**Sister bug to v5.26.0 Mb.9** (which fixed the same Win64 ABI byref-
threshold mismatch for `__mn_count_user_brace_block_openers` and
`__mn_emit_brace_deprecation_warning`). Mb.9 missed the parent
function `__mn_indent_to_braces` itself — only the brace-deprecation
detector pair got the routing fix in self-host `emit_llvm.mn`.

**Mechanism:**

`__mn_indent_to_braces(MnString source)` returns `MnString` (24 B:
`{ptr, i64, i64}`). On Win64 gcc lowers `MnString source` per Win64
ABI as **pass-by-hidden-pointer** (rcx = pointer to caller-stack
copy). `declare_runtime_fn` already accounts for this — it rewrites
the parameter to `ptr` via `win64_rewrite_decl_params`
(`mapanare/self/emit_llvm.mn:1150`).

The **call site** doesn't match the declaration. There is **no
routing for `__mn_indent_to_braces` in `emit_mir_call`** — it falls
through to the default user-call path, which on Win64 emits the
call with the struct passed by-value (`{ptr, i64, i64} %arg`)
while the declaration expects `ptr`. gcc generates code that
dereferences rcx as the struct pointer, but rcx actually contains
the struct's first 8 bytes (the `data` pointer of MnString) — bogus
pointer → SIGSEGV the moment the function tries to read its
`source.len` field.

**Asymmetry between emitters:**

| Emitter | `__mn_indent_to_braces` routing | `__mn_count_user_brace_block_openers` routing |
|---|---|---|
| Python (`emit_llvm_text.py`) | ✅ Line 3632 (v5.23.1 Mb.1) | ✅ Line 3654 (v5.26.0 Mb.9) |
| Self-host (`emit_llvm.mn`) | ❌ **MISSING** | ✅ Line 3781 (v5.26.0 Mb.9) |

So `mnc-stage1.exe` (built from Python's IR — has the fix) works on
Windows. The self-built `mnc-stage2.exe` / `mnc-win-x64.exe` (built
from stage2.ll, which is emitted by mnc-stage1 running the
self-host emitter logic — missing the fix) crashes the moment its
compiled-in `parser.mn::parse` calls `__mn_indent_to_braces`.

**Why now and not at v5.26.0:** Mb.9's author fixed the two
brace-deprecation funcs cited in publish-run-#48 but didn't sweep
for the parent function with the same shape. The bug stayed latent
because Windows publish wasn't getting to the stage2-self-compile
step (it was failing earlier on other things). The v5.28.0 panel
implicitly inherited Mb.10 as a still-open carry-forward but
didn't surface it (test gap; covered by Tn.1 panel rec).

**Why on SysV (Linux/macOS) the bug is silent:** the SysV AMD64
calling convention passes 16-24 byte aggregates in registers
regardless of the declared `ptr` vs struct shape — no ABI
mismatch from the receiver's perspective. Win64's 8-byte byref
threshold is what surfaces the bug.

### Pv.7 — `clean-build-test` race against parallel pytest workers

Pre-fix, `make clean-build-test` (v5.25.0 Pv.3) did:

```makefile
clean-build-test:
    @rm -f runtime/native/libmapanare_rt.a \
           runtime/native/libmapanare_runtime.{so,dylib,dll}
    @$(MAKE) -s build-rt >/dev/null
    @pytest tests/test_at_test_runtime.py tests/test_runtime_lib_lookup.py ...
```

The `rm -f` then `make build-rt` sequence left a 1-3 second window
where `runtime/native/libmapanare_rt.a` was missing. Under
`pytest tests/ -v -n auto` (the main CI invocation), this raced
with parallel workers in `tests/bootstrap/`, `tests/llvm/`, etc.
that link tests against the canonical archive — `pytest -n auto`
runs `tests/test_ci.py::TestMakeCIGates::test_make_ci_gates_target_runs`
in one worker (which invokes `make ci-gates` → `make
clean-build-test` → the destructive `rm`), while another worker
might be mid-`clang ... runtime/native/libmapanare_rt.a` and trip
"no such file or directory" before the rebuild completes.

Surfaced as a flake on `tests/bootstrap/test_chained_cmp_mirror.py
::test_chained_cmp_golden_byte_identical[92_chained_cmp_simple]`
on a recent CI run (gw0 worker hit the race window).

**Already fixed on dev** in commit `bc3bc7b "Parameterize runtime
archive; update GitNexus"`:

- `Makefile` parameterizes `build-rt` with `RT_OUTPUT ?=
  runtime/native/libmapanare_rt.a` — every existing caller gets
  the canonical path; `clean-build-test` overrides to a sandbox
  path.
- `clean-build-test` rebuilds into
  `runtime/native/.libmapanare_rt.cbt-tmp.a` (same filesystem so
  `mv` is atomic), then `mv -f` into the canonical path. The
  canonical archive is **never absent** from the perspective of
  parallel workers.

Pv.7 in v5.29.0 is the **release-documentation** pass on the
already-shipped fix — SESSION_REPORT writeup, race-test
falsifiability evidence, race-window measurement (200-poll
test at 20 ms cadence over the full 4-second rebuild produced
zero "MISSING" reports).

### Pv.8 — `test_c_runtime.c` agent-state timing races

The C-runtime smoke binary at `tests/native/test_c_runtime.c` runs
74 tests serially in one process. Two of them
(`test_agent_pause_resume` at `:712`,
`test_agent_failing_handler` at `:738`) failed on a recent CI run
under load:

```
test_agent_pause_resume    [FAIL] tests/native/test_c_runtime.c:712:
   (mapanare_agent_get_state(&agent)) == (MAPANARE_AGENT_PAUSED)
test_agent_failing_handler [FAIL] tests/native/test_c_runtime.c:738:
   (mapanare_agent_get_state(&agent)) == (MAPANARE_AGENT_FAILED)
=== Results: 72/74 passed, 2 FAILED ===
```

**Root cause:** `mapanare_agent_pause()` (`runtime/native/
mapanare_runtime.c:740`) is a guarded transition:

```c
if (atomic_load_i32(&agent->state) == MAPANARE_AGENT_RUNNING) {
    atomic_store_i32(&agent->state, MAPANARE_AGENT_PAUSED);
    ...
}
```

It **silently no-ops** if the agent isn't yet RUNNING. The worker
thread sets state=RUNNING in `agent_thread_fn` (`mapanare_runtime.c
:569`) **only after the OS schedules the new thread**. The test
slept `usleep(50000)` and hoped 50 ms was enough — on a quiet dev
machine it always was; on a loaded GitHub runner the worker
occasionally takes longer to first-run, the `pause()` no-ops,
state stays at IDLE/0, the assertion fails.

`test_agent_failing_handler` is the same shape: send the bad
message, sleep `usleep(200000)` and hope the worker has
processed it and transitioned to FAILED — usually enough but not
guaranteed under load.

**Already fixed on dev tree (uncommitted as of PLAN authoring):**

- New polling helpers in `tests/native/test_c_runtime.c`:
  - `wait_for_agent_state(agent, target, timeout_ms)` — polls the
    state field at 5 ms cadence, returns 1 on first match.
  - `wait_for_messages_processed(agent, target, timeout_ms)` —
    polls `mapanare_agent_messages_processed()`.
  - `wait_for_agent_recv(agent, out, timeout_ms)` — polls
    `mapanare_agent_recv()` for outbox availability.
  - `wait_for_counter(target, timeout_ms)` — polls thread-pool
    `g_counter`.
- 7 test sites converted from fixed-delay sleeps to bounded polls:
  `test_agent_lifecycle`, `test_agent_send_recv`,
  `test_agent_pause_resume` (the flake), `test_agent_failing_handler`
  (the flake), `test_agent_metrics`, `test_shutdown_with_agents`,
  `test_pool_basic` + `test_pool_saturation`.
- Generous timeouts (1000 ms for state, 2000 ms for FAILED /
  messages-processed, 5000 ms for 500-task pool stress) — returns
  on first match; only consumes the full budget if the worker is
  genuinely stuck.

Pv.8 in v5.29.0 is the **commit + release-documentation** pass on
the already-implemented fix.

---

## Goals

1. **Mb.10** Add the missing `__mn_indent_to_braces` routing in
   `mapanare/self/emit_llvm.mn::emit_mir_call`. ~5 LOC mirroring
   the v5.26.0 Mb.9 brace-deprecation routing. Closes the
   publish-run-#50 Windows SIGSEGV.
2. **Mb.10.B** Stage1 rebuild + strict 3-stage fixed-point
   validation. The IR delta is small (~3-10 lines per
   `__mn_indent_to_braces` call site, only `parser.mn::parse`
   calls it once); stage2.ll == stage3.ll preserved by
   construction since both stages use the same fixed emitter.
3. **Mb.10.C** New `tests/llvm/test_indent_to_braces_win64_abi.py`
   regression guard (~80 LOC). Cross-platform ctypes call into
   `runtime/native/libmapanare_runtime.so` exercising
   `__mn_indent_to_braces` with a real fixture; asserts return
   value matches what Python's `_indent_to_braces` produces. Not
   Windows-specific — Linux/macOS catches any future shape
   drift via direct ctypes call (no compiler involvement). Same
   shape as v5.26.0 Mb.9's `test_brace_funcs_windows_abi.py`.
4. **Mb.10.D** Bb.\* seed refresh: **NOT required.** No new
   C-runtime exports, no call-shape changes — only IR call-site
   shape. The v5.10.0-vintage seed is unaffected.
5. **Pv.7** SESSION_REPORT documentation of the
   `clean-build-test` sandbox + atomic-rename fix shipped in
   commit `bc3bc7b`. Race-window measurement evidence captured.
6. **Pv.8** Commit + SESSION_REPORT documentation of the
   `test_c_runtime.c` polling helpers. Falsifiability evidence:
   stash the helpers, watch flakes return; restore, watch them
   disappear.
7. **Version bump** to 5.29.0 via `python scripts/bump_version.py
   5.29.0`. Updates VERSION, README.md, localized READMEs
   (es/pt/zh-CN), CHANGELOG.md.
8. **Windows publish job** green on next push — Mb.10 closes the
   only remaining Wb.\* failure mode.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Mb.10.A** | HIGH | **Self-host emit routing for `__mn_indent_to_braces`.** Add to `mapanare/self/emit_llvm.mn::emit_mir_call` (around line 3787, near the v5.26.0 Mb.9 brace-deprecation routing): `if fn_name == "__mn_indent_to_braces": let as_itb: String = llvm_string() + " " + args[0].name; return emit_rt_call(st, dn, llvm_string(), "__mn_indent_to_braces", as_itb)`. ~3-5 LOC. Comment cross-referencing v5.23.1 Mb.1 (Python side) and v5.26.0 Mb.9 (sister functions). | 30 min |
| **Mb.10.B** | HIGH | **Stage1 rebuild + fixed-point validation.** Re-run `python scripts/build_stage1.py`, then `bash scripts/verify_fixed_point.sh`. Strict 0-line diff between stage2.ll and stage3.ll preserved (both use the fixed emitter); absolute line count shifts ~3-10 lines from v5.28.0's 241,842 baseline (one call site, sret-rewritten). Document the new line count in SESSION_REPORT. | 30 min |
| **Mb.10.C** | MEDIUM (regression guard) | **New `tests/llvm/test_indent_to_braces_win64_abi.py`** (~80 LOC). Cross-platform ctypes call into the runtime archive; constructs a known-good MnString; calls `__mn_indent_to_braces`; asserts return value matches `mapanare.parser._indent_to_braces` (Python reference). Mirror of v5.26.0 Mb.9's `test_brace_funcs_windows_abi.py`. Falsifiability: stash the Mb.10.A edit, rebuild stage1, run the test → Linux passes (stage1.ll has the Python fix, runtime is correct), but stage2 self-compile fails on Windows. The pytest test exercises the runtime directly via ctypes — guards against future C-side ABI drift, not the emitter routing per se. | 1h |
| **Mb.10.D** | LOW | **Bb.\* seed refresh: explicitly NOT required.** Document this in SESSION_REPORT — Mb.10 changes only IR call-site shape, not C-runtime export signatures. The v5.10.0-vintage seed has no view of how mnc-stage1 emits the call. Seed refresh discipline preserved by NOT refreshing when not needed. | 5 min |
| **Pv.7** | MEDIUM (already shipped) | **SESSION_REPORT writeup of `bc3bc7b`.** Document: race shape (rm + rebuild window), fix shape (sandbox + atomic mv), evidence (200-poll test at 20 ms cadence over 4-second rebuild = 0 MISSING reports). No code edits — `bc3bc7b` is on dev. | 30 min |
| **Pv.8.A** | MEDIUM | **Commit `tests/native/test_c_runtime.c` polling helpers** (currently uncommitted in working tree). 4 helpers, 7 test rewrites. Falsifiability: stash the helpers, run the test 5×, count flake rate; restore, run 5× again, all pass. | 30 min |
| **Pv.8.B** | LOW | **Optional: extend the polling-helpers pattern to `tests/native/test_agent_scheduler.py`.** Audit found 11 sites with the same `agent.spawn() → time.sleep(0.05) → assert state` shape. Same root cause (worker-thread state lag). **Decision:** defer to v5.30.0+ — these haven't actually flaked yet (Pv.8.A is the reactive fix; preemptive Python-side hardening is out of scope unless the panel asks). Document the deferral. | 0 (deferred) |
| **Vb.1** | LOW (mechanical) | **Version bump.** `python scripts/bump_version.py 5.29.0`. Validates the CHANGELOG.md entry, README badges, localized READMEs. Inspect the diff before commit — `bump_version.py` has been the source of one prior CARRY_FORWARD finding (v5.23.0 RC.3 goldens-badge), so eyeball the changes. | 10 min |

---

## Phase plan

### Phase 0 — pre-flight (~10 min)

```bash
# Confirm v5.28.0 HEAD is clean
make ci-gates
bash scripts/verify_fixed_point.sh --keep
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: 95/95, fixed point STRICT at 241,842 lines / 0 diff

# Confirm bc3bc7b's clean-build-test sandbox is in place
grep -A3 'SANDBOX=runtime' Makefile
# expected: lines about .libmapanare_rt.cbt-tmp.a and atomic mv

# Confirm test_c_runtime.c uncommitted polling helpers are in working tree
grep -n 'wait_for_agent_state\|wait_for_messages_processed' \
    tests/native/test_c_runtime.c
# expected: helper definitions + 7 call sites
```

### Phase 1 — Mb.10.A surgical fix (~30 min)

```bash
$EDITOR mapanare/self/emit_llvm.mn
# Around line 3787 (after the v5.26.0 Mb.9 brace-deprecation routing),
# add the __mn_indent_to_braces case.
```

The edit:

```mapanare
    // v5.29.0 Mb.10: route __mn_indent_to_braces through emit_rt_call
    // for the same Win64 ABI reason as v5.26.0 Mb.9 routed the
    // brace-deprecation siblings. The Python emitter has had this
    // routing since v5.23.1 Mb.1 (emit_llvm_text.py:3632); the
    // self-host side was never updated, so stage2.ll emitted a
    // by-value call against a declare-as-`ptr` signature on Win64,
    // and gcc lowered the call as pass-by-hidden-pointer with rcx
    // pointing into the struct's data buffer instead of into a
    // valid MnString — SIGSEGV on the first source.len read.
    if fn_name == "__mn_indent_to_braces":
        let as_itb: String = llvm_string() + " " + args[0].name
        return emit_rt_call(st, dn, llvm_string(), "__mn_indent_to_braces", as_itb)
```

Validate locally:

```bash
# Regenerate mnc_all.mn (concat self-host modules)
bash scripts/concat_self.sh

# Rebuild stage1
python scripts/build_stage1.py

# Goldens still 95/95?
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Diff stage2.ll for the parse() function specifically
./mapanare/self/mnc-stage1 emit-llvm mapanare/self/mnc_all.mn > /tmp/stage2.ll
grep -A 30 '__mn_indent_to_braces' /tmp/stage2.ll | head -40
# expected: sret + sarg pattern (no plain by-value call)
```

### Phase 2 — Mb.10.B fixed-point validation (~30 min)

```bash
bash scripts/verify_fixed_point.sh --keep
# expected: stage2.ll == stage3.ll, 0-line diff
# Line count: ~241,845-241,852 (a few lines above v5.28.0's 241,842
# from the new sret allocation + sarg rewrite at the one call site)
```

If stage2 != stage3 after the edit:

- Mb.10's IR change must be deterministic. If the diff is non-empty,
  it indicates the Mb.10 fix is being applied inconsistently
  between stages — STOP and re-investigate. Do not paper over.

### Phase 3 — Mb.10.C regression test (~1h)

```bash
$EDITOR tests/llvm/test_indent_to_braces_win64_abi.py
```

Test design (mirrors `test_brace_funcs_windows_abi.py`):

```python
"""v5.29.0 Mb.10 — runtime-side ABI gate for __mn_indent_to_braces.

Locks the C-runtime side of the Mb.10 fix: __mn_indent_to_braces
must read its MnString parameter and return a valid MnString under
every ABI. The publish-run-#50 Windows SIGSEGV was an emitter-side
bug (call site shape didn't match declaration), but a future
C-runtime edit could re-introduce the bug from the runtime side
(e.g., changing the parameter type to `const char *`). This test
exercises the function via ctypes — every CI host catches the
regression class.
"""
import ctypes, sys
from pathlib import Path
import pytest

LIB = Path("runtime/native") / (
    "libmapanare_runtime.so" if sys.platform == "linux" else
    "libmapanare_runtime.dylib" if sys.platform == "darwin" else
    "libmapanare_rt.dll"
)

class MnString(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_char_p),
        ("len",  ctypes.c_uint64),
        ("cap",  ctypes.c_uint64),
    ]

@pytest.fixture(scope="module")
def lib():
    if not LIB.exists():
        pytest.skip(f"{LIB} not built; run `make build-rt` first")
    return ctypes.CDLL(str(LIB))

@pytest.mark.parametrize("src,contains", [
    (b"fn main():\n    print(1)\n", b"fn main()"),
    (b"fn x():\n    pass\n",        b"fn x()"),
    (b"",                            b""),
])
def test_indent_to_braces_returns_valid_mnstring(lib, src, contains):
    """Mb.10: __mn_indent_to_braces must read MnString correctly."""
    s = MnString(src, len(src), len(src))
    lib.__mn_indent_to_braces.argtypes = [MnString]
    lib.__mn_indent_to_braces.restype = MnString
    out = lib.__mn_indent_to_braces(s)
    assert out.data is not None or len(src) == 0
    assert out.len >= len(contains)
    if contains:
        # Output is brace-form preprocessed source; must contain the
        # function header verbatim (preprocessor only adds braces
        # around indented blocks, doesn't rewrite identifiers).
        assert contains in ctypes.string_at(out.data, out.len)
```

Falsifiability round-trip:

```bash
git stash push -- mapanare/self/emit_llvm.mn
python scripts/build_stage1.py
make build-rt
pytest tests/llvm/test_indent_to_braces_win64_abi.py -v
# Linux passes (the runtime itself is correct; only the emitter
# routing was wrong). The test is the gate against future C-side
# regressions, not against the Mb.10.A emitter edit.
# Round-trip Mb.10's emitter contract via the existing
# tests/llvm/test_async_link.py instead — extend with a Win64
# triple variant.
git stash pop
```

### Phase 4 — Pv.7 + Pv.8 documentation + commit (~1h)

```bash
# Pv.7 evidence — re-run the race test on bc3bc7b's HEAD
RT=runtime/native/libmapanare_rt.a
(for i in $(seq 1 200); do
    if [ ! -f "$RT" ]; then echo "MISSING at iter $i"; fi
    sleep 0.02
done) &
WATCHER=$!
sleep 0.1
make -s clean-build-test 2>&1 | tail -3
wait $WATCHER
# expected: 0 MISSING reports across 200 polls (4-second window)

# Pv.8 evidence — falsifiability of the polling helpers
git stash push -- tests/native/test_c_runtime.c
for i in 1 2 3 4 5; do
    pytest tests/native/test_c_hardening.py::TestCRuntimePlain \
           ::test_all_c_tests_pass -q 2>&1 | tail -1
done
# expected: at least 1-2 FAIL out of 5 on a loaded runner
git stash pop
for i in 1 2 3 4 5; do
    pytest tests/native/test_c_hardening.py::TestCRuntimePlain \
           ::test_all_c_tests_pass -q 2>&1 | tail -1
done
# expected: 5/5 PASS

# Commit Pv.8.A
git add tests/native/test_c_runtime.c
git commit -m "v5.29.0 Pv.8: replace fixed-delay sleeps with polling helpers in test_c_runtime.c"
```

### Phase 5 — version bump (~10 min)

```bash
python scripts/bump_version.py 5.29.0
git diff VERSION README.md README.es.md README.pt.md README.zh-CN.md CHANGELOG.md
# Eyeball the diff. bump_version.py has surfaced one prior bug
# (v5.23.0 RC.3 — goldens badge); confirm no surprises.
git add VERSION README.md README.es.md README.pt.md README.zh-CN.md CHANGELOG.md
git commit -m "v5.29.0 Vb.1: bump version + READMEs + CHANGELOG"
```

### Phase 6 — closeout

```bash
# Full validation
make ci-gates
bash scripts/verify_fixed_point.sh
pytest tests/llvm/test_indent_to_braces_win64_abi.py \
       tests/native/test_c_hardening.py \
       tests/test_runtime_lib_lookup.py -v
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: all green; 95/95 goldens; 0-line stage2/3 diff

# Write SESSION_REPORT
$EDITOR docs/roadmap/v5/v5.29.0/SESSION_REPORT.md

# Update CLAUDE.md release notes
$EDITOR CLAUDE.md
# Add v5.29.0 entry above v5.28.0
```

---

## Out of scope

- **Tn.1** — extend `tests/llvm/test_async_link.py` to all 95
  goldens (v5.28.0 panel Cobra Cb.New1 + Rattler Ra.Inf1
  recommendation). Panel marked: "Escalate to MEDIUM at v5.29.0
  if not picked up in a Pv.\* follow-on." v5.29.0 deliberately
  defers — Mb.10 is the load-bearing item; bundling Tn.1 dilutes
  scope. Tn.1 is its own release (v5.30.0 candidate).
- **M.1** (Mamba — `.h` vs `.c` header asymmetry recurrence;
  Pv.7-style structural gate) — separate Pv.\* item; v5.30.0+.
- **A.1** (Anaconda — new `check_carry_forward_freshness.py`
  gate) — separate Pv.\* item; v5.30.0+.
- **Ra.New1** (Rattler — Stage2 teardown narrowed to
  stdout-redirect-specific SIGSEGV) — separate investigation;
  may close in v5.30.0+ rather than v6.0 per panel.
- **Pv.8.B** — preemptive `test_agent_scheduler.py` polling-helper
  conversion. Not yet flaky in CI; reactive-only fix discipline
  preserved.
- **Borrow checker / multi-level alias analysis** — v6.0 work.
- **Hard removal of `{}` syntax** — v5.19.0 Te.3 was soft
  deprecation; hard removal stays at v6.0.

---

## Risk

1. **Mb.10 stage2/3 fixed-point break.** The IR delta from the
   sret rewrite is small (~3-10 lines per call site, one call
   site total). Both stages use the same fixed emitter, so the
   diff between them stays at 0. Risk is the absolute line count
   shifting from 241,842 to ~241,852 — informational, not a
   gate. Mitigation: document the new line count in
   SESSION_REPORT.
2. **Mb.10 surfaces a deeper bug.** The Python and self-host
   emitters have been demonstrably divergent since v5.23.1. If
   bringing them into alignment surfaces other latent
   divergences in the IR they emit for `mnc_all.mn`, the
   stage2/3 fixed point could break (different stages emit
   different IR for the same input). Mitigation: Phase 0
   pre-flight verifies the v5.28.0 baseline; Phase 2 catches
   any non-trivial drift immediately.
3. **Pv.7 / Pv.8 documentation drift.** Both are already-shipped
   fixes; the risk is SESSION_REPORT not matching the actual
   committed code. Mitigation: write SESSION_REPORT after
   re-reading the diffs, not from memory.
4. **Bump_version.py surprise.** Past instances: v5.23.0 RC.3
   (goldens badge regex didn't catch all locales). Mitigation:
   Phase 5 explicitly eyeballs the diff before commit.

---

## Success criteria

- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved at 0-line diff (line
  count documented).
- ✅ `tests/llvm/test_indent_to_braces_win64_abi.py` green on
  Linux + macOS (Windows via publish job).
- ✅ `tests/native/test_c_hardening.py::TestCRuntimePlain` /
  `TestCRuntimeASan` / `TestCRuntimeTSan` 3/3 deterministic
  (5/5 runs PASS each).
- ✅ Race-window test against `make clean-build-test` reports
  0 MISSING across 200 polls.
- ✅ `make ci-gates` clean.
- ✅ `make lint` clean.
- ✅ Windows publish job (`build-native (windows-latest,
  mnc-win-x64.exe, x86_64-w64-mingw32)`) green on next push.
- ✅ VERSION = 5.29.0; README badges + CHANGELOG.md updated.
- ✅ SESSION_REPORT.md complete; CLAUDE.md release notes added;
  Mb.\* arc reopened-and-closed at v5.29.0.

---

## Carry-forward delta

Closes:
- **Mb.10** (latent since v5.23.1 Mb.1 — Python side fixed,
  self-host side missed; surfaced fresh in publish run #50;
  closed in same release as discovered).
- **Pv.7** (race shipped on dev as `bc3bc7b`; documented at
  v5.29.0).
- **Pv.8** (test-timing flake fix in dev tree; committed +
  documented at v5.29.0).
- **Mb.\* arc** — reopened for one residual; closed
  structurally this time. v5.26.0's "Mb.\* arc CLOSED" claim
  was strictly correct for Mb.7 + Mb.9 but incomplete on the
  Win64 ABI sweep — the Mb.\* arc is now actually closed.

Inherits to v5.30.0:
- Tn.1 (escalate to MEDIUM per v5.28.0 panel directive if not
  picked up here — and v5.29.0 explicitly does not pick it up).
- M.1, A.1, Ra.New1 (v5.28.0 panel LOWs).
- Pv.8.B (`test_agent_scheduler.py` preemptive sweep — only
  if flake materializes).

**Aggregate state entering v5.30.0:**
0 HIGH / 1 MEDIUM (Tn.1 escalated) / ~5 LOW.

**Cadence:** next routine panel still due v5.33.0
(unchanged from v5.28.0 directive — v5.29.0 is a normal
non-panel release).
