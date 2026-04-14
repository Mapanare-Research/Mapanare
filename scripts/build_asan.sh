#!/usr/bin/env bash
# v4.105.0 Phase 2: build mnc-stage1-asan.
# Uses the existing main.ll produced by scripts/build_stage1.py.
# Instruments the compiled IR, the C runtime, and the main wrapper with ASan at -O1.
set -euo pipefail
ROOT=${MAPANARE_ROOT:-$(pwd)}
BUILD=/tmp/asan_build
mkdir -p $BUILD

VERSION=$(cat $ROOT/VERSION)

ASAN_CFLAGS=(-O1 -g -fPIC -fsanitize=address -fno-omit-frame-pointer
             -Wall -Wno-unused-function
             -I "$ROOT/runtime/native"
             "-DMAPANARE_VERSION=\"$VERSION\"")

echo "=== [1/4] Compile IR with ASan → main.o ==="
clang -c -O1 -fsanitize=address -fno-omit-frame-pointer \
    "$ROOT/mapanare/self/main.ll" -o "$BUILD/main.o" 2>&1 | grep -v "overriding" || true

echo "=== [2/4] Compile C runtime with ASan ==="
for src in mapanare_core.c mapanare_io.c mapanare_runtime.c mapanare_gpu.c mapanare_gpu_builtins.c mapanare_db.c mapanare_html.c; do
  obj=${src%.c}.o
  clang -c "${ASAN_CFLAGS[@]}" "$ROOT/runtime/native/$src" -o "$BUILD/$obj"
done

echo "=== [3/4] Compile main wrapper with ASan ==="
clang -c "${ASAN_CFLAGS[@]}" "$ROOT/mapanare/self/mnc_main.c" -o "$BUILD/mnc_main.o"

echo "=== [4/4] Link mnc-stage1-asan ==="
BIN="$ROOT/mapanare/self/mnc-stage1-asan"
rm -f "$BIN"
clang -fsanitize=address -fno-omit-frame-pointer \
  -o "$BIN" \
  "$BUILD/mnc_main.o" "$BUILD/main.o" \
  "$BUILD/mapanare_core.o" "$BUILD/mapanare_io.o" "$BUILD/mapanare_runtime.o" \
  "$BUILD/mapanare_gpu.o" "$BUILD/mapanare_gpu_builtins.o" "$BUILD/mapanare_db.o" "$BUILD/mapanare_html.o" \
  -no-pie -rdynamic -lm -lpthread -ldl

echo "  Binary: $BIN ($(stat -c %s $BIN) bytes)"
ls -la "$BIN"
