# Login blocked: decision rules

Human walkthrough with commands: [docs/04-login-blocked.md](../../../docs/04-login-blocked.md).

This is a **reading-the-evidence** problem, not a bypass problem. There is no reliable technical bypass and this repository does not offer one.

## Never merge these results

| Observation | Proves |
| --- | --- |
| API `401` unauthenticated | Requests arrive. **Nothing** about account usability |
| API `200` authenticated | That call works from that exit |
| Page `403` + challenge headers | A risk check is challenging. Not a transport failure |
| Form fails repeatedly, page loads | Session/cookie/challenge, usually client-side |
| CLI authorization error | Entitlement or challenge, not necessarily the tunnel |

The most common reporting error: treating `401` on an unauthenticated call as proof the site works through the node.

## Exit vs entry

The destination scores the **exit**. A CDN changes the **entry**.

Therefore: fronting with a CDN, or switching transport, **does not change** what the destination sees. Only a different exit address or a different account/session does.

Verify the exit as the destination sees it (`curl https://api.ipify.org` through the proxy) and compare with the VPS address.

## Classify before recommending

| Class | Signal | Honest options |
| --- | --- | --- |
| Transport | TCP/TLS fails | Fix path ([unreachable](unreachable.md)) |
| Risk challenge | `403` + challenge, captcha, redirect loop | Different exit, residential/mobile path, or accept the limit |
| Account/entitlement | Authenticated but refused; quota/region message | Account side; network changes do not help |

Third-party risk scores are **signals**, not the destination's verdict. A "risk 66" does not mean "66% clean" or "will be blocked". Never present one as a conclusion.

## Escalation order

1. Real browser, signed in, on the user's own device. Cheapest, most conclusive.
2. A different exit (another VPS, or the user's home connection).
3. A different hour.
4. Accept the boundary and say the exit is unsuitable for that service.

## Anti-patterns

- Stacking another proxy hop to "fix" it (changes latency, not exit identity).
- Calling a challenge a ban.
- Citing a third-party score as authoritative.
- Declaring success from a partial signal.
- Building or advising challenge bypasses. Explaining signals is diagnosis; evading them is not.

## Output contract

```text
EXIT_IP=<observed>  EXIT_MATCHES_VPS=<yes/no>
API_UNAUTH=<status>          # reachability only
API_AUTH=<status/result>     # requires user credentials
SITE=<status> CHALLENGE_HEADERS=<present/absent>
REAL_BROWSER_LOGIN=<user-verified yes/no/not attempted>
THIRD_PARTY_RISK=<source> <value>   # signal, not verdict
CLASS=<transport|risk challenge|account|undetermined>
RECOMMENDATION=<...>
UNVERIFIED=<...>
```

The last line must stay honest. "Tunnel verified, real login not verified" is a complete result.
