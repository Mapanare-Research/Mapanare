# Memory ownership work log

## Resume point — 2026-10-08

Borrowed map views now participate in the Python loop-result lifetime proof,
committed as **`c81dfb64`** (`Track borrowed map views before recycling loop results`).
Local cursors and String key/value reads permit recycling only when all derived
aliases are dead; copied scalar results may survive independently. Retained
views, unknown consumers and mixed origins still reject recycling. See
[MAP_BORROWED_VIEWS.md](MAP_BORROWED_VIEWS.md) for the contract and next boundary.

The tests also exposed packed-key alignment UB. Its separate fix is committed
as **`ace5c43a`** (`Read packed map keys without alignment assumptions`); see
[PACKED_MAP_KEYS.md](PACKED_MAP_KEYS.md). Hash/equality/deep cleanup use aligned
local copies without changing the map layout or ABI.

Evidence: `build/memory-ownership/map-borrowed-views/`.

- `baseline-tests.log`: all 32 borrowed-view leak cases fail with the previous
  proof and corrected runtime, isolating the ownership change.
- `candidate-tests.log`: 95 passed (40 executions, 32 new proof cases and 23
  existing proof cases). Six subsequent branch-liveness controls pass in the
  broad suite below.
- `runtime-baseline.log`: both packed-key tests fail on the previous runtime.
- `runtime-tests.log`: 33 passed, including both packed-key cases and 31 owned-map
  lifecycle/policy controls.
- `llvm-mir-tests.log`: 1,214 passed, including all 38 new MIR proof controls.
- `ownership-regressions.log`: 240 passed, including 32 new leak-checked runs and
  eight retained-view invalid-access guards. Those eight guards intentionally
  disable leak detection because retained ownership remains open.
- `fixed-point.log`, `build/fixed-point-yip0m8ol`: both generations pass 104 LLVM
  goldens and nine required outputs; stage2/stage3 IR is byte-identical. Native
  source and emitted IR hashes are unchanged. The corrected runtime changes
  the archive and linked successor hashes.

GitNexus reports HIGH impact for the recycling proof: one direct caller, four
reachable indexed symbols, zero indexed processes. The warning was reported
before editing. The new helper is unindexed until refresh; its one direct
caller and all recognized/rejected consumers were reviewed manually. Runtime
helpers have LOW indexed impact; generated calls/function-pointer dispatch were
checked through sanitizer executions. The initial candidate failures exposed
the alignment bug; all affected cases pass with that correction.

Staged detection reports four expected runtime files with LOW risk, then eight
expected ownership/documentation files with LOW risk (`runtime-precommit.log`,
`precommit.log`). Some indexed ranges drift across added lines, so the exact
diffs and new symbols were reviewed directly. Black/Ruff and whitespace checks
pass. All verification processes have finished.

The exact tested successor is installed at `mapanare/self/mnc-stage1`, with its
previous binary preserved under the evidence directory as `previous-mnc-stage1`.
`verification.json` ties the committed source to the successful gate and hashes:

| Artifact | SHA-256 |
| --- | --- |
| Installed compiler | `5eeaa3ecee02868fbc7530eba7dff33374c6f34dfac1d9d2a26fb904fd4dc41d` |
| Runtime archive | `b6374c61abf9e7630b7efc1d80cb5008421b5975f82d82c52558d2f24a386db9` |
| Concatenated native source | `a79a01a72ccc2734fcefaa50767f5b187891732e8ef94bb94601e8d7302fd4ba` |
| Stage2 and stage3 IR | `62728337381f7e1c1ff3d5ffd59067f7345a6a9f5a5106a55784ff0efbaa73cb` |

**Next:** continue retained aliases, multiple allocation origins and general
transfer/retain/clone semantics. Nested element ownership and native adoption
remain open. Priority 2 stays active; nothing pushed.

```bash
.venv/bin/python -m pytest tests/mir/test_map_borrowed_liveness.py tests/integration/test_map_borrowed_views.py tests/native/test_packed_map_keys.py -q
```

## Previous verified milestone — loop map owners

The Python loop-result fix is committed as **`8f494554`**
(`Reclaim loop map results when prior aliases are dead`) for proven nonescaping factory results.
Liveness and a single-origin alias proof select allocation sites; private owner
slots survive Copy bookkeeping and release previous results only when no alias
can still be used. Retained/captured/uncertain aliases keep the old behavior.
See [MAP_LOOP_OWNERS.md](MAP_LOOP_OWNERS.md) for the exact scope and next boundary.

Evidence: `build/memory-ownership/map-loop-owners/`.

- `baseline-tests.log`: all 32 new leak cases fail on the committed emitter.
  The original fixture reproduces 535,464 bytes / 1,998 allocations retained.
- `final-tests.log`: 57 passed (32 leak-checked executions, four retained-alias
  invalid-access guards, and 21 MIR proof cases).
- `proof-final.log`: 23 proof cases pass, including two later single-origin
  branch-liveness controls. The initial candidate test expected an unused capture
  to survive optimization; its corrected fixture keeps that capture live.
- `llvm-mir-tests.log`: 1,174 passed. The two later branch controls are covered
  by `proof-final.log`.
- `ownership-regressions.log`: 200 passed, including all previous focused checks.
- `fixed-point.log`, `build/fixed-point-8ht_8407`: both generations pass 104 LLVM
  goldens and nine required outputs; stage2/stage3 IR is byte-identical. The
  compiler source, runtime, successor and IR hashes match the previous gate.

GitNexus marks function emission CRITICAL (one direct caller, five affected
flows, nine reachable symbols); this was reported before editing. Call dispatch
has LOW indexed impact. The new analysis was reviewed directly and tested with
both positive and conservative controls. No runtime or native source changed.
The installed compiler/runtime remain at the previously verified hashes.
Staged detection (`precommit.log`) reports ten expected files, ten indexed symbols
and five emitter flows, with MEDIUM risk. New analysis and tests were also
reviewed directly. `verification.json` records the committed revision and hashes.
No native binary replacement was necessary. Black/Ruff and whitespace checks
pass, and all verification processes are finished.

**Next:** extend ownership beyond the closed alias groups proven here: retained
aliases, multiple allocation origins and borrowed map views need explicit
transfer/retain/clone rules or stronger lifetime proofs. Keep the retained-alias
guard passing before enabling broader recycling. Nested element ownership and
native adoption remain open. Priority 2 stays active; nothing pushed.

```bash
.venv/bin/python -m pytest tests/mir/test_map_liveness.py tests/integration/test_map_loop_ownership.py -q
```

## Previous verified milestone — direct map returns

The direct Python map-return fix is committed as **`18c73cda`**
(`Preserve direct map returns and track proven owned results`). Returned map
handles survive callee cleanup; callers clean up results only from conservatively
proven factories. Borrowed results are not newly treated as owners. See
[MAP_RETURNS.md](MAP_RETURNS.md) for the proof, tests, and remaining boundaries.

Evidence under `build/memory-ownership/map-returns/`:

- `baseline-tests.log`: 20 sanitizer failures and eight passing controls against
  the committed baseline emitter.
- `candidate-tests.log`: 37 initial checks pass.
- `final-return-tests.log`: 41 passed (28 executable ASan/UBSan/LSan cases and
  thirteen proof controls after tightening capture and recursion limits).
- `llvm-mir-tests.log`: 1,151 passed; the two subsequently added proof-boundary
  tests are included in the final 41-check run.
- `ownership-regressions.log`: 164 passed, including prior iterator, borrowing,
  inlining, lifetime, generic, output and stack controls.
- `loop-probe.log`, `loop-leak.log`: repeated factory calls within one function
  leak 535,464 bytes / 1,998 allocations at 1,000 iterations. The durable next
  reproducer is `tests/native/fixtures/map_return_loop_lifetime.mn`.
- `fixed-point.log`, `build/fixed-point-n45ogd72`: both generations pass 104 LLVM
  goldens and nine executable outputs, with byte-identical stage2/stage3 IR.
  Source, runtime, successor and IR hashes match the previous verified gate.

GitNexus marks the module `emit` entry point CRITICAL (two direct callers, five
affected flows, thirteen reachable symbols); this was reported before editing.
Cleanup/dispatch paths have LOW indexed impact. The new ownership summary is
unindexed until refresh, so its direct caller and conservative cases were checked
manually. Black/Ruff and whitespace checks pass. No native compiler or runtime
code changed, and the installed compiler remains the verified `81da982a...`
binary from the previous milestone.
Staged detection (`precommit.log`) found eleven expected files, thirteen indexed
symbols and five emitter execution flows, with MEDIUM risk. New proof/test files
were reviewed directly. `verification.json` records the committed checkpoint;
the installed compiler and runtime match the successful fixed-point manifest.
No binary replacement was necessary. All verification processes have finished.

**Next:** establish branch-sensitive map owner slots and transfer/retain rules,
then fix the recorded map-result replacement leak without freeing live aliases.
Keep borrowed and mixed returns conservative. Continue nested/element ownership
and both-emitter adoption afterward. Priority 2 remains active; nothing pushed.

```bash
.venv/bin/python -m pytest tests/mir/test_map_ownership.py tests/integration/test_map_return_ownership.py -q
```

## Previous verified milestone — bootstrap iterators

The Python bootstrap iterator follow-up is committed as **`970bc93c`**
(`Fix bootstrap range and map iterator lifetimes`). All
six expected failures from the native loop-control milestone now pass; their
markers are removed. Inclusive ranges link and include `INT64_MAX` without
overflow. Map loops create one cursor per loop entry, retain the correct key
type, and release private cursors on normal exit, break, and early return.
Nested and repeated loops over one map keep independent cursors. See
[the loop-control notes](../compiler-correctness/LOOP_CONTROL.md).

Evidence: `build/memory-ownership/bootstrap-iteration/`.

- `type-fix-tests.log`: 36 loop-control checks pass, including all six former
  expected bootstrap failures.
- `iterator-runtime-final.log`: 128 passed. Includes 20 new O0–O3 ASan/LSan
  executable cases, two range probes covering twelve boundary cases against
  instrumented source and the optimized runtime, and existing container controls.
- `llvm-mir-tests.log`: 1,140 passed, using the previously installed native
  compiler and the updated runtime for native link checks.
- `successor-link-tests.log`: 105 passed (104 golden programs plus corpus count)
  against the exact optimized successor.
- `successor-regressions.log`: 136 passed, including the previous focused
  ownership/control checks and the new bootstrap iterator cases.
- `source-tests.log`: 253 passed, two existing expected failures.
- `fixed-point.log`, `build/fixed-point-uvraczp_`: both generations pass 104 LLVM
  goldens and nine required executable outputs; stage2/stage3 are byte-identical.
- `map-return-comparison.log`, `map-return-{baseline,current}.log`: a separate
  map-return use-after-free reproduces on both emitters. The durable fixture is
  `tests/native/fixtures/map_return_lifetime.mn` (expected output `3`). No loop is
  needed: `_emit_drop_glue_maps` frees returned maps, and caller result ownership
  also needs explicit tracking. This is the next concrete ownership checkpoint.

GitNexus reports LOW impact for iterator lowering, emitter dispatch, return
cleanup, and the runtime range functions. Map literal type propagation has
MEDIUM indexed impact: one direct caller, one process, 41 reachable symbols.
Generated runtime calls and dynamic emitter dispatch are incompletely indexed,
so executable and sanitizer checks supplement the graph. No native compiler
source or public container ownership contract changed.
Staged detection (`precommit.log`) reports twelve expected files, 22 indexed
symbols, five emitter execution flows, and MEDIUM risk. Some neighboring symbol
names reflect index line-range drift; the staged diff contains only the intended
iterator and map-type edits, tests, and documentation. New helpers/fixtures were
also reviewed directly.

Gate SHA256 hashes:

- Compiler source: `a79a01a72ccc2734fcefaa50767f5b187891732e8ef94bb94601e8d7302fd4ba`.
- Optimized successor: `81da982abfb246d3bc0cb541480a389d1a0613c941c69558f950642a0adaba85`.
- Both IR stages: `62728337381f7e1c1ff3d5ffd59067f7345a6a9f5a5106a55784ff0efbaa73cb`.
- Runtime: `b8397083a5f92603487d674f31b00bd00723a64723b92e3a87958cdda9a2b28a`.

The prior verified compiler/runtime are preserved as `mnc-baseline` and
`runtime-baseline.a` in the evidence directory. Promotion at `970bc93c`
regenerated compiler source and rebuilt the runtime, matching both gate hashes.
The exact tested optimized successor is installed at `mapanare/self/mnc-stage1`;
`promotion.json` records its source revision and prior/current hashes. All
builds and checks are finished. Toolchain: Linux/WSL, Clang/LLVM 18.1.3,
Python 3.12.3. Black/Ruff and whitespace checks pass.

Rerun from Linux/WSL:

```bash
.venv/bin/python -m pytest tests/integration/test_native_for_continue.py tests/integration/test_bootstrap_iterators.py tests/native/test_range_iterators.py -q
.venv/bin/python scripts/verify_fixed_point.py --stage1 mapanare/self/mnc-stage1 --keep
```

**Next:** fix returned-map transfer and caller ownership first, using the saved
ASan reproducer. Then continue handle retain/clone/transfer, copy-in insertion,
and borrowed lookup lifetimes in both emitters. Raw-container leaks remain open;
owned runtime constructors stay opt-in. Priority 2 remains active. Nothing pushed.

## Previous verified milestone — native loop control

Native range-loop `continue` and map-loop control are committed as **`8c341089`**
(`Fix native for-loop continue progress and map control targets`) in `lower_for` and
`lower_for_map`. Both bind the current visible value, then advance the hidden
counter before user control flow. Map loops also install and restore their own
break/continue targets. This preserves block layout and avoids a state-layout or
runtime change. See [the loop-control notes](../compiler-correctness/LOOP_CONTROL.md).

Evidence is under `build/memory-ownership/range-continue/`:

- `baseline-tests.log`: 16 of 18 native cases fail against the preserved compiler;
  the empty-range controls pass. Six additional failures are unchanged Python
  bootstrap bugs; twelve other Python controls pass.
- `candidate-tests.log`: all 18 native and twelve Python controls pass. The six
  bootstrap failures remain and are now strict expected failures with specific
  exception types. The tests cover O0/O2 execution, bounds, nested range/map/while
  loops, unconditional continue, break and early return, with a three-second
  execution timeout.
- `fixed-point.log`, `build/fixed-point-v1axkv58`: both generations pass **104 LLVM
  goldens and nine executable fixtures**; stage2/stage3 are byte-identical. The
  new `104_for_continue` golden must execute successfully on both generations.
- `source-tests.log`: 253 passed, two pre-existing expected xfails.
- `llvm-mir-final.log`: 1,140 passed. The link harness uses the optimized
  successor; the earlier run used the preserved installed compiler and exposed
  the new regression plus the outdated 103-corpus count.
- `successor-regressions.log`: 110 passed, six strict expected bootstrap failures.
  This includes the prior 80 focused checks. Black/Ruff and whitespace checks pass.

GitNexus returned UNKNOWN for both native lowerers (unindexed language). Manual
tracing identified `lower_stmt -> lower_for -> lower_for_map`; this affects all
native for loops and self-hosting, so HIGH risk was reported before editing.
The golden-count test has LOW impact, with zero callers/processes. Its expected
count now matches the current corpus, and the link harness accepts
`MAPANARE_TEST_COMPILER` so a candidate can be validated without replacing the
installed compiler. Historical release reports keep their original denominators.
Staged detection (`precommit.log`) found nine expected files, three indexed
symbols, no indexed processes and LOW risk. Native edits and new tests/goldens
were reviewed manually because the graph does not cover those additions yet.

Verified SHA256 hashes:

- Compiler source: `a79a01a72ccc2734fcefaa50767f5b187891732e8ef94bb94601e8d7302fd4ba`.
- Optimized successor: `d3e50fce00fd4161c10043aae9cd6ba7803aba8651dfa1b9feb09cc0f477b789`.
- Both IR stages: `62728337381f7e1c1ff3d5ffd59067f7345a6a9f5a5106a55784ff0efbaa73cb`.
- Unchanged runtime: `6d857dd5c21b7e159afc8b1efedc4511c28ae1fe5abb6997890da02e77f9a185`.

Promotion regenerated source and rebuilt the runtime at `8c341089`, matching
the gate hashes. The exact tested optimized successor is installed at
`mapanare/self/mnc-stage1`. The prior verified pair remains in the evidence
directory as `mnc-baseline` and `runtime-baseline.a`; `promotion.json` records the
replacement. All builds/checks are finished. Toolchain: Linux/WSL, Clang/LLVM
18.1.3, Python 3.12.3.

Rerun from the repository root in Linux/WSL:

```bash
.venv/bin/python -m pytest tests/integration/test_native_for_continue.py -q -rx
.venv/bin/python scripts/verify_fixed_point.py --stage1 mapanare/self/mnc-stage1 --keep
```

**Next:** fix the Python bootstrap's inclusive-range linking and nested map/range
iteration before container ownership integration. The exact reproductions and
strict expected-failure markers are in `test_native_for_continue.py`: `golden`
fails to link `__mn_range_inclusive`; `map-in-for` and `for-in-map` time out at
both optimization levels. These failed before this native change too. Remove
each marker once its regression passes. Then resume handle retain/clone/transfer,
copy-in insertion and borrowed lookup lifetimes in lowering and both emitters.
Priority 2 remains active; raw-container leaks remain open. Nothing pushed/released.

## Previous verified milestone — inlining cleanup

The inlining cleanup fix is committed as **`b280a29f`** (`Preserve cleanup
boundaries during MIR inlining`) in both optimizers. Resource-bearing
callees keep their original call boundary, and resource operations after a call
prevent a block split that would discard the caller's loop-body metadata.
Scalar arithmetic still inlines. Unsupported operations and unknown types fail
closed. See [ARGUMENT_BORROWING.md](ARGUMENT_BORROWING.md) for the restrictions.
No runtime API or MIR layout changed; owned containers remain opt-in.

Evidence is under `build/memory-ownership/inlining-lifetimes/`:

- The original combined fixture retained 92,285 bytes / 2,869 allocations before
  this fix. A second caller-allocation case retained 3,488 bytes / 872 allocations
  (`caller-baseline.log`). Both now pass at Python O2/O3.
- `candidate-inline-tests.log`: 22 checks pass, including String-only, list-only,
  combined, forward-wrapper and caller-allocation cases on both compilers, plus
  a native scalar-inlining control. All 21 executable cases use ASan/LSan.
- `llvm-mir-tests.log`: 1,137 passed, including 49 optimizer checks.
- `source-tests.log`: 253 passed, two existing expected xfails.
- `fixed-point-final.log`, `build/fixed-point-nsh_77x0`: both generations pass
  103 LLVM goldens and eight executable fixtures; stage2/stage3 are byte-identical.
  The initial gate (`fixed-point.log`, `build/fixed-point-8igqvfv9`) exposed the
  range-continue bug described below; the final proof avoids that construct.
  No emitted IR was patched.
- `successor-regressions.log`: all 80 focused checks pass on the optimized
  successor, including 22 new inlining checks and 58 prior ownership, generics,
  output and loop-stack controls. Black/Ruff and whitespace checks pass.

GitNexus impact for `_should_inline` was LOW (one direct caller, three affected
symbols). Caller-suffix protection also changes `inline_small_functions`, whose
impact was CRITICAL: one direct caller, ten affected symbols and eleven execution
flows. This was reported before editing. Native `.mn` symbols and new helpers
were unindexed; manual review traced them through the full optimization pipeline.
Staged detection (`precommit.log`) found eight expected files, thirteen indexed
symbols and no indexed processes (LOW). It also reported neighboring symbols
shifted by the additions; manual diff review confirmed their bodies are unchanged.

Verified SHA256 hashes:

- Compiler source: `7ac6f42f1f10d1dbfa6ddf65471f9db5383c2268a9a12b21d0aacd4e4278ca33`.
- Optimized successor: `3980c1f4d157a64a252007217d3b2e7f44e06574bd8fde37cf8f88a7a264203f`.
- Both IR stages: `a50482c1d226948e668a1dbf98d76a1dac2d3ba0027df0f1066e1b610a4cc2ca`.
- Unchanged runtime: `6d857dd5c21b7e159afc8b1efedc4511c28ae1fe5abb6997890da02e77f9a185`.

Promotion regenerated compiler source and rebuilt the runtime at `b280a29f`;
both match the strict gate. The exact tested optimized successor is installed at
`mapanare/self/mnc-stage1`. The previous compiler/runtime are preserved as
`mnc-baseline` and `runtime-baseline.a` in the evidence directory; promotion is
recorded in `promotion.json`. All checks and builds are finished. Toolchain:
Linux/WSL, Clang/LLVM 18.1.3, Python 3.12.3.

Rerun from the repository root in Linux/WSL:

```bash
.venv/bin/python -m pytest tests/mir_opt \
  tests/integration/test_inlined_resource_lifetime.py -q
.venv/bin/python scripts/verify_fixed_point.py --stage1 mapanare/self/mnc-stage1 --keep
```

**Next:** fix native range-loop `continue` lowering, then resume compiler adoption
of owned containers. This existing bug was exposed while building the proof:
`continue` branches to the range header without incrementing its counter.
`tests/native/fixtures/range_continue_progress.mn` expects `8`, but the unchanged
installed compiler's output, linked at Clang O0, times out (exit 124 after three
seconds; `range-continue.log`). At O1 the same program exits without output.
The existing golden 33 exercises while-continue and for-break, not for-continue.
The new proof avoids this construct. Add an executable timeout regression when
fixing lowering; do not treat LLVM-valid IR alone as evidence of loop progress.

After that, coordinate container handle retain/clone/transfer, copy-in insertion
markers, returned/captured aliases and borrowed lookup lifetimes in lowering and
both emitters. Existing native container leaks remain open. Priority 2 remains
active. Nothing pushed or released.

## Previous verified milestone — read-only argument borrowing

Read-only argument borrowing is committed as **`c3538bd0`** (`Preserve caller
ownership for proven read-only list calls`) in both LLVM emitters. Python now
suppresses automatic argument moves only for a proven borrowing body; native
String borrowing now permits read-only list parameters, aliases and indexing.
Both register summaries before body emission, covering forward calls. Mutators,
captures, unknown calls and resource-bearing returns remain conservative. See
[ARGUMENT_BORROWING.md](ARGUMENT_BORROWING.md) for the precise whitelist and
remaining integration requirements. Owned runtime constructors are not activated.

Evidence under `build/memory-ownership/container-handles/`:

- `baseline-final-cases.log`: ten of 16 leak checks fail against the preserved
  compilers; six controls pass. Native list-argument cases retain 8,890 bytes
  over 1,000 calls. The final fixtures preserve the allocating call boundary.
- `bootstrap-probes.log`: 20 proof checks and eight Python executable cases pass.
- `candidate-probes.log`: all eight native executable cases pass.
- `capture-tests.log`: both invalid-access capture controls pass. Leak detection
  is intentionally disabled only in those controls because legacy returned lists
  still retain their elements; the 16 borrowing cases use LeakSanitizer.
- `llvm-mir-tests.log`: 1,088 passed.
- `source-tests.log`: 253 passed, two expected xfails.
- `fixed-point.log`, `build/fixed-point-r_9qtc2m`: 103 LLVM goldens and eight
  executable fixtures pass on both generations; stage2/stage3 IR is identical.
- `successor-regressions.log`: all 58 checks pass on the optimized successor,
  including the 18 new executable cases and 40 prior native controls.

Verified hashes (SHA256):

- Compiler source: `9b3bee6a98aad73f05655c584a88735788bb260d0fe71d99bb75e7d3e636e4dd`.
- Optimized successor: `3c2b89b4d6ab5336857f0aa82cbf89093f9c71fe9216956339ff3039b791f4bb`.
- Both IR stages: `4627c305beb12f4ac7b0aac758beda3375ac0a1f301fe3ab388b7a35982a93bf`.
- Unchanged runtime archive: `6d857dd5c21b7e159afc8b1efedc4511c28ae1fe5abb6997890da02e77f9a185`.

The prior compiler/runtime pair is preserved as `mnc-baseline` and
`runtime-baseline.a` in this evidence directory. Promotion regenerated compiler
source and rebuilt the runtime at `c3538bd0`; both match the gate hashes. The
exact tested successor is installed at `mapanare/self/mnc-stage1`. The record is
`build/memory-ownership/container-handles/promotion.json`. All validation/builds
are finished. Toolchain: Linux/WSL, Clang/LLVM 18.1.3, Python 3.12.3.

GitNexus reports CRITICAL for Python `emit`: two direct callers, 13 affected
symbols and five process groups across CLI builds/emission and IR diagnostics.
This warning was reported before editing. `_do_call` reports LOW with no indexed
callers; native `.mn` helpers and new Python helpers are outside the index and
were manually traced. Full LLVM/MIR and strict self-hosting checks cover the
broader risk. No MIR layout or runtime API changed in this milestone.
Staged detection (`container-handles/precommit.log`) found eleven expected files,
nine indexed symbols and five affected call-emission flows, MEDIUM risk.
Manual review also covered the unindexed native helpers and new proof/tests.

Rerun the new checks from the repository root in Linux/WSL:

```bash
.venv/bin/python -m pytest tests/llvm/test_argument_borrow_proof.py \
  tests/integration/test_container_argument_borrow.py \
  tests/integration/test_container_capture_lifetime.py -q
.venv/bin/python scripts/verify_fixed_point.py --stage1 mapanare/self/mnc-stage1 --keep
```

**Next:** fix the Python optimizer's allocation-lifetime boundary before enabling
owned containers. The durable diagnostic is
`tests/native/fixtures/inlined_resource_lifetime.mn`; its body is small enough
to inline into a loop, losing function-exit cleanup. The durable fixture was
rerun: expected stdout `1514280`, with 92,285 bytes / 2,869 allocations retained
under LeakSanitizer (`inline-repro.log`). Preserve cleanup scope or
conservatively reject affected inline candidates. Then coordinate container
handle retain/clone/transfer, copy-in insertion markers, returned/captured aliases
and borrowed lookup lifetimes in lowering and both emitters. Existing native
container leaks remain open. Priority 2 remains active. Nothing pushed/released.

## Previous verified milestone — owned maps

The opt-in owned-map runtime contract is committed as **`5e2f88db`**
(`Add opt-in owned map key and value policies`) and verified.
`__mn_map_new_owned` copies independent key/value policies;
`__mn_map_str_str_new_owned` provides the String/String case. Insertion copies
inputs before mutation, replacement drops the old value and unused copied key,
deletion releases both fields, and rehash transfers entries without extra
copies/drops. Keys returns an independent list with the correct key size.
Owned storage is aligned, and bounded linear probing handles tombstones and
long collision chains. Existing raw APIs remain compatible. See
[the contract](CONTAINER_OWNERSHIP.md) before compiler adoption.

Evidence under `build/memory-ownership/owned-maps/`:

- `runtime-tests.log`: 88 initial passes (27 new checks plus 61 controls).
- `map-tests.log`: all 31 final map checks pass under ASan/UBSan/LSan, including
  four added borrowed-key growth/plain-value checks. There are 92 unique runtime
  checks across these two runs; unchanged controls were not rerun.
- `archive-tests.log`: all 54 owned-list/map checks pass against the exact
  optimized archive. The source run instruments runtime internals; the archive
  run checks the artifact with sanitizer allocation interception.
- `c-runtime.log`: 74/74 standalone C runtime checks pass.
- `fixed-point.log`, `build/fixed-point-fjc4esu9`: both generations pass 103 LLVM
  goldens and eight executable fixtures; stage2/stage3 IR is byte-identical.
- `successor-regressions.log`: all 40 focused native regressions pass on that
  optimized successor. Compiler source is unchanged.

Verified hashes (SHA256):

- Compiler source: `3fc824f2de6e75e80795325dba97f7d089dbd7e3a66246020e66c1f77aeafdf0`.
- Optimized successor: `23d39cf6f225b1b63f7526c0c38ed434c69ed4e127f83afbfb1168d9b1568651`.
- Both IR stages: `3cfe326658775fb4791eac77fe3f99e10506dbdf9a370a040b6af079e4ae050b`.
- Runtime archive: `6d857dd5c21b7e159afc8b1efedc4511c28ae1fe5abb6997890da02e77f9a185`.

The prior verified compiler/runtime pair is preserved as `mnc-baseline` and
`runtime-baseline.a` in this evidence directory. Promotion regenerated compiler
source and rebuilt the runtime at `5e2f88db`; both matched the verified hashes.
The exact tested successor is installed at `mapanare/self/mnc-stage1`. The record
is `build/memory-ownership/owned-maps/promotion.json`. All builds and checks for
this milestone are complete. Toolchain: Linux/WSL, Clang/LLVM 18.1.3, Python 3.12.3.

GitNexus impact reported LOW risk: set/get/iterator-next each have one indexed
direct caller, zero indexed processes; the map struct, delete, keys, free and
deep-free have zero indexed callers. Generated callers are outside the index,
so runtime-wide risk was checked through strict self-hosting. New probe symbols
returned UNKNOWN and were manually reviewed. All validation was Linux/WSL.
Staged detection (`owned-maps/precommit.log`) found seven expected files,
23 indexed symbols, zero affected processes and LOW risk. Manual diff review
confirmed only map dispatch/storage and the new tests/docs changed; line mapping
also listed nearby unchanged legacy declarations.

To rerun the owned-container checks in Linux/WSL from the repository root:

```bash
.venv/bin/python -m pytest tests/native/test_owned_maps.py tests/native/test_owned_lists.py -q
MAPANARE_TEST_RUNTIME=runtime/native/libmapanare_rt.a \
  .venv/bin/python -m pytest tests/native/test_owned_maps.py tests/native/test_owned_lists.py -q
.venv/bin/python scripts/verify_fixed_point.py --stage1 mapanare/self/mnc-stage1 --keep
```

**Next:** integrate container ownership in lowering and both emitters. Begin by
tracing handle copies, call arguments, returns and captures before activating
owned constructors or recursive drops. Map handles currently have exclusive
ownership; choose an explicit retain/clone or transfer contract for aliases.
Insertion copies inputs, so matching Move markers must stop suppressing caller
cleanup. Lookup/iterator results are borrowed, including nested fields, and
must not be independently freed or outlive mutation/destruction. Start with
`List<String>`, `List<List<Int>>`, and String-key/value maps, keeping both
destruction orders and returned/captured aliases in the regression gates.
Existing native container leaks remain open until this integration lands.
Priority 2 remains active; nothing was pushed or released.

## Previous verified milestone — owned lists

The owned-list runtime contract is committed as **`8449beb2`** (`Add opt-in owned
list copy and destruction policies`). New constructors
`__mn_list_new_owned` and `__mn_list_str_new_owned` attach copy/drop operations to
an aligned backing buffer. Descriptor values are copied; the public `MnList`
layout and raw-list behavior stay compatible. The list API now supports copy-in
insertion/replacement, COW detach, growth, concat, clear, pop transfer, deep clone,
and final-owner destruction for these opt-in lists. Nested owned fields are
handled by callbacks. See [the contract](CONTAINER_OWNERSHIP.md) for requirements.

This is the runtime foundation. Existing compiler-generated lists have not been
switched to it, and raw-list/map retention probes remain unresolved. Next:
extend the explicit policy to map keys/values, then coordinate lowering and both
emitters. Before compiler adoption, fix handle copying/argument/return ownership,
remove transfer markers where insertion copies inputs, and preserve borrowed
lookup lifetimes. Do not activate recursive cleanup in isolation.

Evidence under `build/memory-ownership/owned-lists/`:

- `runtime-tests.log`: 61 passed, including 22 new lifecycle cases repeated
  1,000 times under ASan/UBSan/LSan, one incompatible-concat check, and 38 controls.
- `archive-tests.log`: all 23 new checks also pass against the exact GCC-optimized
  runtime archive. The direct-source run instruments runtime internals; the
  archive run verifies the artifact and uses sanitizer allocation interception.
- `c-runtime.log`: the existing standalone runtime suite passes 74/74.
- `fixed-point.log`, `build/fixed-point-xa4kv481`: both generations pass 103 LLVM
  goldens and eight executable fixtures; stage2/stage3 IR is byte-identical.
- `successor-regressions.log`: all 40 focused native checks pass on the optimized
  successor linked with the new runtime. Compiler source itself is unchanged.

Verified hashes (SHA256):

- Compiler source: `3fc824f2de6e75e80795325dba97f7d089dbd7e3a66246020e66c1f77aeafdf0`.
- Optimized successor: `e398ce11961617df0cac2b0432d0106a8eadcf76ed9c3285ceaf75fd3cfc9079`.
- Both IR stages: `3cfe326658775fb4791eac77fe3f99e10506dbdf9a370a040b6af079e4ae050b`.
- Runtime archive: `802a1e99dade4880cc64c0baa331f0fe7fae6c6f53c7e90aec41911bb7bc183f`.

The previous compiler/runtime pair is preserved under `owned-lists/`. Promotion
regenerated compiler source and rebuilt the runtime at `8449beb2`; both matched
the verified hashes. The exact tested successor is installed at
`mapanare/self/mnc-stage1`. The record is
`build/memory-ownership/owned-lists/promotion.json`. All checks and builds for this
milestone are finished. Nothing was pushed or released.

GitNexus impact: push has six direct callers, 13 affected symbols, MEDIUM risk,
and zero indexed processes. String convenience functions, directory listing,
map keys, stream collect, and tensor list conversion are among its callers.
Set/pop/clear/concat/deep-clone/free-strings report LOW; free and clone each have
one indexed direct caller. Generated calls are not represented; broad runtime
risk was reported and checked with self-hosting. New probe symbols were manually
reviewed before indexing. All validation was Linux/WSL. Priority 2 remains active.
Staged detection (`owned-lists/precommit.log`) found six expected files, 32 indexed
symbols, zero affected processes, and LOW risk. Manual diff review confirmed the
nine lifecycle dispatch changes and new helpers; index line mapping also listed
nearby unchanged legacy helpers.

## Previous verified milestone — allocated empty nested buffers

The nested-container milestone is committed as **`48d381ec`** (`Retain allocated
empty buffers when cloning nested lists`). It fixes an allocated-empty-buffer use-after-free
in `__mn_list_deep_clone`. Cleared or popped inner lists still own storage;
cloning must retain that storage even when their length is zero. This changes
one runtime ownership condition and does not enable automatic recursive drops.
The native emitter does not currently call this helper.

The durable [container evidence and implementation sequence](CONTAINER_OWNERSHIP.md)
contains the next task: introduce explicit owned-element copy/drop semantics,
coordinate COW mutation and map replacement/deletion, then integrate lowering
and both emitters. Five C probe modes and two native programs now reproduce
the remaining gaps. Do not add deep frees before establishing element ownership.

Evidence under `build/memory-ownership/nested-containers/`:

- `before.log`: eight ASan use-after-free failures, eight passing controls.
- `after.log`: all 16 nested ownership cases plus list/map controls pass (38 total).
- `c-runtime.log`: the complete standalone C runtime suite passes 74/74.
- `fixed-point.log`, `build/fixed-point-ol5n0yze`: both generations pass 103 LLVM
  goldens and eight executable fixtures; stage2/stage3 output is byte-identical.
- `successor-regressions.log`: all 40 focused native checks pass on the optimized
  successor linked against the updated runtime.
- `baseline-probes.json`: shared/detached String-list use-after-free; shallow
  nested cleanup leaks 80,000 bytes/1,000 allocations; map overwrite leaks
  9,990 bytes/1,998 allocations; deletion leaks 10,000 bytes/2,000 allocations.
- `nested-native.log`, `map-native.log`: native programs retain 415,584 bytes /
  1,998 allocations and 638,000 bytes / 6,000 allocations respectively. Their
  functional outputs are 42000 and 6000. These gaps remain open.

Verified hashes (SHA256):

- Unchanged compiler source: `3fc824f2de6e75e80795325dba97f7d089dbd7e3a66246020e66c1f77aeafdf0`.
- Optimized successor: `fc640380ddae8104e18f60dff08787fc9713fc4952f8bb1c958facee47bb945e`.
- Both compiler IR stages: `3cfe326658775fb4791eac77fe3f99e10506dbdf9a370a040b6af079e4ae050b`.
- Updated runtime archive: `4771333eb0022c11242a6ecd6fc41af3eb2099def2423b655fe376f26f14aeec`.

The prior compiler and runtime are preserved as `nested-containers/mnc-baseline`
and `nested-containers/runtime-baseline.a`. The exact tested successor is installed
at `mapanare/self/mnc-stage1`. Promotion verified fresh source at `48d381ec`, the
runtime archive hash, and the installed binary hash; see
`build/memory-ownership/nested-containers/promotion.json`. All milestone builds
and checks are finished. Nothing was pushed or released.
Validation is Linux/WSL; this does not complete priority 2 or qualify other platforms.

GitNexus context and impact resolve the runtime helper: LOW, zero indexed direct
callers/processes. Generated calls are outside that graph; manual emitter review
and the compiler gate cover that limitation. The only production edit is the
retain condition; the C fixture includes explicitly documented failing diagnostic
modes, while pytest gates only the fixed contract. Existing user edits remain untouched.
Staged detection (`nested-containers/precommit.log`) found the expected five files,
four indexed symbols, zero affected processes, and LOW risk; newly added probes
and documentation were reviewed manually before indexing.

## Previous verified milestone — borrowing calls

The borrowed-String milestone is committed as **`7a54a7bc`** (`Keep String ownership
at proven borrowing call sites`). A conservative MIR proof
records `FnEntry.borrows_strings` in both forward and body registration; callers
keep ownership when the callee is proven not to retain String parameters.
The original reproduction and all 12 new leak regressions now pass. The proof
covers local scalar/String loads and stores, scalar arithmetic, branches,
loops, `len(String)`, integer range helpers, and Void placeholders. Every block
is inspected; stores must target verified local allocas.

Unknown/user/extern calls, aggregate or pointer parameters/returns, resource
captures, Move instructions, and async functions are not proven. They retain
the previous conservative transfer behavior. This is a bounded fix, not a
complete ownership contract. There are no new callee frees or runtime changes.

Current evidence is in `build/memory-ownership/borrowed-string/`: `before.log`
records 12 failing baseline cases (98,890 bytes / 10,000 allocations for each
large case); `candidate-tests.log` records 40 passing checks, including all
12 leak cases and eight String-return/capture controls. The new tests cover
100 and 10,000 iterations, repeated calls, caller and callee aliases, two
arguments sharing one buffer, and both declaration orders. Capture controls
use ASan without LSan because nested container leaks remain unresolved.
`source-tests.log`: 343 passed, two pre-existing xpasses.

The previous installed compiler is preserved at
`build/memory-ownership/borrowed-string/mnc-baseline` (SHA256
`25ff1d8d5494ca809e1603c65814eb8027e19d94fbcd9140524cf606fb5d35b0`).
Strict gate `build/fixed-point-d3yb2vvg` passed: both generations passed all
103 LLVM goldens and eight executable fixtures; stage2/stage3 IR is byte-identical.
Its optimized successor also passed all 40 focused checks
(`successor-regressions.log`). No emitted IR was patched. Promotion verified
fresh concatenated source at `7a54a7bc`, the runtime hash, and the installed
binary hash. The exact verified successor is installed at `mapanare/self/mnc-stage1`;
the record is `build/memory-ownership/borrowed-string/promotion.json`. Builds and
tests for this milestone are finished. No push or release was performed.

Verified hashes (SHA256):

- Concatenated source: `3fc824f2de6e75e80795325dba97f7d089dbd7e3a66246020e66c1f77aeafdf0`.
- Optimized successor: `9c8cd28eec6eeba703f27e7b9b429f4ad665eb289776f78ef5e6bec9afa47d96`.
- Both stage2/stage3 IR: `3cfe326658775fb4791eac77fe3f99e10506dbdf9a370a040b6af079e4ae050b`.
- Unchanged runtime: `381638c3b620a87c04376a5988a9b93b409ad170f5b0abcdd9d1f1106a890830`.

Staged impact (`borrowed-string/precommit.log`): four expected files, seven
indexed symbols, zero affected processes, LOW. Native symbols and the new
test were not indexed at that point; the manual emitter review and full native
validation above cover that limitation. Validation was Linux/WSL only.

Nested container/map retention is now reproduced in the checkpoint above.
Unproven String callees
still need broader capture summaries, especially non-inlined forwarding calls.
Priority 2 remains active.

## Previous verified milestone — value-only struct returns

Priority 2 of the [reliability roadmap](../RELIABILITY_ROADMAP.md) is active,
authorized by the follow-up to continue and commit along the way. Starting
commit: `32dfbcb4` on `dev`, version 5.54.2. Priority 1's verified compiler is
preserved at `build/memory-ownership/mnc-baseline` (SHA256
`819cf7753ef97d8aa0b6b4ee923956a1bc4eaa901b13a567d5845feca23d9bc1`).

**First milestone committed and verified:** `6ad3110d` (`Free native heap locals
when returning value-only structs`). That milestone's optimized successor was installed as
`mapanare/self/mnc-stage1`; its 26 focused checks and strict self-hosting gate
pass. The previous verified compiler remains preserved. This does not complete
priority 2. The borrowed-String follow-up is recorded above.

Final hashes (SHA256):

- Committed concatenated source: `f804bcb15487183a9599cd87af5046cf4e69bd83b764355fce1efe44faab463f`.
- Installed optimized compiler: `25ff1d8d5494ca809e1603c65814eb8027e19d94fbcd9140524cf606fb5d35b0`.
- Both stage2/stage3 IR: `09a247ca5d51f8597682e57a8f13f4aa40d7e63e279872c4998ac081ca55afc7`.
- Runtime archive: `381638c3b620a87c04376a5988a9b93b409ad170f5b0abcdd9d1f1106a890830`.

Promotion record: `build/memory-ownership/promotion.json`. The gate began at
`32dfbcb4` with pending changes; promotion regenerated source at `6ad3110d` and
required byte equality with the validated source, checked the runtime hash,
and verified the installed compiler hash. Builds and tests for this milestone
are finished. No push or release was performed.

## Observed ownership contract

This table describes the current implementation, including gaps. It is not a
claim that all ownership boundaries are consistent or leak-free.

| Value / boundary | Current behavior | Remaining issue |
|---|---|---|
| String literal | Heap bit is clear; runtime free leaves literal storage alone | None identified in this milestone |
| String-producing operation | Emitter tracks an owned slot; overwrite and return cleanup release it unless moved/returned | Ownership transfer through user calls is conservative |
| String return | Locally owned buffers transfer; borrowed heap buffers are cloned; literals stay borrowed | Aggregate escape accounting is still separate |
| User-call String argument | Proven borrowers leave ownership with the caller; unknown/capturing calls clear matching slots | The initial proof is deliberately narrow; non-inlined forwarding and broader capture summaries remain |
| Raw list buffer | COW refcount owns the outer allocation; shallow free releases it at the last reference | Compiler-generated lists still use this contract without recursive element destruction |
| Opt-in owned list buffer | Copy/drop policy follows the buffer; detach copies elements and final-owner release drops them | Runtime API is tested; compiler handle/insertion/lookup integration remains |
| String inserted into container | Lowering emits Move so caller cleanup does not free the captured String | Shallow container cleanup does not establish recursive element cleanup |
| Map entry | Runtime set copies entry bytes; shallow/deep free helpers are separate | Replacement/removal ownership and native emitter map tracking need investigation |
| Heap-bearing struct/enum/boxed return | Native emitter conservatively suppresses cleanup to protect transitive escaping resources | Unrelated temporaries can leak; one-level pointer comparisons are insufficient |
| Value-only struct return | This milestone proves the complete field graph contains scalar values and then permits normal local cleanup | Unknown metadata or depth >= 64 remains conservative |

Relevant sources: `mapanare/self/emit_llvm.mn` (ownership slots, transfers,
returns), `mapanare/self/lower.mn` (Move emission), and
`runtime/native/mapanare_core.c` (String flags, COW lists, map entry storage).
String-list COW cleanup and map replacement are source-review leads, not yet
reproduced defects in this workstream. Do not change their contracts without
executable aliasing and lifetime tests.

## First reproduction and fix

`ret_ty_is_aggregate` previously skipped all cleanup for every `%struct.*`
return, including records containing only integers. A function that allocates
temporary Strings and a `List<Int>`, computes a count, and returns that count
in a struct leaked **88 bytes in two allocations per call**. LeakSanitizer
reported 8,800 bytes / 200 allocations at 100 calls and 880,000 bytes / 20,000
allocations at 10,000 calls. Flat, nested, and five-field records all reproduced it.

The new `return_type_has_no_resources` recursively checks complete struct
metadata and a whitelist of scalar LLVM field types. Pointers, containers,
enums, unknown/incomplete metadata, and recursion at depth 64 are not considered
safe. Empty complete structs are safe. The cleanup guard now allows ordinary
local cleanup only when no tracked heap allocation could escape through the
returned struct. Existing String/List/boxed/tensor cleanup performs the releases;
this does not introduce a new destructor or alter the runtime ABI.

Heap-bearing returns keep their existing conservative behavior. In particular,
`St { lines: List<String> }` must not be treated as safe just because it is small:
the individual String pointers can escape inside that list. A nested String
return control supplements the existing enum, list-capture, and call-capture
ASan regressions.

## Validation ledger

Local evidence lives under ignored `build/memory-ownership/`; this document is
the durable summary for machines without those artifacts.

| Check | Evidence / result |
|---|---|
| Original compiler leak reproduction | `value-return-before.log`: all six cases fail with the linear leak described above |
| Diagnostic compiler | `build-candidate.log`: fresh concatenated source emitted by preserved compiler, LLVM-valid, linked at LLVM O0 |
| Candidate leak checks | `value-return-after.log`: six passed with ASan and LeakSanitizer enabled |
| Native source / semantic checks | `source-tests.log`: 343 passed, two pre-existing xpasses |
| Existing executable controls plus nested String return | `candidate-controls.log`: 20 passed |
| Strict optimized self-hosting | `fixed-point.log`, `build/fixed-point-gfe7dx_s`: both generations pass 103 goldens and eight executable fixtures; stage2/stage3 byte-identical |
| Optimized successor regressions | `successor-regressions.log`: 26 passed, including all six leak-sensitive cases |

No emitted IR is patched. The installed production compiler is the exact
verified successor; source and runtime equality were checked before promotion.
The runtime archive is unchanged by this milestone. Native execution validation
was Linux/WSL; Windows/macOS release qualification is not implied.

## Original borrowed String reproduction (now fixed for proven borrowers)

`borrowed-call.log` records **98,890 bytes in 10,000 allocations** retained by a
read-only String parameter. The diagnostic candidate reproduces this separately
from the now-fixed struct-return leak. Minimal program:

```mapanare
fn measure(text: String) -> Int:
    let mut total: Int = 0
    for i in 0..3:
        total = total + len(text)
    return total
fn main():
    let mut total: Int = 0
    for i in 0..10000:
        let text: String = "item-" + str(i)
        total = total + measure(text)
    print(total)
```

Compile with the native compiler, link the resulting LLVM with clang
`-O1 -g -fsanitize=address -no-pie` and `libmapanare_rt.a`, then run with
`ASAN_OPTIONS=detect_leaks=1:halt_on_error=1`. The baseline caller cleared ownership
for every user call, while this callee only borrowed the String. The new proof
keeps ownership in this caller. Blanket callee frees or blanket removal of caller
transfers can still break captured aliases and were not used.

## Next steps

1. Follow [the container implementation sequence](CONTAINER_OWNERSHIP.md), using
   its confirmed probes: extend owned policies to map keys/values and mutation,
   then integrate handle copying/insertion/lookup in lowering plus both emitters.
   A deep free alone is unsafe for shared element pointers.
2. Extend the borrowing/capture contract beyond the initial proof. Unknown calls
   must remain conservative; track per-argument capture and forwarding only when
   justified by MIR evidence. Keep all leak and captured-alias regressions passing.
3. Establish a repeated-workload memory gate covering these paths before marking
   priority 2 complete. Keep exact compiler self-hosting as a required regression.

## Commands and impact review

Run executable checks in Ubuntu WSL from the repository root:

```bash
.venv/bin/python -m pytest tests/native/test_owned_lists.py tests/native/test_nested_list_ownership.py tests/runtime/test_list_bounds.py tests/llvm/test_map_runtime.py -q
MAPANARE_TEST_RUNTIME=runtime/native/libmapanare_rt.a .venv/bin/python -m pytest tests/native/test_owned_lists.py -q
.venv/bin/python -m pytest tests/integration/test_native_string_argument_borrow.py tests/integration/test_native_value_return_cleanup.py tests/integration/test_string_return_ownership.py tests/integration/test_native_generics.py tests/integration/test_native_bool_output.py tests/integration/test_native_loop_stack.py -q
.venv/bin/python scripts/verify_fixed_point.py --keep
.venv/bin/python -m pytest tests/self_hosted/ tests/bootstrap/test_verification.py::TestPipelineIntegrity -q --tb=short
```

Set `MAPANARE_TEST_COMPILER=<candidate>` to test a retained compiler. The strict
gate accepts `--stage1 <candidate>`. Do not overwrite the preserved baseline.

GitNexus CLI impact/context cannot find native `.mn` symbols, so their risk is
UNKNOWN, not LOW. Manual callers: `ret_ty_is_aggregate` is called by
`emit_drop_glue`; return emission invokes cleanup for all native functions.
The new proof helper calls `find_struct_entry` and recursively checks field
types. Broad emitter risk was reported before editing. The added nested String
test's impact is LOW with zero indexed callers/processes. Run staged
`detect-changes` before each commit, and preserve unrelated AGENTS/CLAUDE/skill
edits and the untracked desktop restart plan.

Borrowing follow-up: impact returned UNKNOWN for `FnEntry`, `new_fn_entry`,
`build_internal_struct_list`, `register_all_internal_structs`, `emit_mir_call`,
`emit_mir_function`, `emit_mir_module`, and the new proof helper. Manual review:
the two function-registration paths call the factory; `emit_mir_by_kind` calls
call emission; `new_emit_state` uses the internal struct field list. `find_function`
reads entries backwards, so both registration paths must preserve the proof flag.
This affects native call emission and self-hosting broadly and was treated as
HIGH risk. The capture test's indexed impact is LOW, zero callers/processes.

`precommit-value-return.log`: five staged files, five indexed symbols, zero
affected processes, LOW. New files/native symbols were reviewed manually because
they were not yet indexed. The first post-commit incremental refresh failed in
GitNexus with `LOWER: Invalid UTF-8` (`reindex-value-return.log`). Use a single
Windows writer and recover with
`npx --offline gitnexus analyze --force --embeddings 1 --index-only`:
rebuild the graph, retain cached embeddings, and cap new embedding generation
to bypass the previously observed duplicate-key bug. Check `.gitnexus/meta.json`
for the latest HEAD and a nonzero embedding count after completion.
