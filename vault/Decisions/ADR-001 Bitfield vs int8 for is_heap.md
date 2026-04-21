---
decision: ADR-001
date: 2026-04-13
version: "[[v4.100.0]]"
status: accepted
tags: [decision, runtime, abi]
---

# ADR-001: Bitfield vs int8_t for MnString is_heap

## Context

v4.99.0 panel prescribed replacing `mn_tag_heap` (bit-tagging on `char*`) with an `int8_t is_heap` field. During implementation, adding `int8_t` grew MnString from 16 to 24 bytes, crossing the SysV AMD64 16-byte register-passing boundary. Every call site would need sret/byval rewrite.

## Options Considered

1. **int8_t is_heap** — grows struct to 24 bytes, breaks ABI at every call site
2. **C bitfield** — `uint64_t len:63; uint64_t is_heap:1` keeps struct at 16 bytes

## Decision

Option 2 (bitfield). The data pointer is now always valid (no UB). The heap flag rides in the integer's high bit where LLVM can't exploit it for pointer provenance. ABI unchanged.

## Consequences

- LLVM IR still sees `{ ptr, i64 }` — must mask bit 63 when reading `.len`
- Self-hosted emitter adds `and i64 %raw, 0x7FFFFFFFFFFFFFFF` after extractvalue
- No sret/byval rewrite needed across the codebase
- Confirmed with minimal repro: 24-byte MnString segfaulted on return
