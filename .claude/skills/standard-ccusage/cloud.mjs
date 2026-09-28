#!/usr/bin/env node
// Cloud-session half of the "standard ccusage" report.
// ccusage only sees logs on the machine it runs on, so usage from Claude Code on
// the web / cloud sessions has to come from the session list instead.
//
// Input: a JSON array of sessions, each {id, title, created_at, updated_at,
// environment_kind, usage: {cost_usd, input_tokens, output_tokens,
// cache_write_tokens, cache_read_tokens} | null}, as collected from
// list_sessions (see SKILL.md).
// Usage is only reported per session (not per day), so each session is counted
// on the day it was created, in the report timezone.
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

const localDate = (d) =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(d);
const today = localDate(new Date());
const [ty, tm, td] = today.split("-").map(Number);
const isoDay = (d) => d.toISOString().slice(0, 10);
const days = Array.from({ length: DAYS }, (_, i) =>
  isoDay(new Date(Date.UTC(ty, tm - 1, td - i)))
);
const months = Array.from({ length: MONTHS }, (_, i) =>
  isoDay(new Date(Date.UTC(ty, tm - 1 - i, 1))).slice(0, 7)
);

const sessions = JSON.parse(readFileSync(file, "utf8")).filter((s) => s.usage);
const fields = ["input_tokens", "output_tokens", "cache_write_tokens", "cache_read_tokens", "cost_usd"];
const zero = () => ({ n: 0, ...Object.fromEntries(fields.map((f) => [f, 0])) });
const daily = new Map();
const monthly = new Map();
for (const s of sessions) {
  const day = localDate(new Date(s.created_at));
  for (const [map, key] of [[daily, day], [monthly, day.slice(0, 7)]]) {
    const acc = map.get(key) ?? zero();
    acc.n += 1;
    for (const f of fields) acc[f] += s.usage[f] ?? 0;
    map.set(key, acc);
  }
}

const num = (n) => Math.round(n).toLocaleString("en-US");
const usd = (n) => `$${n.toFixed(2)}`;
function table(title, label, periods, data) {
  const lines = [
    `### ${title}`,
    "",
    `| ${label} | Sessions | Input | Output | Cache Create | Cache Read | Total Tokens | Cost |`,
    "|---|--:|--:|--:|--:|--:|--:|--:|",
  ];
  const sum = zero();
  for (const p of periods) {
    const r = data.get(p) ?? zero();
    sum.n += r.n;
    for (const f of fields) sum[f] += r[f];
    const total = r.input_tokens + r.output_tokens + r.cache_write_tokens + r.cache_read_tokens;
    lines.push(
      `| ${p} | ${r.n} | ${num(r.input_tokens)} | ${num(r.output_tokens)} | ${num(r.cache_write_tokens)} | ${num(r.cache_read_tokens)} | ${num(total)} | ${usd(r.cost_usd)} |`
    );
  }
  const total = sum.input_tokens + sum.output_tokens + sum.cache_write_tokens + sum.cache_read_tokens;
  lines.push(
    `| **Total** | **${sum.n}** | **${num(sum.input_tokens)}** | **${num(sum.output_tokens)}** | **${num(sum.cache_write_tokens)}** | **${num(sum.cache_read_tokens)}** | **${num(total)}** | **${usd(sum.cost_usd)}** |`
  );
  return lines.join("\n");
}

console.log(
  [
    `Cloud sessions · Timezone: ${tz} · Today: ${today} · each session counted on its start date`,
    "",
    table(`Cloud daily — past ${DAYS} days (most recent first)`, "Date", days, daily),
    "",
    table(`Cloud monthly — last ${MONTHS} months (most recent first)`, "Month", months, monthly),
  ].join("\n")
);
