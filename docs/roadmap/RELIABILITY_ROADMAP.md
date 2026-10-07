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

**Priority 2 active; second ownership fix committed as `7a54a7bc`.** Proven
borrowing calls now leave String cleanup with their callers. The reproduced
98,890-byte leak over 10,000 items is gone in all 12 new LeakSanitizer cases,
including aliases, repeated calls, loops, and forward declarations. Unknown
calls and captures retain conservative transfer behavior.

The first ownership fix, `6ad3110d`, means returning a
value-only struct no longer retains unrelated heap locals. The reproduced leak
was 88 bytes per call (880,000 bytes at 10,000 calls); six LeakSanitizer cases now
pass for flat, nested, and wide records. Heap-bearing returns retain their
conservative escape protection, checked by String/container lifetime regressions.

The current gate is `build/fixed-point-d3yb2vvg`: both compiler generations pass
103 LLVM goldens and eight executable fixtures, and stage2/stage3 are byte-identical.
Its optimized successor passes all 40 focused native checks and is installed as
`mapanare/self/mnc-stage1`. Promotion verified fresh source at commit `7a54a7bc`
and the runtime against the gate's hashes. The prior verified compiler remains
preserved. Native source checks: 343 passed, two pre-existing xpasses.

**Next:** reproduce nested container/map retention and address element ownership
together with COW cloning and destruction; extend capture summaries beyond the
initial borrowing proof. The current ownership rules, reproductions, hashes, and resume commands are in
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
