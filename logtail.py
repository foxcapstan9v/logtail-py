"""logtail - a tiny tail -f style log watcher with pattern rules."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator


@dataclass
class Rule:
    name: str
    pattern: re.Pattern
    level: str = "warn"

    @classmethod
    def build(cls, name: str, pattern: str, level: str = "warn") -> "Rule":
        return cls(name=name, pattern=re.compile(pattern), level=level)


@dataclass
class Hit:
    rule: str
    level: str
    line: str
    ts: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return {"rule": self.rule, "level": self.level, "line": self.line, "ts": self.ts}


def follow(path: Path, poll: float = 0.4) -> Iterator[str]:
    """Yield appended lines, tolerating rotation."""
    fh = path.open("r", encoding="utf-8", errors="replace")
    fh.seek(0, 2)
    inode = path.stat().st_ino if hasattr(path.stat(), "st_ino") else None
    while True:
        line = fh.readline()
        if line:
            yield line.rstrip("\n")
            continue
        time.sleep(poll)
        try:
            st = path.stat()
        except FileNotFoundError:
            continue
        if inode is not None and getattr(st, "st_ino", inode) != inode:
            fh.close()
            fh = path.open("r", encoding="utf-8", errors="replace")
            inode = st.st_ino


def match(rules: Iterable[Rule], line: str) -> list[Hit]:
    hits = []
    for rule in rules:
        if rule.pattern.search(line):
            hits.append(Hit(rule=rule.name, level=rule.level, line=line))
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="logtail")
    ap.add_argument("path", type=Path)
    ap.add_argument("-r", "--rule", action="append", default=[], metavar="NAME=REGEX")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    rules = []
    for raw in args.rule:
        if "=" not in raw:
            ap.error(f"bad rule {raw!r}, want NAME=REGEX")
        name, pattern = raw.split("=", 1)
        rules.append(Rule.build(name, pattern))

    for line in follow(args.path):
        for hit in match(rules, line):
            print(json.dumps(hit.as_dict()) if args.json else f"[{hit.level}] {hit.rule}: {hit.line}")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
