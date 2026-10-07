# Memory ownership work log

## Resume point — 2026-10-07

The borrowed-String milestone is committed as **`7a54a7bc`** (`Keep String ownership
at proven borrowing call sites`). A conservative MIR proof
records `FnEntry.borrows_strings` in both forward and body registration; callers
keep ownership when the callee is proven not to retain String parameters.
The original reproduction and all 12 new leak regressions now pass. The proof
covers local scalar/String loads and stores, scalar arithmetic, branches,
loops, `len(String)`, integer range helpers, and Void placeholders. Every block
is inspected; stores must target verified local allocas.

Unknown/user/extern calls, aggregate or pointer parameters/returns, resource
captures, Move instructions, and async functions are not proven. They retain
the previous conservative transfer behavior. This is a bounded fix, not a
complete ownership contract. There are no new callee frees or runtime changes.

Current evidence is in `build/memory-ownership/borrowed-string/`: `before.log`
records 12 failing baseline cases (98,890 bytes / 10,000 allocations for each
large case); `candidate-tests.log` records 40 passing checks, including all
12 leak cases and eight String-return/capture controls. The new tests cover
100 and 10,000 iterations, repeated calls, caller and callee aliases, two
arguments sharing one buffer, and both declaration orders. Capture controls
use ASan without LSan because nested container leaks remain unresolved.
`source-tests.log`: 343 passed, two pre-existing xpasses.

The previous installed compiler is preserved at
`build/memory-ownership/borrowed-string/mnc-baseline` (SHA256
`25ff1d8d5494ca809e1603c65814eb8027e19d94fbcd9140524cf606fb5d35b0`).
Strict gate `build/fixed-point-d3yb2vvg` passed: both generations passed all
103 LLVM goldens and eight executable fixtures; stage2/stage3 IR is byte-identical.
Its optimized successor also passed all 40 focused checks
(`successor-regressions.log`). No emitted IR was patched. Promotion verified
fresh concatenated source at `7a54a7bc`, the runtime hash, and the installed
binary hash. The exact verified successor is installed at `mapanare/self/mnc-stage1`;
the record is `build/memory-ownership/borrowed-string/promotion.json`. Builds and
tests for this milestone are finished. No push or release was performed.

Verified hashes (SHA256):

- Concatenated source: `3fc824f2de6e75e80795325dba97f7d089dbd7e3a66246020e66c1f77aeafdf0`.
- Optimized successor: `9c8cd28eec6eeba703f27e7b9b429f4ad665eb289776f78ef5e6bec9afa47d96`.
- Both stage2/stage3 IR: `3cfe326658775fb4791eac77fe3f99e10506dbdf9a370a040b6af079e4ae050b`.
- Unchanged runtime: `381638c3b620a87c04376a5988a9b93b409ad170f5b0abcdd9d1f1106a890830`.

Staged impact (`borrowed-string/precommit.log`): four expected files, seven
indexed symbols, zero affected processes, LOW. Native symbols and the new
test were not indexed at that point; the manual emitter review and full native
validation above cover that limitation. Validation was Linux/WSL only.

Next, reproduce nested container/map retention and design element ownership
together with COW cloning, overwrite, and destruction. Unproven String callees
still need broader capture summaries, especially non-inlined forwarding calls.
Priority 2 remains active.

## Previous verified milestone — value-only struct returns

Priority 2 of the [reliability roadmap](../RELIABILITY_ROADMAP.md) is active,
authorized by the follow-up to continue and commit along the way. Starting
commit: `32dfbcb4` on `dev`, version 5.54.2. Priority 1's verified compiler is
preserved at `build/memory-ownership/mnc-baseline` (SHA256
`819cf7753ef97d8aa0b6b4ee923956a1bc4eaa901b13a567d5845feca23d9bc1`).

**First milestone committed and verified:** `6ad3110d` (`Free native heap locals
when returning value-only structs`). That milestone's optimized successor was installed as
`mapanare/self/mnc-stage1`; its 26 focused checks and strict self-hosting gate
pass. The previous verified compiler remains preserved. This does not complete
priority 2. The borrowed-String follow-up is recorded above.

Final hashes (SHA256):

- Committed concatenated source: `f804bcb15487183a9599cd87af5046cf4e69bd83b764355fce1efe44faab463f`.
- Installed optimized compiler: `25ff1d8d5494ca809e1603c65814eb8027e19d94fbcd9140524cf606fb5d35b0`.
- Both stage2/stage3 IR: `09a247ca5d51f8597682e57a8f13f4aa40d7e63e279872c4998ac081ca55afc7`.
- Runtime archive: `381638c3b620a87c04376a5988a9b93b409ad170f5b0abcdd9d1f1106a890830`.

Promotion record: `build/memory-ownership/promotion.json`. The gate began at
`32dfbcb4` with pending changes; promotion regenerated source at `6ad3110d` and
required byte equality with the validated source, checked the runtime hash,
and verified the installed compiler hash. Builds and tests for this milestone
are finished. No push or release was performed.

## Observed ownership contract

This table describes the current implementation, including gaps. It is not a
claim that all ownership boundaries are consistent or leak-free.

| Value / boundary | Current behavior | Remaining issue |
|---|---|---|
| String literal | Heap bit is clear; runtime free leaves literal storage alone | None identified in this milestone |
| String-producing operation | Emitter tracks an owned slot; overwrite and return cleanup release it unless moved/returned | Ownership transfer through user calls is conservative |
| String return | Locally owned buffers transfer; borrowed heap buffers are cloned; literals stay borrowed | Aggregate escape accounting is still separate |
| User-call String argument | Proven borrowers leave ownership with the caller; unknown/capturing calls clear matching slots | The initial proof is deliberately narrow; non-inlined forwarding and broader capture summaries remain |
| List buffer | COW refcount owns the outer allocation; shallow list free releases it at the last reference | Element ownership and recursive destruction are not encoded in that buffer contract |
| String inserted into container | Lowering emits Move so caller cleanup does not free the captured String | Shallow container cleanup does not establish recursive element cleanup |
| Map entry | Runtime set copies entry bytes; shallow/deep free helpers are separate | Replacement/removal ownership and native emitter map tracking need investigation |
| Heap-bearing struct/enum/boxed return | Native emitter conservatively suppresses cleanup to protect transitive escaping resources | Unrelated temporaries can leak; one-level pointer comparisons are insufficient |
| Value-only struct return | This milestone proves the complete field graph contains scalar values and then permits normal local cleanup | Unknown metadata or depth >= 64 remains conservative |

Relevant sources: `mapanare/self/emit_llvm.mn` (ownership slots, transfers,
returns), `mapanare/self/lower.mn` (Move emission), and
`runtime/native/mapanare_core.c` (String flags, COW lists, map entry storage).
String-list COW cleanup and map replacement are source-review leads, not yet
reproduced defects in this workstream. Do not change their contracts without
executable aliasing and lifetime tests.

## First reproduction and fix

`ret_ty_is_aggregate` previously skipped all cleanup for every `%struct.*`
return, including records containing only integers. A function that allocates
temporary Strings and a `List<Int>`, computes a count, and returns that count
in a struct leaked **88 bytes in two allocations per call**. LeakSanitizer
reported 8,800 bytes / 200 allocations at 100 calls and 880,000 bytes / 20,000
allocations at 10,000 calls. Flat, nested, and five-field records all reproduced it.

The new `return_type_has_no_resources` recursively checks complete struct
metadata and a whitelist of scalar LLVM field types. Pointers, containers,
enums, unknown/incomplete metadata, and recursion at depth 64 are not considered
safe. Empty complete structs are safe. The cleanup guard now allows ordinary
local cleanup only when no tracked heap allocation could escape through the
returned struct. Existing String/List/boxed/tensor cleanup performs the releases;
this does not introduce a new destructor or alter the runtime ABI.

Heap-bearing returns keep their existing conservative behavior. In particular,
`St { lines: List<String> }` must not be treated as safe just because it is small:
the individual String pointers can escape inside that list. A nested String
return control supplements the existing enum, list-capture, and call-capture
ASan regressions.

## Validation ledger

Local evidence lives under ignored `build/memory-ownership/`; this document is
the durable summary for machines without those artifacts.

| Check | Evidence / result |
|---|---|
| Original compiler leak reproduction | `value-return-before.log`: all six cases fail with the linear leak described above |
| Diagnostic compiler | `build-candidate.log`: fresh concatenated source emitted by preserved compiler, LLVM-valid, linked at LLVM O0 |
| Candidate leak checks | `value-return-after.log`: six passed with ASan and LeakSanitizer enabled |
| Native source / semantic checks | `source-tests.log`: 343 passed, two pre-existing xpasses |
| Existing executable controls plus nested String return | `candidate-controls.log`: 20 passed |
| Strict optimized self-hosting | `fixed-point.log`, `build/fixed-point-gfe7dx_s`: both generations pass 103 goldens and eight executable fixtures; stage2/stage3 byte-identical |
| Optimized successor regressions | `successor-regressions.log`: 26 passed, including all six leak-sensitive cases |

No emitted IR is patched. The installed production compiler is the exact
verified successor; source and runtime equality were checked before promotion.
The runtime archive is unchanged by this milestone. Native execution validation
was Linux/WSL; Windows/macOS release qualification is not implied.

## Original borrowed String reproduction (now fixed for proven borrowers)

`borrowed-call.log` records **98,890 bytes in 10,000 allocations** retained by a
read-only String parameter. The diagnostic candidate reproduces this separately
from the now-fixed struct-return leak. Minimal program:

```mapanare
fn measure(text: String) -> Int:
    let mut total: Int = 0
    for i in 0..3:
        total = total + len(text)
    return total
fn main():
    let mut total: Int = 0
    for i in 0..10000:
        let text: String = "item-" + str(i)
        total = total + measure(text)
    print(total)
```

Compile with the native compiler, link the resulting LLVM with clang
`-O1 -g -fsanitize=address -no-pie` and `libmapanare_rt.a`, then run with
`ASAN_OPTIONS=detect_leaks=1:halt_on_error=1`. The baseline caller cleared ownership
for every user call, while this callee only borrowed the String. The new proof
keeps ownership in this caller. Blanket callee frees or blanket removal of caller
transfers can still break captured aliases and were not used.

## Next steps

1. Reproduce nested container and map retention, then design recursive cleanup
   together with COW cloning/mutation. A deep free alone is unsafe for shared
   element pointers. Add tests for aliases, detach, overwrite, removal, and return.
2. Extend the borrowing/capture contract beyond the initial proof. Unknown calls
   must remain conservative; track per-argument capture and forwarding only when
   justified by MIR evidence. Keep all leak and captured-alias regressions passing.
3. Establish a repeated-workload memory gate covering these paths before marking
   priority 2 complete. Keep exact compiler self-hosting as a required regression.

## Commands and impact review

Run executable checks in Ubuntu WSL from the repository root:

```bash
.venv/bin/python -m pytest tests/integration/test_native_string_argument_borrow.py tests/integration/test_native_value_return_cleanup.py tests/integration/test_string_return_ownership.py tests/integration/test_native_generics.py tests/integration/test_native_bool_output.py tests/integration/test_native_loop_stack.py -q
.venv/bin/python scripts/verify_fixed_point.py --keep
.venv/bin/python -m pytest tests/self_hosted/ tests/bootstrap/test_verification.py::TestPipelineIntegrity -q --tb=short
```

Set `MAPANARE_TEST_COMPILER=<candidate>` to test a retained compiler. The strict
gate accepts `--stage1 <candidate>`. Do not overwrite the preserved baseline.

GitNexus CLI impact/context cannot find native `.mn` symbols, so their risk is
UNKNOWN, not LOW. Manual callers: `ret_ty_is_aggregate` is called by
`emit_drop_glue`; return emission invokes cleanup for all native functions.
The new proof helper calls `find_struct_entry` and recursively checks field
types. Broad emitter risk was reported before editing. The added nested String
test's impact is LOW with zero indexed callers/processes. Run staged
`detect-changes` before each commit, and preserve unrelated AGENTS/CLAUDE/skill
edits and the untracked desktop restart plan.

Borrowing follow-up: impact returned UNKNOWN for `FnEntry`, `new_fn_entry`,
`build_internal_struct_list`, `register_all_internal_structs`, `emit_mir_call`,
`emit_mir_function`, `emit_mir_module`, and the new proof helper. Manual review:
the two function-registration paths call the factory; `emit_mir_by_kind` calls
call emission; `new_emit_state` uses the internal struct field list. `find_function`
reads entries backwards, so both registration paths must preserve the proof flag.
This affects native call emission and self-hosting broadly and was treated as
HIGH risk. The capture test's indexed impact is LOW, zero callers/processes.

`precommit-value-return.log`: five staged files, five indexed symbols, zero
affected processes, LOW. New files/native symbols were reviewed manually because
they were not yet indexed. The first post-commit incremental refresh failed in
GitNexus with `LOWER: Invalid UTF-8` (`reindex-value-return.log`). Use a single
Windows writer and recover with
`npx --offline gitnexus analyze --force --embeddings 1 --index-only`:
rebuild the graph, retain cached embeddings, and cap new embedding generation
to bypass the previously observed duplicate-key bug. Check `.gitnexus/meta.json`
for the latest HEAD and a nonzero embedding count after completion.
