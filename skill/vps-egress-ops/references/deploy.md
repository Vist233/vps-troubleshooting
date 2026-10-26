# Deploy: decision rules

Human walkthrough with commands: [docs/01-deploy.md](../../../docs/01-deploy.md).
Read that file for the actual steps. This page holds only the rules that change what you do.

## Preconditions

- Host identity known: OS, arch, whether dedicated.
- Role known: exit, relay, or general server.
- Advertised bandwidth known (plan, not speedtest).
- Provider firewall reachable, or the user can open ports themselves.

Missing any of these → ask before installing.

## Decide the transport before installing

This is the one decision that cannot be fixed later without reinstalling.

| Constraint | Consequence |
| --- | --- |
| User's problem is a bad direct path and they want CDN improvement | Must use HTTP-family transport (VLESS/VMess/Trojan over WS+TLS). Shadowsocks cannot be fronted. |
| User needs UDP | HTTP-family over CDN gives TCP only. Keep a non-CDN inbound for UDP. |
| No public inbound port available | Tunnel-based only. |
| Nothing special | Simplest transport that meets the need. Do not add complexity without a reason. |

State the choice and its consequence to the user before proceeding.

## Hard gates

- **Do not pipe an unread installer.** `curl | sh` from a vendor URL is not acceptable. Read it, or use the official package/release.
- **Both firewalls.** Host firewall *and* provider security group. Verify from outside, not from config.
- **`0600` on any file containing a credential.**
- **The subscription token is a credential.** Do not commit it, log it, or paste it into chat.
- **Verify in order:** service active → port bound → local connect → client exit IP → destination response → subscription fetchable from outside. Earlier steps do not imply later ones.
- **Return 404 for non-subscription paths.** No directory listing.

## Stop conditions

Stop and report rather than improvise when:

- the box already runs services you do not own;
- the OS or arch is unsupported by the chosen binary;
- opening the required port would expose an unrelated service;
- you cannot verify the port from outside and the user cannot either.

## Output contract

```text
HOST=<os/arch/dedicated?>
TRANSPORT=<chosen>  CDN_FRONTABLE=<yes/no>
REASON=<why this transport, given the user's actual problem>
LISTENER=<addr:port>
HOST_FIREWALL=<verified how>
PROVIDER_FIREWALL=<verified how / unknown>
SUB_URL=<redacted>  SHA256=<hash>
VERIFIED=<which of the six checks passed>
NOT_VERIFIED=<path speed, client reachability, site login>
```
