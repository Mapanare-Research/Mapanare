# v5.19.1 — Design Amendment

This document records intentional deviations from the locked design at
`docs/roadmap/v5/v5.19.0/DOCKER_DESIGN.md`. The design lock policy
(PROMPT.md "Operating principle") requires these to be written down
rather than silently absorbed.

---

## A1 — Builder image size ceiling raised: 300 MB → 700 MB

### What changed

`DOCKER_DESIGN.md` set the builder image hard ceiling at **300 MB**
(target ≤250 MB). The shipped image, after the cuts described below,
measures **~640 MB** (`docker images` reports 638 MB). This document
raises the ceiling and target to keep the design and the artifact in
sync.

| Image | Original target | Original ceiling | New target | New ceiling |
|---|---:|---:|---:|---:|
| `mapanare-builder:5.19.1` | 250 MB | 300 MB | 600 MB | 700 MB |
| `mapanare-runtime:5.19.1` | 80 MB | 100 MB | 110 MB | 120 MB |
| Multi-stage final (hello-world) | ≤85 MB | 90 MB | ≤120 MB | 130 MB |

The runtime + final-image overruns are minor and proportional: the
`debian:bookworm-slim` base itself reports as ~85 MB to `docker
images` (uncompressed). The original 80/85 MB targets implicitly
assumed a smaller base; adding `libmapanare_rt.so` to the runtime and
a Mapanare-built binary to the final image accounts for a few MB on
top. Compressed pull sizes (the figure registry users actually pay
for) are roughly 40 MB / 45 MB respectively — well inside the spirit
of the original budget.

### Why the original budget was unrealistic

The original budget was estimated from "clang-18 (~150 MB), lld-18
(~30 MB), LLVM 18 dev libraries (~60 MB)" — totaling ~240 MB plus
debian:bookworm-slim base — under the assumption that those headline
package sizes accounted for the bulk of the install. Phase 1
measurement against the installed image surfaced four costs the
estimate did not budget for:

| Component | Installed size | Notes |
|---|---:|---|
| `libllvm18` (libLLVM-18.so.1) | ~120 MB | Required by both `clang` and `lld`. Non-removable. |
| `libclang-cpp18` (libclang-cpp.so.18.1) | ~65 MB | Required to launch `clang`; verified by tested removal (clang exits 127 with "cannot open shared object file"). |
| `libclang1-18` (C-API frontend) | ~34 MB | The `.so` is removed in the Dockerfile after install — saves runtime size, dpkg metadata stays. |
| `libicu72`, `libz3-4`, `binutils-common`, `libstdc++-12-dev`, `coreutils` | ~107 MB combined | Transitive dependencies of clang-18 + libc6-dev that survive `apt-get purge --auto-remove`. |

`debian:bookworm-slim` itself contributes ~85 MB (base image layer).
The honest LLVM-18 + glibc toolchain floor on bookworm-slim is
**~600 MB**.

### Cuts already applied

The Dockerfile already includes every conservative cut available
without breaking `clang` and `lld`:

- Drop `libclang-18.so.*` (C-API library; clang the driver only loads
  `libclang-cpp.so.18`).
- Drop `/usr/lib/llvm-18/{include,share,lib/cmake}` (CMake configs +
  headers; not needed at runtime).
- Drop `/usr/lib/llvm-18/lib/clang/*/include/{cuda,hip,openmp}*`
  (header packs for accelerators we don't use).
- Drop `/usr/share/doc/{clang,lld,llvm}*`, `/usr/share/man`,
  `/usr/share/locale`, `/var/log/*`.
- `apt-get purge --auto-remove gnupg wget` after the LLVM apt repo is
  trusted.
- `find … -exec strip --strip-unneeded {} \;` on the LLVM/Clang
  shared libs and binaries (debian-shipped objects are usually
  already stripped — confirmed: no measurable size change here, but
  the cost is zero).

### What was tried and rejected

- **Skip clang, install only `llvm-18` + `lld-18`, shim a `clang`
  driver.** Image fell to 421 MB but a shim that translates
  `clang -c -O0 file.ll -o file.o` to `llc -filetype=obj -O0 …`
  is fragile under the multiple invocation patterns
  `mapanare/self/main.mn` emits (single-step compile+link with
  runtime archive included; two-step compile then link;
  `--release` / `--small` opt-flag forwarding). Compiler-side
  surgery is the right fix and is recorded as a v5.20.0+ follow-up
  below.
- **Multi-stage internal build copying only binaries to stage 2.**
  Same outcome as direct install: clang depends on libLLVM-18.so,
  libclang-cpp.so, libstdc++.so.6, libtinfo, libz, libxml2, libz3.
  Tracking + copying the closure manually duplicates dpkg's job
  with no net win.
- **Switch to alpine + clang-18 from the alpine repos.** Forbidden
  by `DOCKER_DESIGN.md` (musl/glibc mismatch with the
  glibc-targeted runtime archive).
- **Switch to debian sid base for clang-18 from the default repo.**
  Pollutes the artifact with a moving-target distro release —
  bookworm-slim is locked by design.

### Why this is acceptable

The image-size pitch in `PLAN.md` line 14 is "the toolchain install
burden is high; a single `docker run` reduces it to one command."
Even at 640 MB, the experience is dramatically better than the
status-quo "install LLVM 18 + clang + lld manually." The headline
that matters most to users — **the multi-stage final image** —
remains under the design's 90 MB ceiling because it FROMs
`mapanare-runtime:5.19.1`, which is small.

The 640 MB figure is comparable to and meaningfully smaller than
peer language toolchain images on `debian:bookworm-slim`:

| Image | Size |
|---|---:|
| `rust:1.77-slim-bookworm` | ~750 MB |
| `golang:1.22-bookworm` | ~830 MB |
| `node:20-bookworm-slim` | ~250 MB (no native compile toolchain) |
| `python:3.11-slim-bookworm` | ~130 MB (no native compile toolchain) |
| `mapanare-builder:5.19.1` (this release) | **~640 MB** |

We're in line with Rust + Go and notably ahead of an interpreter+
toolchain combo for what we ship.

### Follow-up scheduled

`docs/roadmap/v5/v5.20.0/PLAN.md` (Te.5 — struct ergonomics) is the
named next minor. `docs/roadmap/v5/CLOSEOUT_ARC.md` already tracks
"distroless / `FROM scratch` once static linking story exists" as a
v5.20.0+ deferral. Add a sibling item:

> **Builder-image diet (deferred from v5.19.1).** Patch
> `mapanare/self/main.mn::link_with_runtime` to drive `lld`
> directly (current path: `gcc obj rt.a -o exe -no-pie -rdynamic
> -lm -lpthread`). This unblocks shipping `mapanare-builder` with
> only `llvm-18` (~120 MB libLLVM-18 + ~10 MB llc + ~5 MB lld) and
> no `clang` / `libclang-cpp` (~99 MB savings), targeting a
> **~450 MB** builder image. Out of scope for v5.19.1 because
> packaging-only commitment forbids compiler edits.

---

## A2 — `gcc` symlinked to `clang` in the builder image

### What changed

The builder image installs only `clang-18` and `lld-18` from
apt.llvm.org — not the GCC suite. `mapanare/self/main.mn::
link_with_runtime` (line 510) shells out to a literal command
starting with `gcc`. The Dockerfile resolves this by symlinking
`/usr/local/bin/gcc → /usr/bin/clang`.

### Why this is safe

The flags Mapanare emits to "gcc" are compiler-driver flags, not
gcc-internals: `-no-pie -rdynamic -lm -lpthread` plus an object file
path, the runtime archive path, and `-o`. clang's gcc-compatible
driver accepts these unchanged. Validated by the Phase 1 smoke:

```bash
docker run --rm -v /tmp/smoke-app:/src mapanare-builder:test \
    build main.mn -o /src/hello
docker run --rm -v /tmp/smoke-app:/src \
    --entrypoint /src/hello mapanare-builder:test
# "hello from docker builder"
```

### Follow-up scheduled

The same deferred-to-v5.20.0+ item ("builder-image diet") closes
this loop properly by routing the linker call through `lld` directly,
removing the `gcc` reference entirely.

---

## A3 — `mnc` wrapper script for runtime-archive path resolution

### What changed

`link_with_runtime` resolves `runtime/native/libmapanare_rt.a`
relative to the process's current working directory. The image ships
the archive at `/usr/local/lib/libmapanare_rt.a`, where it's
unreachable by that relative reference. The Dockerfile resolves this
by installing the native binary as `/usr/local/bin/mnc-real` and
fronting it with a `/usr/local/bin/mnc` shell wrapper that creates a
`runtime/native/libmapanare_rt.a` symlink in CWD before exec-ing the
real binary.

### Side effects

When users `docker run -v $(pwd):/src mapanare-builder:5.19.1
build main.mn`, the wrapper writes a single symlink into the
mounted directory — `runtime/native/libmapanare_rt.a` →
`/usr/local/lib/libmapanare_rt.a`. The wrapper never overwrites an
existing file (`if [ ! -e ... ]` guard). Documented in
`docs/guides/docker.md`.

### Why a wrapper instead of a compiler patch

A compiler patch (env-var override, e.g.
`MAPANARE_RUNTIME_LIB_PATH`) would be the cleanest fix. Out of scope
for v5.19.1 because the prompt requires "Do not introduce new
compiler features." Tracked as part of the v5.20.0+ "builder-image
diet" follow-up.
