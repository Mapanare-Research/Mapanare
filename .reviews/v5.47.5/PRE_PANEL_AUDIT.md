# v5.47.5 Pre-Panel Audit — End-of-v5 Closeout

> **Cadence framing.** Last full panel was v5.28.0 RE-PANEL
> (aggregate 9.72; Option A; reviewed v5.23.0 → v5.27.0). v5.47.5
> is **19 minor versions past** the v5.28.0 panel — the longest
> deliberate cadence-gap in v5 history. Per the v5.28.0 directive
> (recorded in `feedback_no_forced_cadence_gates` user-memory and
> codified at v5.33.2 Cd.\* — `check_cadence.py` is informational
> REMINDER, not enforced) **panels run at the end of an arc, not
> in the middle.** v5.47.5 closes that gap in one shot, on
> purpose. The v5.45.0 panel slot was deferred to v5.47.5 so
> v5.45.0 (Ts.\* tensor closeout) + v5.46.0 (Lf.\* lowerer-bug
> closeout) + v5.47.0 (Cl.\* pre-panel hygiene) could close
> three long-standing debts before the panel audits ecosystem
> readiness for v6.0. **Reviewers must not dock for the
> cadence gap** — surface this entry if asked.
>
> **Pre-panel posture.** v5.47.0 was a hygiene-ahead-of-panel
> cleanup mirroring the v5.28.0 precedent (where H.1–H.7
> closures landed pre-panel-cut so reviewers couldn't dock for
> drift the lead's own audit had already found). v5.47.0
> closed **Cl.1** (Lf.4 variant-name collision across both
> Python bootstrap and self-host stage1) and **Cl.4**
> (websocket.mn `str(byte)` decimal-stringification cleanup),
> and split **Cl.2** (agent stdlib ergonomic refactor —
> v5.43.0 flat-tuple → `Result<T, NetworkError>`) and **Cl.3**
> (fs.mn walk_dir IR codegen) to v5.47.1 because Phase 0
> verified each is structurally non-trivial. v5.47.0
> aggregate state entering panel: **0 HIGH / 2 MEDIUM
> (Cl.2 + Cl.3 splits; macOS notarization carry from
> v5.33.0 Nu.2) / ~6 LOW**.

**Audit date:** 2026-05-06
**Target version:** v5.47.5 (post-v5.47.0 hygiene closure)
**Arc graded:** v5.31.0 → v5.47.0 (17 releases, 17 SESSION_REPORTs)
**Decision rule:** v5-gate mechanical — mean ≥ 9.5 = Option A;
9.0-9.5 = Option A with notes; <9.0 = Option B/C.

---

## 1. Scope

The full v5.31.0 → v5.47.0 arc clusters into six structural
sub-arcs:

| Sub-arc | Releases | Codenames | Closure status |
|---|---|---|---|
| Foundation (banner + native binaries) | v5.31.0, v5.32.0, v5.33.0, v5.33.1, v5.33.2 | Bn.\*, Nw.\*, Nu.\*, Hd.\*, Cd.\* | CLOSED |
| Stdlib gap-close | v5.34.0, v5.35.0, v5.36.0, v5.37.0, v5.38.0, v5.39.0 + 7 Js.4 sub-releases (v5.39.1-7) | Dt.\*, Sq.\*, Js.\*, Ht.\*, Re.\*, Cr.\* | CLOSED |
| Manifesto | v5.40.0, v5.42.0, v5.43.0 | Ai.\*, As.\*, Da.\* | CLOSED |
| Tensor closeout | v5.41.0, v5.45.0 | Ts.1, Ts.2 + Ts.3 | CLOSED |
| Package-system runway | v5.44.0, v5.44.1 | Ps.\* | CLOSED |
| v5.43.0 lowerer-bug closeout + pre-panel hygiene | v5.46.0, v5.47.0 | Lf.\*, Cl.\* | CLOSED |

This is the longest single-panel scope in project history (the
v5.28.0 RE-PANEL covered 8 releases; v5.47.5 covers 17 substantive
releases plus v5.39.1–v5.39.7 sub-releases that closed the Js.4
typed-serde arc). **Reviewers should grade against the absolute
v5-gate decision rule, not the v5.28.0 9.72 ceiling** —
v5.47.5 may score lower simply because scope is wider, not
because work is worse.

---

## 2. Per-release SHIPPED / PARTIAL / DEFERRED matrix

State at v5.47.0 HEAD entering panel cut. Cross-checked against
each release's SESSION_REPORT and the symbol/file at HEAD where
testable.

### Foundation arc (5 releases)

| Release | ID | State | Notes |
|---|---|---|---|
| v5.31.0 | Bn.1 | SHIPPED | argv-peek banner skip |
| v5.31.0 | Bn.2 | SHIPPED | `_is_release_install()` helper |
| v5.31.0 | Bn.3 | SHIPPED | banner reword + path embed |
| v5.31.0 | Bn.4 | SHIPPED | `tests/test_cli_banner.py` (5 cases) |
| v5.31.0 | Bn.5 | SHIPPED | PyInstaller entry sets `MAPANARE_RELEASE=1` |
| v5.32.0 | Nw.1 | DEVIATION | reused build-native artifact (approach b) instead of cross-compile (approach a) — PROMPT-allowed fallback |
| v5.32.0 | Nw.2 | SHIPPED | `mnc-windows-x64-native` artifact + staging |
| v5.32.0 | Nw.3 | SHIPPED | native-binary fallback wrapper in `__main__.py` |
| v5.32.0 | Nw.4 | SHIPPED | smoke gates (in-job + published) |
| v5.32.0 | Nw.5 | SHIPPED | minimal ZIP also gets native `mnc.exe` |
| v5.32.0 | Nw.6 | SHIPPED | docs (CLAUDE Native-First, README) |
| v5.33.0 | Nu.1 | SHIPPED | Linux x86_64 native `mnc` |
| v5.33.0 | Nu.2 | PARTIAL | macOS arm64 native `mnc` (ad-hoc-signed; notarization deferred) |
| v5.33.0 | Nu.3 | DEFERRED | Linux aarch64 + macOS x86_64 — v5.34.0+ carry |
| v5.33.0 | Nu.4 | SHIPPED | smoke gates (Layer 1 in-job + Layer 2 published) |
| v5.33.0 | Nu.5 | SHIPPED | `_native_binary_name()` testable helper |
| v5.33.0 | Nu.6 | SHIPPED | docs |
| v5.33.1 | Hd.1+Hd.2 | SHIPPED | SPEC.md header re-sync; `check_doc_freshness.py` GREEN |
| v5.33.2 | Cd.1+Cd.2 | SHIPPED | `check_cadence.py` demoted to informational REMINDER + tests updated |

**Foundation arc closure:** complete. Native-frontend bundling
shipped on all three primary platforms (Linux x86_64, macOS
arm64, Windows x64). The two deferred arches (Linux aarch64,
macOS x86_64) are infrastructure-bound (no native runner /
cross-compile pipeline); routing to v6.0+ candidate set is
reasonable.

### Stdlib gap-close arc (6 + 7 releases)

| Release | ID | State | Notes |
|---|---|---|---|
| v5.34.0 | Dt.1+Dt.2+Dt.3+Dt.4+Dt.5+Dt.6+Dt.7+Dt.8+Dt.9 | SHIPPED | first-class date/time stdlib; ~723 LOC `stdlib/time.mn` + ~340 LOC `mapanare_time.c` + 6 new C exports + 9 pytest cases + cookbook |
| v5.34.0 | Dt.5 | DEVIATION | operator overloads spike-deferred (`impl Add for Dur` not lowered); free-function method form (`duration_add(a, b)`) shipped |
| v5.34.0 | (single-file vs directory) | DEVIATION | shipped as `stdlib/time.mn` not `stdlib/time/` (cross-module emitter limitation) |
| v5.35.0 | Sq.0 | SHIPPED | (formerly Tn.1) `tests/llvm/test_llvm_link_all.py` link-and-run gate for all 95 goldens — closed v5.28.0 cadence directive 6 releases late, bundled into v5.35.0 |
| v5.35.0 | Sq.1+Sq.2+Sq.3+Sq.4+Sq.6+Sq.7+Sq.8+Sq.9 | SHIPPED | first-class sqlite3 driver; ~720 LOC `stdlib/sql/sqlite.mn` + 8 new C exports + 7 GREEN tests + cookbook |
| v5.35.0 | Sq.5 | DEFERRED | statement cache — v5.36.0 candidate (manual prepare+reset+bind+step pattern documented) |
| v5.36.0 | Js.0 | SHIPPED | emitter `_san` sanitizer fix (`%` over-stripping) |
| v5.36.0 | Js.0.B | SHIPPED | `_do_wrap_ok` / `_do_wrap_err` Result wrap-shape fix |
| v5.36.0 | Js.1 | SHIPPED | RFC 8259 strict parse (leading-zero, control chars, depth cap); 283/318 corpus CONFORM |
| v5.36.0 | Js.2 | SHIPPED | configurable-indent `to_json_pretty` + aliases |
| v5.36.0 | Js.3 | PARTIAL (LITE) | streaming API surface; chunked I/O deferred to native `Bytes` type |
| v5.36.0 | Js.4 (Shape B) | PARTIAL | `to_json::<T>` + `from_json::<T>` typed-serde intrinsics; `from_json` SEGV at v5.36.0 → closed across v5.39.1-v5.39.7 |
| v5.36.0 | Js.5 | SHIPPED | corpus regression gate (CONFORM ≥ 283) |
| v5.36.0 | Js.7 | SHIPPED | `docs/stdlib/json.md` |
| v5.36.0 | Js.6 | DEFERRED | sqlite Value::Json variant — blocked on Js.4.B fix; rescoped |
| v5.37.0 | Ht.1+Ht.2+Ht.4+Ht.6+Ht.7+Ht.8 | SHIPPED | HTTP App / router / middleware / streaming encoders |
| v5.37.0 | Ht.2 | DEVIATION | registration-table middleware (not closure-chain) — fn-typed param invocation broken in v5.x |
| v5.37.0 | Ht.1 | DEVIATION | ordered list of compiled patterns (not recursive trie) |
| v5.37.0 | Ht.3 | DEVIATION | docs-only (websocket.mn already shipped RFC 6455) |
| v5.37.0 | Ht.4 | DEVIATION | encoders only (bounded-RSS streamer needs `__mn_tcp_send_bytes`) — Ht.4.B v5.38.0+ |
| v5.37.0 | Ht.5 | DEFERRED | typed-handler shorthand — blocked on Js.4.B; rescoped |
| v5.38.0 | Re.1+Re.2+Re.3+Re.4+Re.5 | SHIPPED | regex Regex-first API + Captures + named groups + tests + cookbook |
| v5.38.0 | (Pike VM rewrite) | DEVIATION | Phase 0 found PCRE2 wrapper already shipped; lead-approved keeping PCRE2 |
| v5.38.0 | (two pre-existing fixes) | SHIPPED | `pon _:` parser non-acceptance + `parse_named_groups` substr semantics |
| v5.38.0 | Re.6 | DEFERRED | `pon m: Option<Match>` allocation bug — same class as v5.36.0 Js.0.B; v5.38.x candidate |
| v5.39.0 | Cr.0 | SHIPPED | emitter shortcut bypass fix (`emit_llvm_text.py:3713-3776`) — load-bearing prerequisite for Cr.\* |
| v5.39.0 | Cr.1+Cr.2+Cr.5+Cr.7+Cr.8+Cr.9 | SHIPPED | hashing additions (sha3_256, blake2b) + streaming digest + HMAC-SHA512 + constant_time_eq + random_u64/range + 10 new C exports + RFC corpus + cookbook |
| v5.39.0 | Cr.3+Cr.4+Cr.6 | DEFERRED | AEAD + Ed25519/X25519 + password KDFs — v5.39.1 explicit deferral (correctness traps; structural independence) |
| v5.39.1 | Js.4.B.1 | SHIPPED | IR-emission shape fix (no-import case); `_ensure_json_types_registered()` helper |
| v5.39.2 | Js.4.B.2 | SHIPPED | runtime SEGV fix in `_do_map_init` empty-literal type derivation; link-and-run regression suite |
| v5.39.3 | Js.4.C | SHIPPED | `to_json::<T>` nested-struct recursion |
| v5.39.4 | Js.4.D.1+Js.4.D.2 | SHIPPED | LIST encode + STRUCT decode |
| v5.39.5 | Js.4.D.3 | SHIPPED | LIST decode (in-place ListPush across loop boundary) |
| v5.39.6 | Js.4.E.1+Js.4.E.2 | SHIPPED | MAP encode + decode (string-key only invariant) |
| v5.39.7 | Js.4.F.0+Js.4.F.1+Js.4.F.2 | SHIPPED | ENUM encode + decode (externally-tagged); typed-serde round-trip CLOSED |

**Stdlib gap-close arc closure:** complete. Six new stdlib
modules + Js.4 typed-serde round-trip end-to-end. The
emitter-shortcut bypass class (Js.0 / Js.0.B / Cr.0) surfaced
under three independent stdlib extensions and was closed
structurally each time, not symptomatically. The Js.4 staged
closure (v5.39.1 → v5.39.7) is exemplary discipline — one
TypeKind per release with documented invariant decisions.

### Manifesto arc (3 releases)

| Release | ID | State | Notes |
|---|---|---|---|
| v5.40.0 | Ai.0 (function-syntax fall-back) | SHIPPED | `ask_text(prompt) -> Result<String, AskError>` + `ask_with_schema(prompt, schema)` |
| v5.40.0 | Ai.3+Ai.4+Ai.5+Ai.6+Ai.7 | SHIPPED | `stdlib/ai/ask.mn` + `stdlib/ai/ask_cache.mn` + 5 deterministic tests + plan_generator demo + cookbook |
| v5.40.0 | Ai.1+Ai.2 | DEFERRED | reserved `ask` keyword + `ask_typed::<T>` — blocked on `_specialize_fn` body-walk fix; v5.41.0+ candidate |
| v5.42.0 | As.1+As.2+As.3 | SHIPPED | `Supervisor`, `ChildSpec`, `RestartPolicy` constants, `RestartStrategy` constants, `RestartDecision` |
| v5.42.0 | As.4+As.6 | SHIPPED | C runtime substrate: 4 new exports, `mapanare_exit_reason_kind_t`, append-only struct extension on `mapanare_agent_t` (488→984 bytes) |
| v5.42.0 | As.7+As.8+As.9 | SHIPPED | examples + `docs/stdlib/agent.md` + binary-compat regression test |
| v5.42.0 | (PROMPT/PLAN deviations) | DEVIATION | five surfaced at Phase 0 audit (naming, no system-msg enum, no agent_exit API, restart-policy field semantics, golden count) — all lead-approved |
| v5.42.0 | (Path B) | DEVIATION | push-driven via opt-in C callback (lead-approved over Path A pure-Mapanare poll) |
| v5.42.0 | (library shape) | DEVIATION | strategy library, not supervisor agent — sidesteps fn-typed-parameter + cross-typed-agent v5.x quirks |
| v5.43.0 | Da.0 | SHIPPED | `__mn_str_chr` 0..255 range fix (latent bug since byte-strings landed) |
| v5.43.0 | Da.1+Da.2+Da.3+Da.4+Da.5+Da.6+Da.7+Da.8+Da.9 | SHIPPED | `RemoteAgent` + `NodeHandle` + 5-symbol HMAC-SHA256 wire protocol v1 + 6 msg_types + 10 new C exports + 4 GREEN link-and-run tests + 250 LOC pytest harness |
| v5.43.0 | (server-side TLS) | DEVIATION | Phase 0 surfaced no SSL_accept; lead-approved Option B (~95 LOC C added 5 dlopen symbols + 3 exports) |
| v5.43.0 | (three v5.x lowerer bugs surfaced) | DEFERRED | Result<COMPLEX_OK, NetworkError> destructure + variant rewrap + nested 15-arm match silently failing — workaround via flat-tuple shape; closed at v5.46.0 |
| v5.43.0 | (RemoteExitReason::TransportLost rename) | DEVIATION | renamed to RemoteUnreachable to avoid name collision with NetworkError::TransportLost |
| v5.43.0 | (async heartbeat + auto-route ChildExited + generic RemoteAgent<T>) | DEFERRED | requires fn-typed callbacks / dedicated agent threads / Ai.1; v5.43.x candidates |

**Manifesto arc closure:** complete. The "first-class agents"
manifesto pitch graduates from library-class with extra steps
to actual cross-machine agent semantics. The flat-tuple
workaround for v5.43.0 lowerer bugs was structurally honest
(documented in source preambles + deferred to a dedicated
closeout release at v5.46.0).

### Tensor closeout arc (2 releases)

| Release | ID | State | Notes |
|---|---|---|---|
| v5.41.0 | Ts.1 (option B part 1) | SHIPPED | `tensor.reshape(shape)` end-to-end on LLVM (Python bootstrap + self-host); ~58 LOC C + ~85 LOC golden + 225 LOC pytest |
| v5.41.0 | (option B scope split) | DEVIATION | Phase 0 sized full closeout at ~1900 LOC / 3-5 days vs PROMPT's ~750/1-2 sessions; lead-approved Ts.1-only ship |
| v5.41.0 | (copy semantics) | INTENTIONAL | ships copy semantics; Ts.2 adds aliasing under same surface (semantic swap) |
| v5.45.0 | Ts.2.A | SHIPPED | refcount on `mapanare_tensor_t` (40→64 bytes append-only) |
| v5.45.0 | Ts.2.B | SHIPPED | `t.view(shape)` + reshape semantic swap (writes visible in source) |
| v5.45.0 | Ts.3.A+Ts.3.B | SHIPPED | grammar + AST + parser + runtime for `[start..end:step]` + multi-axis routing |
| v5.45.0 | Ts.4+Ts.5+Ts.7+Ts.8 | SHIPPED | 3 new goldens (97/98/99) + cookbook + self-host mirror + binary-compat regression |
| v5.45.0 | (5 Phase-0 deviations) | DEVIATION | grammar HEAD state; existing GpuTensor.reshape namespace; struct-grow audit; +24 vs +16 bytes; IndexItem inclusive flag |
| v5.45.0 | (concat_self.py lesson) | LESSON | first STRICT NEAR — ran scripts/build_stage1.py before scripts/concat_self.py; reordered, STRICT restored |
| v5.45.0 | (`Tensor<Int>` parser bug) | DEFERRED | pre-existing v5.44.1 — v5.46.0+ LOW carry |
| v5.45.0 | (`.copy()` ergonomic) | DEFERRED | v5.47.0+ candidate |

**Tensor closeout arc closure:** complete. The CLAUDE.md
"Not yet on LLVM" line for tensor mutable views + stepped
slices is **removed entirely** at v5.45.0. Static borrow-
checking for view aliasing remains a v6.0 deliverable
(documented explicitly in the cookbook).

### Package-system runway (2 releases)

| Release | ID | State | Notes |
|---|---|---|---|
| v5.44.0 | Ps.1+Ps.2 | SHIPPED | `mapanare/pkg_discovery.py` (280 LOC) + resolver extension; reserved `source` literals (mn_modules, path, git, global-cache) |
| v5.44.0 | Ps.3 | SHIPPED | CLI parity refactor across cli.py / multi_module.py / test_runner.py / lsp/analysis.py |
| v5.44.0 | Ps.4 | SHIPPED | install diagnostics (`--verbose`, `--diag-json`) |
| v5.44.0 | Ps.5+Ps.6 | SHIPPED | pure exemplar `examples/packages/consumer_collections/` + LEGACY.md markers |
| v5.44.0 | Ps.7+Ps.8+Ps.9 | SHIPPED | 3 docs guides (~660 LOC) |
| v5.44.0 | Ps.10 | SHIPPED | tests/packages/ (65 cases across 7 files) |
| v5.44.0 | (PROMPT premise gap) | DEVIATION | PLAN treated as green-field; Phase 0 found stdlib/pkg.py = 1037 LOC complete; lead-approved wire-existing-parts |
| v5.44.1 | Ps.11.A+Ps.11.B | SHIPPED | scripts/benchmarks resolver parity + new gate `test_scripts_pass_resolver_to_compile_helper` |
| v5.44.1 | Ps.12.A+Ps.12.B | SHIPPED | init template `.gitignore` + lock test |
| v5.44.1 | Ps.13 | SHIPPED | `from typing import Any` import hoist |
| v5.44.1 | (PROMPT/PLAN surface shape deviation) | DEVIATION | Phase 0 found bare `ModuleResolver()` regex doesn't fire for the four tooling files; new gate locks `resolver=` kwarg invariant |

**Package-system runway closure:** complete. After v5.44.0+v5.44.1
a project with `mapanare.toml` + `mapanare.lock` + `mn_modules/`
imports installed packages without manual `--stdlib-path` hacks.
Forward-compat for global-cache + git + path sources reserved.

### v5.43.0 lowerer-bug closeout + pre-panel hygiene (2 releases)

| Release | ID | State | Notes |
|---|---|---|---|
| v5.46.0 | Lf.0 | SHIPPED | Phase 0 audit reconstructed all 4 v5.43.0 repros; localized fix sites; verified self-host already correct |
| v5.46.0 | Lf.1+Lf.2+Lf.3 | SHIPPED | single ~30 LOC fix at `mapanare/lower.py:2398-2453` Ok/Err constructor branches — closes 3 distinct symptoms (Result destructure tag corruption + variant rewrap + nested 15-arm silent no-fire) |
| v5.46.0 | Lf.4 | DEFERRED | variant-name disambiguation (≥50 LOC) — split to v5.47.0; closed there as Cl.1 |
| v5.46.0 | Lf.5 | NO-OP | self-host mirror — Phase 0 verified already correct (zero `.mn` source touches; STRICT preserved trivially) |
| v5.46.0 | Lf.6 | SHIPPED | broader sweep audit (237 non-trivial-Ok callers) |
| v5.46.0 | Lf.7 | SHIPPED | 3 new goldens (100-102) + 5-case `tests/llvm/test_lowerer_fixes.py` + glob-pattern fix |
| v5.46.0 | (5 PROMPT/PLAN deviations) | DEVIATION | Lf.5 no-op gate; one-fix-three-regressions; Lf.4 split; pre-existing test bookkeeping; pre-existing failures inventory |
| v5.47.0 | Cl.1 | SHIPPED | Lf.4 variant-name collision closure across both Python bootstrap (`semantic.py` + `lower.py`) AND self-host stage1 (`semantic.mn` + `lower.mn`) — ~80 LOC across 4 files |
| v5.47.0 | Cl.4 | SHIPPED | `stdlib/net/websocket.mn` `str(byte)` decimal-stringification cleanup (11 sites → `__mn_str_chr`) |
| v5.47.0 | Cl.2 | DEFERRED | agent stdlib ergonomic refactor (~400 LOC + ~50 callers) — v5.47.1 split |
| v5.47.0 | Cl.3 | DEFERRED | `stdlib/fs.mn::walk_dir` IR codegen — v5.47.1 split (receiver-side wrong-shape Result aggregate; v5.40.0 carry) |
| v5.47.0 | (Phase-0 split rationale) | DEVIATION | both Cl.2 and Cl.3 verified structurally non-trivial at Phase 0; warranted dedicated focus rather than rushed bundling |

**v5.43.0 lowerer-bug closeout + pre-panel hygiene:** complete.
Single ~30 LOC fix in v5.46.0 closed three symptoms via one
root cause (Phase 0 surfaced this); v5.47.0 picked up the
v5.46.0-deferred Lf.4 plus one independent latent stdlib bug.
The Cl.2 + Cl.3 splits to v5.47.1 are honest structural
deferrals, not "we ran out of time" deferrals.

---

## 3. Silent-RED gate sweep at v5.47.0 HEAD

The v5.28.0 RE-PANEL caught Anaconda's 3 silent-RED CI gates;
this audit must do the same. Live state at HEAD on the day of
the panel cut:

| Gate | At HEAD | Notes |
|---|---|---|
| `make ci-gates` | GREEN (running, 9 sub-gates) | Output captured below |
| `make lint` | GREEN | black + ruff + mypy clean |
| `verify_fixed_point.sh` | STRICT (244,654 lines / 0 diff) | 50-release strict streak from v5.7.1 baseline; preserved by construction at v5.47.0 (no compiler edits there beyond Cl.1 self-host mirror which was concat'd + rebuilt cleanly) |
| Goldens via `test_native.py` | 103/103 | 102 from v5.46.0 + new `103_variant_name_collision.mn` from v5.47.0 |
| `check_doc_freshness.py` | GREEN | clean |
| `check_changelog_honesty.py` | GREEN | `## [5.47.0] - 2026-05-06` clean |
| `check_cadence.py` | REMINDER (informational) | "19 minor versions since last panel (v5.28.0). Per .reviews/REVIEW_CADENCE.md, a full 7-reviewer panel was suggested at v5.33.0. Informational only — lead drives review timing." This is the deliberate cadence-gap shape per v5.28.0 directive; not a dock target. |
| pytest (non-bootstrap) | 0 fail | Per v5.47.0 SESSION_REPORT |
| pytest (bootstrap) | unchanged | Per v5.47.0 SESSION_REPORT (test_run_hello gcc.exe env issue, test_reshape_size_mismatch_aborts, test_link_and_run[98_*/99_*] are pre-v5.46.0 baseline failures, not v5.31.0+ regressions — documented in v5.46.0 PRE_PHASE_AUDIT) |
| `tests/llvm/test_lowerer_fixes.py` | 8/8 GREEN | Lf.1+Lf.2+Lf.3 from v5.46.0 + 3 new Lf.4 cases from v5.47.0; falsifiability locked per layer |

**Pre-existing (v5.45.0+) baseline failures — NOT v5.31.0+
regressions:**

- `test_run_hello` (gcc.exe env issue on Windows worker — not
  reproducible on Linux)
- `test_reshape_size_mismatch_aborts` (intentional abort path
  surfacing in pytest harness)
- `test_link_and_run[98_*/99_*]` (Tensor<Int> parser bug from
  v5.44.1 — documented carry; float-element variant works)

These are documented in v5.46.0 + v5.47.0 SESSION_REPORTs;
reviewers should not surface them as new findings.

**No silent-RED gates surfaced at HEAD.** The lead's audit
pass before panel cut found nothing the panel will dock for
that v5.47.0 didn't already document or close.

---

## 4. Arc-completion claims verified at HEAD

| Claim | Evidence at HEAD |
|---|---|
| Foundation arc CLOSED | `dist/mapanare/mnc{,.exe}` paths exist in publish.yml staging steps for win-x64 + linux-x64 + darwin-arm64; `mapanare/__main__.py::_native_binary_name()` testable helper present; CHANGELOG entries v5.31.0-v5.33.2 explicit |
| Stdlib gap-close arc CLOSED | `stdlib/{time,sql/sqlite,encoding/json,net/http/router,net/http/streaming,text/regex,crypto}.mn` exist; `runtime/native/{mapanare_time.c,mapanare_db.c,mapanare_io.c}` extensions present; 6 docs guides under `docs/stdlib/` |
| Manifesto arc CLOSED | `stdlib/ai/{ask,ask_cache}.mn`, `stdlib/agent/{supervisor,url,remote,node,supervision,remote_proto}.mn` exist; `runtime/native/mapanare_node.c` (~360 LOC) + `mapanare_io.c` server-side TLS extensions present |
| Tensor closeout arc CLOSED | CLAUDE.md "Not yet on LLVM" line for tensor view + stepped slices removed; `mapanare_tensor_t` extended to 64 bytes (`runtime/native/mapanare_runtime.h` cross-checked); goldens 97/98/99 present |
| Package-system runway CLOSED | `mapanare/pkg_discovery.py` exists; reserved-source-literals tests at `tests/packages/test_resolver_does_not_scan_global_cache.py`; `examples/packages/consumer_collections/` complete |
| v5.43.0 lowerer-bug closeout CLOSED at v5.46.0 | `tests/llvm/test_lowerer_fixes.py` 8/8 GREEN; `mapanare/lower.py:2398-2453` Ok/Err branches consult `current_fn.return_type` |
| Pre-panel hygiene cleanup CLOSED at v5.47.0 | Cl.1 fix sites at `mapanare/semantic.py::_check_let`, `mapanare/lower.py`, `mapanare/self/semantic.mn::SemState`, `mapanare/self/lower.mn::LowerState`; Cl.4 sites at `stdlib/net/websocket.mn` |
| Mb.\* arc CLOSED (since v5.29.0) | unchanged from v5.28.0 panel — Mb.10 + Pv.7 + Pv.8 closed at v5.29.0 |
| Pv.\* arc CLOSED (since v5.32.0/v5.33.0) | unchanged — Pv.7 (clean-build-test race) + Pv.8 (agent-state timing) shipped |
| Js.4 arc CLOSED (v5.36.0 → v5.39.7) | every `TypeKind` branch in `_encode_field_to_json` / `_decode_json_field` closed; round-trip locked per shape in `tests/stdlib/test_struct_json_runtime.py` (18 cases) |
| STRICT 3-stage fixed-point preserved | 50-release strict streak from v5.7.1 baseline (244,654 lines / 0 diff at v5.47.0) |

All arc-CLOSED claims from CLAUDE.md release-notes verified at
HEAD. **No false-CLOSED claims surfaced.**

---

## 5. Carry-forward draft (input to Cp.4)

Pre-categorized into Cp.4's three buckets. Reviewers may
re-categorize during panel; this is the draft state.

### (a) v6.0 PLAN inputs

| Item | Source | Severity | Notes |
|---|---|---|---|
| Borrow checker / multi-level alias analysis | v5.6.6 + v5.27.0 carry; `Rt.04` at v5.7.1/v5.11.0/v5.22.0 panels | HIGH | The v6.0 thesis. Closes the depth-2 struct→list→string drop-glue path that was the original Lk.1 driver. |
| Hard removal of `{}` syntax | v5.19.0 Te.3 soft deprecation; v6.0 promised | HIGH | `{}` warns since v5.19.0; SPEC §22 deprecation cycle terminates at v6.0 |
| Static view-aliasing safety (Ts.2 stopgap) | v5.45.0 cookbook explicit | MEDIUM | v5.45.0 ships runtime substrate (refcount); static borrow-check for view aliasing is v6.0 |
| `_specialize_fn` body-walk fix for nested generic intrinsics | v5.40.0 Ai.1 deferral | MEDIUM | Gates `ask` keyword sugar + `ask_typed::<T>` + generic stdlib functions calling generic intrinsics |
| Strided / non-contiguous tensors (transpose, permute, reverse step) | v5.45.0 deferred | MEDIUM | Forces `mapanare_tensor_t` ABI change |
| GPU tensor surface unification (`stdlib/gpu/tensor.mn::GpuTensor` vs builtin `Tensor`) | v5.41.0 / v5.45.0 carry | MEDIUM | Two parallel tensor surfaces; cohesion debt |
| Stage2-binary teardown crash (RC=3) | v4.30.0 PLAN, 70+ releases stale | LOW | Papered over by `set +e` in `verify_fixed_point.sh:124-137`; v6.0 cleanup window |
| Single-line `if x: y` (v5.21.1 explicit rescope) | v5.21.1 H.4 | LOW | Coincides with `{}` hard removal |

### (b) v5.47.x patch candidates

| Item | Source | Severity | Notes |
|---|---|---|---|
| macOS notarization (proper Developer ID, replace ad-hoc-sign) | v5.33.0 Nu.2 | MEDIUM | Needs paid Apple Developer cert; not a code change |
| Cl.2 — agent stdlib ergonomic refactor (flat-tuple → `Result<T, NetworkError>`) | v5.47.0 deferred | MEDIUM | ~400 LOC across `stdlib/agent/{url,remote,node,supervision}.mn` + ~50 internal callers + test updates |
| Cl.3 — `stdlib/fs.mn::walk_dir` IR codegen | v5.47.0 deferred (v5.40.0 carry) | LOW | Receiver-side wrong-shape Result aggregate bug; different fix-site from v5.46.0 constructor-side |
| Linux aarch64 + macOS x86_64 native `mnc` tarballs | v5.33.0 Nu.3 | LOW | No native runner / cross-compile pipeline yet |
| Pike VM regex rewrite (alternative to PCRE2 dlopen) | v5.38.0 Re.6 carry | LOW | PCRE2 surface works; Pike VM removes dlopen dependency at cost of feature parity |
| Closure-chain middleware (HTTP) | v5.37.0 Ht.2 carry | LOW | Registration-table works; closure-chain ergonomic; blocked on fn-typed param invocation fix |
| Bounded-RSS HTTP streamer (Ht.4.B) | v5.37.0 Ht.4 carry | LOW | Encoders ship; pump driver needs `__mn_tcp_send_bytes(fd, ptr, len)` |
| Re.6 — `pon m: Option<Match>` allocation bug | v5.38.0 carry | LOW | Same class as v5.36.0 Js.0.B (Result wrap-shape mismatch on Option) |
| Async per-connection heartbeat task (distributed agents) | v5.43.0 deferred | LOW | Requires fn-typed callbacks or dedicated agent runtime threads |
| Auto-route inbound MSG_CHILD_EXITED frames | v5.43.0 deferred | LOW | Cross-references supervision arc |
| Generic `RemoteAgent<T>` with auto-`to_json` | v5.43.0 deferred | LOW | Blocked on Ai.1 prerequisite |
| AEAD (AES-GCM, ChaCha20-Poly1305) + Ed25519/X25519 + Argon2id | v5.39.1 explicit deferral | LOW | Each has its own correctness trap (GCM nonce reuse, etc.); structurally independent of Cr.\* baseline |
| `to_terse` empty `#{}` rewriter bug | v5.27.0 Tk.1 closed | RETIRED — closed v5.27.0 |
| HMAC over SHA-3 / BLAKE2 | v5.39.0 carry | LOW | Requires `EVP_MAC` migration |
| Streaming JSON true chunked I/O | v5.36.0 Js.3 LITE | LOW | Needs native `Bytes` type |
| Native `Bytes` type | v5.36.0 + v5.39.0 carry | LOW | Cross-cutting; v6.0 candidate if it becomes load-bearing |
| Sub-second precision in date/time broken-down forms | v5.34.0 carry | LOW | Cosmetic |
| Full strftime expansion | v5.34.0 carry | LOW | Cosmetic |
| Named timezone database (tz_named beyond UTC + system-local) | v5.34.0 explicit defer | LOW | Cosmetic; non-negotiable defer was correct |
| Hash-dispatched enum decode (vs linear cascade) | v5.39.7 carry | LOW | Cosmetic; <20 variants is fine linear |
| Internally / adjacently tagged JSON enum shapes | v5.39.7 carry | LOW | Externally-tagged is the documented invariant |
| Custom serde rename attributes | v5.39.7 carry | LOW | Cosmetic ergonomic |
| Parser ergonomic `=> return EXPR` after match arm | v5.39.7 carry | LOW | Block-form `=> { ok = ... }` works |
| LSP / IDE polish | not surfaced explicitly | LOW | Not a release-blocker |

### (c) retired (closed in a later release)

| Item | Original source | Reason |
|---|---|---|
| Tn.1 95-golden link gate | v5.28.0 panel rec | Closed v5.35.0 Sq.0 |
| Js.4.B runtime SEGV | v5.36.0 deferred | Closed v5.39.2 Js.4.B.2 |
| Js.4.C nested-struct encode | v5.39.2 deferred | Closed v5.39.3 |
| Js.4.D LIST encode/decode | v5.39.3 deferred | Closed v5.39.4 + v5.39.5 |
| Js.4.E MAP encode/decode | v5.39.5 deferred | Closed v5.39.6 |
| Js.4.F ENUM encode/decode | v5.39.6 deferred | Closed v5.39.7 |
| Lf.1+Lf.2+Lf.3 (v5.43.0 lowerer bugs) | v5.43.0 deferred | Closed v5.46.0 |
| Lf.4 (variant-name collision) | v5.46.0 deferred | Closed v5.47.0 Cl.1 |
| `__mn_indent_to_braces` Win64 ABI | v5.28.0 panel surface | Closed v5.29.0 Mb.10 |
| `clean-build-test` race | v5.28.0 panel surface | Closed v5.29.0 Pv.7 |
| Agent-state timing in test_c_runtime.c | v5.28.0 panel surface | Closed v5.29.0 Pv.8 |
| SPEC header drift | v5.30.0 → v5.33.0 | Closed v5.33.1 Hd.\* |
| `check_cadence.py` enforced gate | v5.24.0 Hy.3 | Demoted to informational at v5.33.2 Cd.\* per project memory |
| Banner "[dev mode]" lie on release installs | publish-run-#50 | Closed v5.31.0 Bn.\* |
| Windows SDK ZIP `mnc.exe` was PyInstaller copy | v5.12.0 oversight surfaced at v5.31.0 | Closed v5.32.0 Nw.\* |
| Js.6 sqlite Value::Json variant | v5.36.0 deferred (blocked on Js.4.B) | Routed to v5.36.x candidate; Js.4.B closed v5.39.2 — re-open if user demand surfaces, otherwise retire silently |

---

## 6. Reviewer reading list

Each reviewer should read this audit + the SESSION_REPORTs +
CLAUDE.md ledger in scope. Per-axis focus:

| Reviewer | Primary focus | Heavy on |
|---|---|---|
| **Rattler** (mechanical correctness) | All ci-gates, fixed-point trajectory (50-release strict streak), goldens (102 → 103), sanitizer state | v5.42.0 + v5.43.0 (binary compat regression tests; TSan/ASan + valgrind + 1000-iteration network fuzz), v5.45.0 (concat_self.py lesson), v5.46.0 (zero `.mn` source touches preserving STRICT trivially) |
| **Viper** (perf + benchmarks) | Per-release perf footprint; runtime additions; copy-vs-view tensor semantics; JSON serde overhead; network protocol DoS guards | v5.41.0 (tensor copy semantics + perf implications), v5.43.0 (network perf, JSON serde at 1MB, 100MB DoS guard), v5.45.0 (Ts.2 view-vs-copy trade-off), v5.39.0 (HMAC + streaming digest perf) |
| **Anaconda** (process + test discipline + silent-RED) | Every "PROMPT/PLAN deviation" Phase-0 surface; test infrastructure additions; convergent-recommendation pattern; HEAD-state premise drift | v5.42.0 (5 deviations at Phase 0), v5.45.0 (5 deviations at Phase 0), v5.41.0 (4 mismatches), v5.44.0 (PROMPT premise gap), v5.40.0 (Ai.1+Ai.2 deferral), v5.39.0 (Cr.0 emitter shortcut surfaced under Cr.\*) |
| **Cobra** (architecture + cohesion) | v5.42.0/v5.43.0 architecture (supervision substrate + distributed transport); cohesion across the stdlib arc; namespace coexistence (GpuTensor vs Tensor); package-system shape | v5.42.0 (library-vs-agent shape decision), v5.43.0 (wire-format invariants + 6 msg_types lock), v5.44.0 (resolver extension shape), v5.37.0 (registration-table vs closure-chain trade-off) |
| **Coral** (UX + docs + ergonomics) | All `docs/stdlib/*.md` additions (6 new); CLAUDE.md release-notes density; localized README state (v5.28.0 H.4 cross-reference) | All 6 new stdlib cookbooks (time, sql, json, regex, crypto, agent, http, ai); v5.40.0 manifesto.md update; v5.45.0 cookbook (~325 LOC) |
| **Boa** (long-tail bug closure + carry-forward discipline) | Carry-forward closure rates per release; v5.34.0+ "Tn.1" trajectory (escalation pattern); Mb.\* / Pv.\* / Js.4 arc claimed closures; v5.47.0 hygiene-ahead-of-panel pattern | v5.46.0 (one-fix-three-regressions discipline), v5.47.0 (Cl.\* hygiene closures + Cl.2/Cl.3 honest splits), all "Aggregate state entering" lines |
| **Mamba** (security + correctness under adversarial inputs) | v5.39.0 Cr.\* (HMAC + crypto surface); v5.43.0 Da.\* (network security model, replay defense, HMAC truncation rationale, MAPANARE_NODE_KEY env, DoS guard); package signing carry | v5.39.0 (RFC corpus tests; constant_time_eq), v5.43.0 (HMAC-SHA256 truncation to 16 bytes RFC 4868; per-connection last_seen replay watermark; 100MB DoS guard; 1000-iteration fuzz; server-side TLS extension), v5.44.0 (no opportunistic global-cache scan invariant) |

---

## Process observation

This audit binds to no specific prior-panel finding ID because
the v5.28.0 panel docket was structurally fully closed before
this arc began (per `CARRY_FORWARD.md`, `Aggregate state
entering v5.29.x`). Every v5.28.0-surfaced LOW that escalated
or was mid-arc-relevant has been either (a) closed in scope
(see section 5(c) above), (b) explicitly carried forward with
documented target release (section 5(a)/(b)), or (c) retired.

The convergent-recommendation pattern from v5.28.0 (Cb.New1 +
Ra.Inf1 — independent reviewers reaching same finding shape)
**did fire mid-arc** — Tn.1's escalation across v5.29.0 →
v5.32.0 → v5.33.0 directives surfaced the structural test
gap that v5.35.0 Sq.0 closed. The pattern works; recommend
making it explicit in v5.47.5 V5_DECISION.md "Followups" as
a v6.0 process input.

---

## End of audit

**Status:** PRE_PANEL_AUDIT.md complete. Reviewers may begin
Cp.2 panel run.

**Next:** `.reviews/v5.47.5/<reviewer>/findings.md` per axis.
