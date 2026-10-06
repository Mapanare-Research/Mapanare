"""Check signed replacement lengths with GCC and Clang's bit-field rules."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux sanitizer linking")


@pytest.mark.parametrize("compiler", ["gcc", "clang"])
@pytest.mark.parametrize("optimization", ["-O0", "-O2"])
def test_replace_growth_shrink_and_longer_needle(compiler, optimization, tmp_path):
    cc = shutil.which(compiler)
    if not cc:
        pytest.skip(f"{compiler} required")
    source = tmp_path / "replace.c"
    source.write_text(r"""
#include "mapanare_core.h"
#include <assert.h>
#include <string.h>

static MnString literal(const char *s) {
    MnString result = {s, strlen(s), 0};
    return result;
}

static void check(const char *s, const char *old, const char *replacement,
                  const char *expected) {
    MnString result = __mn_str_replace(literal(s), literal(old), literal(replacement));
    assert(result.len == strlen(expected));
    assert(memcmp(result.data, expected, (size_t)result.len) == 0);
    __mn_str_free_v(result);
}

int main(void) {
    check("banana", "na", "x", "baxx");
    check("banana", "na", "", "ba");
    check("aaaa", "aa", "z", "zz");
    check("aaa", "aa", "", "a");
    check("hello", "l", "LONG", "heLONGLONGo");
    check("short", "a longer needle", "x", "short");
    check("short", "absent", "x", "short");
    check("", "x", "y", "");
    check("abc", "", "y", "abc");
    check("abc", "abc", "", "");
    return 0;
}
""")
    binary = tmp_path / "replace"
    subprocess.run(
        [
            cc,
            optimization,
            "-g",
            "-fsanitize=address,undefined",
            "-no-pie",
            "-ffunction-sections",
            "-fdata-sections",
            "-Wl,--gc-sections",
            str(source),
            str(ROOT / "runtime/native/mapanare_core.c"),
            "-I",
            str(ROOT / "runtime/native"),
            "-lm",
            "-pthread",
            "-o",
            str(binary),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    result = subprocess.run(
        [str(binary)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1", "UBSAN_OPTIONS": "halt_on_error=1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
