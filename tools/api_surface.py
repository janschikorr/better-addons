#!/usr/bin/env python3
"""Extract the game's API surface from Gethe/wow-ui-source.

Blizzard ships machine-readable API definitions in
Interface/AddOns/Blizzard_APIDocumentationGenerated. Extracting them gives the
scan script a list of every function, event and CVar that actually exists in a
given game version - so "invented API call" becomes a provable finding rather
than a guess.

Two branches of that mirror matter here:
  forever  the version being targeted (Interface 16001)
  live     retail, used only to tell apart the two kinds of mistake:
           a function that exists nowhere (a hallucination) and one that
           exists in retail but not here (a bad port).

Usage:
    git clone --depth 1 --single-branch -b forever \\
        https://github.com/Gethe/wow-ui-source.git forever
    python tools/api_surface.py forever --out data/api/forever.json
    python tools/api_surface.py forever --out data/api/forever.json \\
        --compare live --compare-label retail

The clone is untrusted input: this script only reads it as text and never
executes any of it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DOC_DIR = Path("Interface/AddOns/Blizzard_APIDocumentationGenerated")

FIELD = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
BOOL_FIELD = re.compile(r"(\w+)\s*=\s*(true|false)")
INLINE_PARAM = re.compile(
    r'\{\s*Name\s*=\s*"(?P<name>[^"]+)"\s*,\s*Type\s*=\s*"(?P<type>[^"]+)"'
    r'(?:\s*,\s*Nilable\s*=\s*(?P<nilable>true|false))?'
)


def depth(line: str) -> int:
    """Indentation depth in tabs; the generated files use one tab per level."""
    return len(line) - len(line.lstrip("\t"))


def parse_document(path: Path) -> dict:
    """Parse one generated documentation file into a plain dict.

    The files are generated, so their shape is dependable: a single table with
    Name/Namespace/Environment at depth 1, then Functions, Events and Tables
    sections whose entries start at depth 2.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    system = {"file": path.name, "functions": [], "events": [], "tables": []}
    section = None
    entry: dict | None = None
    param_target: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        level = depth(line)

        # System-level fields.
        if level == 1 and entry is None:
            for key, value in FIELD.findall(stripped):
                if key in ("Name", "Namespace", "Environment", "Type"):
                    system.setdefault(key.lower(), value)
            if stripped.startswith("Functions"):
                section = "functions"
                continue
            if stripped.startswith("Events"):
                section = "events"
                continue
            if stripped.startswith("Tables"):
                section = "tables"
                continue

        if section is None:
            continue

        # An entry opens at depth 2 and closes at the same depth.
        if level == 2 and stripped == "{":
            entry = {}
            param_target = None
            continue
        if level == 2 and stripped.startswith("}") and entry is not None:
            if entry.get("name"):
                system[section].append(entry)
            entry = None
            param_target = None
            continue
        if entry is None:
            continue

        # Depth 3 is the entry's own level: either a named sub-section opens
        # here, or it is one of the entry's scalar fields. Anything deeper
        # belongs to the sub-section - crucially, the Name fields of arguments
        # and returns must not be read as the entry's own name.
        if level == 3:
            head = stripped.split("=")[0].strip()
            if head in ("Arguments", "Returns", "Payload", "Fields"):
                param_target = head.lower()
                entry.setdefault(param_target, [])
                continue
            # The sub-section's own braces sit at this level too; only a real
            # field ends the sub-section.
            if stripped in ("{", "}", "},", "{},"):
                continue
            param_target = None
            for key, value in FIELD.findall(stripped):
                if key in ("Name", "Type", "LiteralName", "SecretArguments", "SecretReturns"):
                    entry[key.lower()] = value
            for key, value in BOOL_FIELD.findall(stripped):
                if key in ("Deprecated", "SynchronousEvent"):
                    entry[key.lower()] = value == "true"
            continue

        # Inline parameters: { Name = "x", Type = "number", Nilable = false },
        if param_target and level >= 4:
            match = INLINE_PARAM.search(stripped)
            if match:
                param = {"name": match.group("name"), "type": match.group("type")}
                if match.group("nilable") == "true":
                    param["nilable"] = True
                entry[param_target].append(param)

    return system


IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")

# Functions the generated documentation does not cover. CreateFrame, SetCVar,
# hooksecurefunc and the rest of the old FrameXML globals are real but
# undocumented, so their absence from the documentation proves nothing. The
# identifiers used anywhere in the game's own UI code are collected as a second,
# weaker source: present there means plausible, absent from both means suspect.
def collect_ui_identifiers(root: Path) -> set[str]:
    names: set[str] = set()
    interface = root / "Interface"
    for path in interface.rglob("*"):
        if path.suffix.lower() not in (".lua", ".xml") or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        names.update(IDENTIFIER.findall(text))
    return names


def collect(root: Path) -> dict:
    doc_dir = root / DOC_DIR
    if not doc_dir.is_dir():
        sys.exit(f"not found: {doc_dir}\nIs {root} a wow-ui-source clone?")

    version_file = root / "version.txt"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else ""

    functions: dict[str, dict] = {}
    events: dict[str, dict] = {}
    globals_: dict[str, dict] = {}
    systems: list[str] = []
    files = sorted(doc_dir.glob("*.lua"))

    for path in files:
        system = parse_document(path)
        name = system.get("name") or path.stem
        namespace = system.get("namespace")
        systems.append(name)

        for function in system["functions"]:
            record = {
                "system": name,
                "args": function.get("arguments", []),
                "returns": function.get("returns", []),
            }
            if function.get("secretarguments"):
                record["secret_args"] = function["secretarguments"]
            if function.get("secretreturns"):
                record["secret_returns"] = function["secretreturns"]
            if function.get("deprecated"):
                record["deprecated"] = True
            if namespace:
                functions[f"{namespace}.{function['name']}"] = record
            else:
                globals_[function["name"]] = record

        for event in system["events"]:
            literal = event.get("literalname")
            if literal:
                events[literal] = {"system": name, "payload": event.get("payload", [])}

    return {
        "source": "https://github.com/Gethe/wow-ui-source",
        "version": version,
        "doc_files": len(files),
        "systems": sorted(set(systems)),
        "namespaced_functions": functions,
        "global_functions": globals_,
        "events": events,
        "ui_identifiers": sorted(collect_ui_identifiers(root)),
        "limits": {
            "namespaced": (
                "The documentation covers the C_* namespaces completely, so a "
                "C_Something.Function absent from namespaced_functions does not "
                "exist in this version."
            ),
            "globals": (
                "The documentation does NOT cover the old FrameXML globals "
                "(CreateFrame, SetCVar, hooksecurefunc, InCombatLockdown and "
                "many more). Absence from global_functions proves nothing. Check "
                "ui_identifiers as well: absent from both is suspect, not proven."
            ),
        },
    }


def summarise(surface: dict, label: str) -> str:
    return (
        f"{label}: version {surface['version']}, "
        f"{len(surface['systems'])} systems, "
        f"{len(surface['namespaced_functions'])} namespaced functions, "
        f"{len(surface['global_functions'])} global functions, "
        f"{len(surface['events'])} events "
        f"(from {surface['doc_files']} documentation files), "
        f"{len(surface['ui_identifiers'])} identifiers in the UI code"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="a wow-ui-source clone of the target branch")
    parser.add_argument("--out", type=Path, help="write the surface here as JSON")
    parser.add_argument("--label", default="target", help="name for the target in the summary")
    parser.add_argument("--compare", type=Path,
                        help="a second clone (e.g. the live branch) to diff against")
    parser.add_argument("--compare-label", default="other")
    args = parser.parse_args()

    surface = collect(args.source)
    print(summarise(surface, args.label))

    if args.compare:
        other = collect(args.compare)
        print(summarise(other, args.compare_label))

        here = set(surface["namespaced_functions"]) | set(surface["global_functions"])
        there = set(other["namespaced_functions"]) | set(other["global_functions"])
        only_there = sorted(there - here)
        only_here = sorted(here - there)
        surface["absent_here"] = {
            "label": args.compare_label,
            "note": (
                "Functions that exist in the compared version but not in this one. "
                "A call to any of these is a bad port, not a hallucination."
            ),
            "functions": only_there,
        }
        print(f"  only in {args.compare_label}: {len(only_there)} functions")
        print(f"  only in {args.label}: {len(only_here)} functions")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(surface, separators=(",", ":")), encoding="utf-8")
        size_mb = args.out.stat().st_size / 1048576
        print(f"written {args.out} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
