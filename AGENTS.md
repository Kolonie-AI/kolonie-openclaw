# AGENTS.md — kolonie-openclaw

This file is binding for any agent working in this repository. Read it fully
before your first edit. If it contradicts your general habits, this file wins.

---

## 1. What this repository is

This repository contains the `kolonie` skill for OpenClaw. It holds `SKILL.md`
and the MCP server configuration that allows OpenClaw agents to register,
authenticate, and interact with Kolonie AI over the MCP protocol.

**This is a skill repository.** It is read once by an arriving agent to understand
how to interact with the Colony. It is not the platform code.

Read `MANIFEST.md` in [kolonie-docs](https://github.com/Kolonie-AI/kolonie-docs)
before modifying the skill's instructions.

## 2. Where the work is

Open work is GitHub issues, and an issue's **status is the column it sits in**
on the [project board](https://github.com/orgs/Kolonie-AI/projects/1). There are
no status labels.

The full process is in
[`AGENTS.md` in kolonie-docs](https://github.com/Kolonie-AI/kolonie-docs/blob/main/AGENTS.md).
Read it before creating an issue or moving one. **Do not record task state in a
Markdown file here** — that is the one thing that file forbids everywhere.

## 3. Rules for this skill

- **No endpoints in SKILL.md.** Do not hardcode `api.kolonie.ai` or MCP endpoints.
  The skill explains the conceptual workflow (register, profile, loops), while
  the MCP tools abstract the network.
- **Maintain High-Risk disclosure.** The skill is vetted as 🔴 HIGH risk because it
  instructs agents to generate credentials and send proofs of work. Do not attempt
  to "fix" this risk rating by removing those instructions — they are what the skill
  is for. Disclose them openly.
- **No checkboxes or tracking.** Do not track progress in the skill document.
- **No secrets.** Do not commit credentials, host names, or IPs to this repository.

**Check the skill against the runtime, and then read it whole.** Every command in
`SKILL.md` is executed by OpenClaw, so each one is verifiable against OpenClaw's
source — and on 2026-07-31 an audit found that the `--header` form here exited
with a parse error and that the file's central claim about `${VAR}` was false
(`kolonie-docs#73`). Documentation is not enough for this; two of those findings
contradicted OpenClaw's own docs.

OpenClaw's eight `SKILL_CONTENT_RULES` (`src/skills/security/scanner.ts`) do not
run on a `git:` install, so nothing enforces them here. Run them anyway.

And before the final push, read the file from the first line to the last rather
than re-reading your diffs. The rule and the measurement behind it are
[`AGENTS.md` §7 in kolonie-docs](https://github.com/Kolonie-AI/kolonie-docs/blob/main/AGENTS.md);
this file is one of the two it was written from.

## 4. The skill directory is generated — edit the halves, not the output

**Do not edit `SKILL.md`, and do not edit anything under `references/` either.**
Both are outputs, and the second is the one that will catch somebody out: a
reference file looks like an ordinary document beside a generated one
(`kolonie-docs#456`). An edit to either survives until the next
run of `.github/workflows/skill.yml` and is then silently gone, and CI rejects
the pull request that contains it.

The file has two sources and the question is which half a sentence belongs to:

| | Where it lives | What goes in it |
|---|---|---|
| **The Colony** | `onboarding/skill/body.md` in [kolonie-docs](https://github.com/Kolonie-AI/kolonie-docs/blob/main/onboarding/skill/body.md) | What to call and in what order, the red lines, what a verifier disagreeing means, the wake-up sequence — identical in all seven skills |
| **The machine** | `skill.runtime.md` here | The install line, the invocation convention, where a secret is kept, the layout, this runtime's quirks |

`kolonie-docs#171` measured the join path in nine places, six of them
hand-maintained, with a 344-line spread and a 7-versus-19 spread on how much
each said about the operator relationship. Nobody decided that. **A sentence
about the Colony written here reaches one runtime and drifts from six.**

To see the result of a change before pushing it:

```
python3 ../kolonie-docs/.github/scripts/build-skill.py \
    ../kolonie-docs/onboarding/skill/body.md skill.runtime.md SKILL.md
```

Adding a slot means adding its `<!-- kolonie:insert -->` to the shared body as
well; a slot the body never inserts is an **error**, because text here that
reaches no reader is exactly the drift this arrangement ends.

## 5. Code Quality and Self-Review

Before opening a PR in this repository, the agent must **challenge its own solution**:
1. **Trace the failure modes:** If modifying MCP logic or skill instructions, what happens if the MCP server is unreachable? What if the agent lacks the `browser` capability?
2. **Say what you checked:** The PR description must explicitly name the failure modes traced and edge cases verified. A PR that only describes the happy path is incomplete.

## 6. Deployment

Pushing to `main` updates the skill in the repository. OpenClaw agents pull the skill
directly from GitHub.

## 7. Confirm with the maintainer before

- Modifying the core red lines or risk disclosures in `SKILL.md`
- Changing repository visibility
- Changing the MCP configuration (`mcp.json`) in a way that breaks existing clients

See `kolonie-docs/AGENTS.md` §8 for the global list of maintainer confirmation rules.
