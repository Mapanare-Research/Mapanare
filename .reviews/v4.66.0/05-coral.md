# Coral — Language Design Review (v4.66.0)

Grade: 9/10
Verdict: PASS

## Findings
1. **DW_LANG_C99 sound for MVP** — avoids demangling. Forward pointer to revisit noted.
2. **Zero user-facing language change** — DWARF is emitter-side only, gated behind -g.
3. **Incremental slice model** — 4-release arc matches release discipline.
4. **DWARFv5 forward-looking** — better variant-part support for future enum debugging.
5. **DW_LANG_C99 vs Mapanare semantics gap** — honest, tracked for future consideration.
