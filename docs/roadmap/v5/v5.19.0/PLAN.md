# v5.19.0 — Te.3 + Dk.* — deprecate `{}` + Docker images

**Status:** PLANNING
**Breaking:** Soft-breaking. `{}` syntax still parses but emits a
deprecation warning. Hard removal scheduled for v6.0.
**Prerequisite:** v5.18.0 shipped (LSP + init + check). Self-hosted
compiler in terse syntax (v5.17.0). `mnc fmt --to-terse` available
(v5.14.0).
**Estimated effort:** 14–22h, two sessions. Te.3 is small; Dk.* is
the bulk.

---

## Why this exists

This release is the closeout of the terse-syntax arc and the entry
point for production deployment.

**Te.3** — formally deprecate brace syntax. The self-hosted
compiler is already terse (v5.17.0), all examples and docs are
terse (v5.17.0/v5.18.0). The only `{}`-style code left in the wild
is downstream user code. Deprecation warning + automatic fmt
migration gives users a clean path forward.

**Dk.*** — Docker images. Mapanare's "compile native binaries"
pitch is undermined by the toolchain install burden. A
`docker run -v $(pwd):/src mapanare/builder:5.18.0 build` reduces
"try Mapanare" from "install LLVM + clang + lld + Mapanare" to a
single command. Multi-stage Dockerfiles let users ship apps as
~85 MB final images — closer to Go than Python.

These ship together because they're both "polish for newcomers"
work and they're small enough on their own to feel like patch
releases. Together they make a credible v5.19.0.

---

## Goal

1. Brace-style blocks emit a deprecation warning at parse time.
   Default: warning to stderr per file with `{}` syntax. Suppress
   with `MAPANARE_NO_BRACE_WARNING=1`.
2. `mnc fmt` with no flags becomes equivalent to
   `mnc fmt --to-terse` for `.mn` files containing `{}` blocks
   (auto-migration on next format).
3. Pre-built Docker images published to a public registry on
   release tag:
   - `mapanare/builder:5.18.0` and `:latest`
   - `mapanare/runtime:5.18.0` and `:latest`
4. `mnc init --docker` scaffolds a multi-stage `Dockerfile` and
   `.dockerignore` in a new project.
5. Docs at `docs/guides/docker.md` covering: builder image usage,
   multi-stage app pattern, image sizes, FROM scratch caveats.
6. CI workflow `publish-docker.yml` that builds + pushes images on
   release tag.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.3.A** | MEDIUM | Parser emits `BraceBlockDeprecation` warning when `{}` blocks parsed. Once per file, not once per block. | 1h |
| **Te.3.B** | MEDIUM | `mnc fmt` (no flag) auto-converts `{}` → `:` if any `{}` blocks present. Document in `docs/guides/formatter.md`. | 1h |
| **Te.3.C** | LOW | `MAPANARE_NO_BRACE_WARNING=1` env var suppresses the warning (for downstream CI). Document in CHANGELOG migration notes. | 0.5h |
| **Te.3.D** | LOW | Docs sweep: any remaining `{}` in `docs/`, `examples/`, `README.md` updated to terse style. Should be ~zero work after v5.17.0 + v5.18.0. | 0.5h |
| **Dk.1** | HIGH | `docker/builder/Dockerfile`: debian:bookworm-slim base + clang-18 + lld + LLVM 18 dev libs + the `mnc` binary + native runtime. Target: ~250 MB stripped. | 3–4h |
| **Dk.2** | HIGH | `docker/runtime/Dockerfile`: debian:bookworm-slim + just the C runtime shared lib + minimal libc. Target: ~80 MB. | 1–2h |
| **Dk.3** | HIGH | `mnc init --docker` flag: scaffold `Dockerfile` (multi-stage, builder→runtime) + `.dockerignore`. New template at `templates/init/docker/`. | 2–3h |
| **Dk.4** | HIGH | `.github/workflows/publish-docker.yml`: build + push both images to GHCR on release tag. Multi-arch deferred (amd64-only in v5.19.0). | 3–4h |
| **Dk.5** | MEDIUM | `docs/guides/docker.md`: usage, sizes, multi-stage pattern, opt-out from-source build, troubleshooting. | 1–2h |
| **Dk.6** | MEDIUM | CI smoke: build hello-world Mapanare app via `mapanare/builder:5.18.0`, run resulting binary via `mapanare/runtime:5.18.0`, assert output. | 1–2h |

---

## Phase plan

**Phase 0 — Image hosting decision.** Write `DOCKER_DESIGN.md`:

- Registry: GHCR (`ghcr.io/mapanare-research/...`) vs Docker Hub
  (`mapanare/...`)? **Recommendation:** GHCR primary (free for
  public repos, integrates with GH Actions); Docker Hub mirror as
  follow-up if there's user demand.
- Architectures: amd64 only in v5.19.0; arm64 in v5.20.0+ once we
  have ARM CI capacity.
- Base image: `debian:bookworm-slim` (~30 MB) over `alpine` (musl
  vs glibc mismatch with the existing C runtime).
- Image naming: `mapanare/builder` + `mapanare/runtime` (two
  images, multi-stage friendly).

**Phase 1 — Te.3.A/B/C/D.** Smallest piece. Single commit per
sub-item. Validate: existing `{}` code parses with warning;
existing tests still pass; `mnc fmt` auto-migrates.

**Phase 2 — Dk.1 builder image.**

```dockerfile
# docker/builder/Dockerfile
FROM debian:bookworm-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang-18 lld-18 llvm-18-dev libc6-dev make ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 100 \
    && update-alternatives --install /usr/bin/lld lld /usr/bin/lld-18 100

COPY mnc /usr/local/bin/mnc
COPY runtime/native/libmapanare_rt.a /usr/local/lib/

WORKDIR /src
ENTRYPOINT ["mnc"]
```

Test locally: `docker build -t mapanare/builder:test docker/builder/`.

**Phase 3 — Dk.2 runtime image.**

```dockerfile
# docker/runtime/Dockerfile
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6 libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*
COPY runtime/native/libmapanare_rt.so /usr/local/lib/
RUN ldconfig
WORKDIR /app
```

**Phase 4 — Dk.3 `mnc init --docker`.** Add `--docker` flag to
`cmd_init`. New template at `templates/init/docker/`:

```
templates/init/docker/
├── Dockerfile           # multi-stage builder→runtime
└── .dockerignore        # dist/, .cache/, *.ll, .git/
```

Dockerfile content:

```dockerfile
FROM mapanare/builder:5.18.0 AS build
COPY . /src
RUN mnc build --release

FROM mapanare/runtime:5.18.0
COPY --from=build /src/dist/{{NAME}} /app/{{NAME}}
ENTRYPOINT ["/app/{{NAME}}"]
```

**Phase 5 — Dk.4 publish workflow.** New
`.github/workflows/publish-docker.yml` triggered on release tag.
Steps: checkout, set up buildx, login to GHCR, build builder
image with cache, push, build runtime image with cache, push.

**Phase 6 — Dk.5/Dk.6 docs + smoke.** Docker guide + CI smoke job.

**Phase 7 — Closeout.** SESSION_REPORT, CHANGELOG, README badges,
CLAUDE.md update marking Te.* and Dk.* arcs closed.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Builder image larger than 250 MB target | MEDIUM | Use multi-stage build inside the Dockerfile if needed. Strip debug symbols from clang/lld. Confirm in Phase 2 with `docker images mapanare/builder:test --format "{{.Size}}"`. |
| Runtime image larger than 80 MB | LOW | debian:bookworm-slim is ~30 MB; libc6 + libgcc adds ~20 MB; runtime lib is small. Should comfortably fit. |
| GHCR rate limits or auth issues in CI | LOW | Use `GITHUB_TOKEN` with `packages: write` permission. Document in publish workflow. |
| Multi-stage Dockerfile in template doesn't work for non-trivial projects | MEDIUM | Template is for `mnc init` newbies; document the limits in `docs/guides/docker.md`. Real apps will customize. |
| Te.3 brace warning floods CI logs for projects mid-migration | MEDIUM | `MAPANARE_NO_BRACE_WARNING=1` env var. Documented prominently in CHANGELOG migration notes. |
| Auto-fmt `{}`→`:` on save surprises users running `mnc fmt --check` | MEDIUM | `mnc fmt --check` exits 1 if `{}` blocks present (because it would change them). Documented as the migration prompt. |
| Docker images break on glibc-incompatible C extensions | LOW | We don't have C extensions; this is a pure runtime concern. Document Alpine incompatibility. |

---

## Out of scope (deferred)

- ARM64 / multi-arch images → v5.20.0+
- Alpine variant → not happening (glibc/musl mismatch)
- Windows containers → far future
- Kubernetes operator / Helm chart → separate ecosystem repo
- Distroless final image (`FROM scratch` + statically-linked
  binary) → v5.20.0+ once we have static linking story
- Hard removal of `{}` syntax → **v6.0** (alongside borrow checker)
- Docker Hub mirror → patch release if GHCR usage shows demand
- Auto-publish on every commit to dev → tags only

---

## Success criteria

- `{}`-style code parses with one deprecation warning per file
- `mnc fmt` auto-converts `{}`→`:`
- `mnc fmt --check` flags `{}` files as needing migration
- `mapanare/builder:5.18.0` published to GHCR, ~250 MB
- `mapanare/runtime:5.18.0` published to GHCR, ~80 MB
- `mnc init demo --docker` produces a buildable Dockerfile
- Multi-stage build of hello-world produces final image ≤90 MB
- CI smoke runs an app inside the runtime image
- Goldens 66/66
- Strict 3-stage fixed point preserved
- `make lint` clean
- Docs: `docs/guides/docker.md` complete with examples and image
  sizes
- The Mapanare README has a "Quick start with Docker" section
