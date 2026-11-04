# Better Addons – Manifest Specification

**Spec version:** 0.1 · **Format version:** `1` · **Status:** draft (phase 1)

A Better Addons manifest states **what part of the interface an addon occupies**
and **how it relates to other addons**. From those statements, conflicts and
incompatibilities can be determined without starting the game.

A manifest can live in either of two places:

| Place | When | Format |
| --- | --- | --- |
| `## X-BetterAddons-*` lines in the `.toc` | The addon maintains its own data | TOC fields (this document) |
| `manifests/<addon>.yaml` in this repository | The addon has no manifest yet | YAML, same fields (see [`manifest.schema.json`](manifest.schema.json)) |

**One manifest per `.toc` file.** Forever addons commonly ship a separate `.toc`
per game version (`Addon_Vanilla.toc`, `Addon_Mists.toc`, …), and the slots they
occupy can differ between those versions.

---

## 1. Terms

| Term | Meaning |
| --- | --- |
| **Slot** | A distinguishable place in the interface or game state that an addon can occupy — e.g. `map.window` (the world map frame) or `minimap.layout` (shape and position of the minimap). All slots are listed in [`slots.yaml`](slots.yaml). |
| **Way** (`slot=way`) | *How* the slot is occupied. Two addons in the same slot using the **same** way collide; using different ways they usually do not. Example: `map.pins=HereBeDragons` versus `map.pins=native`. |
| **exclusive** | Slot property: only one addon can occupy it meaningfully. Two providers of the same exclusive slot are a **conflict**. |
| **additive** | Slot property: several addons can occupy it at once, as long as the ways are compatible. |
| **Interaction kind** | How the addon touches the slot: `replace`, `hook`, `add`, `modify` (see §4). |
| **Conflict** | Both addons occupy the same exclusive slot, or one names the other in `Breaks`. The result is visibly broken, or one addon loses its function. |
| **Incompatible** | A `Depends` entry is unmet — the addon is missing, or its version falls outside the stated range. |
| **Compatible** | No conflict and no unmet `Depends`. |

---

## 2. The four keywords

All fields are TOC metadata and start with `## X-BetterAddons-`.

### `Provides` — what the addon occupies

```
## X-BetterAddons-Provides: map.window, map.pins=HereBeDragons>=2.0, minimap.layout?
```

A comma-separated list of **slot expressions** (§3). Each entry claims: this addon
occupies this slot, in this way.

### `Depends` — what must be present

```
## X-BetterAddons-Depends: HereBeDragons>=2.0, questie:tracker.lines
```

A comma-separated list of **addon names** (the TOC folder name) or **slot names**.
A slot name means: some loaded addon must provide that slot. If an entry is unmet,
the addon counts as **incompatible** with the current installation.

`Depends` does not replace Blizzard's `## RequiredDeps`. It describes the
*functional* dependency, including dependencies on slots, not load order.

### `Recommends` — what makes the addon better

```
## X-BetterAddons-Recommends: Questie, map.pins=HereBeDragons
```

Same syntax as `Depends`, but with no effect on the verdict. An unmet
recommendation is shown as a note, not as a problem.

### `Breaks` — what must not run alongside

```
## X-BetterAddons-Breaks: Mapster<3.0, Leatrix_Maps
```

A comma-separated list of addon names with an optional version constraint. An
entry without a version means **every** version breaks. `Breaks` is always a
**conflict**, even when no shared slot is detectable — the addon author knows
better than the tool.

`Breaks` is declared one-sidedly but applies both ways: if A names B, the pair
A+B is a conflict even when B says nothing about A.

---

## 3. Slot expressions

```
slot                     plain occupation
slot=way                 occupation by a specific way
slot=way>=2.0            way with a version constraint
slot?                    applies only while the corresponding module is enabled
addon:slot               a slot the addon itself offers (namespace)
```

Slot names are lowercase segments separated by dots —
`^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$` — optionally prefixed with a namespace
`<addon>:`.

### 3.1 Format version

```
## X-BetterAddons-Format: 1
```

**Required** whenever any of the four keywords is used. A tool that encounters a
format version higher than it knows reports the manifest as *unread* instead of
misreading it. That lets the format grow without breaking existing manifests.

### 3.2 Version constraints

Debian-style notation. Permitted operators are `<<`, `<=`, `=`, `>=`, `>>`, plus
the short forms `<` (= `<<`) and `>` (= `>>`):

```
map.pins=HereBeDragons>=2.0      way must be at least version 2.0
Breaks: Mapster<3.0              breaks with Mapster before 3.0
Depends: Questie>=10.0.0
```

Versions are compared segment by segment: numeric segments numerically, others
character by character. With no version given, the constraint matches any version.

### 3.3 Optional parts

A trailing `?` marks an entry that **applies only while the corresponding module
is enabled**:

```
## X-BetterAddons-Provides: map.window, minimap.layout?
```

The addon reports its enabled modules at runtime through a plain global table —
no dependency on Better Addons:

```lua
BetterAddons_Active = BetterAddons_Active or {}
BetterAddons_Active["MyAddon"] = { ["minimap.layout"] = true }
```

If the table is absent, the checker treats every `?` entry as **enabled** — the
more cautious assumption.

### 3.4 Namespaces

Slots an addon offers **to others** carry its folder name as a lowercase prefix:

```
questie:tracker.lines
openmap:canvas.overlay
```

Only the addon itself may provide slots inside its namespace; others may name
them in `Depends` and `Recommends`.

---

## 4. Interaction kinds

The interaction kind is not written in the TOC fields. It is derived from the code
by the scan script and recorded in the YAML manifest. It decides how strictly a
double occupation is judged.

| Kind | Meaning | Double occupation |
| --- | --- | --- |
| `replace` | The original is replaced or hidden | conflict |
| `hook` | An existing function is wrapped | usually fine, order may matter |
| `add` | Something is added, nothing changed | fine |
| `modify` | Values or properties are changed | conflict only in exclusive slots |

---

## 5. Verdict for a pair of addons

Checked in this order; the first match decides:

1. A names B in `Breaks` (version matching), or B names A → **conflict**
2. A and B occupy the same **exclusive** slot, both entries active → **conflict**
3. A and B occupy the same **additive** slot via **different, incompatible** ways,
   and at least one interacts with `replace` → **conflict**
4. Any `Depends` entry of A or B is unmet → **incompatible**
5. Otherwise → **compatible**; unmet `Recommends` are listed as notes

If either addon has no manifest at all, the verdict is **unknown** — not
"compatible".

---

## 6. Full example

```
## Interface: 11507
## Title: OpenMap
## Version: 2.4.1
## X-BetterAddons-Format: 1
## X-BetterAddons-Provides: map.window, map.pins=HereBeDragons>=2.0, openmap:canvas.overlay
## X-BetterAddons-Depends: data.zones
## X-BetterAddons-Recommends: Questie
## X-BetterAddons-Breaks: Leatrix_Maps, Mapster<3.0
```

The same thing as `manifests/openmap.yaml`:

```yaml
format: 1
addon: OpenMap
toc: OpenMap.toc
versions: ">=2.4.0"
provides:
  - slot: map.window
    via: native
    kind: replace
    source: "OpenMap/Core.lua:812 WorldMapFrame:SetParent"
  - slot: map.pins
    via: HereBeDragons
    via_version: ">=2.0"
    kind: add
    source: "OpenMap/Pins.lua:44"
  - slot: openmap:canvas.overlay
    kind: add
depends:
  - data.zones
recommends:
  - Questie
breaks:
  - addon: Leatrix_Maps
  - addon: Mapster
    version: "<3.0"
```

Every YAML entry read from code carries a `source` field with file and line.
Hand-written manifests (phase 2) carry it too — it is the evidence that the entry
was not guessed.

---

## 7. Open points for v0.2

- Load order when several `hook` interactions touch the same slot
- Slots for combat and data sources (`combat.*`, `data.*`) — not dependable before phase 2
- Several ways in one `Provides` entry (e.g. "native **or** HereBeDragons")
- Whether two ways in the same additive slot are compatible is currently the tool's
  assumption, not a statement in the manifest
