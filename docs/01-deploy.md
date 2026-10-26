# 1. 从裸机到能上网

目标：一台新 VPS，装好一个代理，生成一个其他设备能拉取的订阅地址。

不针对任何特定服务商。CloudCone、RackNerd、Vultr、Oracle 只是机房和线路不同，流程一样。

## 1.1 先看清这台机器

只读，不改任何东西。

```bash
hostnamectl; uname -m; head -3 /etc/os-release
ss -ltnp                       # 谁占着端口
systemctl list-units --type=service --state=running --no-pager | head -40
```

记下：系统版本、架构、已占用的端口、是不是专用机器。

**出现这些情况先停：** 机器上已有别人的业务、系统或架构不在你选的代理程序支持范围内。要么适配，要么换一台专用机器，不要硬上。

## 1.2 先定传输方式，再动手装

这一步决定了后面所有可能性，不要装完再想。

| 需求 | 传输方式 | 能不能套 CDN |
| --- | --- | --- |
| 最简单，开销低，TCP+UDP 都要 | Shadowsocks | **不能**（裸 TCP/UDP） |
| 直连线路差，想借 CDN 改善入口 | VLESS/VMess/Trojan over WebSocket + TLS | **能**（HTTP 系） |
| 长 RTT、丢包严重，不套 CDN | Hysteria2 / TUIC | 不能 |
| 完全没有公网入站端口 | 隧道类方案 | — |

**关键判断：** 如果你的问题是"直连线路差"，纯 Shadowsocks 没有任何可优化的余地，因为你没法在前面加 CDN。这时要选 HTTP 系传输。这个决定要在安装前做。

## 1.3 安装代理服务

从项目官方仓库或 release 安装，固定一个版本并记录。**不要 `curl | sh`** 一个你没读过的安装脚本。

最小配置（端口按上一步决定）：

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
      "password": "<自己生成>"
    }
  ],
  "outbounds": [{ "type": "direct", "tag": "direct" }],
  "route": { "final": "direct" }
}
```

启动前先校验：

```bash
sing-box check -c /etc/sing-box/config.json
```

配置文件权限设 `0600`，里面有凭据。

systemd 单元建议加上 `Restart=on-failure`、`NoNewPrivileges=true`、`ProtectSystem=strict`、`ProtectHome=true`。

## 1.4 防火墙有两层

必须同时放开：

1. VPS 自己的防火墙（`ufw` / `nftables` / `firewalld`）；
2. 服务商控制台里的安全组 / 云防火墙。

**只开一层，是"服务在跑但连不上"最常见的原因。** 两层都要确认。

从外部实际测试，而不是相信配置：

```bash
nc -vz -w 5 <vps-ip> <端口>
```

## 1.5 发布订阅

用 HTTPS 提供 YAML 文件，设备通过 URL 拉取。

```caddy
sub.example.com {
    root * /srv/clash
    encode gzip
    @subscription path /<足够长的随机token>.yaml
    handle @subscription {
        header Content-Type "text/yaml; charset=utf-8"
        file_server
    }
    handle { respond 404 }
}
```

几个必须知道的点：

- **token 就是凭据。** 拿到 URL 的人就能用你的节点。当密钥对待，不要提交到 Git。
- `encode gzip` 能显著缩短大规则集的下载时间。它只影响下载，不影响上网速度。
- 其他路径一律 `404`，不要开目录浏览。
- 证书用真的（Caddy 会自动申请，前提是 DNS 已生效）。

从外部验证：

```bash
curl -sI -H 'Accept-Encoding: gzip' "https://sub.example.com/<token>.yaml"
curl -s  -H 'Accept-Encoding: gzip' "https://sub.example.com/<token>.yaml" | gzip -dc | sha256sum
```

记下这个哈希，后面用它做完整性对照。

## 1.6 按顺序验收

每一步证明的东西不同，不要跳。

| 检查 | 证明什么 |
| --- | --- |
| `systemctl is-active` | 进程没退出 |
| `ss -ltnp` 看到端口 | 监听在你以为的地方 |
| 本机连这个端口 | 监听器接受连接 |
| 客户端连上后出口 IP 是 VPS | 隧道端到端通了 |
| 目标网站返回 204/200 | 真实流量到了互联网 |
| 从外部能拉到订阅 | 其他设备真的能拿到 |

**只有最后两项对用户有意义。** 服务状态是绿的，不等于交付了可用节点。

## 1.7 "部署完成"不等于什么

部署只证明隧道能跑。它不证明：

- 线路快（见 [02-slow.md](02-slow.md)）；
- 用户的网络能连上（见 [03-unreachable.md](03-unreachable.md)）；
- 第三方网站接受这个出口（见 [04-login-blocked.md](04-login-blocked.md)）。

这三件事要分开报告，不要合并成一句"部署成功"。
