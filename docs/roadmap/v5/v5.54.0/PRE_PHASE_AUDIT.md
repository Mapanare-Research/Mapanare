# v5.54.0 — PRE_PHASE_AUDIT

**Status:** PHASE 0 COMPLETE — three audits, **two load-bearing
reversals** of the PLAN.md premise require user direction before
implementation begins.

**Phase 0 gate result:** **HOLD.** Two of the three sub-arcs need
re-scoping per audit findings below.

---

## Cl.2 — agent stdlib ergonomic refactor (audit OK; bundle-or-split decision needed)

### Actual surface at HEAD (v5.53.0)

| File | LOC | Result-shaped struct types | Public fns returning them | Inferred internal helpers (`*_ok`/`*_err`) |
|---|---:|---|---:|---:|
| `stdlib/agent/url.mn` | 281 | `UrlParseResult` | 1 (`parse_agent_url`) | 2 (`url_parse_ok`, `url_parse_err`) |
| `stdlib/agent/node.mn` | 351 | `NodeListenResult`, `NodeAcceptResult`, `ConnSendResult`, `ConnRecvResult` | 5 (`node_listen`, `node_listen_tls`, `node_accept_one`, `conn_send_frame`, `conn_recv_frame`) | 8 |
| `stdlib/agent/remote.mn` | 223 | `RemoteConnectResult`, `RemoteSendResult`, `RemoteRecvResult` | 5 (`remote_agent_connect`, `remote_agent_send`, `remote_agent_recv`, `remote_agent_send_typed_msg`, `remote_agent_ping`) | 6 |
| `stdlib/agent/supervision.mn` | 411 | (reuses `RemoteSendResult`) | 1 (`remote_agent_heartbeat_check`) | 0 |
| **Total** | **1266** | **8 named types** | **12 pub fns** | **16 constructor helpers** |

**Refactor mechanic per file:** delete the `tipo *Result { ok, value..., err_kind, err_msg }` struct and the matching `*_ok` / `*_err` constructor helpers; change each pub fn signature from `-> *Result` to `-> Result<T, NetworkError>`; rewrite returns from `da listen_ok(h)` / `da listen_err(3, "msg")` to `da Ok(h)` / `da Err(MissingKey("msg"))` shape; update callers to `match result { Ok(v) => ..., Err(e) => ... }`.

### Caller counts (incl. own-module refs)

| Public fn | refs (stdlib + tests + examples) |
|---|---:|
| `parse_agent_url` | 17 |
| `node_listen` | 9 |
| `node_accept_one` | 5 |
| `conn_send_frame` | 4 |
| `conn_recv_frame` | 4 |
| `remote_agent_connect` | 8 |
| `remote_agent_send` | 8 |
| `remote_agent_recv` | 6 |
| `remote_agent_send_typed_msg` | 3 |
| `remote_agent_ping` | 3 |
| `remote_agent_heartbeat_check` | 4 |
| **Sum** | **71 refs** (incl. internal self-refs + tests) |

Conservative external-caller estimate (excluding own-module self-refs and test refs): ~30 unique caller sites across stdlib + tests + examples.

### LOC sizing (PLAN gate: split if > 600 LOC)

Per-file estimate:
- `url.mn`: delete ~20 LOC (struct + 2 helpers); rewrite ~10 LOC (1 fn body); update ~15 caller sites = **~50 LOC**.
- `node.mn`: delete ~80 LOC (4 structs + 8 helpers); rewrite ~50 LOC (5 fn bodies); update callers = **~180 LOC**.
- `remote.mn`: delete ~50 LOC (3 structs + 6 helpers); rewrite ~40 LOC (5 fn bodies) = **~130 LOC**.
- `supervision.mn`: rewrite ~10 LOC (1 fn body inheriting RemoteSendResult change) = **~25 LOC**.
- Cross-cluster caller updates (stdlib + tests + examples ~30 sites @ ~5 LOC each) = **~150 LOC**.
- Tests + docs = **~80 LOC**.

**Total: ~615 LOC.** At the PLAN's 600-LOC split threshold. Bundle decision recommended (single break-point release is cleaner than v5.54.0+v5.54.1 churn), but **user confirmation required.**

### NetworkError variant inventory (Cl.2.1+ landing target)

`NetworkError` is declared in `stdlib/agent/url.mn` (verify with full read; `ne_kind` in `node.mn` enumerates 1=BadUrl ... 15=Internal). The Err sites that currently pass `(err_kind: Int, err_msg: String)` need a single canonical NetworkError variant per err_kind. Recommend audit-and-table during Cl.2.1 implementation, not Phase 0.

### Decision needed

- **Q1.** Bundle all 4 files in v5.54.0 (~615 LOC, single break), or split: ship `url.mn` in v5.54.0 (canary) + remaining 3 files in v5.54.1?
- **Q2.** Atomic refactor across all 4 files, or per-file with cross-module callers temporarily held on a v5.43.0-shaped adapter during the 4-file rollout? **PLAN recommends atomic.**

### `mapanare/self/*.mn` STRICT impact

None. `grep -rn "node_listen\|remote_agent_connect\|parse_agent_url" mapanare/self/` returns no matches. The distributed-agent surface is stdlib-only, not used by self-host. **STRICT 3-stage fixed point preserves by construction.**

---

## Cl.3 — `stdlib/fs.mn::walk_dir` IR codegen (PREMISE STALE — RE-SCOPE OR CLOSE)

### Load-bearing finding

**`walk_dir` does not exist in `stdlib/fs.mn` at v5.53.0 HEAD.** The function the carry references no longer exists by that name. Current state:

| Function | Signature | Notes |
|---|---|---|
| `walk(path)` | `-> List<String>` (NOT Result-shaped) | Lines 469-510. Internally calls `match list_dir(current) { Ok(names) => ..., Err(e) => ... }`. Compiles + runs in the existing stdlib build. |
| `list_dir(path)` | `-> Result<List<String>, FsError>` | Lines 453-463. The actual Result-of-List shape. |

The Cl.3 carry from v5.40.0 / v5.47.0 was sized against a "walk_dir IR codegen failure: `extractvalue ptr ... 0` then `zext ptr to i64`". That site:
- Doesn't exist under the named function (renamed or removed).
- Existing `walk()` uses the bug-class shape (match-on-`Result<List<String>, FsError>`) at line 487 and compiles successfully against the v5.46.0+ lowerer.

### Reference in code

The only mention of `walk_dir` at HEAD is a comment in `stdlib/ai/ask_cache.mn:19`:

```
// pre-existing IR codegen issue around walk_dir's match-on-Result-of-
// List shape that's unrelated to v5.40.0; tracked outside scope
```

This comment is stale documentation referencing a function that has either been renamed to `walk` or never landed under the v5.40.0 name.

### Hypothesis: v5.46.0 Lf.\* closed Cl.3 implicitly

v5.46.0 Lf.\* fixed the wrap-shape default in Ok/Err constructors which was the root cause of the Result-receiving-destructure bug class. The walk_dir-class bug shape (match on `Result<List<String>, FsError>`) is structurally identical to the Lf.1/Lf.2/Lf.3 family — they all stem from the same constructor-side wrap-shape default. v5.40.0's bug surfaced because `walk_dir` (whatever it was named then) was the only stdlib caller exercising this shape; v5.46.0's fix to `mapanare/lower.py` Ok/Err branches transparently fixed walk_dir's call site too.

### Decision needed

- **Q3.** Close Cl.3 as **OBSOLETE** (implicitly fixed by v5.46.0 Lf.\*), update the stale comment in `stdlib/ai/ask_cache.mn:19`, and remove `walk_dir` from CARRY_FORWARD.md. Drop Phase 6 from v5.54.0 scope.
- **Q4.** Or: add a Cl.3-replacement falsifiability test against `list_dir` (the actual Result-returning fn) at `tests/stdlib/test_fs.py` to lock the v5.46.0 implicit closure, then close. ~20 LOC test addition; <0.5h.

**Recommendation: Q4** (lock the implicit closure with a falsifiability anchor; document the closure rationale in SESSION_REPORT.md). Defers the broader Result-destructure sweep risk-question to v6.0 borrow-checker scope.

---

## Cl.4r — `stdlib/net/websocket.mn` `str(byte)` sweep (audit OK; trivial)

### Residual sites at HEAD

`grep -nE '\bstr\(' stdlib/net/websocket.mn` returns 8 matches. Three are decimal-stringification of single byte values; five are `Int`-stringification of port/opcode values (intended decimal stringification, not bug sites).

| Line | Site | Bug? | Fix |
|---|---|---|---|
| 236 | `result = result + str(xored)` (xored is XOR'd byte for masking) | YES — byte→decimal in framing | `result = result + __mn_str_chr(xored)` |
| 493 | comment line (v5.47.0 Cl.4 historical note) | N/A | n/a (comment) |
| 646 | `str(parsed.port)` (port is Int — error msg) | NO | keep |
| 665 | `str(parsed.port)` (port is Int — Host header) | NO | keep |
| 743 | `payload = str(hi) + str(lo) + reason` (status code bytes) | YES — 2 byte sites | `__mn_str_chr(hi) + __mn_str_chr(lo) + reason` |
| 820 | `str(frame.opcode)` (opcode is Int — error msg) | NO | keep |
| 1023 | `str(cont_frame.opcode)` (opcode is Int — error msg) | NO | keep |
| 1121 | `close_payload: String = str(hi) + str(lo) + reason` (status code bytes) | YES — 2 byte sites | `__mn_str_chr(hi) + __mn_str_chr(lo) + reason` |

**Bug-site count: 5** (not the 11 v5.47.0 reported; v5.47.0 Cl.4 closed 6 of 11). Three logical sites, five `str()` calls because two sites have `str(hi) + str(lo)` pairs.

### Falsifiability

`tests/stdlib/test_websocket.py` exercises the framing path on the masked-frame branch (line 236 hot) and the close-frame branch (lines 743 + 1121 hot). Existing test coverage should detect a regression at all three sites; verify the test suite is wired to assert raw-byte payload bytes (not decimal-string bytes) after the fix. If not wired, add an explicit byte-assertion test (~15 LOC).

### Externs available

`__mn_str_chr` was added at v5.43.0 Da.0 per the v5.47.0 Cl.4 precedent. Verify the extern declaration is present in `stdlib/net/websocket.mn` (or accessible via include chain) before applying the sweep — if not, add the extern decl.

### Decision

No decision needed; mechanical sweep. **Estimated 20 LOC + 1 extern decl + 15 LOC test wiring = ~35 LOC total. <0.5h.**

---

## Phase 0 summary + recommendation

| Sub-arc | Status | Recommendation |
|---|---|---|
| **Cl.2** | Audit OK; sizing at ~615 LOC (at 600 split-line) | **Bundle in v5.54.0.** ~615 LOC is at the threshold but the alternative (4-file refactor split across 2 releases) is worse for the BREAKING annotation — external consumers refactor once, not twice. |
| **Cl.3** | **PREMISE STALE.** `walk_dir` does not exist; existing `walk()` uses the bug-class shape and compiles. Implicitly closed by v5.46.0 Lf.\*. | **Close as OBSOLETE; add 20-LOC `list_dir` falsifiability anchor at `tests/stdlib/test_fs.py` to lock the implicit closure (Q4).** Drop Phase 6. |
| **Cl.4r** | Audit OK; **5 bug-sites** (not 11). | Apply mechanical sweep. ~35 LOC. |

**Revised v5.54.0 scope:** Cl.2 (full 4-file refactor, ~615 LOC) + Cl.3-replacement (lock-the-closure test, ~20 LOC) + Cl.4r (sweep, ~35 LOC) = **~670 LOC total source delta + ~150 LOC tests/docs.** Single session feasible if Cl.2 caller-update web turns out clean; otherwise 2-session per PLAN estimate.

**STRICT 3-stage fixed point** preserves by construction — none of the three sub-arcs touches `mapanare/self/*.mn`.

---

## Awaiting user direction before Phase 1

1. **Q1** — Cl.2 bundle in v5.54.0 (~615 LOC, single break) or split v5.54.0 + v5.54.1?
2. **Q2** — Atomic vs per-file with adapter shim?
3. **Q3 / Q4** — Cl.3 close-as-obsolete + lock test, or full re-scope?
4. **Confirm** — Proceed with Cl.4r mechanical sweep at Phase 7?

Once these are answered, Phase 1 (Cl.2.1 url.mn canary) begins.
