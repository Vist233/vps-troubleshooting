# Multi-device: one subscription, several clients

Serving one configuration to a phone, a laptop, and a tablet sounds trivial and is where most support time disappears. The failures are usually in the subscription, the client, or the ruleset size, not in the proxy.

## One source of truth

One file, one URL, every device. Do not maintain a "phone version" and a "laptop version" unless a real incompatibility forces it.

```
/srv/clash/<token>.yaml   ← the only configuration
        │
        ├── HTTPS (gzip)  → device A
        ├── HTTPS (gzip)  → device B
        └── HTTPS (gzip)  → device C
```

One place to change a node, one hash to verify, no drift. If a device cannot load it, that is a client problem to diagnose, not a reason to fork the file.

## What must not be in a shared subscription

| Do not include | Why |
| --- | --- |
| Absolute filesystem paths | Valid only on the machine that wrote them |
| A specific interface name such as `en0` or `eth0` | Device-specific |
| Hardcoded CDN edge IPs | They change; use the hostname |
| `tun`, DNS, or `hosts` blocks | Every platform and client differs |
| A local controller port | Conflicts with the client's own |

Keep the shared file portable and let each device set its own DNS and TUN.

## Ruleset size

A ruleset assembled from public sources can reach about 120,000 entries and 2.5 MB of YAML. A desktop does not care. On a phone with a client memory ceiling, this is a plausible cause of a blank node list or a failed load. Plausible, not established. Do not assert it without client-side evidence.

What is safe to do regardless:

- Serve it gzipped. About 2.5 MB compresses to about 560 KB, and an observed fetch time fell from about 180 seconds to about 42. This affects download only, never proxy throughput.
- Prefer compiled rulesets. Mihomo's MRS is a binary format that loads far faster than equivalent YAML for large sets.
- Merge groups that exist for no reason. If "Google", "Gemini", and "Antigravity" all point at the same exit, they are one group.
- Never put `REJECT` first in a service selection group. A device with no cached selection inherits the first entry, and a silent block is very hard to diagnose.

## Diagnosing "the subscription loads but the node list is empty"

This is a client-side symptom with several possible causes. Distinguish them before changing the server.

1. Did the download succeed? Fetch the URL with the client's User-Agent from a normal network. If it returns the YAML intact, the server is fine.
2. Is it a fetch failure or a parse failure? A timeout means network; a load error with a parse message means content or compatibility.
3. Does the client apply its own override? Some clients merge a global script or profile over the subscription. That override can inject fields the server never sent. Inspect the client's effective config, not the server file.
4. Is the ruleset too large for this client? Test with a trimmed copy to see whether size is the variable. This is a diagnostic, not a shipped variant.
5. Same device and network, different client, does it work? If yes, the problem is that specific client.

Only then can you name the failing layer.

Do not conclude "the client is broken" from one failure, and do not conclude "the config is fine" because a desktop fetched it. A desktop fetching successfully does not prove a phone can load it.

## Selection semantics and expectations

A `select` group is manual and does not fail over.

If the user expects automatic fallback they need `url-test` or `fallback`, and must accept that the exit may change silently. State which behavior the subscription provides.

Several groups pointing at one node is not redundancy. With one exit, every group resolves to that exit.

## Adding a second entry later

- New imports should default to whichever entry measures better on the user's network. Measure, do not assume.
- Existing devices may keep their previous selection, so tell the user to switch manually.
- Keep the old entry working until the new one is verified from a real device.

## Report

```
SUBSCRIPTION_URL=<redacted>  SIZE_RAW=<bytes>  SIZE_GZIP=<bytes>
FETCH_FROM_OUTSIDE=<status> <seconds>
SHA256=<hash>
PROXIES=<n> GROUPS=<n> RULESET_ENTRIES=<n>
DEVICE_A=<client and version> <result>
DEVICE_B=<client and version> <result>
FAILING_LAYER=<server | download | client parse | client override | ruleset size | undetermined>
PORTABILITY_EXCLUSIONS=<what you deliberately left out>
UNVERIFIED=<devices or networks not tested>
```
