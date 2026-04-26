# Panel v5.8.0 — Coral (Language Design)

**Score:** 9.6 / 10
**Grade:** EXCEEDS
**Delta vs v5.2.0:** +0.2

## Summary

The v5.3.1-through-v5.7.1 arc is the cleanest language-design release
window I have reviewed. Two parity gaps that have lived in the
known-issues table for the entire v5 era — async (Sh.4) and tensor
(Sh.6) — closed with full SPEC backing in §29 and §3.11. The third
parity gap (Sh.7, closure-typed parameters) closed in v5.7.0 with a
SPEC callout in §6.3. Or-patterns over built-in variants (B) closed
the same release with a §5.6 note. The package registry I praised at
v5.2.0 for its security posture but flagged for missing SPEC coverage
now has a normative §30 spanning manifest schema, version constraints,
install semantics, lockfile format, registry API, and security model.
The signals demo I carried forward as PARTIAL since v4.143.0 ships at
`examples/signals/counter.mn` with documented expected output. The
SPEC version header that I have flagged for **three consecutive
panels** — 4.143.0 against a v5.x README — is now 5.7.1, closing a
**27-release staleness window** that I gave the project explicit
notice would cost 0.05 if it persisted.

The arc shipped genuine language semantics: tensor literals + multi-dim
indexing + broadcasting + slicing + reductions, real LLVM coroutines
with `presplitcoroutine` + the `@llvm.coro.id/begin/save/suspend/end`
pipeline, scheduler-driven `AwaitSuspend` and `BlockOn`, drop-glue
ownership tracking for string / list / boxed / tensor across return
paths and loop iterations, destination-passing semantics for
let-binding allocation. None of this required a grammar change —
`git log v5.0.0..HEAD -- mapanare/mapanare.lark` returns empty across
the entire v5 arc spanning 36 releases. The language surface a
programmer writes against is byte-identical to v5.0.0 and now
fully self-hostable: native goldens **66/66** for the first time
in project history.

The carry-forward closure rate this cycle is **5/5 + 3 deferrals
appropriately scoped**. Demo gap CLOSED. SPEC-pkg CLOSED. SPEC
header CLOSED. The two LOW deferrals (Gr.1 multi-line literals,
Sh.5 `const` in fn bodies) are correctly classified as parser /
self-hosting quirks with documented workarounds, not language
design ambiguity. I am awarding **+0.2** over my v5.2.0 score —
the largest single-cycle delta in my history — because (1) the
SPEC re-sync alone is worth +0.10 after three cycles of warning,
(2) §30 is genuinely good normative spec (not just guide copy),
(3) closing 12 goldens that span three different language
features without breaking grammar discipline is a process win,
and (4) the §3.11 / §29 / §6.3 / §5.6 cross-section sync work
demonstrates the spec-discipline doc loop functioning the way
the project's guidance says it should.

## What improved since v5.2.0

### SPEC §30 Package Management (v5.3.3) — closes my v5.2.0 carry-forward

This is the single largest closure of my v5.2.0 review. I carried
SPEC-pkg as a LOW item with the note "Before open publishing (v5.3+),
the SPEC should have a section defining the `mapanare.toml` schema,
install semantics, lockfile format, and version constraint resolution
rules." Verification at HEAD confirms §30 covers all four:

- **§30.1 `mapanare.toml` Manifest** — Field-by-field table for
  `[package]` (name, version, description, license, repository,
  authors, entry, mapanare_version) with required/optional flags
  and types. `[dependencies]` and `[dev-dependencies]` shape
  documented including the inline-table form for git deps.
  Forward-compatibility clause: "Unknown keys MUST be ignored, not
  rejected." This is correct — it lets the manifest format add
  fields in patch releases without breaking older toolchains.

- **§30.2 Version Constraints** — Six constraint forms (`^X.Y.Z`,
  `~X.Y.Z`, `>=X.Y.Z`, ranges, exact, `*`) with their resolution
  semantics. Greedy latest-satisfying resolution is **explicitly
  documented as such** ("There is no SAT solver"). Transitive
  resolution honestly flagged as "**not guaranteed**" in v5.3.x.
  This is the correct posture: SAT solving is a v6+ feature, and
  documenting the gap in the SPEC means consumers can plan around
  it rather than hit it as undocumented behavior.

- **§30.3 `mapanare install` Semantics** — Seven-step sequence
  (manifest load → lock consultation → resolution → download →
  integrity check → extract → lock update). The integrity-check
  step explicitly aborts "with no files written" on SHA-256
  mismatch — atomic failure is the correct semantic for
  install. The "Install-time scripts are not supported" clause
  is in the SPEC, not just the guide. This converts what was a
  CLI implementation choice into a normative language guarantee:
  a future Mapanare distribution that adds `postinstall` hooks
  would be **non-conforming**. That is the right place to put
  this rule. Side-effects clause confines writes to
  `mn_modules/`, `mapanare.lock`, and `~/.mapanare/cache/`.

- **§30.4 `mapanare.lock` Lockfile** — Full JSON shape with
  field-by-field table. Lockfile-version gating clause: "A
  lockfile whose `lockfile_version` is higher than the installer
  supports MUST cause the install to abort with a diagnostic
  rather than silently downgrade." This is correct — it
  prevents the silent-corruption class where a v5.3 toolchain
  reads a v5.5 lockfile, ignores fields it doesn't understand,
  and produces a different resolution.

- **§30.5 Registry API** — Six endpoints with auth requirements
  documented. Authentication lines up with what shipped (GitHub
  OAuth + token storage at `~/.mapanare/token`).
  Idempotency clause: "Publishing the same `(name, version)`
  twice MUST be rejected by the registry." This is the correct
  immutability rule for a registry — without it, a malicious
  publisher could overwrite a known-good version.

- **§30.6 Security Model** — Five bullets. The "Token storage"
  bullet specifies `0600` permissions and forbids writing tokens
  to `mapanare.toml` / `mapanare.lock`. This addresses my v5.2.0
  concern about credential leakage in lockfiles.

- **§30.7 Out of Scope** — Six items honestly enumerated:
  full transitive resolution, version yanking, private
  registries, vendoring, signatures beyond SHA-256, and
  offline-mirror support. "Implementations MAY experiment with
  these but MUST NOT rely on them in documented behavior." This
  is the correct conformance posture — it lets the registry
  evolve without breaking spec compliance.

§30 is normative spec, not migrated guide content. The text uses
RFC-2119 language correctly (MUST, MUST NOT, SHOULD, MAY). The
section length (197 lines) is appropriate for the feature surface.
This earns full credit for the carry-forward closure.

### SPEC header 4.143.0 → 5.7.1 (27-release staleness window CLOSED)

I have flagged this at v4.144.0, v4.154.0, and v5.2.0 — three
consecutive cycles. v5.2.0 review explicitly stated: "**I will
dock 0.05 next cycle if it persists.**" Verification:

```
$ head -5 docs/SPEC.md
# Mapanare Language Specification

**Version:** 5.7.1
**Status:** Live — synced to the v5.7.1 cut (2026-04-26)
```

Closed. The header now matches the live release. The 27-release
window — which spanned my v4.144.0 / v4.154.0 / v5.2.0 reviews and
covered all of v5.0.x / v5.1.x / v5.2.x / v5.3.x / v5.4.x / v5.5.x /
v5.6.x / v5.7.x — is gone.

The follow-on work justifies the staleness: v5.7.1 isn't a
cosmetic header bump. The SPEC sync covers eight sections (§2.1,
§3, §3.11, §5.6, §6.3, §27.1, §28, §29, Appendix B) per the
"Spec sync discipline" block at lines 20-29. I verified each:

- **§3.11 (Tensor)** — sync complete (next subsection)
- **§5.6 (Or-Patterns)** — sync complete (B closure note at 1105)
- **§6.3 (Closures)** — sync complete (Sh.7 callout at 1220-1239)
- **§29 (Async)** — sync complete (Sh.4 status at 2490-2501)
- **§30 (Packages)** — added at v5.3.3 (covered above)
- **Appendix B (3-stage fixed point)** — sync complete (next
  subsection)

The "Spec sync discipline" instruction-block to the panel —
"Each release fact-checks this spec against the live grammar
(`mapanare/mapanare.lark`), type system (`mapanare/types.py`),
and self-hosted lexer (`mapanare/self/lexer.mn`)" — is exactly
the discipline I asked for at v4.144.0. Codifying it inline in
the SPEC means future cycles inherit the requirement.

The +0.05 I telegraphed at v5.2.0 does not apply. The closure is
clean enough to earn credit instead. **+0.10** for closure plus
the discipline addition.

### §3.11 Tensor surface spec'd + closed (v5.6.0–v5.6.4)

The §3.11 status block at lines 774-785:

> Status: Stable on LLVM backend, in both the Python bootstrap
> and the self-hosted emitter (parity closed v5.6.0–v5.6.3, Sh.6).
> Tensor literals (v4.42.0; self-hosted v5.6.0), multi-dimensional
> indexing with bounds checking (v4.43.0; self-hosted v5.6.1),
> NumPy-style broadcasting (v4.44.0; self-hosted v5.6.2),
> reductions and slicing (v4.45.0; self-hosted v5.6.3).
> Drop-glue ownership tracking for tensor allocations
> (`emit_track_tensor`) closed v5.6.4 (Rt.06).

This is exactly the right level of detail. Each feature is dual-
attributed (Python emit version + self-hosted port version), so a
reader can see the parity arc. The drop-glue closure is
attributed by Rt-id, which lets a reviewer cross-reference
PARITY_GAPS.md (where Rt.06 closure is at line 243).

The body at lines 787-869 covers:
1. Tensor literal syntax with shape inference (`Tensor<Float>[...]`)
2. Jagged-array rejection ("rejected at parse time with a
   diagnostic message")
3. Multi-dim indexing with rank check + runtime bounds check
4. NumPy broadcasting rules ("Dimensions are compared right-to-left;
   a dimension pair is compatible if both are equal or one is 1.
   Shorter shapes are left-padded with 1s")
5. Compile-time shape mismatch errors with the offending dimension
   surfaced
6. Matrix multiplication via `@` operator
7. Six reduction methods (sum / mean / max / min / argmax / argmin)
8. Slicing with range and wildcard syntax (returns a copy)

I confirm: PARITY_GAPS.md line 247 marks Sh.6 CLOSED v5.6.0–v5.6.3
with grep verification (`grep -l "lower_tensor_slice|tensor_reduction"
mapanare/self/lower.mn` → match). MEASUREMENTS.md §2 confirms goldens
49/50/51/52/53 byte-identical (sample `1 3 1 3 2 6 1 6 2 3 3 8 1 8
3 20 -1 -2.5` for golden 49). Five tensor goldens that have failed
under `mnc-stage1` since v4.42.0 (when tensor literals first
entered the Python emitter) now pass through `mnc-stage1 → llc →
clang`.

This is a load-bearing closure for the language's marketing
posture. "Tensors are first-class primitives" is the headline
under which the language is shipped (line 18 of SPEC, README
H1). Until v5.6.x that claim was Python-emitter-only — a user
running the native compiler on a tensor program got a parse
failure or a function-count mismatch. v5.6.x makes the
self-hosted compiler honor the headline.

### §29 Async surface spec'd + closed (v5.5.4–v5.5.7)

The §29 v5.5.4–v5.5.7 update block at lines 2490-2501:

> v5.5.4–v5.5.7 update (Sh.4 closure). The self-hosted emitter
> now ships full LLVM-coroutine lowering for async fns:
> `presplitcoroutine` attribute + the `@llvm.coro.id/begin/save/
> suspend/end` pipeline (v5.5.4), scheduler-driven `AwaitSuspend`
> (v5.5.5), scheduler-driven `BlockOn` + main lifecycle (v5.5.6),
> and sanitizer-clean drop-glue / fixed-point hardening (v5.5.7).
> All 5 Sh.4 goldens (55_async_basic through 59_async_fanout)
> compile through `mnc-stage1` and execute correctly through
> the real LLVM coroutine ABI; valgrind / ASan / LSan / TSan
> all clean on the corpus.

This block does important spec work: it documents the
**implementation strategy** (LLVM switched-resume coroutines
via the `@llvm.coro.*` intrinsic family) without elevating it
to normative behavior. The async surface in §29.1-29.7 stays
implementation-neutral — `await`, `Future<T>`, `block_on`,
coroutine lifecycle, memory model, interaction with other
primitives — while the status block tells implementers and
reviewers what shipped.

§29.3 is particularly clean: `Future<T>` is documented with a
two-state machine (Pending / Ready) and an LLVM representation
(`{i8, ptr}`) that's listed as "the implementation" rather than
required by the spec. The clause "All `Future<T>` have the same
LLVM type (`{i8, ptr}`) regardless of `T`, enabling a uniform
scheduler queue" is informative enough that another implementer
could match the ABI but isn't a hard requirement.

§29 is honest about the cooperative-vs-preemptive choice:

> The async model is **cooperative, not preemptive**: async fns
> yield only at `await` points; synchronous runtime calls
> (`__mn_file_write`, `http_get`) block the current worker for
> their duration.

This is the kind of safety-critical detail a future user needs
to know before they put an async Mapanare program in production.
Documenting "synchronous runtime calls block the worker" closes
a footgun that would otherwise surface as performance regressions
in unrelated tasks sharing the worker pool.

PARITY_GAPS.md line 246 confirms Sh.4 CLOSED v5.5.4–v5.5.7 with
the full breakdown by sub-release. MEASUREMENTS.md §2 shows all
5 async goldens passing (55_async_basic through 59_async_fanout).
MEASUREMENTS.md §5.1-5.4 confirms valgrind / ASan / LSan / TSan
clean across the corpus.

### §6.3 Closure-typed parameters spec'd (v5.7.0)

§6.3.4 "Closure-Typed Parameters" at lines 1206-1239 introduces
function-type-annotated parameters:

```mn
fn apply(f: fn(Int) -> Int, x: Int) -> Int {
    return f(x)
}
let double = (x) => x * 2
let result = apply(double, 5)   // 10
```

The v5.7.0 (Sh.7 closure) callout enumerates all four self-hosted
changes:

1. `parser.mn`'s `FAT_ARROW` handler extracts multi-parameter
   lambdas from `(a, b) => ...` (was: only single `Ident` LHS)
2. `lower.mn::lower_call_by_name` routes calls through fn-typed
   locals via indirect-call SSA name (`Load` + `Call(dest,
   "%loaded_val", args)`)
3. `emit_llvm_ir.mn::emit_call_ir` / `emit_call_void` recognise
   `%`-prefixed callees and emit `call <ret> %fn(...)` without
   the `@` prefix
4. `mir_opt.mn`'s `clone_instr_for_inline` and
   `replace_uses_in_instr` rename `Call.fn_name` when it's an SSA
   value

This is the right level of detail for a closure callout: it tells
a reviewer what changed in the self-hosted compiler without
overspecifying the implementation. A future re-implementation
could choose a different lowering strategy as long as the
function-type annotation works as documented.

PARITY_GAPS.md line 248 marks Sh.7 CLOSED v5.7.0 with grep-style
verification. MEASUREMENTS.md §2 shows golden 64_closure_typed
PASS at 22 basic blocks / 260 stack bytes.

The note at line 1189 ("Lambda parameter types are inferred from
context. Type annotations on lambda parameters are not supported
in the grammar — use a named function if explicit types are
needed.") is honest about the remaining grammar gap. This is
correct: don't claim a feature works that doesn't.

### §5.6 Or-pattern + identifier `None` resolution (v5.7.0)

The §5.6 "v5.7.0 (B closure)" block at lines 1105-1114:

> The Python bootstrap's `_is_enum_variant_name` originally
> treated built-in `None` / `Some` / `Ok` / `Err` as fresh
> binding names rather than enum variants when checking
> or-pattern binding-set equality. The fix short-circuits these
> names to enum-variant resolution and resolves
> `Identifier("None")` to `Option` in both `_infer_expr` and
> `_lower_identifier`. This closes the last bootstrap gap for
> or-patterns over built-in variants and was the second of two
> v5.7.0 fixes that delivered the first 66/66 golden run in
> project history.

The §5.6 body at line 1101 is honest about the implementation's
current limit:

> All alternatives in an or-pattern must bind the same set of
> variable names. (The current implementation checks name-set
> equality only; type compatibility across alternatives is not
> yet enforced.)

This is the correct level of detail. A reader knows what works
(`A | B` with identical bindings) and what to avoid (`Some(x:
Int) | Some(x: String)` — type-incompatible bindings would
silently typecheck as `Any` rather than fail).

PARITY_GAPS.md line 249 marks B CLOSED v5.7.0 with re-blessed
golden 51_match_guards_and_or (298 lines, 2 fns).

### Demo gap CLOSED — `examples/signals/counter.mn` (v5.3.3)

I carried the demo gap as PARTIAL since v4.143.0 — over **eight
panel cycles**. I noted at v5.2.0: "There is still no standalone
signal example in `examples/`." Verification:

```
$ ls examples/signals/
counter.mn

$ wc -l examples/signals/counter.mn
45
```

The file at `examples/signals/counter.mn` is 45 lines and is
exactly what I asked for. It demonstrates:

- A source signal: `let mut count = signal(0)`
- A computed signal: `let doubled = signal { count.value * 2 }`
- The reactivity contract (writes to `count.value` invalidate
  `doubled`, which recomputes on next read)
- Expected output documented inline (8 lines of expected
  integer output)

The header docstring is well-crafted:

> The Python bootstrap's C backend currently has a signal-typing
> bug, so run this example via the LLVM path:
> python -m mapanare emit-llvm examples/signals/counter.mn -o
> counter.ll && clang counter.ll runtime/native/libmapanare_rt.a
> -lm -lpthread -o counter && ./counter

This is the correct way to ship a demo with a known limitation:
document the workaround inline, point to the path that works,
and forward-reference what would simplify it (`mnc run`). I
prefer this honesty to a demo that silently fails on one
backend.

The expected-output block (lines 7-15) lets a user verify the
demo without reading the source. This is the documentation
practice every primitive demo should follow.

The demo gap closure earns **+0.05**. Eight cycles is a long
time for a 45-line file, but it shipped.

### Localized READMEs (es / pt / zh-CN) current

All three localized READMEs are at version 5.7.1 with the new
"Native compiler — what `mnc-stage1` ships" subsection in the
local language. I verified Spanish + Portuguese + Chinese:

- **Spanish** (`docs/README.es.md` line 27, 116-126): "Compilador
  nativo — lo que envia `mnc-stage1`" — covers tensores,
  async/await/`block_on` con corrutinas LLVM reales, parametros
  tipo cierre, pattern matching con or-patterns y guards,
  drop-glue para ownership. Punto fijo NEAR documented.

- **Portuguese** (`docs/README.pt.md` line 27, 116-118): "Compilador
  nativo — o que `mnc-stage1` entrega" — same five-bullet
  feature list in Portuguese. Version badge `versao-5.7.1`.

- **Chinese** (`docs/README.zh-CN.md` line 27, 116-126): "原生
  编译器 — `mnc-stage1` 提供的功能" — same five-bullet list
  in Simplified Chinese. Version badge `版本-5.7.1`.

This is good i18n discipline. The localized READMEs are not
machine-translated stubs — the translations are competent and
the technical content is accurate. A Spanish-speaking reviewer
reading "lifetimes de string / list / boxed / tensor rastreados
en rutas de retorno y bucles" gets the same load-bearing
information as an English reader.

### Appendix B: 3-stage fixed point + Native goldens — refreshed

Appendix B at lines 2992-3036 is now version-stamped through
v5.6.4–v5.6.10 regression window, v5.6.11 NEAR restoration, and
v5.7.0 66/66 milestone. The previous version of the appendix had
v4.139.0–present (Dr.1) as the latest entry — now v4.134.0 strict
→ Dr.1 NEAR → v5.6.4–v5.6.10 regression (Ve.1/3/4) → v5.6.11
restoration (14 LOC across emit_index_get / emit_index_set) →
v5.7.0 66/66 are all documented.

The new "Native goldens" subsection at lines 3029-3036 explicitly
crosswalks the `scripts/test_native.py` corpus to the SPEC: 66/66
representative programs, "first 100% native pass in project
history," "closes the v4.x → v5.x parity arc."

This is the documentation discipline I asked for at v5.2.0: the
SPEC tracks self-hosted progress at a level a reviewer can verify.

### Zero grammar changes in the entire v5 arc

```
$ git log v5.0.0..HEAD -- mapanare/mapanare.lark
(empty)
```

The grammar file `mapanare/mapanare.lark` has not been modified
since before v5.0.0. The most recent v4 grammar change was at
v4.139.0 (Gr.2 closure for qualified types). Across **36 v5
releases** the language surface a programmer writes against is
byte-identical. Tensor multi-dim indexing, async coroutine
semantics, closure-typed parameters, or-patterns — all of these
were already in the grammar; v5.x ported the implementation to
the self-hosted compiler.

This is sustained grammar discipline I have praised in three
consecutive reviews and continue to praise. The v5 arc is the
strongest evidence yet that the language is post-1.0 stable
in the way the SPEC §27.1 promises.

## What concerns me

### Sh.5 (`const` in fn bodies) — still open

The known_issues.md line 9 entry:

> Sh.5 | `const` in function bodies partially supported in
> self-hosted | use `let` in fn bodies; `const` works at module
> level | v5.x

This is documented behavior with a documented workaround. The
SPEC's bilingual keyword table at §2.1.1 lists `const` as a
keyword. A user reading the SPEC would assume `const` works
identically inside fn bodies and at module level — but it
doesn't.

This is a LOW deferral. The workaround is correct (`let` works)
and the gap is documented. But the SPEC doesn't have a callout
explaining that `const` in fn bodies is partially supported.
A one-line note in §2.1.1 ("`const` declarations are restricted
to module scope in the v5.x self-hosted emitter; use `let`
inside functions.") would close the documentation gap without
fixing the underlying parser quirk.

I am not docking for this. It is a small documentation
omission against a documented behavior. **Carry forward as
LOW** for v5.8.0 with a SPEC-callout fix.

### Gr.1 (multi-line literal parse-error) — still open

The known_issues.md line 37 entry:

> Gr.1 | multi-line list/tensor literals parse-error | put
> literal on one line; wrap in parens on next | v5.x

This is the parser quirk I have noted since v4.129.0. The
workaround is documented (single-line literal or parenthesized
multi-line) and the gap is small in surface area. The SPEC at
§16.1 (List Literals) and §3.11 (Tensor) shows multi-line
formats in the example code without a footnote. A user
copying the §3.11 multi-line tensor literal:

```mn
let m: Tensor<Float>[2, 3] = Tensor<Float>[[1.0, 2.0, 3.0],
                                            [4.0, 5.0, 6.0]]
```

might assume similar layouts work for List literals. They don't
without parenthesization.

Like Sh.5, this is a LOW documentation gap — a one-line callout
in §16.1 / §3.11 explaining "multi-line literals require
enclosing parens after the opening bracket" would close it. The
parser fix is more invasive (lookahead through newlines) and
correctly deferred to v5.x.

**Carry forward as LOW.**

### `mapanare_version` constraint enforcement (from v5.2.0 review)

I noted at v5.2.0: "**`mapanare_version` constraint is not
enforced.** The field exists in the manifest schema but
`stdlib/pkg.py` does not check whether the currently running
Mapanare version satisfies it before installing."

§30.1 still documents `mapanare_version` as an optional
manifest field with default `">=0.2.0"`. §30.3 (install
semantics) lists seven steps, none of which mention
toolchain-version verification. §30.7 (Out of Scope) does not
list it either.

This isn't a SPEC defect — the field is documented and the
behavior (or lack of it) is implicit. But a user reading §30
would reasonably conclude that setting `mapanare_version =
">=5.7.0"` would prevent installation under v5.6.x. It
doesn't.

A one-line addition to §30.3 step 1: "Manifest load. Parse
`mapanare.toml` at the working directory. **Verify
`mapanare_version` constraint against the running toolchain
version; fail with a diagnostic if unsatisfied** (deferred:
this check is currently not enforced; see §30.7)." — would
close the documentation gap and explicitly defer the
implementation.

**Carry forward as LOW.**

### Transitive resolution honesty — well done, but watch for drift

§30.2 says: "Transitive dependency resolution is deferred; in
v5.3.x, a package's `[dependencies]` table is read but nested
resolution across the full graph is **not guaranteed** —
projects that require it must flatten dependencies manually or
wait for a future spec revision."

This is exactly the right posture at MVP scope. But the
"v5.3.x" anchor in the text will date as v5.x progresses.
When the SPEC is next re-synced, this clause should either
update the version reference ("in v5.7.x") or rewrite as a
future-tense conditional ("until transitive resolution is
specified by a future revision"). Otherwise readers in v5.7+
will see "v5.3.x" and wonder if the limitation has been lifted.

This is a tiny housekeeping note, not a docket.

### `commit` field overload (from v5.2.0 review)

I noted at v5.2.0: "**The `commit` field in the lockfile is
overloaded.** For registry installs, `commit` holds the
SHA-256 of the tarball. For git installs, `commit` presumably
holds a git SHA. This dual semantics is confusing."

§30.4 documents `packages[].commit` as "Archive content hash
(SHA-256)" — single semantic. But the example payload at
§30.4 shows `"commit": "sha256:abc123..."` for what is clearly
a registry install. If a git install uses the same field for
a git SHA, the field meaning depends on the install source —
which §30.4 doesn't make explicit.

A two-line addition to §30.4 — "For git-backed dependencies,
`commit` is the resolved git SHA (not a SHA-256 archive
hash). Distinguishable by the `sha256:` prefix when present." —
would resolve the dual semantics in the SPEC.

**Carry forward as LOW.**

## What remains open

| Docket | Severity | Source | Action |
|---|---|---|---|
| **Gr.1** | LOW | v4.129.0 | Multi-line literal parse-error; docs callout in §3.11 / §16.1; parser fix v5.x |
| **Sh.5** | LOW | known_issues | `const` in fn bodies; SPEC §2.1.1 callout |
| **`mapanare_version` enforcement** | LOW | v5.2.0 carry | SPEC §30.3 step-1 callout + §30.7 deferral |
| **`commit` field dual semantics** | LOW | v5.2.0 carry | SPEC §30.4 two-line clarification |
| **Transitive resolution v5.3.x anchor** | TRIVIAL | this review | §30.2 wording refresh next sync |

Net: **5 LOW + 1 TRIVIAL** carry-forwards. Zero MEDIUM. Zero
HIGH. Zero CRITICAL.

**Items closed from my v5.2.0 carry-forward:**
- **Demo gap (signals)** — CLOSED v5.3.3
- **SPEC-pkg** — CLOSED v5.3.3 (§30 added)
- **SPEC header staleness** (telegraphed -0.05) — CLOSED v5.7.1

## Score breakdown

| Adjustment | ± | Reason |
|---|---|---|
| Demo gap CLOSED (8 cycles) | +0.05 | `examples/signals/counter.mn` 45 LOC |
| SPEC §30 Package Management | +0.10 | Normative spec for the only user-facing v5 feature |
| SPEC header 4.143.0 → 5.7.1 + sync discipline | +0.10 | 27-release staleness window CLOSED + inline discipline addition |
| §3.11 Tensor sync (v5.6.0–v5.6.4) | +0.05 | Self-hosted parity attribution per feature |
| §29 Async sync (v5.5.4–v5.5.7) | +0.05 | Implementation-strategy block, surface stays neutral |
| §6.3 Closure-typed callout (v5.7.0) | +0.025 | Right-detail callout; honest grammar-gap note |
| §5.6 Or-pattern (B) callout (v5.7.0) | +0.025 | Honest current-implementation limit |
| Appendix B refresh (3-stage + native goldens) | +0.025 | Crosswalks stage 2 to corpus |
| Localized READMEs (es / pt / zh-CN) bumped | +0.025 | Native compiler subsection in three languages |
| Zero grammar changes across 36-release v5 arc | +0.05 | Sustained discipline |
| Open: 5 LOW + 1 TRIVIAL carry-forwards | -0.0 | Honestly classified, all documented |
| Open: SPEC documentation gaps (Sh.5 / Gr.1) | -0.05 | One-line spec callouts not yet added |
| **Net delta vs v5.2.0** | **+0.4 minus +0.2 fade** | Cycle-over-cycle ceiling effect |

I am scoring **+0.2 cycle delta**, not the full +0.4 the line items
suggest, because of the EXCEEDS-ceiling effect: my v5.2.0 score
already credited the v5 discipline foundation (zero grammar
changes, honest scoping, post-1.0 stability). Stacking another
+0.4 would over-credit the cumulative work — what's new is the
actual closure of long-standing carry-forwards, not a fresh
discipline signal. **Net: +0.2 from 9.4 → 9.6.**

## The 27-release staleness story

Three consecutive panels — v4.144.0, v4.154.0, v5.2.0 — I
documented the SPEC header at version 4.143.0 against the live
v4.144.0 / v4.154.0 / v5.2.0 release. Each time I stated the
content was correct (no SPEC semantics had drifted) but the
header was misleading. At v5.2.0 I telegraphed: "**I will dock
0.05 next cycle if it persists.**"

The discipline that closes this kind of gap looks like what
v5.7.1 shipped: not just bumping `5.2.0` → `5.7.1` in one
line, but doing a full re-sync of the sections that had the
most language activity in the staleness window — §3.11 for
tensor (v5.6.0–v5.6.4), §29 for async (v5.5.4–v5.5.7), §6.3
for closures (v5.7.0), §5.6 for or-patterns (v5.7.0), §30
for packages (v5.3.3 — earlier in the arc). The "Spec sync
discipline" block at lines 20-29 codifies the discipline so
future cycles don't have to reinvent it: every release fact-
checks the SPEC against the live grammar / type system /
self-hosted lexer.

This is the correct shape of a SPEC re-sync — content discipline
first, version stamp second. It earns more credit than the bare
version bump would have at v5.2.0, because the work delivered
matches the work the SPEC promised.

## The package registry story (continued from v5.2.0)

My v5.2.0 review opened with: "A package registry is the most
dangerous thing a language can build. It is an invitation to
every supply-chain attack the industry has invented:
typosquatting, dependency confusion, install-time code
execution, checksum bypass, compromised maintainer accounts."

§30 spec'd the security posture into the language contract:

1. **No install-time scripts** is now MUST NOT in §30.3
   ("Packages MUST NOT execute arbitrary code during install.").
   This is a load-bearing change — what was a CLI implementation
   choice is now a normative spec rule. A future Mapanare
   distribution that ships `postinstall` hooks is non-conforming.

2. **SHA-256 integrity** is documented in §30.3 step 5 with
   the abort-on-mismatch clause ("**On mismatch, abort with
   no files written.**") and §30.6 first bullet ("SHA-256
   integrity on every download; mismatches abort install.").

3. **Confined side effects** in §30.3 ("**Side effects are
   confined to** the current project directory (`mn_modules/`,
   `mapanare.lock`) and `~/.mapanare/cache/` for downloaded
   archives.") and §30.6 third bullet ("Sandboxed module path.
   Installed packages live under `mn_modules/` relative to the
   project root; resolution never escapes this directory.").

4. **Token security** in §30.6 fourth bullet ("Token storage.
   Tokens are stored with user-only permissions (`0600`) under
   `~/.mapanare/`. They are never written to `mapanare.toml`
   or `mapanare.lock`."). This addresses my v5.2.0 concern
   about credential leakage in committed lockfiles.

The MVP gaps I noted at v5.2.0 — transitive resolution
deferred, greedy resolver, no `mapanare_version` enforcement —
are all now in §30.7 (Out of Scope) or §30.2 with explicit
deferral language ("**not guaranteed**"). The SPEC honestly
documents what works, what is deferred, and what is currently
not enforced. This is the correct posture for a normative
spec at MVP scope.

The two LOW carry-forwards I'm raising in this review
(`mapanare_version` enforcement callout, `commit` field dual
semantics) are documentation refinements, not security
concerns. The MVP security model in §30.6 covers the
load-bearing cases.

## The closeout arc — language-design view

The v5.3.1 → v5.7.1 arc closed three Sh.* parity gaps that have
been open since v4.x:

- **Sh.4 (async)** — opened v4.74 (when async/await first
  entered the grammar); closed v5.5.4–v5.5.7 (full LLVM
  coroutine pipeline). 5 goldens move from "function-count
  match" to "byte-identical output." The Python bootstrap was
  the only path that ran async correctly until v5.5.4; from
  v5.5.4 the self-hosted compiler has full parity.

- **Sh.6 (tensor)** — opened v4.42 (when tensor literals first
  entered the grammar); closed v5.6.0–v5.6.3 (literals + multi-
  dim indexing + broadcasting + slicing + reductions). 5
  goldens move from "parse-error" or "function-count match" to
  "byte-identical output." With Sh.6 closed, the
  "AI-native" claim in the SPEC headline is no longer
  Python-only.

- **Sh.7 (closure-typed)** — opened v4.103 (when fn-typed
  parameters first entered the grammar); closed v5.7.0. 1
  golden moves from FAIL to PASS. With Sh.7 closed,
  higher-order programming via the self-hosted compiler is
  legal.

- **B (or-pattern + None)** — opened v4.35 (when or-patterns
  first entered the grammar); closed v5.7.0. 1 golden moves
  from FAIL to PASS.

These are not v5 features — they are the v4 grammar surface
finally being honored by the self-hosted compiler. The v4 → v5
boundary at v5.0.0 was supposed to mean "the language is post-
1.0 stable on the LLVM backend." The v5.0.0 → v5.7.1 arc was
the project paying the technical debt that statement implied.
At v5.7.0 the corpus reaches 66/66 — the first time in project
history. At v5.7.1 the SPEC is re-synced to attribute the
closure to the right releases.

This is the correct shape of a closeout arc: v4 grammar
shipped + Python bootstrap parity → v5 self-hosted parity +
SPEC re-sync. Every step is documented at the docket level
(PARITY_GAPS.md), the release level (per-release SESSION_REPORT),
and the SPEC level (§3.11 / §29 / §6.3 / §5.6 callouts). A
future reviewer can audit the closure with grep, not narrative.

---

## Verdict

**EXCEEDS.** Third consecutive EXCEEDS, with the largest cycle
delta in my history.

The **+0.2** over my v5.2.0 score reflects:

- **+0.10** for SPEC header closure with full re-sync discipline.
  After three consecutive cycles of warning, the work that closed
  the staleness window was substantive (sync discipline added inline
  to the SPEC, multiple section refreshes, attribution-per-feature
  blocks for tensor and async). The cycle-over-cycle ceiling means
  this is the tail of a multi-cycle credit, not a fresh +0.10.

- **+0.10** for SPEC §30 Package Management. This was the largest
  language-design gap I carried at v5.2.0 (a feature that ships
  but is not in the spec). §30 is normative, RFC-2119-correct,
  and covers all six surfaces I asked for (manifest, constraints,
  install, lockfile, registry, security). The remaining LOW
  carry-forwards (`mapanare_version` enforcement, `commit` field
  dual semantics) are refinements, not rebuttals.

- **+0.05** for the demo gap closure. Eight cycles is a long time
  for a 45-line file, but the file shipped with documented
  expected output, accurate workaround for the C-backend
  signal-typing bug, and forward-reference to `mnc run`. This is
  the kind of demo I asked for at v4.143.0 and got.

- **+0.025** apiece for the §3.11 / §29 / §6.3 / §5.6 / Appendix B
  refresh quality. Each section is attributed-per-feature, honest
  about implementation gaps, and uses the right level of normative
  language.

- **-0.05** for the 5 LOW + 1 TRIVIAL carry-forwards I am opening.
  None of these are language-design defects — they are
  documentation refinements that one re-sync cycle should clean
  up. But the SPEC is in this review's name and the gaps are in
  the SPEC.

- **+0.05** for sustained grammar discipline across 36 v5 releases.
  Zero changes to `mapanare/mapanare.lark` since pre-v5.0.0. This
  is the strongest post-1.0 stability signal a compiled language
  can produce, and it has now held across three consecutive
  reviews.

Net: **+0.2, from 9.4 to 9.6.**

The trajectory is stable in EXCEEDS territory. I do not see a
path to a 10.0 in the v5.x line — that would require an FFI
specification (§18 expansion), a formal stability matrix
covering all 29 TypeKind variants and their LLVM ABI, and a
public-publishing-ready package registry with transitive
resolution. Each of those is multi-release work.

But the v5.7.1 SPEC is the cleanest the language has been since
v1.0.0. Everything that ships through `mnc-stage1` is described
in the SPEC. The corpus passes at 66/66. The fixed point is at
NEAR. The carry-forward closure rate is **3/3 + 3 LOW deferrals
appropriately scoped**. This is the shape of a release that
deserves the v5.8.0 RE-PANEL it's scoped for.

---

## Score history

| Version | Score | Grade | Delta |
|---|---|---|---|
| v4.99.0 | 7.5 | RESERVATIONS | -- |
| v4.114.0 | 8.3 | PASS WITH NOTES | +0.8 |
| v4.120.0 | 8.1 | PASS WITH NOTES | -0.2 |
| v4.136.0 | 8.7 | MEETS | +0.6 |
| v4.143.0 | 8.5 | MEETS | -0.2 |
| v4.144.0 | 8.9 | MEETS | +0.4 |
| v4.154.0 | 9.3 | EXCEEDS | +0.4 |
| v5.2.0 | 9.4 | EXCEEDS | +0.1 |
| **v5.7.1** | **9.6** | **EXCEEDS** | **+0.2** |

The +0.2 is the largest cycle delta in EXCEEDS territory. It
reflects multi-cycle work that landed in one window:
SPEC re-sync (3 cycles deep), SPEC §30 (1 cycle deep), demo gap
(8 cycles deep), Sh.* closure (4-versions deep). Each of these
items was approaching the cost-of-deferral threshold I had
telegraphed in prior reviews. Closing all of them in one arc is
the rare-but-correct response.

---

## Reproducibility

```bash
# SPEC header (closed)
head -5 docs/SPEC.md
# Expected: Version: 5.7.1

# SPEC §30 added v5.3.3
grep -n '## 30. Package Management' docs/SPEC.md
# Expected: 2607

# SPEC §3.11 tensor sync (v5.6.0–v5.6.4)
grep -n 'parity closed v5.6.0' docs/SPEC.md
# Expected: match in §3.11

# SPEC §29 async sync (v5.5.4–v5.5.7)
grep -n 'v5.5.4–v5.5.7 update' docs/SPEC.md
# Expected: match at 2490

# SPEC §6.3 closure-typed callout (v5.7.0)
grep -n 'v5.7.0 (Sh.7 closure)' docs/SPEC.md
# Expected: match at 1220

# SPEC §5.6 or-pattern callout (v5.7.0)
grep -n 'v5.7.0 (B closure)' docs/SPEC.md
# Expected: match at 1105

# Demo gap closed (signals example)
wc -l examples/signals/counter.mn
# Expected: 45

# Localized READMEs current
grep '5.7.1' docs/README.es.md docs/README.pt.md docs/README.zh-CN.md | head
# Expected: matches in all three (es: version-, pt: versao-, zh-CN: 版本-)

# Native compiler subsection in localized READMEs
grep -E 'Compilador nativo|Compilador nativo|原生编译器' \
  docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# Expected: 3 matches

# Zero grammar changes in v5 arc
git log v5.0.0..HEAD -- mapanare/mapanare.lark
# Expected: empty

# Sh.4/6/7 closures in PARITY_GAPS.md
grep -E 'Sh\.4|Sh\.6|Sh\.7|B \(or-pattern' docs/roadmap/v5/PARITY_GAPS.md
# Expected: matches in Historical section

# 66/66 native goldens
grep -n 'first 100% native pass' docs/SPEC.md
# Expected: match in Appendix B

# 3-stage fixed point status
grep -n 'NEAR' docs/SPEC.md | head
# Expected: matches in Appendix B v5.6.11 line
```
