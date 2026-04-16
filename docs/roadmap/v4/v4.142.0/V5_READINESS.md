# Mapanare v5 Readiness — Updated for v4.143.0 Panel

> Written at v4.142.0 (2026-04-16) as informational input for the
> v4.143.0 panel. This refresh carries the v4.135.0 readiness snapshot
> forward through the v4.137.0–v4.142.0 post-rc1 arc.

## Headline

**7 of 8** items from the v4.119.0 "would embarrass v5" list are now
closed. The single remaining open item is the package manager, which is
explicitly ecosystem scope rather than a v5.0.0 correctness gate.

The new closure in this release is the last valgrind memory-safety
bucket:

- **Valgrind ERRORS:** `5 -> 0`
- **Ge.1:** CLOSED

## Status matrix

| # | Item | v4.119.0 | **v4.142.0** |
|---|---|---|---|
| 1 | Package manager | OPEN | **OPEN** (v5.x ecosystem scope) |
| 2 | Fixed-point proof | OPEN | **CLOSED** (v4.134.0) |
| 3 | Sh.2 memory safety | OPEN | **CLOSED** (v4.131.0 / v4.132.0) |
| 4 | CI / testing hygiene | OPEN | **CLOSED** (v4.133.0) |
| 5 | `make lint` clean | OPEN | **CLOSED** (v4.141.0) |
| 6 | SPEC current | OPEN | **CLOSED** (v4.129.0 / v4.139.0) |
| 7 | Valgrind ERRORS | OPEN | **CLOSED** (v4.142.0, `5 -> 0`) |
| 8 | ASan ASAN_ERROR | OPEN | **CLOSED** (v4.132.0) |

## Why item 7 is now closed

At v4.135.0, the only residual valgrind ERRORS were the five Ge.1
generic-monomorphization cases:

- `26_generics`
- `29_generic_impl`
- `30_nested_generics`
- `31_generic_multi`
- `32_generic_enum`

At v4.142.0:

- all five targeted tests are valgrind-clean
- the full sweep lands at **0 ERRORS**
- the residual `32_generic_enum` path was traced to moved enum metadata
  being freed too early in the self-hosted lowerer and is now fixed

## Current remaining v5-visible gap

### Package manager

Still open, still ecosystem scope, still explicitly **not** a v5.0.0
correctness blocker. The compiler/runtime/tooling evidence base is now
stronger than the ecosystem story; that trade remains honest and named.

## Net stance

The v4.137.0–v4.142.0 bridge releases systematically emptied the
v4.136.0 carry-forward:

- Ch.1 CLOSED (v4.137.0)
- Bo.* CLOSED (v4.138.0)
- Gr.2 / Sem.1 / Dr.1 CLOSED (v4.139.0)
- Cb.5 / SE.1 / Cb.3 CLOSED (v4.140.0)
- An.2 CLOSED (v4.141.0)
- Ge.1 CLOSED (v4.142.0)

That leaves the readiness picture materially cleaner than the
v4.136.0 rc1 gate: the panel is no longer being asked to carry any
named memory-safety or documentation debt forward into the clean v5
decision.
