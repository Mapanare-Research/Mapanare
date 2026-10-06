#!/usr/bin/env bash
# mnc-build.sh — Incremental multi-module build for Mapanare projects.
#
# Features:
#   - Module dependency graph from import statements
#   - Source hashing (SHA-256) for cache invalidation
#   - Per-module .o compilation with caching
#   - Single link step at the end
#   - --timing flag for per-module timing
#   - Incremental: only recompiles modules whose source (or deps) changed
#
# Usage:
#   bash scripts/mnc-build.sh <dir> [-o output] [--timing] [--clean]
#   bash scripts/mnc-build.sh mapanare/self/ -o mnc --timing
#
# Cache layout:
#   .mnc_cache/
#       manifest.txt    — "module hash" per line
#       <module>.ll     — cached LLVM IR
#       <module>.o      — cached object file
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MNC="${MNC:-${ROOT}/mapanare/self/mnc-stage1}"
CACHE_ROOT="${ROOT}/.mnc_cache"
CC="${CC:-clang}"

# Parse arguments
DIR=""
OUTPUT="a.out"
TIMING=0
CLEAN=0
JOBS=1
OPT=-O2
LTO=""

while [ $# -gt 0 ]; do
    case "$1" in
        --timing) TIMING=1; shift ;;
        --clean)  CLEAN=1; shift ;;
        -j|--jobs) JOBS="$2"; shift 2 ;;
        --release) OPT=-O2; LTO=-flto; shift ;;
        --debug) OPT=-O0; LTO=""; shift ;;
        --small) OPT=-Os; LTO=-flto; shift ;;
        -o)       OUTPUT="$2"; shift 2 ;;
        *)        DIR="$1"; shift ;;
    esac
done

if [ -z "${DIR}" ]; then
    echo "usage: mnc-build.sh <dir> [-o output] [--timing] [--clean]" >&2
    exit 1
fi

# Resolve directory
if [ ! -d "${DIR}" ]; then
    echo "error: not a directory: ${DIR}" >&2
    exit 1
fi
DIR="$(cd "${DIR}" && pwd)"
if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
    echo "error: --jobs must be a positive integer" >&2
    exit 1
fi
if [ ! -f "$MNC" ]; then
    echo "error: native compiler not found: $MNC" >&2
    exit 1
fi
# Partition by project, compiler contents, toolchain and optimization flags.
# Source/dependency hashes below handle incremental edits within that context.
CONTEXT=$( { printf '%s\n' "$DIR" "$OPT" "$LTO" "$CC"; sha256sum "$MNC"; "$CC" --version; } | sha256sum | cut -d' ' -f1)
CACHE_DIR="${CACHE_ROOT}/projects/${CONTEXT}"

# Clean cache if requested
if [ "${CLEAN}" -eq 1 ]; then
    # Only this project's resolved context under the repository cache is removed.
    case "$CACHE_DIR" in "$ROOT"/.mnc_cache/projects/*) rm -rf -- "$CACHE_DIR" ;; *) exit 1 ;; esac
    echo "Cache cleared."
    exit 0
fi

mkdir -p "${CACHE_DIR}"
# Avoid competing invocations publishing a manifest over one another. Module
# jobs within this build have disjoint paths and may run concurrently.
if ! mkdir "${CACHE_DIR}/build.lock" 2>/dev/null; then
    echo "error: build already active for this cache; retry or remove stale build.lock" >&2
    exit 1
fi
trap 'rmdir "${CACHE_DIR}/build.lock"' EXIT

# Find all .mn files in the directory
MN_FILES=()
while IFS= read -r -d '' f; do
    MN_FILES+=("$f")
done < <(find "${DIR}" -maxdepth 1 -name '*.mn' -print0 | sort -z)

if [ ${#MN_FILES[@]} -eq 0 ]; then
    echo "error: no .mn files found in ${DIR}" >&2
    exit 1
fi

# --- Build dependency graph from import statements ---
# For each file, extract import paths and map to files in the same directory
declare -A DEPS       # module → space-separated list of dependency modules
declare -A MOD_FILE   # module name → file path
declare -A FILE_MOD   # file path → module name
declare -A UNCACHED   # imports outside this script's dependency model

for f in "${MN_FILES[@]}"; do
    mod=$(basename "$f" .mn)
    MOD_FILE[$mod]="$f"
    FILE_MOD[$f]="$mod"

    # Extract imports: "import self::foo" → "foo"
    deps=""
    while IFS= read -r imp; do
        if [ -n "${imp}" ]; then
            deps="${deps} ${imp}"
        fi
    done < <(sed -n 's/^[[:space:]]*import self::\([a-zA-Z_][a-zA-Z_0-9]*\).*/\1/p' "$f")
    DEPS[$mod]="${deps}"
    # The script only resolves self:: imports in this directory. Never reuse an
    # object when another import could have changed outside that known graph.
    if sed -n '/^[[:space:]]*import /p' "$f" | grep -qv '^[[:space:]]*import self::[a-zA-Z_][a-zA-Z_0-9]*[[:space:]]*$'; then
        UNCACHED[$mod]=1
    fi
done
for mod in "${!MOD_FILE[@]}"; do
    for dep in ${DEPS[$mod]:-}; do
        if [ -z "${MOD_FILE[$dep]:-}" ]; then UNCACHED[$mod]=1; fi
    done
done

# --- Topological sort ---
# Simple iterative toposort: repeatedly emit modules with all deps satisfied
declare -A EMITTED
ORDER=()
MAX_ITER=${#MN_FILES[@]}
for _round in $(seq 1 $((MAX_ITER + 1))); do
    progress=0
    for mod in "${!MOD_FILE[@]}"; do
        [ -n "${EMITTED[$mod]:-}" ] && continue
        all_ok=1
        for dep in ${DEPS[$mod]:-}; do
            if [ -n "${MOD_FILE[$dep]:-}" ] && [ -z "${EMITTED[$dep]:-}" ]; then
                all_ok=0
                break
            fi
        done
        if [ "${all_ok}" -eq 1 ]; then
            ORDER+=("$mod")
            EMITTED[$mod]=1
            progress=1
        fi
    done
    [ "${progress}" -eq 0 ] && break
done

# Check for cycles
if [ ${#ORDER[@]} -ne ${#MN_FILES[@]} ]; then
    echo "warning: possible circular dependency; compiling remaining modules" >&2
    for mod in "${!MOD_FILE[@]}"; do
        [ -z "${EMITTED[$mod]:-}" ] && ORDER+=("$mod")
    done
fi

# --- Hash-based cache check ---
MANIFEST="${CACHE_DIR}/manifest.txt"
declare -A OLD_HASH
if [ -f "${MANIFEST}" ]; then
    while IFS=' ' read -r mod hash; do
        OLD_HASH[$mod]="$hash"
    done < "${MANIFEST}"
fi

# Compute current hashes and determine what needs recompiling
declare -A CUR_HASH
declare -A NEEDS_REBUILD

for mod in "${ORDER[@]}"; do
    f="${MOD_FILE[$mod]}"
    hash=$(sha256sum "$f" | cut -d' ' -f1)
    CUR_HASH[$mod]="$hash"

    if [ "${OLD_HASH[$mod]:-}" != "${hash}" ] || [ ! -f "${CACHE_DIR}/${mod}.o" ] || [ -n "${UNCACHED[$mod]:-}" ]; then
        NEEDS_REBUILD[$mod]=1
    fi
done

# If a dependency changed, all dependents need rebuilding too
changed=1
while [ "${changed}" -eq 1 ]; do
    changed=0
    for mod in "${ORDER[@]}"; do
        [ -n "${NEEDS_REBUILD[$mod]:-}" ] && continue
        for dep in ${DEPS[$mod]:-}; do
            if [ -n "${NEEDS_REBUILD[$dep]:-}" ]; then
                NEEDS_REBUILD[$mod]=1
                changed=1
                break
            fi
        done
    done
done

# --- Compile modules ---
TOTAL=${#ORDER[@]}
CACHED=0
COMPILED=0
FAILED=0
SECONDS=0

if [ "${TIMING}" -eq 1 ]; then
    printf "\n  %-30s %-12s %s\n" "Module" "Status" "Time"
    printf "  %-30s %-12s %s\n" "------" "------" "----"
fi

compile_module() {
    local mod="$1"
    local f ll_cache o_cache MOD_START MOD_TIME
    f="${MOD_FILE[$mod]}"
    ll_cache="${CACHE_DIR}/${mod}.ll"
    o_cache="${CACHE_DIR}/${mod}.o"

    if [ -z "${NEEDS_REBUILD[$mod]:-}" ] && [ -f "${o_cache}" ]; then
        # Use cached object
        if [ "${TIMING}" -eq 1 ]; then
            printf "  %-30s %-12s %s\n" "${mod}.mn" "[cached]" "0ms"
        fi
        return 0
    fi

    # Compile module
    MOD_START=$SECONDS

    # Use mnc to compile to IR (v5.9.1 DX.5: explicit `emit-llvm` subcommand;
    # default is now implicit-run).
    # Delete a previous object before attempting its replacement. A failed
    # compile must never let the new source hash bless an old object.
    rm -f -- "${o_cache}"
    if "${MNC}" emit-llvm "$f" > "${ll_cache}.tmp"; then
        # Rename @main if present
        sed 's/@main(/@mn_main(/g' "${ll_cache}.tmp" > "${ll_cache}"

        # Compile IR to object
        if "$CC" -c "$OPT" ${LTO:+"$LTO"} "${ll_cache}" -o "${o_cache}.tmp"; then
            mv -- "${o_cache}.tmp" "${o_cache}"
            MOD_TIME=$(( SECONDS - MOD_START ))
            if [ "${TIMING}" -eq 1 ]; then
                printf "  %-30s %-12s %s\n" "${mod}.mn" "[compiled]" "${MOD_TIME}s"
            fi
        else
            echo "error: clang failed for ${mod}.mn" >&2
            return 1
        fi
    else
        echo "error: mnc failed for ${mod}.mn" >&2
        return 1
    fi
}

PIDS=()
for mod in "${ORDER[@]}"; do
    compile_module "$mod" &
    PIDS+=("$!")
    if [ "${#PIDS[@]}" -ge "$JOBS" ]; then
        for pid in "${PIDS[@]}"; do
            if ! wait "$pid"; then FAILED=$((FAILED + 1)); fi
        done
        PIDS=()
    fi
done
for pid in "${PIDS[@]}"; do
    if ! wait "$pid"; then FAILED=$((FAILED + 1)); fi
done
OBJ_FILES=()
for mod in "${ORDER[@]}"; do
    if [ -f "${CACHE_DIR}/${mod}.o" ]; then
        OBJ_FILES+=("${CACHE_DIR}/${mod}.o")
        if [ -z "${NEEDS_REBUILD[$mod]:-}" ]; then CACHED=$((CACHED + 1)); fi
    fi
done

# Save manifest (even if some modules failed — cache successful ones)
{
    for mod in "${ORDER[@]}"; do
        if [ -f "${CACHE_DIR}/${mod}.o" ]; then
            echo "${mod} ${CUR_HASH[$mod]}"
        fi
    done
} > "${MANIFEST}"

if [ "${FAILED}" -gt 0 ]; then
    echo "error: ${FAILED} module(s) failed to compile" >&2
    exit 1
fi

# --- Link ---
LINK_START=$SECONDS
if [ ${#OBJ_FILES[@]} -gt 0 ]; then
    # Try precompiled runtime first
    LINK_CMD=("$CC" "$OPT")
    if [ -n "$LTO" ]; then LINK_CMD+=("$LTO"); fi
    LINK_CMD+=("${OBJ_FILES[@]}")

    RT="${ROOT}/runtime/native/libmapanare_rt.a"
    if [ -f "${RT}" ]; then
        LINK_CMD+=("${RT}")
    else
        LINK_CMD+=("${ROOT}/runtime/native/mapanare_core.c" "${ROOT}/runtime/native/mn_user_main.c" -I "${ROOT}/runtime/native")
    fi
    LINK_CMD+=(-o "${OUTPUT}" -lm -lpthread)
    if [ "$(uname -s)" = Linux ]; then LINK_CMD+=(-no-pie -rdynamic -ldl); fi

    if "${LINK_CMD[@]}"; then
        LINK_TIME=$(( SECONDS - LINK_START ))
        if [ "${TIMING}" -eq 1 ]; then
            printf "  %-30s %-12s %s\n" "link" "" "${LINK_TIME}s"
            printf "  %s\n" "─────────────────────────────────────────"
            printf "  total: %ds  (%d/%d cached)\n" "${SECONDS}" "${CACHED}" "${TOTAL}"
        fi
        echo "built: ${OUTPUT}"
    else
        echo "error: link failed" >&2
        exit 1
    fi
fi

# Manifest already saved above.
