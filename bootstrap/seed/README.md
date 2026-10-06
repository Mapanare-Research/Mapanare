# Bootstrap Seed Binaries

This directory contains pre-built Mapanare compiler binaries used to bootstrap
the compiler from source without requiring Python.

## How It Works

The Mapanare compiler is self-hosted: it compiles itself. To break the
chicken-and-egg problem, we check in a known-good binary (the "seed") that
can compile the compiler source into a new binary.

```
seed/mnc  +  mapanare/self/mnc_all.mn  -->  ./mnc  (fresh binary)
```

This is the same approach used by Go, Rust, and OCaml.

## Platform Support

| Directory | Platform | Triple |
|-----------|----------|--------|
| `linux-x86_64/` | Linux x86-64 | x86_64-linux-gnu |

Future: `darwin-arm64/`, `windows-x64/`.

## Building From Seed

```bash
bash scripts/build_from_seed.sh
```

Requirements: `gcc`, `llvm` (llvm-as, llc). No Python.

## Updating the Seed

When a syntax change in `mapanare/self/*.mn` lands that the current
seed can't parse — e.g. v5.48.1's Te.3.D.5 migration of
`mnc_all.mn` to colon-block syntax which the v0.6.0 seed segfaulted
on — update the seed.

### Automated (preferred)

Trigger `.github/workflows/update-bootstrap-seed.yml` from the
GitHub Actions UI ("Update Bootstrap Seed"). The workflow:

1. Builds `mapanare/self/mnc-stage1` on an `ubuntu-latest` runner via
   `python scripts/build_stage1.py`.
2. Verifies the new binary compiles colon-block source AND
   `mapanare/self/mnc_all.mn` to valid IR.
3. Runs `bash scripts/build_from_seed.sh` end-to-end with the new
   seed staged — falsifies any case where the seed wouldn't make the
   bootstrap CI gate green.
4. Strips + checksums, then opens a PR against the triggering branch
   with `bootstrap/seed/linux-x86_64/{mnc,mnc.sha256}` updated.

Review the PR (the workflow log shows verification output) and merge.

### Manual (when CI isn't available)

1. **Verify correctness first:**
   ```bash
   bash scripts/verify_fixed_point.sh   # stage2.ll == stage3.ll
   bash scripts/test_runtime.sh          # all runtime tests pass
   ```

2. **Update the seed binary:**
   ```bash
   strip -o bootstrap/seed/linux-x86_64/mnc mapanare/self/mnc-stage1
   ```

3. **Update the checksum:**
   ```bash
   cd bootstrap/seed/linux-x86_64
   sha256sum mnc > mnc.sha256
   ```

4. **Commit both files together.**

## Verification

Each seed has a `.sha256` file. To verify:

```bash
cd bootstrap/seed/linux-x86_64
sha256sum -c mnc.sha256
```

## Security

The seed binary is built from the exact source in `mapanare/self/`. The
three-stage fixed-point verification (`verify_fixed_point.sh`) proves that
the seed faithfully represents the source: compiling the source with the
seed produces an identical compiler, which in turn produces an identical
compiler again.
