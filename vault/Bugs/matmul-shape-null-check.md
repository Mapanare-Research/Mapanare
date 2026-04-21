---
severity: high
found: "[[v3.47.0]]"
fixed: "[[v4.28.0]]"
status: fixed
tags: [bug, high, gpu, tensor, null-check, carry-forward]
---

# Matmul Shape NULL Check

`__mn_gpu_tensor_matmul` in the GPU runtime accepted shape arrays without any NULL check and performed no dimension validation. Passing a tensor with uninitialized or missing shape metadata produced an out-of-bounds read on the shape pointer, corrupting kernel launch parameters or segfaulting inside the CUDA driver.

## Root Cause
The GPU tensor matmul implementation assumed shapes were always valid because the caller (the MIR lowerer) was supposed to guarantee it. No defensive check was added. The bug was a known carry-forward from v3.47.0 (27 versions) because the GPU path was rarely exercised in CI and the issue only manifested with malformed or dynamically-constructed tensors.

## Fix
Added NULL checks on both input shape arrays and a dimension compatibility assertion (`a.cols == b.rows`) before kernel dispatch. Returns an error result instead of crashing. Added GPU tensor matmul to the CI test matrix with shape edge cases. Fixed in v4.28.0.
