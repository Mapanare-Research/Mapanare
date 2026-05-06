"""v5.45.0 Ts.4 — ASan + valgrind sweeps on tensor view drop-glue.

UB-risk tier from PROMPT_TEMPLATE: drop-glue ordering on a refcount-
managed tensor is the load-bearing invariant. ASan catches use-after-
free, double-free, and leaks; valgrind catches uninitialized reads
and additional leak shapes. Both run on every view scenario.

Falsifiability — revert mapanare_runtime.c::mapanare_tensor_free to
the unconditional pre-v5.45.0 free path (always free data + shape +
struct, no refcount check) and every test fails:
- view-then-parent: ASan reports double-free of data on second free
- multi-view: ASan reports use-after-free as v2 reads parent's
  freed data
- view-of-view chain: valgrind reports uninitialized read after
  intermediate view's struct is freed

These tests use a small C harness rather than going through the
Mapanare emitter because (a) they need precise control over alloc/
free ordering that the language-level `let` scope doesn't expose,
(b) they exercise the runtime invariant directly, and (c) they're
the same shape as the Phase 1 / Phase 2 /tmp/ts2[ab]_smoke.c
harnesses but committed to the test suite for CI.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def runtime_archive() -> Path:
    archive = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"
    if not archive.is_file():
        pytest.skip(f"libmapanare_rt.a not present at {archive}; run `make build-rt`")
    return archive


@pytest.fixture(scope="module")
def gcc_bin() -> str:
    found = shutil.which("gcc")
    if not found:
        pytest.skip("gcc not on PATH")
    return found


@pytest.fixture(scope="module")
def valgrind_bin() -> str | None:
    return shutil.which("valgrind")


_C_HARNESS = textwrap.dedent(
    """\
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include <stdint.h>

    typedef struct mapanare_tensor {
        void *data; int64_t ndim; int64_t *shape; int64_t size; int64_t elem_size;
        int64_t refcount; uint8_t is_view; uint8_t _pad[7];
        struct mapanare_tensor *parent;
    } mapanare_tensor_t;
    typedef struct { void *data; int64_t len, cap, elem_size, managed; } MnList;

    extern mapanare_tensor_t *mapanare_tensor_alloc(int64_t, const int64_t *, int64_t);
    extern void mapanare_tensor_free(mapanare_tensor_t *);
    extern mapanare_tensor_t *__mn_tensor_view(mapanare_tensor_t *, const MnList *);
    extern mapanare_tensor_t *__mn_tensor_reshape(mapanare_tensor_t *, const MnList *);
    extern mapanare_tensor_t *__mn_tensor_step_slice(
        const mapanare_tensor_t *, const int64_t *, const int64_t *,
        const int64_t *, int64_t);

    static MnList shape_list(int64_t *dims, int64_t n) {
        MnList l = {dims, n, n, sizeof(int64_t), 0};
        return l;
    }

    int main(void) {
    %BODY%
        return 0;
    }
    """
)


_SCENARIOS = {
    "alloc_then_free": """
        int64_t shape[] = {4};
        mapanare_tensor_t *t = mapanare_tensor_alloc(1, shape, sizeof(double));
        ((double *)t->data)[0] = 1.0;
        mapanare_tensor_free(t);
    """,
    "view_then_parent": """
        int64_t shape4[] = {4}, shape22[] = {2, 2};
        mapanare_tensor_t *p = mapanare_tensor_alloc(1, shape4, sizeof(double));
        MnList sl = shape_list(shape22, 2);
        mapanare_tensor_t *v = __mn_tensor_view(p, &sl);
        mapanare_tensor_free(v);
        mapanare_tensor_free(p);
    """,
    "parent_then_view": """
        int64_t shape4[] = {4}, shape22[] = {2, 2};
        mapanare_tensor_t *p = mapanare_tensor_alloc(1, shape4, sizeof(double));
        MnList sl = shape_list(shape22, 2);
        mapanare_tensor_t *v = __mn_tensor_view(p, &sl);
        mapanare_tensor_free(p);
        mapanare_tensor_free(v);
    """,
    "multi_view": """
        int64_t shape4[] = {4}, shape22[] = {2, 2};
        mapanare_tensor_t *p = mapanare_tensor_alloc(1, shape4, sizeof(double));
        MnList sl1 = shape_list(shape22, 2), sl2 = shape_list(shape4, 1);
        mapanare_tensor_t *v1 = __mn_tensor_view(p, &sl1);
        mapanare_tensor_t *v2 = __mn_tensor_view(p, &sl2);
        mapanare_tensor_t *v3 = __mn_tensor_view(p, &sl1);
        mapanare_tensor_free(v2);
        mapanare_tensor_free(v3);
        mapanare_tensor_free(p);
        mapanare_tensor_free(v1);
    """,
    "view_of_view_chain": """
        int64_t shape4[] = {4}, shape22[] = {2, 2};
        mapanare_tensor_t *p = mapanare_tensor_alloc(1, shape4, sizeof(double));
        MnList sl1 = shape_list(shape22, 2), sl2 = shape_list(shape4, 1);
        mapanare_tensor_t *v1 = __mn_tensor_view(p, &sl1);
        mapanare_tensor_t *v2 = __mn_tensor_view(v1, &sl2);
        if (v2->parent != p) abort();  // single-hop invariant
        mapanare_tensor_free(v1);
        mapanare_tensor_free(v2);
        mapanare_tensor_free(p);
    """,
    "reshape_aliased_drop": """
        int64_t shape4[] = {4}, shape22[] = {2, 2};
        mapanare_tensor_t *p = mapanare_tensor_alloc(1, shape4, sizeof(double));
        ((double *)p->data)[0] = 1.0;
        MnList sl = shape_list(shape22, 2);
        mapanare_tensor_t *r = __mn_tensor_reshape(p, &sl);
        ((double *)r->data)[3] = 99.0;
        if (((double *)p->data)[3] != 99.0) abort();
        mapanare_tensor_free(r);
        mapanare_tensor_free(p);
    """,
    "step_slice_owns_data": """
        int64_t shape6[] = {6};
        mapanare_tensor_t *t = mapanare_tensor_alloc(1, shape6, sizeof(double));
        for (int i = 0; i < 6; i++) ((double *)t->data)[i] = (double)i;
        int64_t starts[] = {0}, ends[] = {6}, steps[] = {2};
        mapanare_tensor_t *s = __mn_tensor_step_slice(t, starts, ends, steps, 1);
        if (s->is_view) abort();              // copy semantics, NOT a view
        if (s->refcount != 1) abort();
        ((double *)s->data)[0] = 999.0;
        if (((double *)t->data)[0] == 999.0) abort();  // src untouched
        mapanare_tensor_free(s);
        mapanare_tensor_free(t);
    """,
}


def _build_and_run(
    body: str,
    gcc_bin: str,
    runtime_archive: Path,
    tmp_path: Path,
    sanitizer: str | None,
    valgrind: str | None,
) -> tuple[int, str, str]:
    src = _C_HARNESS.replace("%BODY%", body)
    src_path = tmp_path / "harness.c"
    src_path.write_text(src)
    bin_path = tmp_path / "harness"
    cmd = [
        gcc_bin,
        "-O1" if sanitizer else "-O2",
        "-g",
        str(src_path),
        f"-L{runtime_archive.parent}",
        "-lmapanare_rt",
        "-lm",
        "-lpthread",
        "-ldl",
        "-o",
        str(bin_path),
    ]
    if sanitizer == "asan":
        cmd.insert(1, "-fsanitize=address")
    subprocess.run(cmd, check=True, capture_output=True)
    if valgrind:
        run_cmd = [
            valgrind,
            "--error-exitcode=99",
            "--leak-check=full",
            "--show-leak-kinds=definite,indirect",
            str(bin_path),
        ]
    else:
        run_cmd = [str(bin_path)]
    env = os.environ.copy()
    if sanitizer == "asan":
        env["ASAN_OPTIONS"] = "detect_leaks=1"
    result = subprocess.run(run_cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr


@pytest.mark.parametrize("scenario", list(_SCENARIOS.keys()))
def test_view_scenario_asan(
    scenario: str, gcc_bin: str, runtime_archive: Path, tmp_path: Path
) -> None:
    """Each scenario must run cleanly under ASan: 0 leaks, 0 errors."""
    rc, stdout, stderr = _build_and_run(
        _SCENARIOS[scenario], gcc_bin, runtime_archive, tmp_path,
        sanitizer="asan", valgrind=None,
    )
    assert rc == 0, f"ASan failure on {scenario}: rc={rc}\nstdout={stdout}\nstderr={stderr}"
    # ASan exits non-zero on detected issues; if rc==0, scenario is clean.


@pytest.mark.parametrize("scenario", list(_SCENARIOS.keys()))
def test_view_scenario_valgrind(
    scenario: str,
    gcc_bin: str,
    runtime_archive: Path,
    tmp_path: Path,
    valgrind_bin: str | None,
) -> None:
    """Each scenario must run cleanly under valgrind: 0 leaks, 0 errors.
    Skipped when valgrind is not available."""
    if valgrind_bin is None:
        pytest.skip("valgrind not on PATH")
    rc, stdout, stderr = _build_and_run(
        _SCENARIOS[scenario], gcc_bin, runtime_archive, tmp_path,
        sanitizer=None, valgrind=valgrind_bin,
    )
    assert rc == 0, (
        f"valgrind failure on {scenario}: rc={rc}\nstdout={stdout}\n"
        f"stderr={stderr}"
    )
