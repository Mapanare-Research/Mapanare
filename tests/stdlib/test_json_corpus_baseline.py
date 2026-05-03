"""v5.36.0 Js.5 — RFC 8259 corpus regression gate.

Runs `scripts/run_json_corpus.py` end-to-end and asserts the JSON
parser is RFC 8259 conformant on the vendored nst/JSONTestSuite
corpus. This is the load-bearing test for Js.1 (parser strictness)
— if a future change re-introduces the leading-zero / unescaped-
control-char / deep-nesting bugs, this test will fail.

The corpus runner clones nst/JSONTestSuite into the gitignored
`stdlib/json/tests/fixtures/rfc8259/` on first run if missing.
Subsequent runs reuse the cached copy.

Skipped automatically in environments without git/network. The
slow marker keeps it out of fast pytest passes.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNNER = REPO_ROOT / "scripts" / "run_json_corpus.py"

# Baseline pinned at v5.36.0 ship: 283 CONFORM + 35 IMPL + 0
# DEVIATE_* + 0 CRASH = 318 fixtures total. A regression that
# re-introduces a leading-zero or unescaped-control-char bug
# moves a fixture from CONFORM → DEVIATE_ACCEPT and fails this
# test loudly.
EXPECTED_MIN_CONFORM = 283
EXPECTED_MAX_DEVIATE = 0
EXPECTED_MAX_CRASH = 0


@pytest.mark.slow
def test_rfc8259_corpus_baseline() -> None:
    if not shutil.which("git"):
        pytest.skip("git not available — corpus runner needs it for clone-on-demand")
    if not RUNNER.exists():
        pytest.skip(f"runner missing: {RUNNER}")

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "RFC_AUDIT.md"
        rc = subprocess.run(
            [sys.executable, str(RUNNER), "--out", str(out)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if rc.returncode != 0:
            pytest.fail(f"corpus runner failed:\n{rc.stderr}\n{rc.stdout}")
        text = out.read_text()

    by_outcome = _extract_summary(text)
    assert by_outcome["CONFORM"] >= EXPECTED_MIN_CONFORM, (
        f"CONFORM regressed: got {by_outcome['CONFORM']}, " f"expected ≥ {EXPECTED_MIN_CONFORM}"
    )
    assert by_outcome["DEVIATE_REJECT"] <= EXPECTED_MAX_DEVIATE, (
        f"DEVIATE_REJECT regressed: parser now rejects "
        f"{by_outcome['DEVIATE_REJECT']} valid RFC 8259 inputs"
    )
    assert by_outcome["DEVIATE_ACCEPT"] <= EXPECTED_MAX_DEVIATE, (
        f"DEVIATE_ACCEPT regressed: parser now accepts "
        f"{by_outcome['DEVIATE_ACCEPT']} invalid RFC 8259 inputs"
    )
    assert by_outcome["CRASH"] <= EXPECTED_MAX_CRASH, (
        f"CRASH regressed: parser now crashes on "
        f"{by_outcome['CRASH']} fixtures (was 0 at v5.36.0 ship)"
    )


def _extract_summary(text: str) -> dict[str, int]:
    """Pull the CONFORM/DEVIATE/IMPL/CRASH counts from RFC_AUDIT.md."""
    out: dict[str, int] = {
        "CONFORM": 0,
        "DEVIATE_REJECT": 0,
        "DEVIATE_ACCEPT": 0,
        "IMPL": 0,
        "CRASH": 0,
    }
    for line in text.splitlines():
        for key in out:
            if line.startswith(f"| {key} |"):
                # Format: "| CONFORM | 283 |"
                parts = [p.strip() for p in line.strip("|").split("|")]
                if len(parts) >= 2 and parts[1].isdigit():
                    out[key] = int(parts[1])
    return out


def test_extract_summary_parses_audit_format() -> None:
    """Self-test for the summary parser — guards against pretty-print drift."""
    sample = """## Summary

| Outcome | Count |
|---|---:|
| CONFORM | 283 |
| DEVIATE_REJECT | 0 |
| DEVIATE_ACCEPT | 0 |
| IMPL | 35 |
| CRASH | 0 |
| **TOTAL** | **318** |
"""
    counts = _extract_summary(sample)
    assert counts == {
        "CONFORM": 283,
        "DEVIATE_REJECT": 0,
        "DEVIATE_ACCEPT": 0,
        "IMPL": 35,
        "CRASH": 0,
    }
