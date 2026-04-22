# v5.x PROMPT.md Standard Template

> Every v5.x release PROMPT.md follows this template. Extracted from
> the v4.140.0–v4.150.0 pattern so future releases don't re-derive it.
>
> The template has **three tiers**:
>
> - **Baseline** sections — every release has these
> - **UB-risk** sections — releases that touch runtime / ABI / drop-glue
> - **Perf experiment** sections — the measure → hypothesis → patch →
>   verify → 5% rule → record loop
>
> Per-release PROMPT.md files take the baseline plus whichever tier
> applies.

---

## Baseline sections (every release)

### 1. Title + lead paragraph
```markdown
# v5.X.Y Execution Prompt — "<codename>"

> Read `PLAN.md` first. <one-paragraph summary of scope>.
```

### 2. Read before starting
Numbered list of files / docs to load into context first.

### 3. Environment (platform spec)

Pick one:

**WSL2-only work (stage2 / fixed-point / valgrind / ASan):**
```markdown
## Environment

This session runs in **WSL2** (Linux on Windows). Key implications:
- Git push via HTTPS may fail (`No such device or address`). If push
  fails, ask the user to run `! git push origin dev` manually.
- File paths: `/mnt/c/Users/Juan/Documents/GitHub/Mapanare/...`
- All build tools (clang, gcc, python3, llvm-as, opt, lli, hyperfine,
  rustc, go) are WSL-native.
- Valgrind, ASan, TSan only available under WSL.
- Fixed-point verification (`scripts/verify_fixed_point.sh`) is
  Linux-only.
```

**Windows-only work (PyInstaller bundle / w64devkit / Windows CI):**
```markdown
## Environment

This session runs on **Windows 11 native** (`Platform: win32`). Key
implications:
- Shell is Git Bash — Unix syntax works; `/dev/null` not `NUL`;
  forward slashes in paths.
- MinGW toolchain available via `./toolchain/bin/` (if staged)
  or via PATH (if user ran winget install).
- No valgrind; no Linux-only sanitizers.
- Fixed-point verification deferred (Linux CI does it).
```

**Either platform (docs / YAML / plans):**
```markdown
## Environment

Docs-only edits — either WSL or Windows works. If any step requires
running `build_stage1.py` or goldens, drop into WSL for that step.
```

### 4. GitNexus pre-flight (MANDATORY before edit)

Every release with compiler / runtime / build-script changes:

```markdown
## GitNexus pre-flight (MANDATORY before edit)

Ensure the index is fresh:
```bash
npx gitnexus analyze
```

Assess blast radius for every symbol this release touches:
```
gitnexus_impact({target: "<fn_name>", direction: "upstream"})
gitnexus_context({name: "<fn_name>"})
gitnexus_query({query: "<feature or symptom>"})
```

**STOP and report to the user if any `gitnexus_impact` returns
HIGH or CRITICAL risk.** Do not proceed until the user acknowledges.
```

### 5. Phases (numbered)

Each phase:
- Heading with duration estimate
- Specific file:line edits
- Verification command at end of phase

### 6. Standard reproduction snippets

Include whichever apply:

```bash
# Fixed-point verification (WSL)
bash scripts/verify_fixed_point.sh --keep
md5sum /tmp/stage2.ll /tmp/stage3.ll

# Golden tests (WSL)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -5

# Non-bootstrap pytest
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 | tail -3

# Bootstrap pytest
python3 -m pytest tests/bootstrap/ --tb=no -q 2>&1 | tail -3

# Lint gate
ruff check . && black --check . && mypy mapanare/ runtime/

# Valgrind sweep (WSL)
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh 2>&1 | tail -5

# ASan sweep (WSL)
bash scripts/run_asan_goldens.sh 2>&1 | tail -5

# Cross-language benchmark (WSL)
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v5.X.Y-baseline.json
```

### 7. Ready-to-ship checklist

```markdown
## Ready-to-ship checklist

Before commit:
- [ ] VERSION file reads `5.X.Y`
- [ ] `docs/roadmap/ROADMAP.md` has a new "Where We Are (v5.X.Y ...)" entry
- [ ] `CLAUDE.md` has a v5.X.Y entry at top of "Current Version & Roadmap"
- [ ] `docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` written
- [ ] `docs/roadmap/v5/PARITY_GAPS.md` updated for any closed items
- [ ] Non-bootstrap pytest 0-fail
- [ ] Bootstrap pytest unchanged (byte-identical failure set)
- [ ] `make lint` clean
- [ ] (if compiler change) strict 3-stage fixed-point holds on Linux
- [ ] (if runtime change) valgrind 0 new ERRORS, ASan 0 new findings
- [ ] `gitnexus_detect_changes({scope: "staged"})` matches expected scope
```

### 8. Commit + tag + push

```markdown
## Commit + tag + push

```bash
# Stage the change set (prefer specific files over `git add -A`)
git add <files>

# Commit with the docket-closure format
git commit -m "$(cat <<'EOF'
v5.X.Y: <theme> — <docket IDs closed>

<one-paragraph summary: what changed, why, quantitative result>

<bullet list if multi-docket>

<test + sanitizer state summary>

Closes <docket IDs>. docs/roadmap/v5/PARITY_GAPS.md: <moved items>.
EOF
)"

# Tag the release
git tag v5.X.Y

# Push — if HTTPS auth fails in WSL, stop and ask the user to
# `! git push origin dev && git push origin v5.X.Y` from their shell
git push origin dev
git push origin v5.X.Y

# Re-analyze so GitNexus index reflects the new commit
npx gitnexus analyze

# Journal the release
culebra journal add "v5.X.Y shipped: <one-line>" --action milestone
```
```

### 9. "Don't" section

5-10 explicit anti-patterns. The list per release should include
the generic ones:

- Do not skip GitNexus impact analysis on any symbol edit
- Do not push without passing `gitnexus_detect_changes`
- Do not commit if strict fixed-point broke
- Do not skip sanitizer sweeps on runtime / ABI / codegen changes
- Do not amend a published commit; always create new commits

Plus 3-5 release-specific ones.

---

## UB-risk tier (runtime / ABI / drop-glue releases)

Add after Phase N, before commit:

### Sanitizer HARD GATE

```markdown
## Sanitizer HARD GATE (non-negotiable)

This release touches <runtime alloc / ABI layout / drop-glue / ...>.
Any new valgrind ERROR or ASan finding is an unconditional rollback.

```bash
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh
awk '$2 == "ERROR"' /tmp/vg/valgrind-summary.tsv | wc -l
# expect: <= <baseline count>; any increase triggers rollback

bash scripts/build_asan.sh
ASAN_OUTDIR=/tmp/asan bash scripts/run_asan_goldens.sh
awk '$2 == "ASAN_ERROR"' /tmp/asan/asan-summary.tsv | wc -l
# expect: 0; any finding triggers rollback

# TSan (if release touches threading / agents / scheduler)
bash scripts/build_tsan.sh
pytest tests/native/test_c_hardening.py -v
# expect: 0 races reported
```

If any gate fires: revert the patch, close the docket as "attempted
and reverted," open a v5.X.(Y+1) slot for the follow-up investigation.
Do not ship a regressed sanitizer state.
```

---

## Perf experiment tier (releases targeting cross-language benchmarks)

Use for v5.0.4 (Cb.15 sret), v5.1.0 (list IR inlining), v5.1.4
(lazy threads), and any future E-series.

### HYPOTHESIS.md writing task

```markdown
## Phase 0 — Write HYPOTHESIS.md

Before touching code, write `docs/roadmap/v5/v5.X.Y/HYPOTHESIS.md`:

- **Target workload**: <benchmark file + function>
- **Baseline**: <current Mapanare number + Rust/C reference + ratio>
- **Hypothesis**: <why this lever will improve the target>
- **Patch sketch**: <file:line of planned change + ~LOC estimate>
- **Expected outcome**: <target ratio post-patch>
- **5% rule**: hit → ship. Miss → roll back, mark DEAD END.
- **Non-target watch list**: <workloads that might regress>; acceptable
  regression ≤ 2%.

Commit HYPOTHESIS.md as the first commit of the release before any
code edit. This prevents post-hoc rationalization of results.
```

### IR_DIFF.md + RESULTS.md writing tasks

```markdown
## Phase M — Write IR_DIFF.md + RESULTS.md

After measurement:

`docs/roadmap/v5/v5.X.Y/IR_DIFF.md`:
- Use `culebra extract` to pull the target function's IR before +
  after optimization
- Table format: column per function, row per attribute (inline flags,
  call count, alloca count, branch count)

`docs/roadmap/v5/v5.X.Y/RESULTS.md`:
- n=20 measurement for each target workload + reference
- ratio vs Rust + vs C + vs self
- non-target workload impact table
- 5% rule decision: PASS / FAIL
- LLVM IR size delta for stage2.ll

Culebra commands used:
```bash
culebra extract /tmp/before.ll <function> > /tmp/before-fn.ll
culebra extract /tmp/after.ll  <function> > /tmp/after-fn.ll
culebra diff /tmp/before-fn.ll /tmp/after-fn.ll > docs/roadmap/v5/v5.X.Y/ir.diff
```

### 5% rule

Hard decision boundary. No discussion, no "almost there":

- Target workload improves ≥ 5% → ship
- Target workload improves < 5% → roll back, mark DEAD END in
  PERF_EXPERIMENTS.md, commit message reads
  `v5.X.Y: <lever> DEAD END — <n>% below 5% threshold`

No partial landings. The patch either earns the slot or is reverted.

### Non-stacked levers

If the release attempts multiple levers (E6a / E6b / E6c pattern):

- Measure after EACH lever, not at the end
- Record each as a separate entry in PERF_EXPERIMENTS.md
- Each lever faces the 5% rule independently
- If lever N fails but lever N+1 succeeds, the combined delta still
  matters — but the naming ("E6b WIN, E6a DEAD END") prevents
  future confusion
```

---

## Template check before committing a new release's PROMPT.md

Grep the PROMPT you're about to save:

```bash
grep -c "gitnexus\|npx gitnexus" docs/roadmap/v5/v5.X.Y/PROMPT.md
# expect: >= 3 (analyze, impact/context, post-commit analyze)

grep -c "git push origin" docs/roadmap/v5/v5.X.Y/PROMPT.md
# expect: >= 2 (push dev, push tag)

grep -c "culebra journal add" docs/roadmap/v5/v5.X.Y/PROMPT.md
# expect: >= 1

grep -c "## Don't\|## What NOT to do" docs/roadmap/v5/v5.X.Y/PROMPT.md
# expect: == 1

grep -c "Environment" docs/roadmap/v5/v5.X.Y/PROMPT.md
# expect: >= 1 (platform specification)

grep -c "Ready-to-ship checklist\|## Ready-to-ship" docs/roadmap/v5/v5.X.Y/PROMPT.md
# expect: == 1
```

If any of those greps returns 0 where the template requires ≥ 1, the
PROMPT is incomplete — add the missing section before saving.

---

## Platform matrix (which release goes on which OS)

| Release | Platform | Why |
|---|---|---|
| v5.0.1 | Windows (bundle + smoke) + WSL (stage1 build) | Bundle is Windows-native; `build_stage1.py` Windows path needs Linux-side test too |
| v5.0.2 | Either | Reactive — whatever v5.0.1 caught |
| v5.0.3 | CI-only (`macos-13`) | No local macOS; trust CI |
| v5.0.4 | **WSL required** | ABI classifier port + fixed-point verification |
| v5.0.5 | **WSL required** | Grammar + semantic.mn + fixed-point |
| v5.0.6 | Either (mostly docs) | Some Dr.1-mutation patch needs WSL |
| v5.1.0 | **WSL required** | List IR inlining + sanitizer sweep + benchmarks |
| v5.1.1 | **WSL required** + Windows CI | Ge.1r needs valgrind; Windows stage2 needs CI |
| v5.1.2 | **WSL required** | MIR passes + fixed-point + benchmarks |
| v5.1.3 | **WSL required** | Own.1 drop-glue + valgrind + ASan + TSan |
| v5.1.4 | **WSL required** | Lazy threads + TSan + benchmarks |
| v5.2.0 | **WSL for client**; Cloudflare for registry | Multi-session; registry backend is separate |
| v5.3.0 | **WSL required** | Panel measurement + sanitizers + benchmarks |
