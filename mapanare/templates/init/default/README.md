# {{NAME}}

A Mapanare project.

## Build & run

```bash
mapanare run main.mn   # Python bootstrap (slower, no native toolchain needed)
mnc run main.mn        # native (faster)
```

## Type-check

```bash
mapanare check main.mn
```

## Test

Add `@test` functions and run:

```bash
mapanare test .
```

## Layout

- `main.mn` — entry point.
- `mapanare.toml` — package manifest.
