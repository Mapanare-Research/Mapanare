# Multi-stage build using the official Mapanare images.
#
# Stage 1 — `mapanare-builder` provides clang, lld, the `mnc` compiler,
# and the static C runtime archive. We compile the project to a single
# native executable inside this stage.
#
# Stage 2 — `mapanare-runtime` is a minimal glibc base. We copy only
# the produced binary into it. Final image typically lands under 90 MB.
#
# See https://mapanare.dev/docs/docker for usage and tuning.

FROM ghcr.io/mapanare-research/mapanare-builder:5.19.1 AS build
COPY . /src
WORKDIR /src
RUN mkdir -p dist && mnc build main.mn --release -o dist/{{NAME}}

FROM ghcr.io/mapanare-research/mapanare-runtime:5.19.1
COPY --from=build /src/dist/{{NAME}} /app/{{NAME}}
ENTRYPOINT ["/app/{{NAME}}"]
