#!/usr/bin/env node
// "Standard ccusage" report (local logs, via ccusage):
//   1. Past 30 days, listed per session (most recent first), with a total.
//   2. Monthly totals for the last 6 months (current month included), each month
//      on its own row, most recent first. Months with no usage show as zero rows.
//
// Usage: node report.mjs [--timezone <IANA tz>]
// Set CCUSAGE_CMD to override how ccusage is invoked (default: "npx -y ccusage@latest").

import { execSync } from "node:child_process";
import { closeSync, existsSync, openSync, readdirSync, readSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join } from "node:path";

const args = process.argv.slice(2);
const tzFlag = args.indexOf("--timezone");
const tz =
  (tzFlag !== -1 && args[tzFlag + 1]) ||
  Intl.DateTimeFormat().resolvedOptions().timeZone ||
  "UTC";
const ccusage = process.env.CCUSAGE_CMD || "npx -y ccusage@latest";

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

function run(report, since) {
  const cmd = `${ccusage} ${report} --json --since ${since.replaceAll("-", "")} --timezone ${tz}`;
  const out = execSync(cmd, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
    maxBuffer: 64 * 1024 * 1024,
  });
  return JSON.parse(out)[report] ?? [];
}

const FIELDS = [
  "inputTokens",
  "outputTokens",
  "cacheCreationTokens",
  "cacheReadTokens",
  "totalTokens",
  "totalCost",
];
const zero = () => Object.fromEntries(FIELDS.map((f) => [f, 0]));
const add = (acc, r) => {
  for (const f of FIELDS) acc[f] += r[f] ?? 0;
  return acc;
};

const num = (n) => (n ? Math.round(n).toLocaleString("en-US") : "0");
const usd = (n) => `$${(n ?? 0).toFixed(2)}`;
const shortModel = (m) => m.replace(/^claude-/, "").replace(/-\d{8}$/, "");
const cell = (s) => String(s).replace(/\s+/g, " ").replaceAll("|", "\\|").trim();

// --- Session labels from the local JSONL logs --------------------------------

const projectRoots = [
  ...(process.env.CLAUDE_CONFIG_DIR ?? "").split(",").filter(Boolean).map((d) => join(d, "projects")),
  join(homedir(), ".config", "claude", "projects"),
  join(homedir(), ".claude", "projects"),
].filter((d) => existsSync(d));

const logIndex = new Map(); // sessionId -> jsonl path
for (const root of projectRoots)
  for (const dir of readdirSync(root, { withFileTypes: true }))
    if (dir.isDirectory())
      for (const f of readdirSync(join(root, dir.name)))
        if (f.endsWith(".jsonl") && !logIndex.has(f.slice(0, -6)))
          logIndex.set(f.slice(0, -6), join(root, dir.name, f));

function readHead(path, bytes = 2 * 1024 * 1024) {
  const fd = openSync(path, "r");
  const buf = Buffer.alloc(bytes);
  const n = readSync(fd, buf, 0, bytes, 0);
  closeSync(fd);
  return buf.subarray(0, n).toString("utf8");
}

function describe(sessionId) {
  const path = logIndex.get(sessionId);
  const info = { start: null, project: "", title: "" };
  if (!path) return info;
  let prompt = "";
  for (const line of readHead(path).split("\n")) {
    let e;
    try {
      e = JSON.parse(line);
    } catch {
      continue;
    }
    if (!info.start && e.timestamp) info.start = new Date(e.timestamp);
    if (!info.project && e.cwd) info.project = basename(e.cwd);
    const title = e.customTitle ?? e.aiTitle ?? e.title ?? (e.type === "summary" ? e.summary : undefined);
    if (typeof title === "string" && title && !info.title) info.title = title;
    if (!prompt && e.type === "user" && !e.isSidechain) {
      const c = e.message?.content;
      const text = typeof c === "string" ? c : Array.isArray(c) ? c.find((p) => p.type === "text")?.text : "";
      if (text && !text.startsWith("<")) prompt = text;
    }
  }
  if (!info.title) info.title = prompt.length > 60 ? `${prompt.slice(0, 57)}...` : prompt;
  return info;
}

// --- Past 30 days, per session ------------------------------------------------

function sessionTable() {
  const rows = run("session", windowStart)
    .map((r) => {
      const last = r.metadata?.lastActivity ? new Date(r.metadata.lastActivity) : null;
      const d = describe(r.period);
      return { ...r, id: r.period, last, start: d.start ?? last, project: d.project, title: d.title };
    })
    .filter((r) => r.last && localDate(r.last) >= windowStart)
    .sort((a, b) => b.start - a.start);

  const lines = [
    `### Past ${DAYS} days by session (${windowStart} → ${today}, most recent first)`,
    "",
    "| Start | Last active | Session | Project | Models | Total Tokens | Cost |",
    "|---|---|---|---|---|--:|--:|",
  ];
  const sum = zero();
  for (const r of rows) {
    add(sum, r);
    const models = (r.modelsUsed ?? []).map(shortModel).join(", ") || "—";
    lines.push(
      `| ${localStamp(r.start)} | ${localStamp(r.last)} | ${cell(r.title || r.id.slice(0, 8))} | ${cell(r.project || "—")} | ${models} | ${num(r.totalTokens)} | ${usd(r.totalCost)} |`
    );
  }
  if (!rows.length) lines.push("| — | — | (no local sessions in this window) | | | 0 | $0.00 |");
  lines.push(`| **Total** | | **${rows.length} sessions** | | | **${num(sum.totalTokens)}** | **${usd(sum.totalCost)}** |`);
  return lines.join("\n");
}

// --- Last 6 months, per month -------------------------------------------------

function monthTable() {
  const byMonth = new Map();
  for (const r of run("monthly", `${months[months.length - 1]}-01`)) {
    const key = r.period ?? r.month;
    const acc = byMonth.get(key) ?? { ...zero(), models: new Set() };
    add(acc, r);
    for (const m of r.modelsUsed ?? []) acc.models.add(m);
    byMonth.set(key, acc);
  }
  const lines = [
    `### Monthly usage — last ${MONTHS} months (${months[months.length - 1]} → ${months[0]}, most recent first)`,
    "",
    "| Month | Models | Input | Output | Cache Create | Cache Read | Total Tokens | Cost |",
    "|---|---|--:|--:|--:|--:|--:|--:|",
  ];
  const sum = zero();
  for (const p of months) {
    const r = byMonth.get(p);
    if (!r) {
      lines.push(`| ${p} | — | 0 | 0 | 0 | 0 | 0 | $0.00 |`);
      continue;
    }
    add(sum, r);
    const models = [...r.models].map(shortModel).join(", ") || "—";
    lines.push(
      `| ${p} | ${models} | ${num(r.inputTokens)} | ${num(r.outputTokens)} | ${num(r.cacheCreationTokens)} | ${num(r.cacheReadTokens)} | ${num(r.totalTokens)} | ${usd(r.totalCost)} |`
    );
  }
  lines.push(
    `| **Total** | | **${num(sum.inputTokens)}** | **${num(sum.outputTokens)}** | **${num(sum.cacheCreationTokens)}** | **${num(sum.cacheReadTokens)}** | **${num(sum.totalTokens)}** | **${usd(sum.totalCost)}** |`
  );
  return lines.join("\n");
}

console.log(
  [`Local logs (ccusage) · Timezone: ${tz} · Today: ${today}`, "", sessionTable(), "", monthTable()].join("\n")
);
