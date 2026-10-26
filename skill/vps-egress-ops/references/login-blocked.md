# Login blocked: the site loads but you cannot sign in

A working tunnel does not mean a working account session. Sites that protect themselves with risk checks treat an IP as a signal, and a VPS address is a signal they dislike.

This page is about reading the evidence correctly, not about defeating protections. There is no reliable technical bypass and this repository does not pretend otherwise.

## Step 1: what did you actually observe?

These are different results and must not be merged:

| Observation | What it proves |
| --- | --- |
| API returns `401` without credentials | Requests reach the API. Nothing about account usability |
| API returns `200` with valid credentials | That call works from that exit |
| Page returns `403` with challenge headers | A risk check is challenging the client, not a network failure |
| Page loads but the login form fails repeatedly | Session, cookie, or challenge problem, usually client-side |
| CLI tool reports an authorization error | Account entitlement or challenge, not necessarily the tunnel |

The most common reporting error is treating a `401` on an unauthenticated call as proof that the site works through the node. It does not. `401` is the expected answer for an unauthenticated request and says nothing about whether a real login will pass.

## Step 2: is the exit the problem?

The destination sees the exit address, which is the VPS. A CDN in front of the VPS changes the entry, not the exit.

- Fronting with a CDN does not change how the destination scores the address.
- Switching transport, such as Shadowsocks to VLESS/WS, does not change the exit either.
- Only a different exit address, or a different account or session, changes what the destination sees.

Check the exit as the destination would see it:

```bash
curl -s https://api.ipify.org    # through the proxy
```

Compare with the VPS's own public address. If they match, the exit is the VPS and CDN fronting has not altered it.

## Step 3: classify the three failure classes

| Class | Signal | Honest options |
| --- | --- | --- |
| Transport | TCP or TLS fails, timeouts, resets | Fix the path, see [unreachable](unreachable.md) |
| Risk challenge | `403` with challenge headers, captcha, redirect loop | Different exit, residential or mobile path, or accept the limit |
| Account or entitlement | Authenticated but refused, quota or region message | Account side; network changes do not help |

Third-party "IP purity" or risk scores are third-party signals only. They are not the destination's score, and a figure like "risk 66" does not mean "66% clean" or "will be blocked". Do not present one as a verdict.

## Step 4: what can honestly be tried

1. A real browser, signed in, on the user's own device. Most "it's blocked" reports turn out to be a challenge a normal browser passes. Cheapest test, and the one that most often resolves the question.
2. A different exit. Another VPS in another datacenter, or the user's home connection. If home works and the VPS does not, the exit is the variable.
3. A different hour. Risk decisions and challenge frequency vary; one failure is not a permanent verdict.
4. Accept the boundary. If a datacenter exit is consistently challenged and the user needs reliable access, the honest answer is that this exit is unsuitable for that service.

## What not to do

- Stacking another proxy hop to "fix" it. Adding hops changes latency, not the exit identity.
- Calling a challenge a ban. `403` with a challenge means "prove you are not a bot".
- Treating a third-party score as authoritative.
- Declaring success from a partial signal.
- Building or advising challenge bypasses. Explaining signals is diagnosis; evading them is not.

## Report

```
EXIT_IP=<observed through proxy>
EXIT_MATCHES_VPS=<yes/no>
API_UNAUTH=<status>          # 401 is expected; proves reachability only
API_AUTH=<status/result>     # requires user credentials
SITE=<status> CHALLENGE_HEADERS=<present/absent>
REAL_BROWSER_LOGIN=<user-verified yes/no/not attempted>
THIRD_PARTY_RISK=<source> <value>   # signal only
CLASS=<transport | risk challenge | account | undetermined>
RECOMMENDATION=<...>
UNVERIFIED=<...>
```

The last line must stay honest. "Tunnel verified, real login not verified" is a complete and useful result.
