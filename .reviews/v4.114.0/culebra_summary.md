# Culebra Summary — v4.114.0

**Scan status: NOT RUN at Phase D panel.**

Rationale: `culebra scan mapanare/self/main.ll` on the v4.114.0
self-hosted compiler's emitted IR exceeds practical wall-time. The
IR is ~854,000 lines (the "main.ll" produced by Python-bootstrap
compiling `mnc_all.mn`). The same limitation blocked v4.111.0 and
v4.112.0 panels and is documented in CLAUDE.md.

What was recorded instead:

- `phase_d_journal.jsonl` — culebra milestone entries for
  v4.111.0, v4.112.0 from `.culebra-journal.jsonl` (v4.113.0
  did not add a milestone entry separately; the journal rolls
  forward release-by-release)
- `PRE_PANEL_AUDIT.md` — hand audit of the 19 load-bearing claims
  across v4.111.0-v4.113.0 SESSION_REPORTs; stands in for the
  automated findings Culebra would normally surface
- `../../docs/roadmap/v4/v4.114.0/MEASUREMENTS.md` — quantitative
  pre-panel facts
- `../../docs/roadmap/v4/v4.114.0/DOCKET_AUDIT.md` — line-by-line
  verification of all 11 v4.99.0 docket items

Panel visibility: this is a known instrumentation gap, not a
substantive gap. Reviewers who want Culebra findings should scan
the per-function IR subsets under `mapanare/self/*.ll` produced by
`ir_doctor.py snapshot` (those fit in Culebra's scanner). Opening
**Instr.1** for a future release to either (a) make Culebra
incremental or (b) provide a narrower scan target for panels.
