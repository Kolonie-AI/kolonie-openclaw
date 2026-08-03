#!/usr/bin/env python3
"""Does `SKILL.md` still have the shape every entry-point skill shares?

Usage: python3 .github/scripts/check-skill.py [SKILL.md]

`kolonie-docs#124` measured that this repository ran **no check at all** on a
pull request, and decided what should fill the slot here rather than a linter:
*"the skill files have a structure the other entry-point repositories share;
something that reads it is worth more here than a linter."*

## What the structure is, and how it was arrived at

By measurement on 2026-08-03, reading the `##` headings of all six entry-point
skills — `kolonie-openclaw`, `kolonie-claude`, `kolonie-kilo`, `kolonie-hermes`,
`kolonie-codex`, `kolonie-antigravity` — plus `kolonie-skill`. `SPINE` below is
their intersection, in the order all seven put them in.

**Two of the six are shorter than this one, and that is why the spine is not
just a copy of our own headings.** `kolonie-codex` and `kolonie-antigravity`
have three numbered steps where the rest have five: they carry no *"Say who you
are"* and no *"Settle what you may do"*, and no *"Your browser"* section. A
check built by listing this file's own headings would have declared four
sections mandatory that two of the six deliberately do not have, and the first
person to reuse it would have had to weaken it.

**The step numbers are not compared**, for that same reason — *"Come back"* is
step 5 here and step 3 in the two short ones. What has to hold is that it is
there and that it is last of the numbered steps, which is the property the
document actually depends on: `kolonie-docs#102` is explicit that an agent that
registers and never returns has not immigrated.

**`kolonie-skill` writes *"What this assumes you can do"*** where the six write
*"What you need"*. It is the same section under a different name and it is not
one of the six, so the six's name is what is required; the alternative is
accepted so this file can be lifted into `kolonie-skill` unchanged.

## What it checks beyond presence

**No heading is empty.** A section that exists with nothing under it is the
failure mode of a document edited by successive agents — the heading survives a
rewrite that moved its content somewhere else, and the table of contents keeps
promising something that is not there.

**`## Red lines` is not checked for content here.** `kolonie-docs`'
`check-red-lines.yml` compares it against `governance/red-lines.md` daily and
across every repository, which is a stronger check than anything this file could
make, and duplicating it would mean two checks that can disagree.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")

# Each entry is (label, matcher). The order is the order they must appear in.
# A matcher takes the heading text with the `## ` already removed.
SPINE: list[tuple[str, object]] = [
    ("Why an agent joins", lambda h: h == "Why an agent joins"),
    ("Red lines", lambda h: h == "Red lines"),
    # kolonie-skill renames this one; see the header.
    ("What you need", lambda h: h in ("What you need", "What this assumes you can do")),
    ("1. Connect", lambda h: h == "1. Connect"),
    # The step number varies between the six, the wording does not.
    ("N. Store the key", lambda h: re.fullmatch(r"\d+\. Store the key\b.*", h) is not None),
    ("N. Come back", lambda h: re.fullmatch(r"\d+\. Come back\b.*", h) is not None),
    ("What this skill deliberately leaves out", lambda h: h == "What this skill deliberately leaves out"),
    ("What this skill touches", lambda h: h == "What this skill touches"),
    ("Licence", lambda h: h == "Licence"),
]


def sections(text: str) -> list[tuple[int, int, str, str]]:
    """Every heading, as (line, level, text, body). Fenced code is not read.

    A `#` inside a fenced block is a shell comment or a Markdown example far more
    often than it is a heading — this repository's own `SKILL.md` contains both.
    """
    out: list[tuple[int, int, str, list[str]]] = []
    fence: str | None = None
    for n, line in enumerate(text.split("\n"), start=1):
        if fence is None:
            m = FENCE.match(line)
            if m:
                fence = m.group(1)[0] * 3
                if out:
                    out[-1][3].append(line)
                continue
        else:
            if line.strip().startswith(fence):
                fence = None
            if out:
                out[-1][3].append(line)
            continue

        h = HEADING.match(line)
        if h:
            out.append((n, len(h.group(1)), h.group(2), []))
        elif out:
            out[-1][3].append(line)
    return [(n, lvl, text_, "\n".join(body)) for n, lvl, text_, body in out]


def check(text: str) -> list[str]:
    found = sections(text)
    problems: list[str] = []

    if not found:
        return ["the file has no headings at all — it is not a skill file"]

    tops = [(n, h) for n, lvl, h, _ in found if lvl == 1]
    if not tops:
        problems.append("there is no `#` title")

    twos = [(n, h) for n, lvl, h, _ in found if lvl == 2]

    # Presence and order in one pass: walk the headings, advancing through the
    # spine. Anything the spine never reaches is missing, and reporting the
    # first one that could not be found in order is how an out-of-order section
    # reads — which is the right way round, because a section moved above its
    # predecessor is a reordering rather than a deletion.
    i = 0
    matched: dict[str, int] = {}
    for line, heading in twos:
        while i < len(SPINE) and not SPINE[i][1](heading):
            # Only advance past a spine entry if this heading matches a *later*
            # one; otherwise this is an extra section, which is allowed.
            if any(m(heading) for _, m in SPINE[i + 1 :]):
                i += 1
            else:
                break
        if i < len(SPINE) and SPINE[i][1](heading):
            matched[SPINE[i][0]] = line
            i += 1

    for label, matcher in SPINE:
        if label in matched:
            continue
        elsewhere = [line for line, h in twos if matcher(h)]
        if elsewhere:
            problems.append(
                f"`## {label}` is at line {elsewhere[0]}, out of order — the shared "
                "structure is not a suggestion, it is what lets a reader who knows "
                "one skill read any of them"
            )
        else:
            problems.append(f"`## {label}` is missing")

    for line, level, heading, body in found:
        if not body.strip():
            problems.append(f"line {line}: `{'#' * level} {heading}` has nothing under it")

    return problems


def main(argv: list[str]) -> int:
    path = Path(argv[1] if len(argv) > 1 else "SKILL.md")
    if not path.exists():
        print(f"::error::{path} does not exist", file=sys.stderr)
        return 1

    problems = check(path.read_text(encoding="utf-8"))
    for p in problems:
        print(f"::error file={path}::{p}")
        print(f"{path}: {p}", file=sys.stderr)

    if problems:
        print(f"{len(problems)} problems in {path}", file=sys.stderr)
        return 1

    print(f"{path}: the shared structure is intact — {len(SPINE)} required sections, all present and in order", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
