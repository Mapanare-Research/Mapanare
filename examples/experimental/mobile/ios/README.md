# Mapanare iOS Example

Minimal iOS app embedding a Mapanare-compiled static library via C FFI.

## Prerequisites

- Xcode 15.0+
- macOS with Apple Silicon (or Rosetta)

## Build the static library

```bash
mapanare build --target aarch64-apple-ios --lib -o libmapanare_app.a app.mn
```

## Integrate with Xcode

1. Create a new iOS project in Xcode
2. Add `libmapanare_app.a` to the project (drag into Frameworks)
3. Add `mapanare_app-Bridging-Header.h` and set it in Build Settings > Objective-C Bridging Header
4. Use the Swift wrapper from `ViewController.swift`

## Architecture

The Mapanare compiler emits LLVM IR with the `aarch64-apple-ios17.0` target
triple, compiles to a native `.o`, and links via `libtool -static` to produce a
`.a` that Xcode embeds in the app bundle.

Mapanare agents map to OS threads via the C runtime with mobile-tuned defaults
(smaller arena, smaller ring buffers, cooperative scheduling).
