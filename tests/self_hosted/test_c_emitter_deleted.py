"""v4.54.0: Regression gate — emit_c.mn must not exist.

The self-hosted C emitter was deleted in v4.2.0 and formally closed as A9
in v4.54.0 (Path B). This test prevents accidental resurrection.
"""

from __future__ import annotations

import os

import pytest

EMIT_C_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "mapanare", "self", "emit_c.mn")


def test_emit_c_mn_does_not_exist():
    """mapanare/self/emit_c.mn must not exist (deleted in v4.2.0, A9 closed in v4.54.0)."""
    assert not os.path.exists(EMIT_C_PATH), (
        f"emit_c.mn was resurrected at {EMIT_C_PATH}. "
        "The self-hosted C emitter was intentionally deleted in v4.2.0. "
        "See docs/roadmap/v4/v4.54.0/DECISIONS.md for rationale."
    )
