# Better Addons – context for AI assistants

This file is the entry point for an AI assistant working **in this repository** or
**on an addon that wants a Better Addons manifest**. It is deliberately short and
points at the authoritative documents instead of repeating them.

> Status: phase 1. The quality rules below are the working set; the full guide
> lands in phase 9 as [`guides/quality.md`](guides/quality.md).

## What this project is

Two goals, because AI assistants are currently producing a great many new addons:

1. **Compatibility.** More addons means more collisions. The manifest format makes
   visible who occupies what, so conflicts and incompatibilities can be detected.
2. **Anti-slop.** More addons also means more quickly generated, unreviewed addons.
   Guides and checking tools keep addons soundly built, honestly described and
   consistently styled — whether or not an AI wrote them.

Anti-slop does not mean anti-AI. Better Addons is itself built with AI. What gets
judged is the result, not the tool.

## Read these first

| Document | What it settles |
| --- | --- |
| [`spec/SPEC.md`](spec/SPEC.md) | The four keywords, slot expressions, version constraints, how a pair is judged |
| [`spec/slots.yaml`](spec/slots.yaml) | Every slot that exists, and whether it is exclusive or additive |
| [`spec/manifest.schema.json`](spec/manifest.schema.json) | The machine-checkable shape of a YAML manifest |
| [`spec/CHANGELOG.md`](spec/CHANGELOG.md) | What changed between spec versions, and the addon code that forced each change |
| [`examples/`](examples/) | Manifests that must pass, and manifests that must be rejected |

## Writing a manifest

1. Read the addon's code. Find every place where it touches the interface.
2. Map each place to a slot in `spec/slots.yaml`. **Do not invent slots.** If
   nothing fits, add the finding to the manifest's `unknown` list and say so.
3. Decide the **aspect** for each entry, and get this right - it decides the
   verdict. `content` is what a frame shows, `geometry` is where it sits and how
   big it is, `style` is textures and fonts, `behaviour` is how it responds.
   An addon that only moves frames is `geometry`, not `content`.
4. Claim the **nearest useful parent slot**, not every child: occupying a slot
   occupies its children. Claiming both a slot and its ancestor is rejected.
5. Record `via` (the way) and `kind` (`replace`, `hook`, `add`, `modify`).
6. If the addon stands down for another addon, use `yields_to`. If it conflicts
   only under a setting, use `clashes`, not `breaks`.
7. For an optional (`?`) entry, state the module's real `default` - read it from
   the code, do not assume. Both assumptions were wrong in half the cases.
8. Give every entry a `source` of the form `path/file.lua:123`. An entry without
   a source is a guess, and guesses do not belong in a manifest. Add a `reason`
   wherever the choice would otherwise read as careless.
9. Validate: `python tools/validate.py manifests/<addon>.yaml`
10. Where the code is ambiguous, **say so instead of deciding**. A flagged
    uncertainty is a correct answer; a confident wrong slot is not.

## Checking an API call

The game's own interface code is mirrored at
[Gethe/wow-ui-source](https://github.com/Gethe/wow-ui-source); the `forever`
branch is the version targeted here (1.60.1.70790 = Interface 16001).
`tools/api_surface.py` extracts its API surface.

Do not guess whether a function exists. Check it, and respect what the check can
prove:

- A `C_*` call absent from the extracted surface **does not exist**. Report it.
- A global call absent from it proves nothing: the old FrameXML globals are
  undocumented. If it is also absent from the UI code identifiers, say it is
  suspect - do not call it an error.
- Forever is an API superset of Retail, so "this came from Retail" is almost
  never the explanation. It carries both the classic globals and the modern
  namespaces; prefer the `C_*` namespace where both exist.

## Quality rules for addon code

These are the rules the scan script and `luacheck` check for. They exist because
each one is a recurring slop pattern.

| Rule | Why |
| --- | --- |
| Use only documented API of the target game version | Functions carried over from Retail or Classic that do not exist there fail at runtime |
| Let errors surface; handle them deliberately. No blanket `pcall` around everything | A swallowed error turns a bug into silent wrong behaviour |
| Work from events, not from `OnUpdate` every frame | Per-frame polling costs frame time for no reason |
| Keep everything in your own namespace; no unprefixed globals | Unprefixed globals collide with other addons |
| Respect the restrictions of the target game version (e.g. protected values in combat) | Otherwise the addon breaks exactly when it matters |
| Name source and licence for any bundled database; prefer shared data packages | Copied databases without provenance are both a legal and a maintenance problem |
| Describe the addon honestly: what it does, what it does not, known limits, real screenshots | Emoji lists, superlatives and promised features are the clearest slop marker |
| Make the manifest match the actual behaviour | The runtime observation in phase 6 compares the two, and a mismatch is reported |
| Before writing a new addon, check the slot registry and consider extending an existing one | Forever already has more than half a dozen dungeon journal addons |

## Working in this repository

- Repository content is written in **English**. Nothing in `spec/`, `guides/`,
  `site/` or code comments should be in another language.
- Every slot name is lowercase and dotted. A slot an addon offers to others is
  namespaced: `openmap:canvas.overlay`.
- Changing `spec/slots.yaml` or `spec/manifest.schema.json` means re-running
  `python tools/validate.py` before committing.
- Phases and acceptance criteria come from the project plan. Do not skip ahead:
  phase 3's scan script is validated against phase 2's hand-written manifests, so
  writing the script first would remove the only yardstick there is.

## Using tools/scan.py

The scan proposes manifests from code patterns. It is a suggestion tool with
citations, never an author, and its output in `tests/proposed/` is not a
manifest - every file says `proposed: true` for that reason.

`tests/SCAN-REPORT.md` has the measurement: it finds 37% of what a human finds,
and 46% of what it proposes is right. Read that report before relying on a
proposal. Three things follow for anyone writing a manifest:

- Use a proposal as a checklist of places to look, not as a draft to edit. Each
  entry names the file and line that produced it, so confirming or rejecting one
  is quick.
- Expect it to miss the addons that matter most. Detectability follows coding
  style, not scale: Questie scores 8/11 because it calls named APIs, MoveAny
  2/14 because it drives 115 frames from a table. Frame-moving addons are
  systematically under-reported.
- Never take an aspect, a default, a `reason`, a `Yields-To` or a `Clashes` from
  a proposal. The scan cannot see any of them; the `blind` list at the end of
  `mapping/api-patterns.yaml` says why.

When a pattern proves wrong, change it in `mapping/api-patterns.yaml`, say in
its `note` what the measurement showed, and re-run `compare`. Demoting a pattern
to `confidence: low` turns it into a question rather than deleting what it
knows.
