# Docker

> **Available since v5.19.1.**

Mapanare publishes two official Docker images on every release. They
let you compile and run Mapanare programs without installing LLVM,
clang, or the `mnc` toolchain on your host.

| Image | Purpose | Approx. size |
|---|---|---:|
| `ghcr.io/mapanare-research/mapanare-builder:5.19.1` | Compiles `.mn` to a native ELF binary | ~640 MB |
| `ghcr.io/mapanare-research/mapanare-runtime:5.19.1` | Minimal glibc base for running compiled binaries | ~115 MB |

Both images are linux/amd64 only in v5.19.1. ARM64 ships in v5.20.0+.

> **Image-size note.** The builder image is larger than the original
> 300 MB target documented in `DOCKER_DESIGN.md`. The amendment at
> `docs/roadmap/v5/v5.19.1/DESIGN_AMENDMENT.md` records why: libLLVM-18
> + libclang-cpp + transitive deps are non-removable while `mnc build`
> shells out to `clang`. A v5.20.0+ "builder-image diet" follow-up
> tracks the path to ~450 MB.

---

## Quick start — `mnc init --docker`

```bash
mnc init demo --docker
cd demo
docker build -t demo .
docker run --rm demo
```

`mnc init --docker` adds a multi-stage `Dockerfile` and a
`.dockerignore` to the standard project scaffold. The Dockerfile uses
`mapanare-builder` for the build stage and `mapanare-runtime` for the
final image, which typically lands under 90 MB.

---

## Compile without installing Mapanare

If you have `.mn` source on the host but no Mapanare toolchain, mount
the source into the builder image and run `mnc` directly:

```bash
docker run --rm -v "$(pwd):/src" \
    ghcr.io/mapanare-research/mapanare-builder:5.19.1 \
    build main.mn -o /src/myapp
```

The image's `mnc` entrypoint forwards every argument to the native
binary. The output `myapp` lands in your host directory.

> **Heads-up:** the wrapper inside the image creates a
> `runtime/native/libmapanare_rt.a` symlink in the mounted directory
> if one does not already exist. This is required because `mnc build`
> resolves the runtime archive path relative to its CWD. A future
> release will replace this with an env-var override.

---

## Multi-stage pattern

The recommended way to ship a Mapanare app:

```dockerfile
# build stage — `mapanare-builder` has clang, lld, and `mnc`
FROM ghcr.io/mapanare-research/mapanare-builder:5.19.1 AS build
COPY . /src
WORKDIR /src
RUN mnc build --release main.mn -o /src/dist/myapp

# final stage — `mapanare-runtime` is just glibc + libgcc_s
FROM ghcr.io/mapanare-research/mapanare-runtime:5.19.1
COPY --from=build /src/dist/myapp /app/myapp
ENTRYPOINT ["/app/myapp"]
```

`mnc init --docker` writes exactly this template to your project.

`mnc build --release` enables `-O2` and strips debug symbols from the
final binary.

---

## Image tags

| Tag | Meaning | Mutable? |
|---|---|---|
| `:5.19.1` | This release exactly | No |
| `:latest` | Current stable release | Yes |

Pin to `:5.19.1` for reproducible builds. There is no moving `:5` tag
during the v5.x pre-1.0 series.

---

## Opt-out: build without the bundled images

If you'd rather use a host clang and a host runtime, build from
source and skip Docker entirely:

```bash
git clone https://github.com/mapanare-research/Mapanare.git
cd Mapanare
bash scripts/build_from_seed.sh
mnc build main.mn -o myapp
```

---

## Troubleshooting

### `error while loading shared libraries: libc.so.6` inside an Alpine container

The runtime is glibc-built. Alpine ships musl libc, which is not
ABI-compatible. Use `mapanare-runtime:5.19.1` (debian-based) or any
glibc Linux distribution as your base. There is no Alpine variant and
no plan to ship one.

### `clang: not found` when running `mnc build` on a host machine

The bundled `mapanare-builder` image already includes clang and lld.
If you're outside the image and getting this error, `apt install
clang` (Linux) or `brew install llvm` (macOS) — see
`docs/guides/getting_started.md`.

### Image is too big

That's the cost of bundling the LLVM toolchain. For a smaller
**deployable** image, use the multi-stage pattern above — the final
image (the one users pull) is `mapanare-runtime` plus your binary,
typically under 90 MB. Only the **build** image carries clang/lld.

### `runtime/native/libmapanare_rt.a` appears in my source tree after running the builder

The wrapper inside `mapanare-builder` creates that symlink in the
mounted directory so `mnc build`'s linker step resolves the runtime
archive. Add `runtime/` to your `.gitignore` if you don't want it
tracked. Removing the symlink between runs is safe; the wrapper
re-creates it on demand.

### How do I run the smoke test myself?

```bash
mkdir /tmp/mn-smoke && cd /tmp/mn-smoke
cat > main.mn <<'EOF'
fn main():
    print("hello")
EOF
cat > Dockerfile <<'EOF'
FROM ghcr.io/mapanare-research/mapanare-builder:5.19.1 AS build
COPY . /src
WORKDIR /src
RUN mnc build main.mn -o /src/hello

FROM ghcr.io/mapanare-research/mapanare-runtime:5.19.1
COPY --from=build /src/hello /app/hello
ENTRYPOINT ["/app/hello"]
EOF
docker build -t mn-smoke .
docker run --rm mn-smoke
```

Expected output: `hello`. Final image size: ~85 MB.

---

## Source

- `docker/builder/Dockerfile` — builder image
- `docker/runtime/Dockerfile` — runtime image
- `mapanare/templates/init/docker/` — `mnc init --docker` overlay
- `.github/workflows/publish-docker.yml` — release-time publish
