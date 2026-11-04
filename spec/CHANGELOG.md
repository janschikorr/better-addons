# Specification changelog

Every change names the addon whose code made it necessary. A change without
evidence does not belong in the format.

## 0.2 — format version 2

Written after hand-reading OpenMap, MoveAny, ClassicUI Forever and Legacy
Forever (phase 2, bundle 1). Four addons were enough to show that version 0.1
predicted conflicts where addons cooperate and missed conflicts where they do
not.

This version was pulled forward from phase 8. The remaining fourteen manifests
would otherwise have been written against rules already known to be wrong.

### Added: `aspect` (§4.1)

One slot stood for three different things: what a frame shows, where it sits and
how it looks. Entries now say which.

- **Evidence:** OpenMap owns the map artwork and the view but leaves the window
  to MoveAny (`OpenMap/Map/Compat.lua:19`). ClassicUI Forever retextures the
  minimap (`Art/ThemeParts.lua:81`) while MoveAny moves it
  (`ele/minimap.lua:6`) — version 0.1 called that a conflict; it is not.
- **Also fixed:** MoveAny moving the quest frame while DialogueUI replaces it is
  a real risk that version 0.1 did not flag at all.
- **Side effect:** `retexture` moves from being a way to being `aspect: style`,
  which is where it belonged.

### Added: `Yields-To` (§5)

"I claim this slot only while that addon is absent." A loaded addon turns the
pair into a handover instead of a conflict.

- **Evidence:** OpenMap stands down from the map window for MoveAny
  (`Map/Window.lua:216`); MoveAny's minimap element returns immediately under
  ElvUI (`ele/minimap.lua:7`). Two of four addons read did this. Both wrote the
  code; neither could state it.

### Added: slot hierarchy (§3.5)

Occupying a slot now occupies its children.

- **Evidence:** ClassicUI Forever claimed `ui.skin` plus eight individual `ui.*`
  parts, stating the same thing twice. `ui.skin` became the parent slot `ui`,
  and its manifest lost eight redundant entries.
- **Also fixed:** MoveAny moves about 130 named frames, roughly 115 of which
  nothing else in the test set touches. They need no slots of their own — the
  nearest parent says enough. The registry stays a map of contested places, not
  of the whole interface.

### Changed: module defaults decide the assumption (§3.3)

When the runtime reports nothing, a `?` entry falls back to its declared
default, and `default` is now required.

- **Evidence:** ClassicUI Forever's parts default to on
  (`Core/Defaults.lua:7,61-64`), OpenMap's routes and minimap button default to
  off (`Map/Routes.lua:2`, `Map/Launcher.lua:13`). Version 0.1 assumed every
  `?` entry was active, calling it the cautious choice. It was wrong half the
  time, in whichever direction.

### Added: `Clashes` (§2.5)

A conflict that depends on a setting rather than on installation. Reported as a
note naming the settings.

- **Evidence:** OpenMap cooperates with Leatrix Maps — it lifts Leatrix's pins
  above its own artwork — while four Leatrix options fight its window and
  coordinates, which OpenMap names at login (`Map/Compat.lua:181`). `Breaks`
  would have been a lie; recording nothing lost the only warning that existed.
- **Consequence for testing:** the oracle's prediction for OpenMap plus
  Leatrix Maps changed from "conflict" to a clash naming those options. The
  original prediction was not decidable.

### Added: `reason` (§8)

Free text on any entry, saying why a way or aspect was chosen.

- **Evidence:** Legacy Forever draws map pins on its own frames instead of using
  Blizzard's pin system, because a data provider would taint the secure walk
  Forever's gamepad cursor performs each frame (`UI/MapCanvas.lua:5-13`).
  Recorded as `map.pins=custom-overlay` alone, the careful choice reads as the
  lazy one.

### Added: per-entry `interface` (§3.6)

- **Evidence:** ClassicUI Forever declares four interface numbers in one `.toc`,
  so "one manifest per `.toc`" does not give one manifest per game version.

### Decided against: fields for frame maintenance and layout reading (§9)

- OpenMap raises the frame levels of four other addons' pins so they stay
  visible (`Map/Compat.lua:56-129`).
- Legacy Forever reads where Questie's tracker sits and places its column clear
  of it (`UI/TrackerQuestie.lua:3-6`).

Both are real and deliberate, and neither changes any verdict. They stay in
`notes`. A field that changes no prediction is a field nobody fills in.

### Still open for 0.3

- Load order among several `hook` entries on one slot
- Whether two ways in the same additive slot are compatible is still the tool's
  assumption
- MoveAny decides its behaviour from `GetWoWBuild()` at load time, which neither
  the per-`.toc` rule nor `interface` narrowing covers
- `Clashes` names another addon's settings as free text, so nothing verifies
  that those settings still exist

## 0.1 — format version 1

First draft: `Provides`, `Depends`, `Recommends`, `Breaks`, slot expressions
with ways, version constraints, optional parts and namespaces. Written before
any addon code had been read, which is visible in hindsight — every 0.2 change
above corrects something that reading four addons disproved.

## 0.2.1 - bundle 3 of phase 2

Nothing in the keywords changed. The registry gained slots and ways, the
validator gained a check, and six findings were recorded that the format cannot
express yet. The findings are in the manifests' `unknown` lists; the three worth
repeating here are at the end.

### The validator now checks ways against the registry

`manifests/aegis-instance-journal.yaml` said `via: custom-frame` on
`journal.dungeon`, where the registry lists `standalone-frame`. It validated
cleanly, because nothing compared the two. `tools/validate.py` gained
`check_ways`, and running it found four real errors in manifests that had
already been accepted - including two in `classicuiforever.yaml` from bundle 1.
`examples/invalid/way-not-in-registry.yaml` now holds the case.

The way decides collisions in SPEC.md 6.1, so an unlisted way was an unchecked
claim. This is the second time a new check found errors in finished work; the
first was the hierarchy rule in 0.2.

### New slots

- `keybinding` - Aegis Instance Journal claims Shift-J at load when the player
  has no binding yet (`Core/Init.lua:51 SetBinding`). Two addons reaching for
  the same key is a conflict no interface slot described.
  ForeverDungeonJournal reaches the same end through `Bindings.xml`, which is
  the quieter way; the registry cannot yet tell the two apart.
- `trainer.frame`, `trainer.list` - What's Training? adds rows to the class
  trainer window (`Forever/Views.lua:1`), and SkillUp Forever reads it
  (`Integrations/Trainer.lua:1`).

### New ways

- `embedded-copy` on `map.pins` and `minimap.pins` - Questie embeds
  `HereBeDragonsQuestie-2.0`, a renamed HereBeDragons, so its pin pool is its
  own (`Questie/Modules/Map/QuestieMap.lua:53`). Naming each renamed copy as a
  way of its own would need a registry entry per library, so the way is general
  and the library goes in the entry's note.
- `retexture` on `minimap.layout`, `chat.frame`, `profession.frame`,
  `spellbook.frame` - ClassicUI Forever retextures all four. The registry was
  simply too narrow, which only became visible once ways were checked.
- `bundled` on `audio.sound` - Spoken ships pre-generated audio files and never
  calls SpeakText (`Spoken/SoundUtils.lua:120 PlaySoundFile`).
- `LibDataBroker` on `minimap.button` - What's Training? registers a broker
  object and leaves the button to a display addon (`Broker.lua:1`).
- `custom-overlay` on `minimap.pins` and `profession.sidebar` - War Effort draws
  on its own minimap layer (`MinimapEdge.lua:2`), SkillUp Forever overlays the
  professions window (`UI/DetailsBar.lua:1`).

### Corrected while doing this

`data.zones`, `data.quests` and `data.items` briefly listed `HereBeDragons`
among their ways, because a broad search-and-replace for the new
`embedded-copy` way matched every slot whose ways ended in `HereBeDragons]`.
`check_ways` caught it on the next run.

### Three findings the format cannot express

1. **Extending another addon's slot.** Spoken writes rows into DialogueUI's
   settings window (`Spoken/API.lua:258 DialogueUIOptions:Add`) and buttons onto
   its dialogs (`API.lua:178`). The slot belongs to DialogueUI; SPEC.md 3.4
   rightly forbids providing it, and no other keyword fits. Candidate for 0.3:
   an `Extends` keyword naming a foreign namespaced slot, silent when the host
   is absent.
2. **The .toc already does several of these jobs.** Spoken's data packages
   carry `Group`, `X-Part-Of` and `X-Child-Of`, which is the family relation
   that forced a collective manifest. What's Training? gates its dependencies
   per client with `[AllowLoadGameType camelot][ExcludeLoadGameType classic]`,
   which the client enforces and which the format's own `interface` narrowing
   duplicates and can contradict. SkillUp Forever declares `X-License`, the
   single most useful field for the quality guide, which the format lacks.
   0.3 should read these rather than invent parallels.
3. **Enabled is not loaded.** Spoken's audio packages are `LoadOnDemand` and
   say so in their own notes: it is fine for them to appear disabled or out of
   date, because Spoken loads them anyway. Every verdict rule in SPEC.md 6
   assumes installed-and-enabled means active. The phase 5 checker must report
   what is loaded, not what is ticked.
