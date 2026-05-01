# mapanare-builder — compiles .mn sources to native binaries.
#
# Provides clang-18, lld-18, the LLVM 18 toolchain, the `mnc` self-hosted
# Mapanare compiler, and `libmapanare_rt.a` for static linking.
#
# Used as the build stage of multi-stage Mapanare app Dockerfiles. See
# `docs/guides/docker.md` for usage.
#
# Target size: ≤250 MB. Hard ceiling: 300 MB.

FROM debian:bookworm-slim

# clang-18 / lld-18 are not in bookworm's default repos; pull from
# apt.llvm.org. After install we aggressively prune unused frontends
# and tools — `mnc build` only needs the IR-to-object backend plus
# the linker driver, not Clang's tooling/CTU machinery.
#
# See docs/roadmap/v5/v5.19.1/DESIGN_AMENDMENT.md for why the image
# still exceeds DOCKER_DESIGN.md's original 300 MB ceiling: libLLVM-18
# alone is ~120 MB and is non-optional.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        gnupg \
        wget \
        libc6-dev \
    && wget -qO- https://apt.llvm.org/llvm-snapshot.gpg.key \
        | gpg --dearmor -o /usr/share/keyrings/llvm-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/llvm-archive-keyring.gpg] https://apt.llvm.org/bookworm/ llvm-toolchain-bookworm-18 main" \
        > /etc/apt/sources.list.d/llvm.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        clang-18 \
        lld-18 \
    && apt-get purge -y --auto-remove gnupg wget \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /etc/apt/sources.list.d/llvm.list /usr/share/keyrings/llvm-archive-keyring.gpg \
    # Strip LLVM/Clang headers + cmake configs + unused tooling. We keep
    # only the binaries and shared libs that `clang` and `lld` exec at
    # runtime to compile + link Mapanare-emitted IR.
    && rm -rf \
        /usr/lib/llvm-18/include \
        /usr/lib/llvm-18/share \
        /usr/lib/llvm-18/lib/cmake \
        /usr/lib/llvm-18/lib/clang/*/include/cuda* \
        /usr/lib/llvm-18/lib/clang/*/include/hip* \
        /usr/lib/llvm-18/lib/clang/*/include/openmp* \
        /usr/lib/x86_64-linux-gnu/libclang-18.so* \
        /usr/lib/llvm-18/lib/libclang.so* \
        /usr/lib/llvm-18/lib/libclang-18.so* \
        /usr/share/doc/clang* \
        /usr/share/doc/lld* \
        /usr/share/doc/llvm* \
        /usr/share/man \
        /usr/share/locale \
        /var/log/* \
    # Strip debug symbols from LLVM/Clang shared libs and binaries.
    # Saves ~80–120 MB on amd64.
    && find /usr/lib/x86_64-linux-gnu/libLLVM* \
            /usr/lib/x86_64-linux-gnu/libclang-cpp* \
            /usr/lib/llvm-18/bin/* \
        -type f -exec strip --strip-unneeded {} \; 2>/dev/null \
        || true \
    && update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 100 \
    && update-alternatives --install /usr/bin/lld   lld   /usr/bin/lld-18   100 \
    && update-alternatives --install /usr/bin/ld.lld ld.lld /usr/bin/ld.lld-18 100 \
    # `mnc build` shells out to `gcc` for linking. clang is a drop-in
    # replacement for the flags Mapanare emits (-no-pie -rdynamic -lm
    # -lpthread); aliasing avoids pulling in the full gcc package.
    && ln -s /usr/bin/clang /usr/local/bin/gcc

# `mnc` (Linux amd64 self-hosted compiler) and the static C runtime archive.
# The publish workflow stages these from the release build; for local
# development the contributor stages them from the in-tree artifacts.
COPY mnc /usr/local/bin/mnc-real
COPY libmapanare_rt.a /usr/local/lib/

# `mnc build` resolves `runtime/native/libmapanare_rt.a` relative to CWD.
# The wrapper ensures that path exists by symlinking the prebuilt archive
# from /usr/local/lib/, then forwards every argument to the real binary.
COPY mnc-wrapper.sh /usr/local/bin/mnc

RUN chmod +x /usr/local/bin/mnc-real /usr/local/bin/mnc

WORKDIR /src

ENTRYPOINT ["mnc"]
