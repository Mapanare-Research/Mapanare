# Borrowed views in loop map ownership

The Python compiler's loop-result proof now follows private map cursors and
borrowed String keys/values. Maps produced by proven fresh factories can be
recycled after local iteration or lookup, provided every dependent view is dead
before the next allocation. Existing private owner slots perform the cleanup.

## Accepted operations

| Value | Accepted consumers |
| --- | --- |
| Map alias | Copy/Phi, `len`, private iterator creation, scalar/String index reads |
| Private cursor | Copy/Phi, has-next, scalar/String next-key, cursor free |
| Borrowed String | Copy/Phi, `len`, `print`, `println`, String equality/inequality, key reads from the same map group |
| Copied scalar | Independent value; may outlive the map or be passed elsewhere |

Cursor and String aliases are closed over the same Copy/Phi graph as map
aliases. Every definition must come from a recognized read or another alias;
unknown origins, parameter origins and overlapping groups reject recycling.
The existing backwards liveness analysis must find no dependent alias live at
the allocation site. Phi inputs remain conservatively live on every predecessor.

Unknown consumers, aggregate captures, returned views, mutations, mixed map
origins and views retained across replacement reject recycling. A String view
keeps this dependency even though its descriptor was copied: the underlying
heap bytes still belong to the parent map. This change adds no general retain,
clone or transfer semantics, and does not enable native compiler map ownership.

## Verification

Eight executable programs run at Python O0–O3 with ASan/UBSan/LSan: heap keys,
scalar lookup, heap String values, printed values, nested cursors, continue,
break and early return. All 32 leak with the previous proof (`34a33421`) and
pass with the new proof. That comparison uses the corrected runtime in both
cases, so it isolates the ownership change.

Eight retained-key/value executions verify that recycling is declined and the
view remains readable. Leak detection is disabled for these guards because
retained map ownership is still unresolved. The tests do not claim those
programs are leak-free.

Thirty-eight new MIR controls cover accepted reads, unknown calls, captures,
returns, and single-origin branch liveness. In the branch controls, skipping
a view overwrite blocks recycling for cursors and Strings but not for copied
scalars. Those cases isolate liveness from the separate mixed-origin guard.
The 23 existing map-loop proof controls also pass, including local iteration,
which is now eligible.

The executable tests exposed unaligned packed-key runtime reads; see
[PACKED_MAP_KEYS.md](PACKED_MAP_KEYS.md) for their separate fix and regressions.
Evidence lives in `build/memory-ownership/map-borrowed-views/`; broad suite and
self-host gate results are recorded in [WORK_LOG.md](WORK_LOG.md).

## Next boundary

Retained aliases, multiple allocation origins, unknown borrow summaries and
nested element ownership need explicit transfer/retain/clone semantics or
stronger proofs. Keep the retained-view guards when extending this analysis.
Native owned-container adoption remains separate. Validation here runs on
Linux/WSL; Windows and macOS execution have not been qualified.
