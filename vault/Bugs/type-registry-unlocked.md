---
severity: high
found: "[[v4.26.0]]"
fixed: "[[v4.28.0]]"
status: fixed
tags: [bug, high, concurrency, type-system, thread-safety]
---

# Type Registry Unlocked

The global type registry (a hash table mapping type names to type metadata) had no synchronization. Concurrent generic monomorphization from multiple agent threads could trigger simultaneous inserts, causing hash table corruption, infinite loops during lookup, or use-after-free when the table resized.

## Root Cause
The type registry was implemented as a plain hash table in the C runtime, initialized at startup and assumed to be read-only after module loading. Generic monomorphization (added in v3.8.1) inserts new types at runtime, turning the registry into a concurrent read-write data structure without any corresponding locking.

## Fix
Protected the type registry with a read-write lock: reads (lookups) take a shared lock, writes (inserts from monomorphization) take an exclusive lock. Registration during module init remains uncontended since it runs single-threaded before agents start. Fixed in v4.28.0.
