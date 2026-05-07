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

from mapanare.parser import _indent_to_braces, _rewrite_arm_stmt_shorthand


def _python_preprocess(source: str) -> str:
    """v5.48.1 Te.3.D.4.6: full Python preprocessor pipeline.

    Mirrors what `mapanare/parser.py::parse` runs and what the
    self-host `run_preprocess` runs on the C side: first
    `_indent_to_braces` then `_rewrite_arm_stmt_shorthand`. The
    cross-bootstrap byte-identity contract is asserted on the full
    pipeline output.
    """
    return _rewrite_arm_stmt_shorthand(_indent_to_braces(source))

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
    # v5.48.1 Te.3.D.4.6: single-line statement-block colon body
    # (positive). Each new accepted head shape gets one fixture. The
    # byte-identity contract is asserted against the full pipeline
    # (_indent_to_braces + _rewrite_arm_stmt_shorthand on Python side;
    # __mn_indent_to_braces + __mn_rewrite_arm_stmt_shorthand via
    # `mnc-stage1 preprocess` on the C side).
    (
        "v5481_inline_if",
        "fn f(x: Int) -> Int:\n    if x > 0: return 1\n    return 0\n",
    ),
    (
        "v5481_inline_si",
        "fn f(x: Int) -> Int:\n    si x > 0: da 1\n    da 0\n",
    ),
    (
        "v5481_inline_while",
        "fn f():\n    while ready(): step()\n",
    ),
    (
        "v5481_inline_mien",
        "fn f():\n    mien ready(): step()\n",
    ),
    (
        "v5481_inline_for",
        "fn f(xs: List<Int>):\n    for x in xs: print(x)\n",
    ),
    (
        "v5481_inline_cada",
        "fn f(xs: List<Int>):\n    cada x in xs: print(x)\n",
    ),
    (
        "v5481_inline_fn_zero_arg",
        "fn main(): print(1)\n",
    ),
    (
        "v5481_inline_fn_zero_arg_ret",
        "fn pi() -> Float: return 3.14\n",
    ),
    (
        "v5481_inline_pub_fn",
        "pub fn ping(): print(1)\n",
    ),
    (
        "v5481_inline_async_fn",
        "async fn run(): print(1)\n",
    ),
    # v5.48.1 single-line continuation body
    (
        "v5481_inline_else",
        "fn f(x: Int) -> Int:\n    if x > 0:\n        return 1\n    else: return 0\n",
    ),
    (
        "v5481_inline_sino",
        "fn f(x: Int) -> Int:\n    si x > 0:\n        da 1\n    sino: da 0\n",
    ),
    (
        "v5481_inline_else_if",
        "fn f(x: Int) -> Int:\n    if x > 0:\n        return 1\n    else if x < 0: return -1\n    return 0\n",
    ),
    (
        "v5481_inline_sino_si",
        "fn f(x: Int) -> Int:\n    si x > 0:\n        da 1\n    sino si x < 0: da -1\n    da 0\n",
    ),
    # v5.48.1 match-arm statement shorthand — all 7 keywords
    (
        "v5481_arm_short_return",
        "fn f(e: Expr) -> Int:\n    match e:\n        IntLit(n) => return n\n        _ => return 0\n",
    ),
    (
        "v5481_arm_short_da",
        "fn f(e: Expr) -> Int:\n    match e:\n        IntLit(n) => da n\n        _ => da 0\n",
    ),
    (
        "v5481_arm_short_break",
        "fn f():\n    while ready():\n        match e:\n            X => break\n            _ => sigue\n",
    ),
    (
        "v5481_arm_short_sal",
        "fn f():\n    while ready():\n        match e:\n            X => sal\n            _ => sigue\n",
    ),
    (
        "v5481_arm_short_continue",
        "fn f():\n    while ready():\n        match e:\n            X => continue\n            _ => break\n",
    ),
    (
        "v5481_arm_short_sigue",
        "fn f():\n    while ready():\n        match e:\n            X => sigue\n            _ => sal\n",
    ),
    (
        "v5481_arm_short_pass",
        "fn f(e: Expr):\n    match e:\n        X => pass\n        _ => pass\n",
    ),
    # v5.48.1 negative shapes — must NOT migrate / must NOT trigger
    (
        "v5481_neg_let_with_type_ann",
        "fn f():\n    let x: Int = 5\n    print(x)\n",
    ),
    (
        "v5481_neg_struct_literal",
        "fn f():\n    let p = Point { x: 1, y: 2 }\n",
    ),
    (
        "v5481_neg_namespace_op",
        "fn f():\n    let r = X::Y::Z\n    print(r)\n",
    ),
    (
        "v5481_neg_generic_with_colon_open",
        "fn max<T: Ord>(a: T, b: T) -> T {\n    return a\n}\n",
    ),
    # v5.48.1 Te.3.D.5.1: `{` inside a string literal must NOT
    # disable single-line detection. Real shape from
    # mapanare/self/lexer.mn — `if ch == "{": stmt` was preserved
    # as colon form by the unguarded `'{' not in content` check,
    # then rejected by the LALR parser. Both Python and C must mask
    # strings before the guard.
    (
        "v5481_brace_in_string_literal",
        "fn classify(ch: String) -> String:\n    if ch == \"{\": return \"LBRACE\"\n    return \"OTHER\"\n",
    ),
]


@pytest.mark.parametrize(
    "name,src",
    FIXTURES,
    ids=[name for name, _ in FIXTURES],
)
def test_fixture_matches_python(name: str, src: str) -> None:
    py = _python_preprocess(src)
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
    py = _python_preprocess(src)
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
    py = _python_preprocess(terse)
    c = _bootstrap_preprocess(terse)
    assert py == c, (
        f"divergence on colon-form {path.name}\n"
        f"--- python (first 200) ---\n{py[:200]!r}\n"
        f"--- c (first 200) ---\n{c[:200]!r}"
    )
