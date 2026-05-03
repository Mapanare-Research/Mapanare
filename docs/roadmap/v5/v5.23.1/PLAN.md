# v5.23.1 — Mb.* — memory hygiene

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.23.0 shipped (RC.\* CI recovery + HIGH
closures). All 8 silent-CI-fail gates green.
**Estimated effort:** 1 session (~3–4 hours).
**Arc context:** Second release in the v5.23–v5.24 recovery
arc. See `docs/roadmap/v5/RECOVERY_ARC_v5.23-v5.24.md`.

---

## Why this exists

Three real memory bugs surfaced in the v5.22.0 panel + post-
panel CI analysis. None block correctness; all three are
production-discipline gaps that the v5.21.1 hygiene release
did not catch:

1. **V.9** (Viper, MEDIUM) —
   `__mn_indent_to_braces` MnString lifecycle leak. The
   returned `joined` buffer is not drop-glue tracked at the
   `parser.mn::parse` call site; missing tracked-output
   annotation on the `extern "C" fn` decl. Bounded to
   single-shot in `mnc-stage1` (OS reaps on exit) but
   **unbounded if the runtime is embedded in a long-lived
   process** (LSP server with re-parse, watch-mode compiler).
   151-byte leak per colon-syntax compile.

2. **Te.5 ASan leaks** (post-panel CI surface) — 3 NEW LEAK
   regressions on `tests/golden/{88_if_let,90_while_let,
   91_let_else}.mn` (1 leak / 8 bytes each). Almost certainly
   missing drop-glue site in the let-else / while-let / if-let
   desugaring at v5.20.0 in `mapanare/lower.py`. The Te.6
   chained-cmp goldens (95) are leak-clean per Viper, so this
   is Te.5-specific. **Viper missed this in v5.22.0 review;
   surface was the LeakSanitizer CI workflow, not Viper's
   manual valgrind.**

3. **V.6 / V.7 / V.8** (Viper, LOW, **3rd cycle each**) —
   DX.4 walker carries: unbounded recursion in `mn_dir_walk_*_`,
   Win32 reparse-point loop risk, no ASan/valgrind sweep on
   v5.10.0+ deltas. Cumulative −0.05 discipline drift across
   v5.7.1 / v5.11.0 / v5.22.0 panels. Each is a small fix; all
   close together at v5.23.1.

Plus mandatory **prevention infrastructure** (Mb.4) — a
valgrind regression CI gate so V.9-class lifecycle leaks
surface immediately. The byte-identical oracle in
`tests/bootstrap/test_indent_preprocessor.py` cannot detect
lifecycle issues; this gate would have caught V.9 at v5.14.1.

---

## Goals

1. Close V.9 at the lifecycle level (tracked-output
   annotation, not just symptom).
2. Close 3 Te.5 ASan leak regressions at the lower-time
   drop-glue site.
3. Close V.6 / V.7 / V.8 (3rd cycle each).
4. Install valgrind regression CI gate (Mb.4) so future
   lifecycle bugs surface in CI.
5. Strict 3-stage fixed point preserved at 238,086 lines /
   0 diff (Te.5 drop-glue addition does not change emitted
   IR shape — only adds `__mn_*_free` calls at existing
   tracking sites).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Mb.1** | MEDIUM | **V.9 — `__mn_indent_to_braces` MnString lifecycle leak.** Add the "tracked output string" annotation to the `extern "C" fn __mn_indent_to_braces(...) -> String` declaration in `mapanare/self/parser.mn`, mirroring `__mn_str_concat` / `__mn_str_from_cstr`. The lower pass will then emit `%str_track` allocas + drop-glue free at scope exit. Verify with `valgrind --leak-check=full mnc-stage1 emit-llvm <colon-syntax-golden>.mn`: the 151-byte-per-parse leak should disappear. Local fix at the `extern "C" fn` decl is ~1 line; `mapanare/self/semantic.mn::is_string_returning_builtin` may need an entry if name-table-driven. | 1-2h |
| **Mb.2** | MEDIUM | **Te.5 ASan leaks on goldens 88 / 90 / 91.** Investigate `mapanare/lower.py::_lower_let_else`, `_lower_while_let`, `_lower_if_let`. Each desugars to existing match/while/let machinery, but the synthesized intermediate temps (Te.5 patterns destructure `Some(x)` etc.) need to thread through the existing `%str_track` / `%list_track` / `%generic_track` machinery the same way Te.6's `__mn_chain_N` temps do. Verify with `bash scripts/run_asan_leak_goldens.sh` post-fix: the 3 NEW LEAK entries should disappear; the baseline should stay clean (or the v5.4.2 baseline updated if any prior LEAK is now CLEAN). **Update the v5.4.2 baseline TSV** at `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` to reflect any FIXED entries (the v5.21.1 ASan run shows 39_gpu_detect, 40_gpu_tensor, 62_list_output as IMPROVED — those baseline updates are also blocking the ASan gate from going green). | 2-3h |
| **Mb.3** | MEDIUM | **Mb.4 — valgrind regression CI gate.** New job `sanitizer-mnc-stage1` at `.github/workflows/sanitizers.yml`: build `mnc-stage1`, run `valgrind --leak-check=full --error-exitcode=1 mnc-stage1 emit-llvm tests/golden/<a-colon-syntax-golden>.mn -o /tmp/out.ll`. Fail the build on non-zero exit. **Mandatory follow-up to Mb.1** because the byte-identical oracle (`test_indent_preprocessor.py`) cannot detect lifecycle issues. Also exercises Mb.2's drop-glue paths — let-else / while-let / if-let goldens 88/90/91 should be in the corpus for this job. | 30 min |
| **Mb.4** | LOW | **V.6 — DX.4 walkers unbounded recursion.** Rewrite `mn_dir_walk_size_`, `mn_dir_walk_count_`, `mn_dir_remove_recursive_` as iterative work-queue walkers. ~30 LOC per walker; reuse `MnIB_LineList`-style dynamic arrays from `__mn_indent_to_braces` as a template. Cap queue depth at 4096 entries with a clean error path. **3rd cycle.** | 1h |
| **Mb.5** | LOW | **V.7 — Win32 walkers reparse-point skip.** In each of the three Win32 walker branches in `runtime/native/mapanare_core.c`, before recursing, check: `if (ffd.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) continue;` (or treat as a file). ~5 LOC × 3 sites = 15 LOC. **3rd cycle.** | 30 min |
| **Mb.6** | LOW | **V.8 — `sanitizer-cache-walkers` job at sanitizers.yml.** Build a populated cache directory fixture (3 levels deep, mixed files + subdirs + a non-loop symlink). Run `mnc cache stats` / `mnc cache clean` / `mnc --version` (exercises `__mn_executable_dir`) under valgrind `--leak-check=full --error-exitcode=1`. Block the release gate on non-zero exit. **3rd cycle. Closes the v5.10.0+ delta sanitizer-coverage gap.** | 1h |
| **Mb.7** | LOW | **ASan-gate llc aborts** — `scripts/run_asan_leak_goldens.sh` shows 5 `Aborted (core dumped)` from `llc -filetype=obj -relocation-model=pic` (8 LINK_FAILs). Pre-existing; investigate but defer if stable across baselines. May be related to ASan instrumentation conflicting with PIC reloc — try `-relocation-model=static` or omit. Don't block v5.23.1 closure on this; defer to v5.24.0+ if not trivial. | 1h or defer |

---

## Phase plan

### Phase 0 — pre-flight verification

```bash
# Baseline (must hold from v5.23.0)
bash scripts/verify_fixed_point.sh --keep
# expected: 238086 / 0 diff
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: 95/95
cat VERSION
# expected: 5.23.0

# Reproduce V.9 leak
echo 'fn main():\n    print("hi")' > /tmp/colon.mn
valgrind --leak-check=full --error-exitcode=1 \
  mapanare/self/mnc-stage1 emit-llvm /tmp/colon.mn -o /tmp/out.ll 2>&1 | tail -20
# expected: "151 bytes in 1 blocks are definitely lost" or similar from __mn_indent_to_braces

# Reproduce Te.5 ASan leaks
bash scripts/run_asan_leak_goldens.sh 2>&1 | tail -30
# expected: NEW LEAK on 88_if_let / 90_while_let / 91_let_else
```

If V.9 or Te.5 leaks don't reproduce locally, the GHA
sanitizers run is the ground truth.

### Phase 1 — Mb.1 V.9 lifecycle annotation

1. Open `mapanare/self/parser.mn`. Find the
   `extern "C" fn __mn_indent_to_braces(source: String) -> String`
   declaration.
2. Add tracked-output annotation. Look at how
   `__mn_str_concat` / `__mn_str_from_cstr` are declared — the
   pattern likely involves an attribute or a type-system
   marker the lower pass uses to emit `%str_track` allocas +
   drop-glue free at scope exit. Match that pattern verbatim.
3. If the predicate is name-table-driven, also add
   `__mn_indent_to_braces` to
   `mapanare/self/semantic.mn::is_string_returning_builtin`
   (or whatever the equivalent helper is).
4. Rebuild stage1: `python3 scripts/build_stage1.py`.
5. Re-run valgrind on the colon-syntax fixture: leak should
   be gone.
6. Run goldens: `python3 scripts/test_native.py --stage1
   mapanare/self/mnc-stage1`. Must be 95/95.
7. Verify fixed point: `bash scripts/verify_fixed_point.sh
   --keep`. The Mb.1 fix may grow stage2.ll by a small
   amount (extra `__mn_str_free` calls in `parse()` lower).
   Document the new line count.

### Phase 2 — Mb.2 Te.5 ASan leak fix

1. Run `bash scripts/run_asan_leak_goldens.sh 2>&1 | tail -50`
   to confirm the 3 NEW LEAK entries.
2. Read `mapanare/lower.py::_lower_let_else`,
   `_lower_while_let`, `_lower_if_let`.
3. Compare to `_lower_match` (the canonical reference) and
   `_lower_chained_compare` (the v5.21.0 version that's
   leak-clean per Viper). Identify the missing drop-glue
   site for the synthesized destructure pattern temps
   (likely an `Identifier` extracted from a `Some(x)` /
   `Ok(x)` pattern that doesn't get tracked when the binding
   site is in the synthesized match arm).
4. Add the missing tracking. Mirror the v5.21.0 chain-temp
   discipline: bind via `let`, mark in tracking machinery,
   ensure drop-glue runs at scope exit.
5. Rebuild stage1; re-run goldens (88/90/91 must still PASS
   on the Python bootstrap; should now ALSO ASan-clean).
6. Re-run `bash scripts/run_asan_leak_goldens.sh`: 3 NEW LEAK
   entries should be gone.
7. **Baseline TSV refresh**: the v5.21.1 ASan run shows
   FIXED on `39_gpu_detect`, `40_gpu_tensor` and IMPROVED on
   `62_list_output`. Update `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`
   to remove the FIXED entries and update the IMPROVED count.
   Document each baseline update in SESSION_REPORT.

### Phase 3 — Mb.3 valgrind regression CI gate

1. Open `.github/workflows/sanitizers.yml`. Add new job
   `sanitizer-mnc-stage1` after the existing LeakSanitizer
   job:

   ```yaml
   sanitizer-mnc-stage1:
     name: Valgrind on mnc-stage1 (lifecycle leak gate)
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: "3.12"
       - name: Install LLVM + valgrind
         run: |
           sudo apt-get update
           sudo apt-get install -y llvm-18 clang-18 valgrind
       - name: Build mnc-stage1
         run: python3 scripts/build_stage1.py
       - name: Build runtime
         run: |
           cd runtime/native
           gcc -c -fPIC -O0 -g mapanare_core.c -o mapanare_core.o
           ar rcs libmapanare_rt.a mapanare_core.o
       - name: Valgrind on colon-syntax golden
         run: |
           valgrind --leak-check=full --error-exitcode=1 --track-origins=yes \
             mapanare/self/mnc-stage1 emit-llvm tests/golden/86_let_destructure_rest.mn -o /tmp/out.ll
       - name: Valgrind on Te.5 if-let golden
         run: |
           valgrind --leak-check=full --error-exitcode=1 --track-origins=yes \
             mapanare/self/mnc-stage1 emit-llvm tests/golden/88_if_let.mn -o /tmp/out.ll
       - name: Valgrind on Te.5 while-let golden
         run: |
           valgrind --leak-check=full --error-exitcode=1 --track-origins=yes \
             mapanare/self/mnc-stage1 emit-llvm tests/golden/90_while_let.mn -o /tmp/out.ll
       - name: Valgrind on Te.5 let-else golden
         run: |
           valgrind --leak-check=full --error-exitcode=1 --track-origins=yes \
             mapanare/self/mnc-stage1 emit-llvm tests/golden/91_let_else.mn -o /tmp/out.ll
   ```

2. Push to a test branch; verify the job runs green at v5.23.1
   HEAD (post-Mb.1 + post-Mb.2).
3. Verify the job WOULD have failed at v5.22.0 HEAD by
   running locally before the Mb.1 + Mb.2 fixes.

### Phase 4 — Mb.4 / Mb.5 / Mb.6 (V.6 / V.7 / V.8 closures)

1. **Mb.4 (V.6)** — open
   `runtime/native/mapanare_core.c`. Find `mn_dir_walk_size_`,
   `mn_dir_walk_count_`, `mn_dir_remove_recursive_`. Rewrite
   each as iterative work-queue:
   - Replace direct recursion with a while-loop popping
     `WalkEntry { path, depth }` from a queue.
   - Cap queue depth at 4096; on overflow, set an error and
     exit the loop with a clean failure path.
   - Reuse `MnIB_LineList`-style dynamic-array helpers from
     the indent preprocessor.
2. **Mb.5 (V.7)** — in each Win32 walker branch (3 sites in
   `mapanare_core.c`), add reparse-point skip:
   ```c
   if (ffd.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) continue;
   ```
   before each recursive (or now iterative) descent step.
3. **Mb.6 (V.8)** — new job `sanitizer-cache-walkers` at
   `.github/workflows/sanitizers.yml`:
   ```yaml
   sanitizer-cache-walkers:
     name: Valgrind on mnc cache walkers
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: "3.12"
       - name: Install valgrind + LLVM
         run: sudo apt-get install -y valgrind llvm-18 clang-18
       - name: Build native mnc
         run: bash scripts/build_from_seed.sh
       - name: Populate cache fixture
         run: |
           mkdir -p /tmp/cache-fixture/level1/level2
           touch /tmp/cache-fixture/file1.bin
           touch /tmp/cache-fixture/level1/file2.bin
           touch /tmp/cache-fixture/level1/level2/file3.bin
           ln -s /tmp/cache-fixture/level1 /tmp/cache-fixture/non-loop-symlink
           export MAPANARE_CACHE_DIR=/tmp/cache-fixture
       - name: Valgrind on cache stats
         run: valgrind --leak-check=full --error-exitcode=1 ./mnc cache stats
       - name: Valgrind on cache clean
         run: valgrind --leak-check=full --error-exitcode=1 ./mnc cache clean
       - name: Valgrind on --version
         run: valgrind --leak-check=full --error-exitcode=1 ./mnc --version
   ```

### Phase 5 — Mb.7 ASan-gate llc aborts (defer if not trivial)

1. Run `bash scripts/run_asan_leak_goldens.sh 2>&1 | grep "Aborted" | head -5`.
2. Pick one failing golden; reproduce manually:
   ```bash
   python3 -m mapanare emit-llvm tests/golden/<failing>.mn -o /tmp/test.ll
   llc -filetype=obj -relocation-model=pic /tmp/test.ll -o /tmp/test.o
   ```
3. If the abort is triggered by ASan-instrumented PIC reloc:
   - Try `-relocation-model=static` in the script.
   - Or skip llc-failed entries from the gate.
4. **If non-trivial**, defer to v5.24.0 with a docket entry
   noting "ASan-gate llc aborts; pre-existing; investigation
   deferred."

### Phase 6 — closeout

1. SESSION_REPORT.md.
2. CHANGELOG `## [5.23.1]` entry.
3. CLAUDE.md release note.
4. Bump VERSION 5.23.0 → 5.23.1.
5. `python3 scripts/bump_version.py 5.23.1` sweep.
6. CRLF restoration on README + CHANGELOG + CLAUDE.md.
7. CARRY_FORWARD.md update.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Mb.1 lifecycle annotation pattern doesn't exist in `mapanare/self/parser.mn` for other extern fns | LOW | The pattern is implemented for `__mn_str_concat` etc. in v5.16.0 string-interp parity; if the annotation is in `mapanare/self/semantic.mn` rather than at the decl, follow that path |
| Mb.2 Te.5 drop-glue fix changes IR observable | LOW | The fix is drop-glue addition only — emits `__mn_*_free` calls at existing tracking sites. Goldens 88/90/91 stdout stays identical. Verify by `diff <(stage1 emit-llvm 88) <(stage1-fixed emit-llvm 88) | head -20` — expect only `__mn_*_free` insertions |
| Mb.1 fix grows stage2.ll meaningfully | MEDIUM | Each colon-syntax site adds 1-2 IR lines (track + free); mnc_all.mn parses many files but has only one parse() entry, so growth is bounded. Document new line count in SESSION_REPORT |
| Mb.4/5/6 (V.6/V.7/V.8) Windows-side changes break the Windows CI lane | LOW | The Win32 paths are exercised by smoke tests; the iterative-walker rewrite is straightforward; the reparse-point skip is a 1-line check before the existing recursion call |
| Mb.7 ASan-gate llc aborts surface a real bug | MEDIUM | Defer if not trivial; document in SESSION_REPORT as "tracked v5.24.0 follow-up." Don't block v5.23.1 |
| Bb.\* seed refresh required | HIGH if Mb.1 grows mnc_all.mn meaningfully | Mb.1 modifies `mapanare/self/parser.mn` (extern decl annotation); this likely does NOT change the bootstrap seed binary's compile of stage1, since the annotation is consumed by lowering, not parsing. Test by running `bash scripts/build_from_seed.sh` post-Mb.1; if it fails, refresh the seed |

---

## Success criteria

- [ ] V.9 leak fixed at the lifecycle level (verified by valgrind)
- [ ] Te.5 leaks fixed (88/90/91 ASan-clean)
- [ ] V.6 / V.7 / V.8 closed (3rd cycle each)
- [ ] `sanitizer-mnc-stage1` CI job green
- [ ] `sanitizer-cache-walkers` CI job green
- [ ] LeakSanitizer baseline updated for FIXED / IMPROVED entries
- [ ] Goldens 95/95 preserved
- [ ] Strict 3-stage fixed point preserved (or new fixed point at slight line growth from Mb.1 — documented)
- [ ] `make lint` clean
- [ ] CARRY_FORWARD.md updated
- [ ] SESSION_REPORT.md written
- [ ] CHANGELOG `## [5.23.1]` entry
- [ ] CLAUDE.md release note
- [ ] VERSION bumped 5.23.0 → 5.23.1

---

## Out of scope (explicitly held)

- **Te.3 hollow-surface** (single-line shape + native mirror).
  v5.23.2.
- **`make ci-gates` / `check_doc_freshness.py` / cadence enforcement.**
  v5.24.0.
- **Manifesto M2 / SPEC corpus M3 / Coral L1–L5.** v5.24.1.
- **v6.0 carries** (Rt.04 multi-level alias, etc.).

---

## What this release CANNOT do

- Touch the Te.3 deprecation surface in any way (single-line
  shape, native mirror — both v5.23.2).
- Change emitted IR shape (drop glue addition only — Mb.1 +
  Mb.2 add `__mn_*_free` calls; do NOT add new MIR ops or
  IR shapes).
- Bypass the panel docket — every Mb.\* item must land or
  defer-with-tracking, no silent skips.
