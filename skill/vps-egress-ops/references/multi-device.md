# Multi-device: decision rules

Human walkthrough with commands: [docs/05-multi-device.md](../../../docs/05-multi-device.md).

## One source of truth

One file, one URL, every device. Do not fork a "phone version" to work around a client problem — that turns one bug into two configs that drift.

If a device cannot load the shared file, that is a client diagnosis, not a reason to split.

## What must not be in a shared subscription

Absolute paths, a specific interface name, hardcoded CDN edge IPs, `tun`/DNS/`hosts` blocks, a local controller port. Each is device-specific and breaks portability.

Keep the shared file portable; let each device set its own DNS/TUN.

## Ruleset size

A ruleset assembled from public sources can reach ~120k entries / ~2.5 MB. On a phone with a memory ceiling this is a **plausible** cause of a blank node list — **plausible, not established**. Do not assert it without client-side evidence.

What is safe to say and do:

- gzip cuts fetch time substantially (measured ~180 s → ~42 s for ~2.5 MB → ~560 KB). Affects download only, never proxy throughput.
- Compiled rulesets (Mihomo MRS) load far faster than equivalent YAML for large sets.
- Merge groups that point at the same exit. Fewer groups, fewer per-device mistakes.
- **Never** put `REJECT` first in a service selection group: a fresh device inherits it and silently blocks everything.

## Diagnose "loads but node list is empty" in this order

1. Fetch the URL with the client's User-Agent from a normal network → is the server serving it intact?
2. Timeout vs parse error → network vs content/compatibility.
3. Does the client apply its own override? Inspect the client's **effective** config, not the server file. An override can inject fields the server never sent.
4. Retry with a trimmed ruleset → is size the variable? (diagnostic, not a shipped variant)
5. Same device and network, different client → is it that specific client?

Only then name the failing layer.

Do not conclude "client is broken" from one failure, or "config is fine" because a desktop fetched it. A desktop fetching successfully does not prove a phone can load it.

## Selection semantics

`select` is manual and does not fail over. If the user expects automatic fallback they need `url-test` or `fallback`, and must accept that the exit may change silently. State which behavior the subscription provides.

**Several groups pointing at one node is not redundancy.** With one exit, every group resolves to that exit.

## Adding a second entry

- New imports default to whichever entry measures better on the user's network — measure, do not assume.
- Existing devices may keep their previous selection; tell the user to switch manually.
- Keep the old entry working until the new one is verified from a real device.

## Output contract

```text
SUBSCRIPTION_URL=<redacted>  SIZE_RAW=<bytes>  SIZE_GZIP=<bytes>
FETCH_FROM_OUTSIDE=<status> <seconds>  SHA256=<hash>
PROXIES=<n> GROUPS=<n> RULESET_ENTRIES=<n>
DEVICE_A=<client+version> <result>
DEVICE_B=<client+version> <result>
FAILING_LAYER=<server|download|client parse|client override|ruleset size|undetermined>
PORTABILITY_EXCLUSIONS=<what you deliberately left out>
UNVERIFIED=<devices or networks not tested>
```
