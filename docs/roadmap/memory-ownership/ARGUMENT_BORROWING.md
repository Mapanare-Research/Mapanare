# Read-only argument borrowing

The Python and native LLVM emitters now retain caller cleanup at calls whose
entire MIR body is proven to borrow its inputs. This is a prerequisite for owned
container adoption, not activation of the owned runtime constructors.

The native proof previously rejected every list parameter. Calling a read-only
function with a String and a list therefore moved the String away from its owner
even though the callee did not acquire ownership. The fixture retained 8,890
bytes over 1,000 calls. Python applied blanket argument moves at surviving user
calls; its read-only list fixtures retained caller-owned lists and Strings too.

## Proof and scope

`mapanare/borrow.py::function_borrows_arguments` and the native
`function_borrows_strings` inspect all blocks, including unreachable blocks.
Summaries are registered before emitting any body so declaration order does not
change cleanup. The native summary keeps its existing field name and layout;
native container arguments already lack automatic call-site moves, so this
extension changes String cleanup when a call also has list parameters. Python
uses its proof to suppress automatic moves for all arguments of a proven borrower.

The whitelist accepts scalar/String parameters and recursively typed lists with
those element types. It permits local aliases, scalar arithmetic, comparisons,
branches, phi nodes, read-only list indexing, and String/list length. Native
loads and stores must address proven local allocas. Recursive type inspection
has a depth limit. Numeric range loops use each lowerer's existing representation:
native scalar range operations, or Python's private range iterator and cleanup.

Mutation, allocation of resource-bearing containers, moves, resource-bearing
returns, closures, async suspension, unknown/extern/user/indirect calls, maps,
structs and unrecognized types fail closed. This does not infer borrowing from
purity or a scalar return alone. In particular, a scalar-returning function that
stores a String into a caller's list can capture that String; it must retain the
existing conservative transfer behavior.

No changes to lowering were needed for this milestone: the unwanted moves came
from emitters. Lowering's insertion/capture Move markers remain necessary for
the legacy raw containers and must be coordinated with future copy-in adoption.

## Evidence

- `tests/integration/test_container_argument_borrow.py`: 16 executable checks
  across both compilers, forward/backward declaration order, aliases, indexed
  reads and loops. Each workload runs 1,000 times with ASan and LeakSanitizer.
  The preserved baseline fails ten checks and passes six controls; all 16 pass
  after the fix.
- `tests/integration/test_container_capture_lifetime.py`: both compilers preserve
  a String captured by a scalar-returning list mutator. These are invalid-access
  controls with leak detection disabled because legacy lists still lack element
  cleanup; they do not establish general leak freedom.
- `tests/llvm/test_argument_borrow_proof.py`: 20 proof checks, including nested
  list reads and rejection of mutation, capture, unknown calls, async bodies,
  absent bodies, unreachable mutation and recursive type graphs.
- `build/memory-ownership/container-handles/`: baseline logs, impact checks,
  candidate probes, 1,088 LLVM/MIR passes, 253 source checks (two existing xfails),
  and 58 successor regressions. `build/fixed-point-r_9qtc2m` passes 103 LLVM
  goldens/eight output fixtures on both generations with identical stage2/stage3 IR.

## Inlined allocation lifetimes

`tests/native/fixtures/inlined_resource_lifetime.mn` now has a passing sanitizer
regression in `tests/integration/test_inlined_resource_lifetime.py`. Previously,
Python MIR optimization at O2 inlined an allocating scalar-returning helper into
the caller's loop. Its allocations shared function-exit tracking slots, and
String free-before-store detection depended on loop block naming. The original
diagnostic retained 92,285 bytes in 2,869 allocations over 1,000 iterations.

Both optimizers now keep resource-bearing callees out of the inliner. Scalar
arguments, results and operations remain eligible; resource or unknown types,
ownership operations and unsupported instructions fail closed. Native lowering
uses explicit scalar stack slots, so its proof also accepts scalar allocation,
load and store instructions. This is a conservative optimization restriction,
not an implementation of nested cleanup scopes.

The caller's post-call instructions also need the proof: moving an allocation
into the new merge block loses loop-body metadata even when the callee is purely
arithmetic. A second Python reproduction retained 3,488 bytes in 872 allocations
over 1,000 iterations. Such call sites now stay intact. Scalar wrappers may
inline only where their remaining call and caller suffix satisfy the proof;
allocating callees keep their own cleanup boundary on subsequent optimizer runs.

The borrowing fixtures retain their early-return branch to isolate borrowing.
The new regression suite exercises unguarded String/list allocations, the original
combined fixture, forward scalar wrappers, and allocations in the caller at
Python O2/O3 and through the native compiler. Existing SSA-renaming tests and a
native scalar-arithmetic control ensure eligible inlining still runs.

To reproduce, emit the diagnostic with the Python compiler at O2, link the IR
with Clang `-O1 -g -fsanitize=address -no-pie`, the native runtime archive,
`-lm -lpthread -ldl`, and run with `ASAN_OPTIONS=detect_leaks=1:halt_on_error=1`.
Expected stdout is `1514280`, with no sanitizer diagnostics after this fix.

Before enabling owned lists/maps in generated programs, coordinate handle
retain/clone/transfer rules, copy-in insertion
Move markers, returned/captured containers and borrowed lookup lifetimes. The
runtime contracts in [CONTAINER_OWNERSHIP.md](CONTAINER_OWNERSHIP.md) remain opt-in.
