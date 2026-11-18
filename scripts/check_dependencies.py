"""Fail when pyproject.toml declares a direct dependency that dependency-policy.toml lacks.

Run from the repository root: `uv run python scripts/check_dependencies.py`. For each unapproved
package it prints the license the installed package declares, so the reviewer can see what approval
would involve.
"""

import re
import sys
import tomllib
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def declared_dependencies(pyproject: dict) -> set[str]:
    requirements = list(pyproject.get("project", {}).get("dependencies", []))
    for group in pyproject.get("dependency-groups", {}).values():
        requirements.extend(item for item in group if isinstance(item, str))
    names = set()
    for requirement in requirements:
        match = NAME.match(requirement)
        if match:
            names.add(normalize(match.group(1)))
    return names


def installed_license(name: str) -> str:
    try:
        info = metadata.metadata(name)
    except metadata.PackageNotFoundError:
        return "not installed"
    expression = info.get("License-Expression")
    if expression:
        return expression
    classifiers = [
        c.split("::")[-1].strip()
        for c in info.get_all("Classifier") or []
        if c.startswith("License ::")
    ]
    if classifiers:
        return ", ".join(classifiers)
    return (info.get("License") or "unknown").splitlines()[0][:60]


def main() -> int:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    policy = tomllib.loads((ROOT / "dependency-policy.toml").read_text(encoding="utf-8"))
    approved = {normalize(name) for name in policy.get("packages", {})}

    unapproved = sorted(declared_dependencies(pyproject) - approved)
    if not unapproved:
        print(f"All {len(declared_dependencies(pyproject))} direct dependencies are approved.")
        return 0

    print("Direct dependencies without an approval in dependency-policy.toml:")
    for name in unapproved:
        print(f"  - {name} (license: {installed_license(name)})")
    print("Remove the dependency, or record its approval in dependency-policy.toml.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
