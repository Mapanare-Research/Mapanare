# v4.28.0 Session Report — 2026-04-11

> Recovery release #2. Zero new features. Second in the five-version
> recovery arc (v4.27.0 → v4.31.0). The arc terminates externally when
> the next 7-reviewer panel runs against v4.31.0 and returns aggregate
> ≥9.0 with zero NEEDS WORK verdicts.

## Verdict

- **Self-graded aggregate (lead):** ~9.0/10 — up from ~8.7/10 at v4.27.0.
  The concurrency fixes close the v4.26.0 panel's HIGH-severity runtime
  findings, and the v3.47.0 carry-forward items that had been overdue
  for 27 review cycles are now closed.
- **Self-graded vs external:** progress marker, not a release signal.
  The v4.31.0 panel is the only arbiter.

## Phase 0 finding — no revert to bisect

The v4.26.0 panel's hypothesis was that a commit between v4.0.0 and
v4.26.0 reverted the matmul fixes. `git log --follow` proved otherwise:
`runtime/native/mapanare_gpu_builtins.c` has **one commit in its entire
history** (`fbd382e v3.46.0`). The v4.0.0 CHANGELOG claim that the
matmul hard blockers were fixed was **false at the time it was
written** — the fix was claimed but never landed. The version string
issue was the same shape: bumped manually from v3.46.0 through v4.7.1,
then the bump step was dropped at v4.8.0 and never reinstated.

Both failures share one systemic cause: **manual release steps with no
automation or CI enforcement**. Phase 3 closes the version-string case
(build-time substitution from `VERSION`); the CHANGELOG honesty case
is scheduled for v4.31.0's CI gate work.

Full writeup: [`FORENSICS.md`](./FORENSICS.md).

## Phases completed

### Phase 0 — Forensics (30 min)

- `git log --follow runtime/native/mapanare_gpu_builtins.c` → 1 commit
- `git show 14be7378 -- runtime/native/mapanare_gpu_builtins.c` → empty diff (v4.0.0 didn't touch the file)
- `git log -p --follow mapanare/self/main.mn` → last version bump was `8b1ce50 v4.7.1`, 19 versions stale
- Wrote `docs/roadmap/v4/v4.28.0/FORENSICS.md` with the findings and the
  systemic cause

### Phase 3 — Version string (~45 min)

- `mapanare/self/main.mn:32` — hardcoded `"mapanare 4.7.1"` replaced
  with `"mapanare __MN_VERSION__"` placeholder + a doc comment
  explaining why.
- `scripts/build_stage1.py` — new `VERSION_FILE`, `VERSION_PLACEHOLDER`,
  and `_substitute_version()` helper. The helper runs on the root
  `main.mn` source before `compile_multi_module_mir` sees it. A
  missing placeholder is a build error.
- `tests/self_hosted/test_main_mn.py` — the existing `test_version_string`
  was passing by accident (substring match found "4.27.0" in my v4.27.0
  comment). Split into three real checks:
  - `test_version_placeholder_in_source`: raw source contains the
    placeholder
  - `test_version_string_is_not_hardcoded`: regex scan of the
    `version()` body rejects any `"mapanare X.Y.Z"` literal
  - `test_mnc_stage1_version_matches_version_file`: runs
    `./mnc-stage1 version` and asserts `VERSION` contents in stdout
- Verified end to end: `./mapanare/self/mnc-stage1 version` prints
  `mapanare 4.28.0` after the final VERSION bump.

### Phase 1.1 — Signal value mutation under lock

- `runtime/native/mapanare_core.c:1887-1930` — `__mn_signal_set`
  rewritten so the `memcmp` / `dtor` / `memcpy` sequence runs inside
  the signal mutex. Propagation is still called outside the lock so
  reactive callbacks that call back into `__mn_signal_set` don't
  deadlock.
- Scope note (documented inline): the reader path via
  `__mn_signal_get` still returns a raw pointer to `signal->value`,
  and a caller dereferencing that pointer against a concurrent writer
  is a separate API-shape issue (copy-on-read or get/release
  bracketing) tracked for a future release. The v4.26.0 panel's
  HIGH finding was specifically on the write side; that is what
  v4.28.0 closes.
- `tests/runtime/tsan/signal_stress.c` — 4 writer threads × 5000
  iterations. Runs TSan-clean after the fix.

### Phase 1.2 — Agent inbox producer lock (MPSC safety)

- `runtime/native/mapanare_runtime.h` — new field
  `mapanare_mutex_t inbox_producer_lock` on `mapanare_agent_t`.
  Follows the same pattern the thread pool's `work_queue` already
  uses (`queue_lock` at `line 112`) for its own SPSC→MPSC ring.
- `runtime/native/mapanare_runtime.c` — `mapanare_agent_init` calls
  `mapanare_mutex_init`, `mapanare_agent_destroy` calls
  `mapanare_mutex_destroy`, `mapanare_agent_send` locks around the
  `mapanare_ring_push` call.
- **Decision:** producer lock, not Vyukov bounded MPSC. Ships
  correctness in 30 minutes. Performance work is deferred to v4.32.0+
  per the PROMPT default. The panel called out the race; it did not
  call out the latency.
- `tests/runtime/tsan/inbox_stress.c` — 4 producers × 5000 msgs =
  20000 messages processed, no TSan races. Uses a handler that
  increments an atomic counter and waits for the consumer to drain
  before joining.

### Phase 1.3 — Type registry reader-writer lock

- `runtime/native/mapanare_core.c:2585-2720` — new
  `pthread_rwlock_t mn_typereg_lock` on POSIX, `SRWLOCK` on Windows.
  Inline `mn_typereg_read_lock` / `mn_typereg_write_lock` wrappers.
- `__mn_type_registry_put` takes the write lock around the open-
  addressing probe + entry update.
- `__mn_type_registry_get_kind` / `__mn_type_registry_get_name`
  snapshot the entry into a local buffer under the read lock, then
  release the lock before allocating a Mapanare string from the
  buffer (the string allocator takes other locks, which would
  otherwise invite deadlock).
- `__mn_type_registry_clear` takes the write lock.
- `tests/runtime/tsan/type_registry_stress.c` — 4 writer threads + 4
  reader threads × 2000 ops each over a shared 50-name corpus. TSan
  clean.

### Phase 1.4 — `pthread_once` / `InitOnceExecuteOnce` (7th-cycle fix)

- `runtime/native/mapanare_core.c` — `mn_init_tag_strings`,
  `init_small_int_cache`, and the Windows `intern_lock` init all
  rewritten on top of `pthread_once` (POSIX) /
  `InitOnceExecuteOnce` + `INIT_ONCE_STATIC_INIT` (Windows). The
  3-year-old `if (init_flag) return; ...; init_flag = 1;` pattern is
  gone from the runtime entirely.
- `runtime/native/mapanare_core.c:1811-1830` — `mn_signal_mutex` init
  on Windows also switched from `InterlockedCompareExchange` to
  `InitOnceExecuteOnce`. Fixes the Cobra #5 propagated-race site.
- `runtime/native/mapanare_gpu.c:46-51, 1057-1085` — `g_gpu_init_once`
  switched from `volatile LONG` + `InterlockedCompareExchange` to
  `INIT_ONCE` + `InitOnceExecuteOnce`. Fixes the original Cobra #5
  GPU init race.
- `grep InterlockedCompareExchange runtime/native/*.c` now returns
  only historical comments explaining what was replaced. No active
  use remains.
- `mn_init_tag_strings` has been a carry-forward for **7 review
  cycles** (Mamba, v4.26.0 panel). It was the longest-running runtime
  debt in the project. It is closed.

### Phase 2.1 + 2.2 — matmul NULL check and dimension validation

- `runtime/native/mapanare_gpu_builtins.c:161-260` — `__mn_gpu_tensor_matmul`
  rewritten with three new checks at the top of the function:
  1. Positive-dim check (`m > 0 && n > 0 && k > 0`).
  2. Overflow-safe product check via `__int128` where available, with
     a per-step fallback (`m > INT64_MAX / k`).
  3. Flat-length consistency check (`a->len == m*k`, `b->len == k*n`).
- The shape-array `malloc`s are now NULL-checked with the same
  cleanup pattern the v3.47.0 panel asked for.
- Invalid inputs return an empty list instead of crashing. The
  language-level behaviour is consistent with the pre-existing
  `tensor_from_list` error path in the simpler binary ops.
- `tests/runtime/tsan/matmul_validation.c` — 7 regression cases,
  including one that allocates valid 2x3 and 3x4 inputs and runs a
  real matmul against an RTX 4090 to prove the non-crash path still
  works.

### Phase 2.3 — GPU temp file race

- `runtime/native/mapanare_gpu.c:827-900` — `vk_compile_glsl` no
  longer uses hardcoded `/tmp/mn_gpu_shader.comp` /
  `mn_gpu_shader.spv` paths. POSIX path uses `mkstemps` (template
  `/tmp/mn_gpu_shader_XXXXXX.comp`, 5-char `.comp` suffix kept).
  Windows path uses `GetTempPathW` + `GetTempFileNameW`, widening
  from the returned wchar into a UTF-8 buffer for the existing
  `CreateProcessA` glslc invocation.
- Had to shrink `tmp_glsl_buf` from 512 to 256 + widen
  `tmp_spirv_buf` to 264 to satisfy GCC's `-Wformat-truncation` under
  `-Werror` after the `snprintf(..., "%s.spv", ...)` pattern. Noted
  inline — these buffers are larger than any realistic temp dir
  under both platforms.

### Phase 2.4 — Windows GPU init race

- **Closed as a side-effect of Phase 1.4.** Both sites the v4.26.0
  panel called out (`mapanare_gpu.c:1059-1062` original + `mapanare_core.c:1815-1823`
  propagated) use `InitOnceExecuteOnce` now. The grep I ran after
  Phase 1.4 showed zero `InterlockedCompareExchange` in non-comment
  positions.

### Phase 4 — Carry-forward audit

- `docs/roadmap/v4/v4.28.0/CARRY_FORWARD_AUDIT.md` — every item from
  `.reviews/v3.47.0/README.md` and `.reviews/v4.26.0/README.md`
  classified with a target release. Status legend:
  `FIXED-IN-v4.27.0`, `FIXED-IN-v4.28.0`, `DEFERRED-TO-v4.29.0/v4.30.0/v4.31.0`,
  `INTENTIONALLY-IGNORED` (with reason), or `NEVER-REAL` (the matmul
  CHANGELOG claim). No item is in limbo.

## Carry-forward closed

### v3.47.0 hard blockers (conditional on v4.0.0)

- Matmul shape NULL check (Cobra) — Phase 2.1
- Matmul dimension validation (Viper, Cobra) — Phase 2.2
- GLSL temp file race (Viper) — Phase 2.3
- Windows GPU init race (Cobra) — Phase 2.4 / 1.4

### v3.47.0 should-fix items

- `mn_init_tag_strings` thread safety (7th cycle) — Phase 1.4

### v4.26.0 panel HIGH items closed this release

- Signal / recompute value mutation outside lock — Phase 1.1
- Agent inbox SPSC-used-as-MPSC — Phase 1.2
- Type registry unlocked — Phase 1.3
- Windows init race propagated to signal mutex — Phase 1.1 / 1.4
- `main.ll` version string stale `mapanare 4.7.1` — Phase 3
- `mn_init_tag_strings` carry-forward → closed — Phase 1.4

## Carry-forward still open (deferred by design)

See [`CARRY_FORWARD_AUDIT.md`](./CARRY_FORWARD_AUDIT.md) for the full
table. Summary of where each deferred item lands:

| Target | Count | Examples |
|---|---|---|
| v4.29.0 | 6 | orphaned `db.c`/`html.c`, `extern "Python"` xfails, `verify_fixed_point.sh` teeth, `stage3.ll`, `--no-check` warning, Makefile enumeration |
| v4.30.0 | 7 | `await` coroutine, agent dispatch, optimizer ICE, six emitter 7-cycle items |
| v4.31.0 | 7 | SPEC sync, Spanish README, User-Agent bump, dead code sweep, CHANGELOG honesty CI, docs-drift CI, hollow-feature CI |
| v5.x | 1 | DWARF debug info decision (or v4.31.0 if appetite) |

## Measurements

| Metric | v4.27.0 | v4.28.0 | Δ |
|---|---|---|---|
| Golden tests | 46/46 | 46/46 | 0 |
| Stage2 modules valid | 11/11 | 11/11 | 0 |
| `mapanare/self/mnc-stage1` | 3,221,600 B | 3,231,184 B | +9,584 |
| `mapanare/self/main.ll` lines | 183,658 | 183,658 | 0 (same MIR) |
| Passing pytest in core suites | 345 | 614 (includes self_hosted) | +269 |
| TSan stress tests | 0 | 4 | +4 |
| `raise NotImplementedError` in compile path | 0 | 0 | 0 |
| `InterlockedCompareExchange` in runtime (non-comment) | 3 | 0 | −3 |
| Hardcoded `"mapanare X.Y.Z"` in self-hosted | 1 | 0 | −1 |
| `pthread_once` / `InitOnceExecuteOnce` sites | 1 | 8 | +7 |
| Signal write path outside lock | yes | no | — |
| Agent inbox MPSC-safe | no | yes | — |
| Type registry locked | no | yes | — |
| Carry-forward items in `AUDIT.md` | n/a | all tracked | +1 doc |

## Decisions Made

1. **Agent ring — producer lock, not Vyukov.** Ships correctness now.
   Real MPSC is deferred to v4.32.0+. The thread pool's existing
   `queue_lock` pattern is the precedent.
2. **TSan stress scope — minimum (4 tests).** One per fixed race.
   Full TSan re-audit is a v4.31.0+ process item.
3. **Signal write lock only, not read lock.** The panel called out the
   write side explicitly. The read side is a raw pointer return with
   separate API-shape consequences; closing it cleanly needs a
   copy-on-read or get/release API change that is bigger than a
   recovery-arc fix. Documented inline in the test file so the next
   review cycle knows the scope choice.
4. **Phase 1.4 expanded scope.** Beyond `mn_init_tag_strings`, the grep
   surfaced four other `if (init) ... init=1` sites. Fixed all of
   them in the same release because the panel had flagged Windows
   init races (Cobra #5) as propagating. Zero pattern instances
   remain.
5. **`__MN_VERSION__` placeholder is load-bearing.** A missing
   placeholder is now a build error. The alternative (silent fallback
   to literal "4.7.1" or similar) would recreate the original bug.
6. **Decision not to run full TSan audit.** PROMPT default and panel
   scope both say "stress the fixed races, not the whole runtime."
   Full runtime TSan-under-load is a v4.31.0+ process item.

## Verification Results

```bash
# Full lint
$ black --check .
268 files would be left unchanged.

$ ruff check .
All checks passed!

$ mypy mapanare/ runtime/
Success: no issues found in 50 source files
```

```bash
# Golden + stage2
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
All 46 tests passed in 3.7s

$ python3 scripts/ir_doctor.py stage2 --timeout 60
11/11 stage2 modules valid
```

```bash
# Binary prints the live VERSION
$ ./mapanare/self/mnc-stage1 version
mapanare 4.28.0
```

```bash
# Pytest (614 passing + 4 pre-existing xfail)
$ python3 -m pytest tests/self_hosted/ tests/bind/ tests/parser tests/semantic tests/diagnostics -q
614 passed, 4 xfailed, 1 warning in 11.14s
```

```bash
# TSan: signal set path
$ gcc -fsanitize=thread -g -O1 \
    tests/runtime/tsan/signal_stress.c runtime/native/mapanare_core.c \
    -I runtime/native -o /tmp/tsan_signal -lpthread -lm -ldl
$ /tmp/tsan_signal
signal_stress: 4 writer threads x 5000 iters complete, no TSan races
```

```bash
# TSan: agent inbox
$ gcc -fsanitize=thread -g -O1 -I runtime/native \
    tests/runtime/tsan/inbox_stress.c \
    runtime/native/mapanare_runtime.c runtime/native/mapanare_core.c \
    -o /tmp/tsan_inbox -lpthread -lm -ldl
$ /tmp/tsan_inbox
inbox_stress: 4 producers x 5000 msgs = 20000 received, no TSan races
```

```bash
# TSan: type registry
$ gcc -fsanitize=thread -g -O1 -I runtime/native \
    tests/runtime/tsan/type_registry_stress.c \
    runtime/native/mapanare_core.c \
    -o /tmp/tsan_typereg -lpthread -lm -ldl
$ /tmp/tsan_typereg
type_registry_stress: 4 writers + 4 readers x 2000 ops, no TSan races
```

```bash
# Matmul validation (on real RTX 4090)
$ gcc -g -O1 -I runtime/native \
    tests/runtime/tsan/matmul_validation.c \
    runtime/native/mapanare_gpu_builtins.c runtime/native/mapanare_gpu.c \
    runtime/native/mapanare_runtime.c runtime/native/mapanare_core.c \
    -o /tmp/matmul_validation -lpthread -lm -ldl
$ /tmp/matmul_validation
mapanare_gpu: CUDA initialized — NVIDIA GeForce RTX 4090 (24563 MB)
mapanare_gpu: Vulkan initialized — llvmpipe (LLVM 19.1.1, 256 bits)
PASS: a.len != m*k returns empty list
PASS: b.len != k*n returns empty list
PASS: m == 0 returns empty list
PASS: k == 0 returns empty list
PASS: overflow (m*k > INT64_MAX) returns empty list
PASS: NULL list pointers return empty list
PASS: valid dims reach matmul without NULL-deref
matmul_validation: all checks passed
```

```bash
# No more InterlockedCompareExchange in live code
$ grep -n InterlockedCompareExchange runtime/native/*.c | grep -v '\*.*v4.28.0\|swapped\|replaced\|canonical'
(empty)

# No TEXTREL in runtime archive
$ readelf -d runtime/native/libmapanare_rt.a | grep -c TEXTREL
0
```

## Exit Criteria Check

| # | Check | Status |
|---|-------|--------|
| 1 | Phase 0 forensics complete; FORENSICS.md written | ✅ |
| 2 | `__mn_signal_set` value mutation under lock; TSan stress test passes | ✅ |
| 3 | Agent inbox ring is MPSC-safe (lock or real MPSC); TSan passes | ✅ |
| 4 | Type registry uses rwlock; stress test passes | ✅ |
| 5 | `mn_init_tag_strings` uses `pthread_once`/`InitOnceExecuteOnce` | ✅ |
| 6 | matmul shape NULL check + regression test | ✅ |
| 7 | matmul dimension validation + regression test | ✅ |
| 8 | GPU temp file race fixed via `mkstemps`/`GetTempFileNameW` | ✅ |
| 9 | Windows GPU init race fixed at both sites with `InitOnceExecuteOnce` | ✅ |
| 10 | `main.mn` version string sourced from `VERSION` at build time | ✅ |
| 11 | `test_version_string` passes; not skipped or xfailed | ✅ (rewritten as 3 real tests) |
| 12 | Carry-forward audit document written and committed | ✅ |
| 13 | 46/46+ golden, 11/11 stage2 | ✅ |
| 14 | black/ruff/mypy clean | ✅ |
| 15 | TSan-clean for the new stress tests | ✅ |
| 16 | `docs/roadmap/v4/v4.28.0/SESSION_REPORT.md` written | ✅ (this file) |

## Next Session Should Start With

1. Re-read `docs/roadmap/v4/RECOVERY_MASTER_PROMPT.md` for the
   recovery-arc discipline.
2. Read `docs/roadmap/v4/v4.29.0/PLAN.md` (assuming it exists — if
   not, write it first). v4.29.0 scope from the audit:
   - Orphaned `mapanare_db.c`/`mapanare_html.c` — 1,942 lines — add
     to build rule, declare exports, smoke tests
   - `extern "Python" fn` — 79 silent xfails — decide: restore against
     LLVM emitter or delete and unskip
   - `verify_fixed_point.sh` — add `set -e`, remove `|| true`,
     propagate exit code in CI
   - `stage3.ll` zero-byte file — regenerate or delete
   - `--no-check` — add stderr warning
   - `NotImplementedError` CI gate
3. Known pre-existing LLVM test failures still in scope for later:
   - `tests/llvm/test_any_type.py::TestAnyArithmeticRejection::test_any_plus_any_error`
   - Three others noted in the recovery master prompt
4. Confirm the 46/46 baseline is still green before starting v4.29.0.
5. **Do not advance to v4.30.0 until the v4.29.0 exit criteria are all
   green.** Strict sequencing. If v4.29.0 misses an exit criterion,
   open v4.29.1 rather than rolling the deficit forward.
