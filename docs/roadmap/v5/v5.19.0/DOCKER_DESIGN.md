# v5.19.0 — Docker design lock + Te.3 detection architecture

**Status:** Locked 2026-04-30 (Phase 0 of v5.19.0).

This document records the decisions made during Phase 0 of v5.19.0
before any image or code work begins. All later phases reference
these decisions.

---

## Te.3 — brace-block detection architecture

### The problem

The PROMPT.md sketch suggests hooking the Lark transformer:

```python
class MapanareTransformer:
    def brace_block(self, items):
        self._brace_block_count += 1
        return Block(...)
```

This does **not** work. The parser pipeline is:

1. Source text
2. `_indent_to_braces(source)` — converts every `body:` into
   `body {`, inserts matching `}` at dedent. Fast path: if no
   line ends with `:`, returns source unchanged.
3. Lark parses the (now 100% brace-form) source.
4. `MapanareTransformer` walks the tree.

By step 4, every block is a brace block — including blocks that
the user wrote with colon syntax. A transformer hook would fire on
those too, false-positive-flagging files that contain zero
user-written braces.

### Decision: detect on the original source, before preprocessing

Add a function in `parser.py` that scans the source pre-preprocess
and counts user-written brace-block openers. Call it from `parse()`
and `parse_recovering()` before `_indent_to_braces`.

Detection rule (line-based, deliberately conservative):

A line is a "user brace-block opener" if, after stripping
trailing line comments and trailing whitespace:

- the line ends with `{`, AND
- the line does NOT end with `#{` (map literal), AND
- the line is not entirely inside a triple-quoted string (we
  approximate by tracking `"""` toggle — Mapanare doesn't have
  triple-quoted literals as of v5.19.0, so this is reserved
  capability), AND
- the line does not start with `#` or `//` (comment line)

False positives are limited to the rare case of a multi-line
struct literal opener like:

```
let p = Point {
    x: 1,
    y: 2
}
```

Such literals do exist but are vanishingly rare in canonical
Mapanare style (struct literals usually fit on one line or use
`Foo { x, y }` shorthand which doesn't end with `{`). The cost of
a false positive is one stderr warning line, which is bounded.

### Warning policy

- One warning per file (not per occurrence).
- Stderr only. Does not affect parse result, exit code, or the
  produced AST.
- Suppressed by env var `MAPANARE_NO_BRACE_WARNING=1`.
- Stable wording so downstream CI can grep for it:
  `warning: <path>: uses deprecated {}-block syntax (N occurrence(s)). Run \`mnc fmt <path>\` to migrate. Hard removal in v6.0.`

### `mnc fmt` default behavior

Pre-v5.19.0 default: whitespace-only canonicalization
(`format_source`).

v5.19.0 default: detect user-written braces in the source. If
present, default behavior becomes `to_terse` + `format_source`
(equivalent to today's `--to-terse` flag). Otherwise, behavior is
unchanged.

Rationale: a user running `mnc fmt myfile.mn` after seeing the
deprecation warning expects the file to be migrated. Forcing them
to remember `--to-terse` is friction.

Opt-out: new flag `--keep-braces` runs `format_source` only
(legacy behavior). Useful for downstream projects mid-migration
that want canonical whitespace without surface rewriting.

`--check` becomes:

- if any file would be rewritten (whitespace changes OR
  brace→colon conversion needed): exit 1.
- otherwise: exit 0.

This is the migration prompt: a CI job that ran `mnc fmt --check`
and previously passed will now fail on any file with `{}` blocks,
forcing the maintainer to either add `--keep-braces` or run `mnc
fmt`.

---

## Dk.* — image hosting + tagging

### Registry: GHCR primary

`ghcr.io/mapanare-research/mapanare-builder` and
`ghcr.io/mapanare-research/mapanare-runtime`. Public visibility.

Rationale: the project's GitHub org is `mapanare-research`; GHCR
is free for public repos; integration with the existing
`publish.yml` workflow uses `GITHUB_TOKEN` natively (no third-
party secret needed).

Docker Hub mirror at `mapanare/builder` and `mapanare/runtime`
deferred to a patch release if user demand emerges.

### Architectures

linux/amd64 only in v5.19.0. arm64 deferred to v5.20.0+ once we
have ARM CI capacity (GitHub-hosted ARM runners are still in
limited availability for organizations).

### Base image

`debian:bookworm-slim` (~30 MB). Not Alpine: the C runtime is
glibc-built; musl/glibc mismatch would silently miscompile
runtime calls. Documented in `docs/guides/docker.md`.

### Image inheritance

Two independent images, both `FROM debian:bookworm-slim`. They do
NOT inherit from each other — the runtime image is intentionally
small and the builder is intentionally large; chaining them would
either bloat the runtime or strip the builder.

User apps use the multi-stage pattern:

```dockerfile
FROM ghcr.io/mapanare-research/mapanare-builder:5.19.0 AS build
COPY . /src
RUN mnc build --release

FROM ghcr.io/mapanare-research/mapanare-runtime:5.19.0
COPY --from=build /src/dist/myapp /app/myapp
ENTRYPOINT ["/app/myapp"]
```

### Tagging strategy

| Tag | Meaning | Mutable? |
|---|---|---|
| `:5.19.0` | This release exactly | No |
| `:5` | Latest 5.x | Yes — moves on every 5.x release |
| `:latest` | Current stable | Yes |

Pre-1.0 (i.e. all v5.x at time of writing) does not get a `:5`
moving tag for stability — `:5` only starts moving once a v5
final ships, so v5.19.0 ships with `:5.19.0` and `:latest` only.

Track via the `tags` block of `docker/build-push-action@v5`. When
v5.20.0 ships, `:5` will be added.

### Image-size targets

| Image | Target | Hard ceiling |
|---|---:|---:|
| `mapanare-builder:5.19.0` | ≤250 MB | 300 MB |
| `mapanare-runtime:5.19.0` | ≤80 MB | 100 MB |
| Multi-stage user app (hello-world) | ≤85 MB | 90 MB |

Builder size is dominated by clang-18 (~150 MB), lld-18 (~30
MB), and LLVM 18 dev libraries (~60 MB). Runtime size is
dominated by libc6 + libgcc-s1 (~50 MB).

If builder exceeds 300 MB, audit before merge. Levers: drop
`llvm-18-dev` (only needed for `llvm-as` validation in the test
harness, not for `mnc build`); use a multi-stage builder
internally (build stage with full LLVM, copy only the binaries
needed into the published image).

### v5.19.0 vs v5.18.0 tag inconsistency in PROMPT.md

PROMPT.md examples use `:5.18.0` in several places. The release
in flight is **v5.19.0** per `PLAN.md` line 1 and `VERSION`
(when bumped). All Docker image tags published by this release
ship as `:5.19.0`. The PROMPT examples are corrected to
`:5.19.0` in the actual files this release produces.

---

## Out-of-scope reaffirmations

- Hard removal of `{}` syntax — v6.0 only. v5.19.0 is soft
  deprecation.
- ARM64 / multi-arch — v5.20.0+.
- Alpine / musl variants — never (glibc-only runtime).
- Distroless / `FROM scratch` — v5.20.0+ once static linking
  story exists.
- Auto-publish on every dev commit — release tags only.
- Kubernetes operator / Helm chart — separate ecosystem repo.

---

## Validation gates (all must pass before merge)

1. `python -m pytest tests/test_brace_deprecation.py -v` —
   Te.3 unit tests pass.
2. `python -m pytest tests/test_format.py -v` — fmt regression
   suite passes.
3. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
   — goldens 66/66.
4. `bash scripts/verify_fixed_point.sh --keep` — strict 3-stage
   fixed point preserved.
5. `docker build -t mapanare/builder:test docker/builder/` succeeds,
   `docker images` reports ≤300 MB.
6. `docker build -t mapanare/runtime:test docker/runtime/` succeeds,
   `docker images` reports ≤100 MB.
7. `mnc init /tmp/v519-smoke --docker` produces a buildable
   project, multi-stage hello-world final image ≤90 MB.
8. `python -c "import yaml; yaml.safe_load(open('.github/workflows/publish-docker.yml'))"`
   succeeds.
9. `make lint` clean.
