#!/usr/bin/env python3
"""v5.36.0 Phase 0 / Phase 1 — RFC 8259 corpus runner.

Builds a per-run .mn driver that concatenates the JSON stdlib module +
a main() that walks a hardcoded manifest of fixture paths and prints
one line per fixture in the form:

    <category>:<basename>:<expected>:<actual>

where:
  category = y | n | i  (from filename prefix)
  expected = PASS (y) | FAIL (n) | EITHER (i)
  actual   = PASS | FAIL  (whether decode() returned Ok)

Why no argv: Python bootstrap compiler emits @main() directly and does
not run __mn_argv_init. To avoid 318 separate compile cycles we embed
the manifest path as a literal string constant and have the driver read
it via __mn_file_read. The driver iterates the manifest, reads each
fixture, calls decode(), prints the result. One compile, one run.

Usage:
    python3 scripts/run_json_corpus.py
        --fixtures stdlib/json/tests/fixtures/rfc8259
        --json-source stdlib/encoding/json.mn
        --out docs/roadmap/v5/v5.36.0/RFC_AUDIT.md
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DRIVER_TAIL = r"""

// ---------- corpus driver appended to json.mn ----------
//
// Single-fixture per invocation. Reads the fixture path from a fixed
// control file (path embedded at build time as __FIXTURE_PATH_FILE__).
// Writes the result to a fixed result file. Python harness writes one
// path to the control file, runs the binary, reads the result; loops.
// Per-fixture isolation means parser SEGV terminates only that one
// invocation — the next iteration starts fresh.

extern "C" fn __mn_file_read(path: String) -> String
extern "C" fn __mn_file_write(path: String, content: String) -> Int

fn main() -> Int {
    let fixture_path_file: String = "__FIXTURE_PATH_FILE__"
    let result_file: String = "__RESULT_FILE__"
    let path: String = __mn_file_read(fixture_path_file)
    // Strip trailing newline if present.
    let mut clean_path: String = path
    if len(path) > 0 {
        let last: String = path.substr(len(path) - 1, 1)
        if last == "\n" { clean_path = path.substr(0, len(path) - 1) }
    }
    print("clen=" + str(len(clean_path)) + "\n")
    let content: String = __mn_file_read(clean_path)
    print("rlen=" + str(len(content)) + "\n")
    let dr: Result<JsonValue, JsonError> = decode(content)
    // v5.x bootstrap drop-glue: arm bodies must end with a print() statement
    // — write before print prevents a SEGV in match cleanup. Discovered by
    // bisection at v5.36.0 Phase 0; the SEGV is suppressed when arm body's
    // last statement is a print(), so put the print last.
    match dr {
        Ok(_) => {
            let _w: Int = __mn_file_write(result_file, "PASS\n")
            print("ok\n")
        },
        Err(_) => {
            let _w: Int = __mn_file_write(result_file, "FAIL\n")
            print("err\n")
        }
    }
    return 0
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--fixtures",
        default=str(REPO_ROOT / "stdlib" / "json" / "tests" / "fixtures" / "rfc8259"),
    )
    ap.add_argument(
        "--json-source",
        default=str(REPO_ROOT / "stdlib" / "encoding" / "json.mn"),
    )
    ap.add_argument(
        "--string-utils-source",
        default=str(REPO_ROOT / "stdlib" / "text" / "string_utils.mn"),
    )
    ap.add_argument("--out", default=None, help="Path for RFC_AUDIT.md (optional)")
    ap.add_argument("--keep-temp", action="store_true", help="Keep /tmp/json_corpus_*")
    ns = ap.parse_args()

    fixtures_dir = Path(ns.fixtures).resolve()
    if not fixtures_dir.is_dir() or not list(fixtures_dir.glob("*.json")):
        # v5.36.0: fixtures are gitignored; clone-on-demand from
        # nst/JSONTestSuite. The directory is `.gitignore`d so this
        # populates the local working tree without polluting the repo.
        print(f"[corpus] fixtures missing at {fixtures_dir}; cloning JSONTestSuite...")
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        clone_dst = Path(tempfile.mkdtemp(prefix="jts_clone_"))
        rc = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "https://github.com/nst/JSONTestSuite",
                str(clone_dst),
            ],
            capture_output=True,
            text=True,
        )
        if rc.returncode != 0:
            sys.stderr.write(rc.stderr)
            sys.exit("git clone failed; check network or run with prepopulated --fixtures dir")
        for p in (clone_dst / "test_parsing").glob("*.json"):
            shutil.copy(p, fixtures_dir / p.name)
        # Copy the license too so users see attribution if they inspect.
        shutil.copy(clone_dst / "LICENSE", fixtures_dir / "LICENSE")
        shutil.rmtree(clone_dst, ignore_errors=True)
        print(f"[corpus] vendored {len(list(fixtures_dir.glob('*.json')))} fixtures")

    fixture_paths = sorted(fixtures_dir.glob("*.json"))
    if not fixture_paths:
        sys.exit(f"no .json fixtures in {fixtures_dir}")

    # Build driver (compile once)
    workdir = Path(tempfile.mkdtemp(prefix="json_corpus_"))
    fixture_path_file = workdir / "fixture.txt"
    result_file = workdir / "result.txt"

    string_utils_src = Path(ns.string_utils_source).read_text()
    json_src = Path(ns.json_source).read_text()
    json_src = "\n".join(
        line for line in json_src.splitlines() if line.strip() != "usa text::string_utils"
    )
    driver_tail = DRIVER_TAIL.replace("__FIXTURE_PATH_FILE__", str(fixture_path_file)).replace(
        "__RESULT_FILE__", str(result_file)
    )
    driver_src = string_utils_src + "\n\n" + json_src + "\n\n" + driver_tail

    driver_mn = workdir / "driver.mn"
    driver_mn.write_text(driver_src)

    driver_bin = workdir / "driver"
    print(f"[corpus] building driver ({len(driver_src):,} chars)...")
    rc = subprocess.run(
        [
            sys.executable,
            "-m",
            "mapanare",
            "build",
            str(driver_mn),
            "-o",
            str(driver_bin),
        ],
        capture_output=True,
        text=True,
    )
    if rc.returncode != 0 or not driver_bin.exists():
        sys.stderr.write(rc.stderr)
        sys.stderr.write(rc.stdout)
        sys.exit("build failed")

    # Loop: one invocation per fixture. Crash → CRASH outcome.
    rt_lines: list[str] = []
    print(f"[corpus] running driver against {len(fixture_paths)} fixtures (one inv each)...")
    crashed: set[str] = set()
    for idx, p in enumerate(fixture_paths):
        if (idx + 1) % 50 == 0:
            print(f"[corpus]   {idx + 1}/{len(fixture_paths)}...")
        fixture_path_file.write_text(str(p) + "\n")
        if result_file.exists():
            result_file.unlink()
        cat = p.name[0] if p.name and p.name[0] in "yni" else "?"
        expected = {"y": "PASS", "n": "FAIL", "i": "EITHER"}.get(cat, "EITHER")
        run = subprocess.run([str(driver_bin)], capture_output=True, text=True, timeout=20)
        if run.returncode != 0 or not result_file.exists():
            crashed.add(p.name)
            rt_lines.append(f"{cat}:{p.name}:{expected}:CRASH")
            continue
        actual = result_file.read_text().strip()
        if actual not in ("PASS", "FAIL"):
            crashed.add(p.name)
            rt_lines.append(f"{cat}:{p.name}:{expected}:CRASH")
        else:
            rt_lines.append(f"{cat}:{p.name}:{expected}:{actual}")

    # Parse final results.
    results: list[dict] = []
    by_outcome: Counter[str] = Counter()
    for line in rt_lines:
        parts = line.split(":")
        if len(parts) != 4:
            continue
        cat, name, expected, actual = parts
        if actual == "CRASH":
            outcome = "CRASH"
        else:
            outcome = _outcome(expected, actual)
        results.append(
            {"cat": cat, "name": name, "expected": expected, "actual": actual, "outcome": outcome}
        )
        by_outcome[outcome] += 1

    # Summary
    print("\n[corpus] summary:")
    for k in ("CONFORM", "DEVIATE_ACCEPT", "DEVIATE_REJECT", "IMPL", "CRASH"):
        print(f"  {k:<18} {by_outcome.get(k, 0):>4}")
    print(f"  {'TOTAL':<18} {sum(by_outcome.values()):>4}")

    if ns.out:
        out = Path(ns.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_render_audit(results, by_outcome))
        print(f"[corpus] wrote {out} ({out.stat().st_size:,} bytes)")

    if not ns.keep_temp:
        shutil.rmtree(workdir, ignore_errors=True)

    return 0


def _outcome(expected: str, actual: str) -> str:
    if expected == "EITHER":
        return "IMPL"
    if expected == actual:
        return "CONFORM"
    if expected == "PASS" and actual == "FAIL":
        return "DEVIATE_REJECT"  # we reject what RFC requires accepting
    return "DEVIATE_ACCEPT"  # we accept what RFC requires rejecting


def _render_audit(results: list[dict], by_outcome: Counter[str]) -> str:
    out: list[str] = []
    out.append("# RFC 8259 corpus audit — v5.36.0 baseline")
    out.append("")
    out.append("Source corpus: nst/JSONTestSuite (vendored at")
    out.append("`stdlib/json/tests/fixtures/rfc8259/`).")
    out.append("")
    out.append("Categories (filename prefix):")
    out.append("  - `y_*` — must accept (RFC valid)")
    out.append("  - `n_*` — must reject (RFC invalid)")
    out.append("  - `i_*` — implementation-defined (either accept or reject")
    out.append("    is acceptable; we pin actual behavior here)")
    out.append("")
    out.append("Outcome key:")
    out.append("  - `CONFORM`        — parser matches RFC requirement")
    out.append("  - `DEVIATE_REJECT` — parser rejects something RFC requires accepting")
    out.append("  - `DEVIATE_ACCEPT` — parser accepts something RFC requires rejecting")
    out.append("  - `IMPL`           — i_* fixture; behavior pinned (not graded)")
    out.append("  - `CRASH`          — parser SEGV/UB on this fixture (must close)")
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append("| Outcome | Count |")
    out.append("|---|---:|")
    for k in ("CONFORM", "DEVIATE_REJECT", "DEVIATE_ACCEPT", "IMPL", "CRASH"):
        out.append(f"| {k} | {by_outcome.get(k, 0)} |")
    out.append(f"| **TOTAL** | **{sum(by_outcome.values())}** |")
    out.append("")
    out.append("## Phase 1 backlog (DEVIATE_* / CRASH — must close before v5.36.0 ships)")
    out.append("")
    backlog = [r for r in results if r["outcome"] in ("DEVIATE_REJECT", "DEVIATE_ACCEPT", "CRASH")]
    if not backlog:
        out.append("_None — parser is RFC 8259 conformant + crash-free._")
    else:
        out.append("| Outcome | Fixture | Expected | Actual |")
        out.append("|---|---|---|---|")
        for r in sorted(backlog, key=lambda r: (r["outcome"], r["name"])):
            out.append(f"| {r['outcome']} | `{r['name']}` | {r['expected']} | {r['actual']} |")
    out.append("")
    out.append("## i_* — implementation-defined behavior (pinned)")
    out.append("")
    out.append("| Fixture | Actual |")
    out.append("|---|---|")
    for r in sorted([r for r in results if r["cat"] == "i"], key=lambda r: r["name"]):
        out.append(f"| `{r['name']}` | {r['actual']} |")
    out.append("")
    out.append("## Full per-fixture results")
    out.append("")
    out.append("<details>")
    out.append("<summary>318 entries</summary>")
    out.append("")
    out.append("| Cat | Fixture | Expected | Actual | Outcome |")
    out.append("|---|---|---|---|---|")
    for r in sorted(results, key=lambda r: (r["cat"], r["name"])):
        out.append(
            f"| {r['cat']} | `{r['name']}` | {r['expected']} | {r['actual']} | {r['outcome']} |"
        )
    out.append("")
    out.append("</details>")
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
