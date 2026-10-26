---
name: vps-troubleshooting
description: Diagnose and tune a remote VPS that is slow, unreachable, or failing to log in to a site, using read-only evidence before any change. Covers path diagnosis, congestion control, CDN-fronted ingress, subscription distribution, and client routing. Use when the user owns a VPS and wants it usable as a stable egress; not for buying servers, choosing providers, or obtaining nodes.
---

# VPS egress ops

Turn a remote VPS into a stable egress, and locate the failing layer when it is slow or broken.

Provider-neutral. CloudCone, RackNerd, Vultr, Oracle, a home lab: same method, different path.

## Establish these before acting

Reuse anything already known from the session. Ask only for what is genuinely missing.

- Host: SSH target, OS, arch, whether the box is dedicated or shared with other services.
- Role: what this VPS is for, a landing/exit node, a relay, or a general server.
- Advertised bandwidth: the plan's port speed, up and down. Public speedtests disagree with this; prefer the plan.
- Client and ISP: which device and network the user actually uses. This decides whether a result is environment-specific.
- Current state: which services listen, what the subscription looks like now.
- Authorization: read-only inspection is usually fine; anything that writes needs approval for that specific change.
- Agent connectivity: if the agent reaches the user's machine through the VPS, a disruptive change can cut the agent off. Confirm recovery access before touching routing or the proxy.

If the agent's own channel depends on the thing being changed, say so and stop before the mutation.

## Evidence order

Trust in this order, and prefer the rightmost evidence available:

```
Declared config  →  Generated config  →  Runtime state  →  Observed traffic
```

Panel says healthy does not mean the config generated correctly, which does not mean the runtime loaded it, which does not mean traffic actually flows.

Before measuring, check for contamination: TUN, system proxy, VPN, `ProxyCommand`, or a stale DNS cache can silently redirect the test. A measurement taken through an unexpected path is not evidence about the intended path.

## Route to the right procedure

| Symptom | Read |
| --- | --- |
| New host, nothing configured yet | [deploy](references/deploy.md) |
| Works but slow | [slow-path](references/slow-path.md) |
| Connection times out or resets | [unreachable](references/unreachable.md) |
| Site loads but login fails | [login-blocked](references/login-blocked.md) |
| Multiple devices, one subscription | [multi-device](references/multi-device.md) |

Load only the branch the current symptom needs.

## Bundled tools

Two scripts in this skill's `scripts/` directory replace work you would otherwise redo by hand. Run them instead of improvising the equivalent commands.

- `scripts/inspect.sh` collects the read-only baseline every branch needs: OS and arch, listeners, proxy services, congestion control and qdisc, NIC errors and drops, default route, memory, failed units. Pipe it over SSH:

  ```bash
  ssh <host> 'bash -s' < scripts/inspect.sh
  ```

  It writes nothing. On a non-Linux host it says so instead of printing empty sections that look like findings.

- `scripts/measure.py` runs an alternating control/treatment comparison and refuses to call unequal sample counts a result:

  ```bash
  python3 scripts/measure.py --url <object> --rounds C,T,T,C,C,T
  ```

  Exit codes: `0` comparable, `2` bad arguments, `3` every attempt failed, `4` unbalanced arms. Treat `4` as "no conclusion", not as a speedup.

Use `inspect.sh` before recommending anything, and `measure.py` whenever you are about to claim a change helped. Do not restate their output as a conclusion the data does not support.

## Non-negotiable rules

1. Separate the two directions. Client to VPS and VPS to destination are different links with different bottlenecks. Never merge them into one speed number.

2. Separate transport from application. HTTP 401/403 after a working TLS handshake is an application-layer result, not a transport failure. A reachable API does not mean a usable account.

3. Single stream versus aggregate. One slow stream with several fast parallel streams means congestion control, not insufficient bandwidth. Measure both before concluding anything about capacity.

4. A CDN changes the entry, not the exit. Fronting a VPS with a CDN changes how the client reaches it. The destination still sees the VPS address. This does not resolve third-party risk checks.

5. Not every transport can be fronted. A CDN proxies HTTP-family transports. Raw TCP or UDP proxy protocols cannot simply be switched to orange cloud; the ingress transport has to change, and that decision belongs before installation.

6. BBR is not a fix for a bad path. It improves a lossy, high-RTT path for the sending side. It creates no capacity and does not control the segment the client receives from a CDN.

7. Compare like with like. Same client, same ISP, same destination, same window, same measurement code. Alternate control and treatment to cancel drift. Report the median of repeated rounds, not the best round. Overlapping ranges mean the difference is not established.

8. Budget the traffic. State a ceiling before throughput tests. A budget is a maximum, not a target.

9. Leave a rollback before every write. Record what changed, where the backup is, and how to restore. Verify the restore path is real, not assumed.

10. Do not fabricate the result. Distinguish measured, user-confirmed, inferred, and unknown. A short test does not prove all-day or peak-hour behavior.

## Reporting

Lead with which layer failed. Then give the evidence, the change if any, and what remains unverified.

State explicitly:

- what was measured, when, on which path, and how many samples
- whether the client was the user's real device or a stand-in
- what is environment-specific and would not transfer to another ISP or hour
- what the user still has to verify themselves, such as browser login, phone client, peak hour

Do not claim a fix is complete when only the server side was verified.

## References

- [deploy](references/deploy.md)
- [slow-path](references/slow-path.md)
- [unreachable](references/unreachable.md)
- [login-blocked](references/login-blocked.md)
- [multi-device](references/multi-device.md)
