# v5.19.1 — Dk.* — Docker images + `mnc init --docker`

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.19.0 shipped (Te.3 — terseness arc closed,
golden corpus on colon syntax). v5.18.0 shipped (`mnc init`).
**Estimated effort:** 14–18h, one or two sessions. Bulk is the
Docker image work; CI workflow + docs are smaller.

---

## Why this exists

Mapanare's "compile native binaries" pitch is undermined by the
toolchain install burden. A clean-machine "try Mapanare" today is
"install LLVM 18, install clang, install lld, install Mapanare,
hope the versions match." That's a high bar for a language that
markets itself as "closer to Go than Python."

A pre-built `ghcr.io/mapanare-research/mapanare-builder:5.19.1`
reduces the bar to:

```bash
docker run --rm -v $(pwd):/src \
  ghcr.io/mapanare-research/mapanare-builder:5.19.1 \
  build main.mn
```

Multi-stage Dockerfiles let users ship apps as ~85 MB final images.
That's the headline.

This release was originally scoped as part of v5.19.0 (Te.3 + Dk.*)
but split out mid-execution so the deprecation work could ship
cleanly. Locked design decisions live in
`docs/roadmap/v5/v5.19.0/DOCKER_DESIGN.md`.

---

## Goal

1. `ghcr.io/mapanare-research/mapanare-builder:5.19.1` and `:latest`
   — debian:bookworm-slim + clang-18 + lld-18 + LLVM 18 dev libs +
   the `mnc` binary + `libmapanare_rt.a`. Target ≤250 MB; ceiling
   300 MB.
2. `ghcr.io/mapanare-research/mapanare-runtime:5.19.1` and
   `:latest` — debian:bookworm-slim + libc6 + libgcc-s1 +
   `libmapanare_rt.so`. Target ≤80 MB; ceiling 100 MB.
3. `mnc init --docker <name>` scaffolds a multi-stage `Dockerfile`
   + `.dockerignore`. New overlay at `mapanare/templates/init/docker/`.
4. `.github/workflows/publish-docker.yml` — builds + pushes both
   images to GHCR on release tag. amd64 only.
5. `docs/guides/docker.md` — usage, multi-stage pattern, image
   sizes, opt-out, troubleshooting.
6. CI smoke job — builds hello-world via builder image, runs via
   runtime image, asserts output.
7. README "Quick start with Docker" section + GHCR badges.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Dk.1** | HIGH | `docker/builder/Dockerfile`: debian:bookworm-slim base + clang-18 + lld + LLVM 18 dev libs + the `mnc` binary + native runtime. Target: ~250 MB stripped. | 3–4h |
| **Dk.2** | HIGH | `docker/runtime/Dockerfile`: debian:bookworm-slim + just the C runtime shared lib + minimal libc. Target: ~80 MB. | 1–2h |
| **Dk.3** | HIGH | `mnc init --docker` flag: scaffold `Dockerfile` (multi-stage, builder→runtime) + `.dockerignore`. New overlay at `mapanare/templates/init/docker/`. | 2–3h |
| **Dk.4** | HIGH | `.github/workflows/publish-docker.yml`: build + push both images to GHCR on release tag. Multi-arch deferred (amd64-only in v5.19.1). | 3–4h |
| **Dk.5** | MEDIUM | `docs/guides/docker.md`: usage, sizes, multi-stage pattern, opt-out from-source build, troubleshooting. | 1–2h |
| **Dk.6** | MEDIUM | CI smoke: build hello-world Mapanare app via `mapanare-builder:5.19.1`, run resulting binary via `mapanare-runtime:5.19.1`, assert output. | 1–2h |
| **Dk.7** | LOW | README "Quick start with Docker" section + GHCR badges (build + version). | 0.5h |

---

## Phase plan

**Phase 0 — Verify locked design.** Re-read
`docs/roadmap/v5/v5.19.0/DOCKER_DESIGN.md`. The decisions there
(GHCR primary, amd64-only, debian:bookworm-slim, two independent
images, `:5.19.1` + `:latest` tags, image-size ceilings 300/100/90
MB) are committed. If a Phase exposes a need to revisit, write a
DESIGN_AMENDMENT.md rather than silently changing course.

**Phase 1 — Dk.1 builder image.** Write `docker/builder/Dockerfile`
matching the design. Stage build context: copy the v5.19.1 `mnc`
native binary + `runtime/native/libmapanare_rt.a` into
`docker/builder/build-context/` (or use a build arg pointing at a
release artifact location). Build locally:

```bash
docker build -t mapanare/builder:test docker/builder/
docker images mapanare/builder:test --format "{{.Size}}"
docker run --rm mapanare/builder:test --version
```

If the image exceeds 300 MB, audit before merging. Levers: drop
`llvm-18-dev` if not needed for `mnc build`; introduce internal
multi-stage build to copy only the binaries.

**Phase 2 — Dk.2 runtime image.** Write
`docker/runtime/Dockerfile`. The runtime needs `libmapanare_rt.so`
— verify `runtime/native/build_native.py` produces a clean
amd64-Linux `.so` first, or fall back to `gcc -shared` directly.

```bash
docker build -t mapanare/runtime:test docker/runtime/
docker images mapanare/runtime:test --format "{{.Size}}"
```

**Phase 3 — Dk.3 `mnc init --docker`.** Add `--docker` flag to
`cmd_init` in `mapanare/cli.py`. The existing `init_project()` in
`stdlib/pkg.py` takes a `template` parameter — extend to accept an
optional overlay (or list of overlays) so `--docker` overlays the
docker template on top of `default`. New overlay:

```
mapanare/templates/init/docker/
├── Dockerfile           # multi-stage builder→runtime
└── .dockerignore        # dist/, .cache/, *.ll, .git/, .gitignore, README.md
```

Dockerfile content (with `{{NAME}}` substitution):

```dockerfile
FROM ghcr.io/mapanare-research/mapanare-builder:5.19.1 AS build
COPY . /src
WORKDIR /src
RUN mnc build --release

FROM ghcr.io/mapanare-research/mapanare-runtime:5.19.1
COPY --from=build /src/dist/{{NAME}} /app/{{NAME}}
ENTRYPOINT ["/app/{{NAME}}"]
```

Tests: `tests/test_init.py` extended with cases for `--docker`.

**Phase 4 — Dk.4 publish workflow.** New
`.github/workflows/publish-docker.yml` triggered on release tag.
Steps: checkout, set up buildx, login to GHCR via `GITHUB_TOKEN`,
build builder image with cache-from/to GHA cache, push, build
runtime image, push.

Mid-Phase 4: push to a personal GHCR namespace
(`ghcr.io/<your-handle>/mapanare-builder:test`) to validate the
auth + push paths work end-to-end. Don't develop against `--load`
only.

**Phase 5 — Dk.5/Dk.6 docs + smoke.** `docs/guides/docker.md` +
new `docker-smoke` job in `.github/workflows/ci.yml` that builds a
hello-world app inside the builder image, runs it inside the runtime
image, asserts stdout.

**Phase 6 — Dk.7 closeout + README.** README "Quick start with
Docker" section, GHCR badges (build status + version), final
SESSION_REPORT, CHANGELOG, CLAUDE.md update marking Dk.* arc closed.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Builder image larger than 250 MB target | MEDIUM | Use multi-stage build inside the Dockerfile if needed. Strip debug symbols from clang/lld. Confirm in Phase 1 with `docker images`. Hard ceiling 300 MB. |
| Runtime image larger than 80 MB | LOW | debian:bookworm-slim is ~30 MB; libc6 + libgcc adds ~20 MB; runtime lib is small. Should comfortably fit. |
| GHCR rate limits or auth issues in CI | LOW | Use `GITHUB_TOKEN` with `packages: write` permission. Document in publish workflow. Validate against personal namespace mid-Phase 4. |
| `runtime/native/build_native.py` doesn't produce a clean amd64-Linux `.so` | MEDIUM | Investigate in Phase 2; fall back to direct `gcc -shared` if cffi-based build is fragile. |
| Multi-stage Dockerfile in template doesn't work for non-trivial projects | MEDIUM | Template is for `mnc init` newbies; document the limits in `docs/guides/docker.md`. Real apps will customize. |
| Docker images break on glibc-incompatible environments | LOW | We don't have C extensions; this is a pure runtime concern. Document Alpine incompatibility prominently. |
| `mnc` native binary (~123 MB) bloats the builder image | MEDIUM | `mnc-stage1` is the self-hosted compiler; alternate path is to ship the Python `mapanare` CLI inside the image and skip the native binary. Decision deferred to Phase 1. Document in DESIGN_AMENDMENT if we go this way. |
| Image-name collision with Docker Hub `mapanare/*` | LOW | We publish to GHCR (`ghcr.io/mapanare-research/*`), not Docker Hub. Docker Hub mirror is a separate decision. |

---

## Out of scope (deferred)

- ARM64 / multi-arch images → v5.20.0+
- Alpine variant → not happening (glibc/musl mismatch)
- Windows containers → far future
- Kubernetes operator / Helm chart → separate ecosystem repo
- Distroless final image (`FROM scratch` + statically-linked
  binary) → v5.20.0+ once we have static linking story
- Docker Hub mirror → patch release if GHCR usage shows demand
- Auto-publish on every commit to dev → release tags only
- CUDA / Vulkan support inside the builder image → too specific
  for v1; users can build their own derived image

---

## Success criteria

- `mapanare-builder:5.19.1` published to GHCR, ≤300 MB
- `mapanare-runtime:5.19.1` published to GHCR, ≤100 MB
- `mnc init demo --docker` produces a buildable Dockerfile
- Multi-stage build of hello-world produces final image ≤90 MB
- CI smoke runs an app inside the runtime image, asserts output
- Goldens 80/80 (unaffected — Docker work is packaging, not compiler)
- Strict 3-stage fixed point preserved (unaffected)
- `make lint` clean
- `docs/guides/docker.md` complete with examples and image sizes
- README has "Quick start with Docker" section + GHCR badges
