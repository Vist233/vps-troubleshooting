# Deploy: bare host to a working egress

One proxy on a fresh VPS, plus a subscription URL other devices can fetch. No provider assumptions.

## 1. Read the host before writing anything

Read-only. Do this every time.

```bash
hostnamectl; uname -m; head -3 /etc/os-release
ss -ltnp                       # who already owns the ports
systemctl list-units --type=service --state=running --no-pager | head -40
```

Record: OS and version, arch, occupied ports, whether the box is dedicated.

Stop if the box already runs services you do not own, or the OS or arch is outside what your chosen proxy binary supports. Adapt, or use a dedicated host. Do not force it.

## 2. Pick the transport before installing

This decision constrains everything downstream. Changing it later means reinstalling.

| Need | Transport | CDN-frontable |
| --- | --- | --- |
| Simplest, low overhead, TCP and UDP | Shadowsocks | No, raw TCP/UDP |
| Bad direct path, wants a CDN in front | VLESS/VMess/Trojan over WebSocket + TLS | Yes, HTTP-family |
| Lossy long-RTT path, no CDN | Hysteria2 / TUIC | No |
| No public inbound port at all | Tunnel-based | n/a |

Key judgement: if the user's problem is a bad direct path, plain Shadowsocks leaves nothing to improve, because there is no way to put a CDN in front. An HTTP-family transport is required, and that choice belongs before installation. Tell the user the consequence.

If UDP is needed: HTTP-family through a CDN gives TCP only. Keep a non-CDN inbound for UDP.

## 3. Install the proxy service

Install from the project's official repository or release, pinned to a version you record. Do not pipe an installer from a URL you have not read.

Minimal inbound, port chosen in step 2:

```json
{
  "log": { "level": "warn" },
  "inbounds": [
    {
      "type": "shadowsocks",
      "tag": "ss-in",
      "listen": "0.0.0.0",
      "listen_port": 8388,
      "method": "chacha20-ietf-poly1305",
      "password": "<generate one>"
    }
  ],
  "outbounds": [{ "type": "direct", "tag": "direct" }],
  "route": { "final": "direct" }
}
```

Validate before starting:

```bash
sing-box check -c /etc/sing-box/config.json
```

Use a systemd unit with `Restart=on-failure`, `NoNewPrivileges=true`, `ProtectSystem=strict`, `ProtectHome=true`. Set mode `0600` on any file containing a credential.

## 4. Two firewalls

Both must allow the port:

1. the VPS's own firewall (`ufw`, `nftables`, `firewalld`);
2. the provider's security group or cloud firewall, in their console.

Opening only one is the most common cause of a service that runs but never answers.

Test from outside instead of trusting either config:

```bash
nc -vz -w 5 <vps-ip> <port>
```

## 5. Publish a subscription

Serve YAML over HTTPS so devices can fetch it by URL.

```caddy
sub.example.com {
    root * /srv/clash
    encode gzip
    @subscription path /<long-random-token>.yaml
    handle @subscription {
        header Content-Type "text/yaml; charset=utf-8"
        file_server
    }
    handle { respond 404 }
}
```

- The token is the credential. Anyone with the URL has your node. Treat it as a secret; never commit it.
- `encode gzip` cuts fetch time on a large ruleset substantially. It affects download only, never proxy throughput.
- Return `404` for every other path. Do not expose a directory listing.

Verify from outside and record the hash:

```bash
curl -sI -H 'Accept-Encoding: gzip' "https://sub.example.com/<token>.yaml"
curl -s  -H 'Accept-Encoding: gzip' "https://sub.example.com/<token>.yaml" | gzip -dc | sha256sum
```

## 6. Verify in order

Each step proves a different thing. Do not skip ahead.

| Check | Proves |
| --- | --- |
| `systemctl is-active` | The process did not exit |
| `ss -ltnp` shows the port | It is bound where you think |
| Local connect to the port | The listener accepts |
| Client connects and exits with the VPS IP | The tunnel works end to end |
| Destination returns 204/200 | Real traffic reaches the internet |
| Subscription fetchable from outside | Other devices can actually get it |

Only the last two matter to the user. A green service status is not a delivered node.

## Stop conditions

- The box runs services you do not own.
- The OS or arch is unsupported.
- Opening the port would expose an unrelated service.
- Neither you nor the user can verify the port from outside.

## Report

```
HOST=<os/arch/dedicated?>
TRANSPORT=<chosen>  CDN_FRONTABLE=<yes/no>
REASON=<why this transport fits the user's actual problem>
LISTENER=<addr:port>
HOST_FIREWALL=<how verified>
PROVIDER_FIREWALL=<how verified / unknown>
SUB_URL=<redacted>  SHA256=<hash>
VERIFIED=<which of the six checks passed>
NOT_VERIFIED=<path speed, client reachability, site login>
```
