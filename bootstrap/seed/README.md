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

When the self-hosted compiler changes, update the seed:

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
