---
severity: high
found: "[[v4.106.0]]"
fixed: ""
status: open
tags: [bug, high, runtime, memory, use-after-free, list]
---

# List Free Use-After-Free

`__mn_list_free` frees the backing buffer of a list, but when multiple list values share the same buffer (via assignment, parameter passing, or return), the first free invalidates the buffer while other references continue to access it. Subsequent reads or writes through the aliased references produce heap use-after-free, detectable under AddressSanitizer.

## Root Cause
Lists use a flat `{ptr, i64, i64}` representation (data pointer, length, capacity) with no reference counting or copy-on-write semantics on the backing buffer. When a list is assigned to another variable, only the struct is copied (shallow copy), so both variables point to the same heap allocation. Freeing one invalidates both.

## Fix
**OPEN.** Requires either reference counting on list buffers or copy-on-write semantics with a shared refcount header. The [[string-concat-perf]] COW approach from v3.13.0 is the likely model. Workaround: avoid explicit free on lists that may be aliased.
