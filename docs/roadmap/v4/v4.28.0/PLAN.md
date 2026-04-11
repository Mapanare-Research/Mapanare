# Mapanare v4.28.0 — Concurrency + v3.47.0 Carry-Forwards

> **Recovery release #2.** v4.27.0 closed the 8 CRITICAL items from the
> v4.26.0 panel. v4.28.0 closes the HIGH-severity concurrency regressions
> and the v3.47.0 carry-forward items that were missed across 27 versions.
> Still **zero new features.**

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.27.0
**Estimated work:** 1 day
**Theme:** Make concurrency safe; pay back the v3.47.0 debt that should never have aged.

---

## The Problem

The v4.26.0 panel found three categories of HIGH-severity issues that fall
together because they share a common root cause: **discipline that worked at
v3.47.0 stopped propagating into the v4.x changes.**

### Category A: New concurrency races since v4.0.0

The v3.47.0 panel praised the codebase for thread-safe dlopen loaders
(atomic CAS for `ssl_load`, `evp_load`, `pcre2_load`) and for the locking
discipline in the signal subsystem. That discipline did not propagate to
the v4.x signal/agent work:

| Site | File:Line | Issue | Reporter |
|------|-----------|-------|----------|
| Signal value mutation | `mapanare_core.c:1887-1898` | `__mn_signal_set` and `recompute` read/write `value` outside the signal lock | Viper H5, Mamba H1 |
| Agent inbox ring | `mapanare_runtime.c` | SPSC ring used as MPSC without producer lock | Viper H5 |
| Type registry | `mapanare_core.c` | Global hash table no locking | Viper H5 |
| `mn_init_tag_strings` | `mapanare_core.c` | Race on init flag, **7th cycle carry-forward** | Mamba |

### Category B: v3.47.0 hard-blocker carry-forwards

The v3.47.0 panel marked these as "must fix before tagging v4.0.0." They
were fixed in v4.0.0. They are **byte-identical** to the pre-v4.0.0 state at
v4.26.0 — which means there was a revert somewhere between v4.0.0 and
v4.26.0 that no review caught:

| Site | File:Line | Issue | Reporter |
|------|-----------|-------|----------|
| matmul shape NULL check | `mapanare_gpu_builtins.c:161-185` | `malloc` return not NULL-checked | Cobra #6, Viper |
| matmul dimension validation | `mapanare_gpu_builtins.c:161-185` | Inner dimension mismatch not checked | Cobra #6 |
| GPU temp file race | `mapanare_gpu.c:822-823` | Temp file collision if two processes invoke GPU codegen simultaneously | Viper |
| Windows GPU init race (original) | GPU init path | Use `InitOnceExecuteOnce` not double-checked locking | Cobra #5 |
| Windows GPU init race (propagated) | `mapanare_core.c:1815-1823` | Same pattern propagated to signal mutex | Cobra #5 |

The fact that these are byte-identical to v3.47.0 means the v4.0.0 fixes
were reverted somewhere along the way. Phase 0 of v4.28.0 is to find when.

### Category C: Stale version string regression

| Site | File:Line | Issue | Reporter |
|------|-----------|-------|----------|
| Self-hosted version string | `mapanare/self/main.mn:32` | Returns `"mapanare 4.7.1"` — **19 versions stale** | Rattler #21, Anaconda I-20 |
| Regression test | `tests/self_hosted/test_main_mn.py::test_version_string` | **Currently failing locally** (Anaconda reproduced) | Anaconda |

This is a direct regression of the v3.45.0 fix. The test exists but is
failing. The v4.26.0 panel found this by running the test.

---

## Phase 0: Forensics — find the v4.0.0 → v4.x revert

**Before fixing the matmul carry-forwards, find when they regressed.**
This is 30 minutes of `git log -p` and `git bisect` to identify the commit
that reverted the v4.0.0 fixes. The reason: if there's a systemic cause
(e.g., a refactor that re-applied an older snapshot of the file), it will
explain the other carry-forwards too.

- [ ] `git log -p mapanare_gpu_builtins.c | grep -A 20 "matmul"` — find when
      the NULL check was removed
- [ ] `git log -p mapanare/self/main.mn | grep -B 2 -A 2 "version"` — find
      when `4.7.1` was hardcoded
- [ ] Document findings in `docs/roadmap/v4/v4.28.0/FORENSICS.md` —
      whichever commit reverted the v4.0.0 fixes is the one to learn from
- [ ] If there's a pattern (e.g., a refactor re-imported an older `.c` file
      from a stale source tree), note it as a process item for v4.31.0

---

## Phase 1: Concurrency hardening

### Phase 1.1: Signal value mutation under lock

- [ ] `runtime/native/mapanare_core.c:1887-1898` — `__mn_signal_set` reads
      old `value`, writes new `value`, both outside the signal lock. The
      lock exists; the value mutation is just outside it.
- [ ] Move all `value` reads and writes inside the existing critical section
      (extend the lock scope to cover both, or split into a write lock and
      keep readers under read lock)
- [ ] `recompute` (same file region) has the same issue — fix together
- [ ] Add a TSan-only stress test: 4 threads, 1 signal, 10000 set/get pairs;
      under TSan no races reported

### Phase 1.2: Agent inbox ring — MPSC vs SPSC

- [ ] `runtime/native/mapanare_runtime.c` — the agent inbox ring is declared
      SPSC but used by multiple producer threads (any thread that calls
      `agent_send`)
- [ ] Choose one of:
      - Add a producer lock (`pthread_mutex_t inbox_producer_lock`) — simple
        but contended
      - Switch to a real MPSC structure (e.g., Vyukov bounded MPSC) — more
        work, much faster under contention
- [ ] Recommendation: producer lock for v4.28.0 — ship the correctness, defer
      performance to v4.32.0+
- [ ] Add a TSan stress test: 4 sender threads, 1 agent, 10000 messages each

### Phase 1.3: Type registry locking

- [ ] `runtime/native/mapanare_core.c` — global type registry hash table is
      currently unlocked
- [ ] Add a `pthread_rwlock_t type_registry_lock`
- [ ] Reads under read lock; inserts under write lock
- [ ] Stress test: 8 threads, 1000 type registrations + lookups each

### Phase 1.4: `mn_init_tag_strings` once-init (7th cycle)

- [ ] This has been carried forward across 7 review cycles. Fix it.
- [ ] Replace whatever current pattern is in place with `pthread_once_t` on
      POSIX and `InitOnceExecuteOnce` on Windows
- [ ] No more `volatile int initialized = 0` patterns anywhere
- [ ] Grep for the pattern across the runtime and fix every site

---

## Phase 2: v3.47.0 hard-blocker carry-forwards

### Phase 2.1: matmul shape NULL check

- [ ] `runtime/native/mapanare_gpu_builtins.c:161-185` — apply the 5-line
      fix the v3.47.0 README already specified
- [ ] Add the regression test from the v3.47.0 panel: synthesize a malloc
      failure (e.g., via `__wrap_malloc` in the test build) and assert that
      the matmul call returns an error rather than crashing

### Phase 2.2: matmul dimension validation

- [ ] Same file, same region — validate that left.cols == right.rows before
      dispatching to the GPU kernel
- [ ] Return a typed error if the dimensions don't match
- [ ] Regression test: call matmul with `[3,4] @ [5,6]`; assert error, not
      crash, not silent miscompute

### Phase 2.3: GPU temp file race

- [ ] `runtime/native/mapanare_gpu.c:822-823` — current temp file path is
      not unique per process
- [ ] Use `mkstemp` (POSIX) / `GetTempFileNameW` (Windows) so two
      simultaneous GPU codegen invocations don't collide
- [ ] Stress test: invoke `gpu_tensor_add` from two threads simultaneously;
      assert no temp file collision

### Phase 2.4: Windows GPU init race

- [ ] Both sites: original (GPU init path) and propagated (`mapanare_core.c:1815-1823`)
- [ ] Use `InitOnceExecuteOnce` at both sites
- [ ] Document in the source comment that this is the canonical Windows
      pattern, and link to the v3.47.0 review item that introduced it
- [ ] Add a comment block explaining why double-checked locking is wrong
      under the Windows memory model so this doesn't get reverted again

---

## Phase 3: Version string regression

### Phase 3.1: Wire `main.mn` version to `VERSION` file

- [ ] `mapanare/self/main.mn:32` — currently hardcoded `"mapanare 4.7.1"`
- [ ] Add a build-time substitution step in `scripts/build_stage1.py` and
      `Makefile`: read `VERSION`, substitute into a generated header or a
      sed-edited copy of `main.mn` before compilation
- [ ] Verify: `mnc --version` after a fresh build prints the contents of
      the `VERSION` file
- [ ] Add the substitution step to CI

### Phase 3.2: Un-skip the regression test

- [ ] `tests/self_hosted/test_main_mn.py::test_version_string` — currently
      failing locally per Anaconda's reproduction
- [ ] After Phase 3.1, this test must pass
- [ ] Remove any `@pytest.mark.skip` or `xfail` decorator on it
- [ ] Add a CI assertion that the test is in the run list (catch future
      silent skipping)

---

## Phase 4: Carry-forward debt audit

The v4.26.0 panel reported a carry-forward resolution rate collapse from
~64% to ~10%. v4.28.0 is the place to inspect what was deferred and either
fix it or document why it's still deferred.

- [ ] Read `.reviews/v3.47.0/README.md` and extract the full carry-forward
      list
- [ ] Read `.reviews/v4.26.0/README.md` "Carry-forward debt" section
- [ ] For each item: status one of `FIXED-IN-v4.27.0`, `FIXED-IN-v4.28.0`,
      `DEFERRED-TO-v4.30.0` (with reason), `DEFERRED-TO-v4.31.0` (with reason),
      `INTENTIONALLY-IGNORED` (with reason)
- [ ] Write `docs/roadmap/v4/v4.28.0/CARRY_FORWARD_AUDIT.md` with the table
- [ ] Items not in the table are not allowed to ship — they must be in the
      audit before v4.28.0 tags

---

## Exit Criteria

| # | Check | Required |
|---|-------|----------|
| 1 | Phase 0 forensics complete; FORENSICS.md written | YES |
| 2 | `__mn_signal_set` value mutation under lock; TSan stress test passes | YES |
| 3 | Agent inbox ring is MPSC-safe (lock or real MPSC); TSan passes | YES |
| 4 | Type registry uses rwlock; stress test passes | YES |
| 5 | `mn_init_tag_strings` uses `pthread_once`/`InitOnceExecuteOnce` | YES |
| 6 | matmul shape NULL check + regression test | YES |
| 7 | matmul dimension validation + regression test | YES |
| 8 | GPU temp file race fixed via `mkstemp`/`GetTempFileNameW` | YES |
| 9 | Windows GPU init race fixed at both sites with `InitOnceExecuteOnce` | YES |
| 10 | `main.mn` version string sourced from `VERSION` at build time | YES |
| 11 | `test_version_string` passes; not skipped or xfailed | YES |
| 12 | Carry-forward audit document written and committed | YES |
| 13 | 46/46+ golden, 11/11 stage2 | YES |
| 14 | black/ruff/mypy clean | YES |
| 15 | TSan-clean for the new stress tests | YES |
| 16 | `docs/roadmap/v4/v4.28.0/SESSION_REPORT.md` written | YES |

---

## What v4.28.0 explicitly does NOT do

- FFI argtypes/restype — closed in v4.27.0
- `const` keyword — closed in v4.27.0
- `@gpu` decorator — closed in v4.27.0
- MIR verifier wiring — closed in v4.27.0
- Diagnostics consolidation — closed in v4.27.0
- Orphaned `mapanare_db.c` / `mapanare_html.c` (→ v4.29.0)
- `extern "Python"` 79 xfailed tests (→ v4.29.0)
- `verify_fixed_point.sh` cannot fail (→ v4.29.0)
- `await` coroutine implementation OR strike (→ v4.30.0)
- `_emit_agent_wrap` no-op stub (→ v4.30.0)
- Stale emitter carry-forwards (i64*, void()*, etc.) (→ v4.30.0)
- SPEC update, Spanish README sync (→ v4.31.0)
- DWARF debug info decision (→ v4.31.0)

---

## Verification Protocol

After every phase:

```bash
# C runtime sanity
gcc -c -fsyntax-only -Wall -Wextra -Werror runtime/native/mapanare_core.c -I runtime/native
gcc -c -fsyntax-only -Wall -Wextra -Werror runtime/native/mapanare_runtime.c -I runtime/native
gcc -c -fsyntax-only -Wall -Wextra -Werror runtime/native/mapanare_gpu.c -I runtime/native

# TSan stress tests
make test-tsan  # add this target if it doesn't exist

# matmul regression
python3 -m pytest tests/runtime/test_matmul_validation.py -v

# Version string regression
python3 -m pytest tests/self_hosted/test_main_mn.py::test_version_string -v

# Full validation
.\dev.ps1
```

Before tag: TSan-clean run of the full native test suite + the new stress
tests. If TSan reports any race that wasn't there at v4.0.0, do not tag.
