# 部署：从裸机到可用出口

一台新 VPS，装好一个代理，生成其他设备能拉取的订阅地址。不针对任何服务商。

## 1. 先看清这台机器

只读，不改任何东西。

```bash
hostnamectl; uname -m; head -3 /etc/os-release
ss -ltnp                       # 谁占着端口
systemctl list-units --type=service --state=running --no-pager | head -40
```

记下：系统版本、架构、已占用端口、是不是专用机器。

出现这些情况先停：机器上已有别人的业务；系统或架构不在所选代理程序支持范围内。要么适配，要么换专用机器，不要硬上。

## 2. 先定传输方式，再动手装

这一步决定后面所有可能性，装完再想就来不及了。

| 需求 | 传输方式 | 能不能套 CDN |
| --- | --- | --- |
| 最简单，开销低，TCP+UDP 都要 | Shadowsocks | **不能**（裸 TCP/UDP） |
| 直连线路差，想借 CDN 改善入口 | VLESS/VMess/Trojan over WebSocket + TLS | **能**（HTTP 系） |
| 长 RTT、丢包严重，不套 CDN | Hysteria2 / TUIC | 不能 |
| 完全没有公网入站端口 | 隧道类方案 | — |

关键判断：如果用户的问题是"直连线路差"，纯 Shadowsocks 没有任何可优化的余地，因为没法在前面加 CDN。这时必须选 HTTP 系传输。这个决定要在安装前做，并把后果告诉用户。

需要 UDP 时注意：HTTP 系过 CDN 只给 TCP。要保留非 CDN 入站承担 UDP。

## 3. 安装代理服务

从项目官方仓库或 release 安装，固定版本并记录。不要 `curl | sh` 一个没读过的安装脚本。

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

启动前校验：

```bash
sing-box check -c /etc/sing-box/config.json
```

systemd 单元建议加 `Restart=on-failure`、`NoNewPrivileges=true`、`ProtectSystem=strict`、`ProtectHome=true`。含凭据的文件权限设 `0600`。

## 4. 防火墙有两层

必须同时放开：

1. VPS 自己的防火墙（`ufw` / `nftables` / `firewalld`）；
2. 服务商控制台里的安全组 / 云防火墙。

只开一层，是"服务在跑但连不上"最常见的原因。

从外部实测，不要相信任何一边的配置：

```bash
nc -vz -w 5 <vps-ip> <端口>
```

## 5. 发布订阅

用 HTTPS 提供 YAML，设备通过 URL 拉取。

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

- token 就是凭据。拿到 URL 的人就能用你的节点。当密钥对待，不要提交到 Git。
- `encode gzip` 显著缩短大规则集的下载时间，只影响下载，不影响上网速度。
- 其他路径一律 `404`，不要开目录浏览。

从外部验证并记录哈希：

```bash
curl -sI -H 'Accept-Encoding: gzip' "https://sub.example.com/<token>.yaml"
curl -s  -H 'Accept-Encoding: gzip' "https://sub.example.com/<token>.yaml" | gzip -dc | sha256sum
```

## 6. 按顺序验收

每一步证明的东西不同，不要跳。

| 检查 | 证明什么 |
| --- | --- |
| `systemctl is-active` | 进程没退出 |
| `ss -ltnp` 看到端口 | 监听在你以为的地方 |
| 本机连这个端口 | 监听器接受连接 |
| 客户端连上后出口 IP 是 VPS | 隧道端到端通了 |
| 目标网站返回 204/200 | 真实流量到了互联网 |
| 从外部能拉到订阅 | 其他设备真的能拿到 |

只有最后两项对用户有意义。服务状态是绿的，不等于交付了可用节点。

## 停止条件

- 机器上已有不属于你的服务；
- 系统或架构不受支持；
- 开端口会暴露无关服务；
- 你和用户都无法从外部验证端口。

## 报告

```
主机=<系统/架构/是否专用>
传输=<选择>  可套CDN=<是/否>
理由=<为什么这个传输方式适合用户的实际问题>
监听=<地址:端口>
主机防火墙=<怎么核实的>
服务商防火墙=<怎么核实的 / 未知>
订阅URL=<脱敏>  SHA256=<哈希>
已验证=<六项中通过了哪些>
未验证=<线路速度、客户端可达性、网站登录>
```
