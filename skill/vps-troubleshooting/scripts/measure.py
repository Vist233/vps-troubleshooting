#!/usr/bin/env python3
"""Alternating control/treatment throughput comparison.

Purpose: answer "did this change help?" without the usual mistake of running
the control at 2am and the treatment at 10am and calling the difference an
improvement.

Design:
  - fetches the same URL repeatedly, alternating between the configured rounds;
  - reports per-round values and the median for each arm;
  - refuses to compare arms with unequal sample counts;
  - makes no changes to any system setting.

This measures a single HTTP transfer. It does not measure a proxy protocol's
behaviour, and it is not a bandwidth ceiling. See docs/02-slow.md.

Usage:
  python3 scripts/measure.py --url URL --rounds C,T,T,C,C,T
  python3 scripts/measure.py --url URL --rounds C,T,T,C,C,T --interface en0
  python3 scripts/measure.py --url URL --rounds C,T --proxy http://127.0.0.1:7890

Exit codes: 0 ok, 2 bad arguments, 3 network failure on every attempt,
            4 comparison not usable (unbalanced arms or fewer than 3 samples per arm).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request


def fetch(url: str, timeout: float, proxy: str | None) -> tuple[int, float]:
    """Return (bytes_received, seconds). Raises on failure."""
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    else:
        # Explicitly bypass any ambient proxy so the measurement is not silently
        # rerouted through the user's own client.
        handlers.append(urllib.request.ProxyHandler({}))
    opener = urllib.request.build_opener(*handlers)

    request = urllib.request.Request(url, headers={"User-Agent": "vps-troubleshooting/measure"})
    started = time.monotonic()
    with opener.open(request, timeout=timeout) as response:
        total = 0
        while True:
            chunk = response.read(65536)
            if not chunk:
                break
            total += len(chunk)
    return total, time.monotonic() - started


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Alternating control/treatment throughput comparison.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Rounds are labels: any two distinct labels form the comparison.",
    )
    parser.add_argument("--url", required=True, help="object to download repeatedly")
    parser.add_argument("--rounds", required=True,
                        help="comma-separated arm labels in execution order, e.g. C,T,T,C,C,T")
    parser.add_argument("--interface", default=None,
                        help="bind to this interface (Linux: SO_BINDTODEVICE; macOS: not supported)")
    parser.add_argument("--proxy", default=None, help="HTTP proxy URL, e.g. http://127.0.0.1:7890")
    parser.add_argument("--timeout", type=float, default=60.0, help="per-attempt timeout seconds")
    parser.add_argument("--pause", type=float, default=1.0, help="seconds between attempts")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()

    arms = [label.strip() for label in args.rounds.split(",") if label.strip()]
    if len(arms) < 2:
        print("error: need at least two rounds to compare", file=sys.stderr)
        return 2
    distinct = sorted(set(arms))
    if len(distinct) < 2:
        print("error: rounds must contain at least two distinct labels", file=sys.stderr)
        return 2

    if args.interface:
        if not sys.platform.startswith("linux"):
            print("error: --interface requires SO_BINDTODEVICE (Linux only)", file=sys.stderr)
            return 2
        # Applied globally for this process only; nothing on the host changes.
        import socket
        socket.SO_BINDTODEVICE = getattr(socket, "SO_BINDTODEVICE", 25)
        original = socket.socket.bind

        def bind_with_device(self, address):
            self.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,
                            args.interface.encode() + b"\0")
            return original(self, address)

        socket.socket.bind = bind_with_device  # type: ignore[assignment]

    results: list[dict] = []
    failures = 0
    for index, arm in enumerate(arms, start=1):
        try:
            size, seconds = fetch(args.url, args.timeout, args.proxy)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures += 1
            results.append({"round": index, "arm": arm, "error": f"{type(exc).__name__}: {exc}"})
            print(f"round {index} arm={arm} FAILED {type(exc).__name__}", file=sys.stderr)
        else:
            rate = size / seconds if seconds > 0 else 0.0
            results.append({"round": index, "arm": arm, "bytes": size,
                            "seconds": round(seconds, 3), "bytes_per_second": round(rate, 1)})
            print(f"round {index} arm={arm} {size} B in {seconds:.2f}s = {rate / 1024:.1f} KB/s")
        if index < len(arms):
            time.sleep(args.pause)

    if failures == len(arms):
        print("error: every attempt failed; nothing to compare", file=sys.stderr)
        return 3

    summary: dict[str, dict] = {}
    for arm in distinct:
        rates = [r["bytes_per_second"] for r in results if r["arm"] == arm and "bytes_per_second" in r]
        if not rates:
            summary[arm] = {"samples": 0}
            continue
        summary[arm] = {
            "samples": len(rates),
            "median": round(statistics.median(rates), 1),
            "min": round(min(rates), 1),
            "max": round(max(rates), 1),
            "values": rates,
        }

    counts = {arm: summary[arm]["samples"] for arm in distinct}
    comparable = len(set(counts.values())) == 1 and all(c > 0 for c in counts.values())
    # Equal counts are not the same as enough counts: with one sample per arm the
    # min and max are identical, so ranges can never overlap and a difference can
    # look established when nothing was repeated.
    min_samples = 3
    thin = [arm for arm in distinct if 0 < counts[arm] < min_samples]

    if args.json:
        print(json.dumps({
            "url": args.url,
            "rounds": results,
            "summary": summary,
            "comparable": comparable,
            "failed_attempts": failures,
        }, indent=2, ensure_ascii=False))
    else:
        print("\n--- summary (bytes/second) ---")
        for arm in distinct:
            entry = summary[arm]
            if entry["samples"] == 0:
                print(f"{arm}: no successful samples")
            else:
                print(f"{arm}: n={entry['samples']} median={entry['median']} "
                      f"min={entry['min']} max={entry['max']}")
        if not comparable:
            print("\nWARNING: arms have unequal sample counts; this is not a valid comparison.")
            print("         Rerun with a balanced alternating order.")
        elif thin:
            print("\nWARNING: fewer than %d samples for %s; one or two rounds cannot"
                  % (min_samples, ", ".join(thin)))
            print("         separate a real difference from run-to-run variance.")
        print("\nRanges that overlap mean the difference is not established.")
        print("This is one HTTP transfer, not a proxy throughput ceiling.")

    return 0 if comparable and not thin else 4


if __name__ == "__main__":
    sys.exit(main())
