---
name: standard-ccusage
description: Show the user's "standard ccusage" report — daily Claude Code usage for the past 30 days (most recent first) plus each of the last 6 months' totals individually. Use whenever the user says "standard ccusage" (or asks for their usual/standard usage report).
---

# Standard ccusage

When the user says **"standard ccusage"**, produce exactly this report:

1. **Daily usage for the past 30 days** (today included), **most recent first**.
2. **Total monthly usage for the last 6 months** (current month included), one row per month, most recent first.

## Steps

1. Run the bundled script (it calls `ccusage` via `npx`, fetches JSON, fills in zero days/months, and sorts newest first):

   ```bash
   node .claude/skills/standard-ccusage/report.mjs
   ```

   - Pass `--timezone <IANA tz>` if the user has named a timezone; otherwise the system timezone is used.
   - Set `CCUSAGE_CMD` to change how ccusage is invoked (e.g. `CCUSAGE_CMD=ccusage` if it's installed globally).

2. Show the two markdown tables the script prints to the user as-is (don't summarize away rows), then add a one-line headline: 30-day total cost and the current month's cost so far.

## Caveat for cloud sessions

ccusage reads local Claude Code logs (`~/.claude/projects/**/*.jsonl`). In a Claude Code on the web / cloud container, those logs only cover the current container's session, so the report will not reflect the user's full history. Say so in one line when running in a cloud environment; for full history the user should run it on their own machine.
