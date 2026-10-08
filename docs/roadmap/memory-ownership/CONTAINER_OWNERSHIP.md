# Container ownership: evidence and implementation sequence

This is the next-step design for priority 2, based on the 2026-10-07 probes.
The empty nested-buffer retain and opt-in owned-list/map runtime contracts are
implemented. Compiler adoption remains open; existing native programs still use
raw containers and retain the leaks recorded below.

## Implemented: opt-in owned lists

`__mn_list_new_owned(elem_size, ops)` accepts `MnElementOps` copy/drop callbacks;
`__mn_list_str_new_owned()` supplies the String policy. The callback pair is copied
into an aligned backing header, so a stack-allocated descriptor is safe. Callback
code must outlive the list. The public five-field `MnList` layout is unchanged.
The internal management tag selects the owned header; legacy buffers retain their
original format. Empty owned lists allocate a buffer to preserve their policy.

The ordinary list API then follows these rules:

| Operation | Owned-list behavior |
|---|---|
| Push/set | Copy borrowed input before detach/growth/destruction; caller retains its input |
| Get | Borrow read-only storage, including nested fields; mutation/free can invalidate it |
| Clone | Retain the shared buffer without duplicating elements |
| Detach | Construct independently owned element copies, then release the old reference |
| Grow | Transfer storage without copying/dropping existing elements |
| Deep clone | Detach the outer buffer using its policy; callbacks handle nested fields instead of the offset array |
| Clear | Drop live elements and retain an empty buffer with its policy |
| Pop | Transfer one owned element to non-aliasing caller storage |
| Free | Drop elements only when releasing the last buffer reference |
| Concat | Independently copy elements; both lists must have equal sizes and callback pairs |

Raw/owned or incompatible-policy concat aborts with a diagnostic. Callbacks must
construct an independent value in uninitialized storage, must not fail or re-enter
the same container, and support at most `max_align_t` alignment. Cyclic owning
values are unsupported. Clone owning handles rather than byte-copying them, and
replace stored values through set rather than mutating borrowed pointers.

`tests/native/fixtures/owned_lists.c` covers the former shared/detached String
failure shapes using the new API, plus self-replacement, aliased input during
growth, clear/reuse, pop lifetime, concat, empty buffers, explicit deep clone,
large aligned elements, exact callback balance, and two nested list fields.
There are 22 sanitizer lifecycle cases (1,000 iterations each) and one incompatible
concat check. The legacy failing probe modes below deliberately stay unchanged.

Compiler adoption is still required: enabling this constructor while retaining
old Move markers would leak caller inputs, and borrowed lookups must not be
mistaken for owned values. See step 3 below before switching generated programs.

## Implemented: opt-in owned maps

`__mn_map_new_owned(key_size, val_size, key_type, key_ops, val_ops)` copies
independent `MnElementOps` descriptors for keys and values. A null descriptor
means a plain value with no owned resources; a supplied descriptor must contain
both callbacks. String keys require a policy. String values and other owning
values also require a policy; a null value policy is not an inferred destructor.
`__mn_map_str_str_new_owned()` supplies both String policies.

Key sizes must match the selected Int, Float, or String representation. Callbacks
follow the list contract and must preserve key hash/equality. Callback code must
outlive the map. Both fields and temporary copies are aligned to `max_align_t`;
the opaque map layout can carry this policy without changing generated handles.

| Operation | Owned-map behavior |
|---|---|
| Set | Copy borrowed key and value before growth or destruction; caller retains inputs |
| Equal-key replacement | Keep the stored key, drop the unused copied key and old value, transfer the new value |
| Delete | Drop both stored fields exactly once and mark the slot reusable |
| Grow/rehash | Move live entries without extra callback copies or drops |
| Get/iteration | Borrow read-only storage, including nested fields, until mutation/free |
| Keys | Return an independent list with the actual key size and key ownership policy; it can outlive the map |
| Free/free_deep | Equivalent: drop every live key/value and free storage |

Owned maps use bounded linear probing with tombstones and aligned bucket offsets.
Search continues past tombstones before choosing a vacant slot, so deletion does
not introduce duplicate equal keys. Missing lookup/delete terminates even if
every bucket is a tombstone. There is no eight-bit probe-distance limit. The
legacy packed Robin Hood implementation and its raw ownership behavior remain
unchanged. These correctness choices are not a performance claim or benchmark.

Map handles remain exclusive, with no retain/clone API or concurrent access
support. Copying the handle does not create another owner. Mutation invalidates
borrows and active iterators. Cyclic owning values and callback re-entry into the
same container are unsupported. Nested-list policies can explicitly retain list
buffers and release them on replacement/deletion; the runtime never guesses
nested types from element size.

`tests/native/fixtures/owned_maps.c` covers replacement and deletion with aliased
inputs, equal keys from distinct heap allocations, growth with borrowed keys/values,
all-tombstone tables, wraparound collisions, chains exceeding 255 entries,
independent key lists, large aligned callback values, exact callback counts,
nested list fields in both destruction orders, Float zero equality, plain values
the same size as a String, and a deterministic reference model. Twenty-six lifecycle cases exercise both free
entry points; five rejection cases cover malformed constructor inputs. Most
lifecycle cases repeat 1,000 times; the long-chain and reference-model cases
repeat ten times. The pytest harness enables ASan/UBSan/LSan and also accepts
`MAPANARE_TEST_RUNTIME=runtime/native/libmapanare_rt.a` to check the exact archive.

## Fixed: allocated empty inner lists

`__mn_list_deep_clone` detached the outer buffer but retained an inner list only
when `len > 0`. Both `clear` and the last `pop` leave an allocation behind. The
new outer copy therefore held an uncounted alias; destroying either copy could
free storage still used by the survivor. Retaining every non-null inner buffer
fixes this without changing layout or destruction semantics.

The sanitizer regression runs 16 cases, each 1,000 times: fresh, cleared,
popped, and nonempty inner lists; either destruction order; with or without
mutation before destruction. Each outer list has three records with two list
fields at distinct offsets. The baseline had eight use-after-free failures;
the fix has zero ASan/LSan failures. This is a runtime API fix: the current
native emitter does not call `__mn_list_deep_clone`, and automatic recursive
cleanup is not enabled by this change.

## Remaining evidence

Compile the durable C probes from the repository root in Linux/WSL:

```bash
mkdir -p build/memory-ownership/nested-containers
clang -O1 -g -fsanitize=address -fno-omit-frame-pointer -no-pie \
  -I runtime/native tests/native/fixtures/container_ownership.c \
  runtime/native/mapanare_core.c -lm -lpthread \
  -o build/memory-ownership/nested-containers/probe
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 \
  build/memory-ownership/nested-containers/probe deep-clone 1 0 0
```

Replace the final arguments with the modes below to reproduce the remaining
gaps. These modes intentionally fail under sanitizers. They are diagnosis
fixtures, not passing CI checks or xfailed tests. Their results are recorded in
`build/memory-ownership/nested-containers/baseline-probes.json` and separate logs.

| Mode | Observed result | Missing contract |
|---|---|---|
| `shared-strings` | Use-after-free after freeing one COW alias | String destruction must belong to the shared buffer's last owner |
| `detached-strings` | Use-after-free after mutation detaches a shared list | Detach must establish independent element ownership before either copy destroys elements |
| `nested-retention` | 80,000 bytes / 1,000 allocations leaked | Shallow outer cleanup does not release inner buffers |
| `map-overwrite` | 9,990 bytes / 1,998 allocations leaked | Adopting inserted strings and later deep-freeing cannot recover replaced values or unused equal keys |
| `map-delete` | 10,000 bytes / 2,000 allocations leaked | Deleted entries disappear before deep-free can release their strings |

The generic C APIs currently copy raw bytes. Their callers can also supply
borrowed data, so blindly freeing elements during set/delete would break valid
borrowed usage. These probes demonstrate that transfer followed by deep-free
is insufficient; they do not establish permission to free every generic input.

Native Mapanare programs independently reproduce retention. Save either program,
emit LLVM with `mapanare/self/mnc-stage1 emit-llvm <file>`, link with clang
`-O1 -g -fsanitize=address -no-pie`, `runtime/native/libmapanare_rt.a`,
`-lm -lpthread -ldl`, and run with the ASAN_OPTIONS above.

Nested lists: expected stdout `42000`; observed 415,584 bytes in 1,998
allocations retained (`nested-native.log`).

```mapanare
fn count(n: Int) -> Int:
    let mut inner: List<Int> = []
    inner.push(n)
    let mut outer: List<List<Int>> = []
    outer.push(inner)
    return outer[0][0]
fn main():
    let mut total: Int = 0
    for i in 0..1000:
        total = total + count(42)
    print(total)
```

Map replacement: expected stdout `6000`; observed 638,000 bytes in 6,000
allocations retained (`map-native.log`).

```mapanare
fn count(n: Int) -> Int:
    let mut values: Map<String, String> = #{"key": "first-" + str(n)}
    for i in 0..3:
        values["key"] = "next-" + str(i)
    return len(values["key"])
fn main():
    let mut total: Int = 0
    for i in 0..1000:
        total = total + count(42)
    print(total)
```

## Implementation sequence

1. **Owned-list and map runtime contracts implemented.** Preserve generic raw-byte
   APIs for borrowed callers. Maps carry key and value policies independently.
   Element size alone cannot identify
   Strings, lists, or structs; do not infer types by inspecting arbitrary pointers.
2. **List and map mutations implemented.** A shared list buffer owns its
   elements once; shallow handle clones retain the buffer. Detach copies or
   retains elements into the new buffer before releasing the old reference.
   Only the last buffer owner destroys elements. Growth transfers storage;
   concat creates independently owned elements. Replacement copies the incoming
   value before dropping the old one, including self-aliasing input. Clear
   drops live elements; pop transfers one element to its caller. Map insertion,
   replacement, deletion, growth, and final destruction follow the same rules.
   Equal-key replacement releases any unused copied key. Rehash moves
   existing ownership without double cloning or dropping it.
3. **Integrate lowering and both emitters together.** Native `emit_drop_glue`
   currently calls shallow `__mn_list_free`; map ownership is not tracked there.
   Container insertion also emits Move markers. If insertion becomes copy-in,
   remove the matching transfer markers so caller cleanup still runs. Track
   container handle copies/arguments/returns with explicit retain/transfer rules;
   a raw copy of an owned handle does not acquire another buffer reference. Track
   returned containers and popped values, and distinguish borrowed lookup results
   from owned copies before tracking String results. Start with `List<String>`,
   `List<List<Int>>`, and String-key/value maps; fail conservatively on unsupported
   type graphs. Preserve captured aliases and heap-bearing return controls.
4. **Promote the probes into passing regression gates.** Cover both alias-free
   orders, detach/set/grow/concat/clear/pop, the same input inserted twice, borrowed
   literals and heap strings, returned lookups, equal keys from distinct heap
   buffers, map deletion and rehash, and multiple nested fields. Verify both
   correct output and zero invalid accesses/leaks over repeated workloads. Keep
   strict compiler self-hosting as a required check before promotion.

Do not fix `__mn_list_free_strings` only by checking the outer refcount: the
detached-string probe would still double-own the same inner pointers. Likewise,
enabling recursive native drops before defining copying and capture semantics
can turn today's leaks into use-after-free failures.
