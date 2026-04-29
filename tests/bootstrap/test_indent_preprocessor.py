"""Cross-bootstrap validation for the colon-block preprocessor.

v5.14.1 B.7: asserts byte-identical output between
``mapanare.parser._indent_to_braces`` (Python) and
``runtime/native/mapanare_core.c::__mn_indent_to_braces`` (C, exposed
via ``mnc-stage1 preprocess``) on every parseable golden plus the
parameterized hand-rolled fixtures below.

Without this test, a divergence between the two preprocessors goes
undetected until v5.17.0 (Sh.\\* — mechanical rewrite of
``mapanare/self/``) fails on some edge case the corpus didn't
exercise. Failing loudly now is the whole point.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

from mapanare.parser import _indent_to_braces

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
STAGE1 = ROOT / "mapanare" / "self" / "mnc-stage1"
GOLDEN_DIR = ROOT / "tests" / "golden"


def _bootstrap_preprocess(source: str) -> str:
    """Run ``mnc-stage1 preprocess`` on ``source`` and return its stdout.

    The subcommand reads from a file argument (no stdin), so we write
    to a tempfile inside the test fixture. The bootstrap binary writes
    a trailing newline because the underlying ``.mn`` driver uses
    ``print()`` (which appends ``\\n``); the Python reference does not.
    Strip exactly one trailing ``\\n`` to align the two — anything more
    nuanced would mask real divergence.
    """
    if not STAGE1.exists():
        pytest.skip(f"mnc-stage1 not built (expected at {STAGE1})")

    import tempfile

    with tempfile.NamedTemporaryFile(
        "w", suffix=".mn", delete=False, encoding="utf-8"
    ) as tf:
        tf.write(source)
        tf.flush()
        path = tf.name
    try:
        result = subprocess.run(
            [str(STAGE1), "preprocess", path],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    finally:
        pathlib.Path(path).unlink(missing_ok=True)

    out = result.stdout
    if out.endswith("\n"):
        out = out[:-1]
    return out


def _golden_files() -> list[pathlib.Path]:
    return sorted(GOLDEN_DIR.glob("*.mn"))


# ---------------------------------------------------------------------------
# Hand-rolled fixtures. Each pair exercises one shape of the algorithm
# (block opener, dedent close, comma back-patch, continuation rewrite,
# fast path, mixed brace+colon) so a regression in any single arm shows
# up here even if no corpus golden happens to exercise it.
# ---------------------------------------------------------------------------

FIXTURES: list[tuple[str, str]] = [
    ("brace_only_passthrough", "fn main() {\n    print(1)\n}\n"),
    ("colon_fn_main", "fn main():\n    print(1)\n"),
    ("colon_if_else", "fn main():\n    if 1 == 1:\n        print(1)\n    else:\n        print(2)\n"),
    ("colon_struct", "struct Point:\n    x: Int\n    y: Int\n"),
    ("colon_enum", "enum Color:\n    Red\n    Green\n    Blue\n"),
    (
        "colon_match",
        "fn classify(c: Color) -> Int:\n"
        "    match c:\n"
        "        Red => { return 1 }\n"
        "        Green => { return 2 }\n"
        "        Blue => { return 3 }\n",
    ),
    ("colon_pass", "fn empty():\n    pass\n"),
    ("trailing_blank", "fn main():\n    pass\n\n"),
    ("comment_only_dedent", "fn main():\n    print(1)\n# tail comment\n"),
    (
        "mixed_brace_and_colon",
        "fn a() {\n    print(1)\n}\nfn b():\n    print(2)\n",
    ),
    # v5.17.0 Sh.A.1: multi-level dedent on `else:` continuation. The
    # outer `else:` at level 0 follows content at level 2 — both
    # preprocessors must close the inner if-block before emitting the
    # `} else {` form, otherwise the brace output has unmatched braces.
    (
        "multi_level_dedent_else",
        "fn f(a: Bool, b: Bool) -> Int:\n"
        "    if a:\n"
        "        if b:\n"
        "            return 1\n"
        "        else:\n"
        "            return 2\n"
        "    else:\n"
        "        return 3\n",
    ),
]


@pytest.mark.parametrize(
    "name,src",
    FIXTURES,
    ids=[name for name, _ in FIXTURES],
)
def test_fixture_matches_python(name: str, src: str) -> None:
    py = _indent_to_braces(src)
    c = _bootstrap_preprocess(src)
    assert py == c, (
        f"divergence on fixture {name!r}\n"
        f"--- python ---\n{py!r}\n"
        f"--- c ---\n{c!r}"
    )


# ---------------------------------------------------------------------------
# Corpus sweep. The same goldens used by ``scripts/test_native.py`` are
# the most realistic stress test — colon-form variants are produced by
# ``mapanare fmt --to-terse`` in the harness, which is itself
# v5.14.0's exhaustively-tested rewriter.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    _golden_files(),
    ids=lambda p: p.name,
)
def test_brace_form_passes_through(path: pathlib.Path) -> None:
    """Every brace-form golden should hit the fast path on both sides
    and emerge byte-identical."""
    src = path.read_text(encoding="utf-8")
    py = _indent_to_braces(src)
    c = _bootstrap_preprocess(src)
    assert py == c, f"divergence on brace-form {path.name}"


@pytest.mark.parametrize(
    "path",
    _golden_files(),
    ids=lambda p: p.name,
)
def test_colon_form_round_trip(path: pathlib.Path) -> None:
    """For every parseable golden, run ``--to-terse`` to get the colon
    form, then assert both preprocessors produce byte-identical output
    on the colon-form source."""
    src = path.read_text(encoding="utf-8")
    # Reuse the Python `to_terse` rewriter — same module that
    # tests/test_colon_blocks.py uses.
    from mapanare.format import to_terse

    terse = to_terse(src)
    py = _indent_to_braces(terse)
    c = _bootstrap_preprocess(terse)
    assert py == c, (
        f"divergence on colon-form {path.name}\n"
        f"--- python (first 200) ---\n{py[:200]!r}\n"
        f"--- c (first 200) ---\n{c[:200]!r}"
    )
