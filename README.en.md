# vps-troubleshooting

When a remote VPS is slow, unreachable, or a site refuses to let you sign in, measure first and locate the failing layer before changing anything.

Works with any VPS and any provider. Different datacenters and routes, same method.

## What it covers

- Decide whether the bottleneck is the server uplink, the cross-border path, or the client's own network
- Decide whether "can't connect" means a dead service, a closed firewall, wrong DNS, or a filtered path
- Decide whether enabling BBR is justified, and how to measure it as a real comparison
- Decide what a CDN can and cannot improve
- Locate why a multi-device subscription fails to load
- Separate "the tunnel connects" from "the site is usable"

## Usage

Send this to an AI agent:

```
Read skill/vps-troubleshooting/SKILL.md from https://github.com/<owner>/vps-troubleshooting
and diagnose my VPS following its procedure. Read-only checks first.
```

Without an AI, read the matching file under `skill/vps-troubleshooting/references/`. Each contains the commands and the criteria for interpreting them.

## Symptoms

| Symptom | First step | Details |
| --- | --- | --- |
| New host, nothing configured | Confirm OS, arch, used ports, then pick a transport | [deploy](skill/vps-troubleshooting/references/deploy.md) |
| Works but slow | Measure the VPS's own speed first | [slow-path](skill/vps-troubleshooting/references/slow-path.md) |
| Connection times out or resets | Check both firewalls, then the path | [unreachable](skill/vps-troubleshooting/references/unreachable.md) |
| Site loads but login fails | Check the exit IP, then classify the rejection | [login-blocked](skill/vps-troubleshooting/references/login-blocked.md) |
| Multiple devices, subscription won't load | Separate download failure from parse failure | [multi-device](skill/vps-troubleshooting/references/multi-device.md) |

## Measured case

A Los Angeles VPS, client in Beijing on a mobile network. Numbers below come from following this repository's method.

### Where the slowness was

| Measurement | Result | Meaning |
| --- | --- | --- |
| VPS to internet download | ~45 MB/s | Server uplink is not the bottleneck |
| Single stream | 14–15 KB/s | Three orders of magnitude below the server |
| Four parallel streams | 51.5 KB/s total | Capacity exists; one flow is throttled |
| RTT | ~195 ms | Long path, slow window growth |
| Packet loss | 6.7%–20% | Intermittent loss collapses a loss-based algorithm |
| cwnd during transfer | 1–3 MSS | Window collapsed |
| Retransmission | ~15.7% | Real loss, not just latency |

The gap between single and parallel streams is the core evidence here. Four streams totalling 51.5 KB/s while one stream gets 15 KB/s means capacity is available and the problem is per-connection congestion control, not bandwidth.

### After enabling BBR

Alternating rounds, algorithm set per test connection only; global setting stayed CUBIC:

| Round | CUBIC | BBR |
| --- | ---: | ---: |
| 1 | 34.0 KB/s | 110.9 KB/s |
| 2 | 29.8 KB/s | 104.2 KB/s |
| 3 | 42.4 KB/s | 108.6 KB/s |
| Median | 34.0 KB/s | 108.6 KB/s |
| Upload (one each) | 705 KB/s | 719 KB/s |

About 3.19× on download, but 108 KB/s is still not fast. Upload barely moved, because the server's algorithm does not govern the client's sending side.

### After fronting with Cloudflare

Same 4 MiB object, alternating rounds:

| Path | Median |
| --- | ---: |
| Original Shadowsocks, direct | 1.075 MB/s |
| New VLESS/WS through Cloudflare | 1.592 MB/s |
| Same protocol, direct to origin | 1.347 MB/s |

Cloudflare was ~48% above the original node and ~18% above the same protocol without it, with overlapping ranges across rounds. No fixed multiple can be promised, and it was sometimes slower.

Plain HTTPS control: download 0.993 → 1.700 MB/s, upload 543 → 497 KB/s.

### Subscription delivery

| Item | Value |
| --- | --- |
| Raw size | ~2.53 MB, 121,344 rules |
| After gzip | ~558 KB |
| Fetch time | ~180 s → ~42 s |

gzip affects subscription download only, never proxy throughput.

### What this case does not show

- Cloudflare changes the entry, not the exit; the exit IP is still that VPS, so site risk checks are unaffected
- BBR improves the sending side; it creates no capacity and cannot rescue a path with no headroom
- 108 KB/s means this datacenter on this route is unsuitable as a primary egress; changing protocols or tuning further will not fix it

## Layout

```
skill/vps-troubleshooting/SKILL.md      entry point for an AI: routing, evidence order, decision rules
skill/vps-troubleshooting/references/   five branches with commands and criteria
scripts/inspect.sh                 read-only host baseline
scripts/measure.py                 alternating comparison; rejects unbalanced samples
scripts/check-links.py             validates relative documentation links
```

`SKILL.md` stays short so only the relevant branch gets loaded.

## Out of scope

- No provider recommendations, no shared nodes, no protocol rankings
- No `curl | sh` installer
- No promise that any exit passes a third party's risk checks
- Functional availability is not security hardening

## FAQ

### BBR is on and it is still slow. Why?

BBR improves the sending side on a lossy path. If the limit is server uplink, path capacity, or peak-hour congestion, it does nothing. Measure single versus parallel streams: if they match, the path has no headroom and BBR cannot help.

### One stream is slow but parallel streams are fine. What is that?

The link has capacity and a single connection is being punished by loss. Check RTT and loss rate, then cwnd and retransmission during the transfer. Congestion control is a legitimate lever here.

### The service is running but nothing can connect from outside.

Usually the host firewall is open and the provider security group is closed. Check both, and test the port from outside with `nc` instead of reading either config.

### Does adding a CDN fix site login problems?

No. A CDN changes the entry path from client to VPS. The exit IP is unchanged, so the destination sees the same identity.

### Why can't Shadowsocks be put behind a CDN?

A CDN proxies HTTP-family traffic. Shadowsocks is raw TCP/UDP and cannot be layered onto it. Using a CDN requires an HTTP-family transport chosen before installation; changing later means reinstalling.

### The subscription downloads but the client shows an empty node list.

Separate download failure from parse failure. Download failure is network; parse failure is content or compatibility. The client may also apply its own override that injects fields the server never sent, in which case inspect the client's effective config. Ruleset size is one possible cause but cannot be concluded without client-side evidence.

### Results differ every run. How do I tell whether a change helped?

Alternate control and treatment in one session, for example `C,T,T,C,C,C,T`, and report medians over several rounds. If the ranges overlap, the difference is not established and must not be reported as a percentage improvement.

### Can I just copy a sysctl tuning block?

Better not. Buffer sizes depend on bandwidth times RTT, RAM, concurrency, and the host's role. A 256 MB buffer on a 1 GB box is a liability, not an optimization.

### How is this different from the VPS tuning scripts online?

Those scripts change parameters and restart services. This repository measures first and only then decides whether to change anything, and requires a rollback path. Many "optimizations" turn out to be unnecessary once measured.

## License

MIT.
