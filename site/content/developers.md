# For developers

## A manifest in five minutes

Add five lines to your `.toc`. Only `Format` and `Provides` really matter at the
start.

```
## X-BetterAddons-Format: 1
## X-BetterAddons-Provides: map.pins=HereBeDragons, map.filter
## X-BetterAddons-Depends: data.zones
## X-BetterAddons-Recommends: Questie
## X-BetterAddons-Breaks: Leatrix_Maps
```

1. **Find your slots.** Open the [slot registry](../slots/) and look for the places
   your addon touches. A slot marked *exclusive* can only be owned by one addon —
   claim it only if you really replace that part of the interface. If you merely add
   pins or lines, claim the *additive* slot instead.
2. **Name the way.** `map.pins=HereBeDragons` and `map.pins=native` are different
   ways into the same slot and usually coexist. Leaving the way out means "however
   it happens", which is less useful to the checker.
3. **Mark optional parts.** A trailing `?` means the entry only applies while that
   module is enabled, e.g. `minimap.layout?`. Report enabled modules at runtime:

   ```lua
   BetterAddons_Active = BetterAddons_Active or {}
   BetterAddons_Active["MyAddon"] = { ["minimap.layout"] = true }
   ```

   No dependency on Better Addons is needed — it is a plain global table.
4. **One manifest per `.toc`.** If you ship one `.toc` per game version and the
   slots differ between them, the fields differ too.
5. **Be honest.** The checker addon watches at runtime which addon touches which
   frame. An entry that does not match actual behaviour is reported as a mismatch,
   which is worse than no entry at all.

## No slot fits?

Then the registry has a gap, not your addon. Open an issue naming the place in the
interface and how you touch it. The registry is version 0.1 and grows with exactly
these reports.

## Your addon has no manifest yet

A manifest can also live in this repository as `manifests/<addon>.yaml` — same
fields, YAML shape, checked by
[`spec/manifest.schema.json`](../spec/manifest.schema.json). Every entry carries a
`source` field pointing at the file and line it was read from. That is the whole
honesty mechanism: an entry without a source is a guess.

```bash
python tools/validate.py manifests/myaddon.yaml
```

## Building with an AI assistant

Drop [`AGENTS.md`](https://github.com/janschikorr/better-addons/blob/main/AGENTS.md)
into your project. It contains the specification, the workflow and the quality
rules in the form an assistant can follow, so the code comes out clean rather than
being cleaned up afterwards.

## Before you write a new addon

Look at the [slot registry](../slots/) first and see who already occupies the slot
you are aiming at. Forever already has more than half a dozen dungeon journal
addons. Extending an existing one is almost always the better contribution.
