# v5.47.0 — Phase 0 audit

**Status:** complete.
**Author:** Phase 0 (Cl.0).
**Outcome:** PLAN/PROMPT premise confirmed. All four Cl.\* items
still open at v5.47.0 HEAD. Cl.1 LOC fits the bundle threshold;
v5.47.0 ships Cl.1 + Cl.2 + Cl.3 + Cl.4 in one release.
**Major load-bearing finding:** Cl.1 Lf.4 lives **only** in
`mapanare/semantic.py` (not `mapanare/lower.py`). Self-host
stage1 has the same bug, so the mirror in
`mapanare/self/semantic.mn` is non-trivial (not a no-op gate).

---

## Pre-flight

- VERSION at HEAD: `5.46.0` ✓
- `bash scripts/verify_fixed_point.sh` STRICT GREEN at 243,749
  lines / 0 diff ✓
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  → 102/102 ✓
- Working tree: `M AGENTS.md`, `M CLAUDE.md` (routine GitNexus
  index updates) — no compiler/runtime/stdlib drift pending.

---

## Per-Cl.* repro reconstruction

### Cl.1 Lf.4 — variant-name collision (STILL OPEN)

**Repro** (`/tmp/diag_lf4.mn`):

```mn
pub tipo NetworkError {
    | TransportLost(String)
    | BadUrl(String)
}
pub tipo ExitReason {
    | TransportLost(String)
    | Crashed(String)
}
fn main() -> Int {
    pon n: NetworkError = TransportLost("net")
    pon x: ExitReason = TransportLost("exit")
    print("net=ok")
    print("exit=ok")
    da 0
}
```

**Pre-fix observed:**

- Python bootstrap (`python3 -m mapanare emit-llvm`):
  ```
  /tmp/diag_lf4.mn:10:5: error: Type mismatch: declared type
  NetworkError but initial value is ExitReason
  ```
  Resolution at `mapanare/semantic.py::_check_let:1797` rejects
  because `_check_call` resolved `TransportLost` to whichever
  enum was last registered in `global_scope` (semantic.py:2069
  unconditionally calls `define()`, which overwrites prior).
- Self-host stage1 (`mapanare/self/mnc-stage1`):
  ```
  /tmp/test_lf4_stg1.mn:0:0: error: Type mismatch: declared type
  NetworkError but initial value is ExitReason
  ```
  **Same bug shape.** Self-host has the same global-shadow
  resolution policy.

**Falsifiability** — the construction itself works correctly
when the destination type is known *via function return type*
rather than let-annotation:

```mn
fn make_net_tl(s: String) -> NetworkError {
    da TransportLost(s)             // self-host: works (Eu.2)
}                                    // Python:    works (return path
                                    //            does not enforce
                                    //            type-compat in semantic)
```

Verified at HEAD: `make_net_tl("x")` followed by `match` correctly
fires `TransportLost(s) => 1` arm. Match-pattern dispatch is **not**
broken by collision; the bug is purely in semantic-checker
constructor-call resolution under let-binding annotation context.

**Fix sites:**
- `mapanare/semantic.py::_register_definitions` (~2050-2080):
  build a multimap `variant_name → list[(enum_name, return_type)]`.
- `mapanare/semantic.py::_check_call`: when resolving an
  Identifier that's a known multi-enum variant, consult the
  expected-type context.
- `mapanare/semantic.py::_check_let`: thread the binding's
  annotation type as expected-type context.
- `mapanare/self/semantic.mn`: mirror.

### Cl.2 — Agent stdlib ergonomic refactor (STILL OPEN — always was)

**Surface enumeration** (`grep -nE "^pub fn|^pub tipo .*Result"
stdlib/agent/{url,remote,node,supervision}.mn`):

Flat-tuple types to remove (or keep internal-only):

| File | Type | Lines |
|---|---|---|
| `stdlib/agent/url.mn` | `UrlParseResult` | 184 |
| `stdlib/agent/remote.mn` | `RemoteConnectResult` | 55 |
| `stdlib/agent/remote.mn` | `RemoteSendResult` | 114 |
| `stdlib/agent/remote.mn` | `RemoteRecvResult` | 149 |
| `stdlib/agent/node.mn` | `NodeListenResult` | 95 |
| `stdlib/agent/node.mn` | `NodeAcceptResult` | 169 |
| `stdlib/agent/node.mn` | `ConnSendResult` | 225 |
| `stdlib/agent/node.mn` | `ConnRecvResult` | 260 |

Public functions to refactor (return `Result<T, NetworkError>` instead):

| File | Function | Currently returns |
|---|---|---|
| `stdlib/agent/url.mn` | `parse_agent_url(s)` | `UrlParseResult` |
| `stdlib/agent/remote.mn` | `remote_agent_connect(url, key)` | `RemoteConnectResult` |
| `stdlib/agent/remote.mn` | `remote_agent_send(r, payload)` | `RemoteSendResult` |
| `stdlib/agent/remote.mn` | `remote_agent_recv(r)` | `RemoteRecvResult` |
| `stdlib/agent/remote.mn` | `remote_agent_send_typed_msg(...)` | `RemoteSendResult` |
| `stdlib/agent/remote.mn` | `remote_agent_ping(r)` | `RemoteSendResult` |
| `stdlib/agent/node.mn` | `node_listen(...)` | `NodeListenResult` |
| `stdlib/agent/node.mn` | `node_listen_tls(...)` | `NodeListenResult` |
| `stdlib/agent/node.mn` | `node_accept_one(n)` | `NodeAcceptResult` |
| `stdlib/agent/node.mn` | `conn_send_frame(c, mt, p)` | `ConnSendResult` |
| `stdlib/agent/node.mn` | `conn_recv_frame(c)` | `ConnRecvResult` |
| `stdlib/agent/supervision.mn` | `remote_agent_heartbeat_check(r)` | `RemoteSendResult` |

**Estimated refactor size:** ~250-400 LOC across 4 files plus
~50 LOC test updates. The internal callers within `stdlib/agent/`
that consume these flat-tuple results need destructure-pattern
migration (`if !r.ok` → `match r { Err(e) => ..., Ok(v) => ... }`).

**Lf.4 dependency:** Cl.2 internally uses both
`url::NetworkError::TransportLost` and
`supervision::RemoteExitReason::RemoteUnreachable` (renamed at
v5.43.0 to dodge Lf.4). Once Cl.1 lands, the v5.43.0 rename
**could** be reverted (`RemoteUnreachable` → `TransportLost`),
but doing so introduces a real variant-name collision that
exercises the new resolver. **v5.47.0 keeps the rename**: the
resolver fix is sound but the rename is cosmetic; reverting it
ships a different surface change without buying anything for
the panel docket. Tracked as v5.47.x candidate.

### Cl.3 — `stdlib/fs.mn::walk_dir` IR codegen (STILL OPEN)

**Repro** — direct compile of `stdlib/fs.mn` via Python emitter:

```bash
python3 -m mapanare emit-llvm stdlib/fs.mn -o /tmp/fs.ll  # succeeds
clang -c /tmp/fs.ll -o /tmp/fs.o
# /tmp/fs.ll:5187:19: error: invalid cast opcode for cast from
# 'ptr' to 'i64'
#  5187 |   %etz.112 = zext ptr %et.111 to i64
#       |                   ^
# 1 error generated.
```

**v5.46.0 Lf.\* did NOT close Cl.3.** The wrong-IR-shape class
is similar (extractvalue ptr → zext ptr to i64) but the trigger
condition is different: Cl.3 is the inner `match listing_result
{ Ok(names) => ... }` inside `pub fn walk(path) -> List<String>`
at `stdlib/fs.mn:469-510`. The receiving function's return type
is not `Result<...>`, so the v5.46.0 wrap-shape default fix
doesn't reach this site.

**Fix site:** `mapanare/lower.py::_lower_match` for
`Result<List<String>, FsError>` patterns. Likely a parallel-shape
fix to Lf.1 in the match-pattern destructure path rather than
the wrap path. Phase 1 will diagnose precisely.

### Cl.4 — `stdlib/net/websocket.mn` `str(byte)` decimal-stringification (STILL OPEN)

**Sites identified** (`grep -nE "str\(byte"
stdlib/net/websocket.mn`):

| Line | Context |
|---|---|
| 492, 495 | `read_frame` ext_len construction (uses `str(0)` literal — not byte-valued) |
| 498 | `result = str(byte0) + str(byte1) + ...` |
| 516, 525 | `build_send_frame` ext_len construction |
| 528 | `frame = str(byte0) + str(byte1) + ...` |
| 903 | `frame_data = str(byte0) + str(byte1) + ...` |

The load-bearing instances are 498, 528, 903 — `str(byte0)` /
`str(byte1)` where the operands are runtime bitfield ints
spanning 0..255. `str(0)` literal calls (492, 495, 516, 525)
are correct (`str(0)` produces `"0"`, decimal stringification
of literal zero is fine for those positions).

**Fix:** replace `str(byte0)` / `str(byte1)` with
`__mn_str_chr(byte0)` / `__mn_str_chr(byte1)` at lines 498, 528,
903. The literal-zero ext_len constructions need the same
treatment (528 uses `str(0)` for high bytes — those should also
become single-byte zero-byte strings). Phase 3 finalizes the
exact site list.

The v5.43.0 Da.0 fix extended `__mn_str_chr` to bytes 0..255 with
0x00 preservation. No new C runtime exports needed.

---

## Cl.1 LOC measurement

Sketched edits to `mapanare/semantic.py` and
`mapanare/self/semantic.mn`:

| Layer | Lines | Notes |
|---|---|---|
| `mapanare/semantic.py` registration multimap | ~10 | New `_variant_alternatives: dict[str, list[...]]` field; populate at line 2069. |
| `mapanare/semantic.py` `_check_call` resolver | ~25 | When `expr.callee.name` is in `_variant_alternatives` and `_expected_type` is an ENUM matching one alternative, return that alternative's type. |
| `mapanare/semantic.py` `_check_let` context | ~5 | Stash/restore `_expected_type = ann_type` around `_infer_expr(let.value)`. |
| `mapanare/self/semantic.mn` mirror | ~30-40 | Mirror the same shape. |
| **Total** | **~70-80 LOC** | — |

**Decision: BUNDLE into v5.47.0.** Per PLAN's Cl.0 guidance:
≤ 60 LOC = bundle; > 60 LOC tight; > 100 LOC = re-split. The
estimate sits at 70-80, in the tight-bundle range. Splitting Cl.1
to v5.47.1 would mean shipping v5.47.0 with only Cl.2 + Cl.4
(skipping the multi-release-arc closure that's the whole point
of pre-panel hygiene). The extra 10-20 LOC over the strict
bundle threshold is acceptable.

---

## Self-host source audit

```bash
# Variant-name collisions in self-host (would Cl.1 mirror affect
# stage1's own behavior?):
$ grep -hP "^\s*\|\s*[A-Z]\w*\s*\(?" mapanare/self/*.mn | sort | uniq -d
# (no output — no collisions in self-host)

# Self-host stage1 has the same Lf.4 bug shape (verified above):
$ mapanare/self/mnc-stage1 emit-llvm /tmp/diag_lf4.mn -o /tmp/lf4_stg1.ll
# error: Type mismatch: declared type NetworkError but initial value is ExitReason
```

Self-host's `_check_let`-equivalent in `mapanare/self/semantic.mn`
exercises the same global-shadow resolution policy. The bug
shape is identical to Python's. **The mirror is non-trivial**
(unlike v5.46.0's Lf.1+2+3 where self-host already had the fix).

Stage1 itself doesn't *exercise* the bug because no self-host
source file declares two enums with a colliding variant name.
The mirror fix is structural-symmetry only; STRICT preservation
is the load-bearing concern.

---

## PLAN/PROMPT deviations surfaced

1. **Lf.4 lives in semantic.py only — NOT lower.py.** PLAN
   hypothesized "match-pattern dispatch may need parallel edit."
   Phase 0 verified match-pattern resolution disambiguates by
   subject type already (the function parameter type carries
   through to `_lower_match`'s subject). The fix is purely in
   the semantic-checker constructor-call resolution under
   let-binding annotation context.
2. **Self-host mirror is non-trivial.** v5.46.0's Lf.\* mirror
   was a no-op gate (self-host already had Eu.2). v5.47.0's
   Cl.5 mirror is real work (stage1 has the bug too). LOC
   estimate ~30-40 in `mapanare/self/semantic.mn`.
3. **Cl.3 NOT closed by v5.46.0.** PLAN allowed for "Lf.\* may
   have closed Cl.3 as a side-effect." Phase 0 verified clang
   still rejects `extractvalue ptr ... 0` then `zext ptr to i64`
   in `stdlib/fs.mn` IR. Different fix-site than v5.46.0's
   wrap-default Result<T, E> fix; Cl.3 fix lives in
   `_lower_match` for `Result<List<X>, E>` destructure where the
   enclosing fn does NOT return Result.
4. **Cl.2 keeps the v5.43.0 `RemoteUnreachable` rename for now.**
   The Cl.1 fix structurally enables the rename revert, but the
   revert itself ships zero functional change and adds a real
   collision that exercises the new resolver path. Out of scope
   for v5.47.0; tracked as v5.47.x candidate.
5. **No new C runtime exports required.** Cl.4 uses existing
   `__mn_str_chr` (v5.43.0 Da.0 export). PLAN guarded against
   adding any; Phase 0 confirmed not needed.
6. **No drop-glue / aliasing edits expected.** Standard pytest
   gate suffices.

---

## Estimated LOC delta (refined post-Phase-0)

| Layer | Lines | Notes |
|---|---|---|
| `mapanare/semantic.py` | ~40 | Cl.1 multimap + resolver + let context. |
| `mapanare/self/semantic.mn` | ~40 | Cl.1 mirror. |
| `stdlib/agent/url.mn` | ~30 | Cl.2 `parse_agent_url` flat → Result. |
| `stdlib/agent/remote.mn` | ~80 | Cl.2 5 functions; type removal. |
| `stdlib/agent/node.mn` | ~120 | Cl.2 5 functions; 4 type removals. |
| `stdlib/agent/supervision.mn` | ~30 | Cl.2 1 function + caller migration. |
| `mapanare/lower.py` | ~10-20 | Cl.3 walk_dir match-arm IR shape fix. |
| `stdlib/net/websocket.mn` | ~10 | Cl.4 `str(byte)` → `__mn_str_chr`. |
| `tests/llvm/test_lowerer_fixes.py` | ~80 | Lf.4 case + falsifiability. |
| `tests/golden/103_*.mn` | ~50 | Cl.6 new golden. |
| `tests/llvm/test_llvm_link_all.py` | ~2 | golden-count 102 → 103. |
| `tests/stdlib/test_distributed_agents.py` | ~80 | New Result shape assertions. |
| CHANGELOG / SPEC / CLAUDE.md / SESSION_REPORT | ~250 | 4 entries (`### Fixed` × 3, `### Changed` × 1). |
| **Total** | **~820 LOC** | Larger than v5.46.0 (~370 LOC) but smaller than v5.43.0 (~2,500 LOC). |

---

## Falsifiability protocol

Per item:

1. **Cl.1 Lf.4** — `/tmp/diag_lf4.mn` rejected pre-fix (`Type
   mismatch`); compiles + runs cleanly post-fix. Revert
   `_variant_alternatives` lookup → re-fails with the recorded
   error.
2. **Cl.2 agent refactor** — `tests/stdlib/test_distributed_agents.py`
   asserts `Result<T, NetworkError>` shape post-fix; pre-fix
   asserted flat-tuple shape. Revert one function signature →
   pytest fails with the recorded shape signature.
3. **Cl.3 walk_dir** — `clang -c /tmp/fs.ll` fails pre-fix with
   `extractvalue ptr → zext ptr to i64`; succeeds post-fix.
4. **Cl.4 websocket str(byte)** — frame headers byte-compare
   correctly post-fix on byte values ≥ 128.

---

## Closeout

PRE_PHASE_AUDIT confirms PLAN/PROMPT premise. v5.47.0 ships
Cl.1 + Cl.2 + Cl.3 + Cl.4 in one bundle. Cl.5 self-host mirror
is real work (~30-40 LOC). STRICT preservation is the
load-bearing gate at Phase 6 closeout.
