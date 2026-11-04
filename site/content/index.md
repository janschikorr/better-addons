# Better Addons

**Make it visible what an addon occupies — and keep addons honest.**

AI assistants are producing a great many new addons right now. That creates two
problems at once, and Better Addons addresses both.

## Compatibility

More addons means more collisions. Two addons that both want to own the world map
frame do not cooperate — one of them simply stops working, often without an error
message.

Better Addons introduces a small manifest: four keywords in the addon's `.toc`
that state which **slots** of the interface it occupies, what it needs, what it
recommends, and what it cannot run alongside. From that, a conflict can be found
before the player ever sees it.

## Anti-slop

More addons also means more quickly generated, unreviewed addons: invented API
calls, errors swallowed wholesale, per-frame polling instead of events, inflated
descriptions promising features that are not there.

Anti-slop is not anti-AI — this project is built with AI itself. What gets judged
is the result, not the tool. The project works at three points:

1. **Prevent.** A context file carries the quality rules, so an addon built with an
   AI assistant starts out clean instead of being corrected afterwards. This is the
   strongest lever.
2. **Check.** The scan script produces a quality report alongside the manifest.
3. **Show.** Addons that pass the manifest and quality checks may carry a badge.

## Status

Phase 1 of nine. The specification, the slot registry and the schema exist; the
scan script, the checker addon and the quality guide follow. Nothing here is
stable yet — the format is explicitly versioned so it can change without breaking
the manifests already written.

- [Compatibility overview](compatibility/) — what is known about which addon
- [Slot registry](slots/) — every slot, and who occupies it
- [Specification](spec/) — the format in full
- [For developers](developers/) — a manifest in five minutes
