# Mapanare reliability roadmap

This is the resume point for the five-priority improvement program approved on
2026-10-06. Update this file when a milestone changes; keep detailed evidence in
the linked work log. A passing historical release is not evidence for today's
compiler.

## Agreed order

1. **Compiler correctness and self-hosting (completed 2026-10-07).** Close generic specialization
   gaps, reproduce and fix optimized stage2 failures, and validate the actual
   candidate through executable comparisons and strict stage2/stage3 checks.
2. **Memory ownership (active).** Establish consistent string/container lifetime semantics
   and bounded memory use in long-running applications.
3. **Native platforms and installation.** Reproduce current Windows application
   failures, fix confirmed issues, and validate downloaded bundles on clean
   machines. Complete macOS notarization when credentials are available.
4. **Developer workflow.** Make installed init/edit/check/test/build workflows,
   diagnostics, package behavior, and executable documentation consistent.
5. **Complete applications.** Ship a calculator and a second application using
   reusable UI and packaging infrastructure. See the desktop restart plan.

Priority 1 is complete. The follow-up to continue and commit authorizes priority
2; priorities 3–5 remain sequenced work.

## Priority 1 acceptance criteria

- Freshly reproduce the generic body-type substitution issue, then check both
  bootstrap and native compiler behavior with executable regression programs.
- Both the working compiler and its optimized self-hosted successor pass every
  current native golden; record the denominator rather than hard-coding 103.
- The successor compiles current concatenated compiler source without a crash;
  both emitted stages are LLVM-valid and byte-identical for a strict fixed point.
- Run relevant LLVM/MIR, self-hosted, and bootstrap tests. Keep failures explicit.
- Validation must identify source revision, dirty changes, compiler/toolchain
  versions and commands. Preserve the known-working compiler until the candidate
  passes. Do not patch emitted IR to disguise a source/compiler failure.
- Check GitNexus impact before symbol edits and detect changes before completion.

## Current checkpoint

**Consumed map Phi ownership passes its acceptance gate.** Selected-edge
transfers preserve parallel assignments, including critical branch/switch
edges. All 20 new executable cases and eight proof controls pass. Broad
validation passes **1,758 tests**, with seven skips and five expected failures.
See [the Phi contract](memory-ownership/MAP_PHI_OWNERSHIP.md). Retained borrowed
String views are the next integration milestone.

**Retained-map return transfer passes its acceptance gate.** One reference
escapes to the caller while all callee aliases are released. All 24 new
sanitizer executions pass; 20 leaked before the fix. Sixteen proof controls
also pass. Broad validation now passes **1,730 tests**, with seven skips and
five expected failures. Committed as `6cf5a249`; Phi ownership followed it.

**Retained-map compiler integration passes its acceptance gate.** Local map
aliases now own runtime references; replacements release obsolete maps while
retained aliases remain valid. All 40 sanitizer executions and four bounded
100,000-iteration tests pass. The optimizer snapshot correction is committed as
`ddcb8f9b`. Broad validation passes **1,690 tests**, with seven skips and five
expected failures. Strict self-hosting at `build/fixed-point-q3waed5b` passes
104 LLVM goldens and nine outputs per generation with byte-identical IR.

Runtime references (`d82e2078`) and the group proof (`dd8c2ce3`) are integrated
in `92467283`.
The user has authorized continuation without further step-by-step approval.
Retained-map returns are now integrated as described above. Retained borrowed
views and native compiler adoption follow Phi ownership. See [the work log](memory-ownership/WORK_LOG.md)
for evidence, exact limits, hashes and the resume point.

**Priority 2 active; borrowed-view loop cleanup committed as `c81dfb64`.**
Private cursors and borrowed String key/value aliases must be dead before the
next allocation; copied scalars are independent. All 32 new leak cases pass,
with eight retained-view guards and 38 new proof controls. Broader validation
passes 1,214 LLVM/MIR tests, 240 ownership regressions and 33 runtime checks.
See [the borrowed-view contract](memory-ownership/MAP_BORROWED_VIEWS.md).
The tests exposed packed-key alignment UB, fixed separately in `ace5c43a`.
Strict self-hosting passes at `build/fixed-point-yip0m8ol`: 104 LLVM goldens and
nine outputs per generation, with identical IR. The exact tested successor,
linked to the corrected runtime, is installed. Hashes and resume instructions
are in [the work log](memory-ownership/WORK_LOG.md).

**Priority 2 active; loop-result cleanup committed as `8f494554`.** A liveness
proof selects nonescaping factory results and private owner
slots release their previous maps. The 535,464-byte reproducer now passes, as
do all 32 new leak-checked executions, four retained-alias guards and 23 proof
controls. Broad suites pass 1,174 LLVM/MIR checks and 200 focused regressions.
See [the loop-owner contract](memory-ownership/MAP_LOOP_OWNERS.md).
Strict self-hosting passes at `build/fixed-point-8ht_8407`: 104 LLVM goldens and
nine required outputs per generation, with identical IR and unchanged native
compiler/runtime hashes.

**Priority 2 active; direct Python map returns committed as `18c73cda`.** Callee
cleanup preserves the returned handle, and callers clean up results only from
proven fresh-map factories. All 28 new sanitizer executions and thirteen proof
controls pass; twenty executions failed on the original emitter. The broader
suites pass 1,151 LLVM/MIR checks and 164 focused regressions. See
[the map return contract](memory-ownership/MAP_RETURNS.md). Native source and
runtime are unchanged; the installed compiler remains the prior verified binary.
Strict self-hosting reran successfully at `build/fixed-point-n45ogd72`: 104 LLVM
goldens and nine outputs per generation, with byte-identical IR and unchanged
compiler/runtime hashes.

**Priority 2 active; bootstrap iterator follow-up committed as `970bc93c`.** Inclusive ranges
now link and safely include `INT64_MAX`. Map loops progress, preserve key types,
and release private cursors on all exits. All 36 native/bootstrap control cases
pass; the six expected bootstrap failures have been removed. Twenty new O0–O3
sanitizer cases and two C boundary probes pass alongside existing runtime tests.

Native loop-control was committed as `8c341089`.
Range `continue` advances the counter, and map break/continue targets stay local
through nesting. All 18 native cases pass at Clang O0/O2; the old compiler failed
16. The new golden runs as part of both strict self-hosting generations. See
[the loop-control notes](compiler-correctness/LOOP_CONTROL.md) for the fix and
the subsequent Python bootstrap iterator fixes.

Inlining cleanup protection was committed as `b280a29f`.
Both optimizers preserve the allocating callee's function boundary and prevent
block splits that lose cleanup metadata for later caller allocations. Scalar
arithmetic still inlines. All 22 new inlining checks pass, alongside 1,137
LLVM/MIR/optimizer checks and strict self-hosting. This conservative guard closes
the inlining prerequisite without introducing nested cleanup scopes.

Read-only argument borrowing was committed as `c3538bd0`.
Proven read-only calls preserve caller cleanup for Strings and lists, including
aliases, indexed reads and forward calls. All 16 leak regressions and two capture
controls pass, alongside 1,088 LLVM/MIR checks and strict self-hosting. Mutating
or capturing callees retain conservative ownership transfer. See
[the borrowing contract](memory-ownership/ARGUMENT_BORROWING.md).

The owned-map runtime contract was committed as `5e2f88db`. Opt-in maps now
copy keys/values before insertion, release replaced/deleted entries, transfer
ownership during rehash, and return independently owned key lists. Aligned
storage and bounded probing cover aliasing and collision edge cases. All 31 new
checks pass under ASan/UBSan/LSan; all 54 owned-list/map checks pass against the
optimized runtime archive. Compiler adoption remains the next milestone.

The owned-list runtime contract was committed as `8449beb2`. Opt-in
lists now carry copy/drop policies through COW cloning, mutation, growth, concat,
clear, pop, and final-owner destruction. All 23 new checks pass both with an
instrumented runtime and against the optimized archive; the combined runtime
suite passes 61 checks and the standalone C suite passes 74/74. Compiler-generated
lists still use the raw contract; activation requires coordinated emitter work.

The previous nested-list runtime fix, `48d381ec`, means deep
cloning now retains allocated empty inner buffers after clear/pop. Eight ASan
use-after-free failures are fixed; all 16 ownership cases and 22 runtime controls
pass, alongside the 74/74 standalone C suite. This does not yet enable automatic
recursive element cleanup in native programs.

The second ownership fix, `7a54a7bc`, means proven
borrowing calls now leave String cleanup with their callers. The reproduced
98,890-byte leak over 10,000 items is gone in all 12 new LeakSanitizer cases,
including aliases, repeated calls, loops, and forward declarations. Unknown
calls and captures retain conservative transfer behavior.

The first ownership fix, `6ad3110d`, means returning a
value-only struct no longer retains unrelated heap locals. The reproduced leak
was 88 bytes per call (880,000 bytes at 10,000 calls); six LeakSanitizer cases now
pass for flat, nested, and wide records. Heap-bearing returns retain their
conservative escape protection, checked by String/container lifetime regressions.

The previous bootstrap iterator gate was `build/fixed-point-uvraczp_`: both compiler generations pass
104 LLVM goldens and nine executable fixtures, and stage2/stage3 are byte-identical.
The optimized successor passes 136 focused checks and all 104 golden link/run
checks plus the corpus-count check. The full LLVM/MIR/optimizer suite passes
1,140 tests; iterator/runtime controls pass 128. Promotion at `970bc93c`
regenerated source and rebuilt the runtime, matching the gate hashes. The exact
tested optimized successor is installed at `mapanare/self/mnc-stage1`.
The prior verified pair is preserved under
`build/memory-ownership/bootstrap-iteration/`.
Self-hosted source checks pass 253 tests with two expected xfails.

**Next:** extend ownership to retained aliases, multiple allocation origins and
unrecognized borrowed views. The original loop and direct-return fixtures now pass for
the proven cases. Broader transfer/retain/clone rules are still needed before
enabling general recycling. Continue container handles, insertion, and borrowed lookups in lowering
and both emitters. Map handles currently have exclusive ownership; sharing needs
an explicit retain/clone or transfer design before generated cleanup is enabled.
The [container evidence and implementation sequence](memory-ownership/CONTAINER_OWNERSHIP.md)
records five C probes and native reproductions retaining about 416 KB for nested
lists and 638 KB for map replacement over 1,000 iterations. Broader borrowing
summaries also remain open. Current hashes and resume commands are in
[the ownership work log](memory-ownership/WORK_LOG.md). Priority 2 remains active.

Priority 1 completed generic specialization, native lifetime/stack/boolean fixes,
and strict self-hosting validation. Its historical evidence, including 1,068
LLVM/MIR passes and the bootstrap reruns, is in
[the compiler correctness work log](compiler-correctness/WORK_LOG.md).

Validation here was Linux/WSL. Windows/macOS release qualification and general
leak freedom remain outside this milestone.

Starting HEAD: `cbcfa0da` (v5.54.2). The first verified milestone is committed as
`9c877e62` (`Fix compiler lifetime bugs and enforce strict self-hosting validation`).
The native generic follow-up is committed as `888ab1f5`
(`Support explicit generics and body specialization in native compiler`).
The pre-existing untracked `DESKTOP_APP_RESTART_PLAN.md` is user work and remains
untouched. No release has been made by this task.

Resume from [the priority 2 work log](memory-ownership/WORK_LOG.md).
