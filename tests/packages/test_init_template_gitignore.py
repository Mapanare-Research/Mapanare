"""v5.44.1 Ps.12.B — locks the canonical init-template `.gitignore`.

Background. v5.44.0 shipped package-aware imports + `mn_modules/`
layout. The init template at
``mapanare/templates/init/default/.gitignore`` is what every
``mnc init``-created project starts from; v5.44.0 missed adding
``mn_modules/`` to the template defaults. v5.44.1 Ps.12 closes
that gap and locks the canonical exclude/include set so a future
edit doesn't silently regress.

Falsifiability. Removing ``mn_modules/`` (or any required pattern)
fails ``test_template_gitignore_required_patterns``. Adding
``mapanare.toml``, ``mapanare.lock``, or ``*.mn`` to the gitignore
fails ``test_template_gitignore_no_forbidden_patterns``. The
end-to-end test ensures ``init_project`` actually copies the
template file into the produced project — a refactor of the
init machinery that drops gitignore copying would surface here.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_GITIGNORE = REPO_ROOT / "mapanare" / "templates" / "init" / "default" / ".gitignore"

# Patterns that MUST appear in the template `.gitignore`.
REQUIRED_PATTERNS = (
    "mn_modules/",
    "__pycache__/",
    "*.pyc",
    "dist/",
    "*.ll",
    "*.o",
)

# Patterns that MUST NOT appear: lockfile + manifest are committed
# per package-management convention; `*.mn` excludes every Mapanare
# source file (catastrophic).
FORBIDDEN_PATTERNS = (
    "mapanare.toml",
    "mapanare.lock",
    "*.mn",
)


def _read_pattern_lines() -> list[str]:
    assert TEMPLATE_GITIGNORE.is_file(), (
        f"v5.44.1 Ps.12 requires {TEMPLATE_GITIGNORE} — "
        f"`mnc init`-created projects must default to excluding "
        f"`mn_modules/`."
    )
    return [
        line.strip()
        for line in TEMPLATE_GITIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_template_gitignore_excludes_mn_modules() -> None:
    """The load-bearing v5.44.1 Ps.12 invariant: `mn_modules/` excluded."""
    lines = _read_pattern_lines()
    assert "mn_modules/" in lines, (
        "v5.44.1 Ps.12: init template must exclude `mn_modules/` by "
        "default so freshly initialized projects don't commit installed "
        "packages."
    )


def test_template_gitignore_required_patterns() -> None:
    """Lock the canonical exclude set."""
    lines = _read_pattern_lines()
    missing = [p for p in REQUIRED_PATTERNS if p not in lines]
    assert not missing, f"init template `.gitignore` is missing required patterns: " f"{missing}"


def test_template_gitignore_no_forbidden_patterns() -> None:
    """Lock the canonical include set: lockfile, manifest, and source
    files are never excluded."""
    lines = _read_pattern_lines()
    forbidden_present = [p for p in FORBIDDEN_PATTERNS if p in lines]
    assert not forbidden_present, (
        f"init template `.gitignore` must NOT exclude: "
        f"{forbidden_present} — these are committed per "
        f"package-management convention."
    )


def test_init_creates_project_with_gitignore(tmp_path: Path) -> None:
    """End-to-end: `init_project` produces a project whose `.gitignore`
    matches the canonical template (template-name placeholder
    substituted, `mn_modules/` present).
    """
    from stdlib.pkg import init_project

    proj_dir = tmp_path / "myproj"
    init_project(str(proj_dir), name="myproj")
    proj_gitignore = proj_dir / ".gitignore"
    assert proj_gitignore.is_file()
    text = proj_gitignore.read_text(encoding="utf-8")
    assert "mn_modules/" in text
    assert "__pycache__/" in text
    # `{{NAME}}` placeholder substituted with the project name.
    assert "myproj" in text
    assert "{{NAME}}" not in text
    # Forbidden patterns never reach the produced project either.
    for forbidden in FORBIDDEN_PATTERNS:
        # Match whole-line so a pattern like `*.mn` doesn't false-match
        # the `myproj.mn` filename if someone adds that to the template.
        assert forbidden not in text.splitlines(), (
            f"init-produced .gitignore unexpectedly contains " f"forbidden pattern {forbidden!r}"
        )
