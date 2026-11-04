# What a scan can and cannot find

Phase 3 asked whether manifests can be generated instead of written. The answer
is measured, not argued: `tools/scan.py` applies the patterns in
`mapping/api-patterns.yaml` to the 30 installed addon folders, writes a proposed
manifest per addon into `tests/proposed/`, and compares those proposals against
the 18 hand-written manifests of phase 2.

Reproduce it with:

```
python -I tools/scan.py scan "E:/World of Warcraft/_forever_/Interface/AddOns"
python tools/scan.py compare
```

## The number

| | first run (25 patterns) | after sharpening (38 patterns) |
|---|---|---|
| recall | 18/78 (23%) | 29/78 (37%) |
| precision | 18/52 (34%) | 29/63 (46%) |
| aspect correct | 18/18 (100%) | 27/29 (93%) |

Recall counts registry slots in the hand-written manifests that the scan also
proposed; precision counts proposed slots that are in the hand-written
manifest. Namespaced slots (`openmap:api.position`) are excluded: an addon's own
API name cannot be derived from a pattern, and counting it as a miss would
flatter nothing. A proposal naming a child slot where the manifest claims the
parent counts as found, since SPEC.md 3.5 makes occupying a slot occupy its
children.

So after two rounds of improvement, **a scan finds under half of what a human
finds, and more than half of what it proposes is wrong.** That is the headline
result of phase 3, and it is not a disappointment: it is the reason the format
is written by hand and the scan is a suggestion tool.

## The one mistake that mattered most

The first run's biggest single source of invented entries was reading comments
as code. QuestieTrace's `Modules/Trackers/GameObject.lua` documents the modern
tooltip API in its file header:

```lua
--   TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Object, func)
```

The scanner read that documentation and reported an occupied tooltip slot. Six
addons were mislabelled this way. `code_lines()` in `tools/scan.py` now skips
line and block comments. Well-documented addons were penalised for being
well documented, which is the opposite of what this project wants to reward.

## The systematic error the measurement exposed

Almost every false positive was one confusion in different clothes: **the
scanner could not tell "this addon uses X for itself" from "this addon occupies
the game's X".**

- `GameTooltip:AddLine` is how an addon fills **its own** tooltip after
  `SetOwner`. It only occupies `tooltip.lines` inside a hook on the game's
  tooltip. The pattern was split: the hook stays high confidence, the bare
  `AddLine` became a question.
- `CreateFrame("Frame", "...Tracker...")` matched MoveAny's
  `ObjectiveTrackerFrame2` (a dummy for its settings panel) and three addons'
  `TrackerHost` (a block **inside** the tracker column, not a replacement of
  it). The pattern was narrowed, and a separate `tracker-block` pattern now
  proposes `quest.tracker.lines` instead.
- `NAME_PLATE_UNIT_ADDED` means an addon **watches** nameplates. Four addons
  that only observe were reported as occupying `ui.nameplates`. Drawing on a
  plate needs `C_NamePlate.GetNamePlateForUnit`, which is now the high
  confidence pattern; the event was demoted to a question.
- `PlaySoundFile` and `SetBindingClick` were demoted for the same reason: a
  click sound is not a narrator, and binding a key to the addon's own button
  takes nothing from the player.

Two patterns had predicted their own demotion in their `note` fields before the
measurement ran. Writing down why a pattern might be wrong turned out to be
worth as much as the pattern.

A sharper version of the same confusion survives: reading a frame is not
occupying it. Questie touches `QuestFrame` to read quest text, and the scan
proposes `quest.detail`, `quest.gossip` and `quest.log` for it. No regular
expression distinguishes a read from a write.

## Detectability depends on coding style, not on function

The clearest pattern in the per-addon results:

| addon | found | why |
|---|---|---|
| Questie | 8/11 | calls named APIs directly: `HBDPins:AddWorldMapIconMap`, `LibDBIcon:Register`, `C_NamePlate.GetNamePlateForUnit` |
| OpenMap | 2/10 | stitches its own map art; no library call names what it does |
| MoveAny | 2/14 | drives about 115 frames from tables, so `PlayerFrame:SetPoint` never appears literally |

MoveAny and Questie do comparable amounts of work to the interface. The scan
sees one and not the other, purely because one writes calls a pattern can match
and the other writes a loop over data. **A manifest generator would therefore
systematically under-report exactly the addons that touch the most frames** -
the ones whose conflicts matter most. For `ui.*` slots this is close to a
guarantee: a frame-moving addon worth its name is data driven.

The same slot can be a false positive in one addon and a false negative in
another. `quest.detail` is invented for Questie, which only reads the frame, and
missed for MoveAny, which really does move it.

## What the scan found that the hand-written manifests had missed

One entry, and it is worth more than the percentages: **Spoken declares four key
bindings** (`_G.BINDING_NAME_SPOKEN_PLAYPAUSE`, skip, stop, compendium) and
applies them with `SetBinding`, clearing the previous key first
(`Spoken/UI/Options.lua:43`, `:617`). The hand-written manifest did not have the
`keybinding` slot. The manual pass had read that very file for Spoken's settings
and not noticed its bindings.

`manifests/spoken.yaml` now carries the entry, and says in its `unknown` list
that a tool found it. The project's argument is that a human reading the code
produces the better manifest. That is true on average, and it was false here.

## What is not even attempted

Three slot families are absent from the pattern file on purpose, because a
pattern is the wrong instrument:

- `data.quests`, `data.items`, `data.zones`. A bundled database is visible in
  the folder's shape - 353 Lua files under `Database/`, or 14 MB of base64 in a
  `.toc` - not in any call. QuestieDB scores 0/1 for this reason.
- `map.route`, `profession.sidebar`, `spellbook.tab`, `trainer.list`. Addons
  build these from plain frames with no distinguishing API, so any pattern wide
  enough to find them would match half the test set.
- Everything in the `blind` list at the end of `mapping/api-patterns.yaml`:
  aspect, defaults, `reason`, `Yields-To`, `Clashes`, the nearest useful parent,
  and whether a call is ever reached.

## Conclusion for the format

The scan is kept, with its role stated: **a suggestion tool with citations, not
an author.** Every proposed entry carries the file and line that produced it, so
checking a proposal is faster than finding the call yourself - which is real
value at 46% precision, and no value at all if anyone mistakes the output for a
manifest. Every file in `tests/proposed/` begins with `proposed: true` and a
header saying so.

Phase 3's acceptance criterion is met in the only honest way available: the
quality report exists, it is measured against hand-written reference manifests,
and the measurement says the tool must not be trusted alone.
