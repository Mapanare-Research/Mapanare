# v5.27.0 — Mc.8 + Mc.9 + Tk.1 — formatter polish

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.26.0 shipped (Mb.\* arc closed).
**Estimated effort:** 1 session (~3–4 hours).
**Arc context:** Closes the **Mc.\*** parity arc (formatter
gaps) and opens a small **Tk.\*** sub-arc (terseness rewriter
hardening). Continuation of v5.13.0 Mc.2 (`mnc fmt` linchpin)
and v5.18.0 Mc.\* (LSP + init + check).

---

## Why this exists

Three unrelated formatter / rewriter polish items that share a
release because they all live in `mapanare/format.py` and ship
without compiler edits.

- **Mc.8** (`--line-length`): v5.13.0 SESSION_REPORT explicitly
  promised "long-line wrapping deferred to v5.20.0+." Twelve
  releases stale at v5.27.0. The user-visible cost is real —
  `mapanare fmt` is non-opinionated about line length, so any
  team standardizing on 100/120 still needs an external tool.
- **Mc.9** (`--sort-imports`): same v5.13.0 deferral; same
  staleness. Idempotent alphabetical sort within stdlib /
  third-party / local groups.
- **Tk.1** (`to_terse` empty `#{}` rewriter bug): surfaced in
  v5.24.1 Wd.2 during the SPEC corpus migration — the rewriter
  emits `#:` followed by an indented `pass` for empty map
  literals, which is grammatically invalid. v5.24.1 used a
  manual revert at SPEC §17.1 as a scope-creep guard. v5.27.0
  fixes the rewriter and removes the manual revert.

⚠ **Cadence note:** v5.27.0 is the v5.24.0 Hy.3 cadence-gate
hard-fire target (5 minor versions since v5.22.0 panel). The
**v5.28.0 RE-PANEL** closes the cadence gap one minor late.
PLAN explicitly acknowledges this and does NOT attempt to
panel earlier — the formatter polish is the wrong scope to
bundle with a panel cycle.

---

## Goals

1. **Mc.8** `mnc fmt --line-length N` (default 100, configurable
   via `mapanare.toml`).
2. **Mc.9** `mnc fmt --sort-imports` (alphabetical within
   stdlib / third-party / local groups).
3. **Tk.1** `to_terse` empty `#{}` map preserved verbatim;
   SPEC §17.1 manual revert retired.
4. New `tests/test_format_wrap.py`, `tests/test_format_imports.py`,
   `tests/test_format.py::test_to_terse_empty_map`.
5. Strict 3-stage fixed point preserved at v5.26.0's line count
   (zero `mapanare/self/*.mn` source edits in v5.27.0; bootstrap
   formatter port deferred per Cb.\* / B.\* precedent).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Tk.1** | LOW (latent bug) | **`to_terse` empty `#{}` map fix.** In `mapanare/format.py::to_terse`, the map-literal rewriter unconditionally emits the colon-block form even when the body is empty. Special-case: `MapLit(items=[])` → `#{}` verbatim, no `pass` synthesis. Two new unit tests: empty-map preservation + idempotence on `#{}`. Then revert SPEC §17.1's manual `<!-- preserve-brace -->` marker for the affected example. | 1h |
| **Mc.8** | LOW (Coral L?) | **`mnc fmt --line-length N`.** Conservative wrapping rules — only wrap at clean break points: comma in arg lists, pipe operator, `&&` / `||`, method chains. Do NOT wrap inside string literals, inside expression internals (e.g. `a + b + c` stays on one line even if long). Default 100; reads `[fmt] line_length` from `mapanare.toml` if present. New `format.py::wrap_lines(src, width)` (~80 LOC). | 1.5h |
| **Mc.9** | LOW (Coral L?) | **`mnc fmt --sort-imports`.** Alphabetical sort within three groups: stdlib (`stdlib/...`), third-party (anything other), local (`./` / relative). Preserves blank-line group separators. Idempotent — running twice produces identical output. New `format.py::sort_imports(src)` (~50 LOC). | 1h |
| **Mc.8/9 wiring** | LOW | CLI + native dispatch. `mapanare/cli.py::cmd_fmt` learns `--line-length` and `--sort-imports`. `mapanare/self/main.mn` shells out to Python (mirror of v5.18.0 Mc.\* `check`/`init`/`lsp` pattern). New documentation in `docs/guides/formatter.md`. | 30 min |

---

## Phase plan

### Phase 0 — pre-flight verification (~10 min)

```bash
bash scripts/verify_fixed_point.sh --keep
make ci-gates
pytest tests/test_format.py -v  # must be green at v5.26.0 HEAD
```

### Phase 1 — Tk.1 (smallest, isolates the fix path)

The rewriter bug surfaces only on empty `#{}`. Fix is a 1-line
guard plus 2 new tests. Revert SPEC §17.1 marker as the proof of
fix — if the SPEC corpus rewrite produces clean output without
the marker, Tk.1 is closed.

### Phase 2 — Mc.8 (long-line wrap)

Conservative ruleset is the entire design. Pick two or three
break points (comma, pipe, `&&`/`||`); refuse to wrap anything
else. Idempotence test is mandatory — running `--line-length 100`
twice must produce identical output.

### Phase 3 — Mc.9 (import sort)

Smaller surface than Mc.8. The only design call is the group
ordering — pick stdlib → third-party → local (matches Python
convention) and document in `docs/guides/formatter.md`.

### Phase 4 — wire + native dispatch

CLI flags + `main.mn` shell-out. `tests/test_cli.py` extension
to assert both flags reach `cmd_fmt`.

---

## Out of scope

- **Bootstrap formatter port** — `mnc fmt` shells out to Python
  (Mc.2 / v5.13.0 design). Native formatter port stays out of
  scope until borrow-checker work in v6.0.
- **Opinionated wrapping** — anything beyond commas / pipes /
  short-circuits. Especially: no wrapping mid-expression, no
  re-flowing of comments, no realignment of trailing comments.
- **Import sorting beyond alphabetical** — no usage-based,
  no group-customization, no `# isort: skip` annotations.
  Three groups, alphabetical, done.
- **`mnc fmt --to-terse` improvements** beyond Tk.1 — the
  bigger `to_terse` audit is out of scope.

---

## Success criteria

- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.
- ✅ `mapanare fmt --line-length 100 mapanare/self/mnc_all.mn`
  runs to completion, idempotent on second invocation, produces
  no semantic diff (AST-preserving — same constraint as Mc.2).
- ✅ `mapanare fmt --sort-imports mapanare/self/main.mn`
  idempotent.
- ✅ `to_terse` produces `#{}` verbatim for empty map literals.
- ✅ SPEC §17.1 `<!-- preserve-brace -->` marker removed.
- ✅ `tests/test_format_wrap.py` + `tests/test_format_imports.py`
  + `tests/test_format.py::test_to_terse_empty_map` all green.

---

## Carry-forward delta

Closes:
- **Mc.8** (12-release carry: v5.13.0 → v5.27.0).
- **Mc.9** (12-release carry: v5.13.0 → v5.27.0).
- **Tk.1** (3-release carry: v5.24.1 → v5.27.0).

Out of arc but related:
- The bigger v5.13.0 formatter docket — long-line wrap and
  import sort were the only items still open. v5.27.0 closes
  them; Mc.\* parity arc is fully closed entering v5.28.0
  panel.

Inherits to v5.28.0 panel:
- 0 HIGH / 0 MEDIUM / ~3 LOW open in carry-forward
  docket post-v5.27.0.
