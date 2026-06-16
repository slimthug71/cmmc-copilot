"use client";

import { Activity, AlertTriangle, Bot, Database, FileSearch, Gauge, Search, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, AssessmentSimulation, ControlEvidenceMap, CopilotDashboard, DriftAlert } from "@/lib/api";

const emptyDashboard: CopilotDashboard = {
  overall_readiness: 0,
  healthy_controls: 0,
  at_risk_controls: 0,
  partially_implemented_controls: 0,
  not_implemented_controls: 0,
  open_alerts: 0,
  automated_sources: 0,
  manual_sources: 0,
  mapped_controls: 0,
  total_controls: 110,
  recent_alerts: [],
};

const statuses = ["", "Implemented", "Partially Implemented", "At Risk", "Not Implemented"];
const sourceSystems = ["", "Microsoft Entra ID", "Microsoft Intune", "Microsoft Defender", "Microsoft 365 Audit Logs", "CMMC Pilot", "Nessus/Qualys", "ServiceNow/Jira"];

function statusClass(status: string) {
  if (status === "Implemented") return "bg-emerald-50 text-emerald-700";
  if (status === "At Risk") return "bg-red-50 text-red-700";
  if (status === "Partially Implemented") return "bg-amber-50 text-amber-700";
  return "bg-slate-100 text-slate-700";
}

export default function CopilotPage() {
  const [dashboard, setDashboard] = useState<CopilotDashboard>(emptyDashboard);
  const [mappings, setMappings] = useState<ControlEvidenceMap[]>([]);
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [activeControlId, setActiveControlId] = useState<string>("");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [simulation, setSimulation] = useState<AssessmentSimulation | null>(null);
  const [status, setStatus] = useState("Ready");

  async function refresh() {
    const [summary, rows, openAlerts] = await Promise.all([
      api.copilotDashboard(),
      api.controlEvidenceMappings(query, statusFilter, sourceFilter),
      api.driftAlerts("Open"),
    ]);
    setDashboard(summary);
    setMappings(rows);
    setAlerts(openAlerts);
    setActiveControlId((current) => rows.some((row) => row.control_id === current) ? current : rows[0]?.control_id ?? "");
  }

  useEffect(() => {
    refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query, statusFilter, sourceFilter]);

  const active = useMemo(
    () => mappings.find((item) => item.control_id === activeControlId) ?? mappings[0],
    [mappings, activeControlId]
  );

  async function runSimulation() {
    if (!active) return;
    setStatus(`Simulating assessment for ${active.control_id}...`);
    setSimulation(await api.simulateAssessment({
      control_id: active.control_id,
      assessor_question: `Show me how ${active.control_title.toLowerCase()} is implemented and evidenced.`,
    }));
    setStatus("Ready");
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Continuous Compliance Copilot</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href="/compliance" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileSearch size={16} />
              Compliance
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 md:grid-cols-5">
          {[
            ["Readiness", `${dashboard.overall_readiness}%`],
            ["Healthy", dashboard.healthy_controls],
            ["At Risk", dashboard.at_risk_controls],
            ["Open Alerts", dashboard.open_alerts],
            ["Automated Sources", dashboard.automated_sources],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500">
                <Gauge size={14} />
                {label}
              </div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-[390px_1fr]">
          <aside className="space-y-5">
            <section className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Control-to-Evidence Map</h2>
              <div className="mt-3 space-y-2">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                  <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm outline-none focus:border-primary" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search controls or evidence sources" />
                </div>
                <select className="h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  {statuses.map((item) => <option key={item || "All"} value={item}>{item || "All statuses"}</option>)}
                </select>
                <select className="h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary" value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
                  {sourceSystems.map((item) => <option key={item || "All"} value={item}>{item || "All source systems"}</option>)}
                </select>
              </div>
              <div className="mt-4 max-h-[560px] space-y-2 overflow-y-auto pr-1">
                {mappings.map((mapping) => (
                  <button key={mapping.control_id} onClick={() => setActiveControlId(mapping.control_id)} className={`w-full rounded-md border px-3 py-2 text-left text-sm ${active?.control_id === mapping.control_id ? "border-primary bg-blue-50" : "border-border bg-white"}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium">{mapping.control_id}</span>
                      <span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(mapping.status)}`}>{mapping.status}</span>
                    </div>
                    <div className="mt-1 text-xs text-slate-500">{mapping.evidence_count} evidence | {mapping.connected_sources} automated | {mapping.open_alerts} alerts</div>
                  </button>
                ))}
                {!mappings.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">No matching controls.</div>}
              </div>
            </section>
          </aside>

          <div className="space-y-5">
            {active ? (
              <section className="rounded-md border border-border bg-white p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">{active.control_id} - {active.control_title}</h2>
                    <p className="text-sm text-slate-600">{active.family} | Review {active.review_frequency}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={runSimulation} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-3 text-sm font-medium">
                      <Bot size={15} />
                      Simulate
                    </button>
                    <span className={`rounded px-3 py-2 text-sm font-medium ${statusClass(active.status)}`}>{active.status}</span>
                  </div>
                </div>
                <div className="mt-4 grid gap-3 md:grid-cols-4">
                  {[
                    ["Required Evidence", active.required_sources],
                    ["Automated Sources", active.connected_sources],
                    ["Manual Sources", active.manual_sources],
                    ["Open Alerts", active.open_alerts],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-md bg-muted p-3">
                      <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
                      <div className="mt-2 text-xl font-semibold">{value}</div>
                    </div>
                  ))}
                </div>

                {simulation && simulation.control_id === active.control_id && (
                  <div className="mt-5 rounded-md border border-border bg-muted p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-semibold">Assessment Simulation</h3>
                      <span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(simulation.assessment_status === "Met" ? "Implemented" : simulation.assessment_status === "Partially Met" ? "Partially Implemented" : "Not Implemented")}`}>
                        {simulation.assessment_status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-700">{simulation.assessor_feedback}</p>
                    <div className="mt-3 grid gap-3 lg:grid-cols-2">
                      <div>
                        <div className="text-xs font-medium uppercase text-slate-500">Missing</div>
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                          {simulation.missing.map((item) => <li key={item}>{item}</li>)}
                        </ul>
                      </div>
                      <div>
                        <div className="text-xs font-medium uppercase text-slate-500">Next Steps</div>
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                          {simulation.recommended_next_steps.map((item) => <li key={item}>{item}</li>)}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                <div className="mt-5 grid gap-5 lg:grid-cols-2">
                  <div>
                    <h3 className="flex items-center gap-2 text-sm font-semibold"><Database size={16} /> Evidence Sources</h3>
                    <div className="mt-2 space-y-2">
                      {active.evidence_sources.map((source) => (
                        <div key={source.id} className="rounded-md border border-border p-3 text-sm">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="font-medium">{source.evidence_name}</div>
                            <span className="rounded bg-muted px-2 py-1 text-xs">{source.collection_method}</span>
                          </div>
                          <div className="mt-1 text-xs text-slate-600">{source.connected_system} | {source.source_type} | {source.review_frequency}</div>
                          <p className="mt-2 text-slate-700">{source.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="flex items-center gap-2 text-sm font-semibold"><Activity size={16} /> Monitoring Rules</h3>
                    <div className="mt-2 space-y-2">
                      {active.monitoring_rules.map((rule) => (
                        <div key={rule.id} className="rounded-md border border-border p-3 text-sm">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="font-medium">{rule.rule_name}</div>
                            <span className="rounded bg-muted px-2 py-1 text-xs">{rule.severity}</span>
                          </div>
                          <div className="mt-1 text-xs text-slate-600">{rule.source_system}</div>
                          <p className="mt-2 text-slate-700">{rule.condition}</p>
                        </div>
                      ))}
                      {!active.monitoring_rules.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">No automated monitoring rules mapped yet.</div>}
                    </div>
                  </div>
                </div>
              </section>
            ) : null}

            <section className="grid gap-5 lg:grid-cols-2">
              <div className="rounded-md border border-border bg-white p-5">
                <h2 className="flex items-center gap-2 text-base font-semibold"><AlertTriangle size={17} /> Drift Alerts</h2>
                <div className="mt-3 space-y-2">
                  {alerts.slice(0, 8).map((alert) => (
                    <div key={alert.id} className="rounded-md border border-border p-3 text-sm">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="font-medium">{alert.title}</div>
                        <span className="rounded bg-red-50 px-2 py-1 text-xs font-medium text-red-700">{alert.severity}</span>
                      </div>
                      <div className="mt-1 text-xs text-slate-500">{alert.control_id} - {alert.control_title}</div>
                      <p className="mt-2 text-slate-700">{alert.description}</p>
                    </div>
                  ))}
                  {!alerts.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">No open drift alerts.</div>}
                </div>
              </div>

              <div className="rounded-md border border-border bg-white p-5">
                <h2 className="flex items-center gap-2 text-base font-semibold"><Bot size={17} /> Copilot Foundation</h2>
                <div className="mt-3 space-y-2 text-sm">
                  <div className="rounded-md bg-muted p-3">Each control now knows its required evidence, possible source systems, collection method, and review frequency.</div>
                  <div className="rounded-md bg-muted p-3">Microsoft 365 source mappings are ready for Entra ID, Intune, Defender, and Audit Logs connectors.</div>
                  <div className="rounded-md bg-muted p-3">Open drift alerts are generated when documentation maps to a control but primary evidence is missing.</div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}
