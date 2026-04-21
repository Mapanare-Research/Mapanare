#!/usr/bin/env bash
# v4.105.0 Phase 3: build mnc-stage1-tsan.
# TSan at -O1 on IR, C runtime, main wrapper.
set -euo pipefail
ROOT=${MAPANARE_ROOT:-$(pwd)}
BUILD=/tmp/tsan_build
mkdir -p $BUILD

VERSION=$(cat $ROOT/VERSION)

TSAN_CFLAGS=(-O1 -g -fPIC -fsanitize=thread -fno-omit-frame-pointer
             -Wall -Wno-unused-function
             -I "$ROOT/runtime/native"
             "-DMAPANARE_VERSION=\"$VERSION\"")

echo "=== [1/4] Compile IR with TSan → main.o ==="
clang -c -O1 -fsanitize=thread -fno-omit-frame-pointer \
    "$ROOT/mapanare/self/main.ll" -o "$BUILD/main.o" 2>&1 | grep -v "overriding" || true

echo "=== [2/4] Compile C runtime with TSan ==="
for src in mapanare_core.c mapanare_io.c mapanare_runtime.c mapanare_gpu.c mapanare_gpu_builtins.c mapanare_db.c mapanare_html.c; do
  obj=${src%.c}.o
  clang -c "${TSAN_CFLAGS[@]}" "$ROOT/runtime/native/$src" -o "$BUILD/$obj"
done

echo "=== [3/4] Compile main wrapper with TSan ==="
clang -c "${TSAN_CFLAGS[@]}" "$ROOT/mapanare/self/mnc_main.c" -o "$BUILD/mnc_main.o"

echo "=== [4/4] Link mnc-stage1-tsan ==="
BIN="$ROOT/mapanare/self/mnc-stage1-tsan"
rm -f "$BIN"
clang -fsanitize=thread -fno-omit-frame-pointer \
  -o "$BIN" \
  "$BUILD/mnc_main.o" "$BUILD/main.o" \
  "$BUILD/mapanare_core.o" "$BUILD/mapanare_io.o" "$BUILD/mapanare_runtime.o" \
  "$BUILD/mapanare_gpu.o" "$BUILD/mapanare_gpu_builtins.o" "$BUILD/mapanare_db.o" "$BUILD/mapanare_html.o" \
  -no-pie -rdynamic -lm -lpthread -ldl

echo "  Binary: $BIN ($(stat -c %s $BIN) bytes)"
ls -la "$BIN"
