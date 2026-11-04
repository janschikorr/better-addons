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
| [`examples/`](examples/) | Manifests that must pass, and manifests that must be rejected |

## Writing a manifest

1. Read the addon's code. Find every place where it touches the interface.
2. Map each place to a slot in `spec/slots.yaml`. **Do not invent slots.** If
   nothing fits, add the finding to the manifest's `unknown` list and say so.
3. Record `via` (the way) and `kind` (`replace`, `hook`, `add`, `modify`).
4. Give every entry a `source` of the form `path/file.lua:123`. An entry without a
   source is a guess, and guesses do not belong in a manifest.
5. Validate: `python tools/validate.py manifests/<addon>.yaml`
6. Where the code is ambiguous, **say so instead of deciding**. A flagged
   uncertainty is a correct answer; a confident wrong slot is not.

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
