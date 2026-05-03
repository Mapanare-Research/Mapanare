# v5.24.1 — Wd.\* — wider docs cleanup (arc closeout)

**Status:** SHIPPED (ready, not tagged).
**Scope:** Wd.1–Wd.8 from `PLAN.md`. **Final** release in the
v5.23–v5.24 recovery arc — see
`docs/roadmap/v5/RECOVERY_ARC_v5.23-v5.24.md`.
**Breaking:** No. Zero compiler / runtime / `mapanare/self/*.mn`
edits.
**Strict 3-stage fixed point:** preserved at **239,835 lines / 0
diff** by construction (19-release strict streak; same line count
as v5.24.0 because no `.mn` source changed).
**Goldens:** 95/95 preserved.
**Bb.\* seed refresh:** **NOT** required (no new C-runtime exports;
no bootstrap surface change).

---

## Headline

The v5.23–v5.24 recovery arc closeout. Five releases shipped (RC.\*
+ Mb.\* + Te.3.B + Hy.\* + Wd.\*); the v5.27.0 panel arrives at
routine cadence with **0 HIGH / 0 MEDIUM / ~5 LOW** open in the
docket.

This release closes the long-running narrative-drift class:
manifesto coherence drift across 3 consecutive panels, SPEC corpus
showing 72% brace-style against §4.0's colon-canonical declaration,
five Coral L1–L5 polish items, and the Bo.27 audit cross-reference
column convention that prevents the v5.22.0 Bo.18r failure mode at
the v5.27.0 audit.

Three of the eight items are **3+ consecutive panel carries**:

1. **Wd.1 — Manifesto coherence (M2)**: Coral has flagged
   `docs/manifesto.md:31` "Curly braces for blocks" at v5.7.1 /
   v5.11.0 / v5.22.0 — three panels.
2. **Wd.2 — SPEC corpus (M3)**: 26 of 36 block-openers in
   `docs/SPEC.md` were brace-style against §4.0's colon-canonical
   declaration. v5.21.1 hygiene closed the prose but not the
   examples.
3. **Wd.8 — Bo.27 audit cross-reference column** convention: the
   structural prevention for the H.\* / Bo.\* mismatch class that
   produced Bo.18r persistence across 3 panels (v5.7.1 / v5.11.0 /
   v5.22.0).

Plus 5 LOW polish items from Coral L1–L5 / TR1 cluster.

---

## What changed

### Wd.1 — Manifesto M2 closure (`docs/manifesto.md:31`)

Two-line edit per Coral M2's verbatim suggested fix:

```diff
-The syntax is clean and direct. Curly braces for blocks, strong
-static typing with inference where it helps, no semicolons where
-they add nothing. If you have written Rust, Go, or TypeScript,
-you can read Mapanare immediately.
+The syntax is clean and direct. Indented blocks (with a brace-
+form legacy through v6.0), strong static typing with inference
+where it helps, no semicolons where they add nothing. If you
+have written Rust, Go, or TypeScript, you can read Mapanare
+immediately.
```

The manifesto's first-impression syntax description now matches
the codebase's soft-deprecation posture (Te.3, v5.19.0). Three
consecutive panels of Coral flagging this; closes structurally.

### Wd.2 — SPEC corpus M3 closure

`docs/SPEC.md` migrated from 26 brace-style block-openers to 0
mechanical brace-style block-openers; the 2 remaining brace
openers live inside the §4.0 "Brace style" demonstration block
(intentionally preserved with a `<!-- preserve-brace -->` marker
because that example *is* the demonstration of brace shape).

**Tooling delta**: new `to_terse_markdown(source)` in
`mapanare/format.py` walks markdown source line-by-line, locates
`` ```mn `` fences, and runs `to_terse` on each fence body. Honors
a `<!-- preserve-brace -->` HTML comment on the line immediately
above the opening fence (blank lines tolerated) as an opt-out
marker. Other code-block languages (`` ```bash ``, `` ```toml ``,
etc.) and prose pass through verbatim.

`mapanare/cli.py::cmd_fmt` learned a `.md` / `.markdown` dispatch
path: detected by suffix, requires explicit `--to-terse`, skips
the `parse()` validation that the `.mn` path uses, routes through
`to_terse_markdown`. Same exit-code conventions as the `.mn` path
(`--check` exits 1 on drift; `--stdout` prints; default writes in
place).

The migration **also surfaced a latent bug** in `to_terse`'s
`endswith("{}")` clause: it was rewriting `let m: Map<K, V> = #{}`
(empty map literal) as `let m: Map<K, V> = #:` plus an indented
`pass`. The bug had been latent since v5.17.0 Sh.A.1 because no
Sh.\* corpus file uses the empty-`#{}` shape, and CI didn't
exercise the markdown rewrite path until v5.24.1. The §17.1 SPEC
example was reverted manually to `#{}`; the latent rewriter bug
itself is held for v5.25.0+ as a `_looks_like_stmt_block_opener`
gate on the empty-body clause (no scope-creep into v5.24.1).

New regression tests: `tests/test_format.py::TestMarkdownRewriter`
(8 cases) — fence body rewrite, preserve-brace marker (with and
without intervening blank line), other-language fences passthrough,
prose-only passthrough, idempotence on already-colon-style,
empty-input edge case, multiple-fences-with-mixed-markers.

### Wd.3 — Coral L1 — SPEC §27.3 Te.3 worked-example crosslink

Added a "Worked example (v5.19.0 → v6.0)" paragraph after the
existing breaking-change-process numbered list. Points at Te.3
(`{}`-block soft-deprecation, v5.19.0) as the canonical worked
example of the deprecation cycle in v5: warning → soak → migration
tool → major-version hard removal. Cross-links to §4.0 for the
user-facing migration commands.

### Wd.4 — Coral L2 — broken-promise wording polish (SPEC §4.0)

Tightened the wording at SPEC line 1048 area. Pre-Wd.4 wording was
clinical ("rescoped at v5.21.1 to coincide with the v6.0 `{}` hard
removal"). Post-Wd.4 wording is closer to language-design rationale,
naming the concrete v5.14.0 forward promise that didn't ship at
v5.21.0, and linking the rescope to the parser ambiguity that hard
removal eliminates.

### Wd.5 — Coral L3 — `mnc fmt --keep-braces` example invocation (SPEC §4.0)

Added two example invocations to the §4.0 Te.3 status block — one
for the auto-migrate path (`mnc fmt src/main.mn`), one for the
soak-window concession (`mnc fmt --keep-braces src/main.mn`). The
flag was documented at v5.21.1 H.6 but the example invocation was
absent.

### Wd.6 — Coral L4 — generic-bound trait sketch (SPEC §7.4)

Added a 10-line worked example to §7.4 (Trait Bounds on Generics).
Defines a `Comparable` trait, implements it for `Score` (a user
struct), and writes a generic `min<T: Comparable>(a: T, b: T) -> T`
that operates on any type bound by the trait. Cross-links to §13.4
(monomorphization) for the runtime story.

The first attempt at the example used `impl Comparable for Int`
mirroring the PLAN's draft — it fails ("Undefined type 'Int' in
impl block"; primitives aren't impl targets in v5.x). The shipped
shape uses a user-defined `Score` struct instead, matching the
existing SPEC §7.2 convention.

The example is also shipped as a runnable file at
`examples/struct_ergo/generic_trait.mn` — verified to compile
through `python3 -m mapanare emit-llvm`.

### Wd.7 — Coral L5 — examples directory micro-organization

Conservative shape: only the Te.\* file at top level (`chained_cmp.mn`)
moved into a new `examples/terseness/` category. Async demos
(`async_file_io.mn`, `async_http_demo.mn`) stay at the top level
because `docs/cookbook/async.md` and `docs/guides/async.md` cite
them by path; moving creates churn for marginal organizational
benefit. Existing categorization (`ai/`, `gpu/`, `tensor/`,
`signals/`, `wasm/`, `network/`, `cli/`, `bind/`, `transpile/`,
`packages/`, `experimental/`, `python_to_native/`) is preserved.

`examples/struct_ergo/generic_trait.mn` (new in Wd.6) seeds the
struct-ergonomics category; future Te.5 examples land there.

New `examples/INDEX.md` documents categories with descriptions —
discoverability gain for newcomers without forcing churn on
existing references.

Live references updated: `mapanare/format.py` docstring
(line 31). Historical references (CHANGELOG, v5.21.1
SESSION_REPORT, v5.22.0 PLAN) stay at the old path — those are
historical text describing what was true at release time.

### Wd.8 — Bo.27 audit cross-reference column

New `.reviews/PANEL_AUDIT_TEMPLATE.md` codifying the cross-walk
convention. Every `H.*` hygiene-release finding must bind to a
prior-panel finding ID (`Bo.18r`, `V.9`, `Co.M2`, etc.) or
explicitly mark "(none — fresh)". Every prior-panel HIGH and
MEDIUM must either appear in the `H.*` table with its prior-panel
ID cited, or appear in a "deferred to <future release>" section —
no third option. Closes the v5.22.0 Bo.18r failure mode where
hygiene-release closures patched the audit's cited line and walked
past the panel-flagged paragraph (the v5.7.1 / v5.11.0 / v5.22.0
3-panel persistence).

`.reviews/REVIEW_CADENCE.md` "How to run a full panel" section
extended with a Step 1 pre-panel audit pointer at the new template.
Convention applies starting v5.27.0 (next routine cadence panel).

---

## Validation results

### CI gates

```
$ make ci-gates
...
=== All gates GREEN ===
```

All 8 sub-gates GREEN: `silent_skips`, `changelog_honesty`,
`workflow_shapes`, `docs_drift`, `hollow_features`,
`struct_registry`, `doc_freshness`, `cadence`.

### test_format.py

```
$ python3 -m pytest tests/test_format.py
896 passed, 144 skipped in 26.28s
```

Includes 8 new `TestMarkdownRewriter` cases for the
`to_terse_markdown` rewriter.

### Strict 3-stage fixed point

```
$ bash scripts/verify_fixed_point.sh --keep
[Stage 1] stage2.ll: 239835 lines, llvm-as: OK
[Stage 2] stage3.ll: 239835 lines, llvm-as: OK
[Verify] ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (239835 lines, 0 diff)
```

Same line count as v5.24.0 — no `.mn` source touched, fixed point
preserved by construction.

### Native goldens

`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
→ **95/95 PASS** (unchanged from v5.24.0).

### lint

`make lint` — clean.

---

## Carry-forward delta

| Item | v5.24.0 status | v5.24.1 status |
|---|---|---|
| Wd.1 (Coral M2 manifesto, 3rd consecutive panel) | OPEN | **CLOSED** |
| Wd.2 (Coral M3 SPEC corpus) | OPEN | **CLOSED** |
| Wd.3 (Coral L1 §27.3 crosslink) | OPEN | **CLOSED** |
| Wd.4 (Coral L2 broken-promise polish) | OPEN | **CLOSED** |
| Wd.5 (Coral L3 `--keep-braces` example) | OPEN | **CLOSED** |
| Wd.6 (Coral L4 generic-bound trait sketch) | OPEN | **CLOSED** |
| Wd.7 (Coral L5 examples directory) | OPEN | **CLOSED** |
| Wd.8 (Bo.27 audit cross-reference) | OPEN | **CLOSED** |

### Arc closure summary (v5.22.0 panel → v5.24.1 closeout)

| Class | At v5.22.0 panel | At v5.24.1 closeout |
|---|---:|---:|
| HIGH | 4 | **0** |
| MEDIUM | 8 | **0** |
| LOW | ~12 | ~5 (polish only) |
| v6.0 carry | 1 (Rt.04) | 1 (Rt.04) — unchanged |

Five releases shipped across the arc (RC.\* + Mb.\* + Te.3.B +
Hy.\* + Wd.\*). v5.27.0 panel inherits **0 HIGH / 0 MEDIUM open**.

---

## What this release CANNOT do

- **Re-grade the v5.22.0 panel.** Routine cadence next at v5.27.0.
- **Touch v6.0 carry items.** Rt.04 (multi-level alias analysis),
  Te.3 hard removal, stage2-teardown crash (v4.30.0), single-line
  `if x: y` (v6.0 rescope) — all held.
- **Close the latent `to_terse` empty-`{}` rewriter bug.** Surfaced
  during Wd.2 markdown migration but held for v5.25.0+ as a scope-
  creep guard. Workaround at v5.24.1 is the manual revert at SPEC
  §17.1.
- **Rename existing example directories** (e.g. `tensor/` →
  `tensors/`). Wd.7 was sized for minimal churn; rename is
  optional polish for v5.25.0+.

---

## Rationale capture

The interesting design decision in Wd.2 was **whether to make the
formatter markdown-aware permanently or write a one-shot script**.
A one-shot would have shipped the migration without touching
`mapanare/format.py` or `cli.py`; the permanent route adds a small
surface that future hygiene runs (and any user maintaining
markdown docs with `` ```mn `` fences) benefit from.

Permanent route chosen because:

1. The `<!-- preserve-brace -->` marker is a real user-visible
   feature once it ships — codifying it in the formatter (with
   regression tests) makes it discoverable.
2. The PROMPT explicitly authorized the format.py change for the
   opt-out.
3. The CI exercise of `to_terse_markdown` via `tests/test_format.py`
   regression tests means future to_terse changes that break
   markdown idempotence get caught at PR time.

The chosen surface is conservative: `.md` / `.markdown` suffix
detection, mandatory `--to-terse` flag, no auto-migration default
on markdown (unlike `.mn` where `mnc fmt` auto-migrates). The
markdown path requires the user to opt in explicitly because
markdown rewriting is a heavier action than whitespace normalization
on `.mn`.

---

## File-level changes

```
docs/manifesto.md                              4 lines   (Wd.1)
docs/SPEC.md                                   ~140 lines  (Wd.2/Wd.3/Wd.4/
                                                            Wd.5/Wd.6)
mapanare/format.py                             +to_terse_markdown (~95 LOC)
mapanare/cli.py                                +.md dispatch in cmd_fmt
                                                  (~25 LOC)
tests/test_format.py                           +TestMarkdownRewriter
                                                  (8 cases)
examples/INDEX.md                              NEW
examples/struct_ergo/generic_trait.mn          NEW           (Wd.6)
examples/terseness/chained_cmp.mn              moved from examples/  (Wd.7)
.reviews/PANEL_AUDIT_TEMPLATE.md               NEW           (Wd.8)
.reviews/REVIEW_CADENCE.md                     +1 step in "How to run a full
                                                  panel"     (Wd.8)
docs/roadmap/v5/v5.24.1/SESSION_REPORT.md      NEW
CHANGELOG.md                                   ## [5.24.1]
CLAUDE.md                                      release note
VERSION                                        5.24.0 → 5.24.1
README.md                                      badges (via bump_version.py)
docs/README.{es,pt,zh-CN}.md                   badges (via bump_version.py)
```

Zero compiler / runtime / `mapanare/self/*.mn` source files
touched. Strict 3-stage fixed point preserved by construction.

---

## v5.27.0 panel preview

Per the v5.22.0 V5_DECISION.md, the next routine cadence panel
runs at v5.27.0 (5-minor cadence from v5.22.0). The arc-end state
should produce:

- Aggregate target: **9.5+** (recovery from v5.22.0's 9.41 floor)
- v5.7.1's 9.66 ceiling is reachable IF every HIGH closes
  structurally + Hy.\* prevention is operational + Wd.\* narrative
  drift is closed
- Expected reviewer deltas: Anaconda recovers from 8.4 (the
  v5.22.0 dock); Coral / Boa stay flat-or-positive given M2 / M3 /
  Bo.18r-class closures; Mamba / Cobra / Rattler / Viper unchanged
  trajectory

The arc is sized for **9.55–9.65** as the realistic best case;
**9.65–9.70** is the stretch goal that requires the structural
prevention to actually work in practice (i.e., the v5.27.0 panel
finds zero new structural gaps that the prevention should have
caught).
