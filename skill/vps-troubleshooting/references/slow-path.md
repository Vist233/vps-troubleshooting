# Slow: locate the bottleneck before tuning

"Slow" is not a diagnosis. It is at least five different failures that feel identical to the user. Separate them by measurement, cheapest first.

## Decision tree

```
Reported: slow
  │
  ├─ Is the VPS itself fast?          → test VPS to internet directly
  │    No  → server uplink / provider / hardware problem
  │    Yes ↓
  │
  ├─ Is one stream slow but N streams fine?
  │    Yes → congestion control / loss on the path   ← tuning can help
  │    No  ↓
  │
  ├─ Is it slow at all hours?
  │    No  → peak-hour congestion; tuning cannot add capacity
  │    Yes ↓
  │
  └─ Is the client's own network the limit?  → change network, retest
```

The order is mandatory. Each step can end the investigation, and the cheap steps rule out the most common wrong guesses.

## Step 1: is the server fast?

Test from the VPS to a nearby, well-connected target. Never to the user.

```bash
curl -o /dev/null -w '%{speed_download} B/s\n' \
  'https://speed.cloudflare.com/__down?bytes=10000000'
ip -s link show
```

Reading it: tens of MB/s with zero errors and drops means the server's uplink is not the bottleneck. Whatever the user sees below that is happening on the path, not on the box.

This eliminates the most common wrong guess: "the VPS is too weak" or "the provider oversold it".

## Step 2: single stream versus parallel streams

The most informative measurement in the whole procedure, and the only one that decides whether tuning is justified.

Download the same object twice: once as one stream, once as N parallel streams.

- single ≈ parallel total / N → the link has capacity and one flow is throttled. Congestion control, loss, or a shaper. Tuning is meaningful.
- single ≈ parallel total → the path itself is capped. More streams will not help, and neither will tuning.

One observed case: a single stream at about 15 KB/s while four parallel streams totalled about 51 KB/s. The capacity existed; one flow was being punished.

Record both numbers. Reporting only the single-stream figure invites the wrong fix.

## Step 3: RTT and loss on the real path

```bash
ping -c 30 <vps>
mtr -rwzc 30 <vps>     # if available
```

- RTT decides the bandwidth-delay product. About 195 ms means a long path where the window grows slowly.
- Loss: even 5% to 20% intermittent loss collapses a loss-based congestion algorithm. This is the usual cause of a tiny single-stream rate on a long path.
- Where loss starts: `mtr` shows the hop. Loss appearing only at the final hop is often ICMP rate-limiting rather than real loss. Confirm with TCP-side evidence.

Cross-border consumer links routinely show both high RTT and intermittent loss. That is a property of the path, not a misconfiguration.

## Step 4: confirm with TCP state

Throughput alone cannot distinguish "bad path" from "misconfigured server". Sample the live connection on the VPS during a transfer:

```bash
ss -tin dst <client-ip>
```

| Field | Meaning when small or large |
| --- | --- |
| `cwnd` | 1 to 3 MSS during a transfer means the window collapsed, from loss or throttling |
| `ssthresh` | Dropping to 2 means repeated loss events |
| `retrans` / `bytes_retrans` | A high ratio, such as about 15%, confirms real loss rather than latency |
| `rtt` | If it disagrees with ping, something is intercepting |
| delivery rate | Very low while the server uplink is fine points at the path |

This step turns "it feels slow" into "on a 195 ms path the window collapsed to 1 to 3 MSS with about 15% retransmission". The second statement is actionable; the first is not.

## Treatments, only after steps 1 to 4 point at the path

| Treatment | When | What it cannot do |
| --- | --- | --- |
| Change the sender's congestion control (BBR) | Step 2 shows single-flow throttling, and the path has loss and high RTT | Create capacity, fix the client-to-VPS segment, guarantee upload gains |
| Put a CDN in front of the entry | The client-to-VPS segment is the bottleneck and the transport is HTTP-family | Change the exit IP, guarantee a speedup, work with raw Shadowsocks |
| Change network or region | Tuning gains are marginal and the path lacks capacity | n/a |

### How to test BBR properly

Do not change the global setting. It affects every connection on the box. Set the algorithm per socket on an isolated test connection and leave the global value alone.

Comparison method:

- alternate control and treatment, for example `CUBIC, BBR, BBR, CUBIC, CUBIC, BBR`, so time-of-day drift cancels;
- report the median of several rounds, never the best round;
- upload often does not change, because the server's algorithm does not govern the client's sending side;
- if the ranges overlap, write "not established". Do not turn overlap into a percentage improvement.

On a bad path the realistic outcome is a few-fold improvement that is still not fast. Say that plainly.

### Check for contamination before measuring

If TUN, a system proxy, a VPN, or a stale DNS cache can reroute the test, the number is not about the intended path. Bind to the physical interface or disable the interceptor for the test, and say which you did.

## Anti-patterns

- Copying a sysctl block from a blog. Buffers depend on bandwidth times RTT, RAM, concurrency, and the host's role. A 256 MB buffer on a 1 GB box is a liability.
- Changing MTU because "1440 is usual". Probe PMTU first; a wrong MTU silently stalls some paths.
- Rate-limiting as soon as retransmissions appear. Retransmission is a symptom; capping throughput adds a second problem.
- Enabling BBR globally and calling it done. It affects every connection on the box.
- Reporting only the best round.
- Multiplying two independently measured speedups. `BBR × CDN` was never measured together.

## Stop conditions

Stop tuning and say so when:

- step 1 shows the server uplink is the limit, which is a provider or hardware problem;
- step 2 shows single ≈ parallel, so there is no capacity to recover;
- the problem appears only at peak hours, which is congestion rather than configuration;
- measured gains fall inside overlapping ranges.

## Report

```
SERVER_UPLINK=<B/s> errors=<n> drops=<n>
SINGLE=<B/s>  PARALLEL_N=<n> TOTAL=<B/s>
RTT=<ms> LOSS=<%> samples=<n>
TCP_STATE=cwnd=<n> ssthresh=<n> retrans=<ratio>
BOTTLENECK=<server uplink | single-flow congestion | path capacity | client network | undetermined>
TREATMENT=<none | congestion control | CDN entry | network change>
BEFORE_MEDIAN=<n> AFTER_MEDIAN=<n> ROUNDS=<n> RANGES_OVERLAP=<yes/no>
UPLOAD_CHANGED=<yes/no/not measured>
ENV_SPECIFIC=<what would not transfer to another ISP or hour>
ROLLBACK=<restore path>
UNVERIFIED=<peak hour, other devices, long-lived connections>
```
