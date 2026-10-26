# NOTICE

本仓库的方法论由本仓库作者整理，代码与文字为原创，采用 MIT 许可。

## 参考过的公开资料

调研阶段阅读过以下项目，用于确认本仓库的边界与不重复造轮子。**没有复制它们的文本、配置模板或脚本。**

| 来源 | 许可 | 参考了什么 |
| --- | --- | --- |
| [SagerNet/sing-box](https://github.com/SagerNet/sing-box) | 见其仓库 | 配置字段语义，以官方文档为准 |
| [caddyserver/caddy](https://caddyserver/caddy) | Apache-2.0 | Caddyfile 指令语义 |
| [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo) | MIT | rule-provider 与 MRS 格式语义 |
| [RedpoQ/vps-proxy-ops](https://github.com/RedpoQ/vps-proxy-ops) | MIT | 「声明→落盘→运行时→真实流量」证据分层思路 |
| [Furinelle/netriage](https://github.com/Furinelle/netriage) | CC BY-NC-SA 4.0（衍生自 Lide/iBytebox 文章） | 「先测量再动手、拒绝照抄参数」的立场 |
| [jedliuai/vps-proxy-skill](https://github.com/jedliuai/vps-proxy-skill) | 未声明 | 仅确认「AI skill + 人类文档 + 脚本」的形态可行 |

### 关于 netriage 的特别说明

`Furinelle/netriage` 的 LICENSE 要求衍生作品遵守 **CC BY-NC-SA 4.0**（禁止商用、相同方式共享）。本仓库**不是它的衍生作品**：

- 没有复制其 `SKILL.md`、`references/` 或 `scripts/` 的任何文本或代码；
- 没有沿用其文件结构或章节组织；
- 只采纳了「先测量、再推荐、拒绝照抄参数」这一公开的方法立场，该立场在运维领域属于通用实践。

如果你要在此基础上做商业产品，上述区分不影响你；但请自行复核，不要直接把 netriage 的文件放进本仓库。

## 技术事实来源

配置与命令以官方文档为准，不依赖本仓库的转述：

- [sing-box 配置文档](https://sing-box.sagernet.org/configuration/)
- [Caddy reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [mihomo rule-providers](https://wiki.metacubex.one/en/config/rule-providers/)
- [Cloudflare SSL/TLS 加密模式](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/)
- [Cloudflare ECH](https://developers.cloudflare.com/ssl/edge-certificates/ech/)
