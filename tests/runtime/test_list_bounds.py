"""v4.32.0 Phase 1.1 — `__mn_list_get` / `__mn_list_set` abort-on-OOB regression.

v4.31.0 removed the ``__mn_list_oob_buf`` 4KB thread-local zero-buffer
workaround. The OOB paths were left returning NULL / silently no-opping.
The Python emitter at ``emit_llvm_text.py:3101-3108`` dereferences the
returned pointer unconditionally, so any program that used to silently
read zeros now segfaults at a non-deterministic location.

Viper V2 (v4.31.0 arc-end panel, HIGH) called for loud aborts at the
runtime call site instead. v4.32.0 Phase 1.1 replaces the NULL return
and silent-noop with ``fprintf(stderr, "mapanare: list index %ld out of
bounds (len=%ld)") + abort()``.

This test compiles a tiny C driver linked against the runtime, drives
OOB cases via argv, and asserts:

1. The subprocess exits with a signal (abort()), not via a normal
   ``return`` or segfault — SIGABRT on Unix, non-zero on Windows.
2. Stderr carries the expected diagnostic pattern.

The parameter matrix covers get and set, empty and non-empty lists,
and negative and past-end indices — eight cases. Every case must abort.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import textwrap

import pytest

_IS_WINDOWS = platform.system() == "Windows"
_CC = os.environ.get("CC") or shutil.which("gcc") or shutil.which("clang") or shutil.which("cc")

_TEST_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
_RUNTIME_DIR = os.path.join(_REPO_ROOT, "runtime", "native")
_CORE_C = os.path.join(_RUNTIME_DIR, "mapanare_core.c")
_RUNTIME_C = os.path.join(_RUNTIME_DIR, "mapanare_runtime.c")

# Driver C program. Takes three argv positions:
#   argv[1]: operation — "get" | "set"
#   argv[2]: list setup — "empty" | "nonempty"
#   argv[3]: index — signed decimal
#
# On a working runtime, every case must abort before printing "REACHED_END".
# If the assertion later in Python sees REACHED_END on stdout, the
# abort path did not fire.
_DRIVER_C = r"""
#include "mapanare_core.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s <get|set> <empty|nonempty> <index>\n", argv[0]);
        return 2;
    }
    const char *op = argv[1];
    const char *setup = argv[2];
    long long idx = atoll(argv[3]);

    MnList list = __mn_list_new((int64_t)sizeof(int64_t));
    if (strcmp(setup, "nonempty") == 0) {
        int64_t v0 = 10, v1 = 20, v2 = 30;
        __mn_list_push(&list, &v0);
        __mn_list_push(&list, &v1);
        __mn_list_push(&list, &v2);
    }
    /* "empty" setup leaves list with len=0. */

    if (strcmp(op, "get") == 0) {
        void *p = __mn_list_get(&list, (int64_t)idx);
        /* Unreachable on OOB. Touch the result so the compiler cannot
           dead-code-eliminate the call. */
        if (p) fprintf(stderr, "UNEXPECTED_NONNULL=%p\n", p);
    } else if (strcmp(op, "set") == 0) {
        int64_t v = 99;
        __mn_list_set(&list, (int64_t)idx, &v);
    } else {
        fprintf(stderr, "unknown op: %s\n", op);
        return 2;
    }

    /* If we reach here the abort path did not fire. */
    printf("REACHED_END\n");
    return 0;
}
"""


def _build_driver(tmp_path: str) -> str:
    """Compile the driver + runtime once; return the binary path."""
    assert _CC is not None
    src_path = os.path.join(tmp_path, "list_bounds_driver.c")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(_DRIVER_C)

    binary_name = "list_bounds_driver"
    if _IS_WINDOWS:
        binary_name += ".exe"
    binary_path = os.path.join(tmp_path, binary_name)

    cmd = [
        _CC,
        "-O1",
        "-g",
        "-pthread",
        "-I",
        _RUNTIME_DIR,
        src_path,
        _CORE_C,
        _RUNTIME_C,
        "-o",
        binary_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        pytest.skip(f"driver compilation failed: {result.stderr[:2000]}")
    return binary_path


# Parameter matrix: (op, setup, index). Every case must abort.
# - empty: len=0; indices 0, -1, 100 are all OOB
# - nonempty: len=3; indices -1 (negative), 3 (first past-end), 100 (far past-end)
_OOB_CASES = [
    # op, setup, index
    ("get", "empty", 0),
    ("get", "empty", -1),
    ("get", "nonempty", -1),
    ("get", "nonempty", 3),
    ("get", "nonempty", 100),
    ("set", "empty", 0),
    ("set", "nonempty", -1),
    ("set", "nonempty", 3),
]


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
@pytest.mark.parametrize(("op", "setup", "index"), _OOB_CASES)
def test_list_oob_aborts_loudly(tmp_path: object, op: str, setup: str, index: int) -> None:
    """Every OOB case must abort with a diagnostic on stderr."""
    binary = _build_driver(str(tmp_path))
    result = subprocess.run(
        [binary, op, setup, str(index)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # 1. Must not reach normal exit. If it did, the abort path did not fire.
    assert "REACHED_END" not in result.stdout, (
        f"OOB {op}({setup}, {index}) returned normally; abort path did not fire.\n"
        f"stdout: {result.stdout!r}\n"
        f"stderr: {result.stderr!r}\n"
        f"returncode: {result.returncode}"
    )

    # 2. Must exit non-zero. On POSIX, abort() is SIGABRT (subprocess
    #    returns -signal.SIGABRT == -6). On Windows, abort() triggers
    #    an abnormal termination with returncode 3 or similar.
    assert result.returncode != 0, (
        f"OOB {op}({setup}, {index}) exited 0 despite no REACHED_END.\n"
        f"stdout: {result.stdout!r}\n"
        f"stderr: {result.stderr!r}"
    )

    # 3. Stderr must carry the diagnostic pattern the runtime prints.
    assert "list index" in result.stderr and "out of bounds" in result.stderr, (
        f"OOB {op}({setup}, {index}) did not print the expected diagnostic.\n"
        f"stderr: {result.stderr!r}"
    )

    # 4. The printed index must match what the caller passed. Catches
    #    accidental int-truncation regressions in the diagnostic format.
    assert str(index) in result.stderr, (
        f"OOB {op}({setup}, {index}) diagnostic did not echo the index.\n"
        f"stderr: {result.stderr!r}"
    )


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
def test_inbounds_still_works(tmp_path: object) -> None:
    """Sanity: an in-bounds get must still return normally (REACHED_END).

    Ensures Phase 1.1 did not break the happy path of __mn_list_get.
    """
    # Nonempty list has len=3; index 0/1/2 is in bounds. We test via a
    # purpose-built driver — a normal return means no abort fired.
    src = textwrap.dedent(r"""
        #include "mapanare_core.h"
        #include <stdio.h>
        #include <stdlib.h>
        int main(void) {
            MnList list = __mn_list_new((int64_t)sizeof(int64_t));
            int64_t v0 = 10, v1 = 20, v2 = 30;
            __mn_list_push(&list, &v0);
            __mn_list_push(&list, &v1);
            __mn_list_push(&list, &v2);
            int64_t *p0 = (int64_t *)__mn_list_get(&list, 0);
            int64_t *p2 = (int64_t *)__mn_list_get(&list, 2);
            if (!p0 || !p2) { fprintf(stderr, "NULL in-bounds result\n"); return 1; }
            printf("%ld %ld\n", (long)*p0, (long)*p2);
            return 0;
        }
        """)
    src_path = os.path.join(str(tmp_path), "list_inbounds_driver.c")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(src)
    binary_path = os.path.join(str(tmp_path), "list_inbounds_driver")
    if _IS_WINDOWS:
        binary_path += ".exe"
    assert _CC is not None
    cmd = [
        _CC,
        "-O1",
        "-g",
        "-pthread",
        "-I",
        _RUNTIME_DIR,
        src_path,
        _CORE_C,
        _RUNTIME_C,
        "-o",
        binary_path,
    ]
    compile_result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if compile_result.returncode != 0:
        pytest.skip(f"inbounds driver compilation failed: {compile_result.stderr[:2000]}")
    run_result = subprocess.run([binary_path], capture_output=True, text=True, timeout=30)
    assert run_result.returncode == 0, f"in-bounds path failed: {run_result.stderr!r}"
    assert "10 30" in run_result.stdout, f"in-bounds values mismatch: {run_result.stdout!r}"
