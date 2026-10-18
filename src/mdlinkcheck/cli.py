"""mdlinkcheck: report broken local (and optionally remote) links in Markdown."""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+.*)?$", re.M)
FENCE_RE = re.compile(r"^(```|~~~).*?^\1", re.M | re.S)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.M)


@dataclass
class Link:
    file: Path
    line: int
    target: str


def slugify(heading: str) -> str:
    s = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return s.replace(" ", "-")


def strip_code(text: str) -> str:
    # Replace fenced blocks with blank lines so line numbers stay correct.
    return FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def extract_links(path: Path) -> list[Link]:
    text = strip_code(path.read_text(encoding="utf-8"))
    links = []
    for rx in (LINK_RE, REF_RE):
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start(1)) + 1
            links.append(Link(path, line, m.group(1)))
    return sorted(links, key=lambda l: l.line)


def anchors(path: Path) -> set[str]:
    return {slugify(h) for h in HEADING_RE.findall(strip_code(path.read_text(encoding="utf-8")))}


def check_remote(url: str, timeout: float) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "mdlinkcheck"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 400
    except Exception:
        return False


def check_link(link: Link, remote: bool = False, timeout: float = 10.0) -> str | None:
    """Return an error message, or None if the link is OK / skipped."""
    t = link.target
    if t.startswith(("mailto:", "tel:")):
        return None
    if re.match(r"^[a-z]+://", t, re.I):
        if remote and not check_remote(t, timeout):
            return "unreachable URL"
        return None
    path_part, _, frag = t.partition("#")
    target = link.file if not path_part else (link.file.parent / path_part).resolve()
    if not target.exists():
        return "file not found"
    if frag and target.suffix.lower() in (".md", ".markdown") and frag.lower() not in anchors(target):
        return f"missing anchor #{frag}"
    return None


def iter_files(paths: list[str]):
    for p in map(Path, paths):
        if p.is_dir():
            yield from sorted(p.rglob("*.md"))
        else:
            yield p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mdlinkcheck", description="Find broken links in Markdown files.")
    ap.add_argument("paths", nargs="+", help="Markdown files or directories")
    ap.add_argument("--remote", action="store_true", help="also check http(s) links")
    ap.add_argument("--timeout", type=float, default=10.0)
    args = ap.parse_args(argv)
    broken = total = 0
    for f in iter_files(args.paths):
        for link in extract_links(f):
            total += 1
            err = check_link(link, args.remote, args.timeout)
            if err:
                broken += 1
                print(f"{f}:{link.line}: {link.target} ({err})")
    print(f"{total} links checked, {broken} broken", file=sys.stderr)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
