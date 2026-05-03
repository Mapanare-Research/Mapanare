#!/bin/sh
# mnc wrapper for the mapanare-builder Docker image.
#
# `mnc build` and `mnc run` shell out to gcc with the literal path
# `runtime/native/libmapanare_rt.a` (resolved against CWD). This wrapper
# stages a symlink to the image's prebuilt /usr/local/lib/libmapanare_rt.a
# so the linker call resolves cleanly when users mount their source at
# /src and don't ship a runtime archive of their own.
set -e

RT_REL="runtime/native/libmapanare_rt.a"
if [ ! -e "$RT_REL" ]; then
    mkdir -p runtime/native 2>/dev/null || true
    ln -sf /usr/local/lib/libmapanare_rt.a "$RT_REL" 2>/dev/null || true
fi

exec /usr/local/bin/mnc-real "$@"
