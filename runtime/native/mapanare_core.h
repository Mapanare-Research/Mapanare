/**
 * mapanare_core.h — Core runtime for the Mapanare self-hosted compiler.
 *
 * Provides fundamental data type operations that native-compiled Mapanare
 * programs link against:
 *   - MnString: heap-allocated, length-prefixed strings
 *   - MnList:   type-erased growable arrays
 *   - File I/O: read source files
 *   - Memory:   alloc/free wrappers
 *
 * All functions use the __mn_ prefix to avoid collisions.
 * Strings are the Mapanare { i8*, i64 } struct passed by value.
 */

#ifndef MAPANARE_CORE_H
#define MAPANARE_CORE_H

#include <stdint.h>
#include <stddef.h>

#ifdef _WIN32
  #define MN_EXPORT __declspec(dllexport)
#else
  #define MN_EXPORT __attribute__((visibility("default")))
#endif

/* -----------------------------------------------------------------------
 * MnString — matches LLVM layout { i8*, i64 }
 *
 * The data pointer is heap-allocated (or points to a global constant).
 * Length does NOT include a null terminator, but we always allocate
 * one extra byte and null-terminate for C interop convenience.
 * ----------------------------------------------------------------------- */

typedef struct {
    const char *data;
    int64_t     len;
} MnString;

/** Create a string from a C string (copies the data). */
MN_EXPORT MnString __mn_str_from_cstr(const char *cstr);

/** Create a string from data + length (copies the data). */
MN_EXPORT MnString __mn_str_from_parts(const char *data, int64_t len);

/** Create an empty string. */
MN_EXPORT MnString __mn_str_empty(void);

/** Concatenate two strings. Returns a new heap-allocated string. */
MN_EXPORT MnString __mn_str_concat(MnString a, MnString b);

/** Get the character at index `i` as a single-character string.
 *  Returns empty string if out of bounds. */
MN_EXPORT MnString __mn_str_char_at(MnString s, int64_t i);

/** Get the raw byte value at index `i`. Returns -1 if out of bounds. */
MN_EXPORT int64_t __mn_str_byte_at(MnString s, int64_t i);

/** String length. */
MN_EXPORT int64_t __mn_str_len(MnString s);

/** String equality. Returns 1 if equal, 0 otherwise. */
MN_EXPORT int64_t __mn_str_eq(MnString a, MnString b);

/** String comparison (lexicographic). Returns <0, 0, or >0. */
MN_EXPORT int64_t __mn_str_cmp(MnString a, MnString b);

/** Substring from `start` (inclusive) to `end` (exclusive).
 *  Clamps to valid range. */
MN_EXPORT MnString __mn_str_substr(MnString s, int64_t start, int64_t end);

/** Returns 1 if `s` starts with `prefix`. */
MN_EXPORT int64_t __mn_str_starts_with(MnString s, MnString prefix);

/** Returns 1 if `s` ends with `suffix`. */
MN_EXPORT int64_t __mn_str_ends_with(MnString s, MnString suffix);

/** Find first occurrence of `needle` in `haystack`. Returns index or -1. */
MN_EXPORT int64_t __mn_str_find(MnString haystack, MnString needle);

/** Returns 1 if `haystack` contains `needle`, 0 otherwise. */
MN_EXPORT int64_t __mn_str_contains(MnString haystack, MnString needle);

/** Trim whitespace from both ends. */
MN_EXPORT MnString __mn_str_trim(MnString s);

/** Trim whitespace from the start. */
MN_EXPORT MnString __mn_str_trim_start(MnString s);

/** Trim whitespace from the end. */
MN_EXPORT MnString __mn_str_trim_end(MnString s);

/** Convert all ASCII lowercase to uppercase. */
MN_EXPORT MnString __mn_str_to_upper(MnString s);

/** Convert all ASCII uppercase to lowercase. */
MN_EXPORT MnString __mn_str_to_lower(MnString s);

/** Replace all occurrences of `old_s` with `new_s`. */
MN_EXPORT MnString __mn_str_replace(MnString s, MnString old_s, MnString new_s);

/** Convert a boolean (0/1) to "true" or "false". */
MN_EXPORT MnString __mn_str_from_bool(int64_t value);

/** Convert an i64 to its decimal string representation. */
MN_EXPORT MnString __mn_str_from_int(int64_t value);

/** Convert a double to its string representation. */
MN_EXPORT MnString __mn_str_from_float(double value);

/** Parse a string to an integer. Handles decimal, 0x hex, 0b binary, 0o octal. */
MN_EXPORT int64_t __mn_str_to_int(MnString s);

/** Parse a string to a float. */
MN_EXPORT double __mn_str_to_float(MnString s);

/** Free a heap-allocated string. No-op for constant strings.
 *  Uses tag bit (LSB of data pointer) to distinguish heap from constant. */
MN_EXPORT void __mn_str_free(MnString s);

/** Print a string to stdout (no newline). */
MN_EXPORT void __mn_str_print(MnString s);

/** Print a string to stdout with newline. */
MN_EXPORT void __mn_str_println(MnString s);

/** Print a string to stderr with newline (for diagnostics). */
MN_EXPORT void __mn_str_eprintln(MnString s);

/* -----------------------------------------------------------------------
 * MnList — type-erased growable array
 *
 * LLVM layout: { i8*, i64, i64, i64 }
 *   - data:      pointer to heap-allocated element buffer
 *   - len:       number of elements
 *   - cap:       allocated capacity
 *   - elem_size: size of each element in bytes
 *
 * Elements are stored inline (memcpy'd). For pointer-sized elements
 * (strings, other lists), this stores them by value.
 * ----------------------------------------------------------------------- */

typedef struct MnList {
    char   *data;
    int64_t len;
    int64_t cap;
    int64_t elem_size;
} MnList;

/** Split `s` by `delim`. Returns a List<String>. */
MN_EXPORT MnList __mn_str_split(MnString s, MnString delim);

/** Create an empty list for elements of `elem_size` bytes. */
MN_EXPORT MnList __mn_list_new(int64_t elem_size);

/** Push an element (copied from `elem_ptr`) onto the end of the list. */
MN_EXPORT void __mn_list_push(MnList *list, const void *elem_ptr);

/** Get pointer to element at index `i`. Returns NULL if out of bounds. */
MN_EXPORT void *__mn_list_get(MnList *list, int64_t i);

/** Set element at index `i` (copied from `elem_ptr`). No-op if OOB. */
MN_EXPORT void __mn_list_set(MnList *list, int64_t i, const void *elem_ptr);

/** Number of elements. */
MN_EXPORT int64_t __mn_list_len(MnList *list);

/** Remove and return the last element. Caller provides buffer `out_ptr`.
 *  Returns 0 on success, -1 if empty. */
MN_EXPORT int64_t __mn_list_pop(MnList *list, void *out_ptr);

/** Clear the list (set len to 0, keep capacity). */
MN_EXPORT void __mn_list_clear(MnList *list);

/** Free the list's data buffer (does NOT free contained elements). */
MN_EXPORT void __mn_list_free(MnList *list);

/** Concatenate two lists into a new list. Both must have the same elem_size. */
MN_EXPORT MnList __mn_list_concat(MnList *a, MnList *b);

/** Free a list of strings: frees each contained string, then the buffer. */
MN_EXPORT void __mn_list_free_strings(MnList *list);

/* -----------------------------------------------------------------------
 * Convenience: MnList of MnString
 * ----------------------------------------------------------------------- */

/** Create a new list of strings. */
MN_EXPORT MnList __mn_list_str_new(void);

/** Push a string onto a string list. */
MN_EXPORT void __mn_list_str_push(MnList *list, MnString s);

/** Get string at index `i`. Returns empty string if OOB. */
MN_EXPORT MnString __mn_list_str_get(MnList *list, int64_t i);

/* -----------------------------------------------------------------------
 * File I/O
 * ----------------------------------------------------------------------- */

/** Read an entire file into a string. Returns empty string on error.
 *  The `ok` flag is set to 1 on success, 0 on failure. */
MN_EXPORT MnString __mn_file_read(MnString path, int64_t *ok);

/** Write a string to a file. Returns 0 on success, -1 on error. */
MN_EXPORT int64_t __mn_file_write(MnString path, MnString content);

/* -----------------------------------------------------------------------
 * Memory
 * ----------------------------------------------------------------------- */

/** Allocate `size` bytes, zero-initialized. Aborts on failure. */
MN_EXPORT void *__mn_alloc(int64_t size);

/** Reallocate to `new_size` bytes. Aborts on failure. */
MN_EXPORT void *__mn_realloc(void *ptr, int64_t new_size);

/** Free memory. */
MN_EXPORT void __mn_free(void *ptr);

/* -----------------------------------------------------------------------
 * Arena Allocator
 *
 * Bump allocator for scope-local temporaries. All allocations are freed
 * in one shot when the arena is destroyed. Blocks are linked together
 * and grow as needed.
 * ----------------------------------------------------------------------- */

typedef struct MnArenaBlock {
    struct MnArenaBlock *next;
    int64_t size;
    int64_t used;
    /* Flexible array member: data follows the header. */
    char data[];
} MnArenaBlock;

typedef struct {
    MnArenaBlock *head;
    int64_t default_block_size;
} MnArena;

/** Create a new arena with the given default block size. */
MN_EXPORT MnArena *mn_arena_create(int64_t block_size);

/** Allocate `size` bytes from the arena (zero-initialized). */
MN_EXPORT void *mn_arena_alloc(MnArena *arena, int64_t size);

/** Destroy the arena, freeing all blocks. */
MN_EXPORT void mn_arena_destroy(MnArena *arena);

/* -----------------------------------------------------------------------
 * Agent-Scoped Arenas (Phase 2.1 integration point)
 *
 * Each agent owns an arena tied to its lifetime. When the agent is
 * stopped or destroyed, its arena is freed in one shot. The actual
 * wiring happens in Phase 2.1 (Native Agents).
 * ----------------------------------------------------------------------- */

/** Create an arena for an agent's lifetime. */
MN_EXPORT MnArena *mn_agent_arena_create(void);

/** Destroy an agent's arena (called on agent stop/destroy). */
MN_EXPORT void mn_agent_arena_destroy(MnArena *arena);

/* -----------------------------------------------------------------------
 * MnMap — open-addressing hash table with Robin Hood hashing
 *
 * Opaque struct; all access via __mn_map_* functions.
 * Keys and values are stored inline (memcpy'd) like MnList elements.
 *
 * Key type tags select hash/equality functions:
 *   0 = Int (i64), 1 = String (MnString), 2 = Float (double)
 * ----------------------------------------------------------------------- */

/** Opaque map type — heap-allocated via __mn_map_new. */
typedef struct MnMap MnMap;

/** Opaque map iterator — heap-allocated via __mn_map_iter_new. */
typedef struct MnMapIter MnMapIter;

/** Key type tags for hash/equality function selection. */
#define MN_MAP_KEY_INT   0
#define MN_MAP_KEY_STR   1
#define MN_MAP_KEY_FLOAT 2

/** Create a new empty map. key_type: MN_MAP_KEY_INT/STR/FLOAT. */
MN_EXPORT MnMap *__mn_map_new(int64_t key_size, int64_t val_size, int64_t key_type);

/** Insert or update a key-value pair. */
MN_EXPORT void __mn_map_set(MnMap *map, const void *key, const void *val);

/** Look up a key. Returns pointer to value, or NULL if not found. */
MN_EXPORT void *__mn_map_get(MnMap *map, const void *key);

/** Delete a key. Returns 1 if deleted, 0 if not found. */
MN_EXPORT int64_t __mn_map_del(MnMap *map, const void *key);

/** Number of entries. */
MN_EXPORT int64_t __mn_map_len(MnMap *map);

/** Check if key exists. Returns 1 if present, 0 otherwise. */
MN_EXPORT int64_t __mn_map_contains(MnMap *map, const void *key);

/** Create an iterator over map entries. */
MN_EXPORT MnMapIter *__mn_map_iter_new(MnMap *map);

/** Advance iterator. Returns 1 and sets key_out/val_out, or 0 when done. */
MN_EXPORT int64_t __mn_map_iter_next(MnMapIter *iter, void **key_out, void **val_out);

/** Free the iterator (does NOT free the map). */
MN_EXPORT void __mn_map_iter_free(MnMapIter *iter);

/** Free the map and its storage. Does NOT free contained strings. */
MN_EXPORT void __mn_map_free(MnMap *map);

/* -----------------------------------------------------------------------
 * Hash functions (exposed for testing; used internally by MnMap)
 * ----------------------------------------------------------------------- */

MN_EXPORT uint64_t __mn_hash_int(const void *key);
MN_EXPORT uint64_t __mn_hash_str(const void *key);
MN_EXPORT uint64_t __mn_hash_float(const void *key);

/* -----------------------------------------------------------------------
 * MnSignal — reactive signal with dependency graph
 *
 * Signals hold a typed value and participate in a reactive dependency graph.
 * When a signal's value changes, all subscribers (dependent computed signals
 * and callbacks) are automatically notified and recomputed.
 *
 * Plain signals: created with __mn_signal_new(), updated with __mn_signal_set().
 * Computed signals: created with __mn_signal_computed(), auto-recompute on
 *   dependency change.
 *
 * Subscribers are stored as a dynamic array of signal pointers.
 * Topological propagation prevents glitches (stale reads).
 * Batching defers propagation until the outermost batch ends.
 * ----------------------------------------------------------------------- */

/** Opaque signal type — heap-allocated via __mn_signal_new. */
typedef struct MnSignal MnSignal;

/** Callback function type for signal subscriptions. */
typedef void (*MnSignalCallback)(void *value, void *user_data);

/** Computed signal function type: returns void, writes result via out_ptr. */
typedef void (*MnSignalComputeFn)(void *out_ptr, void *user_data);

/** Create a new plain signal with the given initial value.
 *  val_size is the byte size of the value type. */
MN_EXPORT MnSignal *__mn_signal_new(const void *initial_value, int64_t val_size);

/** Read the current signal value. Returns pointer to internal value storage.
 *  If called during a computed signal evaluation, registers a dependency. */
MN_EXPORT void *__mn_signal_get(MnSignal *signal);

/** Set a plain signal's value. Triggers subscriber notification. */
MN_EXPORT void __mn_signal_set(MnSignal *signal, const void *value);

/** Create a computed signal that depends on `n_deps` signals.
 *  The compute_fn is called with (out_ptr, user_data) to produce the value.
 *  deps is an array of MnSignal* that this computed signal reads. */
MN_EXPORT MnSignal *__mn_signal_computed(
    MnSignalComputeFn compute_fn,
    void *user_data,
    MnSignal **deps,
    int64_t n_deps,
    int64_t val_size
);

/** Add a dependent signal as a subscriber. When this signal changes,
 *  the subscriber will be notified (marked dirty and re-evaluated). */
MN_EXPORT void __mn_signal_subscribe(MnSignal *signal, MnSignal *subscriber);

/** Remove a subscriber from the signal's subscriber list. */
MN_EXPORT void __mn_signal_unsubscribe(MnSignal *signal, MnSignal *subscriber);

/** Register a callback to be called when the signal value changes.
 *  The callback receives a pointer to the new value and the user_data. */
MN_EXPORT void __mn_signal_on_change(MnSignal *signal, MnSignalCallback cb, void *user_data);

/** Begin a batch update. Propagation is deferred until the matching
 *  __mn_signal_batch_end() call. Batches can be nested. */
MN_EXPORT void __mn_signal_batch_begin(void);

/** End a batch update. If this is the outermost batch, triggers
 *  propagation for all signals that changed during the batch. */
MN_EXPORT void __mn_signal_batch_end(void);

/** Free a signal and its internal storage. */
MN_EXPORT void __mn_signal_free(MnSignal *signal);

/* -----------------------------------------------------------------------
 * MnStream — lazy, composable stream (iterator-based)
 *
 * Streams are lazy pipelines: operators (map, filter, take, skip) create
 * new stream nodes that compose without evaluating. Evaluation happens
 * when a terminal operation (collect, fold, next) pulls elements.
 *
 * Each stream node has a `next_fn` that produces the next element:
 *   - Returns 1 and writes to `out_ptr` if an element is available
 *   - Returns 0 when the stream is exhausted
 *
 * Function pointer types for stream operations:
 *   MapFn:    void (*)(void *out, const void *in, void *user_data)
 *   FilterFn: int64_t (*)(const void *elem, void *user_data)
 *   FoldFn:   void (*)(void *acc, const void *elem, void *user_data)
 * ----------------------------------------------------------------------- */

/** Opaque stream type — heap-allocated via __mn_stream_* functions. */
typedef struct MnStream MnStream;

/** Stream next function: returns 1 + writes out_ptr, or 0 when done. */
typedef int64_t (*MnStreamNextFn)(void *out_ptr, void *state);

/** Map function: transforms an element. */
typedef void (*MnStreamMapFn)(void *out, const void *in, void *user_data);

/** Filter predicate: returns 1 to keep, 0 to skip. */
typedef int64_t (*MnStreamFilterFn)(const void *elem, void *user_data);

/** Fold function: accumulates a value. */
typedef void (*MnStreamFoldFn)(void *acc, const void *elem, void *user_data);

/** Create a stream from a list. elem_size is the byte size of each element. */
MN_EXPORT MnStream *__mn_stream_from_list(MnList *list, int64_t elem_size);

/** Lazy map: transform each element. out_elem_size is the output element size. */
MN_EXPORT MnStream *__mn_stream_map(MnStream *source, MnStreamMapFn map_fn,
                                     void *user_data, int64_t out_elem_size);

/** Lazy filter: keep elements where pred returns 1. */
MN_EXPORT MnStream *__mn_stream_filter(MnStream *source, MnStreamFilterFn pred_fn,
                                        void *user_data);

/** Lazy take: yield at most n elements. */
MN_EXPORT MnStream *__mn_stream_take(MnStream *source, int64_t n);

/** Lazy skip: skip the first n elements. */
MN_EXPORT MnStream *__mn_stream_skip(MnStream *source, int64_t n);

/** Terminal: collect stream into a new list. */
MN_EXPORT MnList __mn_stream_collect(MnStream *stream, int64_t elem_size);

/** Terminal: fold stream into a single value.
 *  init_ptr points to the initial accumulator (copied).
 *  acc_size is the byte size of the accumulator. */
MN_EXPORT void __mn_stream_fold(MnStream *stream, void *init_ptr, int64_t acc_size,
                                 MnStreamFoldFn fold_fn, void *user_data, void *out_ptr);

/** Pull next element. Returns 1 + writes out_ptr, or 0 when done. */
MN_EXPORT int64_t __mn_stream_next(MnStream *stream, void *out_ptr);

/** Lazy bounded: apply backpressure via bounded buffer of given capacity. */
MN_EXPORT MnStream *__mn_stream_bounded(MnStream *source, int64_t capacity,
                                         int64_t elem_size);

/** Free a stream node (does NOT free upstream sources). */
MN_EXPORT void __mn_stream_free(MnStream *stream);

/* -----------------------------------------------------------------------
 * Process
 * ----------------------------------------------------------------------- */

/** Exit with status code. */
MN_EXPORT void __mn_exit(int64_t code);

/** Print an error and exit with code 1. */
MN_EXPORT void __mn_panic(MnString message);

/* -----------------------------------------------------------------------
 * Range Iterator — used by `for i in start..end` loops
 * ----------------------------------------------------------------------- */

/** Create a range iterator from start (inclusive) to end (exclusive). */
MN_EXPORT void *__range(int64_t start, int64_t end);

/** Check if the iterator has more elements. Returns 1 or 0. */
MN_EXPORT int8_t __iter_has_next(void *iter);

/** Get the next element and advance. Returns value as i8* (inttoptr). */
MN_EXPORT void *__iter_next(void *iter);

#endif /* MAPANARE_CORE_H */
