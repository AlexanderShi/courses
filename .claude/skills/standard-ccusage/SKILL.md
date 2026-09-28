---
name: standard-ccusage
description: Show the user's "standard ccusage" report — Claude Code usage for the past 30 days listed per session (most recent first) plus each of the last 6 months' totals individually. Use whenever the user says "standard ccusage" (or asks for their usual/standard usage report).
---

# Standard ccusage

When the user says **"standard ccusage"**, produce exactly this report:

1. **Past 30 days, listed per session** (today included), **most recent first** — one row per session with start time, last activity, session title, model, total tokens and cost, plus a total row. This replaces the old per-day table; don't show a per-day breakdown unless asked.
2. **Total monthly usage for the last 6 months** (current month included), one row per month, most recent first.

## Where the usage lives

The user's usage is split across two places, and no single source sees both:

| Source | What it covers | How to read it |
|---|---|---|
| `ccusage` (local logs, `~/.claude/projects/**/*.jsonl`) | Sessions that ran **on this machine** (e.g. VS Code / terminal on the user's computer) | `report.mjs` |
| `list_sessions` (Claude Code Remote MCP) `external_metadata.usage` | **Cloud** sessions (`environment_kind: anthropic_cloud` — desktop app / claude.ai/code) | `cloud.mjs` |

Local (`bridge`) sessions show up in `list_sessions` but carry no usage there, and on the user's own machine cloud sessions never appear in local ccusage logs — so the two don't double count there.

**In a cloud container** (`CLAUDE_CODE_REMOTE` is set), the only local log is the current cloud session, which `list_sessions` already includes — skip step 1 there and use only the cloud report, or the current session is counted twice.

## Steps

1. **Local ccusage** (skip in a cloud container, see above) — run:

   ```bash
   node .claude/skills/standard-ccusage/report.mjs [--timezone <IANA tz>]
   ```

   Session titles come from the local JSONL logs (custom/AI title if present, else the first prompt).

2. **Cloud sessions** — if `mcp__Claude_Code_Remote__list_sessions` is available (load via ToolSearch), collect every session (`mine: true`, `limit: 100`, paginate with `after_id` = previous `last_id` until a page comes back empty or sessions are older than the 6-month window). Delegate this to a subagent to keep the context small. Save a JSON array of `{id, title, created_at, updated_at, environment_kind, status, model, usage}` (`status` = `session_status`; `model` = `session_context.model` or `configured_model`; `usage` = `external_metadata.usage` copied exactly, or null) to the scratchpad, then run:

   ```bash
   node .claude/skills/standard-ccusage/cloud.mjs <sessions.json> [--timezone <IANA tz>]
   ```

   Cloud usage is a lifetime total per session (not split by day): a session is listed if it was active in the 30-day window, and counted in the month it started. Mention this, and flag sessions still running (their cost will keep growing).

3. **Present**: the per-session tables (local and cloud) and the monthly tables, then one combined line: 30-day total and each month's total across both sources. Show every row as the scripts print it — don't summarize rows away. State explicitly which sources were **not** reachable (e.g. the `bridge` sessions on the user's own machine when running in the cloud — `cloud.mjs` prints how many; Cowork sessions, which the default `list_sessions` listing leaves out).

Use the same timezone for both scripts. If the user hasn't named one, use the system timezone and say which one was used.
