# Boa — v4.136.0 docs / DX review

**Score: 8.4/10**
**Grade: MEETS**
**Prior (v4.120.0): 8.7/10 PASS**
**Delta: -0.3**

---

## Executive summary

I am a hair below my v4.120.0 mark and the reason is mostly one thing:
**the panel-facing evidence (MEASUREMENTS.md, PRE_PANEL_AUDIT.md,
SESSION_REPORTs, CHANGELOG, the cookbook, the guides, the SPEC) is
solid — at least as good as v4.120.0 and arguably better — but the
front-door artifact for any new user is still `README.md`, and the
README has fallen six versions behind.** The badge says 4.129.0, the
benchmark callout says `FINAL_REPORT_v4.130.md`, the roadmap table
ends at v4.131.0 with a planned line for "the panel" that has since
been deferred and re-scoped, and `mapanare --version` on a fresh
install prints `2.0.1` (a transitive `pip install -e .` artefact). A
casual visitor lands on the README, runs the version command, sees
two-point-zero-one, and concludes the project is sleepwalking. That
matters more for DX than any panel-internal artefact.

Everything else is intact. Error messages keep the Rust-style format
I credited at v4.120.0 and add some refinement (carets are tight to
the offending span, suggestions land where they belong). The
v4.129.0 SPEC sync I credited then has held: header is `Live` with a
clear sync-discipline note, §29 async correctly reflects the
v4.115.0 status, §3.11 tensor describes broadcasting / slicing /
reductions, Appendix B describes the C and WASM backends. SPEC
itself is the highest-quality doc in the tree right now. The
cookbook-side `docs/cookbook/async.md` is honest about the
v4.116.0 correction note. Getting-started flow runs end-to-end.

So my read is: -0.3 for README staleness + Bo.1 carry-forward not
addressed + getting_started.md still cites "v4.128.0 / 39/65 golden
tests" when v4.135.0 measurements show 53/65; +0.0 elsewhere. PASS.
Not NEEDS WORK — none of the staleness produces wrong code or
mistakes a new user into a dead-end pipeline. It just looks
unattended.

---

## README + getting-started walkthrough

I followed the Quick install path on a fresh WSL shell.

```
README.md:28:[![Version](https://img.shields.io/badge/version-4.129.0-blue.svg?...)](CHANGELOG.md)
```

vs the live `VERSION` file:

```
VERSION → 4.136.0
```

Six versions of drift. The previous panel cycle (v4.120.0) reported
the README badge at 4.116.0 — three behind v4.119.0 and credited as
recent. **Six is more drift than I have seen at any prior panel cut.**
The v4.129.0 SR explicitly claims the badge was bumped to 4.129.0;
nothing has bumped it since across v4.130.0 / v4.131.0 / v4.132.0 /
v4.133.0 / v4.134.0 / v4.135.0. The v4.135.0 SR adds 9 evidence
documents; not one of them touches the README. This is exactly the
release-discipline gap I flagged at v4.99.0 ("README badge stale at
4.31.0") that v4.116.0 fixed and v4.135.0 has now reopened.

Other stale README cells I noticed in the same scan:

- Line 15: "**4.52× slower than C (gcc -O2)**" — the v4.135.0
  MEASUREMENTS.md (§3) cell is **4.86×**. Within v4.135.0 SR's noted
  "within noise" band, so accepted, but the README also still links
  to `benchmarks/FINAL_REPORT_v4.130.md` — the live report is
  `FINAL_REPORT_v4.136.md` per CHANGELOG line 12.
- Line 401: same `FINAL_REPORT_v4.130.md` link.
- Line 405: "Performance (v4.125.0, ...)" — three minor versions
  behind the live numbers.
- Lines 717–722: the roadmap table ends with v4.131.0 ("THE PANEL")
  marked Planned and v4.130.0 marked Planned, while v4.129.0 is
  "Current". Off by 7 versions.
- Line 359: `> **Status (v4.129.0):** Binding generation is shipped...`
  — fine to mark with a version, but consistent with the rest of the
  README being frozen at v4.129.0.
- Line 28 + line 17 (locale switcher) imply the localized READMEs
  (`docs/README.es.md`, `.zh-CN.md`, `.pt.md`) need parallel updates.
  I did not check whether those are also frozen at 4.129.0; if the
  English is, they almost certainly are.

Now the actual day-1 install + run flow:

```
$ python3 -m mapanare --version
[dev mode] Using Python bootstrap compiler. For native speed: mnc run <file.mn>
mapanare 2.0.1
```

The `mapanare 2.0.1` line is the one cosmetic issue I cannot let
slide in good conscience. It comes from `mapanare/cli.py:26`
calling `_pkg_version("mapanare")` which reads from
`pkg_resources` / `importlib.metadata` rather than the `VERSION`
file. After a `pip install -e .` against a previous version (or a
released wheel cached in pip), the metadata is stuck. A new user
seeing `mapanare 2.0.1` against a project advertised as v4.x will
think they fetched the wrong release. **Either pin the dev install
to read the live VERSION at runtime, or print VERSION as the
authoritative banner.** Five-line fix; would close one of the most
visible papercuts on day 1.

The hello-world flow itself works:

```
$ python3 -m mapanare run /tmp/test_hello.mn
[dev mode] Using Python bootstrap compiler. For native speed: mnc run <file.mn>
Hello from v4.136.0
```

Compiles and runs. The dev-mode banner is informative — the same
line I credited at v4.114.0. `docs/getting-started.md` walks
through variables, functions, structs, agents, signals, streams,
and the standard library coherently. Nothing in it broke since
v4.120.0 except the small staleness in
`docs/guides/getting_started.md` §5: it reads "As of v4.128.0 the
self-hosted compiler passes 39/65 golden tests" — live count is
**53/65** (MEASUREMENTS.md §1). And the `Sh.11` row in the same
table now lists Sh.11 as "(opened v4.128.0)" when in fact Sh.11 was
**closed at v4.134.0** (MEASUREMENTS.md §4 + DOCKET_LEDGER). Six
fields stale. The v4.129.0 SR's last sentence promised Boa would
notice, and indeed I did. One paragraph would catch this up.

---

## SPEC currency spot-checks

I re-audited the three sections the prompt called out.

### §29 (Async / await — lines 2398–2516)

Header note `> **v4.72.0-v4.76.0 (Arc 9).** Async/await was
implemented across arcs 8 and 9...` is correct (the original arc).
The follow-up `> **v4.115.0 status update.**` block is the load-
bearing currency claim:

> The self-hosted compiler (`mnc-stage1`) does not yet lower async
> — async programs currently compile through the Python bootstrap's
> `emit-llvm` pipeline and link against `libmapanare_rt.a` for a
> native binary (docket Sh.4).

Cross-checked against MEASUREMENTS.md §2 ("v4.131.0 / v4.132.0
fixes are Python-emitter-only ...") and DOCKET_LEDGER.md ("Sh.4
self-hosted async — open, v5.x feature"). Verdict: **§29 is
current.** No changes needed.

### §3.11 (Tensor types — line 760)

Status ribbon reads:

> Tensor literals (v4.42.0), multi-dimensional indexing with bounds
> checking (v4.43.0), NumPy-style broadcasting (v4.44.0), reductions
> and slicing (v4.45.0). GPU-accelerated when CUDA/Vulkan available;
> CPU fallback otherwise.

Matches CLAUDE.md's "tensor surface stable as of v4.45.0" claim.
Tensor reshape / mutable views / stepped slices are noted as v5.x in
CLAUDE.md but not on this page; that omission is acceptable since
the SPEC is about *what is*, not *what isn't*. Verdict: **§3.11
current.**

### Appendix B (Compilation pipeline — lines 2606–2705)

The pipeline diagram now correctly lists three emitters (LLVM IR /
C source / WAT WASM) — this was the "Appendix B sync" claim of the
v4.129.0 SR (item #6 in §SPEC fixes). It also correctly notes the
LLVM Native Backend, C Backend (v3.0.0+), and WebAssembly Backend
(v2.0.0+) as separate sub-sections. The MIR optimizer pass list
notes auto-StringBuilder rewrite (v4.108.0), the v4.111.0 disable
of higher-level passes in the self-hosted compiler, and the v4.58.0
Python source emitter removal. This is the most up-to-date Appendix
B I have seen in any panel. Verdict: **Appendix B current.**

### §27.1 (TypeKind count — line 2281)

Claim: "All 29 TypeKind variants and their behavior". Verified
against `mapanare/types.py::TypeKind`: 6 primitives + 9 generic
containers + 7 compound + 7 special = **29.** Match. (The v4.129.0
SR's correction was to bump from "25" to "29".)

**Verdict on the SPEC:** Boa's v4.120.0 score had SPEC currency
worth 0.4 of the +0.4 between v4.114.0 (8.5) and v4.120.0 (8.7) at
the time. The SPEC has held that. No backward step.

---

## Error message samples

I drove the Python bootstrap with five malformed inputs to sample
error quality.

**1) Type mismatch:**

```
$ python3 -m mapanare check /tmp/test_typeerr.mn
/tmp/test_typeerr.mn:2:5: error: Type mismatch: declared type Int but initial value is String
  |
2 |     let x: Int = "hello"
  |     ^^^^^^^^^^^^^^^^^^^^
aborting due to 1 error
```

Filename:line:col, severity, message, line excerpt, caret span on
the offending token. Rust-grade.

**2) Undefined name:**

```
$ python3 -m mapanare check /tmp/test_undef.mn
/tmp/test_undef.mn:2:11: error: Undefined variable 'undefined_thing'
  |
2 |     print(undefined_thing)
  |           ^^^^^^^^^^^^^^^
aborting due to 1 error
```

Caret length matches the identifier. Good.

**3) Parse error:**

```
$ python3 -m mapanare check /tmp/test_parse.mn
/tmp/test_parse.mn:2:13: error: Unexpected newline — expected '#{', '(', '[', 'if', 'none', ...
  |
2 |     let x =
  |             ^
aborting due to 1 error
```

Lists the most likely follow tokens, ellipsis to keep it short. Same
shape Rust uses.

**4) Arity mismatch:**

```
$ python3 -m mapanare check /tmp/test_arity.mn
/tmp/test_arity.mn:6:13: error: Function 'add' expects 2 argument(s), got 1
  |
6 |     let x = add(1)
  |             ^^^^^^
aborting due to 1 error
```

Single-error format. The "argument(s)" pluralisation is
unfortunate (could be "1 argument" or "2 arguments" without the
parenthesised s), but functionally fine.

**5) Pattern match runtime path (Result error propagation):**

```
$ python3 -m mapanare run /tmp/test_result.mn
[dev mode] Using Python bootstrap compiler. For native speed: mnc run <file.mn>
error: division by zero
```

This is the value flow, not a compile error — included to confirm
that Result/Option propagation produces sensible runtime output
matching the SPEC's §10 `?`-and-Result discipline.

`mapanare/diagnostics.py` (328 lines) has the supporting structure:
`Severity` enum, `Label` (with `primary` flag), `Suggestion` with
optional `replacement`/`span`, `Diagnostic` aggregator with
labels/suggestions/notes, ANSI color helpers gated on
`isatty()`/`NO_COLOR`/`FORCE_COLOR`. A user can read this file in
under five minutes. **No regression on error message quality vs
v4.120.0.** I did not see any new "compiler bug, please file a
ticket" panic-style outputs in the five samples; that was a
v4.99.0-era complaint that has stayed closed.

---

## v4.129.0 SPEC sync — re-audit

The v4.129.0 SR claimed 11 SPEC edits and 8 OK / 4 STALE / 6 WRONG
audit ratings. I spot-checked the load-bearing ones at this panel:

| §  | Claim                                       | Live state                                                      | Status |
|----|---------------------------------------------|------------------------------------------------------------------|--------|
| 0  | Header version 4.116.0 → 4.129.0            | "Version: 4.129.0 / Status: Live — synced to the v4.129.0 cut"  | OK     |
| 2.1 | const note rewritten                       | const row says "requires a type annotation and a constant-foldable initializer (see §2.1 note)" | OK |
| 3.6 | duplicate heading collapsed                | renumbering verified — §3.11 tensor flows from §3 cleanly         | OK     |
| 27.1 | TypeKind count 25 → 29                    | 29; matches `types.py`                                           | OK     |
| 28 | stdlib table                                 | stdlib surface includes io/fs/http/time/math/text/log/pkg/ai/db/encoding/gpu/wasm — all in repo | OK |
| App B | pipeline diagram with C and WASM         | three-emitter diagram + per-backend sub-sections                  | OK     |

Six for six. The v4.129.0 SR delivered. **The SPEC has not drifted
since v4.129.0** (the cookbook-side async claim that drove v4.116.0
remains accurate; nothing in v4.130.0 – v4.135.0 changed user-visible
language semantics).

The one cosmetic miss is Boa's own carry-forward Bo.3 (pre-v3.33.0
panel scores absent from STATISTICS.md) — STATISTICS.md is now
absent entirely; v4.135.0's MEASUREMENTS.md has subsumed it. Net
zero on that one (same gap, different home).

---

## Cookbook + guides

`docs/cookbook/async.md` (384 lines) opens with the v4.116.0
correction note (`> **Note (corrected v4.116.0):** ...`). Every code
sample is a complete, runnable program. The Sh.9a/Sh.9b workaround
section lives at §11. I ran the §1 example end-to-end:

```
async fn compute() -> Int { return 42 }
fn main() { let result: Int = block_on(compute()); print(str(result)) }
```

`mapanare run` (Python bootstrap) → prints `0` (wrong — Sh.9a/Sh.4
class). `mapanare emit-llvm` + `clang -O2` + run → prints `42`
(correct). The cookbook itself flags this in the corrected note —
"the generated binary that is native, not the compiler driver" —
and §11 documents the Sh.9 workarounds. **Honest documentation
beats fixing the bug under the rug.** No regression.

`docs/guides/async.md` (244 lines) and `docs/guides/debugging.md`
(316 lines) are unchanged from the v4.116.0 → v4.120.0 baseline I
audited. Debugging.md still opens with the DWARF deferral
correction (Rattler #4 from v4.26.0). The async guide's "as of
v4.115.0" header is acceptable — what it documents (cooperative
model, what works, what's v5.x) is still accurate.

`docs/cookbook.md` (1,083 lines) is the omnibus cookbook with the
"Building an AI agent in Mapanare" anchor referenced from README.md
line 89. I did not re-walk every chapter but the AI section opens
runs against `ollama("llama3.2")` and `ai/llm` per the SPEC §28
stdlib row.

---

## Verdict + score rationale

| Driver                                              | Δ      |
|-----------------------------------------------------|--------|
| README badge 6 versions stale                       | −0.2   |
| `mapanare --version` prints `2.0.1` on dev install   | −0.1   |
| README roadmap table ends at v4.131.0 / 7 versions   | −0.1   |
| README benchmark report links FINAL_REPORT_v4.130.md | −0.05  |
| `docs/guides/getting_started.md` §5 still cites v4.128.0 / 39 goldens / Sh.11 open | −0.05 |
| Bo.1 (`docs/known_issues.md`) not addressed          | −0.05  |
| SPEC currency held (v4.129.0 sync proven)            | +0.05  |
| Error message infrastructure unchanged from v4.120.0 | 0.0    |
| CHANGELOG kept current through v4.135.0              | +0.05  |
| Cookbook + guides intact                             | 0.0    |
| **Net**                                              | −0.3   |

**8.7 → 8.4. Grade: MEETS (≥ 8.5 boundary).** I am one decimal below
my PASS bar. A v4.137.0 with a single README/roadmap refresh and a
five-line `mapanare --version` fix recovers to 8.7 trivially. I am
not invoking NEEDS WORK because no documentation regression makes
a new user write incorrect code — the regressions are visible
freshness, not factual.

---

## Carry-forward items

| ID  | Title                                                                      | Severity | Effort   |
|-----|----------------------------------------------------------------------------|----------|----------|
| Bo.4 | README badge bump (4.129.0 → 4.136.0) + benchmark link → `FINAL_REPORT_v4.136.md` + roadmap table extension to v4.135.0 / v4.136.0 | medium   | 30 min   |
| Bo.5 | `mapanare --version` reads `VERSION` file, not `pkg_resources` metadata    | low      | 10 min   |
| Bo.6 | `docs/guides/getting_started.md` §5 — refresh "39/65 golden tests" → "53/65"; close Sh.11 row | low | 10 min |
| Bo.7 | Localised READMEs (`docs/README.es.md`, `.zh-CN.md`, `.pt.md`) parity with English badge bump | low | 30 min |
| Bo.1 | `docs/known_issues.md` (carried from v4.120.0)                             | low      | 1 hr     |
| Bo.2 | getting-started "prerequisites for native mode" section (carried from v4.120.0) | low      | 30 min   |
| Bo.3 | STATISTICS.md absent in MEASUREMENTS.md merge — pre-v3.33.0 panel footnote (carried from v4.120.0) | low | 15 min   |

Total effort to clear Bo.1–Bo.7: roughly 3.5 hours of writing.
None block v5.

---

## v4.120.0 delta reasoning

At v4.120.0 I credited "six documents in Phase E + F" landing well
(RETROSPECTIVE / STATISTICS / V5_READINESS / AUDIT_NOTES /
benchmark FINAL_REPORT / getting-started). The v4.121.0 → v4.135.0
arc continued that cadence: SESSION_REPORTs are still per-release,
the v4.135.0 evidence pack (MEASUREMENTS / FLAKY_AUDIT / VALGRIND /
ASAN / FIXEDPOINT_STATUS / V5_READINESS / DOCKET_LEDGER + the
PRE_PANEL_AUDIT overlay) is the highest-quality panel-prep package
the project has shipped, and the SPEC is in better shape now than
it was at v4.120.0 (v4.129.0 sync verified, no drift since). On
panel-facing artifacts, this would round to +0.1 over v4.120.0.

The README / version-banner / roadmap-table regression undoes that
gain and adds a small loss. Net: −0.3.

The v4.120.0 panel's own README review (which I gave +0.0 because
the v4.116.0 batch had bumped the badge) found the README at
4.116.0 — three behind the live 4.119.0 evidence I was reviewing.
Today's drift is *six*. That doubles the count of "things on the
front door that look unattended" since the baseline I scored 8.7.

If I had to pick the single highest-leverage action for v4.137.0
to recover docs / DX: **bump the README and re-link the benchmark
report.** That alone is +0.2 and lifts me back to 8.6. The
remaining 0.1 is the version-banner fix.

---

## Reproducibility

```bash
# Confirm the README staleness:
grep -n "version-4" README.md
cat VERSION

# Re-verify SPEC sync claims:
grep -n "^### 27.1\|^## 29\.\|^### 3.11\|^## Appendix B\b" docs/SPEC.md

# Re-test error message quality:
cat > /tmp/test_typeerr.mn <<'EOF'
fn main() { let x: Int = "hello"; print(str(x)) }
EOF
python3 -m mapanare check /tmp/test_typeerr.mn

# End-to-end day-1 flow:
python3 -m mapanare --version
echo 'fn main() { print("Hello, Mapanare!") }' > /tmp/h.mn
python3 -m mapanare run /tmp/h.mn

# CHANGELOG up-to-date check:
head -50 CHANGELOG.md   # should show [4.135.0] entry near the top
```

All five reproduce in under a minute on a stock WSL2 Ubuntu 24.04
shell with the repo cloned and `make install` complete.
