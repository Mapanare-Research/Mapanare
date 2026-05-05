# LEGACY — mn_http

This example does **not compile** on `mnc` v0.7.0+ because it uses
`extern "Python" fn`, which was removed at v4.29.0. The example was
authored against the v0.x Python-interop bridge.

## Don't model new packages on this

Two structural reasons:

1. **`extern "Python"` is gone.** Use `mapanare bind --lang python` to
   generate Python bindings if you need Python interop today.
2. **HTTP is runtime-bound.** Real HTTP support lives in
   `stdlib/net/http.mn` and uses `extern "C"` against `__mn_tcp_*`
   runtime symbols. It cannot move out of the bundled stdlib until
   packages can declare native-ABI dependencies (see
   `docs/guides/stdlib-packaging.md` for the policy and
   `docs/roadmap/v5/v5.44.0/PLAN.md` for the v6.0+ deferral).

## What to model new packages on instead

See `examples/packages/mn_collections/` (the pure-`.mn` reference) and
`examples/packages/consumer_collections/` (the package-aware consumer
demo).

## Why this dir still exists

The package metadata + the broken source have value as a frozen
record of the v0.x Python-interop shape. They show what **not** to do
and what failure mode to expect when porting old packages forward.
