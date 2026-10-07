# Container ownership: evidence and implementation sequence

This is the next-step design for priority 2, based on the 2026-10-07 probes.
Only the empty nested-buffer retain is implemented in this milestone. The
element ownership changes below are proposed work, not runtime guarantees.

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

1. **Add an explicit owned-element runtime contract.** Preserve generic raw-byte
   APIs for borrowed callers. Owned containers need element copy/retain and
   destruction operations attached to the backing allocation, with a policy
   for empty containers as well. Element size alone cannot identify Strings,
   lists, or structs. Define descriptor lifetime and the native ABI before
   implementing it; do not infer types by inspecting arbitrary pointers.
2. **Make all mutations obey that contract.** A shared list buffer owns its
   elements once; shallow handle clones retain the buffer. Detach copies or
   retains elements into the new buffer before releasing the old reference.
   Only the last buffer owner destroys elements. Growth transfers storage;
   concat creates independently owned elements. Replacement copies the incoming
   value before dropping the old one, including self-aliasing input. Clear
   drops live elements; pop transfers one element to its caller. Map insertion,
   replacement, deletion, growth, and final destruction need the same rules.
   Equal-key replacement must release any unused copied key. Rehash must move
   existing ownership without double cloning or dropping it.
3. **Integrate lowering and both emitters together.** Native `emit_drop_glue`
   currently calls shallow `__mn_list_free`; map ownership is not tracked there.
   Container insertion also emits Move markers. If insertion becomes copy-in,
   remove the matching transfer markers so caller cleanup still runs. Track
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
