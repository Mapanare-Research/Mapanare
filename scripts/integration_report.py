#!/usr/bin/env python3
"""Generate RESULTS.md from pytest JUnit XML output.

Usage:
    python scripts/integration_report.py integration-results.xml tests/integration/RESULTS.md
    python scripts/integration_report.py  # defaults: integration-results.xml -> tests/integration/RESULTS.md
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

STAGES = ("emit", "llvm-as", "opt", "llc", "link", "run", "stdout")


def parse_junit_xml(xml_path: Path) -> list[dict]:
    """Parse JUnit XML and extract per-test results."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    results = []
    for suite in root.iter("testsuite"):
        for case in suite.iter("testcase"):
            name = case.get("name", "")
            # Extract test stem from parametrized name like "test_golden_pipeline[01_hello]"
            test_id = name
            if "[" in name and "]" in name:
                test_id = name[name.index("[") + 1 : name.index("]")]

            status = "PASS"
            detail = ""
            failed_stage = ""

            skip = case.find("skipped")
            fail = case.find("failure")
            error = case.find("error")

            if skip is not None:
                msg = skip.get("message", "")
                skip_type = skip.get("type", "")
                if skip_type == "pytest.xfail" or "xfail" in msg.lower():
                    status = "XFAIL"
                    detail = msg
                else:
                    status = "SKIP"
                    detail = msg
            elif fail is not None:
                status = "FAIL"
                detail = fail.get("message", "")[:200]
                # Extract failed stage from error message
                if "failed at '" in detail:
                    start = detail.index("failed at '") + len("failed at '")
                    end = detail.index("'", start)
                    failed_stage = detail[start:end]
            elif error is not None:
                status = "ERROR"
                detail = error.get("message", "")[:200]

            # For passed tests, all stages passed
            stage_results = {}
            if status == "PASS":
                stage_results = {s: "PASS" for s in STAGES}
            elif status == "XFAIL" and detail:
                # Mark stages based on xfail reason
                if "emit" in detail.lower():
                    stage_results = {"emit": "XFAIL"}
                elif "llvm-as" in detail.lower():
                    stage_results = {"emit": "PASS", "llvm-as": "XFAIL"}
                else:
                    stage_results = {"emit": "XFAIL"}
            elif failed_stage:
                for s in STAGES:
                    if s == failed_stage:
                        stage_results[s] = "FAIL"
                        break
                    stage_results[s] = "PASS"

            results.append(
                {
                    "name": test_id,
                    "status": status,
                    "detail": detail,
                    "failed_stage": failed_stage,
                    "stages": stage_results,
                }
            )

    return sorted(results, key=lambda r: r["name"])


def generate_report(results: list[dict], xml_path: Path) -> str:
    """Generate Markdown report from parsed results."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    xfailed = sum(1 for r in results if r["status"] == "XFAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    errored = sum(1 for r in results if r["status"] == "ERROR")

    lines = [
        "# Integration Test Results",
        "",
        f"Generated: {now}",
        f"Source: `{xml_path.name}`",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total tests | {total} |",
        f"| **Passed (end-to-end)** | **{passed}** |",
        f"| Failed | {failed} |",
        f"| Expected failures (xfail) | {xfailed} |",
        f"| Skipped (external resources) | {skipped} |",
        f"| Errors | {errored} |",
        "",
        f"**Pass rate: {passed}/{total} ({100*passed/total:.0f}%)**",
        "",
        "## Per-Test Results",
        "",
        "| Test | emit | llvm-as | opt | llc | link | run | stdout | Status |",
        "|------|------|---------|-----|-----|------|-----|--------|--------|",
    ]

    status_icon = {
        "PASS": "OK",
        "FAIL": "FAIL",
        "XFAIL": "XFAIL",
        "SKIP": "SKIP",
        "ERROR": "ERR",
    }

    for r in results:
        name = r["name"]
        status = r["status"]

        if status == "SKIP":
            cols = ["--"] * 7
        elif status == "PASS":
            cols = ["OK"] * 7
        else:
            cols = []
            for s in STAGES:
                if s in r["stages"]:
                    cols.append(r["stages"][s])
                else:
                    cols.append("--")

        row = f"| {name} | {' | '.join(cols)} | {status_icon.get(status, status)} |"
        lines.append(row)

    # Failure details section
    failures = [r for r in results if r["status"] in ("FAIL", "XFAIL")]
    if failures:
        lines.extend(
            [
                "",
                "## Failure Details",
                "",
            ]
        )
        for r in failures:
            lines.append(f"### {r['name']} ({r['status']})")
            lines.append("")
            if r["failed_stage"]:
                lines.append(f"**Failed at:** `{r['failed_stage']}`")
            if r["detail"]:
                lines.append(f"**Detail:** {r['detail'][:300]}")
            lines.append("")

    lines.extend(
        [
            "---",
            "",
            "Pipeline: `emit-llvm → llvm-as → opt -O2 → llc -filetype=obj → clang link → execute`",
            "",
            "Backend: Python bootstrap (`python -m mapanare emit-llvm`)",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    xml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("integration-results.xml")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("tests/integration/RESULTS.md")

    if not xml_path.exists():
        print(f"error: {xml_path} not found", file=sys.stderr)
        sys.exit(1)

    results = parse_junit_xml(xml_path)
    report = generate_report(results, xml_path)
    out_path.write_text(report)
    print(f"Wrote {out_path} ({len(results)} tests)")


if __name__ == "__main__":
    main()
