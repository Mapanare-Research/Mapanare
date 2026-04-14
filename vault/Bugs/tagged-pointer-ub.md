---
docket: 1
severity: critical
found: "[[v4.99.0]]"
fixed: "[[v4.100.0]]"
status: partial
tags: [bug, critical, fixed, phase-a, runtime]
---

# Tagged-Pointer UB

**Docket #1** from [[v4.99.0]] panel. Unanimous blocker.

## The Bug

`mn_tag_heap` in `runtime/native/mapanare_core.c` set bit 0 of `char*` pointers to mark heap-allocated strings. This is undefined behavior — LLVM's pointer-provenance analysis exploits it at -O2.

## The Fix ([[v4.100.0]])

Replaced bit-tagging with C bitfield in MnString:
```c
typedef struct {
    const char *data;
    uint64_t    len     : 63;
    uint64_t    is_heap : 1;
} MnString;
```

See [[ADR-001 Bitfield vs int8 for is_heap]].

## Status: Partial

The UB is structurally gone. But the output corruption the panel attributed to it turned out to be a **different bug** — confirmed by reverting all v4.100.0 changes and reproducing on pristine v4.99.0. The real corruption was [[list-indexing-bug]] (move-semantics gap in the emitter).

## Reviewers

- [[Rattler]]: confirmed LLVM exploitation at -O2
- [[Viper]]: confirmed production regression
- [[Mamba]]: estimated 3-4 hour fix (actual: ~1 hour for bitfield approach)
