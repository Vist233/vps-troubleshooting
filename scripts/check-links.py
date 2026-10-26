"""Check that every relative markdown link in the repo resolves to a real file."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
bad = []
checked = 0

for md in sorted(ROOT.rglob("*.md")):
    if ".git" in md.parts:
        continue
    text = md.read_text(encoding="utf-8")
    for target in LINK.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = target.split("#", 1)[0].strip()
        if not path:
            continue
        checked += 1
        resolved = (md.parent / path).resolve()
        if not resolved.exists():
            bad.append((str(md.relative_to(ROOT)), target, str(resolved)))

print(f"checked {checked} relative links in {len(list(ROOT.rglob('*.md')))} files")
if bad:
    print("BROKEN:")
    for src, target, resolved in bad:
        print(f"  {src} -> {target}")
    sys.exit(1)
print("all relative links resolve")
