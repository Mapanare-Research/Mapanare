# Retained-map emitter integration

Status: implemented under the user's full integration authorization. The runtime is
already committed as `d82e2078`; its final 45 sanitizer lifecycle tests pass.
The connected `shared_map_aliases` analysis passes 38
tests. Baseline compilation with the unchanged emitter reproduces 36 leaks
across Python O0–O3, with four passing skipped-loop controls. The exact 40-case
integration suite is restored to `tests/integration/test_retained_map_ownership.py`.
All 40 cases are now leak-free and produce the expected output. The rotating-
alias program exposed a pre-existing O2/O3 copy-propagation error, fixed in
`ddcb8f9b`; see [COPY_SNAPSHOT_PROPOSAL.md](COPY_SNAPSHOT_PROPOSAL.md).
Four additional O0–O3 cases run 100,000 iterations, observing at most eight live
maps and zero references remaining at exit. The observer wraps real runtime
calls and all executions run with ASan/UBSan/LSan.

This records the initial integration committed as `92467283`. Follow-ups now
cover direct retained returns, consumed Map/String Phis and retained String
views. See [MAP_RETURNS.md](MAP_RETURNS.md),
[MAP_PHI_OWNERSHIP.md](MAP_PHI_OWNERSHIP.md),
[MAP_BORROWED_VIEWS.md](MAP_BORROWED_VIEWS.md), and the current
[WORK_LOG.md](WORK_LOG.md) checkpoint. The original acceptance suite remains active.

## Initial implementation scope

`mapanare/emit_llvm_text.py` imports the proof
`shared_map_aliases` from `mapanare.map_shared`. The following four existing
methods and one new helper implement the integration:

1. `_emit_fn`: compute the existing recyclable result set once, then call
   `shared_map_aliases(fn, factories, recycled)`. For each eligible value, allocate
   a private pointer slot initialized to null in the entry block. Register it
   under `_map_ref_<value>` in `_alloc` and `_map_vars`, and retain the mapping in
   `_shared_map_owners`. Then create the existing loop-owner slots unchanged.
2. `_do_copy`: before the existing `_put`, call the new helper with `borrow=True`.
   If it handles the destination, perform `_put` and return. Otherwise run the
   existing copy behavior unchanged.
3. `_do_call`: in the existing proven map-factory result branch, pass the returned
   pointer to the helper with `borrow=False`. Return when handled; otherwise
   preserve existing loop-result or legacy container tracking.
4. `_do_map_init`: skip legacy `_track_container` only for names in
   `_shared_map_owners`. After inserting all initial entries, pass the completed
   map to the helper with `borrow=False`, then run the existing `_put`.

The helper is:

```python
def _store_shared_map(self, name: str, value: str, *, borrow: bool) -> bool:
    owner = getattr(self, "_shared_map_owners", {}).get(name)
    if owner is None:
        return False
    if borrow:
        value = self._rt("__mn_map_retain", PTR, [PTR], [(value, PTR)])
    previous = self._f("map_ref_previous")
    self._L(f"{previous} = load ptr, ptr {owner}")
    self._rt("__mn_map_free_deep", VOID, [PTR], [(previous, PTR)])
    self._L(f"store ptr {value}, ptr {owner}")
    return True
```

Acquiring before release makes self-assignment safe. Fresh factory/literal
allocations transfer their initial reference into the slot. Existing return
cleanup releases every registered slot. The initial proof rejected map returns;
the later return-transfer milestone now handles them explicitly.

## Limits and required validation

Only complete local groups qualify. Parameter aliases, captured maps, mutations
and uncertain origins still reject this path. Returned maps, consumed Phis and
cursor/String views were conservative boundaries in this initial milestone and
are now covered by the linked follow-ups. Unused statement-result Phis may be ignored because their
stored pointer cannot be consumed. Literal maps admit scalars and literal
Strings; factory arguments must be scalars. Existing cheaper loop recycling
takes precedence.

GitNexus rates `_emit_fn` CRITICAL: one direct caller, nine reachable symbols,
five affected flows. The other three existing methods have LOW indexed impact.
Incorrect integration could cause widespread premature frees or leaks. Before
committing, run the 40 new executable cases, retained-view guards, broad LLVM/MIR
and ownership suites, and strict self-hosting. Update any existing retained-map
guard to require leak freedom only after proving it is eligible and passing.
The targeted suite passes 225 tests. Broad-suite and strict self-hosting results
are recorded in [WORK_LOG.md](WORK_LOG.md). Expected outputs and sanitizer
checks remain intact.
