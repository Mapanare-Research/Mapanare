---
severity: high
found: "[[v4.26.0]]"
fixed: "[[v4.30.0]]"
status: fixed
tags: [bug, high, self-hosted, llvm-ir, phi, optimizer]
---

# Dead PHI Cleanup

The self-hosted compiler's dead block elimination pass removed unreachable basic blocks but left surviving blocks' PHI instructions pointing to the deleted labels. `llvm-as` rejected the resulting IR with "use of undefined label" errors, making the optimizer's output invalid whenever it eliminated blocks that were PHI predecessors.

## Root Cause
The block elimination pass in the self-hosted MIR optimizer deleted blocks from the function's block list but did not scan remaining blocks' PHI instructions to remove incoming edges from the deleted predecessors. The Python bootstrap had the same latent bug but never triggered it because its optimizer was less aggressive about block removal.

## Fix
Added a PHI cleanup sub-pass that runs after every block deletion: for each surviving block, any PHI incoming edge whose label no longer exists in the function's block set is removed. If a PHI is left with zero incoming edges, it is replaced with `undef`. Fixed in v4.30.0 as part of the MIR optimizer correctness audit.
