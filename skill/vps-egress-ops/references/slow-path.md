# Slow path: decision rules

Human walkthrough with commands: [docs/02-slow.md](../../../docs/02-slow.md).

## Order is mandatory

Do not skip to tuning. Each step can end the investigation, and the cheap steps rule out the most common wrong guesses.

```
1. VPS → internet speed          rules out "server too weak"
2. single stream vs N parallel   rules out / confirms capacity
3. RTT + loss on the real path   explains the mechanism
4. TCP state (cwnd/retrans)      confirms it is not misconfiguration
   ↓ only now consider treatment
```

## The one measurement that decides the branch

Single stream vs N parallel streams, same object, same moment.

- **single ≈ total/N** → capacity exists; one flow is throttled → congestion control is a legitimate lever.
- **single ≈ total** → path is capped → **no amount of tuning adds capacity.**

Report both numbers. A single-stream figure alone misleads.

## Treatment rules

| Treatment | Only when | What it cannot do |
| --- | --- | --- |
| Congestion control (BBR) | Step 2 shows single-flow throttling on a lossy, high-RTT path | Create capacity; fix the client→VPS segment; guarantee upload gains |
| CDN-fronted entry | The client→VPS segment is the bottleneck and transport is HTTP-family | Change the exit IP; guarantee a speedup; work with raw Shadowsocks |
| Change network/region | Tuning gains are marginal and the path lacks capacity | — |

## Measurement discipline

- Alternate control and treatment in one session (`C,T,T,C,C,T`) so time-of-day drift cancels.
- Report the **median of several rounds**, never the best round.
- Report overlapping ranges as "not established". Do not turn overlap into a percentage improvement.
- State the sample count and the local time.
- Separate download from upload. Server-side congestion control does not govern the client's sending side.
- Never multiply two independently measured speedups. `BBR × CDN` was not measured.

## Contamination check before measuring

If the test can be routed by TUN, system proxy, VPN, or a stale DNS cache, the number is not about the intended path. Bind to the physical interface or disable the interceptor for the test, and say which you did.

## Anti-patterns

Refuse these and explain why:

- copying a sysctl block from a blog (buffers depend on bandwidth × RTT, RAM, concurrency, role);
- changing MTU because "1440 is usual" (probe PMTU first);
- rate-limiting on first retransmission (symptom, not cause);
- enabling BBR globally as a "fix" (affects every connection on the box);
- quoting one round as the result.

## Stop conditions

Stop tuning and say so when:

- step 1 shows the server uplink is the limit (provider/hardware problem, not tuning);
- step 2 shows single ≈ parallel (no capacity to recover);
- the problem only appears at peak hours (congestion, not configuration);
- measured gains are within the noise of overlapping ranges.

## Output contract

```text
SERVER_UPLINK=<B/s> errors=<n> drops=<n>
SINGLE=<B/s>  PARALLEL_N=<n> TOTAL=<B/s>
RTT=<ms> LOSS=<%> samples=<n> at=<local time>
TCP_STATE=cwnd=<n> ssthresh=<n> retrans=<ratio>
BOTTLENECK=<server uplink | single-flow congestion | path capacity | client network | undetermined>
TREATMENT=<none | congestion control | CDN entry | network change>
BEFORE_MEDIAN=<n> AFTER_MEDIAN=<n> ROUNDS=<n> RANGES_OVERLAP=<yes/no>
UPLOAD_CHANGED=<yes/no/not measured>
ENV_SPECIFIC=<what would not transfer to another ISP/hour>
ROLLBACK=<restore path>
UNVERIFIED=<peak hour, other devices, long-lived connections>
```
