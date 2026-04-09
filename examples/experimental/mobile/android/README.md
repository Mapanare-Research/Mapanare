# Mapanare Android Example

Minimal Android app embedding a Mapanare-compiled shared library via JNI.

## Prerequisites

- Android NDK r26+ (API 34)
- `aarch64-linux-android34-clang` on PATH (from NDK toolchain)

## Build the shared library

```bash
mapanare build --target aarch64-linux-android --lib -o libmapanare_app.so app.mn
```

For x86_64 emulator:

```bash
mapanare build --target x86_64-linux-android --lib -o libmapanare_app.so app.mn
```

## Integrate with Android Studio

1. Copy `libmapanare_app.so` to `app/src/main/jniLibs/arm64-v8a/`
2. Add `MainActivity.kt` to your project
3. Build and run

## Architecture

The Mapanare compiler emits LLVM IR with the Android target triple, compiles to
a native `.o`, and links with the NDK clang to produce a `.so` that Android
loads via `System.loadLibrary()`.

Mapanare agents run as OS threads via the C runtime, making them suitable for
background tasks on Android (similar to `WorkManager` or coroutine dispatchers).
