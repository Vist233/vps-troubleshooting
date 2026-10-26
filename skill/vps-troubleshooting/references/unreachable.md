# Unreachable: connection times out or resets

"Can't connect" has at least six causes at six layers. Most wasted effort comes from fixing a layer that was never broken.

## Order of checks

Cheapest and most decisive first.

```
1. Is the service running?          systemctl is-active
2. Is it listening where expected?  ss -ltnp
3. Are both firewalls open?         VPS firewall + provider security group
4. Can the VPS reach itself?        connect from the VPS to its own port
5. Can another network reach it?    a different ISP, or an external checker
6. Is the IP blocked or the DNS?    direct IP versus domain
7. Does the transport survive?      TLS / WebSocket handshake
```

## 1 and 2: service and listener

```bash
systemctl is-active <service>
systemctl status <service> --no-pager -l | tail -20
ss -ltnp | grep <port>
```

A service bound to `127.0.0.1` cannot accept external connections. That may be correct, since a loopback-only ingress behind a reverse proxy is a deliberate design. Confirm whether a proxy is supposed to be in front before changing it to `0.0.0.0`.

## 3: two firewalls

```bash
ufw status verbose
nft list ruleset | head -40
```

And the provider's security group in their console.

Opening only the host firewall while the provider blocks the port produces a server that looks perfect and never answers. This is the most common cause of a fresh deployment appearing dead.

Test from outside:

```bash
nc -vz -w 5 <vps-ip> <port>
```

## 4: loopback sanity check

The port answers locally but not externally, so the problem is firewall or provider, not the proxy config:

```bash
nc -vz -w 5 127.0.0.1 <port>
```

## 5: another network

One network is not evidence. A timeout from a single ISP can be that ISP, that route, or a blocked address.

- Try a different network, such as a mobile hotspot or another ISP.
- Use an external multi-location checker to see whether everywhere fails or only the user's region.
- Compare direct IP against domain: if the IP works and the domain does not, look at DNS; if both fail, look at the path.

Only after this can you say "the address is blocked from this region" rather than "it doesn't work".

## 6: what exactly is blocked

| Observation | Likely layer |
| --- | --- |
| TCP to the IP fails everywhere | Port blocked, or service and firewall |
| TCP fails only from one region | Address or route filtered there |
| TCP connects, TLS stalls or resets | SNI-based filtering, or certificate and SNI mismatch |
| TCP and TLS fine, WebSocket upgrade fails | Reverse proxy path or header misconfiguration |
| Everything connects, no traffic passes | Proxy credentials, UUID, or path mismatch |

A `TLS alert internal error` when you connect to the origin IP using the CDN's hostname usually means the origin expects traffic that arrived through the CDN, or the certificate does not cover that name. It does not mean the origin is down.

## 7: a CDN in the path

```bash
curl -sI https://<cdn-host>/does-not-exist        # should be 404
curl -sI https://<cdn-host>/<configured-ws-path>  # should not be 404
```

Expected: unknown paths return `404`, and the configured path does not. A bare `GET` often returns `400` because it lacks the upgrade headers. If the configured path also returns `404`, the reverse proxy is not matching it.

Origin TLS mode: `Full` encrypts to the origin but does not validate the origin certificate; `Full (strict)` validates it. Scope a mode change to that one hostname, never the whole zone.

## The biggest trap: locking yourself out

Before changing anything that affects routing, firewalls, SSH, or the proxy carrying your own connection:

1. Confirm a second independent entry exists, such as the provider console, a serial console, or an already-open second SSH session.
2. Confirm the change is reversible and you know the exact restore command.
3. If your agent session reaches the host through this VPS, stop and require the user to confirm recovery access first.

An agent that cuts its own connection cannot finish the task and cannot roll back. Treat this as a hard stop.

## Anti-patterns

- Editing proxy config when the port was never open. Check the firewall first; it is free and usually the answer.
- Changing protocol to fix a blocked port. A new protocol on the same address may also be filtered. Test the address first.
- Treating "running" as "reachable". `active` only means the process did not exit.
- Judging reachability from one network.
- Disabling a firewall "to test". Open the specific port instead.

## Report

```
SERVICE=<active/inactive>  LISTENER=<addr:port or none>
HOST_FIREWALL=<how verified>
PROVIDER_FIREWALL=<how verified / unknown>
LOOPBACK=<ok/fail>
EXTERNAL_TCP=<ok/fail>  from=<network>
OTHER_NETWORK=<result>
DIRECT_IP=<ok/fail>  DOMAIN=<ok/fail>
TLS_HANDSHAKE=<ok/fail>  WS_UPGRADE=<ok/fail>
FAILING_LAYER=<service | host fw | provider fw | dns | path filter | tls/sni | proxy config>
RECOVERY_ACCESS=<how you can still get in>
UNVERIFIED=<what you could not test>
```
