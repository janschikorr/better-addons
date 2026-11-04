# Better Addons – Manifest Specification

**Spec version:** 0.2 · **Format version:** `2` · **Status:** draft

A Better Addons manifest states **what part of the interface an addon occupies**
and **how it relates to other addons**. From those statements, conflicts and
incompatibilities can be determined without starting the game.

A manifest can live in either of two places:

| Place | When | Format |
| --- | --- | --- |
| `## X-BetterAddons-*` lines in the `.toc` | The addon maintains its own data | TOC fields (this document) |
| `manifests/<addon>.yaml` in this repository | The addon has no manifest yet | YAML, same fields (see [`manifest.schema.json`](manifest.schema.json)) |

**One manifest per `.toc` file.** Forever addons commonly ship a separate `.toc`
per game version, and the slots they occupy can differ between those versions.
Where a single `.toc` covers several interface numbers, individual entries can be
narrowed with `interface` (§3.6).

> **What changed in 0.2.** Reading four addons showed that version 0.1 predicted
> conflicts where addons cooperate, and missed conflicts where they do not. The
> cause was one slot standing for three different things: what a frame shows,
> where it sits, and how it looks. Version 0.2 adds the `aspect` axis (§4),
> `Yields-To` for addons that stand down for one another (§5), slot hierarchy
> (§3.5), `Clashes` for conditional conflicts (§2.5), and makes module defaults
> affect the verdict (§3.3). [CHANGELOG.md](CHANGELOG.md) records the evidence
> for each change.

---

## 1. Terms

| Term | Meaning |
| --- | --- |
| **Slot** | A distinguishable place in the interface or game state that an addon can occupy — e.g. `map.art` or `minimap.layout`. All slots are listed in [`slots.yaml`](slots.yaml). |
| **Aspect** | *Which side* of the slot is touched: `content`, `geometry`, `style` or `behaviour` (§4). Two addons in the same slot touching different aspects usually cooperate. |
| **Way** (`slot=way`) | *How* the slot is occupied, e.g. `map.pins=HereBeDragons` versus `map.pins=native`. |
| **exclusive** | Slot property: only one addon can occupy it meaningfully **per aspect**. |
| **additive** | Slot property: several addons can occupy it at once, if their ways are compatible. |
| **Interaction kind** | `replace`, `hook`, `add` or `modify` (§4.2). |
| **Conflict** | Both addons occupy the same slot and aspect in colliding ways, or one names the other in `Breaks`. Something is visibly broken, or an addon loses its function. |
| **Clash** | A conflict that depends on a setting, not on installation (§2.5). Reported as a note naming the setting. |
| **Handover** | One addon stands down for the other by `Yields-To` (§5). Not a conflict; the checker reports which side yielded. |
| **Incompatible** | A `Depends` entry is unmet. |
| **Compatible** | None of the above. |

---

## 2. The five keywords

All fields are TOC metadata and start with `## X-BetterAddons-`.

### 2.1 `Provides` — what the addon occupies

```
## X-BetterAddons-Provides: map.art/content=stitched, map.window/geometry, minimap.layout/style?
```

A comma-separated list of **slot expressions** (§3). The aspect follows the slot
after a slash. Omitting it means `content`, which is the right default for an
addon that changes what a part of the interface shows — but an addon that only
moves or restyles frames **must** say so, or it will be read as replacing them.

### 2.2 `Depends` — what must be present

```
## X-BetterAddons-Depends: HereBeDragons>=2.0, questie:tracker.lines
```

Addon names (the TOC folder name) or slot names. A slot name means: some loaded
addon must provide that slot. An unmet entry makes the addon **incompatible**
with the current installation.

`Depends` does not replace Blizzard's `## RequiredDeps`; it describes the
functional dependency, not load order.

### 2.3 `Recommends` — what makes the addon better

Same syntax as `Depends`, with no effect on the verdict. Unmet recommendations
are shown as notes.

### 2.4 `Breaks` — what must not run alongside

```
## X-BetterAddons-Breaks: Mapster, Magnify, EnhanceQoL
```

Addon names with an optional version constraint. No version means every version
breaks. `Breaks` is always a conflict, even with no detectable shared slot — the
addon author knows better than the tool. It is declared one-sidedly and applies
both ways.

### 2.5 `Clashes` — conflict only under a setting

```
## X-BetterAddons-Clashes: Leatrix_Maps[UnlockMap,ScaleWorldMap,SimpleMapFrame]
```

The two addons coexist, except while one of the named settings is on. The
checker reports this as a note naming the settings, not as a conflict.

This exists because `Breaks` is all or nothing, and reality is not. OpenMap
cooperates with Leatrix Maps — it even lifts Leatrix's pins above its own
artwork — while three Leatrix options do fight it, and OpenMap says so at login
in its own words. Recording that as `Breaks` would be a lie; recording nothing
loses the only warning that exists.

Setting names in brackets are the other addon's own, verbatim, so a player can
find them. They are not machine-checkable and are not meant to be.

---

## 3. Slot expressions

```
slot                        content aspect, way unspecified
slot/geometry               a specific aspect
slot=way                    a specific way
slot/style=retexture        aspect and way
slot=way>=2.0               way with a version constraint
slot?                       applies only while the module is enabled
addon:slot                  a slot the addon itself offers (namespace)
```

Slot names are lowercase segments separated by dots —
`^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$` — optionally prefixed with `<addon>:`.

### 3.1 Format version

```
## X-BetterAddons-Format: 2
```

**Required** whenever any keyword is used. A tool meeting a higher format
version than it knows reports the manifest as *unread* instead of misreading it.
A format 1 manifest is still valid: its entries are read as `aspect: content`,
which is what version 0.1 effectively meant.

### 3.2 Version constraints

Debian-style: `<<`, `<=`, `=`, `>=`, `>>`, plus `<` and `>`. Compared segment by
segment, numeric segments numerically. No version means any version.

### 3.3 Optional parts, and what they default to

A trailing `?` marks an entry that applies only while its module is enabled:

```
## X-BetterAddons-Provides: map.art/content, minimap.layout/style?
```

The addon reports enabled modules at runtime through a plain global table — no
dependency on Better Addons:

```lua
BetterAddons_Active = BetterAddons_Active or {}
BetterAddons_Active["MyAddon"] = { ["minimap.layout"] = true }
```

**When nothing is reported, the module's declared default applies** — not a
blanket assumption of "enabled". A YAML manifest states it per module:

```yaml
modules:
  minimap.layout:
    title: Minimap restyling
    default: false
```

In a `.toc`, `?` means "default off" and `?!` means "default on":

```
## X-BetterAddons-Provides: minimap.layout/style?!, map.route/content?
```

Version 0.1 assumed every `?` entry was active, on the grounds that it was the
cautious choice. That turned out to be wrong half the time: ClassicUI Forever's
parts default to on, OpenMap's default to off. A wrong assumption in either
direction produces a wrong prediction, and the addon already knows the answer.

### 3.4 Namespaces

Slots an addon offers **to others** carry its folder name as a lowercase prefix:
`questie:tracker.lines`, `openmap:canvas.overlay`. Only that addon may provide
them; others may name them in `Depends` and `Recommends`.

### 3.5 Slot hierarchy

Dots make a hierarchy, and it is binding: **occupying a slot occupies all of its
children.** An addon claiming `ui/style` claims `ui.unitframe.player/style` with
it, and conflicts with another addon that claims only the child.

This keeps the registry a map of *contested* places rather than of the whole
interface. MoveAny moves about 130 named frames, of which roughly 115 share no
frame with anything else in the test set. Those need no slot of their own: the
nearest parent says enough until a second addon touches the same frame.

A child is never implied upwards: claiming `ui.unitframe.player` says nothing
about the rest of `ui`.

### 3.6 Narrowing an entry to a game version

```yaml
  - slot: ui.actionbar.layout
    aspect: style
    interface: [16001]
```

One `.toc` may declare several interface numbers — ClassicUI Forever declares
four — and the slots need not be the same for all of them. Without `interface`,
an entry applies to every interface number in the `.toc`.

---

## 4. Aspect and interaction kind

### 4.1 Aspect: which side of the slot

| Aspect | What it covers | Example |
| --- | --- | --- |
| `content` | What is shown or supplied | DialogueUI replaces the quest frame |
| `geometry` | Position, size, scale | MoveAny |
| `style` | Textures, fonts, colours | ClassicUI Forever retextures the minimap |
| `behaviour` | Response to input, automation | OpenMap's zoom behaviour |

The aspect exists because version 0.1 collapsed all four into one slot and so
predicted a conflict between ClassicUI restyling the minimap and MoveAny moving
it, which are in fact compatible — while missing the real risk of MoveAny moving
the quest frame that DialogueUI has replaced.

### 4.2 Interaction kind: how it is touched

| Kind | Meaning |
| --- | --- |
| `replace` | The original is replaced or hidden |
| `hook` | An existing function is wrapped |
| `add` | Something is added, nothing changed |
| `modify` | Values or properties are changed |

---

## 5. `Yields-To` — standing down for another addon

```
## X-BetterAddons-Yields-To: MoveAny=map.window, ElvUI=minimap.layout
```

"I claim this slot only while that addon is absent." If the named addon is
loaded, the entry does not apply, and the pair is a **handover**, not a conflict.

Two addons in a thirteen-addon test set already do this: OpenMap leaves the map
window to MoveAny when MoveAny is installed, and MoveAny's minimap element
returns immediately under ElvUI. Both wrote the code; neither could state it.
Without this field the tool predicts a conflict where the addons have already
agreed who wins — the worst kind of false positive, because it trains players to
ignore warnings.

The checker reports which side actually yielded, so a handover that fails to
happen is still visible.

---

## 6. Verdict for a pair of addons

Checked in this order; the first match decides.

1. A names B in `Breaks` (version matching), or B names A → **conflict**
2. A `Yields-To` B for a slot, and B is loaded → that entry of A is dropped, and
   the pair is noted as a **handover**; carry on checking the remaining entries
3. For every slot both occupy — including by hierarchy (§3.5) — with both entries
   active per §3.3, apply the collision table below. Any conflict → **conflict**
4. A names B in `Clashes`, or B names A → **clash**, naming the settings
5. Any `Depends` entry of A or B unmet → **incompatible**
6. Otherwise → **compatible**; unmet `Recommends` are listed as notes

If either addon has no manifest, the verdict is **unknown** — not "compatible".

### 6.1 Collision table

For two entries on the same slot:

| | same aspect, exclusive slot | same aspect, additive slot | different aspect |
| --- | --- | --- | --- |
| `replace` + `replace` | conflict | conflict | see below |
| `replace` + `modify` | conflict | conflict | see below |
| `replace` + `add` | conflict | note | see below |
| `modify` + `modify` | conflict | compatible | see below |
| `modify` + `add` | note | compatible | see below |
| `add` + `add` | compatible | compatible | compatible |
| anything + `hook` | compatible, note if order matters | compatible | compatible |

**Different aspects** are compatible, with one exception: a `content` entry with
kind `replace` conflicts with any other addon's `geometry` or `style` entry on
the same slot. Replacing what a frame shows leaves nothing for the other addon
to move or restyle.

Two entries from the same addon never collide with each other.

---

## 7. Full example

```
## Interface: 16001
## Title: OpenMap
## Version: 0.7.5
## X-BetterAddons-Format: 2
## X-BetterAddons-Provides: map.art/content=stitched, map.view/behaviour=stitched, map.window/geometry, map.pins/content=native, minimap.button/content?
## X-BetterAddons-Recommends: Questie, ForeverDungeonJournal
## X-BetterAddons-Breaks: Mapster, Magnify, EnhanceQoL
## X-BetterAddons-Clashes: Leatrix_Maps[UnlockMap,ScaleWorldMap,SimpleMapFrame,ShowCoords]
## X-BetterAddons-Yields-To: MoveAny=map.window
```

The YAML equivalent is in [`../manifests/openmap.yaml`](../manifests/openmap.yaml),
where every entry additionally carries the `source` it was read from, and a
`reason` where the choice needs one.

---

## 8. `reason`: why, not just what

Any entry may carry a free-text `reason`. It is not machine-checkable and is not
meant to be — it exists so that a careful decision does not read like a careless
one.

Legacy Forever draws its map pins on frames of its own instead of using
Blizzard's pin system. Recorded as `map.pins=custom-overlay` alone, that looks
like the lazy option. The reason is that adding a data provider would put addon
values into the secure walk Forever's gamepad cursor performs every frame, and
taint its later protected calls. One sentence turns a suspicious entry into a
documented one, and it is the same sentence a quality review needs.

---

## 9. Deliberately not in the format

Two things found while reading addons were left out, because they carry no
prediction:

- **Maintaining another addon's frames.** OpenMap raises the frame levels of
  Leatrix Maps, Azeroth Tripview, Books on Map Forever and RareScanner so their
  pins stay visible above its artwork. Admirable, and irrelevant to any verdict.
- **Reading another addon's layout.** Legacy Forever looks up where Questie's
  tracker sits and places its own column clear of it. A one-way dependency on
  another addon's internals, but `Depends` would be wrong: it works fine without
  Questie.

Both belong in `notes`. A field that changes no prediction is a field nobody
fills in.

---

## 10. Open points for v0.3

- Load order when several `hook` entries touch the same slot
- Whether two ways in the same additive slot are compatible is still the tool's
  assumption, not a statement in the manifest
- MoveAny decides its behaviour from `GetWoWBuild()` at load time rather than
  from which `.toc` the client picked; `interface` narrowing does not cover that
- `Clashes` names another addon's settings as free text, so nothing verifies that
  those settings still exist
