"use client";

import { ArrowUpRight, FileSearch, GitBranch, HeartPulse, Search, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, ControlHealthDashboard, ControlHealthRow } from "@/lib/api";

const emptyDashboard: ControlHealthDashboard = {
  healthy_controls: 0,
  monitor_controls: 0,
  at_risk_controls: 0,
  critical_controls: 0,
  stale_evidence: 0,
  poam_candidates: 0,
  rows: [],
};

function healthClass(status: string) {
  if (status === "Healthy") return "bg-emerald-50 text-emerald-700";
  if (status === "Monitor") return "bg-blue-50 text-blue-700";
  if (status === "At Risk") return "bg-amber-50 text-amber-700";
  return "bg-red-50 text-red-700";
}

function hasFlag(row: ControlHealthRow, flag: string) {
  if (flag === "stale") return row.stale_evidence > 0;
  if (flag === "rejected") return row.rejected_evidence > 0;
  if (flag === "noAccepted") return row.accepted_evidence === 0;
  return true;
}

export default function HealthPage() {
  const [dashboard, setDashboard] = useState<ControlHealthDashboard>(emptyDashboard);
  const [query, setQuery] = useState("");
  const [family, setFamily] = useState("");
  const [health, setHealth] = useState("");
  const [flag, setFlag] = useState("");
  const [status, setStatus] = useState("Loading control health...");

  useEffect(() => {
    api.controlHealth()
      .then((data) => {
        setDashboard(data);
        setStatus("Ready");
      })
      .catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, []);

  const families = useMemo(() => Array.from(new Set(dashboard.rows.map((row) => row.family))).sort(), [dashboard.rows]);
  const rows = useMemo(() => {
    const q = query.toLowerCase();
    return dashboard.rows.filter((row) => {
      return (
        (!q || `${row.control_id} ${row.title} ${row.family}`.toLowerCase().includes(q)) &&
        (!family || row.family === family) &&
        (!health || row.health_status === health) &&
        hasFlag(row, flag)
      );
    });
  }, [dashboard.rows, query, family, health, flag]);

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Control Health</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href="/evidence" className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <FileSearch size={16} />
              Evidence
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 md:grid-cols-6">
          {[
            ["Healthy", dashboard.healthy_controls],
            ["Monitor", dashboard.monitor_controls],
            ["At Risk", dashboard.at_risk_controls],
            ["Critical", dashboard.critical_controls],
            ["Stale Evidence", dashboard.stale_evidence],
            ["POA&M Candidates", dashboard.poam_candidates],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500">
                <HeartPulse size={14} />
                {label}
              </div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <section className="mt-5 rounded-md border border-border bg-white p-4">
          <div className="grid gap-3 lg:grid-cols-[1fr_220px_180px_220px]">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
              <input
                className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm outline-none focus:border-primary"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search controls"
              />
            </div>
            <select className="h-10 rounded-md border border-border px-3 text-sm" value={family} onChange={(event) => setFamily(event.target.value)}>
              <option value="">All families</option>
              {families.map((item) => <option key={item}>{item}</option>)}
            </select>
            <select className="h-10 rounded-md border border-border px-3 text-sm" value={health} onChange={(event) => setHealth(event.target.value)}>
              <option value="">All health</option>
              <option>Healthy</option>
              <option>Monitor</option>
              <option>At Risk</option>
              <option>Critical</option>
            </select>
            <select className="h-10 rounded-md border border-border px-3 text-sm" value={flag} onChange={(event) => setFlag(event.target.value)}>
              <option value="">All controls</option>
              <option value="stale">Has stale evidence</option>
              <option value="rejected">Has rejected evidence</option>
              <option value="noAccepted">No accepted evidence</option>
            </select>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[1100px] text-left text-sm">
              <thead className="border-b border-border text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-2">Control</th>
                  <th className="py-2">Family</th>
                  <th className="py-2">Objectives</th>
                  <th className="py-2">Accepted</th>
                  <th className="py-2">Review</th>
                  <th className="py-2">Replace</th>
                  <th className="py-2">Stale</th>
                  <th className="py-2">POA&M</th>
                  <th className="py-2">Health</th>
                  <th className="py-2">Links</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.control_id} className="border-b border-border">
                    <td className="py-3">
                      <div className="font-medium">{row.control_id}</div>
                      <div className="text-xs text-slate-500">{row.title}</div>
                    </td>
                    <td className="py-3">{row.family}</td>
                    <td className="py-3">{row.objectives_with_evidence}/{row.total_objectives} ({row.objective_coverage_score}%)</td>
                    <td className="py-3">{row.accepted_evidence}</td>
                    <td className="py-3">{row.under_review_evidence}</td>
                    <td className="py-3">{row.needs_replacement_evidence}</td>
                    <td className="py-3">{row.stale_evidence}</td>
                    <td className="py-3">{row.poam_candidates}</td>
                    <td className="py-3">
                      <span className={`rounded px-2 py-1 text-xs font-medium ${healthClass(row.health_status)}`}>{row.health_status}</span>
                    </td>
                    <td className="py-3">
                      <div className="flex flex-wrap gap-2">
                        <a title="Objectives" href={`/controls/${row.control_id}/objectives`} className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border bg-white">
                          <ArrowUpRight size={14} />
                        </a>
                        <a title="Graph" href={`/controls/${row.control_id}/graph`} className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border bg-white">
                          <GitBranch size={14} />
                        </a>
                        <a title="Evidence" href={`/evidence?control=${row.control_id}`} className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border bg-white">
                          <FileSearch size={14} />
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
                {!rows.length && (
                  <tr>
                    <td className="py-5 text-slate-600" colSpan={10}>No controls match the current filters.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}
