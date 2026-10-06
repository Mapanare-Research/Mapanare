# v5 Retrospective — What Worked, What Didn't, What to Bring to v6.0

> Written at v5.47.5 panel cut covering v5.31.0 → v5.47.0
> (17 substantive releases + 7 Js.4 sub-releases). Looks
> backward at v5 process discipline and forward at v6.0
> structural recommendations.
>
> ~1500 words target. Substance over bullet count.

---

## What worked

**Structural fix discipline over symptom patching.** The
single most consistent thing v5 got right was choosing to
fix root causes instead of papering over symptoms. The
v5.46.0 Lf.\* closeout is the canonical example — three
distinct symptoms (Result destructure tag corruption +
variant rewrap + nested 15-arm match silent no-fire) had
one common root cause (Python bootstrap `Ok`/`Err`
constructor wrap-shape default missing the
`current_fn.return_type` consultation that v5.26.1 Eu.2
had added on the self-host side). Phase 0 audit found
this; ~30 LOC fix closed all three. The temptation to
ship three separate fixes (one per symptom) would have
shipped three releases that each preserved the underlying
bug for the next surface to expose.

The same discipline shows up in v5.39.0 Cr.0 (the emitter
shortcut bypass class — gated `fn not in self._sigs`
instead of adding per-shortcut workarounds) and v5.36.0
Js.0/Js.0.B (`_san` sanitizer fix + Result wrap-shape
fix at the emitter level instead of in the user code that
surfaced them). The user-memory entry `feedback_circular_debugging`
("Stop threshold-tuning and band-aid patches for LLVM
struct codegen — attack root cause instead") was the
operative principle; the v5 record holds 17 releases of
adherence.

**STRICT 3-stage fixed-point as a load-bearing invariant.**
The 50-release strict streak from the v5.7.1 baseline is
the deepest architecture invariant in the project. Every
release in the v5.31-v5.47.0 arc cited STRICT preserved by
construction (zero `mapanare/self/*.mn` source touches —
v5.31, v5.32, v5.33.x, v5.34, v5.35, v5.36, v5.37, v5.38,
v5.39.x, v5.40, v5.41, v5.42, v5.43, v5.44, v5.44.1) or
by explicit Phase 0 verification of self-host parity
(v5.46.0 Lf.5 no-op gate; v5.45.0 concat_self.py rebuild
lesson). The gate kept the bootstrap in lockstep with
the self-host across 16 substantive releases of stdlib
work, runtime extensions, and ABI-extending struct
changes.

**Pre-phase audit pattern (introduced midstream).** The
PRE_PHASE_AUDIT.md format wasn't a v5.31 starting move;
it accumulated as discipline through the arc as multi-
week PROMPT drafts repeatedly drifted from fast-moving
HEAD. Phase 0 mismatches caught:

- v5.41.0 (4 mismatches): grammar HEAD, GpuTensor
  namespace, mapanare_tensor_t structure, LOC budget
- v5.42.0 (5 deviations): naming drift, no system-msg
  enum, no `mn_agent_exit*` API, restart_policy
  semantics, golden count
- v5.45.0 (5 deviations): grammar HEAD, GpuTensor.reshape
  namespace, struct grow audit, +24 vs +16 bytes,
  IndexItem inclusive flag
- v5.44.0 (PROMPT premise error): green-field rewrite of
  pkg.py would have duplicated 1037 LOC of complete
  infrastructure
- v5.40.0 (Ai.1+Ai.2 deferral): naming collision +
  nested-generic intrinsic substitution would have
  shipped subtly broken
- v5.46.0 (Lf.5 no-op gate): self-host already had the
  v5.26.1 Eu.2 fix; STRICT preserved trivially

Without Phase 0 the cost of catching each of these would
have been mid-implementation rebumps. With Phase 0 the
cost was ~1h per release. The pattern is one of v5's
clearest process wins; recommend explicit elevation in
v6.0 PLAN as mandatory at every release.

**Honest CHANGELOG framing.** `### Changed` (potentially
breaking-ish) discipline applied correctly across the arc:
v5.36.0 Js.1 RFC 8259 strict mode, v5.39.6 Map<K,V>
non-String K compile-time error, v5.43.0 Da.\*
RemoteExitReason rename, v5.45.0 Ts.\* mutable-view
semantic swap. Each surface that *could* break a downstream
caller got framing in `### Changed`, not silently in
`### Added`. The check_changelog_honesty.py gate held
across the arc.

**Single-file stdlib pattern.** v5.34.0 Phase 2 surfaced
two cross-module emitter limitations (extern_fn_def
propagation + module-name mangling). Every existing
stdlib module is single-file with self-contained tests
(`math`, `crypto`, `fs`, `ai/llm`, `db/*`); v5.34.0 Dt.\*
followed the proven pattern instead of opening compiler
edits. This made it possible to ship 6 new stdlib
modules in 6 releases without compiler touches. The
`feedback_stdlib_single_file_pattern` user-memory entry
is now the operative default; cross-module fixes are
v6.0+ work.

---

## What didn't

**v5.43.0 PLAN sizing was too aggressive.** The single
biggest release in the arc — ~1500 LOC `.mn` (5 modules)
+ ~360 LOC C (`mapanare_node.c`) + ~95 LOC C (mapanare_io
server-side TLS) + new wire format + supervision interop
bridge + 4 link-and-run tests + pytest harness + 2
examples + 210-LOC docs extension — should have split.
The sizing produced three v5.x lowerer bug carries
(Lf.1/2/3 — Result destructure + variant rewrap +
nested 15-arm) plus a flat-tuple shape workaround across
the agent stdlib that took two more releases to clean up
(v5.46.0 Lf.\*, v5.47.0 Cl.1, v5.47.x Cl.2 still pending).
The lesson for v6.0 is: when a single release ships
≥1000 LOC of `.mn` plus ≥200 LOC of C plus a new wire
contract, **split it**.

**Tn.1 multi-release overrun.** The v5.28.0 panel
recommendation to generalize the async-link gate to all
95 goldens shipped at v5.35.0 Sq.0 — 7 releases late.
Escalated through v5.29.0 carry → v5.32.0 PLAN → v5.33.0
PLAN with DEADLINE-at-v5.35.0 → bundled into v5.35.0
ahead-of-deadline. The escalation pattern eventually
worked (deadline framing forced the closure) but the
underlying issue is real: low-prio test-infrastructure
items get pushed to the end of every release window.
Recommend: when a carry escalates through 3+ release
PLANs, apply a hard deadline.

**HEAD-state premise drift in PROMPT/PLAN.** Multi-week
PROMPT drafts repeatedly contained premises that were
true *when written* but stale *when implementation
started*. v5.41.0 PROMPT/PLAN claimed grammar accepted
`[start..end:step]`; HEAD didn't. v5.42.0 PROMPT/PLAN
used `MnAgent` / `mn_agent_*` / `MN_MSG_*` naming;
runtime is `mapanare_agent_t`. v5.40.0 PROMPT premised
an existing runtime type metadata; HEAD literally just
emits `printf("%lld\n")` for structs. v5.45.0 PROMPT
claimed goldens at HEAD were 98/98; reality was 96/96.
The structural fix surfaced midstream: PRE_PHASE_AUDIT.md
with explicit "PROMPT/PLAN deviation surfaced" tables.
By v5.46.0 + v5.47.0 the pattern was second-nature. v6.0
should not re-discover it; **PRE_PHASE_AUDIT.md mandatory
at every release.**

**SDK-bundle scope creep at v5.12.0 caught only at
v5.31.0.** The "Python is the front door on Windows
release installs" anti-pattern shipped at v5.12.0 (when
the toolchain bundle landed) and stayed silent for 19
minor versions until v5.31.0 banner surfacing made it
visible. v5.32.0 + v5.33.0 closed it structurally
(native `mnc` binaries on three platforms). The lesson:
**release-tarball UX needs a panel-class smoke gate**
that simulates the user's first 3 commands on a fresh
install. v5.32.0 Nw.4 + v5.33.0 Nu.4 introduced this
gate (Layer 1 in-job + Layer 2 published-tarball);
should be canonical for v6.0+.

**Mid-arc panel slippage.** v5.45.0's original panel
slot was deferred to v5.47.5 so v5.45/v5.46/v5.47 could
close three long-standing debts (Ts.\*, Lf.\*, Cl.\*)
before the panel audited ecosystem readiness. The
deferral was correct (per project memory:
"panels at the end of an arc, not in the middle"; per
v5.28.0 directive) but cost 19 minor versions of
informational REMINDER from check_cadence.py before the
gap closed. The shape is right; the **comms could have
been clearer** — recommend the next deferral explicitly
documents the projected next-panel release at the time
of deferral, so the gap closure is plannable.

---

## What to bring to v6.0

**Tighter PLAN sizing.** Per the v5.43.0 lesson: borrow
checker work should split. Recommend v6.0.0 (inference) /
v6.0.1 (enforcement + perf baselines) / v6.0.2 (hard
`{}` removal + tensor unification). Each sub-release
ships one structurally-load-bearing thing with its own
PRE_PHASE_AUDIT, falsifiability gates, and STRICT
preservation budget. The temptation to bundle "since
we're touching lower.py anyway" should be resisted — v5.43.0
is the cautionary tale.

**PRE_PHASE_AUDIT.md mandatory at every release.** Cost
~1h per release. Saves rebumps + scope drift. The pattern
caught 10+ load-bearing PROMPT/PLAN-vs-HEAD mismatches
across v5.31-v5.47.0; would have caught all the
SESSION_REPORT-documented "PROMPT premised X but HEAD
has Y" surprises. v6.0 PLAN drafting should require it.

**Convergent-recommendation pattern explicit.** When 2+
reviewers independently surface the same finding shape
from different axes, treat as load-bearing. v5.28.0
caught Tn.1 this way (Cb.New1 + Ra.Inf1 → v5.35.0 Sq.0
closure 4 releases later); v5.47.5 re-surfaces the
pattern across Anaconda + Boa + Rattler (PRE_PHASE_AUDIT
elevation) and Anaconda + Boa (KNOWN_FAILURES ledger).
Recommend explicit V5_DECISION.md "Followups" elevation
in every panel cycle.

**Adversarial-input testing as default for cross-process
/ network-bound / parser-bound surfaces.** v5.43.0 Da.\*
1000-iteration network fuzz across 8 input variants is
the model. v6.0 PLAN should require this for any new
such surface. The cost is small (1-2 hours setup per
surface); the catch radius is enormous (network-shape
DoS, parse-shape SEGV).

**RFC corpus discipline for crypto / security-load-
bearing surfaces.** v5.39.0 Cr.\* shipped with RFC 6234
SHA-256/SHA-512, FIPS 202 SHA-3-256, RFC 7693 BLAKE2b-512,
RFC 4231 HMAC tests. The pattern should be the default
for v6.0+ crypto / security work.

**Wire-format engineering shape as v6.0 template.**
v5.43.0 Da.\* wire format v1
(`[u32 length BE][u8 v=1][u8 mt][u64 seq BE][16 b hmac][JSON]`,
HMAC truncation, replay watermark, DoS guard, version
byte as escape hatch, locked msg_types) is the cleanest
cross-network contract in the project. Recommend the
shape as v6.0 model for any future cross-network
contract (e.g., borrow checker IPC if it grows one).

**Multi-release escalation → DEADLINE pattern.** Carries
that escalate through 3+ release PLANs get a hard
deadline applied. Tn.1 closure at v5.35.0 Sq.0 demonstrated
the shape works; should be codified.

**Staged closure shape for multi-bug arcs.** v5.39.0 →
v5.39.7 closed Js.4.B/C/D/E/F across 8 sub-releases,
each with one TypeKind branch + documented invariant
decision. Bundling discipline traded release count for
falsifiability rigor. Recommend the shape as the default
for v6.0 multi-bug arcs (the borrow checker may surface
as similarly stair-step).

---

v5 delivered. The terseness arc, stdlib gap-close,
manifesto, package-system runway, tensor closeout — all
shipped at the quality the project promised, every claim
verified at HEAD by Cp.1's audit. v6.0 starts on solid
ground.
