"""Mapanare package manager -- manifest parsing, dependency resolution, and package operations."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
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
    """Install a package, checking the registry first with git fallback.

    Resolution order:
    1. If --git is specified, use git directly
    2. Try the Mapanare package registry
    3. Fall back to convention-based git URL
    """
    # If explicit git URL given, skip registry
    if git_url:
        return _install_from_git(package_name, project_dir, git_url, branch, version)

    # Try registry first
    try:
        locked = _install_from_registry(package_name, project_dir, version)
        if locked:
            # Update manifest and lockfile
            _update_manifest_and_lock(package_name, project_dir, locked, version)
            return locked
    except PackageError:
        pass  # Fall through to git

    # Fall back to git
    return _install_from_git(package_name, project_dir, None, branch, version)


def _install_from_git(
    package_name: str,
    project_dir: str,
    git_url: str | None,
    branch: str | None,
    version: str,
) -> LockedDependency:
    """Install a package by cloning its git repo into mapanare_packages/."""
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

    _update_manifest_and_lock(package_name, project_dir, locked, version, git_url, branch)
    return locked


def _update_manifest_and_lock(
    package_name: str,
    project_dir: str,
    locked: LockedDependency,
    version: str,
    git_url: str | None = None,
    branch: str | None = None,
) -> None:
    """Update manifest and lockfile after a successful install."""
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
# Registry configuration
# ---------------------------------------------------------------------------

REGISTRY_URL = os.environ.get("MAPANARE_REGISTRY_URL", "https://mapanare.dev")
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".mapanare", "token")


def _read_token() -> str | None:
    """Read API token from ~/.mapanare/token."""
    if os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as f:
            return f.read().strip()
    return os.environ.get("MAPANARE_TOKEN")


def _save_token(token: str) -> None:
    """Save API token to ~/.mapanare/token."""
    token_dir = os.path.dirname(TOKEN_FILE)
    os.makedirs(token_dir, exist_ok=True)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(token)


# ---------------------------------------------------------------------------
# mapa publish — upload package to registry
# ---------------------------------------------------------------------------


def _build_tarball(project_dir: str) -> bytes:
    """Build a .tar.gz archive of the project for publishing."""
    load_manifest(project_dir)  # Validate manifest exists and parses
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        # Add mapanare.toml
        toml_path = os.path.join(project_dir, "mapanare.toml")
        tar.add(toml_path, arcname="mapanare.toml")

        # Add all .mn files
        for root, _dirs, files in os.walk(project_dir):
            # Skip hidden dirs, mapanare_packages, __pycache__, etc.
            rel_root = os.path.relpath(root, project_dir)
            if any(
                part.startswith(".") or part in ("mapanare_packages", "__pycache__", "node_modules")
                for part in rel_root.split(os.sep)
            ):
                if rel_root != ".":
                    continue

            for fname in sorted(files):
                if fname.endswith(".mn") or fname.lower() in ("readme.md", "readme.txt", "license"):
                    fpath = os.path.join(root, fname)
                    arcname = os.path.relpath(fpath, project_dir)
                    if arcname != "mapanare.toml":  # already added
                        tar.add(fpath, arcname=arcname)

    return buf.getvalue()


def publish_package(project_dir: str, token: str | None = None) -> dict[str, str]:
    """Publish a package to the Mapanare registry.

    Returns dict with name, version, checksum on success.
    Raises PackageError on failure.
    """
    import urllib.error
    import urllib.request

    manifest = load_manifest(project_dir)
    auth_token = token or _read_token()
    if not auth_token:
        raise PackageError(
            "No API token found. Set MAPANARE_TOKEN environment variable "
            "or run: mapanare publish --token <token>"
        )

    tarball_data = _build_tarball(project_dir)

    # Multipart upload
    boundary = "----MapanarePublish"
    filename = f"{manifest.name}-{manifest.version}.tar.gz"
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/gzip\r\n\r\n"
    )
    body = header.encode("utf-8")
    body += tarball_data
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"{REGISTRY_URL}/api/packages"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result: dict[str, str] = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(error_body).get("detail", error_body)
        except (json.JSONDecodeError, AttributeError):
            detail = error_body
        raise PackageError(f"publish failed ({e.code}): {detail}") from e
    except urllib.error.URLError as e:
        raise PackageError(f"could not connect to registry at {url}: {e}") from e


# ---------------------------------------------------------------------------
# mapa search — query the package registry
# ---------------------------------------------------------------------------


def search_packages(
    query: str = "", keyword: str = "", page: int = 1, per_page: int = 20
) -> dict[str, Any]:
    """Search the Mapanare package registry. Returns search response dict."""
    import urllib.error
    import urllib.parse
    import urllib.request

    params = urllib.parse.urlencode(
        {"q": query, "keyword": keyword, "page": page, "per_page": per_page}
    )
    url = f"{REGISTRY_URL}/api/packages?{params}"

    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        raise PackageError(f"search failed ({e.code})") from e
    except urllib.error.URLError as e:
        raise PackageError(f"could not connect to registry: {e}") from e


# ---------------------------------------------------------------------------
# mapa install — registry-first with git fallback
# ---------------------------------------------------------------------------


def _install_from_registry(
    package_name: str, project_dir: str, version_constraint: str = "*"
) -> LockedDependency | None:
    """Try to install a package from the registry. Returns None if not found."""
    import urllib.error
    import urllib.parse
    import urllib.request

    # First, get package info to find available versions
    url = f"{REGISTRY_URL}/api/packages/{urllib.parse.quote(package_name)}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            pkg_info = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise PackageError(f"registry error ({e.code})") from e
    except urllib.error.URLError:
        return None  # Registry unreachable, fall back to git

    # Find best matching version
    available = [v["version"] for v in pkg_info["versions"] if not v.get("yanked", False)]
    if not available:
        return None

    # Simple version resolution
    best = _resolve_best_local(available, version_constraint)
    if not best:
        return None

    # Download the tarball
    dl_url = f"{REGISTRY_URL}/api/packages/{urllib.parse.quote(package_name)}/{best}/download"
    try:
        req = urllib.request.Request(dl_url, method="GET")
        with urllib.request.urlopen(req, timeout=60) as resp:
            tarball_data = resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        raise PackageError(f"failed to download {package_name}@{best}: {e}") from e

    # Extract to mapanare_packages/<name>/
    packages_dir = os.path.join(project_dir, MAPANARE_PACKAGES_DIR)
    os.makedirs(packages_dir, exist_ok=True)
    pkg_dir = os.path.join(packages_dir, package_name)

    if os.path.isdir(pkg_dir):
        shutil.rmtree(pkg_dir)
    os.makedirs(pkg_dir)

    with tarfile.open(fileobj=io.BytesIO(tarball_data), mode="r:gz") as tar:
        # Security check
        for member in tar.getmembers():
            if member.name.startswith("/") or ".." in member.name:
                raise PackageError(f"unsafe path in tarball: {member.name}")
        tar.extractall(pkg_dir)

    integrity = _compute_integrity(pkg_dir)
    checksum = f"sha256:{hashlib.sha256(tarball_data).hexdigest()}"

    return LockedDependency(
        name=package_name,
        version=best,
        git=f"{REGISTRY_URL}/api/packages/{package_name}/{best}/download",
        commit=checksum,
        integrity=integrity,
    )


def _resolve_best_local(available: list[str], constraint: str) -> str | None:
    """Resolve best version from available list given a constraint.

    Supports: *, >=X.Y.Z, ^X.Y.Z, ~X.Y.Z, exact match.
    """
    if constraint == "*":
        # Return highest version
        if not available:
            return None
        return sorted(available, key=_version_tuple, reverse=True)[0]

    matching = [v for v in available if _satisfies_constraint(v, constraint)]
    if not matching:
        return None
    return sorted(matching, key=_version_tuple, reverse=True)[0]


def _version_tuple(ver: str) -> tuple[int, ...]:
    """Parse version string into comparable tuple."""
    # Strip prerelease/build for basic comparison
    base = ver.split("-")[0].split("+")[0]
    parts = base.split(".")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    return tuple(result)


def _satisfies_constraint(version: str, constraint: str) -> bool:
    """Check if version satisfies a constraint string."""
    constraint = constraint.strip()
    if constraint == "*":
        return True

    ver = _version_tuple(version)

    for part in constraint.split(","):
        part = part.strip()
        if not part:
            continue

        if part.startswith("^"):
            base = _version_tuple(part[1:])
            if base[0] > 0:
                upper = (base[0] + 1, 0, 0)
            elif len(base) > 1 and base[1] > 0:
                upper = (0, base[1] + 1, 0)
            else:
                upper = (0, 0, (base[2] if len(base) > 2 else 0) + 1)
            if not (ver >= base and ver < upper):
                return False

        elif part.startswith("~"):
            base = _version_tuple(part[1:])
            upper = (base[0], (base[1] if len(base) > 1 else 0) + 1, 0)
            if not (ver >= base and ver < upper):
                return False

        elif part.startswith(">="):
            base = _version_tuple(part[2:])
            if not (ver >= base):
                return False

        elif part.startswith(">"):
            base = _version_tuple(part[1:])
            if not (ver > base):
                return False

        elif part.startswith("<="):
            base = _version_tuple(part[2:])
            if not (ver <= base):
                return False

        elif part.startswith("<"):
            base = _version_tuple(part[1:])
            if not (ver < base):
                return False

        elif part.startswith("="):
            base = _version_tuple(part[1:])
            if ver != base:
                return False

        else:
            base = _version_tuple(part)
            if ver != base:
                return False

    return True


# ---------------------------------------------------------------------------
# Version bumping
# ---------------------------------------------------------------------------


def bump_version(project_dir: str, bump_type: str = "patch") -> str:
    """Bump the version in mapanare.toml and return the new version string.

    bump_type can be: major, minor, patch, or an explicit version like "1.2.3".
    """
    manifest = load_manifest(project_dir)
    old = manifest.version

    # If it's an explicit version, just set it
    if bump_type not in ("major", "minor", "patch"):
        # Validate it looks like semver
        parts = bump_type.split("-")[0].split("+")[0].split(".")
        if len(parts) < 2 or not all(p.isdigit() for p in parts[:3]):
            raise ManifestError(f"invalid version: {bump_type}")
        manifest.version = bump_type
        save_manifest(manifest, project_dir)
        return manifest.version

    # Parse current version
    base = old.split("-")[0].split("+")[0]
    parts = base.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    manifest.version = f"{major}.{minor}.{patch}"
    save_manifest(manifest, project_dir)
    return manifest.version


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
            f.write('fn main() {\n    print("Hello, Mapanare!")\n}\n')

    return manifest
