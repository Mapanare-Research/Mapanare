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

**Priority 2 active; native loop-control follow-up committed as `8c341089`.**
Range `continue` advances the counter, and map break/continue targets stay local
through nesting. All 18 native cases pass at Clang O0/O2; the old compiler failed
16. The new golden runs as part of both strict self-hosting generations. See
[the loop-control notes](compiler-correctness/LOOP_CONTROL.md) for the fix and
remaining Python bootstrap discrepancies.

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

The current gate is `build/fixed-point-v1axkv58`: both compiler generations pass
104 LLVM goldens and nine executable fixtures, and stage2/stage3 are byte-identical.
Its optimized successor passes 110 focused checks (six strict expected Python
failures) and 1,140 LLVM/MIR/optimizer checks, and is installed
at `mapanare/self/mnc-stage1`. Promotion regenerated source and rebuilt the runtime
at `8c341089`, matching the gate hashes. The prior verified pair is preserved
under `build/memory-ownership/range-continue/`.
Self-hosted source checks pass 253 tests with two expected xfails.

**Next:** fix Python bootstrap inclusive-range linking and nested map/range
iteration. Both were reproduced against the unchanged bootstrap during the
native comparison: two link failures and four timeouts are now strict expected
failures in `tests/integration/test_native_for_continue.py`.
Then integrate container handles, insertion, and borrowed lookups in lowering
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
