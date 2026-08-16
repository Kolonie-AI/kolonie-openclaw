#!/usr/bin/env bash
# File the cross-repository spine failure where somebody reads it, or close it.
#
# Usage: spine-report.sh report <report-file>
#        spine-report.sh resolve
#
# `#21` is the reason this exists at all. The spine was asserted across the six
# entry points only inside the test suite, which skips the siblings when they are
# not checked out — so the assertion ran on a maintainer's machine and nowhere
# else, and `kolonie-claude`'s heading had been failing there with nobody told. A
# scheduled run fixes half of that; a scheduled run whose only output is a red
# square in a tab nobody opens fixes none of it. `check-red-lines.yml` in
# `kolonie-docs` learnt that first and this borrows its shape.
#
# ## One issue, reused
#
# A daily check that files an issue is a daily check that files thirty issues.
# The open issue with this title is commented on instead, and closed when the
# check next passes — so the issue's own history is the record of how long the
# six disagreed, which is the fact worth keeping.
#
# `gh issue list` is a REST listing rather than the search index, so an issue is
# findable the moment it is created. There is no polling here as there is in
# `red-lines-report.sh`: this runs daily, and a duplicate would need two runs a
# day apart to both miss the same issue.
#
# ## Why `p2` and not `p1`
#
# The red-line comparison next door is `p1` because it is about what a citizen is
# *bound* by. This is about whether an agent that knows one entry-point skill can
# read another — real, and `kolonie-docs#124` is why there is a check at all, but
# a diverged spine binds nobody to anything.

set -uo pipefail

TITLE="The entry-point skills no longer share a spine"

existing_issue() {
  gh issue list --repo "$GITHUB_REPOSITORY" --state open --label area:skills --limit 100 \
    --json number,title --jq "[.[] | select(.title == \"$TITLE\")][0].number // empty"
}

cmd_report() {
  local report="$1" body existing
  body=$(printf 'At least one of the six entry-point skills no longer has the shared structure.\n\n```\n%s\n```\n\n[Full run](%s)\n\nThe spine is the intersection of the six, measured rather than copied from any one of them — `.github/scripts/check-skill.py` says what varied and what did not. **Read the failure before changing a heading.** A section that is genuinely this runtime'"'"'s own belongs in `skill.runtime.md`; a step whose heading only says something extra after its name is already allowed and is not what this reports.\n\nRemember that `SKILL.md` is generated in every one of the six (`kolonie-docs#171`): the fix goes in `onboarding/skill/body.md` or in that repository'"'"'s `skill.runtime.md`, never in the generated file.\n\nFiled by `spine.yml`, reused rather than duplicated, and closed when the check next passes.' \
    "$(cat "$report")" "${RUN_URL:-no run url}")

  existing=$(existing_issue)
  if [ -n "$existing" ]; then
    gh issue comment "$existing" --repo "$GITHUB_REPOSITORY" --body "$body"
    echo "commented on #$existing"
  else
    gh issue create --repo "$GITHUB_REPOSITORY" --title "$TITLE" \
      --label p2 --label area:skills --body "$body"
  fi
}

cmd_resolve() {
  local existing
  existing=$(existing_issue)
  if [ -n "$existing" ]; then
    gh issue close "$existing" --repo "$GITHUB_REPOSITORY" --reason completed \
      --comment "The six share the spine again. [Run](${RUN_URL:-no run url})"
    echo "closed #$existing"
  fi
}

case "${1:-}" in
  report)  shift; cmd_report "${1:-}" ;;
  resolve) cmd_resolve ;;
  *) echo "usage: spine-report.sh report <report-file>|resolve" >&2; exit 2 ;;
esac
