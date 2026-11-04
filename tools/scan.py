#!/usr/bin/env python3
"""Propose manifests from an addon folder, and measure the proposals.

Phase 3 of the plan. Two jobs, deliberately in one script:

  scan     apply mapping/api-patterns.yaml to addon folders and write a
           proposed manifest per addon, every entry carrying the file and line
           that produced it

  compare  measure those proposals against the hand-written manifests of
           phase 2 and print what was found, missed and invented

The second job is the point. A scanner nobody measured is a scanner that
invents entries with a straight face, and the comparison is the only thing that
tells us which patterns are worth keeping.

Usage:
  python -I tools/scan.py scan "E:/World of Warcraft/_forever_/Interface/AddOns"
  python tools/scan.py compare
  python tools/scan.py compare --addon Questie

Run the scan with -I: it reads addon folders, which are untrusted input.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PATTERNS_PATH = ROOT / "mapping" / "api-patterns.yaml"
MANIFEST_DIR = ROOT / "manifests"
PROPOSED_DIR = ROOT / "tests" / "proposed"

# Folders that are data, not code: scanning 14 MB of baked base64 or thousands
# of audio files tells us nothing and costs minutes.
SKIP_DIRS = {"Libs", "Lib", "libs", ".git"}
MAX_FILE_BYTES = 2_000_000


def load_patterns() -> tuple[list[dict], list[str]]:
    data = yaml.safe_load(PATTERNS_PATH.read_text(encoding="utf-8")) or {}
    patterns = []
    for raw in data.get("patterns") or []:
        entry = dict(raw)
        entry["regex"] = re.compile(entry["match"])
        patterns.append(entry)
    return patterns, data.get("blind") or []


def lua_files(folder: Path) -> list[Path]:
    found = []
    for path in folder.rglob("*.lua"):
        if any(part in SKIP_DIRS for part in path.relative_to(folder).parts[:-1]):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        found.append(path)
    return sorted(found)


def code_lines(text: str):
    """Yield (line number, code) for lines that are not comments.

    Lua line comments start with `--`, block comments run from `--[[` to `]]`.
    Scanning comments as code was the largest source of invented entries in the
    first run: QuestieTrace's file header documents
    TooltipDataProcessor.AddTooltipPostCall, and the scanner read that
    documentation as an occupied slot.
    """
    in_block = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if in_block:
            if "]]" in stripped:
                in_block = False
                line = stripped.split("]]", 1)[1]
            else:
                continue
        if stripped.startswith("--[[") or stripped.startswith("--[=["):
            if "]]" not in stripped:
                in_block = True
            continue
        if stripped.startswith("--"):
            continue
        # Trim a trailing comment, but not a `--` inside a string literal.
        if "--" in line and line.count('"') % 2 == 0 and line.count("'") % 2 == 0:
            line = line.split("--", 1)[0]
        if line.strip():
            yield number, line


def scan_addon(folder: Path, patterns: list[dict]) -> dict:
    """Every pattern hit in one addon, keyed by pattern id."""
    hits: dict[str, list[dict]] = defaultdict(list)
    files = lua_files(folder)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for number, line in code_lines(text):
            if len(line) > 2000:
                continue
            for pattern in patterns:
                if pattern["regex"].search(line):
                    hits[pattern["id"]].append(
                        {
                            "file": path.relative_to(folder.parent).as_posix(),
                            "line": number,
                            "text": line.strip()[:160],
                        }
                    )
    return {"addon": folder.name, "files": len(files), "hits": dict(hits)}


def propose(scan: dict, patterns: list[dict]) -> dict:
    """Turn hits into a manifest-shaped proposal.

    High and medium confidence become entries; low confidence becomes
    questions. Both carry the first hit as `source`, so every line of the
    proposal can be checked against the code it came from.
    """
    by_id = {p["id"]: p for p in patterns}
    provides: dict[tuple, dict] = {}
    questions = []

    for pattern_id, places in sorted(scan["hits"].items()):
        pattern = by_id[pattern_id]
        first = places[0]
        source = f"{first['file']}:{first['line']}"
        if pattern["confidence"] == "low" or not pattern.get("slot"):
            questions.append(
                {
                    "pattern": pattern_id,
                    "slot": pattern.get("slot"),
                    "hits": len(places),
                    "source": source,
                    "why": pattern["note"].strip(),
                }
            )
            continue
        key = (pattern["slot"], pattern.get("aspect"))
        entry = {
            "slot": pattern["slot"],
            "aspect": pattern.get("aspect"),
            "kind": pattern.get("kind"),
            "source": source,
            "found_by": pattern_id,
            "hits": len(places),
            "confidence": pattern["confidence"],
        }
        if pattern.get("via"):
            entry["via"] = pattern["via"]
        # Several patterns can point at one slot (tracker-suppress and
        # tracker-own-frame). Keep the more confident one and record both names.
        if key in provides:
            existing = provides[key]
            existing["found_by"] = f"{existing['found_by']}, {pattern_id}"
            existing["hits"] += len(places)
            if existing["confidence"] == "medium" and pattern["confidence"] == "high":
                existing.update({k: entry[k] for k in ("via", "source", "confidence") if k in entry})
            continue
        provides[key] = entry

    return {
        "proposed": True,
        "format": 2,
        "addon": scan["addon"],
        "scanned_files": scan["files"],
        "provides": list(provides.values()),
        "questions": questions,
    }


def write_proposals(addons_dir: Path, patterns: list[dict], blind: list[str], only: str | None) -> int:
    PROPOSED_DIR.mkdir(parents=True, exist_ok=True)
    folders = [p for p in sorted(addons_dir.iterdir()) if p.is_dir()]
    if only:
        folders = [p for p in folders if p.name.lower() == only.lower()]
    if not folders:
        print(f"no addon folders found in {addons_dir}")
        return 1

    print(f"patterns  {len(patterns)}")
    print(f"addons    {len(folders)}")
    print()
    for folder in folders:
        scan = scan_addon(folder, patterns)
        proposal = propose(scan, patterns)
        out = PROPOSED_DIR / f"{folder.name.lower()}.yaml"
        header = (
            "# PROPOSED, not authoritative. Generated by tools/scan.py from\n"
            "# mapping/api-patterns.yaml. Every entry names the file and line that\n"
            "# produced it; check each one before using it. What a scan cannot decide\n"
            "# is listed at the end of mapping/api-patterns.yaml.\n"
        )
        out.write_text(
            header + yaml.safe_dump(proposal, sort_keys=False, allow_unicode=True, width=88),
            encoding="utf-8",
        )
        print(
            f"  {folder.name:38s} {scan['files']:4d} files  "
            f"{len(proposal['provides']):2d} entries  {len(proposal['questions'])} questions"
        )
    print(f"\nwritten to {PROPOSED_DIR.relative_to(ROOT).as_posix()}/")
    print("\nWhat the scan cannot decide:")
    for item in blind:
        print("  - " + " ".join(item.split())[:150])
    return 0


def hand_written() -> dict[str, dict]:
    out = {}
    for path in sorted(MANIFEST_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("addon"):
            out[str(data["addon"]).lower()] = data
    return out


def slot_set(manifest: dict) -> set[str]:
    """Registry slots a manifest claims. Namespaced slots are an addon's own
    invention and no pattern could find them, so they are left out of the
    measurement rather than counted as misses."""
    return {
        entry["slot"]
        for entry in manifest.get("provides") or []
        if isinstance(entry, dict) and entry.get("slot") and ":" not in entry["slot"]
    }


def compare(only: str | None) -> int:
    hand = hand_written()
    if not PROPOSED_DIR.exists():
        print("no proposals yet - run the scan first")
        return 1

    rows = []
    totals = {"found": 0, "missed": 0, "invented": 0, "aspect_wrong": 0}
    for path in sorted(PROPOSED_DIR.glob("*.yaml")):
        proposal = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        name = str(proposal.get("addon", "")).lower()
        if only and name != only.lower():
            continue
        if name not in hand:
            continue
        truth = hand[name]
        want = slot_set(truth)
        got = slot_set(proposal)

        def related(a: str, b: str) -> bool:
            return a == b or a.startswith(b + ".") or b.startswith(a + ".")

        found = sorted(s for s in want if any(related(s, g) for g in got))
        missed = sorted(s for s in want if not any(related(s, g) for g in got))
        invented = sorted(g for g in got if not any(related(g, w) for w in want))
        at_other_depth = sorted(
            f"{g} (hand-written: {w})"
            for g in got
            for w in want
            if related(g, w) and g != w
        )

        # Of the slots both agree on, how many have the right aspect?
        want_aspect = {
            e["slot"]: e.get("aspect", "content")
            for e in truth.get("provides") or []
            if isinstance(e, dict) and e.get("slot")
        }
        got_aspect = {
            e["slot"]: e.get("aspect")
            for e in proposal.get("provides") or []
            if isinstance(e, dict) and e.get("slot")
        }
        aspect_wrong = sorted(s for s in found if want_aspect.get(s) != got_aspect.get(s))

        totals["depth"] = totals.get("depth", 0) + len(at_other_depth)
        totals["found"] += len(found)
        totals["missed"] += len(missed)
        totals["invented"] += len(invented)
        totals["aspect_wrong"] += len(aspect_wrong)
        rows.append((truth.get("addon"), found, missed, invented, aspect_wrong, at_other_depth))

    print("Proposed manifests measured against the hand-written ones")
    print("=" * 72)
    for addon, found, missed, invented, aspect_wrong, at_other_depth in rows:
        total = len(found) + len(missed)
        print(f"\n{addon}  -  {len(found)}/{total} slots found")
        if missed:
            print("  missed:   " + ", ".join(missed))
        if invented:
            print("  invented: " + ", ".join(invented))
        if aspect_wrong:
            print("  wrong aspect: " + ", ".join(aspect_wrong))
        if at_other_depth:
            print("  right place, other depth: " + ", ".join(at_other_depth))

    want_total = totals["found"] + totals["missed"]
    print("\n" + "=" * 72)
    if want_total:
        print(
            f"recall      {totals['found']}/{want_total} "
            f"({100 * totals['found'] // want_total}%) of hand-written registry slots found"
        )
    got_total = totals["found"] + totals["invented"]
    if got_total:
        print(
            f"precision   {totals['found']}/{got_total} "
            f"({100 * totals['found'] // got_total}%) of proposed slots are in the hand-written manifest"
        )
    if totals["found"]:
        right = totals["found"] - totals["aspect_wrong"]
        print(
            f"aspect      {right}/{totals['found']} "
            f"({100 * right // totals['found']}%) of agreed slots have the right aspect"
        )
    print(
        "\nNamespaced slots are excluded: an addon's own API name cannot be\n"
        "derived from a pattern, and counting it as a miss would flatter nothing."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    scan_cmd = sub.add_parser("scan", help="write proposed manifests from addon folders")
    scan_cmd.add_argument("addons", help="path to Interface/AddOns")
    scan_cmd.add_argument("--addon", help="only this folder")

    compare_cmd = sub.add_parser("compare", help="measure proposals against hand-written manifests")
    compare_cmd.add_argument("--addon", help="only this addon")

    args = parser.parse_args()
    patterns, blind = load_patterns()

    if args.command == "scan":
        folder = Path(args.addons)
        if not folder.is_dir():
            print(f"not a directory: {folder}")
            return 1
        return write_proposals(folder, patterns, blind, args.addon)
    return compare(args.addon)


if __name__ == "__main__":
    sys.exit(main())
