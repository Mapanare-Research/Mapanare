# `mapanare-runtime` Docker image

Minimal base for running Mapanare-compiled native binaries.

## Local build

The build context expects one staged file:

```
docker/runtime/build-context/
└── libmapanare_rt.so   # shared C runtime (runtime/native/libmapanare_runtime.so)
```

Stage from in-tree artifacts:

```bash
mkdir -p docker/runtime/build-context
cp runtime/native/libmapanare_runtime.so \
   docker/runtime/build-context/libmapanare_rt.so

docker build -t mapanare-runtime:dev docker/runtime/build-context \
    --file docker/runtime/Dockerfile

docker images mapanare-runtime:dev --format "{{.Size}}"
```

Statically-linked binaries (the default from `mnc build`) do not
depend on `libmapanare_rt.so`; it ships for opt-in `--shared` builds
in a later release.

## CI / release

The `.github/workflows/publish-docker.yml` workflow stages and builds
this image on every release tag, then pushes to
`ghcr.io/mapanare-research/mapanare-runtime`.

See `docs/guides/docker.md` for end-user documentation.
