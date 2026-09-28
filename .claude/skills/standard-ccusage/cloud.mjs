#!/usr/bin/env node
// Cloud-session half of the "standard ccusage" report.
// ccusage only sees logs on the machine it runs on, so usage from Claude Code on
// the web / cloud sessions has to come from the session list instead.
//
// Input: a JSON array of sessions, each {id, title, created_at, updated_at,
// environment_kind, status, model, usage: {cost_usd, input_tokens,
// output_tokens, cache_write_tokens, cache_read_tokens} | null}, as collected
// from list_sessions (see SKILL.md).
//
// Output:
//   1. Past 30 days, listed per session (most recent first), with a total.
//      A session is included if it was active in the window; its cost is the
//      session's lifetime total (list_sessions doesn't split usage by day).
//   2. Monthly totals for the last 6 months, each session counted in the month
//      it started.
//
// Usage: node cloud.mjs <sessions.json> [--timezone <IANA tz>]

import { readFileSync } from "node:fs";

const args = process.argv.slice(2);
const file = args.find((a, i) => !a.startsWith("--") && args[i - 1] !== "--timezone");
const tzFlag = args.indexOf("--timezone");
const tz =
  (tzFlag !== -1 && args[tzFlag + 1]) ||
  Intl.DateTimeFormat().resolvedOptions().timeZone ||
  "UTC";

const DAYS = 30;
const MONTHS = 6;

const localParts = (d) =>
  Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: tz,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(d)
      .map((p) => [p.type, p.value])
  );
const localDate = (d) => {
  const p = localParts(d);
  return `${p.year}-${p.month}-${p.day}`;
};
const localStamp = (d) => {
  const p = localParts(d);
  return `${p.month}-${p.day} ${p.hour}:${p.minute}`;
};

const today = localDate(new Date());
const [ty, tm, td] = today.split("-").map(Number);
const isoDay = (d) => d.toISOString().slice(0, 10);
const windowStart = isoDay(new Date(Date.UTC(ty, tm - 1, td - (DAYS - 1))));
const months = Array.from({ length: MONTHS }, (_, i) =>
  isoDay(new Date(Date.UTC(ty, tm - 1 - i, 1))).slice(0, 7)
);

const all = JSON.parse(readFileSync(file, "utf8"));
const inWindow = (s) => localDate(new Date(s.updated_at)) >= windowStart;
const sessions = all.filter((s) => s.usage);

const fields = ["input_tokens", "output_tokens", "cache_write_tokens", "cache_read_tokens", "cost_usd"];
const zero = () => ({ n: 0, ...Object.fromEntries(fields.map((f) => [f, 0])) });
const add = (acc, u) => {
  acc.n += 1;
  for (const f of fields) acc[f] += u[f] ?? 0;
  return acc;
};
const tokens = (u) => u.input_tokens + u.output_tokens + u.cache_write_tokens + u.cache_read_tokens;

const num = (n) => Math.round(n).toLocaleString("en-US");
const usd = (n) => `$${n.toFixed(2)}`;
const cell = (s) => String(s).replace(/\s+/g, " ").replaceAll("|", "\\|").trim();
const shortModel = (m) => (m ?? "").replace(/^claude-/, "") || "—";

function sessionTable() {
  const rows = sessions.filter(inWindow).sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
  const lines = [
    `### Past ${DAYS} days by session (${windowStart} → ${today}, most recent first)`,
    "",
    "| Start | Last active | Session | Model | Total Tokens | Cost |",
    "|---|---|---|---|--:|--:|",
  ];
  const sum = zero();
  for (const s of rows) {
    add(sum, s.usage);
    const running = /RUNNING/.test(s.status ?? "") ? " (running)" : "";
    lines.push(
      `| ${localStamp(new Date(s.created_at))} | ${localStamp(new Date(s.updated_at))}${running} | ${cell(s.title)} | ${shortModel(s.model)} | ${num(tokens(s.usage))} | ${usd(s.usage.cost_usd)} |`
    );
  }
  if (!rows.length) lines.push("| — | — | (no cloud sessions in this window) | | 0 | $0.00 |");
  lines.push(`| **Total** | | **${sum.n} sessions** | | **${num(tokens(sum))}** | **${usd(sum.cost_usd)}** |`);

  const missing = all.filter((s) => !s.usage && inWindow(s));
  if (missing.length) {
    const kinds = {};
    for (const s of missing) kinds[s.environment_kind ?? "unknown"] = (kinds[s.environment_kind ?? "unknown"] ?? 0) + 1;
    lines.push(
      "",
      `Not included: ${missing.length} session(s) active in this window with no usage in list_sessions (${Object.entries(kinds)
        .map(([k, n]) => `${k}: ${n}`)
        .join(", ")}). "bridge" = runs on the user's own machine; its usage is only in that machine's local logs (report.mjs there).`
    );
  }
  return lines.join("\n");
}

function monthTable() {
  const monthly = new Map();
  for (const s of sessions) {
    const key = localDate(new Date(s.created_at)).slice(0, 7);
    monthly.set(key, add(monthly.get(key) ?? zero(), s.usage));
  }
  const lines = [
    `### Monthly usage — last ${MONTHS} months (${months[months.length - 1]} → ${months[0]}, most recent first)`,
    "",
    "| Month | Sessions | Input | Output | Cache Create | Cache Read | Total Tokens | Cost |",
    "|---|--:|--:|--:|--:|--:|--:|--:|",
  ];
  const sum = zero();
  for (const p of months) {
    const r = monthly.get(p) ?? zero();
    sum.n += r.n;
    for (const f of fields) sum[f] += r[f];
    lines.push(
      `| ${p} | ${r.n} | ${num(r.input_tokens)} | ${num(r.output_tokens)} | ${num(r.cache_write_tokens)} | ${num(r.cache_read_tokens)} | ${num(tokens(r))} | ${usd(r.cost_usd)} |`
    );
  }
  lines.push(
    `| **Total** | **${sum.n}** | **${num(sum.input_tokens)}** | **${num(sum.output_tokens)}** | **${num(sum.cache_write_tokens)}** | **${num(sum.cache_read_tokens)}** | **${num(tokens(sum))}** | **${usd(sum.cost_usd)}** |`
  );
  return lines.join("\n");
}

console.log(
  [`Cloud sessions (list_sessions) · Timezone: ${tz} · Today: ${today}`, "", sessionTable(), "", monthTable()].join("\n")
);
