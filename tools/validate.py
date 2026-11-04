#!/usr/bin/env python3
"""Validate Better Addons manifests against the schema and the slot registry.

Usage:
    python tools/validate.py                 # manifests/ + examples/, with the
                                             # invalid examples expected to fail
    python tools/validate.py path/to/x.yaml  # check specific files

Exit code 0 means everything behaved as expected.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: python -m pip install -r requirements.txt")

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    sys.exit("jsonschema is required: python -m pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "spec" / "manifest.schema.json"
SLOTS_PATH = ROOT / "spec" / "slots.yaml"
MANIFEST_DIR = ROOT / "manifests"
VALID_DIR = ROOT / "examples" / "valid"
INVALID_DIR = ROOT / "examples" / "invalid"

NAMESPACED = re.compile(r"^[a-z0-9_]+:")
SLOT_SHAPED = re.compile(r"^([a-z0-9_]+:)?[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$")


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_registry() -> tuple[dict, set[str]]:
    registry = load_yaml(SLOTS_PATH) or {}
    return registry, set(registry.get("slots") or {})


def check_ways(manifest: dict, registry: dict) -> list[str]:
    """A way must be one the registry lists for that slot.

    Added after bundle 3, where 'via: custom-frame' on journal.dungeon passed
    unnoticed although the registry lists no such way. The way is the entry's
    claim about how the slot is occupied, and collisions are decided partly by
    it, so an unlisted way is an unchecked claim.
    """
    problems = []
    slots = registry.get("slots") or {}
    for entry in manifest.get("provides") or []:
        if not isinstance(entry, dict):
            continue
        name, way = entry.get("slot"), entry.get("via")
        if not name or not way or name not in slots:
            continue
        allowed = (slots[name] or {}).get("ways") or []
        if allowed and way not in allowed:
            problems.append(
                f"provides: slot '{name}' has no way '{way}' "
                f"(registry lists: {', '.join(allowed)})"
            )
    return problems


def slot_references(manifest: dict) -> list[tuple[str, str]]:
    """Every slot name the manifest mentions, with the field it came from."""
    found: list[tuple[str, str]] = []
    for entry in manifest.get("provides") or []:
        if isinstance(entry, dict) and "slot" in entry:
            found.append((entry["slot"], "provides"))
    for field in ("depends", "recommends"):
        for entry in manifest.get(field) or []:
            if isinstance(entry, str):
                if SLOT_SHAPED.fullmatch(entry):
                    found.append((entry, field))
            elif isinstance(entry, dict) and "slot" in entry:
                found.append((entry["slot"], field))
    for field in ("clashes", "yields_to"):
        for entry in manifest.get(field) or []:
            if isinstance(entry, dict) and entry.get("slot"):
                found.append((entry["slot"], field))
    for key in manifest.get("modules") or {}:
        found.append((key, "modules"))
    return found


def check_registry(manifest: dict, known: set[str]) -> list[str]:
    """Slot names must exist in the registry, unless they are namespaced."""
    problems = []
    own = str(manifest.get("addon", "")).lower()
    for name, field in slot_references(manifest):
        if NAMESPACED.match(name):
            namespace = name.split(":", 1)[0]
            if field == "provides" and namespace != own:
                problems.append(
                    f"{field}: '{name}' lives in another addon's namespace "
                    f"(expected prefix '{own}:')"
                )
            continue
        if name not in known:
            problems.append(f"{field}: slot '{name}' is not in spec/slots.yaml")
    return problems


def check_modules(manifest: dict) -> list[str]:
    """Optional entries and the modules table must agree."""
    problems = []
    declared = set(manifest.get("modules") or {})
    used = {
        entry["slot"]
        for entry in manifest.get("provides") or []
        if isinstance(entry, dict) and entry.get("optional") and "slot" in entry
    }
    for slot in sorted(used - declared):
        problems.append(f"modules: no entry for optional slot '{slot}'")
    for slot in sorted(declared - used):
        problems.append(f"modules: '{slot}' is declared but no provide is optional")
    return problems


def check_hierarchy(manifest: dict, known: set[str]) -> list[str]:
    """A slot and one of its own ancestors must not both be claimed.

    Occupying a slot occupies its children (SPEC.md 3.5), so naming both says
    the same thing twice - which is what ui.skin plus ui.unitframe.player did
    in version 0.1.
    """
    problems = []
    claimed: dict[str, list[str]] = {}
    for entry in manifest.get("provides") or []:
        if isinstance(entry, dict) and "slot" in entry:
            claimed.setdefault(entry["slot"], []).append(entry.get("aspect", "content"))
    for slot, aspects in claimed.items():
        parts = slot.split(".")
        for depth in range(1, len(parts)):
            ancestor = ".".join(parts[:depth])
            if ancestor in claimed:
                shared = set(aspects) & set(claimed[ancestor])
                if shared:
                    problems.append(
                        f"provides: '{slot}' is already covered by its ancestor "
                        f"'{ancestor}' for aspect(s) {', '.join(sorted(shared))} "
                        f"(occupying a slot occupies its children)"
                    )
    return problems


def check_yields(manifest: dict) -> list[str]:
    """A yielded slot should be one the addon actually claims."""
    problems = []
    claimed = {
        entry["slot"]
        for entry in manifest.get("provides") or []
        if isinstance(entry, dict) and "slot" in entry
    }
    for entry in manifest.get("yields_to") or []:
        if not isinstance(entry, dict):
            continue
        slot = entry.get("slot")
        if slot and slot not in claimed:
            problems.append(
                f"yields_to: '{slot}' is yielded to {entry.get('addon')} but never "
                f"claimed in provides"
            )
    return problems


def validate_file(path: Path, validator: Draft202012Validator, known: set[str], registry: dict) -> list[str]:
    try:
        manifest = load_yaml(path)
    except yaml.YAMLError as error:
        return [f"not valid YAML: {error}"]
    if not isinstance(manifest, dict):
        return ["top level must be a mapping"]

    problems = []
    for error in sorted(validator.iter_errors(manifest), key=lambda e: list(e.path)):
        where = "/".join(str(part) for part in error.path) or "(root)"
        problems.append(f"{where}: {error.message}")
    if not problems:
        problems += check_registry(manifest, known)
        problems += check_ways(manifest, registry)
        problems += check_modules(manifest)
        problems += check_hierarchy(manifest, known)
        problems += check_yields(manifest)
    return problems


def report(path: Path, problems: list[str], *, expect_failure: bool) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    if expect_failure:
        if problems:
            print(f"  ok      {relative}  (rejected: {problems[0]})")
            return True
        print(f"  FAILED  {relative}  (should have been rejected, but passed)")
        return False
    if problems:
        print(f"  FAILED  {relative}")
        for problem in problems:
            print(f"            {problem}")
        return False
    print(f"  ok      {relative}")
    return True


def collect(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.rglob("*.y*ml") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path, help="specific manifests to check")
    args = parser.parse_args()

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    registry, known = load_registry()

    print(f"schema  {SCHEMA_PATH.relative_to(ROOT).as_posix()}")
    print(f"slots   {len(known)} slots, registry version {registry.get('version')}")

    ok = True
    if args.files:
        print("\nfiles")
        for path in args.files:
            problems = validate_file(path.resolve(), validator, known, registry)
            ok &= report(path.resolve(), problems, expect_failure=False)
        return 0 if ok else 1

    groups = [
        ("manifests (must pass)", collect(MANIFEST_DIR), False),
        ("valid examples (must pass)", collect(VALID_DIR), False),
        ("invalid examples (must be rejected)", collect(INVALID_DIR), True),
    ]
    total = 0
    for title, paths, expect_failure in groups:
        print(f"\n{title}")
        if not paths:
            print("  (none)")
            continue
        for path in paths:
            total += 1
            ok &= report(path, validate_file(path, validator, known, registry), expect_failure=expect_failure)

    print(f"\n{total} file(s) checked - {'all as expected' if ok else 'FAILURES above'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
