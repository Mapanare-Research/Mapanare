# Viper — v5.47.5 Closeout Panel Findings

**Reviewer axis:** Performance + benchmarks + runtime footprint
**Arc reviewed:** v5.31.0 → v5.47.0 (17 releases)
**Audit reference:** `.reviews/v5.47.5/PRE_PANEL_AUDIT.md`
**Prior-panel score:** 9.80 (v5.28.0 RE-PANEL)

---

## Summary

Performance discipline across the arc was substantively
honest — when a release shipped copy semantics where
aliasing would have been faster (v5.41.0 Ts.1) or the
flat-tuple workaround where Result<T, NetworkError> would
have been more ergonomic (v5.43.0 Da.\*), the trade-off
was documented in the source preamble + SESSION_REPORT,
not hidden behind a perf claim.

The single most important perf-shaping decision in the
arc was **v5.45.0 Ts.2.B reshape semantic swap** — the
LLVM `noalias` attribute drops because it would be a lie
under aliasing. This is the right correctness-over-perf
trade and is documented exhaustively in the cookbook.

Runtime footprint grew predictably: `mapanare_agent_t`
488→984 bytes at v5.42.0 (As.6 append-only extension);
`mapanare_tensor_t` 40→64 bytes at v5.45.0 (Ts.2.A
refcount + view metadata). Both extensions are append-only
and pinned by binary-compat regression tests.

---

## Per-category grades

### Append-only struct discipline

**Grade: EXCEEDS**

`mapanare_agent_t` (v5.42.0) and `mapanare_tensor_t`
(v5.45.0) both extended without breaking pre-v5.42.0 /
pre-v5.45.0 binaries. Field offsets locked by regression
tests (`tests/runtime/test_agent_struct_compat.py`,
`tests/runtime/test_tensor_struct_compat.py`). The v5.45.0
+24-vs-+16-byte deviation (Phase 0 surfaced 8-byte alignment
padding the PROMPT/PLAN missed) was load-bearing detail
that the existing test infrastructure caught — exactly
what binary-compat tests are for.

### Network protocol footprint

**Grade: EXCEEDS**

v5.43.0 Da.\* wire-format v1 is well-engineered:
- 100MB DoS guard (caps single-frame allocation)
- Length-prefixed BE u32 length / u8 version / u8 msg_type /
  u64 BE seq / 16-byte HMAC-SHA256 truncation / JSON payload
- Per-connection last_seen replay watermark
- 6 msg_types locked append-only (Send / Reply / Ping /
  Pong / ChildExited / ProtoError); 7-15 reserved for
  v1.x; 16+ require v2 frame
- Single version byte as escape hatch

The HMAC-SHA256 truncation to 16 bytes follows RFC 4868
(secure for keys ≥ 32 raw bytes) — well-justified
deviation from the obvious "use full 32 bytes" baseline.

### Tensor copy-vs-view trade-off

**Grade: EXCEEDS**

v5.41.0 Ts.1 ships copy semantics for reshape. v5.45.0
Ts.2.B swaps to aliasing (view) under the same surface;
the `noalias` LLVM attribute drops. **Migration burden
zero** — Phase 0 audit confirmed no production callers
relied on copy semantics. Stepped slices (Ts.3.B) keep
copy semantics intentionally (multi-axis non-stepped
axes pass step=1 transparently; stepped axes copy). The
copy-vs-view distinction is documented per surface in
the cookbook.

### Inline benchmarks

**Grade: MEETS**

The arc shipped no major benchmark regressions and no
benchmark-driven optimizations. v5.39.0 Cr.\* added HMAC
+ streaming digest with no perf claims; v5.43.0 Da.\* added
JSON-payload encode/decode at the agent boundary with no
1MB-payload measurement. `bench_stdlib.py` v5.44.1 fixed a
pre-existing invalid `use_mir=True` kwarg incidentally
during Ps.11.A — that's a positive (latent breakage
removed).

### Agent supervision substrate

**Grade: EXCEEDS**

v5.42.0 As.6 push-driven via opt-in C callback (Path B
over Path A pure-Mapanare poll-based). Lower restart
latency + preserves ExitReason payload routing. The
static C trampoline `supervisor_trampoline` build-and-
sends `__mn_child_exit_msg_t` to the parent supervisor's
inbox — runtime-thread-safe through the FAILED state-
store release happens-before edge.

---

## Findings

### V.0 — copy-vs-view discipline (LOW, positive)

The v5.41.0 → v5.45.0 tensor closeout arc is exemplary
honest perf framing: ship correctness first (copy
semantics), then swap to aliasing under same surface
once the runtime substrate (refcount on
`mapanare_tensor_t`) is in place. Migration cost zero
because Phase 0 audited the production caller surface
before promising the swap.

### V.1 — `noalias` drop is the right trade (LOW, positive)

`__mn_tensor_reshape` declared with `noalias` at v5.41.0;
v5.45.0 Ts.2.B drops it. This is necessary correctness
under aliasing. The cookbook calls this out explicitly.

### V.2 — JSON serde overhead at scale (LOW, fresh)

v5.43.0 Da.\* uses JSON for all agent message payloads
(no binary serde fast path). At 1MB payloads this is
likely substantial overhead vs CBOR / MessagePack /
Protobuf, but no benchmark exists. **Recommend a
v5.47.x or v6.0+ benchmark** to anchor real overhead;
the binary-fast-path carry in section 5(b) is the
follow-up.

### V.3 — supervision restart latency (LOW, fresh)

Path B (push-driven via C callback) has lower restart
latency than Path A (pure-Mapanare poll). No measured
number. **Recommend including a baseline benchmark** in
the v6.0 perf-baseline workstream so future optimization
decisions have a starting point.

### V.4 — `mapanare_tensor_t` 40→64 byte cost (LOW, fresh)

+24 bytes per tensor instance (refcount 8 + is_view 1 +
pad 7 + parent ptr 8). For tiny scalars and small lists
this is non-trivial overhead; for typical ML-shaped
tensors (1k+ elements) it's noise. The trade is correct
(aliasing safety needs the metadata) but the cost is
real for scratch-tensor-heavy workloads. Documented in
v5.45.0 SESSION_REPORT.

### V.New1 — v6.0 perf-baseline workstream (MEDIUM, fresh)

v6.0 borrow checker work will likely impose new analysis
overhead (compile time) and may shift runtime cost
profiles (drop glue under more accurate alias info).
**Recommend v6.0 PLAN explicitly carve out a perf-
baseline establishment release** (akin to the v5.45.0
PRE_PHASE_AUDIT pattern) so the borrow-checker work
has a number to beat / hold-the-line against.

---

## Carry-forward suggestions

For Cp.4 V5_TO_V6_CARRY.md:

- **(a) v6.0 PLAN input:** Perf-baseline establishment
  release (V.New1) as v6.0.x prerequisite work.
- **(b) v5.47.x patch candidate:** JSON serde 1MB
  benchmark (V.2) — establishes the binary-fast-path
  ROI conversation.
- **(b) v5.47.x patch candidate:** Supervision restart
  latency benchmark (V.3) — anchors future supervisor
  optimization conversations.

---

## Score

**9.85 / 10**

Up 0.05 from v5.28.0's 9.80 — the copy-vs-view discipline
on tensors and the wire-format engineering on v5.43.0 are
both better-than-baseline perf craftsmanship. The
unbenchmarked-additions spread (V.2 + V.3) is a small
dock, not a load-bearing one.

## Recommendation

**PASS**

v5 ships clean from the perf axis. The unbenchmarked
deferrals are acceptable given v5's primary thesis was
correctness + ergonomic stdlib coverage, not perf
optimization.
