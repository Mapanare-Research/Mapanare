# Python ↔ Self-Hosted Parity Gaps

> **What's in the Python bootstrap emitter (`mapanare/emit_llvm_text.py`
> + `mapanare/*.py`) that the self-hosted compiler
> (`mapanare/self/*.mn`) does not yet have.** One-stop inventory
> distilled from the v4.154.0 panel — Cobra, Viper, Mamba.
>
> Every item here means: when the Python bootstrap compiles a file,
> it gets optimization X. When `mnc-stage1` (or `mnc-win-x64.exe`)
> compiles the same file, it does not. The self-hosted compiler
> compiling *itself* doesn't benefit from its own optimizations
> unless those optimizations also live in `.mn` form.

**Opened:** 2026-04-21 (v5.0.1 prep)
**Source panels:** v4.154.0 (primary), v4.144.0 (baseline)
**Cadence:** update after every v5.x panel

---

## The headline gap — CLOSED (v5.0.4)

**Cb.15 — ABI.1 sret classifier is Python-only.** → **CLOSED v5.0.4.**

`mapanare/self/abi.mn` (75 LOC) ports the per-target ABI classifier.
`emit_llvm.mn::use_sret_return` replaces the 64B `is_byref_type_st`
threshold for return types. stage2.ll sret count: 2,263 → 4,112.
All 17-64B aggregates on SysV now correctly use sret. Cobra's
verification grep returns 26 matches (was 0 at v5.0.3).

The next headline gap is **Rt.4** (hardcoded `return 16` for enum
sizes in `llvm_type_size`), which becomes load-bearing now that the
ABI classifier uses those sizes for sret decisions.

---

## Inventory by domain

### ABI / Codegen

| ID | Python has | Self-hosted has | Panel | Target |
|---|---|---|---|---|
| ~~Cb.15~~ | ~~`abi.py` + `_use_sret` per-target classifier~~ | ~~`abi.mn` + `use_sret_return`~~ | ~~Cobra v4.154.0~~ | ~~**v5.0.4 CLOSED**~~ |
| Cb.9a | `module_path` field on TypeExpr | Missing in `semantic.mn:520-529` | Cobra v4.144.0+v4.154.0 | v5.0.5 |
| Gr.2 | `named_type (DOT NAME)*` in grammar | Grammar only — parser built qualified types by hand | Coral v4.136.0 | v5.0.5 |
| **Rt.4** | Correct enum size (compute from type def) | Hardcoded `return 16` at `emit_llvm.mn:1646` (should be ≥24 after Rt.1); comment lies | Rattler v4.154.0 | **v5.0.6** — **MEDIUM (latent heap overflow after v5.0.4)** |
| Own.1 | (neither) | (neither) — no move semantics in the language at all | Viper all panels (28 releases) | **v5.1.3** Phase 1 (register_struct / register_enum); v6.0 full borrow checker |

### Optimizer (MIR passes)

The v4.152.0 E8 audit re-evaluated four passes that were disabled at
v4.111.0. Results:

| Pass | Python | Self-hosted | Status | Target |
|---|:---:|:---:|---|---|
| `strength_reduce` | ON | OFF | Zero-ROI both sides; LLVM instcombine covers — parity deferred | — |
| `inline_small_functions` | ON | OFF | **In.1**: rename_instructions collides on caller's `%dst` after inlining | v5.1.2 |
| `licm` | OFF | OFF | **Li.1**: hoist_instruction leaves original in source block — parity, both disabled | v5.1.2 |
| `escape_analysis` | ON | OFF | **Ea.1**: self-hosted version is a stub (`return f` unchanged) | v5.1.2 |

> Cobra v4.154.0 line 41: *"This is a Python-emitter-only fix. The
> self-hosted emitter has no classifier, no `_use_sret`, and still
> returns everything by value up to the old `_BYREF_BYTES = 64`
> threshold."*

### Emitter — enum layout (historical reference)

Prior parity gap, already closed — documented here so we remember
the shape:

| ID | Gap | Closed |
|---|---|---|
| Cb.5 / Rt.1 | `_enum_inline` Python-only; self-hosted emitted `{i64, ptr}` + heap | **v4.140.0** — ported `_enum_inline` to `emit_llvm.mn` with `EmitState.enum_inline_slots` registry |

### Memory-safety residuals

Not strictly parity gaps (both emitters produce the same buggy code),
but Viper v4.154.0 resurfaced these:

| ID | Symptom | Scope | Target |
|---|---|---|---|
| **Ge.1r** | 4 valgrind ERRORS on goldens 26/29/30/31 — "Invalid read of size 16|8" in generics monomorphization | Same root-cause class as Own.1; was asymptomatic at v4.142.0-v4.144.0; resurfaced due to binary-layout shift | v5.1.1 opportunistic |
| Own.1 | `register_struct` / `register_enum` latent UAFs; no move semantics | Language-level ceiling | v5.x feature track |

### Benchmark reporting (Mamba v4.154.0)

Not compiler parity but listed for completeness — all three are
one-line to small fixes Mamba has now flagged 2-3 times:

| ID | Symptom | Target |
|---|---|---|
| **Bn.2** | Geomean arithmetic wrong in FINAL_REPORT (says 1.17×, actual 1.21×); baseline 7.31× mislabeled as 5.83× | v5.1.2 |
| **Bn.3** | JSON `"version": "4.125.0"` hardcoded; **three** consecutive reviews | v5.0.6 (earlier close — hygiene release) |
| **Bn.4** | C `struct_alloc.c` uses malloc+free; Rust/Mapanare return by value — benchmarks measure different things | v5.1.2 |

### Documentation drift (Boa v4.144.0+v4.154.0)

| ID | Symptom | Severity | Target |
|---|---|---|---|
| **Bo.12-table** | README benchmark table still shows retracted "1.12× Rust" / "4.86× C" numbers; table contradicts corrected prose above it | **MEDIUM** | v5.0.6 |
| **Bo.12-i18n** | `docs/README.es.md`, `.zh-CN.md`, `.pt.md` cite retracted numbers; **9 releases behind** | **MEDIUM** | v5.0.6 |

### Test-coverage gaps (Rattler + Anaconda v4.154.0)

| ID | Gap | Target |
|---|---|---|
| **Cb.6-test** | Self-hosted `type_fits_inline_slot` correctly rejects `i64*` but has no test; a refactor could silently re-enable. 2 cycles. | v5.0.6 |
| **An.9** | v4.145.0 E1 unified-return optimization has no IR-shape regression test; silent perf regression wouldn't be caught by current goldens | v5.0.6 |
| **An.10** | Test-count bookkeeping drift (+34 new vs +27 reported); no authoritative count script | v5.0.6 |

### Build-script hygiene

| ID | Issue | Target |
|---|---|---|
| **Dr.1-mutation** | `scripts/build_stage1.py:60-90` mutates `.mn` source in-place via try/finally; pattern since v4.139.0; fragile if restore path crashes. Rattler 2 cycles. | v5.0.6 |

### Process / tracking (Cobra v4.154.0)

Not technical debt, but a tracking failure Cobra called out:

- **Ledger undercount** — v4.153.0 DOCKET_LEDGER claimed 8 open
  dockets; Cobra verified the honest count was 11+ (Cb.15, Cb.9a,
  Own.1 all absent from tracking). 27% undercount.
- **Fix:** this `PARITY_GAPS.md` document exists specifically to
  catch this failure mode. Every panel release going forward audits
  whether items marked closed in SESSION_REPORTs are actually
  verifiable via grep against HEAD.

### Feature gaps (both emitters lack)

Not parity gaps (both missing), but panel-visible:

- **Sh.4** — tensor reshape — v5.x feature track
- **Sh.5** — mutable views — v5.x feature track
- **Sh.6** — stepped slices — v5.x feature track
- **Sh.7** — closure-typed captures — v5.x feature track
- **Sh.9a** — async test harness — v5.x feature track
- **Perf.2** — lazy thread creation in coro scheduler; eliminates the
  `MAPANARE_ASYNC_THREADS=2` workaround that the 0.85× Go headline
  requires — **v5.1.4**

---

## Why this doc exists (process)

Cobra v4.154.0 noted a 27% undercount in the v4.153.0 `DOCKET_LEDGER`:
three carry-forward items (Cb.15, Cb.9a, Own.1) were opened in
earlier SESSION_REPORTs and quietly dropped before the panel. The
ledger tracked 8 open; the honest count was 11.

The fix: a human-readable parity inventory that lives in the roadmap,
not buried in one release's docket ledger. When an item closes, it
moves from the "Inventory" table into the "Historical" section.

The ledger still exists (in per-release `DOCKET_LEDGER.md`) for
severity/status detail. This doc is the *tracking* layer above it
that Cobra's review said we need.

---

## Close policy

An item closes when:

1. The self-hosted `.mn` implementation exists and is invoked from
   the active optimizer/emitter pipeline
2. A test under `tests/llvm/` or `tests/mir_opt/` asserts the Python
   output and the self-hosted output are byte-identical on a
   representative corpus
3. The item moves to the "Historical" section with closure release
   cited

An item does **not** close just because a SESSION_REPORT says it's
done. Cobra's v4.154.0 finding — three items "closed" in
SESSION_REPORTs but absent from the ledger — is the failure mode
this policy exists to prevent.

---

## Historical (closed items)

| ID | What | Closed | Verification |
|---|---|---|---|
| **Cb.15** | ABI.1 sret classifier ported to self-hosted (`abi.mn` + `emit_llvm.mn::use_sret_return`). stage2.ll sret count 2,263 → 4,112. SysV 16B threshold replaces 64B for returns. | **v5.0.4** | `grep -c 'sret\|classify_return\|_use_sret' mapanare/self/emit_llvm.mn` → 12; `grep -c 'abi_classify' mapanare/self/abi.mn` → 2. Fixed-point NEAR (4 diff, Dr.1 only). Sanitizers: 0 new. |
| Cb.5 / Rt.1 | `_enum_inline` ported to self-hosted `emit_llvm.mn` | **v4.140.0** | — |
