# Rattler — LLVM/DWARF Review (v4.66.0, PRIMARY)

Grade: 9/10
Verdict: PASS WITH NOTES

## Findings

1. **DWARF STRUCTURE SOUND** — DICompileUnit, DISubprogram, DILocation, DILocalVariable all well-formed. Metadata numbering via counter avoids collisions.

2. **OPTION C VALIDATED** — Recomputing from Span at emission time keeps MIR clean. The _L() hook is minimal-surface and covers all instructions without individual handler changes.

3. **DWARFv5 + FULL DEBUG** — Correct choice. emissionKind: FullDebug prepares for variable inspection. DW_LANG_C99 avoids demangling issues.

4. **SELF-HOSTED MIRROR GAP** — Python-side DWARF emission works. Self-hosted emitter (emit_llvm.mn) does not mirror the DWARF methods. Dual-closure convention not applied to A2.

5. **ENUM TYPE MVP ACCEPTABLE** — Plain DW_TAG_structure_type for enums is honest. Full DW_TAG_variant_part deferred to v5.x with documented tracking.
