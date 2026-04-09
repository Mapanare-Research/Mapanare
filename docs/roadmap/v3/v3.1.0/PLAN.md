# Mapanare v3.1.0 — Cut the Cord

> No Python required. The compiler bootstraps from itself.

**Status:** COMPLETE
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No (build system only — language unchanged)

---

## Goal

Remove Python from the compiler build chain entirely. Anyone with `gcc` and
`llvm` can build Mapanare from source. The bootstrap seed is a checked-in
binary (like Go and Rust do).

---

## Inherited State (from v3.0.3)

| Component | Status |
|-----------|--------|
| Three-stage fixed point | stage2.ll == stage3.ll (78,881 lines, 0 diff) |
| 15/15 golden tests | Correct output + exit 0 |
| Runtime test harness | `scripts/test_runtime.sh` |
| Fixed point verifier | `scripts/verify_fixed_point.sh` |
| Stage1 binary | 2.0 MB ELF x86-64, dynamically linked |
| C runtime | `runtime/native/mapanare_core.c` (~2000 lines) |
| C driver | `runtime/native/mnc_driver.c` (entry point for LLVM binaries) |

---

## Phase 1: Check In the Bootstrap Seed

The stage1 binary is the "seed" — it can compile itself. Check it into the
repo as a platform-specific binary.

### 1.1 — Seed Directory Structure

```
bootstrap/seed/
  linux-x86_64/mnc          # ELF binary (stripped, ~1.5MB)
  # Future: darwin-arm64/mnc, windows-x64/mnc.exe
```

Strip the binary to reduce size. Include a SHA256 checksum file for
verification. Add to `.gitattributes` as binary.

### 1.2 — Build Script (No Python)

Create `scripts/build_from_seed.sh`:

```bash
#!/bin/bash
# Build the Mapanare compiler from the bootstrap seed.
# Requirements: gcc, llvm (llvm-as, llc), bash. No Python.

SEED=bootstrap/seed/linux-x86_64/mnc
SOURCE=mapanare/self/mnc_all.mn
RUNTIME=runtime/native/mapanare_core.c
DRIVER=runtime/native/mnc_driver.c

# Stage 1: seed compiles source → stage1.ll
$SEED $SOURCE > /tmp/stage1.ll
llvm-as /tmp/stage1.ll -o /tmp/stage1.bc
llc /tmp/stage1.bc -o /tmp/stage1.o -filetype=obj -relocation-model=pic
gcc /tmp/stage1.o $DRIVER $RUNTIME -I runtime/native -o mnc -lm -lpthread

echo "Built: ./mnc ($(wc -c < mnc) bytes)"
```

### 1.3 — Makefile Target

```makefile
build-native:  ## Build from seed (no Python required)
	bash scripts/build_from_seed.sh

bootstrap:     ## Full three-stage verification
	bash scripts/verify_fixed_point.sh
```

### 1.4 — CI Job

Add a GitHub Actions job that builds from seed WITHOUT Python:

```yaml
bootstrap-from-seed:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: sudo apt-get install -y llvm gcc
    - run: bash scripts/build_from_seed.sh
    - run: ./mnc tests/golden/01_hello.mn > /tmp/test.ll
    - run: llvm-as /tmp/test.ll -o /dev/null  # validate output
```

---

## Phase 2: Multi-Platform Seeds

### 2.1 — Cross-Compilation

The seed binary needs to exist for each supported platform:

| Platform | Triple | Status |
|----------|--------|--------|
| Linux x86-64 | x86_64-linux-gnu | Ready (current) |
| macOS ARM64 | aarch64-apple-darwin | Needs cross-compile or CI |
| Windows x64 | x86_64-w64-mingw32 | Needs cross-compile or CI |

For now, ship Linux x86-64 only. Other platforms can use Python bootstrap
or Docker until native seeds are available.

### 2.2 — Seed Update Protocol

When the self-hosted compiler changes:
1. Run `verify_fixed_point.sh` — must pass
2. Run `test_runtime.sh` — must pass
3. Copy the new stage1 binary to `bootstrap/seed/<platform>/mnc`
4. Update the SHA256 checksum
5. Commit the new seed

Document this in `bootstrap/seed/README.md`.

---

## Phase 3: Remove Python Build Dependency

### 3.1 — Update Documentation

- `README.md`: installation no longer requires Python
- `docs/getting-started.md`: build instructions use seed
- `CONTRIBUTING.md`: development workflow uses seed

### 3.2 — Keep Python for Development

Python is still needed for:
- Running the 535+ pytest test suite
- MIR tracing (`scripts/mir_trace.py`)
- IR doctor (`scripts/ir_doctor.py`)
- Culebra integration
- The Python LLVM/WASM emitters (deprecated but kept)

The Python dependency moves from "required to build" to "required for
development tooling." End users only need gcc + llvm.

---

## Phase 4: Verify Independence

Run the full build from seed on a CLEAN system (Docker container) with
NO Python installed:

```dockerfile
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y gcc llvm
COPY . /mapanare
WORKDIR /mapanare
RUN bash scripts/build_from_seed.sh
RUN ./mnc tests/golden/01_hello.mn > /tmp/test.ll && llvm-as /tmp/test.ll -o /dev/null
```

---

## Success Criteria

- [x] Bootstrap seed binary checked in (`bootstrap/seed/linux-x86_64/mnc`)
- [x] `scripts/build_from_seed.sh` builds a working compiler from seed
- [x] CI job builds from seed without Python
- [x] Docker test passes on clean Ubuntu (no Python)
- [x] README updated: Python no longer required to build
- [x] Three-stage fixed point still holds

---

## Tools

```bash
# Build from seed
bash scripts/build_from_seed.sh

# Verify the seed is correct
bash scripts/verify_fixed_point.sh

# Test runtime correctness
bash scripts/test_runtime.sh

# Update seed after compiler changes
strip -o bootstrap/seed/linux-x86_64/mnc mapanare/self/mnc-stage1
sha256sum bootstrap/seed/linux-x86_64/mnc > bootstrap/seed/linux-x86_64/mnc.sha256
```
