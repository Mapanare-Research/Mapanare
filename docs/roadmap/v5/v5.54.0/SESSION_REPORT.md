# v5.54.0 — SESSION REPORT

**Date:** 2026-05-15
**Status:** READY (not tagged)
**Scope:** Cl.2 + Cl.3 + Cl.4r per PLAN.md, bundled atomic refactor.

---

## Headline

- **Cl.2** — `stdlib/agent/{url,remote,node,supervision}.mn` public
  surface refactored from v5.43.0 flat-tuple Result workaround to
  ergonomic `Result<T, NetworkError>`. **BREAKING for stdlib
  consumers.** 12 public functions, 8 flat-tuple struct types
  removed, 16 constructor helpers removed.
- **Cl.3** — closed as OBSOLETE with falsifiability anchor.
  Phase 0 audit found the v5.40.0 carry's premise stale.
- **Cl.4r** — 5 `str(byte)` sites in `stdlib/net/websocket.mn`
  swept to `__mn_str_chr(byte)`.

**Strict 3-stage fixed point preserved by construction.** Zero
`mapanare/self/*.mn` edits; zero Python compiler edits; zero
runtime edits. 56-release strict streak from v5.7.1 holds at the
v5.53.0 baseline (245,155 lines / 0 diff).

**Goldens 103/103.** No goldens added or modified.

---

## Phase 0 — PRE_PHASE_AUDIT

Two load-bearing reversals of v5.47.0/PLAN.md premise documented
in `PRE_PHASE_AUDIT.md`:

1. **Cl.3 premise stale.** `walk_dir` does not exist in
   `stdlib/fs.mn` at v5.53.0 HEAD. The v5.40.0 carry's named
   function was renamed/removed. Current `walk()` (returns
   plain `List<String>`, line 469) internally uses
   `match list_dir(current)` against
   `Result<List<String>, FsError>` (line 487) — exactly the
   bug-class shape — and compiles cleanly. v5.46.0 Lf.\*
   wrap-shape default fix implicitly closed Cl.3. Only HEAD
   reference is a stale comment in `stdlib/ai/ask_cache.mn:19`.
   **Disposition:** close as OBSOLETE with 3-case falsifiability
   anchor in `tests/stdlib/test_fs.py::TestWalkDirCl3Anchor`.

2. **Cl.4r residual count 5 (not 11).** v5.47.0 reported 11
   `str(byte)` sites; v5.47.0 Cl.4 closed 6. Remaining 5 at
   `stdlib/net/websocket.mn:236, 743 (×2), 1121 (×2)`.

User direction (received after Phase 0): bundle Cl.2 in v5.54.0
atomic, close Cl.3 with anchor test, proceed Cl.4r.

---

## Phase 1 — Cl.2.1 url.mn canary

`stdlib/agent/url.mn`:
- Deleted `UrlParseResult` struct (~6 LOC), `url_parse_ok` (~3
  LOC), `url_parse_err` (~4 LOC), plus their interleaved comment
  block (~5 LOC).
- `parse_agent_url(s: String) -> Result<AgentUrl, NetworkError>`.
- 13 return sites rewritten from `da url_parse_err(N, msg)` /
  `da url_parse_ok(...)` to `da Err(BadUrl/UnsupportedScheme(msg))`
  / `da Ok(...)`.

`stdlib/agent/remote.mn:77-81` caller updated to
`match parse_agent_url(url_str) { Ok(u) => { url = u },
Err(e) => { da rc_err(ne_kind(e), ne_msg(e)) } }` (this remote
caller was later fully refactored in Phase 2; the temporary
adapter via `ne_kind`/`ne_msg` bridges the partial migration
checkpoint).

`stdlib/agent/tests/test_dist_url.mn`: 10 destructure sites
rewritten to `match parse_agent_url(...) { Ok(u) => ...,
Err(e) => ... }`. Added inline `is_unsupported_scheme(e:
NetworkError) -> Bool` helper for the 2 kind-discriminator
checks (unix:// and http:// rejection paths).

**Phase 1 gate result:** Python LLVM emitter compiles
concatenated stdlib + test cleanly (20944 IR lines). 21763 LOC
when the test is concatenated as a single TU.

---

## Phase 2 — Cl.2.2 remote.mn (largest surface)

`stdlib/agent/remote.mn`:
- Deleted `RemoteConnectResult`, `RemoteSendResult`,
  `RemoteRecvResult` structs and their 6 `*_ok` / `*_err`
  constructor helpers (~50 LOC).
- Added `RecvOk { handle: RemoteAgent, frame: Frame }`
  companion type (no first-class tuples in Mapanare; needed for
  `remote_agent_recv`'s Ok side which historically carried both
  the updated handle and the decoded Frame).
- `remote_agent_connect` / `remote_agent_send` /
  `remote_agent_send_typed_msg` / `remote_agent_ping`
  refactored to `-> Result<RemoteAgent, NetworkError>`.
- `remote_agent_recv` refactored to `-> Result<RecvOk,
  NetworkError>`.
- Internal callers of `dr.err` (the `decode_frame`
  NetworkError-bearing branch) now use `Err(dr.err)` directly
  instead of the legacy `ne_kind(dr.err)` / `ne_msg(dr.err)`
  flat-tuple shuttle.

Variant mapping (load-bearing for behavior preservation):
- `kind=3` (NoKey)         → `Err(NoKey(...))`
- `kind=4` (ConnectFailed) → `Err(ConnectFailed(...))`
- `kind=9` (ProtoOversized) → `Err(ProtoOversized(...))`
- `kind=10` (ProtoMalformed) → `Err(ProtoMalformed(...))` (used
  for the "expected Pong, got msg_type=X" case in
  `remote_agent_ping`)
- `kind=12` (TransportLost) → `Err(TransportLost(...))`

`remote_agent_connect`'s parse_agent_url error path: `da Err(e)`
forwards the NetworkError directly from `parse_agent_url`
(previously reclassified via `rc_err(ne_kind(e), ne_msg(e))`,
which round-tripped through the integer-kind shuttle and lost
variant identity). Behavior change is *cleanup* — the caller now
sees the precise variant (`BadUrl`, `UnsupportedScheme`) instead
of an int-encoded round-trip. Forward-compatible improvement.

---

## Phase 3 — Cl.2.3 + Cl.2.4 node.mn + supervision.mn

`stdlib/agent/node.mn`:
- Deleted `NodeListenResult`, `NodeAcceptResult`,
  `ConnSendResult`, `ConnRecvResult` structs and their 8
  constructor helpers (~80 LOC removed).
- Added `ConnRecvOk { conn: NodeConnection, frame: Frame }`
  companion (mirror of `RecvOk` in remote.mn for the conn side).
- `node_listen`, `node_listen_tls`, `node_accept_one`,
  `conn_send_frame` → `Result<T, NetworkError>`.
- `conn_recv_frame` → `Result<ConnRecvOk, NetworkError>`.
- Variant mapping mirrors remote.mn's: `NoKey`, `ListenFailed`,
  `ConnectFailed`, `ProtoOversized`, `TransportLost`.
- `conn_recv_frame`'s `dr.err` forwarding now uses `Err(dr.err)`
  directly (same cleanup as remote.mn).
- `ne_kind` / `ne_msg` helpers retained at lines 297, 322 — still
  needed for the partial caller in remote.mn (now fully removed
  but the helpers remain as a public stdlib surface; external
  consumers reading `RemoteSendResult.err_kind` as Int in v5.43.0
  – v5.53.x can keep using `ne_kind(e)` for the equivalent
  int-shape lookup against the post-refactor Result Err side).

`stdlib/agent/supervision.mn`:
- `remote_agent_heartbeat_check(r: RemoteAgent) -> Result<RemoteAgent, NetworkError>`
  (passthrough to `remote_agent_ping`).
- Doc comment at lines 45-52 refreshed (concat-order summary
  brought into sync with the v5.54.0 surface).

`stdlib/agent/tests/test_dist_node.mn`: Migrated. Added inline
`is_no_key` and `is_connect_failed` discriminator helpers next
to the `is_unsupported_scheme` pattern. The 7 destructure sites
across the listen happy/error paths + 3 remote_agent_connect
error paths converted to `match` form.

`stdlib/agent/tests/test_dist_supervision.mn`: **No changes
required.** This test doesn't touch the migrated public surface
— it operates on `RemoteExitReason` / `Supervisor` /
`ChildExitedMsg`, none of which were Cl.2-affected.

`stdlib/agent/tests/test_dist_proto.mn`: **No changes required.**
Wire-protocol tests; doesn't call migrated APIs.

---

## Phase 4 — Cl.2.5 + Cl.2.6 tests + docs

**Tests (Cl.2.5):** test_dist_url.mn + test_dist_node.mn
rewritten in Phases 1 + 3. 2 of 4 dist tests touched (per Phase
0 enumeration; proto + supervision tests unchanged). 3 new
falsifiability discriminator helpers (`is_unsupported_scheme`,
`is_no_key`, `is_connect_failed`) — these are inline pattern-
match boilerplate that should be replaced by a stdlib
`ne_is(e, variant)` helper or by direct match in v5.54.x ergonomic
follow-up (NOT v5.54.0 scope).

**Docs (Cl.2.6):** `docs/stdlib/agent.md` — 3 cookbook snippets
migrated from `.ok` / `.err_msg` destructure to `match` form.
"What's not here yet" section's "Result<T, NetworkError> at
every API boundary" entry marked SHIPPED with v5.54.0
cross-reference and BREAKING annotation.

**Example (out-of-scope-but-load-bearing):** Phase 2's grep
sweep found `examples/agents/distributed_pool.mn` as an
unforeseen caller of `RemoteConnectResult` + `RemoteSendResult`.
Migrated to `match` form during Phase 2 to keep the example
compileable. Pseudocode comment block at the bottom also
refreshed for documentation consistency.

---

## Phase 5 — Cl.2.7 regression sweep

```
pytest tests/stdlib/ --ignore=test_distributed_agents.py \
       --ignore=test_json_corpus_baseline.py
```

**Result: 987 passed, 56 skipped, 1 xfailed.** Pre-existing
`test_json_corpus_baseline.py::test_rfc8259_corpus_baseline`
failure verified to be pre-existing at v5.53.0 HEAD via
`git stash` → re-run → same failure → `git stash pop`. Unrelated
to v5.54.0 changes (build step in the corpus harness, not a
Cl.\*-affected pytest case).

`tests/stdlib/test_distributed_agents.py` skips on Windows (no
clang + no staged `libmapanare_rt.a`). The IR-emit smoke
performed in Phases 1/2/3 covers the parse → semantic → lower →
emit path on the same concatenated source the pytest harness
links; CI Linux job is the link+execute safety net.

`tests/stdlib/test_websocket.py`: 147 cases GREEN — exercises
the masked-frame path (Cl.4r line 236) and close-frame path
(Cl.4r lines 743 + 1121).

---

## Phase 6 — Cl.3 implicit closure anchor

Added `TestWalkDirCl3Anchor` class to `tests/stdlib/test_fs.py`
(3 cases). Falsifiability protocol locked in class docstring +
per-test docstring: revert v5.46.0 Lf.\* (the Ok/Err wrap-shape
default in `mapanare/lower.py`'s Ok/Err constructor branches)
and `test_list_dir_match_on_result_compiles` fails at the
asserted `extractvalue ptr ... 0` + `zext ptr to i64` IR
sequence.

**Phase 6 gate result:** 3 / 3 GREEN locally.

---

## Phase 7 — Cl.4r websocket sweep

5 sites in `stdlib/net/websocket.mn`:
- Line 236 `apply_mask`: `result = result + str(xored)` →
  `__mn_str_chr(xored)`. Mask-XOR'd byte for RFC 6455 client
  framing.
- Line 743 `build_send_frame` Close arm: `payload = str(hi) +
  str(lo) + reason` → `__mn_str_chr(hi) + __mn_str_chr(lo) +
  reason`. Status code per RFC 6455 §5.5.1.
- Line 1121 `ws_close_normal`: same shape as 743 in the
  close-payload construction. Replaced.

`__mn_str_chr` extern verified pre-existing at
`stdlib/net/websocket.mn:25` (v5.43.0 Da.0 export). No new
externs needed. Test coverage: existing
`tests/stdlib/test_websocket.py` (147 cases) exercises all three
hot paths.

---

## Phase 8 — Closeout

- VERSION 5.53.0 → 5.54.0 via `scripts/bump_version.py 5.54.0`
- CHANGELOG `### Changed` BREAKING annotation + migration recipe
- CHANGELOG `### Fixed` for Cl.3 + Cl.4r
- CLAUDE.md release-notes entry: see top of CLAUDE.md
- SPEC.md re-sync: deferred to v5.55.0 (no SPEC-surface changes
  in v5.54.0; the public agent-API surface is stdlib documented
  in `docs/stdlib/agent.md`, not SPEC.md)

---

## What's NOT in scope (deferred)

- **Result-ergonomic `ne_is(e, variant)` helper.** The
  test-side `is_no_key` / `is_connect_failed` /
  `is_unsupported_scheme` pattern-match boilerplate could become
  a single stdlib helper. v5.54.x ergonomic follow-up.
- **`ne_kind` / `ne_msg` deprecation.** These int-shuttle
  helpers are retained for v5.43.0–v5.53.x consumers' partial
  migration paths; v5.55.0+ may flag them deprecated.
- **CARRY_FORWARD.md / KNOWN_FAILURES.md refresh.** v5.47.5
  Cp.\* panel-deliverable surface; not v5.54.0 scope.
- **`mnc fmt` migration of the 287–336 brace-block deprecation
  warnings** in dist-agent test files. v6.0 hard-removal scope.
- **`tests/llvm/test_lowerer_fixes.py` Cl.3 case addition.** The
  Cl.3 anchor lives in `tests/stdlib/test_fs.py` per Phase 0
  decision (the bug class is destructure-side, not
  constructor-side; same file as the v5.46.0 Lf.\* anchor would
  duplicate falsifiability surface unnecessarily).

---

## Aggregate state entering v5.55.0

- **0 HIGH**
- **2 MEDIUM** — Ai.1 `_specialize_fn` body-walk fix (v5.40.0
  carry; gates Ai.1+Ai.2 keyword sugar); Nu.2 macOS notarization
  (v5.33.0 carry; needs Mac access + Apple Developer cert).
- **~2 LOW** — Lf.4 variant-name collision (v5.46.0 split,
  defer-to-v6.0 candidate); Sf.\* Win64 `__mn_str_free` ABI fix
  (v5.53.1 carry; fix recipe locked in v5.53.0
  PRE_PHASE_AUDIT.md).

**Cl.\* arc CLOSED at v5.54.0.** v5.55.0 picks up either Ai.1
(Windows-doable) or Sf.\* (Win64 fix recipe ready).
