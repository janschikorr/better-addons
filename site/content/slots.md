# Slot registry

A **slot** is a distinguishable place in the interface or game state that an addon
can occupy. Slots marked *exclusive* can only be owned by one addon at a time: two
providers are a conflict. *Additive* slots take several addons, as long as they use
compatible ways.

The table below is generated from
[`spec/slots.yaml`](https://github.com/janschikorr/better-addons/blob/main/spec/slots.yaml),
so it cannot drift away from the specification. The **Addons** column fills up as
manifests are added.

Missing a slot? That is a gap in the registry, not in your addon - please open an
issue.
