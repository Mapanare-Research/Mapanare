# Private range cleanup on function exits

Range lowering already emits a release on the loop's normal exit, but an early
function return bypassed that block. Nested loops leaked every active range,
including functions returning a retained map or a scalar derived from a saved
String view.

The Python emitter now gives each proven private range constructor a pointer
slot initialized to null at entry. Construction replaces that slot; explicit
loop-exit release clears it. Function cleanup releases every remaining slot,
even when the function has no other owned resources. An early return before
construction or a skipped loop is safe, and normal exits do not double-free.
The runtime free is called with its actual void signature.

`private_range_results` accepts exclusive/inclusive constructors with two Int
bounds and only direct has-next, next and release uses. Copies, captures,
returns, parameter overwrites, multiple definitions/releases, malformed bounds
and async functions fail closed. This is private iterator cleanup, not a
general ownership contract for escaped or copied Range values.

The executable suite runs six programs at O0–O3 under ASan/UBSan/LSan: scalar
returns, inclusive ranges, nested early returns, retained-map returns, retained-
view scalar returns, and normal/break/continue/skipped exits. Twenty cases leak
before the fix; all 24 pass afterward. Twelve proof controls and the 92-test
focused interaction suite pass. Broad results are recorded in WORK_LOG.

Evidence: `build/memory-ownership/retained-map-emitter/range-*.log`. This changes
only Python compiler emission; native compiler source and runtime are unchanged.
