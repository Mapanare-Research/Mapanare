# RFC 0002: Memory Management Strategy (Arena + RC Hybrid)

- **Status:** Accepted
- **Phase:** v0.3.0 / Phase 1.1
- **Author:** Mapanare team
- **Date:** 2026-03-09

## Summary

Replace the current no-op `__mn_str_free` with a working memory management
strategy based on **arena allocation** for scope-local values and
**reference counting** for cross-scope values (future extension).

## Motivation

The LLVM backend leaks every heap-allocated string. `__mn_str_free` is a
no-op because it cannot distinguish heap pointers from constant pointers
in `.rodata`. Any program that runs longer than a benchmark exhausts memory.

This was cited as a critical issue by 6 of 7 reviewers of v0.2.0.

## Design

### 1. Tag Bit for Heap vs Constant Strings

All heap-allocated `MnString` values embed a **tag bit** in the pointer's
lowest bit (which is always 0 for aligned allocations):

- `tag = 0` → constant string (points into `.rodata` or static global)
- `tag = 1` → heap-allocated string (safe to free)

Runtime string functions (`__mn_str_from_parts`, `__mn_str_concat`, etc.)
set the tag bit on all heap-allocated returns. `__mn_str_free` checks the
tag bit before freeing.

This is a minimal, zero-overhead approach: tagging costs one OR instruction
at allocation and one AND + test at free.

### 2. Arena Allocator

An `MnArena` is a bump allocator that owns a linked list of memory blocks:

```c
typedef struct MnArenaBlock {
    struct MnArenaBlock *next;
    int64_t size;
    int64_t used;
    char data[];  // flexible array member
} MnArenaBlock;

typedef struct {
    MnArenaBlock *head;
    int64_t default_block_size;
} MnArena;
```

API:
- `mn_arena_create(block_size)` — create a new arena
- `mn_arena_alloc(arena, size)` — bump-allocate from current block
- `mn_arena_destroy(arena)` — free all blocks in one shot

### 3. Scope-Based Arena Insertion (emit_llvm.py)

The LLVM emitter inserts arena lifecycle calls at function boundaries:

- **Function entry:** `%arena = call @mn_arena_create(8192)`
- **Function exit:** `call @mn_arena_destroy(%arena)` (before every `ret`)

Heap-allocated temporaries (string concat results, substrings, int-to-string
conversions) are allocated from the function arena instead of raw `calloc`.

Return values are **copied out** of the arena before destruction if they
escape the function scope.

### 4. Agent-Scoped Arenas (Future)

Each agent will own an arena tied to its lifetime. When an agent is stopped
or garbage-collected, its arena is destroyed in one shot. This is deferred
until Phase 2.1 (Native Agents) delivers the agent lifecycle in the LLVM
backend.

### 5. List Element Cleanup

`__mn_list_free` gains an optional element destructor callback. For
`List<String>`, the list free function iterates elements and calls
`__mn_str_free` on each before freeing the data buffer.

For the initial implementation, `__mn_list_free_strings` is a dedicated
function that frees a list of strings.

### 6. Reference Counting (Deferred)

True reference counting for values that escape function scope (e.g.,
strings stored in structs that outlive the creating function) is deferred
to v0.4.0. The arena approach handles the dominant case (function-local
temporaries), which covers most leaks.

## Implementation Plan

1. Add tag bit to MnString pointer in C runtime
2. Implement arena allocator in C runtime
3. Fix `__mn_str_free` to check tag and free heap strings
4. Fix `__mn_list_free` to free contained strings
5. Emit arena create/destroy in `emit_llvm.py` at function boundaries
6. Stub agent-scoped arenas (API only, wired in Phase 2.1)
7. Stress test: 1M allocations, verify RSS bounded
8. Remove "ownership-based" claims from spec

## Alternatives Considered

- **Garbage collector:** Too much complexity for a systems language.
  Contradicts Mapanare's "no GC in native mode" principle.
- **Rust-style ownership:** Excellent long-term, but requires borrow
  checker infrastructure that doesn't exist yet. Deferred to v0.5.0+.
- **Pure reference counting:** High overhead for temporary strings
  (most allocations). Arena handles this case much better.

## Risks

- Tag bit relies on alignment guarantees (all `calloc` returns are
  at least 8-byte aligned on modern platforms). This is universally true.
- Arena-allocated strings that escape function scope without being
  copied will be use-after-free. The emitter must ensure return values
  are copied out. This is mitigated by the conservative approach of
  only arena-allocating known-temporary values initially.
