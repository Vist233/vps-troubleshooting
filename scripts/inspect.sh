#!/usr/bin/env bash
# Read-only VPS egress baseline. Changes nothing: no sysctl writes, no service
# restarts, no firewall edits, no files created on the host.
#
# Usage:
#   ssh <host> 'bash -s' < scripts/inspect.sh
#   bash scripts/inspect.sh                  # on the host itself
#
# Everything printed here is evidence for the checks described in
# docs/02-slow.md and docs/03-unreachable.md.

set -u

# This script targets a Linux VPS. On macOS/BSD most probes are absent; say so
# plainly instead of printing empty sections that look like real findings.
if [ "$(uname -s)" != "Linux" ]; then
  echo "note: this host is $(uname -s), not Linux." >&2
  echo "note: run it on the VPS instead: ssh <host> 'bash -s' < scripts/inspect.sh" >&2
  echo "note: sections below that are empty are unavailable, not negative findings." >&2
fi

section() { printf '\n===== %s =====\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

section "host"
hostnamectl 2>/dev/null | sed -n '1,8p' || uname -a
printf 'arch=%s kernel=%s\n' "$(uname -m)" "$(uname -r)"
head -3 /etc/os-release 2>/dev/null

section "time and clock"
date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date
printf 'ntp_synchronized=%s\n' "$(timedatectl show -p NTPSynchronized --value 2>/dev/null || echo unknown)"

section "listeners"
if have ss; then
  ss -ltnp 2>/dev/null || echo '<ss produced no output>'
elif have netstat; then
  netstat -ltnp 2>/dev/null || echo '<netstat produced no output>'
else
  echo '<neither ss nor netstat available>'
fi

section "proxy-ish services"
systemctl list-units --type=service --state=running --no-pager 2>/dev/null \
  | grep -Ei 'sing-box|xray|v2ray|hysteria|tuic|realm|gost|caddy|nginx|apache|mihomo|clash' \
  || echo '(none matched)'

section "congestion control and qdisc"
for k in net.ipv4.tcp_congestion_control net.core.default_qdisc \
         net.ipv4.tcp_mtu_probing net.core.rmem_max net.core.wmem_max; do
  printf '%s = %s\n' "$k" "$(sysctl -n "$k" 2>/dev/null || echo '<absent>')"
done
printf 'available_cc = %s\n' "$(sysctl -n net.ipv4.tcp_available_congestion_control 2>/dev/null || echo '<unknown>')"
if have tc; then
  printf 'qdisc: '; tc qdisc show 2>/dev/null | head -3
fi

section "nic errors and drops"
if have ip; then
  ip -s link show 2>/dev/null | sed -n '1,40p'
else
  echo '<ip command absent>'
fi

section "default route"
if have ip; then
  ip route get 1.1.1.1 2>/dev/null || echo '<no route>'
else
  echo '<ip command absent>'
fi

section "uptime and load"
uptime

section "memory"
if have free; then
  free -m 2>/dev/null | head -3
elif have vm_stat; then
  vm_stat 2>/dev/null | head -3
else
  echo '<no free or vm_stat>'
fi

section "recent service failures"
systemctl --failed --no-pager 2>/dev/null | head -10 || true

section "done"
echo "READ_ONLY_INSPECTION_COMPLETE"
