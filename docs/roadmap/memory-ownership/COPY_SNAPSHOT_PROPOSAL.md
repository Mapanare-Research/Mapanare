# Copy snapshot correction

Status: implemented under the user's full integration authorization.
The map emitter integration's rotating-alias test previously
returned `4756` at O0/O1 but the wrong value `4853` at O2/O3. The root cause was
`copy_propagation` replacing a copied snapshot with a source that can change.
Three new standalone MIR regression cases fail before the fix; a stable-source
control passes. Evidence: `build/memory-ownership/retained-map-emitter/copy-baseline.log`.

## Implemented change

The correction changes only `mapanare/mir_opt.py::copy_propagation`:

1. Seed definition counts with one definition for each parameter, so assigning
   to a parameter counts as reassignment.
2. Use the existing `_build_cfg` helper and reachability to identify blocks that
   can reach themselves. Mark values defined in these blocks as cyclic sources:
   a single source instruction can produce different values on different visits.
3. Add these conditions to candidate selection: the source has at most one
   definition, is not a field/index mutation target, and is not a cyclic source.
   Keep the existing destination checks and replacement machinery unchanged.

The resulting eligibility condition is:

```python
if (
    def_counts.get(inst.dest.name, 0) <= 1
    and def_counts.get(inst.src.name, 0) <= 1
    and inst.dest.name not in mutated_names
    and inst.src.name not in mutated_names
    and inst.src.name not in cyclic_defs
):
    copy_map[inst.dest.name] = inst.src
```

This preserves snapshots conservatively; it can reduce optimization of loop
copies until a stronger reaching-definition proof is implemented. GitNexus
rates the optimizer CRITICAL: one direct caller, ten reachable symbols and
eleven affected flows. All four snapshot checks and the rotating-alias output
checks now pass without changing expected output. The targeted run passes 225
checks. Broad-suite results and strict self-hosting evidence are recorded in
[WORK_LOG.md](WORK_LOG.md).
