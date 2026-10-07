# Mapanare reliability roadmap

This is the resume point for the five-priority improvement program approved on
2026-10-06. Update this file when a milestone changes; keep detailed evidence in
the linked work log. A passing historical release is not evidence for today's
compiler.

## Agreed order

1. **Compiler correctness and self-hosting (active).** Close generic specialization
   gaps, reproduce and fix optimized stage2 failures, and validate the actual
   candidate through executable comparisons and strict stage2/stage3 checks.
2. **Memory ownership.** Establish consistent string/container lifetime semantics
   and bounded memory use in long-running applications.
3. **Native platforms and installation.** Reproduce current Windows application
   failures, fix confirmed issues, and validate downloaded bundles on clean
   machines. Complete macOS notarization when credentials are available.
4. **Developer workflow.** Make installed init/edit/check/test/build workflows,
   diagnostics, package behavior, and executable documentation consistent.
5. **Complete applications.** Ship a calculator and a second application using
   reusable UI and packaging infrastructure. See the desktop restart plan.

Only priority 1 is authorized for implementation in this task. Later priorities
remain sequenced work, except where a compiler fix necessarily touches them.

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

**First milestone verified (2026-10-07); priority 1 remains active.** Implemented generic
body specialization, native String return/transfer fixes, inliner ownership
operand renaming, bounded loop stack allocation, and boolean output parity.
Replaced the permissive fixed-point script with a strict validator that records
reproducible evidence.

The optimized production compiler and self-hosted successor pass all 103 LLVM
goldens and eight executable golden fixtures. Stage2 and stage3 are byte-identical;
the production compiler emits that exact same fixed point. All 16 new regression
checks pass. LLVM/MIR: 1,068 passed; self-hosted/bootstrap/optimizer suites:
864 passed, 5 xfailed, 2 xpassed after correcting the CLI test PATH.

**Next:** native explicit `::<T>` calls and generic-body type substitution parity.
This needs AST/parser/semantic/lowering work; the Python body-specialization fix
does not by itself add that native syntax. Stay on priority 1 before moving to
the general memory-ownership program. Validation here was Linux/WSL.

Starting HEAD: `cbcfa0da` (v5.54.2). The pre-existing untracked
`DESKTOP_APP_RESTART_PLAN.md` is user work and remains untouched. No commit or
release has been made by this task.

Resume from [the priority 1 work log](compiler-correctness/WORK_LOG.md).
