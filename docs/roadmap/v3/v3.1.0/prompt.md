# v3.1.0 — Cut the Cord — Continuation Prompt

> Remove Python from the build chain. Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.1.0/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.

## MANDATORY: Use Culebra for ALL debugging

```bash
~/.cargo/bin/culebra wrap -- gcc ...
~/.cargo/bin/culebra journal add "description" --action fix --tags "bootstrap"
~/.cargo/bin/culebra journal show
```

---

## Goal

Anyone with `gcc` + `llvm` can build Mapanare. No Python required.
The bootstrap seed is a checked-in binary.

---

## Attack Order

### Phase 1: Check In the Seed

1. Strip the stage1 binary: `strip -o bootstrap/seed/linux-x86_64/mnc mapanare/self/mnc-stage1`
2. Create `bootstrap/seed/README.md` with seed update protocol
3. Generate SHA256: `sha256sum bootstrap/seed/linux-x86_64/mnc > bootstrap/seed/linux-x86_64/mnc.sha256`
4. Add to `.gitattributes`: `bootstrap/seed/*/mnc binary`

### Phase 2: Build Script

Create `scripts/build_from_seed.sh`:
- Detect platform, select seed binary
- Run seed on `mapanare/self/mnc_all.mn` → LLVM IR
- Compile via llvm-as → llc → gcc
- Output: `./mnc` binary

### Phase 3: CI Job

Add `bootstrap-from-seed` job to `.github/workflows/ci.yml`:
- ubuntu-latest, no Python
- Build from seed, validate output

### Phase 4: Docker Test

Create `Dockerfile.bootstrap`:
- FROM ubuntu:24.04 (no Python)
- Install gcc + llvm only
- Build from seed
- Run golden test

### Phase 5: Documentation

- Update README.md install section
- Update getting-started.md
- Keep Python as "development dependency" only

---

## Key Files

| File | Role |
|------|------|
| `bootstrap/seed/linux-x86_64/mnc` | **NEW** — seed binary |
| `bootstrap/seed/README.md` | **NEW** — seed update protocol |
| `scripts/build_from_seed.sh` | **NEW** — build without Python |
| `.github/workflows/ci.yml` | Add bootstrap-from-seed job |
| `Dockerfile.bootstrap` | **NEW** — clean-room test |
| `README.md` | Update install instructions |

---

## Verification

```bash
# Must all pass:
bash scripts/build_from_seed.sh          # builds ./mnc
./mnc tests/golden/01_hello.mn | llvm-as -o /dev/null  # validates
bash scripts/verify_fixed_point.sh       # fixed point holds
bash scripts/test_runtime.sh             # runtime correct
```
