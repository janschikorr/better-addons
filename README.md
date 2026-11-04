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
## X-BetterAddons-Format: 2
## X-BetterAddons-Provides: map.art/content=stitched, map.window/geometry
## X-BetterAddons-Recommends: Questie
## X-BetterAddons-Breaks: Mapster, Magnify
## X-BetterAddons-Clashes: Leatrix_Maps[Unlock map frame,Scale the map]
## X-BetterAddons-Yields-To: MoveAny=map.window
```

`Provides` names the **slots** of the interface the addon occupies, and after the
slash the **aspect**: whether it changes what a part shows (`content`), where it
sits (`geometry`), how it looks (`style`) or how it responds (`behaviour`). Two
addons in the same slot touching different aspects usually cooperate — which is
why ClassicUI restyling the minimap and MoveAny moving it are compatible.

`Yields-To` says "I claim this only while that addon is absent", and `Clashes`
records a conflict that depends on a setting rather than on installation. Full
details: [`spec/SPEC.md`](spec/SPEC.md); the evidence for each rule is in
[`spec/CHANGELOG.md`](spec/CHANGELOG.md).

Addons without a manifest of their own are described by a YAML file in
[`manifests/`](manifests/), using the same fields.

## Repository layout

```
better-addons/
├── AGENTS.md                 context for AI assistants: workflow, rules, pointers
├── spec/
│   ├── SPEC.md               syntax and meaning of the keywords
│   ├── CHANGELOG.md          what changed per version, and the code that forced it
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
│   ├── inventory.py          what is installed, read from the .toc files
│   ├── api_surface.py        the game's API surface, from wow-ui-source
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
| 2a | Specification v0.2, pulled forward from phase 8 | **done** |
| 2 | Hand-written manifests: 4 of 18 done (bundle 1) | in progress |
| 3 | API pattern mapping and scan script, with quality report | |
| 4 | AI context file, including the quality rules | |
| 5 | Checker addon v0.1, static part | |
| 6 | Checker addon, runtime observation | |
| 7 | In-game testing against the test oracle | |
| 8 | Evaluation of the in-game findings, specification v0.3 | |
| 9 | Quality guide v0.1, full info site | |

## Licence

[MIT](LICENSE) — specification, tooling and addon alike. Use it, change it, ship
it, including in closed and commercial projects. Keep the copyright notice, and
there is no warranty.

The format is meant to be adopted, so adopting it has to be frictionless: quote
the specification in your own documentation, vendor the schema, reimplement the
checker in another language. None of that needs permission.
