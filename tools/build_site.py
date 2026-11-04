#!/usr/bin/env python3
"""Build the Better Addons info site from the repository itself.

The point of generating rather than hand-writing the site is that the site and
the specification can never drift apart: the slot registry page is produced from
spec/slots.yaml, and the compatibility overview from the manifests.

Usage:
    python tools/build_site.py [--out _site]
"""

from __future__ import annotations

import argparse
import html
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: python -m pip install -r requirements.txt")

try:
    import markdown
except ImportError:  # pragma: no cover
    sys.exit("Markdown is required: python -m pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "site" / "site.yaml"
STYLE = ROOT / "site" / "style.css"

MD_EXTENSIONS = ["tables", "fenced_code", "toc", "attr_list", "sane_lists"]


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


# --------------------------------------------------------------- generated parts

def render_slots() -> str:
    registry = load_yaml(ROOT / "spec" / "slots.yaml") or {}
    areas = registry.get("areas") or {}
    slots = registry.get("slots") or {}
    providers = collect_providers()

    out = [
        f'<p class="meta">Registry version {esc(registry.get("version"))}, '
        f"{len(slots)} slots.</p>"
    ]
    grouped: dict[str, list[tuple[str, dict]]] = {}
    for name, slot in slots.items():
        grouped.setdefault(slot.get("area", "other"), []).append((name, slot))

    order = list(areas) + [a for a in grouped if a not in areas]
    for area in order:
        entries = grouped.get(area)
        if not entries:
            continue
        out.append(f'<h2 id="area-{esc(area)}">{esc(areas.get(area, area))}</h2>')
        out.append("<table><thead><tr><th>Slot</th><th>What it is</th>"
                   "<th>Kind</th><th>Known ways</th><th>Addons</th></tr></thead><tbody>")
        for name, slot in sorted(entries):
            kind = "exclusive" if slot.get("exclusive") else "additive"
            ways = ", ".join(f"<code>{esc(w)}</code>" for w in slot.get("ways") or []) or "&mdash;"
            note = slot.get("note") or ""
            title = f"<strong>{esc(slot.get('title', name))}</strong>"
            if note:
                title += f'<br><span class="note">{esc(note.strip())}</span>'
            taken = providers.get(name) or []
            who = ", ".join(esc(a) for a in sorted(taken)) if taken else "&mdash;"
            out.append(
                f'<tr><td><code>{esc(name)}</code></td><td>{title}</td>'
                f'<td><span class="tag {kind}">{kind}</span></td>'
                f"<td>{ways}</td><td>{who}</td></tr>"
            )
        out.append("</tbody></table>")
    return "\n".join(out)


def collect_providers() -> dict[str, set[str]]:
    """slot name -> set of addons occupying it, read from manifests/."""
    providers: dict[str, set[str]] = {}
    for path in sorted((ROOT / "manifests").glob("*.y*ml")):
        manifest = load_yaml(path) or {}
        addon = manifest.get("addon") or path.stem
        for entry in manifest.get("provides") or []:
            if isinstance(entry, dict) and "slot" in entry:
                providers.setdefault(entry["slot"], set()).add(addon)
    return providers


def render_compatibility() -> str:
    manifests = []
    for path in sorted((ROOT / "manifests").glob("*.y*ml")):
        manifest = load_yaml(path) or {}
        manifest["_file"] = path.relative_to(ROOT).as_posix()
        manifests.append(manifest)

    if not manifests:
        return (
            '<p class="empty">No manifests yet. The overview appears here as soon as '
            "phase 2 adds the first hand-written manifests.</p>"
        )

    out = ["<table><thead><tr><th>Addon</th><th>Occupies</th>"
           "<th>Needs</th><th>Breaks with</th><th>Yields to</th></tr></thead><tbody>"]
    for manifest in manifests:
        provides = ", ".join(
            f"<code>{esc(e.get('slot'))}</code>"
            f"<span class=\"aspect\">{esc(e.get('aspect', 'content'))}</span>"
            for e in manifest.get("provides") or []
            if isinstance(e, dict)
        ) or "&mdash;"
        depends = ", ".join(esc(describe_requirement(e)) for e in manifest.get("depends") or []) or "&mdash;"
        breaks = ", ".join(esc(describe_break(e)) for e in manifest.get("breaks") or []) or ""
        for entry in manifest.get("clashes") or []:
            settings = ", ".join(entry.get("settings") or [])
            breaks += (", " if breaks else "") + (
                f'{esc(entry.get("addon"))} <span class="note">(only with: {esc(settings)})</span>'
            )
        breaks = breaks or "&mdash;"
        yields = ", ".join(
            f'{esc(e.get("addon"))} <span class="note">{esc(e.get("slot"))}</span>'
            for e in manifest.get("yields_to") or []
        ) or "&mdash;"
        out.append(
            f'<tr><td><strong>{esc(manifest.get("addon"))}</strong><br>'
            f'<span class="note">{esc(manifest.get("toc") or "")}</span></td>'
            f"<td>{provides}</td><td>{depends}</td><td>{breaks}</td><td>{yields}</td></tr>"
        )
    out.append("</tbody></table>")
    return "\n".join(out)


def describe_requirement(entry) -> str:
    if isinstance(entry, str):
        return entry
    if "addon" in entry:
        return f"{entry['addon']}{entry.get('version', '')}"
    way = f"={entry['via']}" if entry.get("via") else ""
    return f"{entry.get('slot', '?')}{way}"


def describe_break(entry) -> str:
    if isinstance(entry, str):
        return entry
    return f"{entry.get('addon', '?')}{entry.get('version', '')}"


GENERATORS = {"slots": render_slots, "compatibility": render_compatibility}


# ----------------------------------------------------------------------- layout

LAYOUT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{tagline}">
<link rel="stylesheet" href="{base}/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header>
  <a class="brand" href="{base}/">{site_title}</a>
  <nav>{nav}</nav>
</header>
<main id="main">
{body}
</main>
<footer>
  <p>Generated from <a href="{repo}">the repository</a>. Spec version {spec_version}.
     Licensed <a href="{repo}/blob/main/LICENSE">MIT</a>.</p>
</footer>
</body>
</html>
"""


def build(out_dir: Path) -> int:
    config = load_yaml(CONFIG) or {}
    base = config.get("base", "").rstrip("/")
    pages = config.get("pages") or []
    spec_version = (load_yaml(ROOT / "spec" / "slots.yaml") or {}).get("version", "?")

    out_dir.mkdir(parents=True, exist_ok=True)
    nav_items = []
    for page in pages:
        href = f"{base}/" if page["slug"] == "index" else f"{base}/{page['slug']}/"
        nav_items.append(f'<a href="{href}">{esc(page["nav"])}</a>')
    nav = "\n    ".join(nav_items)

    for page in pages:
        source = ROOT / page["source"]
        if not source.is_file():
            print(f"  skipped {page['slug']}: {page['source']} is missing")
            continue
        converter = markdown.Markdown(extensions=MD_EXTENSIONS)
        body = converter.convert(source.read_text(encoding="utf-8"))
        if page.get("include") in GENERATORS:
            body += "\n" + GENERATORS[page["include"]]()

        document = LAYOUT.format(
            title=esc(f'{page["title"]} – {config.get("title")}'
                      if page["slug"] != "index" else config.get("title")),
            site_title=esc(config.get("title")),
            tagline=esc(config.get("tagline")),
            base=esc(base),
            repo=esc(config.get("repo")),
            nav=nav,
            body=body,
            spec_version=esc(spec_version),
        )
        target = out_dir / "index.html" if page["slug"] == "index" else out_dir / page["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(document, encoding="utf-8")
        print(f"  built   {target.relative_to(out_dir.parent).as_posix()}")

    if STYLE.is_file():
        shutil.copy2(STYLE, out_dir / "style.css")

    # Publish the machine-readable sources next to the site so tools can fetch them.
    for name in ("spec/slots.yaml", "spec/manifest.schema.json"):
        source = ROOT / name
        if source.is_file():
            target = out_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    print(f"site    {CONFIG.relative_to(ROOT).as_posix()} -> {args.out}")
    return build(args.out.resolve())


if __name__ == "__main__":
    sys.exit(main())
