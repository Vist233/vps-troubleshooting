# Unreachable: decision rules

Human walkthrough with commands: [docs/03-unreachable.md](../../../docs/03-unreachable.md).

## Order is mandatory

```
service active → port bound → both firewalls → loopback → other network
→ IP vs domain → TLS → WS upgrade → proxy credentials
```

Each step eliminates a layer. Do not change configuration before you know which layer failed.

## The most common real answer

**Host firewall open, provider security group closed.** It produces a server that looks perfectly healthy and never answers. Check the provider side explicitly, and verify with an external `nc`, not with either config.

## Mapping observation to layer

| Observation | Layer |
| --- | --- |
| TCP to IP fails everywhere | Port blocked, service down, or firewall |
| TCP fails only from one region | Address or route filtered there |
| TCP connects, TLS stalls/resets | SNI-based filtering, or cert/SNI mismatch |
| TCP+TLS ok, WS upgrade fails | Reverse proxy path or header config |
| All connects, no traffic | Credentials, UUID, or path mismatch |

## Loopback-only is often correct

A service bound to `127.0.0.1` behind a reverse proxy is a deliberate design, not a bug. Before "fixing" it to `0.0.0.0`, confirm whether a proxy is supposed to be in front.

## CDN in the path

- Unknown path must return `404`; the configured path must **not** return `404` (a bare `GET` often returns `400`).
- If the configured path also `404`s, the reverse proxy is not matching.
- `TLS alert internal error` when hitting the origin IP with the CDN hostname usually means the origin expects CDN-arrived traffic or the cert does not cover that name. It does not mean the origin is down.
- Scope origin-TLS-mode changes to the single hostname, never the whole zone.

## The self-lockout gate

Before any change to routing, firewall, SSH, or the proxy carrying your own connection:

1. Confirm a **second independent entry** exists (provider console, serial console, or an already-open session).
2. Confirm the exact restore command.
3. If your agent session reaches the host **through** the thing you are changing, **stop** and require the user to confirm recovery access first.

An agent that cuts its own connection cannot finish or roll back. Treat this as a hard stop, not a warning.

## Anti-patterns

- Editing proxy config when the port was never open.
- Changing protocol to fix a blocked address (same address, likely same filter).
- Treating `active` as reachable.
- Concluding from a single network.
- Disabling a firewall "to test" instead of opening one port.

## Output contract

```text
SERVICE=<active/inactive> LISTENER=<addr:port>
HOST_FIREWALL=<verified how>  PROVIDER_FIREWALL=<verified how/unknown>
LOOPBACK=<ok/fail>  EXTERNAL_TCP=<ok/fail> from=<network>
OTHER_NETWORK=<result>  DIRECT_IP=<ok/fail>  DOMAIN=<ok/fail>
TLS=<ok/fail>  WS_UPGRADE=<ok/fail>
FAILING_LAYER=<service|host fw|provider fw|dns|path filter|tls/sni|proxy config>
RECOVERY_ACCESS=<how you can still get in>
UNVERIFIED=<what you could not test>
```
