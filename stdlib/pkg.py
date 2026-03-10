"""Mapanare package manager -- manifest parsing, dependency resolution, and package operations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# mapanare.toml manifest format
# ---------------------------------------------------------------------------


@dataclass
class Dependency:
    """A single package dependency."""

    name: str
    version: str  # semver constraint, e.g. ">=1.0.0,<2.0.0" or "*"
    git: str | None = None  # git URL override
    branch: str | None = None  # git branch (default: main)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"version": self.version}
        if self.git:
            d["git"] = self.git
        if self.branch:
            d["branch"] = self.branch
        return d

    @classmethod
    def from_dict(cls, name: str, value: Any) -> Dependency:
        if isinstance(value, str):
            return cls(name=name, version=value)
        if isinstance(value, dict):
            return cls(
                name=name,
                version=value.get("version", "*"),
                git=value.get("git"),
                branch=value.get("branch"),
            )
        raise ManifestError(f"invalid dependency format for '{name}': {value}")


@dataclass
class MapanareManifest:
    """Parsed mapanare.toml project manifest."""

    name: str
    version: str
    description: str = ""
    authors: list[str] = field(default_factory=list)
    license: str = ""
    mapanare_version: str = ">=0.2.0"
    dependencies: dict[str, Dependency] = field(default_factory=dict)
    dev_dependencies: dict[str, Dependency] = field(default_factory=dict)
    entry: str = "main.mn"

    def to_toml(self) -> str:
        """Serialize manifest to TOML string."""
        lines: list[str] = []
        lines.append("[package]")
        lines.append(f'name = "{self.name}"')
        lines.append(f'version = "{self.version}"')
        if self.description:
            lines.append(f'description = "{self.description}"')
        if self.authors:
            author_list = ", ".join(f'"{a}"' for a in self.authors)
            lines.append(f"authors = [{author_list}]")
        if self.license:
            lines.append(f'license = "{self.license}"')
        lines.append(f'mapanare_version = "{self.mapanare_version}"')
        lines.append(f'entry = "{self.entry}"')

        if self.dependencies:
            lines.append("")
            lines.append("[dependencies]")
            for dep_name, dep in self.dependencies.items():
                if dep.git:
                    parts = [f'version = "{dep.version}"', f'git = "{dep.git}"']
                    if dep.branch:
                        parts.append(f'branch = "{dep.branch}"')
                    lines.append(f"{dep_name} = {{ {', '.join(parts)} }}")
                else:
                    lines.append(f'{dep_name} = "{dep.version}"')

        if self.dev_dependencies:
            lines.append("")
            lines.append("[dev-dependencies]")
            for dep_name, dep in self.dev_dependencies.items():
                if dep.git:
                    parts = [f'version = "{dep.version}"', f'git = "{dep.git}"']
                    if dep.branch:
                        parts.append(f'branch = "{dep.branch}"')
                    lines.append(f"{dep_name} = {{ {', '.join(parts)} }}")
                else:
                    lines.append(f'{dep_name} = "{dep.version}"')

        lines.append("")
        return "\n".join(lines)


class ManifestError(Exception):
    """Error parsing or validating an mapanare.toml manifest."""


# Minimal TOML parser for mapanare.toml (supports only what we need)
def _parse_toml_value(raw: str) -> Any:
    """Parse a single TOML value (string, list, inline table)."""
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        items: list[Any] = []
        for item in _split_top_level(inner, ","):
            items.append(_parse_toml_value(item.strip()))
        return items
    if raw.startswith("{") and raw.endswith("}"):
        inner = raw[1:-1].strip()
        if not inner:
            return {}
        result: dict[str, Any] = {}
        for pair in _split_top_level(inner, ","):
            pair = pair.strip()
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            result[k.strip()] = _parse_toml_value(v.strip())
        return result
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _split_top_level(s: str, delimiter: str) -> list[str]:
    """Split string by delimiter, respecting nesting of [], {}, and quotes."""
    parts: list[str] = []
    depth = 0
    in_string = False
    quote_char = ""
    current: list[str] = []
    for ch in s:
        if in_string:
            current.append(ch)
            if ch == quote_char:
                in_string = False
        elif ch in ('"', "'"):
            in_string = True
            quote_char = ch
            current.append(ch)
        elif ch in ("[", "{"):
            depth += 1
            current.append(ch)
        elif ch in ("]", "}"):
            depth -= 1
            current.append(ch)
        elif ch == delimiter and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def parse_manifest(content: str) -> MapanareManifest:
    """Parse an mapanare.toml manifest string into a MapanareManifest."""
    sections: dict[str, dict[str, Any]] = {}
    current_section = ""

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Section header
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            current_section = m.group(1).strip()
            if current_section not in sections:
                sections[current_section] = {}
            continue
        # Key = value
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            sections.setdefault(current_section, {})[key] = _parse_toml_value(value)

    pkg = sections.get("package", {})
    if "name" not in pkg:
        raise ManifestError("missing required field: [package] name")
    if "version" not in pkg:
        raise ManifestError("missing required field: [package] version")

    deps: dict[str, Dependency] = {}
    for dep_name, dep_val in sections.get("dependencies", {}).items():
        deps[dep_name] = Dependency.from_dict(dep_name, dep_val)

    dev_deps: dict[str, Dependency] = {}
    for dep_name, dep_val in sections.get("dev-dependencies", {}).items():
        dev_deps[dep_name] = Dependency.from_dict(dep_name, dep_val)

    authors_raw = pkg.get("authors", [])
    if isinstance(authors_raw, str):
        authors_raw = [authors_raw]

    return MapanareManifest(
        name=pkg["name"],
        version=pkg["version"],
        description=pkg.get("description", ""),
        authors=authors_raw,
        license=pkg.get("license", ""),
        mapanare_version=pkg.get("mapanare_version", ">=0.2.0"),
        dependencies=deps,
        dev_dependencies=dev_deps,
        entry=pkg.get("entry", "main.mn"),
    )


def load_manifest(project_dir: str) -> MapanareManifest:
    """Load mapanare.toml from a project directory."""
    path = os.path.join(project_dir, "mapanare.toml")
    if not os.path.isfile(path):
        raise ManifestError(f"mapanare.toml not found in {project_dir}")
    with open(path, encoding="utf-8") as f:
        return parse_manifest(f.read())


def save_manifest(manifest: MapanareManifest, project_dir: str) -> None:
    """Save manifest to mapanare.toml in the project directory."""
    path = os.path.join(project_dir, "mapanare.toml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(manifest.to_toml())


# ---------------------------------------------------------------------------
# mapanare.lock lock file format
# ---------------------------------------------------------------------------


@dataclass
class LockedDependency:
    """A resolved and locked dependency."""

    name: str
    version: str
    git: str
    commit: str  # pinned commit hash
    integrity: str  # sha256 of the cloned content at commit

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "version": self.version,
            "git": self.git,
            "commit": self.commit,
            "integrity": self.integrity,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LockedDependency:
        return cls(
            name=d["name"],
            version=d["version"],
            git=d["git"],
            commit=d["commit"],
            integrity=d.get("integrity", ""),
        )


@dataclass
class LockFile:
    """Parsed mapanare.lock file."""

    lockfile_version: int = 1
    packages: list[LockedDependency] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialize lock file to JSON string."""
        data = {
            "lockfile_version": self.lockfile_version,
            "packages": [p.to_dict() for p in self.packages],
        }
        return json.dumps(data, indent=2) + "\n"

    @classmethod
    def from_json(cls, content: str) -> LockFile:
        """Parse a lock file from JSON string."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise LockFileError(f"invalid mapanare.lock JSON: {e}") from e

        return cls(
            lockfile_version=data.get("lockfile_version", 1),
            packages=[LockedDependency.from_dict(p) for p in data.get("packages", [])],
        )

    def find(self, name: str) -> LockedDependency | None:
        """Find a locked dependency by name."""
        for pkg in self.packages:
            if pkg.name == name:
                return pkg
        return None


class LockFileError(Exception):
    """Error parsing or writing mapanare.lock."""


def load_lockfile(project_dir: str) -> LockFile:
    """Load mapanare.lock from a project directory. Returns empty if not found."""
    path = os.path.join(project_dir, "mapanare.lock")
    if not os.path.isfile(path):
        return LockFile()
    with open(path, encoding="utf-8") as f:
        return LockFile.from_json(f.read())


def save_lockfile(lockfile: LockFile, project_dir: str) -> None:
    """Save lock file to mapanare.lock in the project directory."""
    path = os.path.join(project_dir, "mapanare.lock")
    with open(path, "w", encoding="utf-8") as f:
        f.write(lockfile.to_json())


# ---------------------------------------------------------------------------
# mapa install <package> (git-based stub)
# ---------------------------------------------------------------------------

MAPANARE_PACKAGES_DIR = "mapanare_packages"


def _default_git_url(package_name: str) -> str:
    """Derive default git URL from package name (convention-based)."""
    return f"https://github.com/Mapanare-Research/{package_name}.git"


def _compute_integrity(directory: str) -> str:
    """Compute SHA-256 integrity hash of all .mn files in a directory."""
    h = hashlib.sha256()
    for root, _dirs, files in sorted(os.walk(directory)):
        for fname in sorted(files):
            if fname.endswith(".mn") or fname == "mapanare.toml":
                fpath = os.path.join(root, fname)
                with open(fpath, "rb") as f:
                    h.update(f.read())
    return f"sha256:{h.hexdigest()}"


def _get_git_commit(repo_dir: str) -> str:
    """Get the current HEAD commit hash of a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def install_package(
    package_name: str,
    project_dir: str,
    git_url: str | None = None,
    branch: str | None = None,
    version: str = "*",
) -> LockedDependency:
    """Install a package by cloning its git repo into mapanare_packages/.

    This is a git-based stub: packages are simply git repos cloned locally.
    """
    packages_dir = os.path.join(project_dir, MAPANARE_PACKAGES_DIR)
    os.makedirs(packages_dir, exist_ok=True)

    pkg_dir = os.path.join(packages_dir, package_name)
    url = git_url or _default_git_url(package_name)
    effective_branch = branch or "main"

    if os.path.isdir(pkg_dir):
        # Update existing
        try:
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=pkg_dir,
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise PackageError(f"failed to update package '{package_name}': {e}") from e
    else:
        # Clone new
        cmd = ["git", "clone", "--depth", "1", "--branch", effective_branch, url, pkg_dir]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise PackageError(
                f"failed to install package '{package_name}' from {url}: {e.stderr}"
            ) from e
        except FileNotFoundError:
            raise PackageError("git is not installed or not in PATH")

    commit = _get_git_commit(pkg_dir)
    integrity = _compute_integrity(pkg_dir)

    locked = LockedDependency(
        name=package_name,
        version=version,
        git=url,
        commit=commit,
        integrity=integrity,
    )

    # Update manifest
    manifest_path = os.path.join(project_dir, "mapanare.toml")
    if os.path.isfile(manifest_path):
        manifest = load_manifest(project_dir)
        manifest.dependencies[package_name] = Dependency(
            name=package_name,
            version=version,
            git=git_url,
            branch=branch,
        )
        save_manifest(manifest, project_dir)

    # Update lock file
    lockfile = load_lockfile(project_dir)
    existing = lockfile.find(package_name)
    if existing:
        lockfile.packages.remove(existing)
    lockfile.packages.append(locked)
    save_lockfile(lockfile, project_dir)

    return locked


def uninstall_package(package_name: str, project_dir: str) -> None:
    """Remove an installed package."""
    pkg_dir = os.path.join(project_dir, MAPANARE_PACKAGES_DIR, package_name)
    if os.path.isdir(pkg_dir):
        shutil.rmtree(pkg_dir)

    # Update manifest
    manifest_path = os.path.join(project_dir, "mapanare.toml")
    if os.path.isfile(manifest_path):
        manifest = load_manifest(project_dir)
        manifest.dependencies.pop(package_name, None)
        save_manifest(manifest, project_dir)

    # Update lock file
    lockfile = load_lockfile(project_dir)
    existing = lockfile.find(package_name)
    if existing:
        lockfile.packages.remove(existing)
        save_lockfile(lockfile, project_dir)


class PackageError(Exception):
    """Error during package install/uninstall."""


# ---------------------------------------------------------------------------
# mapa publish stub (docs only — not yet functional)
# ---------------------------------------------------------------------------

PUBLISH_HELP = """\
mapa publish -- Publish a Mapanare package to the registry.

STATUS: This command is not yet implemented. The Mapanare package registry
is planned for Phase 7.2.

When available, `mapanare publish` will:
  1. Read mapanare.toml to get package metadata
  2. Validate the package structure
  3. Build a distributable archive
  4. Upload to the Mapanare package registry at mapanare.dev/packages

For now, packages are distributed via git repositories.
To share a package:
  1. Push your project to a git hosting service (GitHub, GitLab, etc.)
  2. Others can install it with: mapa install <name> --git <url>

See: https://mapanare.dev/docs/packages (coming soon)
"""


def cmd_publish_stub() -> str:
    """Return help text for the not-yet-implemented publish command."""
    return PUBLISH_HELP


# ---------------------------------------------------------------------------
# CLI init helper
# ---------------------------------------------------------------------------


def init_project(project_dir: str, name: str | None = None) -> MapanareManifest:
    """Initialize a new Mapanare project with mapanare.toml."""
    if name is None:
        name = os.path.basename(os.path.abspath(project_dir))

    manifest = MapanareManifest(
        name=name,
        version="0.1.0",
        description="",
        license="MIT",
    )

    os.makedirs(project_dir, exist_ok=True)
    save_manifest(manifest, project_dir)

    # Create main.ax if it doesn't exist
    main_path = os.path.join(project_dir, "main.mn")
    if not os.path.isfile(main_path):
        with open(main_path, "w", encoding="utf-8") as f:
            f.write('fn main() {\n    println("Hello, Mapanare!")\n}\n')

    return manifest
