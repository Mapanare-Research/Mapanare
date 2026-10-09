# Packed map key alignment

Legacy map buckets store keys immediately after two metadata bytes. Hashing,
equality and String cleanup must therefore accept unaligned addresses. Casting
those bytes to `int64_t *`, `double *` or `MnString *` and dereferencing them is
undefined behavior, even on machines that permit unaligned hardware loads.

The runtime now copies packed values into aligned local variables with `memcpy`.
Hash values, equality semantics, bucket layout and the public ABI are unchanged.
Owned maps continue to use aligned buckets and their existing copy/drop policies.

`tests/native/test_packed_map_keys.py` instruments both the C probe and runtime
with ASan/UBSan/LSan at C O0 and O2. It exercises deliberately unaligned public
hash inputs plus insertion, growth, lookup and deletion for integer, float and
String keys. Both cases fail against revision `34a33421` and pass after the fix.
All 31 owned-map policy/lifecycle controls pass as well. Heap String deep cleanup
is additionally exercised by the borrowed-view integration tests.

Evidence: `build/memory-ownership/map-borrowed-views/runtime-baseline.log` and
`runtime-tests.log`. GitNexus reports LOW impact with no indexed direct callers
or processes for the seven edited helpers. Function-pointer dispatch and calls
from generated LLVM are outside that graph; executable tests cover those paths.

This fix was discovered while extending loop-result ownership to borrowed map
views. The new ownership proof and its final self-host validation are recorded
separately in [WORK_LOG.md](WORK_LOG.md).
