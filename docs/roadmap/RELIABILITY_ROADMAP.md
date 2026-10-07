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

**Priority 1 verified and completed (2026-10-07).** Implemented generic
body specialization, native String return/transfer fixes, inliner ownership
operand renaming, bounded loop stack allocation, and boolean output parity.
Replaced the permissive fixed-point script with a strict validator that records
reproducible evidence.

The final current-source gate is `build/fixed-point-8a9z1nv3`: both optimized
generations pass all 103 LLVM goldens and eight executable fixtures, and stage2
and stage3 are byte-identical. Its successor passes all 19 focused native checks
and is installed locally as `mapanare/self/mnc-stage1`. Promotion verified that
fresh source at commit `888ab1f5` and the runtime match the gate's hashes; the
previous verified compiler remains preserved.

**Native generic follow-up implemented:** explicit `::<T>` calls, recursive body
type substitution, nested type mangling, recursive specialization reuse, typed
pipes, and schema generation through generic impl methods. The optimized native
successor includes the typed Option locals and standalone match fallbacks.
LLVM/MIR: 1,068 passed; the broader suite's two failures
are resolved by standalone semantic fixes and a bounded 180-second object-build
timeout (isolated build passed in 79.72 seconds overall).

**Next: priority 2, memory ownership.** Document ownership across function calls
and container insertion/return, add leak-sensitive long-running regressions,
then fix recursive cleanup with the current compiler gates as the baseline.
The first priority 2 leak has been reproduced and fixed in a diagnostic candidate:
value-only struct returns retained unrelated heap locals (88 bytes per call).
Six LeakSanitizer cases now pass, including on the optimized successor; all 26
focused native checks pass, along with both generations' goldens and the exact
fixed point. The next reproduced gap is read-only String call arguments
(98,890 bytes over 10,000 calls). Continue
from [the ownership work log](memory-ownership/WORK_LOG.md).

Validation here was Linux/WSL; Windows/macOS release
qualification and general leak freedom remain outside this milestone.

Starting HEAD: `cbcfa0da` (v5.54.2). The first verified milestone is committed as
`9c877e62` (`Fix compiler lifetime bugs and enforce strict self-hosting validation`).
The native generic follow-up is committed as `888ab1f5`
(`Support explicit generics and body specialization in native compiler`).
The pre-existing untracked `DESKTOP_APP_RESTART_PLAN.md` is user work and remains
untouched. No release has been made by this task.

Resume from [the priority 1 work log](compiler-correctness/WORK_LOG.md).
