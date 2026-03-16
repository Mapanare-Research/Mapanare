# Mapanare Memory Model (v1.0.0)

This document describes the ownership, allocation, and deallocation rules for every
value type in the Mapanare native runtime. It is the authoritative reference for
language implementors working on the LLVM backend and the C runtime libraries.

Source files covered:

- `runtime/native/mapanare_core.h` / `mapanare_core.c` -- strings, lists, maps, arenas, signals, streams
- `runtime/native/mapanare_runtime.h` / `mapanare_runtime.c` -- agents, ring buffers, thread pool

---

## 1. Arena Lifecycle

Arenas are bump allocators used for scope-local temporaries. All allocations within an
arena are freed in a single `mn_arena_destroy()` call -- there is no per-object free.

### Data Structures

```c
// mapanare_core.h:223-234
typedef struct MnArenaBlock {
    struct MnArenaBlock *next;
    int64_t size;
    int64_t used;
    char data[];       // flexible array member
} MnArenaBlock;

typedef struct {
    MnArenaBlock *head;
    int64_t default_block_size;
} MnArena;
```

Blocks form a singly-linked list. New blocks are prepended to `head` so the most
recent (and least-full) block is checked first.

### Creation: `mn_arena_create(block_size)` (line 85)

```c
MnArena *mn_arena_create(int64_t block_size) {
    if (block_size <= 0) block_size = 8192;
    MnArena *arena = malloc(sizeof(MnArena));
    arena->default_block_size = block_size;
    arena->head = mn_arena_block_new(block_size);  // first block allocated immediately
    return arena;
}
```

- Default block size: 8 KB for general arenas, 64 KB for agent arenas.
- The arena struct itself and every block are `malloc`-allocated.
- The first block is created eagerly (not lazily).

### Allocation: `mn_arena_alloc(arena, size)` (line 97)

```c
void *mn_arena_alloc(MnArena *arena, int64_t size) {
    size = (size + 7) & ~7;  // align to 8 bytes
    MnArenaBlock *blk = arena->head;
    if (blk->used + size > blk->size) {
        // allocate a new block, at least as large as the request
        int64_t new_size = max(arena->default_block_size, size);
        MnArenaBlock *new_blk = mn_arena_block_new(new_size);
        new_blk->next = blk;
        arena->head = new_blk;
        blk = new_blk;
    }
    void *ptr = blk->data + blk->used;
    blk->used += size;
    return ptr;  // zero-initialized (memset in mn_arena_block_new)
}
```

- All allocations are 8-byte aligned.
- Memory is zero-initialized (`memset` in `mn_arena_block_new`, line 81).
- If a single allocation exceeds the default block size, an oversized block is created.
- **You cannot free individual arena allocations.** The entire arena is freed at once.

### Destruction: `mn_arena_destroy(arena)` (line 117)

```c
void mn_arena_destroy(MnArena *arena) {
    MnArenaBlock *blk = arena->head;
    while (blk) {
        MnArenaBlock *next = blk->next;
        free(blk);
        blk = next;
    }
    free(arena);
}
```

Walks the block list and frees every block, then frees the arena struct.
There is no destructor callback for individual objects within the arena.

### Nested Arenas

The runtime does not enforce a stack discipline for arenas. Any code can create and
destroy arenas independently. In practice, the compiler emits arena creation at scope
entry and destruction at scope exit, producing a natural nesting. However, nothing
prevents an inner scope from holding a pointer into an outer arena's memory after that
outer arena is destroyed -- this is undefined behavior.

### Agent-Scoped Arenas (lines 1236-1243)

```c
MnArena *mn_agent_arena_create(void) {
    return mn_arena_create(65536);  // 64 KB default for agents
}
void mn_agent_arena_destroy(MnArena *arena) {
    mn_arena_destroy(arena);
}
```

Each agent owns an arena tied to its lifetime. When the agent is stopped or destroyed,
its arena is freed in one shot. The wiring between agent lifecycle and arena destruction
is handled by the LLVM emitter at code generation time.

---

## 2. String Ownership

### Layout

```c
// mapanare_core.h:35-38
typedef struct {
    const char *data;  // tagged pointer (bit 0 encodes ownership)
    int64_t     len;   // byte length, excludes null terminator
} MnString;
```

LLVM IR type: `{ i8*, i64 }`, passed by value (two registers on most ABIs).

### The Tag-Bit System (lines 43-64)

The lowest bit (bit 0) of the `data` pointer distinguishes heap-allocated strings from
compile-time constants:

| Bit 0 | Meaning | Source | Freeable? |
|-------|---------|--------|-----------|
| `1` | Heap-allocated | `__mn_alloc` (calloc) | Yes |
| `0` | Constant | `.rodata` / static global | No |

This works because `calloc`/`malloc` always return pointers aligned to at least 8 bytes,
so bit 0 is naturally 0. The runtime sets it to 1 after allocation:

```c
// mapanare_core.c:54-64
static inline const char *mn_tag_heap(const char *ptr) {
    return (const char *)((uintptr_t)ptr | 1);      // set bit 0
}
static inline int mn_is_heap(const char *ptr) {
    return (int)((uintptr_t)ptr & 1);                // test bit 0
}
static inline const char *mn_untag(const char *ptr) {
    return (const char *)((uintptr_t)ptr & ~(uintptr_t)1);  // clear bit 0
}
```

**Every function that reads string data must call `mn_untag()` first.** The tagged
pointer is never dereferenced directly.

### When Strings Are Heap-Allocated

Any runtime function that creates a *new* string allocates via `__mn_alloc` and tags
the result:

- `__mn_str_from_cstr(cstr)` -- copies the C string (line 132)
- `__mn_str_from_parts(data, len)` -- copies the buffer (line 148)
- `__mn_str_concat(a, b)` -- allocates for the result (line 170)
- `__mn_str_substr(s, start, end)` -- allocates a copy (line 230)
- `__mn_str_char_at(s, i)` -- allocates a 1-byte string (line 187)
- `__mn_str_trim()`, `__mn_str_to_upper()`, `__mn_str_to_lower()`, `__mn_str_replace()` -- all allocate

### When Strings Are Constants

- `__mn_str_empty()` returns `{ "", 0 }` -- pointer to a static empty string, bit 0 = 0.
- String literals in LLVM IR are emitted as `@.str.N = private unnamed_addr constant [N x i8]`.
  The `data` pointer points directly into `.rodata` with bit 0 = 0.
- `__mn_str_from_cstr(NULL)` returns `{ "", 0 }`.

### Freeing Strings: `__mn_str_free(s)` (line 431)

```c
void __mn_str_free(MnString s) {
    if (s.data && mn_is_heap(s.data)) {
        __mn_free((void *)mn_untag(s.data));
    }
}
```

- No-op for constant strings (bit 0 = 0).
- No-op for NULL data pointers.
- Frees the underlying buffer via `free()` for heap strings.

### Ownership Rules

1. **String values are passed by value** (copied as a `{i8*, i64}` struct). Multiple
   variables can hold the same `data` pointer simultaneously.
2. **The creator of a heap string is responsible for freeing it**, unless ownership is
   explicitly transferred (e.g., stored into a list or returned from a function).
3. **String operations that return new strings transfer ownership to the caller.**
   The caller must eventually free the result.
4. **`__mn_str_from_bool`** (line 415) creates heap copies of `"true"` / `"false"` via
   `__mn_str_from_cstr` -- the caller owns the result.

### Pitfall: Double Free

Since `MnString` is a value type (two words), copying the struct copies the tagged
pointer. If two variables hold the same heap pointer and both call `__mn_str_free`,
this is a double-free bug. The compiler must ensure only one owner frees.

---

## 3. Struct and Enum Ownership

### Stack Allocation (Default)

Structs and enums are stack-allocated by default. The LLVM emitter uses `alloca` for
local struct variables. Fields are stored inline within the struct's stack frame.

### Boxed Recursive Fields

Recursive types (a struct containing a field of its own type, or an enum variant
containing the parent enum type) would create infinite-sized LLVM types. The compiler
auto-detects these and **boxes** the recursive field:

```
// In the LLVM emitter (emit_llvm_mir.py, lines 295-309):
// _boxed_struct_fields: struct_name -> set of field indices
// _boxed_enum_fields:   enum_name -> set of (variant_name, field_index)
```

Boxed fields are heap-allocated via `malloc` at construction time:

```
// emit_llvm_mir.py line 2296:
// Auto-boxed recursive field: heap-allocate and store pointer
malloc_fn = self._rt_malloc()
raw_ptr = builder.call(malloc_fn, [alloc_size])
```

The struct stores an opaque `i8*` pointer to the heap-allocated field value.
Reading a boxed field requires an unbox (pointer dereference + bitcast to the actual type).

### When Structs Are Freed

- **Stack structs:** Freed automatically when the enclosing function returns (LLVM
  `alloca` cleanup).
- **Boxed fields:** The compiler does not currently emit automatic `free()` calls for
  boxed fields. This is a known limitation; v1.0.0 will require either manual cleanup
  or a drop-glue mechanism. For now, boxed recursive fields leak unless the programmer
  explicitly frees them.
- **Arena-allocated structs:** Freed when the arena is destroyed.

### Move Semantics

Mapanare uses value semantics for structs at the LLVM level. Assigning a struct copies
all fields (including any boxed pointers). This means two variables can hold the same
boxed-field pointer, creating a potential double-free risk. The current implementation
relies on arena-scoped allocation to mitigate this — when the arena is destroyed at
function exit, all allocations are freed together regardless of aliasing. A future
version may add ownership tracking or move semantics to the semantic checker.

---

## 4. List Ownership

### Layout

```c
// mapanare_core.h:137-142
typedef struct MnList {
    char   *data;       // heap-allocated element buffer
    int64_t len;        // current element count
    int64_t cap;        // allocated capacity (in elements)
    int64_t elem_size;  // byte size of each element
} MnList;
```

LLVM IR type: `{ i8*, i64, i64, i64 }`.

### Creation: `__mn_list_new(elem_size)` (line 461)

Allocates an initial buffer for 8 elements (`MN_LIST_INITIAL_CAP`):

```c
MnList __mn_list_new(int64_t elem_size) {
    MnList list;
    list.elem_size = elem_size;
    list.len = 0;
    list.cap = 8;
    list.data = (char *)__mn_alloc(list.cap * elem_size);
    return list;
}
```

### Element Storage: Inline Memcpy

Elements are stored **inline** via `memcpy`. For a `List<Int>`, each slot is 8 bytes
holding the `i64` value directly. For a `List<String>`, each slot is 16 bytes holding
the `MnString` struct `{i8*, i64}` by value.

```c
// Push (line 476)
memcpy(list->data + list->len * list->elem_size, elem_ptr, list->elem_size);

// Get (line 493) -- returns pointer into the buffer
return list->data + i * list->elem_size;

// Set (line 498)
memcpy(list->data + i * list->elem_size, elem_ptr, list->elem_size);
```

**Important:** `__mn_list_get` returns a pointer *into* the list's data buffer. This
pointer is invalidated by any subsequent push that triggers a realloc.

### Growth: `mn_list_grow()` (line 470)

```c
static void mn_list_grow(MnList *list) {
    int64_t new_cap = list->cap * 2;
    list->data = __mn_realloc(list->data, new_cap * list->elem_size);
    list->cap = new_cap;
}
```

Capacity doubles on each grow. The old buffer is freed by `realloc`.

### Freeing Lists: `__mn_list_free(list)` (line 520)

```c
void __mn_list_free(MnList *list) {
    if (list->data) {
        __mn_free(list->data);
        list->data = NULL;
    }
    list->len = 0;
    list->cap = 0;
}
```

**`__mn_list_free` does NOT free contained elements.** If the list holds strings or
other heap-allocated values, the caller must free them first. The convenience function
`__mn_list_free_strings` (line 551) handles `List<String>`:

```c
void __mn_list_free_strings(MnList *list) {
    for (int64_t i = 0; i < list->len; i++) {
        MnString *sp = (MnString *)(list->data + i * list->elem_size);
        __mn_str_free(*sp);
    }
    __mn_list_free(list);
}
```

### Ownership Rules

1. The list owns its `data` buffer. Only one `MnList` value should point to a given buffer.
2. Elements are copied in, so the caller retains its own copy after `push`.
3. For lists of heap-owning types (strings, nested lists), the list effectively holds
   shared references to the heap data. The programmer must ensure exactly one free per
   heap allocation.

---

## 5. Map Ownership

### Layout

```c
// mapanare_core.c:649-657
struct MnMap {
    char    *buckets;      // flat array of buckets
    int64_t  len;          // live entry count
    int64_t  cap;          // number of buckets (power of 2)
    int64_t  key_size;
    int64_t  val_size;
    int64_t  bucket_size;  // = 2 + key_size + val_size
    int64_t  key_type;     // MN_MAP_KEY_INT(0) / STR(1) / FLOAT(2)
};
```

`MnMap` is heap-allocated and accessed via pointer. Each bucket has the layout:

```
[ status:1 byte | psl:1 byte | key:key_size bytes | val:val_size bytes ]
```

Where `status` is one of `EMPTY(0)`, `OCCUPIED(1)`, or `TOMBSTONE(2)`, and `psl`
is the probe sequence length for Robin Hood hashing.

### Robin Hood Hashing

- Hash functions: Splitmix64 for ints/floats (lines 666-703), FNV-1a for strings (line 678).
- Load factor threshold: 75% (`MN_MAP_LOAD_FACTOR_NUM=3 / DEN=4`, line 641).
- Initial capacity: 16 buckets (line 640).
- On exceeding load factor, capacity doubles and all entries are re-inserted (line 908).
- Deletion uses tombstones (line 889), not backward shifting.

### Freeing Maps: `__mn_map_free(map)` (line 955)

```c
void __mn_map_free(MnMap *map) {
    if (map) {
        if (map->buckets) __mn_free(map->buckets);
        __mn_free(map);
    }
}
```

**`__mn_map_free` does NOT free contained strings or other heap values.** If the map
uses `MnString` keys or values, the caller must iterate and free them before calling
`__mn_map_free`. There is no `__mn_map_free_strings` convenience function (unlike lists).

### Iterator Lifecycle

```c
MnMapIter *__mn_map_iter_new(MnMap *map);   // heap-allocated
void __mn_map_iter_free(MnMapIter *iter);    // frees only the iterator, not the map
```

The iterator returns pointers directly into the map's bucket array. These pointers are
invalidated if the map is modified (insertion that triggers a grow).

---

## 6. Agent Message Passing

Agents are defined in `mapanare_runtime.h/c`. Each agent runs on its own OS thread and
communicates via lock-free SPSC ring buffers.

### SPSC Ring Buffer (lines 56-65, 213-256)

```c
typedef struct mapanare_ring_buffer {
    void**              slots;     // heap-allocated array of void* pointers
    uint32_t            capacity;  // power of 2
    uint32_t            mask;      // capacity - 1
    // cache-line padding between head and tail
    mapanare_atomic_i64 head;      // write index (producer)
    mapanare_atomic_i64 tail;      // read index (consumer)
} mapanare_ring_buffer_t;
```

- `slots` stores `void*` pointers to messages, not the messages themselves.
- Capacity is rounded up to the next power of 2 for fast modulo via bitmask.
- Head and tail are on separate cache lines to avoid false sharing.

### Ownership Transfer Rules

**`send` transfers ownership.** When a message is sent via `mapanare_agent_send`:

```c
// mapanare_runtime.c:568
int mapanare_agent_send(mapanare_agent_t *agent, void *msg) {
    int rc = mapanare_ring_push(&agent->inbox, msg);
    // ...
}
```

The `void *msg` pointer is pushed into the ring buffer. The sender must not use or free
the message after a successful send. The receiver (the agent's thread) takes ownership.

**`recv` transfers ownership to the caller.** When receiving from the outbox:

```c
// mapanare_runtime.c:578
int mapanare_agent_recv(mapanare_agent_t *agent, void **out) {
    return mapanare_ring_pop(&agent->outbox, out);
}
```

The caller receives a `void*` and is responsible for freeing it.

### What Happens Inside the Agent Thread

The agent thread (line 444) pops messages from the inbox, passes them to the handler,
and optionally pushes output messages to the outbox:

```c
void *msg = NULL;
if (mapanare_ring_pop(&agent->inbox, &msg) == 0 && msg != NULL) {
    mapanare_bp_decrement(&agent->bp);
    void *out_msg = NULL;
    int rc = agent->handler(agent->agent_data, msg, &out_msg);
    if (out_msg != NULL) {
        mapanare_ring_push(&agent->outbox, out_msg);
    }
}
```

The handler receives `msg` and may produce `out_msg`. The runtime does not free either
pointer -- the handler is responsible for managing the lifecycle of the input message
(typically by consuming it) and allocating the output message (which will be owned by
whoever calls `recv`).

### Backpressure

Each agent has a `mapanare_backpressure_t` tracker (line 128) tied to its inbox:

```c
mapanare_bp_init(&agent->bp, (int64_t)agent->inbox.capacity);
```

`mapanare_bp_increment` is called on send, `mapanare_bp_decrement` on receive. When
`pending >= capacity`, the `overloaded` flag is set. The `mapanare_agent_send` function
returns `-1` when the inbox ring buffer is full -- messages are not dropped silently.

### Agent Destruction

```c
// mapanare_runtime.c:624
void mapanare_agent_destroy(mapanare_agent_t *agent) {
    mapanare_ring_destroy(&agent->inbox);
    mapanare_ring_destroy(&agent->outbox);
    mapanare_sem_destroy(&agent->inbox_ready);
    mapanare_sem_destroy(&agent->outbox_ready);
}
```

`mapanare_agent_destroy` frees the ring buffer slot arrays and semaphores. It does
**not** free any messages remaining in the inbox or outbox. If the agent was allocated
with `mapanare_agent_new`, the caller must also `free()` the agent struct itself.

Any unprocessed messages in the inbox/outbox are leaked. The caller should drain queues
before destroying.

---

## 7. Signal Value Lifecycle

Signals are heap-allocated reactive cells with a dependency graph for automatic
propagation.

### Signal Structure (lines 976-996)

```c
struct MnSignal {
    void       *value;         // heap-allocated value buffer (val_size bytes)
    int64_t     val_size;

    MnSignal  **subscribers;   // dynamic array of dependent signals
    int64_t     sub_len, sub_cap;

    MnSignalCbEntry *callbacks;  // user-registered on_change callbacks
    int64_t          cb_len, cb_cap;

    // Computed signal support:
    MnSignalComputeFn  compute_fn;
    void              *compute_user_data;
    MnSignal         **dependencies;
    int64_t            dep_len;
    int64_t            dirty;
};
```

### Creation: `__mn_signal_new(initial_value, val_size)` (line 1015)

Allocates:
- The `MnSignal` struct itself via `__mn_alloc`
- A value buffer of `val_size` bytes (minimum 8 bytes)
- A subscriber array with initial capacity 4
- A callback array with initial capacity 8

The initial value is `memcpy`'d into the value buffer.

### Value Updates and Propagation

`__mn_signal_set(signal, value)` (line 1059):
1. Compares new value to current via `memcmp`. No-op if unchanged.
2. Copies new value into the signal's buffer via `memcpy`.
3. If batching is active, adds signal to the pending list (max 256 signals).
4. Otherwise, triggers `mn_signal_propagate()` immediately.

**The signal owns its value buffer.** The caller passes a pointer to the new value,
which is copied in. The caller retains ownership of its source.

If the value is an `MnString` (16 bytes), the signal stores the `{data, len}` struct
by value. The signal does **not** call `__mn_str_free` on the old value before
overwriting -- this means the old heap string is leaked unless the caller frees it.
This is a known limitation; the signal system operates on opaque bytes and has no
type-aware destructor.

### Computed Signal Dependencies (line 1089)

```c
MnSignal *__mn_signal_computed(compute_fn, user_data, deps, n_deps, val_size)
```

- Allocates a dependency array (`deps` pointers) and subscribes to each dependency.
- Initial evaluation happens immediately via `mn_signal_recompute()`.
- On subsequent dependency changes, the computed signal is marked dirty and lazily
  recomputed on next `__mn_signal_get()`.

Auto-tracking: if `__mn_signal_get` is called during a computed signal's evaluation
(tracked via the global `mn_signal_tracking_context`), the read signal automatically
subscribes the computed signal (line 1045).

### Freeing Signals: `__mn_signal_free(signal)` (line 1215)

```c
void __mn_signal_free(MnSignal *signal) {
    // 1. Unsubscribe from all dependencies
    for (int64_t i = 0; i < signal->dep_len; i++)
        __mn_signal_unsubscribe(signal->dependencies[i], signal);

    // 2. Free internal arrays
    if (signal->dependencies) __mn_free(signal->dependencies);
    if (signal->subscribers)  __mn_free(signal->subscribers);
    if (signal->callbacks)    __mn_free(signal->callbacks);
    if (signal->value)        __mn_free(signal->value);

    // 3. Free the signal struct
    __mn_free(signal);
}
```

**Critical:** `__mn_signal_free` frees the raw value buffer but has no type awareness.
If the value buffer contains an `MnString` with a heap-allocated data pointer, that
string data is leaked. The caller must extract and free any heap-owned values before
calling `__mn_signal_free`.

Subscriber cleanup is one-directional: `__mn_signal_free` unsubscribes the signal from
its *dependencies* (upstream), but does **not** notify its *subscribers* (downstream).
Downstream computed signals may hold dangling pointers to the freed signal. The caller
must ensure signals are freed in topological order (leaves first, roots last).

### Batching (lines 1196-1211)

```c
static int64_t mn_signal_batch_depth = 0;
static MnSignal *mn_signal_batch_pending[256];
```

`__mn_signal_batch_begin()` increments a global depth counter. Signal updates during
a batch are deferred to a static pending array (max 256 entries, duplicates suppressed).
When the outermost `__mn_signal_batch_end()` fires, all pending signals are propagated.

Batching state is global and not thread-safe. Signals are designed for single-threaded
reactive graphs within one agent or the main thread.

---

## 8. Stream Element Lifecycle

Streams are lazy, composable pipelines. No elements are allocated until a terminal
operation pulls them.

### Stream Node Structure (lines 1257-1264)

```c
struct MnStream {
    int64_t   kind;       // FROM_LIST, MAP, FILTER, TAKE, SKIP, BOUNDED
    int64_t   elem_size;  // output element size in bytes
    MnStream *source;     // upstream stream (NULL for source nodes)
    void     *state;      // kind-specific state (heap-allocated)
    void     *fn;         // function pointer (map, filter, fold)
    void     *user_data;  // closure context
};
```

### Per-Element Allocation

Most stream operations use stack-allocated buffers for intermediate elements:

```c
// _stream_map_next (line 1300)
char buf[256];  // stack buffer for input element
void *in_buf = (st->in_elem_size <= 256) ? buf : __mn_alloc(st->in_elem_size);
```

Elements up to 256 bytes use the stack; larger elements are heap-allocated per-pull
and freed immediately after use. This means **stream processing is constant-memory**
for elements <= 256 bytes.

### Backpressure: Bounded Streams (lines 1409-1456)

The `__mn_stream_bounded(source, capacity, elem_size)` node inserts a circular buffer:

```c
typedef struct {
    char   *buffer;       // heap-allocated circular buffer
    int64_t capacity;
    int64_t head, tail, count;
    int64_t source_done;
} MnStreamBoundedState;
```

The buffer is allocated once at stream creation: `capacity * elem_size` bytes. Elements
are `memcpy`'d into and out of the circular buffer. This caps memory usage at
`capacity * elem_size` regardless of the source stream's length.

### Terminal Operations

**Collect** (`__mn_stream_collect`, line 1474): Creates a new `MnList` and pushes each
element from the stream. The resulting list owns all element data. The stream nodes
are not automatically freed.

**Fold** (`__mn_stream_fold`, line 1487): Iterates the stream, accumulating into a
caller-provided buffer. No heap allocation beyond the per-element temp buffer.

### Freeing Streams: `__mn_stream_free(stream)` (line 1501)

```c
void __mn_stream_free(MnStream *stream) {
    if (stream->kind == MN_STREAM_BOUNDED) {
        MnStreamBoundedState *st = stream->state;
        __mn_free(st->buffer);  // free circular buffer
        __mn_free(st);
    } else if (stream->state) {
        __mn_free(stream->state);
    }
    __mn_free(stream);
}
```

**`__mn_stream_free` does NOT free upstream sources.** Stream pipelines form a linked
list via the `source` pointer. To free an entire pipeline, the caller must walk the
chain and free each node individually, starting from the terminal and working upstream.

If the stream holds references to a source `MnList` (via `__mn_stream_from_list`), the
list is not freed -- the stream merely holds a pointer.

---

## 9. Closure Environment Lifecycle

Closures are represented as a two-word struct in LLVM IR:

```llvm
%closure = type { i8*, i8* }   ; { fn_ptr, env_ptr }
```

### Environment Allocation

When a closure captures free variables, the LLVM emitter allocates an environment
struct on the heap via `__mn_alloc`:

```
// emit_llvm_mir.py line 3143-3147
env_struct_ty = ir.LiteralStructType(cap_llvm_types)
alloc_fn = __mn_alloc
env_raw = builder.call(alloc_fn, [size_of(env_struct_ty)])
```

Each captured variable is `memcpy`'d (or stored via GEP) into the environment struct.
The environment pointer is stored as `i8*` in the closure struct.

### When Captured Variables Are Freed

The runtime does **not** automatically free closure environments. There is no reference
counting or drop glue for closure env pointers. The environment lives until:

1. The enclosing scope explicitly frees it (not currently emitted by the compiler), or
2. The program exits.

This means closures that escape their defining scope (e.g., stored in a list, returned
from a function) will leak their environment. This is a known limitation targeted for
resolution in v1.0.0's formal memory model.

### Closures With No Captures

If a closure captures no free variables, the environment pointer is `null`. No heap
allocation occurs:

```
// emit_llvm_mir.py line 3135
closure = { fn_ptr, null }
```

### Escape Analysis

The compiler does not currently perform escape analysis on closures. All closures with
captures are heap-allocated. A future optimization (v1.0.0+) could stack-allocate
environments for closures that provably do not escape their defining scope.

---

## 10. General Memory Helpers

### `__mn_alloc(size)` (line 19)

```c
void *__mn_alloc(int64_t size) {
    void *ptr = calloc(1, (size_t)size);
    if (!ptr) { fprintf(stderr, "..."); exit(1); }
    return ptr;
}
```

- Zero-initializes all memory (via `calloc`).
- Aborts the process on allocation failure -- there is no recoverable OOM path.

### `__mn_realloc(ptr, new_size)` (line 29)

- Aborts on failure.
- Does not zero-initialize the newly extended region (standard `realloc` behavior).

### `__mn_free(ptr)` (line 39)

- Direct wrapper around `free()`.
- Safe to call with NULL.

---

## 11. Range Iterator

```c
// mapanare_core.c:1540-1566
typedef struct { int64_t current; int64_t end; } MnRangeIter;
```

Range iterators are heap-allocated via `malloc` (not `__mn_alloc`). They are **not
automatically freed** -- the compiler must emit a `free()` call after the loop exits.
If the loop body contains a `break` or `return`, the iterator may leak.

---

## Summary: What Is and Is Not Automatically Freed

| Type | Allocation | Automatic Cleanup? | Notes |
|------|------------|-------------------|-------|
| Arena contents | Bump alloc | Yes, on `mn_arena_destroy` | Entire arena freed at once |
| Strings (constant) | `.rodata` | N/A | Never freed |
| Strings (heap) | `__mn_alloc` | No | Must call `__mn_str_free` |
| Lists | `__mn_alloc` | No | Must call `__mn_list_free` |
| List elements | Inline `memcpy` | No | Must free contained heap values first |
| Maps | `__mn_alloc` | No | Must call `__mn_map_free` |
| Map keys/values | Inline `memcpy` | No | Must free contained heap values first |
| Signals | `__mn_alloc` | No | Must call `__mn_signal_free` |
| Signal values | `__mn_alloc` | Partially | Buffer freed, but not typed contents |
| Streams | `__mn_alloc` | No | Must call `__mn_stream_free` per node |
| Closure envs | `__mn_alloc` | No | Leaked in current implementation |
| Boxed fields | `malloc` | No | Leaked in current implementation |
| Agent queues | `calloc` | On `mapanare_agent_destroy` | Remaining messages leaked |
| Range iterators | `malloc` | No | Compiler must emit `free` |

---

## Future Work (v1.0.0 Formal Memory Model)

1. **Drop glue:** Compiler-generated destructors for types containing heap-allocated
   fields (strings in structs, nested lists, closure environments).
2. **Affine/linear types:** Enforce single-ownership at the type system level to prevent
   double-free and use-after-free without runtime cost.
3. **Escape analysis for closures:** Stack-allocate non-escaping closure environments.
4. **Agent arena integration:** Wire arena destruction into `mapanare_agent_destroy` so
   all agent-scoped allocations are freed automatically.
5. **Signal type-aware cleanup:** Register destructor callbacks per signal so that string
   and struct values are properly freed on signal destruction.
6. **Drain-on-destroy for agent queues:** Iterate and free all remaining messages in
   inbox/outbox during `mapanare_agent_destroy`.
