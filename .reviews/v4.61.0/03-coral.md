# Coral — Language Design Review (v4.61.0)

Grade: 9/10
Verdict: PASS WITH NOTES

## Findings

1. **LANGUAGE SURFACE PRESERVED** — Grammar, semantic rules, and LLVM backend untouched. No .mn program that compiled in v4.56.0 breaks in v4.60.0.

2. **MIGRATION GUIDES THOROUGH** — v4.57-to-v4.58.md covers every CLI flag, API surface, FAQ, timeline. v4.58-to-v4.59.md appropriately shorter. Both cross-linked from CHANGELOG.

3. **24 DORMANT HAS_LLVMLITE GUARDS** — Future contributor encountering these sees dead conditional scaffolding. Tracking item would be prudent.

4. **REPL REMOVAL UNDERSPECIFIED** — Migration story for interactive users is "use a file." No forward pointer to replacement tracking.

5. **BATCH DATESTAMP** — All four releases share 2026-04-12. Cosmetically odd but functionally irrelevant.
