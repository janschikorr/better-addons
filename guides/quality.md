# Quality guide

> Status: phase 1. This is the working set of rules, distilled from the recurring
> slop patterns. The full guide is written in phase 9, once scanning the thirteen
> test addons has shown which rules actually catch something.

Anti-slop does not mean anti-AI. Better Addons is built with AI itself. What gets
judged is the result, not the tool. Slop is what was generated quickly and never
reviewed, and it shows up in recurring patterns.

| Pattern | Rule | Checked by |
| --- | --- | --- |
| API calls or functions carried over from another game version that do not exist here | Use only documented API of the target version | scan script, against the API documentation |
| Errors swallowed wholesale, e.g. `pcall` around everything | Let errors surface; handle them deliberately | scan script |
| Polling every frame (`OnUpdate`) instead of reacting to events | Work from events | scan script |
| Unprefixed global variables | Keep everything in your own namespace | luacheck |
| Protected values touched in combat | Respect the restrictions of the target version | scan script |
| Copied databases with no provenance | Name source and licence; prefer shared data packages | review |
| Arbitrary look: gradients, emoji in the interface, every frame styled differently | Design guide, later with ready-made UI building blocks | review |
| Inflated description: emoji lists, superlatives, promised features | Use the [description template](description.md) | review |
| Stated behaviour does not match actual behaviour | Keep the manifest honest | runtime observation by the checker addon |
| Yet another addon for the same thing | Check the slot registry first; extend what exists | the info site shows the addons per slot |

Each rule says whether it is checked automatically or by review. A rule nobody can
check is a wish, not a rule - if it ends up in this table, it needs a column entry.
