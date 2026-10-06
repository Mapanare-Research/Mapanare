# Cobra — v5.47.5 Closeout Panel Findings

**Reviewer axis:** Architecture + cohesion + design
**Arc reviewed:** v5.31.0 → v5.47.0 (17 releases)
**Audit reference:** `.reviews/v5.47.5/PRE_PANEL_AUDIT.md`
**Prior-panel score:** 9.70 (v5.28.0 RE-PANEL)

---

## Summary

The v5.31-v5.47 arc made three substantive architectural
commitments and held all of them:

1. **Native-First Philosophy** (v5.31-v5.33.0) — release
   tarballs ship native `mnc` binaries on the three
   primary platforms; Python entrypoint becomes
   bootstrap-only on release installs. Closes the
   "Python is the front door on Windows" structural
   anti-pattern.
2. **First-class agents go cross-machine** (v5.42.0 +
   v5.43.0) — the manifesto pitch ("agents over RPCs")
   graduates from library-class to actual transport.
   Wire format v1 + supervision substrate ship together.
3. **Stdlib gap-close at runtime-bound layer** (v5.34-v5.39)
   — date/time, sqlite, JSON, HTTP, regex, crypto all
   ship via runtime C extensions exposed as `__mn_*`
   exports + Mapanare-side wrappers.

The third commitment is the most architecturally
load-bearing because it establishes the **runtime-bound
stdlib pattern** — OS primitives in C, ergonomic
wrappers in Mapanare. Every stdlib release in the arc
preserved this pattern; no module shipped pure-Python
or pure-C.

---

## Per-category grades

### Native-First execution

**Grade: EXCEEDS**

Three releases (Nw.\* + Nu.1/Nu.2) shipped native binary
bundling on Windows + Linux + macOS arm64. Two arches
deferred (Linux aarch64 + macOS x86_64) for honest
infrastructure reasons (no native runner / cross-compile
pipeline). The deferral is honest, not hidden.

The v5.32.0 deviation from PROMPT (approach b: reuse
build-native artifact rather than approach a: cross-compile
from Linux) was the right architectural call — full
self-compile cycle on a Windows runner validates Win64
ABI more strongly than a cross-compile would.

### Manifesto arc cohesion

**Grade: EXCEEDS**

v5.40.0 Ai.\* + v5.42.0 As.\* + v5.43.0 Da.\* form the
manifesto arc; cohesion is exemplary:
- Ai.\* extends typed-serde (v5.36.0 Js.4) for
  `ask_with_schema`
- As.\* establishes child-exit semantics (`mapanare_exit_reason_kind_t`,
  4-state lifecycle: NORMAL/SHUTDOWN/KILLED/CRASHED)
- Da.\* extends As.\* with cross-machine via `RemoteExitReason`
  + `ChildExitedMsg` codec

The v5.43.0 RemoteExitReason::TransportLost →
RemoteUnreachable rename was a load-bearing cohesion
preservation move (concat-pattern with NetworkError in
scope was resolving the same name to the wrong enum).

### Strategy library shape (v5.42.0)

**Grade: EXCEEDS**

v5.42.0 As.\* shipped as a *strategy library* answering
"given this child's exit, which children should the
orchestrator restart" — NOT as a supervisor agent
spawning/killing children. This decision sidesteps two
v5.x quirks (fn-typed parameters unreliable to invoke;
cross-typed agents can't be stored in homogeneous list).
**Storing just integer agent IDs sidesteps the latter
entirely.** The orchestrator side does respawn driven by
strategy-library decisions. Tracked as a v5.43.0 ergonomic
upgrade and explicitly named in the v5.42.0 deferral list.

### Wire format engineering (v5.43.0)

**Grade: EXCEEDS**

`[u32 length BE][u8 v=1][u8 mt][u64 seq BE][16 b hmac][JSON]`
is conservative-architectural — version byte as the only
escape hatch; 6 msg_types locked append-only; 7-15
reserved for v1.x; 16+ require v2 frame. Per-connection
last_seen replay watermark + 100MB DoS guard. **Migration
path to v2 is explicit; no backward-incompat hidden in
the version-byte semantics.**

### Package-system runway

**Grade: EXCEEDS**

v5.44.0 Ps.\* wires existing-but-unwired pkg.py
infrastructure into the resolver; **doesn't redesign**.
This is the correct architectural call. The PROMPT premise
error ("treat as green-field") was caught at Phase 0 by
the audit.

The reserved-source-literal contract (`mn_modules`, `path`,
`git`, `global-cache`) — only `mn_modules` shipped at
v5.44.0; `path`/`git`/`global-cache` reserved for v6.0+.
**The compiler must not scan a global cache opportunistically**
— locked by `tests/packages/test_resolver_does_not_scan_global_cache.py`.
This is the correct hygiene for an additive package system.

### Tensor surface coexistence

**Grade: MEETS**

`stdlib/gpu/tensor.mn::GpuTensor` (struct on the GPU side)
and the language-builtin `Tensor` (TypeKind.TENSOR) are
two parallel tensor surfaces. v5.41.0 Phase 0 surfaced
the namespace coexistence question; v5.45.0 cookbook
documents the migration story. **This is the weakest
cohesion point in v5** — two parallel surfaces is a
design debt. Recommend v6.0 unification (surface in
section 5(a)).

---

## Findings

### Cb.0 — wire-format engineering as v6.0 model (LOW, positive)

v5.43.0 Da.\* wire format v1 is the cleanest cross-network
contract in the project. **Recommend its shape as the
template for any v6.0 cross-process contract** (e.g.,
borrow checker IPC if it grows one).

### Cb.1 — strategy-library shape as workaround pattern (LOW, positive)

v5.42.0 As.\* shipped as strategy library because v5.x
fn-typed parameter invocation is unreliable. **The
workaround is honest** (documented in source preamble +
SESSION_REPORT) and the upgrade path (factory closure
in v5.43.0+) is explicit. v6.0 borrow checker work may
fix the underlying fn-typed-param issue, at which point
v5.42.0 As.\* should grow a closure-form
`spawn_supervised(spec, factory)` API.

### Cb.2 — strict 3-stage fixed-point as architecture invariant (LOW, positive)

50-release strict streak is the deepest architecture
invariant in the project. v5.45.0's Ts.\* arc was the
first v5.31+ release to touch `mapanare/self/*.mn` source
materially; preserved STRICT after `concat_self.py`
discipline lesson. **The invariant is the strongest
guarantor of self-host parity in the codebase.**

### Cb.3 — tensor surface debt (MEDIUM, fresh, v6.0 input)

`GpuTensor` (struct) + `Tensor` (TypeKind builtin) are
two parallel surfaces. The v5.45.0 cookbook documents
coexistence but not unification. **Recommend v6.0
unification:** elevate `Tensor` to be the single surface,
with GPU-bound operations as method dispatches that may
fall back to CPU. This is real architecture work, not
cosmetic.

### Cb.4 — package-system reserved-source-literal contract (LOW, positive)

`mn_modules` shipped; `path` / `git` / `global-cache`
reserved. The contract is forward-compat; the test gate
(`test_resolver_does_not_scan_global_cache`) locks the
invariant. **No fresh action needed**; v6.0 path/git/
global-cache implementations slot cleanly.

### Cb.5 — distributed-supervision deferred (MEDIUM, fresh)

v5.42.0 As.\* + v5.43.0 Da.\* ship the substrate
(supervision in-process; remote agents cross-process)
but **distributed supervision** (parent supervisor on
node A, children on node B) is deferred. The pieces
exist (heartbeat primitive, ChildExited codec, classify_
remote_exit) but the wired-together orchestrator is
v5.43.x+. **Recommend v6.0 PLAN explicit elevation** —
this is a manifesto-arc completion item, not a v5.47.x
patch.

### Cb.New1 — Native-First as v6.0 default (LOW, positive)

v5.31-v5.33 closed the "Python is the front door"
anti-pattern on three platforms. **v6.0 should default to
native-first for new platforms** (Linux aarch64 + macOS
x86_64 v6.0+) — the infrastructure pattern is set.

---

## Carry-forward suggestions

For Cp.4 V5_TO_V6_CARRY.md:

- **(a) v6.0 PLAN input:** Tensor surface unification
  (Cb.3) — real design work
- **(a) v6.0 PLAN input:** Distributed supervision
  orchestration (Cb.5) — manifesto-arc completion
- **(a) v6.0 PLAN input:** Closure-form supervisor spawn
  API (Cb.1) — gated on fn-typed-param fix
- **(b) v5.47.x patch candidate:** Linux aarch64 +
  macOS x86_64 native binaries (Cb.New1) — infrastructure
  work, not design

---

## Score

**9.75 / 10**

Up 0.05 from v5.28.0's 9.70 — manifesto-arc cohesion +
Native-First execution outweigh the tensor-surface debt.
The 0.25 gap is the tensor-surface unification debt
(Cb.3) being a real architectural carry, not just
cosmetic.

## Recommendation

**PASS**

v5 ships clean from the architecture axis. v6.0 green-lit
with the tensor unification + distributed supervision
explicitly named as v6.0 PLAN inputs.
