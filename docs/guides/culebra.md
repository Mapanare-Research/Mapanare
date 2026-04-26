# Culebra — IR Diagnostic Workflow

> Contributor reference for the **culebra v2.4.0** template-driven
> LLVM IR / generated C diagnostic engine that Mapanare uses across
> the v5.6.x → v5.7.x arc. This guide is descriptive: it documents
> the workflow that the v5.6.9–v5.7.0 SESSION_REPORTs evolved, not a
> new methodology. For per-command help see
> `.claude/skills/culebra-scan/SKILL.md` and `culebra <cmd> --help`.

---

## 1. What culebra is

Culebra is a Rust-built diagnostic tool that runs Nuclei-style
template scans against LLVM IR (`.ll`) and generated C (`.c`) files.
It ships **49+ templates** organized into five categories:

| Category | What it covers |
|---|---|
| **ABI** | sret/byref classifiers, return-type divergence, struct layout |
| **IR** | PHI corruption, break-inside-nested-control, option-type-pun |
| **Binary** | Symbol export, rodata alignment, missing relocations |
| **Bootstrap** | stage1 / stage2 / stage3 stage divergence patterns |
| **C** | switch-no-break, missing-typedef, union-tag-mismatch |

Templates are YAML-defined under
`~/.culebra/templates/<category>/*.yaml`. Each template fires when
its regex / structural signature matches the input file.

Culebra does **not** parse function bodies into a full AST — it
runs text-pattern matches against the IR. On a 217k-line stage2.ll
this means several findings are template-match noise rather than
real bugs (see §3 False positive policy).

---

## 2. Daily commands

Mapanare uses a small subset of culebra's command surface every
release. Listed roughly in order of frequency:

```bash
# One-line summary — fastest health check
culebra triage stage2.ll --brief

# Save a structured baseline (JSON) — required before every release
culebra baseline save stage2.ll -o docs/roadmap/v5/<release>/culebra/baseline-end.json

# Diff against a saved baseline — what _changed_ since last release
culebra baseline diff stage2.ll -b docs/roadmap/v5/<prev>/culebra/baseline-end.json

# Full triage — group findings by root cause
culebra triage stage2.ll > docs/roadmap/v5/<release>/culebra/triage.md

# Per-struct health — PHI zeroinit, type-pun, null load
culebra health stage2.ll --struct-name EmitState

# String constants — byte-count validation
culebra strings stage2.ll

# Pathology audit — empty switch, alloca alias, PHI undef ref
culebra audit stage2.ll
```

When debugging a specific failure mode (a UAF, a dropped
instruction, a divergent fixed-point), the **debugging arc** below
is the playbook the v5.6.9–v5.7.0 releases used.

### Debugging arc

```bash
# 1. What's wrong?
culebra triage stage2.ll --brief
culebra explain stage2.ll <template-id>     # Show matched IR in context

# 2. Where is it?
culebra suggest stage2.ll --function <fn>   # Prioritized fix suggestions
culebra trace stage2.ll --function <fn> --var '%state'

# 3. Stage divergence?
culebra fixedpoint mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn
culebra diff stage2.ll stage3.ll            # Per-function structural diff
culebra bisect stage2.ll stage3.ll          # Rank divergent fns by impact

# 4. After fixing
culebra verify stage2.ll <template-id>      # Confirm fix: PASS/FAIL
culebra baseline diff stage2.ll             # See what improved
```

### WSL interop gotcha (Windows binary)

Culebra ships as a **Windows PE32+ binary** in
`/home/uan/.cargo/bin/culebra`. When called from WSL it runs
through Windows interop — which means **WSL paths
(`/tmp/stage2.ll`) silently fail with "file not found"**.

Always pass Windows-style paths:

```bash
# WRONG — culebra doesn't see WSL paths
culebra triage /tmp/stage2.ll --brief

# RIGHT — copy to a Windows-mounted path or use the literal Windows path
cp /tmp/stage2.ll /mnt/c/Users/Juan/Documents/GitHub/Mapanare/stage2.ll
culebra triage 'C:\Users\Juan\Documents\GitHub\Mapanare\stage2.ll' --brief
```

A Linux-native culebra is a v5.8.0+ recommendation tracked in the
v5.6.10 SESSION_REPORT.

### Performance notes

The v5.6.9 and v5.6.10 SESSION_REPORTs both noted that on a 217k+
line stage2.ll:

- `triage --brief` completes in seconds.
- `baseline save` completes in 1–2 minutes.
- Full `triage` takes **~7-8 minutes**.
- `summary` (everything-in-one) **may not complete in 5+ minutes**;
  prefer running individual subcommands instead.
- `health`, `audit`, `strings`, `check`, `progress` are all fast.

When iterating on a fix, prefer `triage --brief` + `verify <id>`
over full re-runs.

---

## 3. False positive policy

Culebra v2.4.0 reports **two known critical false positives** on
the Mapanare IR. Treat them as informational, not as bugs:

### `function-count-drop` (≈940 hits, "critical")

The Python bootstrap and `mnc-stage1` produce different sets of
function names by design — Python's helpers (`_lower_*`, `_emit_*`)
have direct equivalents in self-hosted, but they're not 1:1
identifier matches. Every helper-name mismatch flags as a "function
count drop." Documented in v5.6.9 SESSION_REPORT.

### `return-type-divergence` (≈37 hits, "critical")

Aggregate-return runtime declarations (`__mn_str_concat`,
`__mn_str_substr`, `__mn_list_new`, `__mn_str_join`,
`__mn_tensor_alloc`, etc.) appear in both Python-emitted and
self-hosted-emitted IR but with whitespace / attribute differences
that the template-match flags as cross-stage divergent. They are
not — both sides emit equivalent declarations.

### Other "high" findings

- `fixed-point-delta` — counts text-level differences between
  stage outputs. Scales linearly with IR size, not bug count.
- `byte-count-mismatch` — text-pattern noise; the canonical
  byte-count validation runs via `culebra strings` and reports
  "OK All N string constants have correct byte counts" on a
  clean stage2.ll.
- `stage-output-divergence` — same family as `fixed-point-delta`.

Per-release `triage-brief.txt` artifacts are checked into
`docs/roadmap/v5/<release>/culebra/` so reviewers can confirm the
known FP class is preserved (no NEW critical findings).

---

## 4. Per-release journal

Every v5.6.x+ release commits a `culebra-journal.jsonl` to its
`docs/roadmap/v5/<release>/` directory. Use:

```bash
culebra journal add "<message>" --action milestone --tags <tag1>,<tag2>
```

The journal lives at `~/.culebra-journal.jsonl` (or
`./.culebra-journal.jsonl` if invoked from a project root). After
shipping a release, copy the new tail entries into the
release-specific journal:

```bash
tail -N ~/.culebra-journal.jsonl > docs/roadmap/v5/<release>/culebra-journal.jsonl
```

Use `--action` for one of: `note` (default), `bug`, `fix`,
`milestone`. Use `--tags` for searchable categorization (e.g.
`v5.7.0`, `sh7`, `or-pattern`, `closure`, `drop-glue`).

The v5.6.9 release pioneered this practice when the Ve.3 bug took
multiple debugging sessions. Today every release captures at minimum
a `milestone` entry on ship and a `fix`/`bug` entry per docket
closure.

---

## 5. Panel input

Per-release journals aggregate into an **arc journal** at the
panel-prep release:

```bash
cat docs/roadmap/v5/v5.6.9/culebra-journal.jsonl \
    docs/roadmap/v5/v5.6.10/culebra-journal.jsonl \
    docs/roadmap/v5/v5.7.0/culebra-journal.jsonl \
  > docs/roadmap/v5/v5.7.1/culebra/arc-journal.jsonl
```

`arc-journal.jsonl` + `baseline-end.json` are the **primary
diagnostic inputs** for the next panel review (v5.8.0). Reviewers
can:

1. `culebra baseline diff` against the saved JSON to see what
   *actually* changed since the prior anchor.
2. `culebra journal show` (after pointing it at the aggregated
   `arc-journal.jsonl`) to read the debugging trace by milestone /
   fix / bug.
3. Cross-reference the SESSION_REPORTs in
   `docs/roadmap/v5/<release>/SESSION_REPORT.md` for narrative
   context.

This eliminates the "no measurement methodology" objection that
panel reviewers historically raised.

---

## 6. Cross-reference

Worked examples:

- **`docs/roadmap/v5/v5.6.9/SESSION_REPORT.md`** — end-to-end
  debugging trace for the Ve.3 drop-glue UAF on `List<Enum>`
  returns. The SESSION_REPORT walks through 4 hypotheses, the 5
  `__mn_str_eprint` trace points that isolated the bug, and an
  honest retrospective on culebra's contribution (confirmed
  signal classes existed; the actual root cause was found via
  manual instrumentation, not template matches).
- **`docs/roadmap/v5/v5.6.10/SESSION_REPORT.md`** — the
  baseline-freeze methodology, including the WSL paths gotcha and
  the per-release journal cadence.
- **`docs/roadmap/v5/v5.7.1/culebra/`** — the v5.8.0 panel-input
  baseline (clean 66/66 stage2.ll at 217,879 lines, 5 root causes,
  15,829 findings — same false-positive shape as v5.6.10).

Skill reference:

- `.claude/skills/culebra-scan/SKILL.md` — Claude Code skill that
  drives `culebra` commands inside agent sessions. Triggered via
  `/culebra-scan` from the chat surface.
