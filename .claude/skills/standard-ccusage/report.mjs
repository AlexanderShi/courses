#!/usr/bin/env node
// "Standard ccusage" report:
//   1. Daily usage for the past 30 days (today included), most recent first.
//   2. Monthly totals for the last 6 months (current month included), each month
//      on its own row, most recent first.
// Days/months with no usage are shown as zero rows so gaps are visible.
//
// Usage: node report.mjs [--timezone <IANA tz>]
// Set CCUSAGE_CMD to override how ccusage is invoked (default: "npx -y ccusage@latest").

import { execSync } from "node:child_process";

const args = process.argv.slice(2);
const tzFlag = args.indexOf("--timezone");
const tz =
  (tzFlag !== -1 && args[tzFlag + 1]) ||
  Intl.DateTimeFormat().resolvedOptions().timeZone ||
  "UTC";
const ccusage = process.env.CCUSAGE_CMD || "npx -y ccusage@latest";

const DAYS = 30;
const MONTHS = 6;

// Today's calendar date in the report timezone, as YYYY-MM-DD.
const today = new Intl.DateTimeFormat("en-CA", {
  timeZone: tz,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
}).format(new Date());
const [ty, tm, td] = today.split("-").map(Number);

const isoDay = (d) => d.toISOString().slice(0, 10);
const days = Array.from({ length: DAYS }, (_, i) =>
  isoDay(new Date(Date.UTC(ty, tm - 1, td - i)))
);
const months = Array.from({ length: MONTHS }, (_, i) =>
  isoDay(new Date(Date.UTC(ty, tm - 1 - i, 1))).slice(0, 7)
);

function run(report, since) {
  const cmd = `${ccusage} ${report} --json --since ${since.replaceAll("-", "")} --timezone ${tz}`;
  const out = execSync(cmd, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
    maxBuffer: 64 * 1024 * 1024,
  });
  const rows = JSON.parse(out)[report] ?? [];
  const byPeriod = new Map();
  for (const r of rows) {
    const key = r.period ?? r.date ?? r.month;
    const acc = byPeriod.get(key) ?? {
      inputTokens: 0,
      outputTokens: 0,
      cacheCreationTokens: 0,
      cacheReadTokens: 0,
      totalTokens: 0,
      totalCost: 0,
      models: new Set(),
    };
    for (const f of [
      "inputTokens",
      "outputTokens",
      "cacheCreationTokens",
      "cacheReadTokens",
      "totalTokens",
      "totalCost",
    ])
      acc[f] += r[f] ?? 0;
    for (const m of r.modelsUsed ?? []) acc.models.add(m);
    byPeriod.set(key, acc);
  }
  return byPeriod;
}

const num = (n) => (n ? n.toLocaleString("en-US") : "0");
const usd = (n) => `$${(n ?? 0).toFixed(2)}`;
const shortModel = (m) => m.replace(/^claude-/, "").replace(/-\d{8}$/, "");

function table(title, label, periods, data) {
  const header = `| ${label} | Models | Input | Output | Cache Create | Cache Read | Total Tokens | Cost |`;
  const lines = [
    `### ${title}`,
    "",
    header,
    "|---|---|--:|--:|--:|--:|--:|--:|",
  ];
  const sum = {
    inputTokens: 0,
    outputTokens: 0,
    cacheCreationTokens: 0,
    cacheReadTokens: 0,
    totalTokens: 0,
    totalCost: 0,
  };
  for (const p of periods) {
    const r = data.get(p);
    if (!r) {
      lines.push(`| ${p} | — | 0 | 0 | 0 | 0 | 0 | $0.00 |`);
      continue;
    }
    for (const f of Object.keys(sum)) sum[f] += r[f];
    const models = [...r.models].map(shortModel).join(", ") || "—";
    lines.push(
      `| ${p} | ${models} | ${num(r.inputTokens)} | ${num(r.outputTokens)} | ${num(
        r.cacheCreationTokens
      )} | ${num(r.cacheReadTokens)} | ${num(r.totalTokens)} | ${usd(r.totalCost)} |`
    );
  }
  lines.push(
    `| **Total** | | **${num(sum.inputTokens)}** | **${num(sum.outputTokens)}** | **${num(
      sum.cacheCreationTokens
    )}** | **${num(sum.cacheReadTokens)}** | **${num(sum.totalTokens)}** | **${usd(
      sum.totalCost
    )}** |`
  );
  return lines.join("\n");
}

const daily = run("daily", days[days.length - 1]);
const monthly = run("monthly", `${months[months.length - 1]}-01`);

console.log(
  [
    `Timezone: ${tz} · Today: ${today}`,
    "",
    table(
      `Daily usage — past ${DAYS} days (${days[days.length - 1]} → ${today}, most recent first)`,
      "Date",
      days,
      daily
    ),
    "",
    table(
      `Monthly usage — last ${MONTHS} months (${months[months.length - 1]} → ${months[0]}, most recent first)`,
      "Month",
      months,
      monthly
    ),
  ].join("\n")
);
