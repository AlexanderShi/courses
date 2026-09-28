---
name: standard-ccusage
description: Show the user's "standard ccusage" report — daily Claude Code usage for the past 30 days (most recent first) plus each of the last 6 months' totals individually. Use whenever the user says "standard ccusage" (or asks for their usual/standard usage report).
---

# Standard ccusage

When the user says **"standard ccusage"**, produce exactly this report:

1. **Daily usage for the past 30 days** (today included), **most recent first**.
2. **Total monthly usage for the last 6 months** (current month included), one row per month, most recent first.

## Where the usage lives

The user's usage is split across two places, and no single source sees both:

| Source | What it covers | How to read it |
|---|---|---|
| `ccusage` (local logs, `~/.claude/projects/**/*.jsonl`) | Sessions that ran **on this machine** (e.g. VS Code / terminal on the user's computer) | `report.mjs` |
| `list_sessions` (Claude Code Remote MCP) `external_metadata.usage` | **Cloud** sessions (`environment_kind: anthropic_cloud` — desktop app / claude.ai/code) | `cloud.mjs` |

Local (`bridge`) sessions show up in `list_sessions` but carry no usage there, and cloud sessions never appear in local ccusage logs — so the two never double count.

## Steps

1. **Local ccusage** — run:

   ```bash
   node .claude/skills/standard-ccusage/report.mjs [--timezone <IANA tz>]
   ```

   In a cloud container this only covers the current container's session, so say that in one line.

2. **Cloud sessions** — if `mcp__Claude_Code_Remote__list_sessions` is available (load via ToolSearch), collect every session (`mine: true`, `limit: 100`, paginate with `after_id` = previous `last_id` until a page comes back empty or sessions are older than the 6-month window). Delegate this to a subagent to keep the context small. Save a JSON array of `{id, title, created_at, updated_at, environment_kind, usage}` (usage = `external_metadata.usage` copied exactly, or null) to the scratchpad, then run:

   ```bash
   node .claude/skills/standard-ccusage/cloud.mjs <sessions.json> [--timezone <IANA tz>]
   ```

   Cloud usage is only reported per session, so each session is counted on its start date — mention this.

3. **Present**: the local tables and the cloud tables (daily, most recent first; monthly, each month on its own row), then one combined line per window (30-day total, each month's total). Show every row as the scripts print it — don't summarize rows away. State explicitly which sources were **not** reachable (e.g. local logs on the user's own machine when running in the cloud).

Use the same timezone for both scripts. If the user hasn't named one, use the system timezone and say which one was used.
