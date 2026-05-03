# `mapanare-builder` Docker image

Builds Mapanare `.mn` sources to native ELF binaries.

## Local build

The build context expects two staged files:

```
docker/builder/build-context/
├── mnc                  # native amd64 mnc binary (e.g. mapanare/self/mnc-stage1)
└── libmapanare_rt.a     # static C runtime archive (runtime/native/libmapanare_rt.a)
```

Stage from in-tree artifacts:

```bash
mkdir -p docker/builder/build-context
cp mapanare/self/mnc-stage1     docker/builder/build-context/mnc
cp runtime/native/libmapanare_rt.a docker/builder/build-context/

docker build -t mapanare-builder:dev docker/builder/build-context \
    --file docker/builder/Dockerfile

docker images mapanare-builder:dev --format "{{.Size}}"
```

## CI / release

The `.github/workflows/publish-docker.yml` workflow stages and builds
this image on every release tag, then pushes to
`ghcr.io/mapanare-research/mapanare-builder`.

See `docs/guides/docker.md` for end-user documentation.
