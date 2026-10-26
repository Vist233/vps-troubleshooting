# vps-troubleshooting

When a VPS gets slow, refuses connections, or lets a page load but not a login, hand it to an AI that follows a fixed procedure: measure first, decide which layer is failing, and only then change anything.

Works with any VPS and any provider. Different datacenters, different routes, same method.

**You do not need to know Linux or networking.** You only need to describe the symptom.

## How to use

Send this to any AI that can read a URL or a file (Claude Code, Codex, Cursor, pi):

```
Read skill/vps-troubleshooting/SKILL.md from https://github.com/Vist233/vps-troubleshooting
and diagnose my VPS following its procedure. Read-only checks first.
```

The AI starts with **read-only checks** and changes no configuration. Before any change it must show you the plan and the rollback, and you decide.

If you are comfortable on a command line, read the matching file under `skill/vps-troubleshooting/references/` directly. Each contains the commands and the criteria for interpreting them.

## How it diagnoses

You do not need to understand this, but it helps to know what the agent is doing:

1. **Read-only baseline** — OS, open ports, kernel settings, NIC errors, failed services. Look, do not touch
2. **Layered measurement** — measure the server's own speed first, then one connection, then several, and pin the problem to a layer
3. **Controlled comparison** — before changing something, alternate between "changed" and "unchanged" instead of trusting a feeling
4. **Options, not orders** — what each option can and cannot improve
5. **You decide** — change it, roll it back, or do nothing

### Symptom to branch

| What you see | Check first | Details |
| --- | --- | --- |
| New host, nothing configured | OS, arch, used ports, then pick a transport | [deploy](skill/vps-troubleshooting/references/deploy.md) |
| Works, but slow | Measure the VPS's own speed first | [slow-path](skill/vps-troubleshooting/references/slow-path.md) |
| Connection times out or resets | Both firewalls, then the path | [unreachable](skill/vps-troubleshooting/references/unreachable.md) |
| Page loads but login fails | The exit IP, then classify the rejection | [login-blocked](skill/vps-troubleshooting/references/login-blocked.md) |
| Multiple devices, subscription will not load | Separate download failure from parse failure | [multi-device](skill/vps-troubleshooting/references/multi-device.md) |

## Measured

A Los Angeles VPS, client in Beijing on a mobile network. All data from the three steps, from following this repository's method rather than estimating.

| Step | Measurement | Result | Meaning |
| --- | --- | ---: | --- |
| 1 Locate the layer | VPS to internet download | ~45 MB/s | Server uplink is not the bottleneck |
| 1 Locate the layer | Single connection download | 14–15 KB/s | Three orders of magnitude below the server |
| 1 Locate the layer | Four parallel connections | 51.5 KB/s total | Capacity exists; one flow is throttled |
| 1 Locate the layer | RTT | ~195 ms | Long path, slow window growth |
| 1 Locate the layer | Packet loss | 6.7%–20% | Intermittent loss collapses a loss-based algorithm |
| 1 Locate the layer | cwnd during transfer | 1–3 MSS | Window collapsed |
| 1 Locate the layer | Retransmission | ~15.7% | Real loss, not just latency |
| 2 Change congestion control | CUBIC (median of three rounds) | 34.0 KB/s | Control arm |
| 2 Change congestion control | BBR (median of three rounds) | 108.6 KB/s | About 3.19×, still not fast |
| 3 Change the entry | Original node, direct | 1.075 MB/s | Control arm, Shadowsocks |
| 3 Change the entry | New setup through Cloudflare | 1.592 MB/s | About 48% above the original node |
| 3 Change the entry | Same protocol, direct to origin | 1.347 MB/s | About 18% above same-protocol direct |

Steps 2 and 3 both alternated three rounds. The six BBR readings: CUBIC 34.0 / 29.8 / 42.4, BBR 110.9 / 104.2 / 108.6. Ranges overlapped in both steps, so these are medians and orders of magnitude, not fixed multiples.

**The key evidence is the single-versus-parallel gap in step 1**: four streams totalling 51.5 KB/s while one stream gets 15 KB/s means the link has headroom and the problem is per-connection congestion control, not bandwidth.

The same table shows the other half of what measuring is for. BBR really did triple the throughput, **and 108 KB/s is still slow**, which proves this host is unsuitable as a primary egress. "The change worked" and "not worth pursuing further" can both be true.

## FAQ

### I know nothing about this. Can I still use it?

Yes. Describe the symptom, for example "it crawls at night" or "pages spin but WeChat works fine". The AI does the investigating; you decide whether to change anything.

### Will it break my server?

It starts read-only. Neither the baseline nor the measurement changes any configuration. Before a real change the procedure requires a stated rollback, one change at a time, and an immediate re-measure.

### How is this different from other AI skills?

Most VPS tooling hands you a set of "optimised" values or a one-shot script, reboots, and leaves you judging by feel.

The difference here is **measure, then decide**:

- Claims have an evidence bar. A comparison must alternate arms with at least three samples each. Run one test and announce a "3× speedup" and the bundled script refuses to conclude
- It states what it cannot do. A CDN changes the entry but not the exit IP; BBR improves the sending side but creates no capacity
- It draws boundaries instead of making promises. No provider recommendations, no shared nodes, no protocol rankings

If what you want is one command that fixes everything, this repository is not that.

### Can I just copy a set of recommended kernel settings?

No. Buffer size depends on bandwidth times latency, memory, concurrency, and what the machine is for. Copying a 256 MB buffer onto a 1 GB host turns it into a liability.

## Out of scope

- No provider recommendations, no shared nodes, no protocol rankings
- No `curl | sh` installer
- No promise that any exit passes a third party's risk checks
- "It works" is not the same as "it is secure"

## Layout

```
skill/vps-troubleshooting/SKILL.md      entry point for an AI: routing, evidence order, decision rules
skill/vps-troubleshooting/references/   five branches with commands and criteria
skill/vps-troubleshooting/scripts/inspect.sh   read-only host baseline
skill/vps-troubleshooting/scripts/measure.py   alternating comparison; rejects unbalanced samples
```

`scripts/` is for the agent to run, not for manual use.

`SKILL.md` stays short so only the relevant branch gets loaded.

## License

MIT.
