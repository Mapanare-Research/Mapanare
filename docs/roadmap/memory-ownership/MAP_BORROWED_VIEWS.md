# Borrowed views in loop map ownership

## Retained parent references

The Python emitter now supports local String views that survive map replacement.
Each proven view alias has a private parent-map reference slot. Lookup and
cursor-next acquire a parent reference; Copy duplicates that reference before
releasing the destination's previous parent. Literal assignment releases the
old parent. Function cleanup releases all view references, including when the
parent map itself is returned. Private cursor parent slots let a saved key
remain valid after the cursor closes or its source map variable is replaced.

The complete-view proof accepts literal origins, map reads and copies; known
read-only consumers include print, length and equality. Consumed String Phis
carry both the selected descriptor and its parent reference. Parent maps are
proved together when a merge can select either map. Literal alternatives carry
a null parent. Edge blocks acquire all incoming parents before replacing any
old owner, preserving parallel swaps. Unknown calls, captures, returned String
views, parameter origins and concatenation remain conservative boundaries.
Map mutation is still excluded.
The existing cheaper liveness-based loop recycler retains precedence.

All 24 new O0–O3 programs pass with ASan/UBSan/LSan; direct pre-fix executions
confirm all 24 leaked. They cover saved values and keys, copy snapshots,
self-assignment, literal clearing, replacement during iteration and early
scalar returns. Ten proof controls pass. The eight previous retained-view
guards now also require leak freedom. The bounded-memory suite includes saved
keys and values over 100,000 iterations at O0–O3, with at most eight live maps
and no references remaining at exit. See the current broad gate in WORK_LOG.

Evidence: `build/memory-ownership/retained-map-emitter/views-*.log`.

The String-Phi follow-up adds twelve source executions (selected views, literal
alternatives and nested merges), all leaking before integration. Four direct
MIR executions swap String descriptors and parent references across critical
conditional/switch edges at Clang O0/O2, with exact output and bounded live-map
checks. Seven proof controls reject uncertain parents and escaping merges.
All pass. The combined broad gate passes **1,823 tests**, with seven skips and
five expected failures; strict self-hosting passes at `build/fixed-point-c2fybyz0`.
See `view-phi-*.log`, `final-full.log` and `final-fixed-point.log` in the same
evidence directory.

## Earlier liveness milestone

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

Eight retained-key/value executions originally verified that recycling was
declined and the view remained readable with leak detection disabled. The
retained-parent integration above strengthens those same guards to require
leak freedom.

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
