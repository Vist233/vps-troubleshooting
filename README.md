# vps-egress-ops

把一台远程 VPS 调到「能稳定上网」，并在慢、连不上、登录失败时按证据定位到具体一层。

适用于任何 VPS 和服务商。CloudCone、RackNerd、Vultr、Oracle 只是不同机房和线路，**不是不同方法**。

## 这个仓库的形态

```
skill/vps-egress-ops/SKILL.md     ← 给 AI 读的入口
docs/                             ← 给人读的说明
scripts/                          ← 只读采集与对照测量
```

两者共用同一套判据，不重复维护结论。

## 核心主张

**先测量，再动手。** 慢和连不上是两类完全不同的问题，症状相同但层级不同：

```
声明配置 → 落盘配置 → 运行时状态 → 观测到的真实流量
```

越靠右的证据越可信。面板显示正常，不代表配置生成正确；配置正确，不代表运行时已加载；运行时在线，不代表真实流量走得通。

## 不做什么

- 不推荐 VPS 厂商、不分享节点、不做协议排行榜。
- 不提供 `curl | sh` 一键脚本。这类脚本会在你不知情时替换规则、DNS、路由和节点组。
- 不把「功能可用」等同于「安全加固完成」。
- 不保证任何出口能通过第三方风控（例如 OpenAI 的验证挑战）。

## 从哪开始

| 你的情况 | 先看 |
| --- | --- |
| 新机器，还没配 | [docs/01-deploy.md](docs/01-deploy.md) |
| 能用但慢 | [docs/02-slow.md](docs/02-slow.md) |
| 连不上 / 超时 | [docs/03-unreachable.md](docs/03-unreachable.md) |
| 网站能开但登录失败 | [docs/04-login-blocked.md](docs/04-login-blocked.md) |
| 多设备、订阅分发 | [docs/05-multi-device.md](docs/05-multi-device.md) |

让 AI 接手时，读 `skill/vps-egress-ops/SKILL.md`。

## 许可

MIT。见 [LICENSE](LICENSE) 与 [NOTICE.md](NOTICE.md)。
