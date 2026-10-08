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

## Next prerequisite: inlined allocation lifetimes

`tests/native/fixtures/inlined_resource_lifetime.mn` preserves a separate
diagnostic discovered during this work. Python MIR optimization at O2 inlines
an allocating scalar-returning helper into the caller's loop. Its allocations
then share function-exit tracking slots, and String free-before-store detection
also depends on loop block naming. The observed diagnostic after the borrowing
fix retained 92,285 bytes in 2,869 allocations over 1,000 iterations.

The passing borrowing fixtures include a real early-return branch in their
allocating helper, preserving the call boundary under the current single-block
inliner. This isolates the tested borrowing behavior; it does not fix the
inlining issue. Do not erase that guard without addressing resource scope.

To reproduce, emit the diagnostic with the Python compiler at O2, link the IR
with Clang `-O1 -g -fsanitize=address -no-pie`, the native runtime archive,
`-lm -lpthread -ldl`, and run with `ASAN_OPTIONS=detect_leaks=1:halt_on_error=1`.
Expected stdout is `1514280`; sanitizer output currently reports retention.

Before enabling owned lists/maps in generated programs, preserve allocation
cleanup boundaries through inlining (or conservatively decline affected inline
candidates). Then coordinate handle retain/clone/transfer rules, copy-in insertion
Move markers, returned/captured containers and borrowed lookup lifetimes. The
runtime contracts in [CONTAINER_OWNERSHIP.md](CONTAINER_OWNERSHIP.md) remain opt-in.
