# Ownership across map merges

Consumed map Phi values participate in complete retained alias groups. A Phi
must lead its block, have Map-typed inputs and exactly one incoming value for
each actual predecessor. Missing, duplicate, unknown, scalar, late and borrowed
inputs reject ownership for that group; unrelated valid groups remain eligible.

The Python LLVM emitter creates a dedicated block for each selected edge that
transfers map references. It redirects that predecessor's branch or switch
target to the new block. Untaken edges never overwrite a Phi owner. All incoming
values are loaded and retained before any old owner is released, preserving
parallel assignments such as swapping two maps on a loop backedge. The emitter
uses the actual final LLVM block generated for each MIR predecessor, including
blocks split by runtime checks.

The fresh-map factory summary also accepts noncapturing EnumTag reads emitted
by match lowering. Borrowed map returns still fail the freshness proof.

## Verification

- Sixteen source-level match executions pass at O0–O3: factory arms, existing
  aliases, returned merges, and three-way matches. All sixteen leaked before
  integration.
- Four direct-MIR programs pass at Clang O0/O2 for conditional and switch critical
  edges. Each repeatedly swaps two Phi owners after replacing their original
  allocation owners. Exact exit status verifies parallel and selected-edge
  semantics; runtime observers enforce at most eight live maps and zero live
  references at exit. All four failed the bound before integration.
- Eight new proof controls cover valid critical edges, malformed inputs and
  owned-versus-borrowed match factories. Existing invalid-Phi controls remain.
- The focused gate passes 163 tests; the broad LLVM/MIR/integration gate passes
  **1,758 tests**, with seven skips and five expected failures. Executables run
  with ASan/UBSan/LSan. Black/Ruff and staged whitespace checks pass.

Evidence: `build/memory-ownership/retained-map-emitter/phi-*.log`. This milestone
changes the Python compiler. Retained String views, native owned-container
adoption, nested resources, mutation and escaping captures need further rules.
