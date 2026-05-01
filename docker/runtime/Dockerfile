# mapanare-runtime — minimal base image for running Mapanare-compiled
# native binaries.
#
# Mapanare programs built by `mnc build` statically link
# libmapanare_rt.a, so the only runtime requirements are glibc and
# libgcc_s — both already shipped in `debian:bookworm-slim`. The
# bundled libmapanare_rt.so is included for future dynamic-link use
# cases (e.g. opt-in `mnc build --shared`); statically-linked binaries
# do not depend on it.
#
# Target size: ≤80 MB. Hard ceiling: 100 MB.

FROM debian:bookworm-slim

# `debian:bookworm-slim` already ships libc6 + libgcc-s1. We add
# nothing else by default to keep the image as small as possible.
# Apps that need TLS, OpenSSL, or other dynamic libs at runtime
# should base off this image and `apt-get install` what they need.

COPY libmapanare_rt.so /usr/local/lib/
RUN ldconfig

WORKDIR /app
