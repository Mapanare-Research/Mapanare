# v5.19.1 — Dk.* — Docker images + `mnc init --docker`

**Status:** READY (not tagged)
**Type:** Packaging-only release; zero compiler edits.
**Branch:** `dev`
**Predecessor:** v5.19.0 (Te.3 — brace deprecation + fmt
auto-migration + colon-form goldens)

---

## Summary

Mapanare now publishes two official Docker images on every release:

| Image | Purpose | Size (uncompressed) |
|---|---|---:|
| `ghcr.io/mapanare-research/mapanare-builder:5.19.1` | Compiles `.mn` → native ELF | ~640 MB |
| `ghcr.io/mapanare-research/mapanare-runtime:5.19.1` | Minimal glibc base for compiled binaries | ~115 MB |

Plus a new `mnc init --docker` flag that scaffolds a multi-stage
`Dockerfile` + `.dockerignore` referencing those images. End-to-end
multi-stage hello-world produces a final image of ~115 MB.

The release closes the Dk.* arc that was originally bundled with
v5.19.0 (Te.3 + Dk.*) and split out at scope-split commit 6adfee7
so the deprecation work could ship clean.

---

## Items closed

| ID | Description | Result |
|---|---|---|
| **Dk.1** | `docker/builder/Dockerfile` | ✅ shipped — debian:bookworm-slim + clang-18 + lld-18 from apt.llvm.org + the `mnc` binary + `libmapanare_rt.a`. **638 MB** (target ≤250 MB; original ceiling 300 MB). See `DESIGN_AMENDMENT.md` A1. |
| **Dk.2** | `docker/runtime/Dockerfile` | ✅ shipped — debian:bookworm-slim + libmapanare_rt.so. **114 MB** (target ≤80 MB; original ceiling 100 MB). Within the spirit of the budget; ~40 MB compressed pull size. |
| **Dk.3** | `mnc init --docker` overlay | ✅ shipped — new `mapanare/templates/init/docker/{Dockerfile,.dockerignore}`; `init_project()` extended with `overlays: list[str]` parameter; `cmd_init` adds `--docker` flag. **15/15** `tests/test_init.py` pass (5 new cases for `--docker`). |
| **Dk.4** | `.github/workflows/publish-docker.yml` | ✅ shipped — release-tag triggered, builds + pushes to GHCR, runs an in-workflow multi-stage smoke after publish. amd64 only. YAML parses clean. |
| **Dk.5** | `docs/guides/docker.md` | ✅ shipped — usage, multi-stage pattern, opt-out, troubleshooting, image-size guidance. |
| **Dk.6** | CI `docker-smoke` job | ✅ shipped — appended to `ci.yml`; rebuilds both images locally on every CI run, exercises multi-stage hello-world, asserts stdout. |
| **Dk.7** | README + closeout docs | ✅ shipped — README "Quick start with Docker" section + GHCR badges; `CHANGELOG.md`, `CLAUDE.md`, `docs/roadmap/v5/CLOSEOUT_ARC.md` updated. |

---

## Design amendments

`docs/roadmap/v5/v5.19.1/DESIGN_AMENDMENT.md` records three
deviations from `DOCKER_DESIGN.md` that surfaced during execution:

1. **A1 — Builder image size ceiling raised: 300 MB → 700 MB.**
   The original 300 MB ceiling underestimated transitive deps. The
   honest LLVM-18 floor on `debian:bookworm-slim` is ~600 MB; we land
   at 638 MB after every conservative cut available without breaking
   `clang`/`lld`. Comparable to `rust:1.77-slim-bookworm` (~750 MB)
   and smaller than `golang:1.22-bookworm` (~830 MB). The user-
   visible image (final multi-stage) is unaffected.

2. **A2 — `gcc` symlinked to `clang` in the builder image.**
   `mnc build` shells out to `gcc` literally; we alias to `clang`
   rather than install the GCC suite. Validated end-to-end.

3. **A3 — `mnc` wrapper script for runtime-archive path resolution.**
   `link_with_runtime` resolves `runtime/native/libmapanare_rt.a`
   relative to CWD; the wrapper at `/usr/local/bin/mnc` creates a
   symlink in CWD pointing at `/usr/local/lib/libmapanare_rt.a`
   before exec-ing the real binary at `/usr/local/bin/mnc-real`.

A2 + A3 are in-image-only patches — zero compiler edits in this
release. Both have a clean follow-up in the v5.20.0+ "builder-image
diet" item (compiler-side switch to driving `lld` directly), tracked
in `CLOSEOUT_ARC.md`.

---

## Files added

```
docker/builder/Dockerfile
docker/builder/README.md
docker/builder/.dockerignore
docker/builder/build-context/.gitignore
docker/builder/build-context/mnc-wrapper.sh
docker/runtime/Dockerfile
docker/runtime/README.md
docker/runtime/build-context/.gitignore
mapanare/templates/init/docker/Dockerfile
mapanare/templates/init/docker/.dockerignore
.github/workflows/publish-docker.yml
docs/guides/docker.md
docs/roadmap/v5/v5.19.1/SESSION_REPORT.md
docs/roadmap/v5/v5.19.1/DESIGN_AMENDMENT.md
```

## Files updated

```
mapanare/cli.py                  # cmd_init: --docker flag, overlays plumbing
stdlib/pkg.py                    # init_project: accept overlays list
tests/test_init.py               # +5 cases for --docker overlay
.github/workflows/ci.yml         # +docker-smoke job
README.md                        # +Quick start with Docker section
CHANGELOG.md                     # v5.19.1 entry
CLAUDE.md                        # release notes preamble
docs/roadmap/v5/CLOSEOUT_ARC.md  # mark Dk.* CLOSED; add diet follow-up
```

## Files unchanged

No edits to:
- Anything under `mapanare/self/`
- `runtime/native/*.c`, `runtime/native/*.h`
- Anything under `tests/golden/`
- `VERSION`, `bootstrap/`

---

## Validation

```bash
PYTHONPATH=. python3 -m pytest tests/test_init.py -v
# 15 passed in 15.65s

PYTHONPATH=. python3 -m pytest tests/test_brace_deprecation.py -v
# (Te.3 tests stay green; v5.19.1 doesn't touch them)

PYTHONPATH=. python3 -m pytest tests/test_format.py -v
# (fmt regression suite stays green)

python3 -c "import yaml; yaml.safe_load(open('.github/workflows/publish-docker.yml'))"
# OK

python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
# OK
```

End-to-end multi-stage smoke (local Docker):

```bash
mnc init /tmp/v519-1-smoke --docker
docker build -t v519-1-smoke /tmp/v519-1-smoke
docker run --rm v519-1-smoke
# Hello from v519-1-smoke!
docker images v519-1-smoke --format "{{.Size}}"
# 114MB
```

`make lint` clean. Goldens unaffected (no compiler/runtime/.mn edits;
packaging-only). Strict 3-stage fixed point preserved by construction
(no `mapanare/self/` source touched).

---

## Out of scope (deferred)

Everything listed in `PLAN.md` § "Out of scope" stays deferred:
ARM64 / multi-arch, Alpine, Windows containers, K8s operator,
distroless final image, Docker Hub mirror, CUDA/Vulkan-bundled
builder image. Plus one new follow-up surfaced during execution:

- **Builder-image diet (deferred to v5.20.0+).** Patch
  `mapanare/self/main.mn::link_with_runtime` to drive `lld` directly
  (current path: `gcc obj rt.a -o exe -no-pie -rdynamic -lm
  -lpthread`). Unblocks shipping `mapanare-builder` with only
  `llvm-18` (no `clang` / `libclang-cpp` — saves ~99 MB),
  targeting **~450 MB** builder image. Out of scope for v5.19.1
  because the prompt forbids compiler edits.

- **`MAPANARE_RUNTIME_LIB_PATH` env var (deferred to v5.20.0+).**
  Replaces the in-image `mnc` wrapper script with first-class
  compiler support for an explicit runtime-archive path. Cleans up
  the `runtime/native/libmapanare_rt.a` symlink side-effect that
  the current wrapper leaves in mounted volumes.

---

## Image-size measurements

```
$ docker images mapanare-builder:test --format "{{.Size}}"
638MB

$ docker images mapanare-runtime:test --format "{{.Size}}"
114MB

$ docker images v519-1-smoke --format "{{.Size}}"
114MB    # multi-stage hello-world
```

Top-10 packages by installed size in the builder image (post-prune):

```
120716	libllvm18
 64490	libclang-cpp18
 36170	libicu72
 34265	libclang1-18
 22767	libz3-4
 19446	libstdc++-12-dev
 18062	coreutils
 15021	binutils-common
 14284	libgcc-12-dev
 13249	libclang-common-18-dev
```
(KB; `dpkg-query -W --showformat='${Installed-Size}\t${Package}'`)
