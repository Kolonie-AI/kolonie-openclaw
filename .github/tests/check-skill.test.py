#!/usr/bin/env python3
"""Does the skill-structure check catch a removed heading, and pass a good file?

Usage: python3 .github/tests/check-skill.test.py

`kolonie-docs#124`'s definition of done is that each new check is *"proved by a
pull request that fails it"* — a check nobody has seen go red is a check nobody
has seen. These cases are that proof in a form that keeps working after the
pull request is closed.

The last two are the ones with teeth. They read the **real** `SKILL.md` files of
the other five entry-point repositories, so a spine that quietly stops being
shared — because one of them was rewritten — fails here rather than being
discovered by whoever next tries to reuse this file.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "check_skill", ROOT / ".github" / "scripts" / "check-skill.py"
)
assert _spec is not None and _spec.loader is not None
check_skill = importlib.util.module_from_spec(_spec)
sys.modules["check_skill"] = check_skill
_spec.loader.exec_module(check_skill)


FAILURES: list[str] = []


def expect(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def skeleton(**changes: str | None) -> str:
    """A minimal file with the shared spine, with sections swapped or dropped."""
    order = [
        ("why", "## Why an agent joins"),
        ("red", "## Red lines"),
        ("need", "## What you need"),
        ("connect", "## 1. Connect"),
        ("store", "## 2. Store the key — you get one chance"),
        ("back", "## 5. Come back — otherwise you registered, you did not immigrate"),
        ("out", "## What this skill deliberately leaves out"),
        ("touch", "## What this skill touches"),
        ("licence", "## Licence"),
    ]
    parts = ["# Kolonie AI", "", "Body of the title section.", ""]
    for key, heading in order:
        if key in changes and changes[key] is None:
            continue
        parts += [changes.get(key, heading), "", f"Body of {key}.", ""]
    return "\n".join(parts)


print("a good file passes")

expect("the skeleton is accepted", not check_skill.check(skeleton()), str(check_skill.check(skeleton())))
expect(
    "an extra section between required ones is allowed",
    not check_skill.check(skeleton().replace("## Licence", "## Your browser, if the Academy sends you at one\n\nBody.\n\n## Licence")),
)
expect(
    "a differently numbered step is allowed",
    not check_skill.check(skeleton(store="## 2. Store the key — one chance only", back="## 3. Come back — or you did not immigrate")),
)
# `#21`: kolonie-claude qualifies this one, because its plugin has already
# connected the MCP server and the step is a confirmation there rather than an
# instruction. That is a fact about the runtime, not a different section.
expect(
    "a step qualified after its name is allowed",
    not check_skill.check(skeleton(connect="## 1. Connect — the plugin has already done this")),
)
# The other half of the same decision: what varies is the number and the tail,
# never the name. A step called something else is a step a reader who knows one
# skill cannot find in another.
problems = check_skill.check(skeleton(connect="## 1. Get connected"))
expect("a renamed step is still reported", any("N. Connect" in p for p in problems), str(problems))
expect(
    "kolonie-skill's name for 'What you need' is allowed",
    not check_skill.check(skeleton(need="## What this assumes you can do")),
)


print("\na broken file fails")

for key, label in [
    ("red", "Red lines"),
    ("back", "N. Come back"),
    ("licence", "Licence"),
    ("touch", "What this skill touches"),
]:
    problems = check_skill.check(skeleton(**{key: None}))
    expect(f"a missing `{label}` is reported", any("missing" in p and label in p for p in problems), str(problems))

problems = check_skill.check(skeleton(licence="## Licence") .replace("## Licence\n\nBody of licence.", "## Licence\n"))
expect("an empty section is reported", any("nothing under it" in p for p in problems), str(problems))

# Reordering: Licence moved above the two closing sections.
reordered = skeleton(out=None, touch=None).replace(
    "## Licence", "## Licence\n\nBody of licence.\n\n## What this skill deliberately leaves out\n\nBody.\n\n## What this skill touches", 1
)
problems = check_skill.check(reordered)
expect("a section in the wrong place is reported as out of order", any("out of order" in p for p in problems), str(problems))

problems = check_skill.check("Just prose, no headings at all.\n")
expect("a file with no headings is reported", len(problems) == 1 and "no headings" in problems[0], str(problems))

problems = check_skill.check(skeleton().replace("# Kolonie AI", "Not a title"))
expect("a file with no `#` title is reported", any("no `#` title" in p for p in problems), str(problems))

# The check must not read a `#` inside a fence as a heading, or every skill file
# in the Colony fails on its own shell examples.
fenced = skeleton().replace("Body of connect.", "```bash\n# Store this. Not a heading.\ncurl -s https://kolonie.ai\n```")
expect("a `#` inside a fence is not a heading", not check_skill.check(fenced), str(check_skill.check(fenced)))


print("\nthe spine is still shared with the other entry points")

# This repository's own `SKILL.md` is deliberately **not** asserted here.
# Whether it is intact is the check step's answer to give, and duplicating it
# meant that on 2026-08-03 a deliberately broken heading turned the step named
# "Test the check" red — a broken document reading as a broken checker
# (`kolonie-openclaw#11`).
#
# The five others, if they are checked out beside this one. Skipped rather than
# failed when they are not: this suite runs in CI from a single-repository
# checkout, where their absence is the normal state and not a defect.
#
# `#21`: that skip is why this assertion ran on a maintainer's machine and
# nowhere else. It stays, because failing here would only turn every ordinary
# pull request red; what fills the gap is `spine.yml`, which checks the siblings
# out itself and reports where somebody reads it. The set is the checker's own
# `ENTRY_POINTS` so the two cannot come to disagree about who the six are.
siblings = dict(check_skill.ENTRY_POINTS)
checked = 0
for repo, rel in siblings.items():
    path = ROOT.parent / repo / rel
    # This repository's own entry, excluded by where the path lands rather than
    # by its name: a checkout directory does not have to be called after the
    # repository, and a test that assumed so would silently start asserting the
    # very file the note above says it must not.
    if path.resolve() == (ROOT / "SKILL.md").resolve() or not path.exists():
        continue
    checked += 1
    problems = check_skill.check(path.read_text(encoding="utf-8"))
    expect(f"{repo} shares the spine", not problems, str(problems))
if checked == 0:
    print("  skip no sibling entry point is checked out beside this repository")


print()
if FAILURES:
    print(f"{len(FAILURES)} failed: {', '.join(FAILURES)}")
    raise SystemExit(1)
print("all cases pass")
