# Better Addons

**Make it visible what an addon occupies — and keep addons honest.**

AI assistants are producing a great many new addons right now, which creates two
problems at once:

- **Compatibility.** More addons means more collisions. The manifest format makes
  visible who occupies what, so conflicts and incompatibilities can be detected.
- **Anti-slop.** More addons also means more quickly generated, unreviewed addons.
  Guides and checking tools keep addons soundly built, honestly described and
  consistently styled — whether or not an AI wrote them.

Anti-slop does not mean anti-AI. Better Addons is itself built with AI. What gets
judged is the result, not the tool.

> **Status: phase 1 of nine.** The specification, slot registry and schema exist.
> The format is explicitly versioned so it can change without breaking the
> manifests already written. Nothing here is stable yet.

## What a manifest looks like

Five lines in an addon's `.toc`:

```
## X-BetterAddons-Format: 1
## X-BetterAddons-Provides: map.window, map.pins=HereBeDragons>=2.0
## X-BetterAddons-Depends: data.zones
## X-BetterAddons-Recommends: Questie
## X-BetterAddons-Breaks: Leatrix_Maps, Mapster<3.0
```

`Provides` names the **slots** of the interface the addon occupies. A slot marked
*exclusive* can only be owned by one addon — two providers are a conflict. An
*additive* slot takes several, as long as the **ways** (`=HereBeDragons`) are
compatible. Full details: [`spec/SPEC.md`](spec/SPEC.md).

Addons without a manifest of their own are described by a YAML file in
[`manifests/`](manifests/), using the same fields.

## Repository layout

```
better-addons/
├── AGENTS.md                 context for AI assistants: workflow, rules, pointers
├── spec/
│   ├── SPEC.md               syntax and meaning of the four keywords
│   ├── slots.yaml            slot registry: area, title, exclusive/additive, ways
│   └── manifest.schema.json  schema for automatic validation
├── mapping/
│   └── api-patterns.yaml     API pattern → slot + interaction kind
├── manifests/                manifests for addons without one of their own
├── examples/                 manifests that must pass, and that must be rejected
├── guides/
│   ├── quality.md            quality guide (anti-slop)
│   └── description.md        template for addon descriptions
├── site/                     info site, published with GitHub Pages
├── tools/
│   ├── validate.py           schema and registry validation
│   ├── build_site.py         generates the site from spec and manifests
│   ├── scan.py               scan script (phase 3)
│   └── build-data.py         generates the Lua data for the checker addon (phase 5)
├── addon/BetterAddonsCheck/  the checker addon (phase 5)
└── tests/
    ├── oracle.yaml           test oracle: predictions written down before testing
    └── results/              reports from the game
```

## Working on it

```bash
python -m pip install -r requirements.txt

python tools/validate.py              # manifests, plus the examples that must fail
python tools/build_site.py --out _site  # build the info site locally
```

`tools/validate.py` is the phase 1 acceptance check: every manifest and every
valid example must pass, and every file in `examples/invalid/` must be rejected
for the stated reason.

The info site is generated from the repository itself — the slot registry page
from `spec/slots.yaml`, the compatibility overview from the manifests — so the
site and the specification cannot drift apart.

## Plan

Nine phases, each with an acceptance criterion. Phases 1 to 5 run without the
game, on the addon files alone.

| # | Phase | State |
| --- | --- | --- |
| 1 | Specification v0.1, slot registry, schema, site skeleton | **done** |
| 2 | Hand-written manifests for the thirteen test addons | next |
| 3 | API pattern mapping and scan script, with quality report | |
| 4 | AI context file, including the quality rules | |
| 5 | Checker addon v0.1, static part | |
| 6 | Checker addon, runtime observation | |
| 7 | In-game testing against the test oracle | |
| 8 | Evaluation, specification v0.2 | |
| 9 | Quality guide v0.1, full info site | |

## Licence

[MIT](LICENSE) — specification, tooling and addon alike. Use it, change it, ship
it, including in closed and commercial projects. Keep the copyright notice, and
there is no warranty.

The format is meant to be adopted, so adopting it has to be frictionless: quote
the specification in your own documentation, vendor the schema, reimplement the
checker in another language. None of that needs permission.
