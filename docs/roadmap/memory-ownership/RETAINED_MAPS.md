# Explicit map references

The runtime now supports shared ownership of a map handle. Each constructor
starts with one reference; `__mn_map_retain` returns the same pointer and adds
one reference. Each owner must call `__mn_map_free` or `__mn_map_free_deep` once.
The final release destroys the entries and storage. Plain pointer copies remain
borrows unless explicitly retained. Retain/release accept null.

This is shared mutable identity, not an independent clone or copy-on-write map.
Mutations are visible through all handles and still invalidate element views
and active iterators. Counts are non-atomic; concurrent access and ownership
cycles remain unsupported.

Owned maps use their existing key/value drop policies on the final release.
For legacy maps, a deep-release request is remembered until the last release,
even when that last call uses shallow `free`. This preserves the obligation to
destroy transferred String fields regardless of owner destruction order.
Legacy shallow-only callers retain their previous borrowed-element behavior.

Map cursors acquire a parent reference at construction and release it at cursor
destruction. Releasing all ordinary handles therefore does not invalidate an
active cursor. Borrowed keys/values still cannot outlive all owners and cursors.
The public map type remains opaque; every map must come from its constructor.

## Runtime verification

`test_retained_maps.py` runs six lifecycle cases at C O0 and O2, each repeating
1,000 times, with ASan/UBSan/LSan. Cases cover both shallow/deep release orders,
three owners, visible mutation/replacement/deletion, growth, exact copy/drop
balance, and multiple cursors outliving handles for owned and legacy maps.
All twelve pass. Together with 31 owned-map controls and two packed-key controls,
the final runtime suite passes 45 tests. Existing map integration checks also
pass (149 combined runtime/integration tests before the final shallow-free
scan optimization, followed by the 45-test final runtime run).

Evidence: `build/memory-ownership/retained-maps/`. Compiler integration is a
separate milestone: it must prove complete alias groups, acquire a reference
before releasing an overwritten owner, and clean every remaining reference on
all returns. Uncertain captures, escaped views and returned handles need their
own transfer rules before this can be enabled generally.
