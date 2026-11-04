# Quality guide

> Status: phase 1. This is the working set of rules, distilled from the recurring
> slop patterns. The full guide is written in phase 9, once scanning the thirteen
> test addons has shown which rules actually catch something.

Anti-slop does not mean anti-AI. Better Addons is built with AI itself. What gets
judged is the result, not the tool. Slop is what was generated quickly and never
reviewed, and it shows up in recurring patterns.

| Pattern | Rule | Checked by |
| --- | --- | --- |
| Calls to functions that do not exist in this game version | Use API that exists here | scan script, against the extracted API surface (see below) |
| The old global call where a modern namespace exists, e.g. `GetContainerNumSlots` instead of `C_Container.GetContainerNumSlots` | Prefer the `C_*` namespace | scan script |
| Errors swallowed wholesale, e.g. `pcall` around everything | Let errors surface; handle them deliberately | scan script |
| Polling every frame (`OnUpdate`) instead of reacting to events | Work from events | scan script |
| Unprefixed global variables | Keep everything in your own namespace | luacheck |
| Secret values used as if they were plain numbers | Check before using a value the API marks secret | scan script, against the 2798 functions with `SecretArguments` |
| Copied databases with no provenance | Name source and licence; prefer shared data packages | review |
| Arbitrary look: gradients, emoji in the interface, every frame styled differently | Design guide, later with ready-made UI building blocks | review |
| Inflated description: emoji lists, superlatives, promised features | Use the [description template](description.md) | review |
| Stated behaviour does not match actual behaviour | Keep the manifest honest | runtime observation by the checker addon |
| Yet another addon for the same thing | Check the slot registry first; extend what exists | the info site shows the addons per slot |

Each rule says whether it is checked automatically or by review. A rule nobody can
check is a wish, not a rule - if it ends up in this table, it needs a column entry.

## Checking API calls

`tools/api_surface.py` extracts the API surface from
[Gethe/wow-ui-source](https://github.com/Gethe/wow-ui-source), which mirrors the
game's own interface code, including Blizzard's machine-readable API
documentation. For the `forever` branch at 1.60.1.70790 that is 4410 namespaced
functions, 1919 documented globals and 1816 events.

What that does and does not prove:

- **Namespaced `C_*` calls: provable.** The documentation covers those namespaces
  completely, so a `C_Something.Function` that is absent does not exist. The scan
  script may report it as a finding.
- **Global calls: not provable.** The documentation does not cover the old
  FrameXML globals - `CreateFrame`, `SetCVar`, `hooksecurefunc`,
  `InCombatLockdown` and many more are real but undocumented. Absence proves
  nothing. The extractor therefore also collects every identifier appearing
  anywhere in the game's UI code: present there means plausible, absent from both
  means **suspect**, and is reported as a question rather than a defect.

### A correction worth recording

The first draft of this guide assumed the common failure was API carried over
from Retail that does not exist in Forever. Comparing the two branches shows
otherwise: Forever 1.60.1 is an API *superset* of Retail 12.1.5. Only four
functions exist in Retail and not here, all in peripheral systems
(`C_PaperDollInfo`, `C_SecureTransfer`, `C_TransmogOutfitInfo`), while 185 exist
here and not in Retail.

So that rule was largely answering a problem that does not occur. The real risk
is the opposite: Forever carries **both** the classic globals and the modern
namespaces, so `GetContainerNumSlots` and `C_Container.GetContainerNumSlots` both
work. Mixing them is not an error the game will report, which is exactly why it
needs a rule. Genuinely absent classic calls do exist - `GetTradeSkillInfo` is
one - but they are the exception.

Reproduce it:

```bash
git clone --depth 1 --single-branch -b forever \
    https://github.com/Gethe/wow-ui-source.git forever
git clone --depth 1 --single-branch -b live \
    https://github.com/Gethe/wow-ui-source.git live
python tools/api_surface.py forever --label forever \
    --compare live --compare-label retail --out data/api/forever.json
```

The extracted file is derived data and is not committed; regenerate it instead.
