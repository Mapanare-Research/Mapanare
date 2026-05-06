# v5 → v6.0 Carry-Forward Ledger

> Built from every "Inherits to vX.Y" / "Aggregate state
> entering vX.Y" line across v5.31-v5.46 PLANs + every
> panel-surfaced finding from v5.47.5 reviewers.
>
> Each item lands in **exactly one** of three buckets:
> - **(a) v6.0 PLAN input** — real work for v6.0 (borrow
>   checker territory, ABI changes, structural compiler work)
> - **(b) v5.47.x patch candidate** — small structural item
>   that doesn't need v6.0 scope (docs polish, infra carry,
>   ergonomic ship)
> - **(c) retired** — closed in a later release; requirement
>   evaporated; aspirational and de-scoped
>
> No fourth category. When in doubt, default to (b).
>
> The v5-era `.reviews/CARRY_FORWARD.md` ledger is replaced
> by this file going forward (see Boa Bo.New1).

---

## (a) v6.0 PLAN inputs

Real work for v6.0. Cumulative target: ~12-15 items split
across v6.0.0 / v6.0.1 / v6.0.2 sub-releases per the v5.43.0
sizing lesson.

| Item | Source | Severity | Notes |
|---|---|---|---|
| **Borrow checker / multi-level alias analysis** | v5.6.6 + v5.27.0 carry; `Rt.04` at v5.7.1/v5.11.0/v5.22.0 panels | HIGH | The v6.0 thesis. Closes the depth-2 struct→list→string drop-glue path that was the original Lk.1 driver. Likely a multi-release split (Bc.1.0 inference; Bc.2.0 enforcement; Bc.3.0 hard `{}` removal) per Cp.5 retro recommendation. |
| **Hard removal of `{}` syntax** | v5.19.0 Te.3 soft deprecation; v6.0 promised | HIGH | `{}` warns since v5.19.0; SPEC §22 deprecation cycle terminates at v6.0. Coincides with single-line `if x: y` rescope. |
| **Static view-aliasing safety (Ts.2 stopgap)** | v5.45.0 cookbook explicit | MEDIUM | v5.45.0 ships runtime substrate (refcount on `mapanare_tensor_t`); static borrow-check for view aliasing is v6.0. |
| **`_specialize_fn` body-walk fix** (nested generic intrinsic substitution) | v5.40.0 Ai.1 deferral | MEDIUM | Gates `ask` keyword sugar + `ask_typed::<T>` + generic stdlib fns calling generic intrinsics. Confirmed empirically at v5.40.0 Phase 0 — `from_json::<T>` inside generic wrapper substitutes literal type-variable name "T". |
| **Strided / non-contiguous tensors** (transpose, permute, reverse step) | v5.45.0 deferred | MEDIUM | Forces `mapanare_tensor_t` ABI change. Out of v5.45.0 scope by Phase 0 audit. |
| **GPU tensor surface unification** (`stdlib/gpu/tensor.mn::GpuTensor` vs builtin `Tensor`) | Cobra Cb.3 (v5.41.0 / v5.45.0 carry) | MEDIUM | Two parallel tensor surfaces — design debt. Recommend elevating `Tensor` as single surface with GPU-bound ops as method dispatches. |
| **Distributed-supervision orchestration** | Cobra Cb.5 (v5.43.0 deferred) | MEDIUM | Substrate exists (heartbeat primitive, ChildExited codec, classify_remote_exit); wired-together orchestrator is v5.43.x+. Manifesto-arc completion item. |
| **Closure-form supervisor spawn API** | Cobra Cb.1 (v5.42.0 deferred) | LOW | Gated on fn-typed-param fix (which v6.0 borrow checker may unblock). Then `spawn_supervised(spec, factory)` shape. |
| **Registry-side package signing** | Mamba Ma.3 (v5.44.0 carry) | MEDIUM | Pre-public-registry-launch requirement. v5.44.0 reserved-source-literal contract supports signing additively. |
| **STRICT 3-stage fixed-point gate carve-out** | Rattler Ra.New2 | MEDIUM | v6.0 borrow checker work is structurally novel; preserve the 50-release strict streak or document explicitly why the bridge can't. Likely a multi-release v6.0.0 / v6.0.1 / v6.0.2 split. |
| **v6.0 perf-baseline establishment release** | Viper V.New1 | MEDIUM | v6.0 borrow checker may shift compile-time + runtime cost profiles. Establish baselines first; gives borrow-checker work numbers to beat / hold. |
| **Emitter-shortcut audit pass** | Mamba Ma.1 | LOW | Sweep `mapanare/emit_llvm_text.py` for remaining unconditional shortcuts (regex_match, http_get, etc.) that may exhibit v5.39.0 Cr.0 latent class. |
| **Stage2-binary teardown crash (RC=3)** | v4.30.0 PLAN, 70+ releases stale | LOW | Papered over by `set +e` in `verify_fixed_point.sh:124-137`; v6.0 cleanup window. |
| **Single-line `if x: y`** (v5.21.1 explicit rescope) | v5.21.1 H.4 | LOW | Coincides with `{}` hard removal. |

**Process inputs (not numbered items but PLAN-shaping):**

| Process pattern | Source | Notes |
|---|---|---|
| **PRE_PHASE_AUDIT.md mandatory** at every v6.x release | Anaconda An.1 (10+ examples in v5.31-v5.47.0 arc) | Cost ~1h/release; saves rebumps + scope drift. |
| **Convergent-recommendation pattern** explicit | Anaconda + Boa + Rattler convergent at v5.47.5 | When 2+ reviewers independently surface same finding shape, treat as load-bearing. |
| **Multi-release escalation → DEADLINE** | Boa Bo.0 (Tn.1 closure pattern) | Carries that escalate through 3+ releases get hard deadline applied. |
| **Staged closure shape** as template for multi-bug closeout arcs | Anaconda An.New1 (v5.39.x model) | One TypeKind / branch / sub-feature per release with documented invariant decision. |
| **Adversarial-input testing** as default for cross-process / network-bound / parser-bound surfaces | Mamba Ma.New1 (v5.43.0 1000-iteration fuzz model) | Mandatory in v6.0 for any new such surface. |
| **RFC corpus discipline** for crypto / security-load-bearing surfaces | Mamba Ma.4 (v5.39.0 Cr.\* model) | Mandatory for any new such surface. |
| **Wire-format engineering shape** as v6.0 template | Cobra Cb.0 (v5.43.0 Da.\* model) | For any future cross-network contract (e.g., borrow-checker IPC if it grows one). |

---

## (b) v5.47.x patch candidates

Small structural items; close cleanly before or alongside v6.0
PLAN drafting; not load-bearing for v6.0 correctness.

### Already named (v5.47.1 docket per v5.47.0 SESSION_REPORT)

| Item | Source | Severity | Notes |
|---|---|---|---|
| **Cl.2 — agent stdlib ergonomic refactor** (flat-tuple → `Result<T, NetworkError>`) | v5.47.0 deferred | MEDIUM | ~400 LOC across `stdlib/agent/{url,remote,node,supervision}.mn` + ~50 internal callers + test updates. Structurally unblocked by v5.46.0 Lf.\* + v5.47.0 Cl.1. |
| **Cl.3 — `stdlib/fs.mn::walk_dir` IR codegen** | v5.47.0 deferred (v5.40.0 carry) | LOW | Receiver-side wrong-shape Result aggregate bug; different fix-site from v5.46.0 constructor-side. |

### Proposed (v5.47.2 docket — docs/process polish)

| Item | Source | Severity | Notes |
|---|---|---|---|
| **`.reviews/CARRY_FORWARD.md` refresh** with v5.31-v5.47.0 closures | Boa Bo.1 (recurring An.1-class) | MEDIUM | Mirror v5.28.0 hygiene-pass shape: append v5.31/v5.32/.../v5.47.0 closure rows. v5-era ledger should reflect v5-era reality before V5_TO_V6_CARRY.md takes over. |
| **`tests/KNOWN_FAILURES.md` ledger** | Rattler Ra.3 + Anaconda An.3 + Boa Bo.2 (3-axis convergent) | LOW | Single source-of-truth for pre-existing baseline failures (`test_run_hello`, `test_reshape_size_mismatch_aborts`, `test_link_and_run[98_*/99_*]`). Closes the per-cycle re-inventory pattern. |
| **Localized README refresh** (es/pt/zh-CN native-compiler subsections) | Coral Co.1 (v5.28.0 H.4 recurrence) | MEDIUM | v5.31-v5.47.0 arc summary; 50-release streak; 244k lines; 103/103 goldens. One-shot well-scoped doc work; ~2-3 hours. |
| **`docs/stdlib/INDEX.md`** top-level cookbook landing page | Coral Co.2 / Co.New1 | LOW | Lists all 8 cookbooks (time, sql, json, http, regex, crypto, ai, agent) + one-line description each. |
| **manifesto.md As.\*+Da.\* section** | Coral Co.3 | LOW | "v5 closed: agents are cross-machine" pointing at v5.42.0 + v5.43.0. |

### Other v5.47.x slot candidates (lower priority)

| Item | Source | Severity | Notes |
|---|---|---|---|
| **macOS notarization** (proper Developer ID, replace ad-hoc-sign) | v5.33.0 Nu.2 | MEDIUM | Needs paid Apple Developer cert; not a code change. v6.0+ tracking acceptable. |
| **Linux aarch64 + macOS x86_64 native `mnc` tarballs** | v5.33.0 Nu.3 | LOW | No native runner / cross-compile pipeline. v6.0+ candidate. |
| **AEAD + Ed25519/X25519 + Argon2id** ship release | Mamba Ma.2 (v5.39.0 → v5.39.1 deferral) | LOW | Each has known correctness trap; structurally independent. Ship as dedicated v5.x release with own RFC corpus + adversarial gates. |
| **`EVP_MAC` migration** for HMAC over SHA-3/BLAKE2 | Mamba Ma.New2 | LOW | Niche; HMAC-SHA256/SHA-512 covers ~95% of HMAC use. |
| **JSON serde 1MB benchmark** | Viper V.2 | LOW | Establishes binary-fast-path ROI conversation. |
| **Supervision restart latency benchmark** | Viper V.3 | LOW | Anchors future supervisor-optimization conversations. |
| **Pike VM regex rewrite** (alternative to PCRE2 dlopen) | v5.38.0 Re.6 carry | LOW | PCRE2 surface works; Pike VM removes dlopen dep at cost of feature parity. v6.0+ candidate. |
| **Closure-chain HTTP middleware** | v5.37.0 Ht.2 carry | LOW | Registration-table works; closure-chain ergonomic; gated on fn-typed-param fix. |
| **Bounded-RSS HTTP streamer** (Ht.4.B) | v5.37.0 carry | LOW | Encoders ship; pump driver needs `__mn_tcp_send_bytes(fd, ptr, len)`. |
| **Re.6 `pon m: Option<Match>` allocation bug** | v5.38.0 carry | LOW | Same class as v5.36.0 Js.0.B (Result wrap-shape mismatch on Option). |
| **Async per-connection heartbeat task** | v5.43.0 deferred | LOW | Requires fn-typed callbacks or dedicated agent threads. |
| **Auto-route inbound MSG_CHILD_EXITED frames** | v5.43.0 deferred | LOW | Cross-references supervision arc. |
| **Generic `RemoteAgent<T>` with auto-`to_json`** | v5.43.0 deferred | LOW | Blocked on Ai.1. |
| **Streaming JSON true chunked I/O** | v5.36.0 Js.3 LITE | LOW | Needs native `Bytes` type. |
| **Native `Bytes` type** | v5.36.0 + v5.39.0 carry | LOW | Cross-cutting; v6.0 candidate if it becomes load-bearing. |
| **`tests/llvm/test_lowerer_fixes.py` parser-ergonomic** `=> return EXPR` after match arm | v5.39.7 carry | LOW | Block-form `=> { ok = ... }` works. |
| **Hash-dispatched enum decode** (vs linear cascade) | v5.39.7 carry | LOW | <20 variants is fine linear. |
| **Internally / adjacently tagged JSON enum shapes** | v5.39.7 carry | LOW | Externally-tagged is documented invariant. |
| **Custom serde rename attributes** | v5.39.7 carry | LOW | Cosmetic ergonomic. |
| **Sub-second precision in date/time broken-down forms** | v5.34.0 carry | LOW | Cosmetic. |
| **Full strftime expansion** | v5.34.0 carry | LOW | Cosmetic. |
| **Named timezone database (`tz_named` beyond UTC + system-local)** | v5.34.0 explicit defer | LOW | Cosmetic; non-negotiable defer was correct. |
| **Operator-overload infrastructure** (`trait Add` etc.) | v5.34.0 Dt.5 spike-deferred | LOW | Unblocks date/time arithmetic ergonomics. |
| **Cross-module emitter mangling/extern-propagation fix** | v5.34.0 directory-vs-flat-file deviation | LOW | Blocks directory-shape stdlib modules. |
| **Sq.5 sqlite statement cache** | v5.35.0 deferred | LOW | Manual prepare+reset+bind+step works; auto-cache is uglier without first-class state. |

---

## (c) Retired

Closed in a later release; requirement evaporated; aspirational
and de-scoped.

| Item | Original source | Reason |
|---|---|---|
| **Tn.1 95-golden link gate** | v5.28.0 panel rec | Closed v5.35.0 Sq.0 |
| **Js.4.B runtime SEGV** | v5.36.0 deferred | Closed v5.39.2 Js.4.B.2 |
| **Js.4.C nested-struct encode** | v5.39.2 deferred | Closed v5.39.3 |
| **Js.4.D LIST encode/decode** | v5.39.3 deferred | Closed v5.39.4 + v5.39.5 |
| **Js.4.E MAP encode/decode** | v5.39.5 deferred | Closed v5.39.6 |
| **Js.4.F ENUM encode/decode** | v5.39.6 deferred | Closed v5.39.7 |
| **Lf.1+Lf.2+Lf.3** (v5.43.0 lowerer bugs) | v5.43.0 deferred | Closed v5.46.0 |
| **Lf.4** (variant-name collision) | v5.46.0 deferred | Closed v5.47.0 Cl.1 |
| **Da.0** (`__mn_str_chr` 0..127 cap) | v5.43.0 surfaced | Closed v5.43.0 |
| **Cl.4** (websocket.mn `str(byte)` decimal-stringification) | v5.43.0 carry | Closed v5.47.0 |
| **Mb.10** (`__mn_indent_to_braces` Win64 ABI) | v5.28.0 panel surface | Closed v5.29.0 |
| **Pv.7** (`clean-build-test` race) | v5.28.0 panel surface | Closed v5.29.0 |
| **Pv.8** (agent-state timing in test_c_runtime.c) | v5.28.0 panel surface | Closed v5.29.0 |
| **SPEC header drift** | v5.30.0 → v5.33.0 | Closed v5.33.1 Hd.\* |
| **`check_cadence.py` enforced gate** | v5.24.0 Hy.3 | Demoted to informational at v5.33.2 Cd.\* per project-memory directive |
| **Banner "[dev mode]" lie on release installs** | publish-run-#50 | Closed v5.31.0 Bn.\* |
| **Windows SDK ZIP `mnc.exe` was PyInstaller copy** | v5.12.0 oversight surfaced at v5.31.0 | Closed v5.32.0 Nw.\* |
| **Tensor reshape on LLVM** | v5.31.0+ "Not yet on LLVM" | Closed v5.41.0 Ts.1 |
| **Tensor mutable views** | v5.31.0+ "Not yet on LLVM" | Closed v5.45.0 Ts.2 |
| **Tensor stepped slices** | v5.31.0+ "Not yet on LLVM" | Closed v5.45.0 Ts.3 |
| **Js.0** (`_san` sanitizer over-stripping `%`) | v5.36.0 Phase 0 surface | Closed v5.36.0 Js.0 |
| **Js.0.B** (Result wrap-shape mismatch in `_do_wrap_ok`/`_do_wrap_err`) | v5.36.0 Phase 0 surface | Closed v5.36.0 Js.0.B |
| **Cr.0** (emitter shortcut bypass) | v5.39.0 RFC corpus surfaced | Closed v5.39.0 Cr.0 |
| **Mc.\* parity arc** (Mc.8 + Mc.9 + Tk.1 formatter polish) | v5.13.0 carry | Closed v5.27.0 |
| **Js.6 sqlite `Value::Json` variant** | v5.36.0 deferred (blocked on Js.4.B) | Routed to v5.36.x; Js.4.B closed v5.39.2 — re-open if user demand surfaces, otherwise retire silently |
| **Mb.\* arc** | v5.22.0 carry | CLOSED at v5.29.0 |
| **Pv.\* arc** | v5.25.0 ship | CLOSED at v5.32.0/v5.33.0 |
| **Js.4.\* arc** | v5.36.0 ship | CLOSED at v5.39.7 |
| **Tensor closeout arc** | v5.41.0 begin | CLOSED at v5.45.0 |
| **Manifesto arc** | v5.40.0 begin | CLOSED at v5.43.0 |
| **Package-system runway** | v5.44.0 ship | CLOSED at v5.44.1 |
| **Foundation arc** | v5.31.0 begin | CLOSED at v5.33.0 |
| **Stdlib gap-close arc** | v5.34.0 begin | CLOSED at v5.39.0 |
| **`to_terse` empty `#{}` rewriter bug** | v5.27.0 Tk.1 closed | RETIRED — closed v5.27.0 |
| **Spanish/Portuguese/Chinese cookbook localization** | Coral Co.New2 (fresh) | RETIRED — not v5.47.x scope; not v6.0 scope; tracked as future-consideration only |

---

## v6.0 PLAN draft inputs (forward)

After v5.47.5 ships, `docs/roadmap/v6/PLAN.md` drafts begin
with the (a) bucket above as input. Recommended structure
(per Cp.5 retro lesson on v5.43.0 sizing):

- **v6.0.0** — Borrow checker inference + STRICT gate
  carve-out documentation (Bc.1.0)
- **v6.0.1** — Borrow checker enforcement + view-aliasing
  static safety + perf-baseline establishment (Bc.2.0)
- **v6.0.2** — Hard removal of `{}` + single-line `if x: y`
  rescope coincidence + tensor-surface unification (Bc.3.0)
- **v6.0.x** — `_specialize_fn` body-walk; distributed-
  supervision orchestration; registry-side package signing
  (each in own minor, per stair-step closure shape)

Process inputs (PRE_PHASE_AUDIT mandatory; convergent-
recommendation pattern explicit; adversarial-input testing
default; RFC corpus discipline) apply at every v6.x release.

---

## Update protocol (going forward)

Per Boa Bo.New1: **at every v6.x release, append closure rows
to this file** in the (c) section, mirroring the v5.28.0
hygiene-pass shape. The PROMPT/PLAN cross-walk for each new
v6.x release should cite this ledger.

The v5-era `.reviews/CARRY_FORWARD.md` closes with v5.47.5
and is preserved as historical record (recommend a v5.47.x
patch refresh — Boa Bo.1 — to reflect v5.31-v5.47.0 closures
honestly before v6.0 begins).

---

## End of ledger

**Status:** v5 → v6.0 carry-forward complete.
**(a) v6.0 PLAN inputs:** 14 items + 7 process patterns
**(b) v5.47.x patches:** 5 named (Cl.2/3 + 5 docs/process)
+ 23 lower-priority candidates
**(c) retired:** 33 items closed in scope
