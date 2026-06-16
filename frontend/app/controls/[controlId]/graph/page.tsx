"use client";

import { AlertTriangle, ArrowLeft, Bot, Database, FileSearch, FileText, Network, ShieldCheck } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, ControlGraph, ControlGraphItem } from "@/lib/api";

function statusClass(status: string) {
  if (status === "Implemented" || status === "Parsed" || status === "Analyzed") return "bg-emerald-50 text-emerald-700";
  if (status === "At Risk" || status === "Open") return "bg-red-50 text-red-700";
  if (status === "Partially Implemented" || status === "Draft") return "bg-amber-50 text-amber-700";
  return "bg-slate-100 text-slate-700";
}

function GraphList({ title, icon, items, empty }: { title: string; icon: React.ReactNode; items: ControlGraphItem[]; empty: string }) {
  return (
    <section className="rounded-md border border-border bg-white p-4">
      <h2 className="flex items-center gap-2 text-base font-semibold">{icon}{title}</h2>
      <div className="mt-3 space-y-2">
        {items.map((item) => (
          <div key={`${title}-${item.id}-${item.name}`} className="rounded-md border border-border p-3 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="font-medium">{item.name}</div>
              {item.status && <span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(item.status)}`}>{item.status}</span>}
            </div>
            <div className="mt-1 text-xs text-slate-500">{item.item_type} | {item.source}</div>
            {item.detail && <p className="mt-2 text-slate-700">{item.detail}</p>}
          </div>
        ))}
        {!items.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">{empty}</div>}
      </div>
    </section>
  );
}

export default function ControlGraphPage() {
  const params = useParams<{ controlId: string }>();
  const controlId = decodeURIComponent(params?.controlId ?? "");
  const [graph, setGraph] = useState<ControlGraph | null>(null);
  const [status, setStatus] = useState("Loading graph...");

  useEffect(() => {
    if (!controlId) return;
    api.controlGraph(controlId)
      .then((data) => {
        setGraph(data);
        setStatus("Ready");
      })
      .catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, [controlId]);

  const counts = useMemo(() => {
    if (!graph) return [];
    return [
      ["Policies", graph.policies.length],
      ["Procedures", graph.procedures.length],
      ["SSP refs", graph.ssp_references.length],
      ["Evidence", graph.evidence.length],
      ["POA&M", graph.poam_items.length],
      ["Alerts", graph.alerts.length],
    ];
  }, [graph]);

  if (!graph) {
    return (
      <main className="grid min-h-screen place-items-center bg-background px-6">
        <div className="rounded-md border border-border bg-white p-5 text-sm text-slate-700">{status}</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <a href="/" className="mb-2 inline-flex items-center gap-2 text-sm text-slate-600">
              <ArrowLeft size={15} />
              Controls
            </a>
            <h1 className="text-xl font-semibold tracking-normal">{graph.control_id} Knowledge Graph</h1>
            <p className="text-sm text-slate-600">{graph.control_title} | {status}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <a href={`/controls/${graph.control_id}/objectives`} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileSearch size={16} />
              Objectives
            </a>
            <div className={`rounded px-3 py-2 text-sm font-medium ${statusClass(graph.status)}`}>{graph.status}</div>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="rounded-md border border-border bg-white p-5">
          <div className="flex items-start gap-3">
            <div className="mt-1 flex h-10 w-10 items-center justify-center rounded-md bg-primary text-white">
              <Network size={20} />
            </div>
            <div>
              <div className="text-sm font-medium text-primary">{graph.family}</div>
              <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-700">{graph.requirement}</p>
            </div>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            {counts.map(([label, value]) => (
              <div key={label} className="rounded-md bg-muted p-3">
                <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
                <div className="mt-2 text-xl font-semibold">{value}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <GraphList title="Policies" icon={<ShieldCheck size={17} />} items={graph.policies} empty="No policy relationship has been mapped yet." />
          <GraphList title="Procedures" icon={<FileText size={17} />} items={graph.procedures} empty="No procedure relationship has been mapped yet." />
          <GraphList title="Evidence Files" icon={<FileSearch size={17} />} items={graph.evidence} empty="No evidence files are currently linked to this control." />
          <GraphList title="SSP References" icon={<Database size={17} />} items={graph.ssp_references} empty="No SSP references are currently linked to this control." />
          <GraphList title="POA&M Items" icon={<AlertTriangle size={17} />} items={graph.poam_items} empty="No POA&M items are currently linked to this control." />
          <section className="rounded-md border border-border bg-white p-4">
            <h2 className="flex items-center gap-2 text-base font-semibold"><Bot size={17} /> Automation Sources</h2>
            <div className="mt-3 space-y-2">
              {graph.evidence_sources.slice(0, 8).map((source) => (
                <div key={source.id} className="rounded-md border border-border p-3 text-sm">
                  <div className="font-medium">{source.evidence_name}</div>
                  <div className="mt-1 text-xs text-slate-500">{source.connected_system} | {source.collection_method} | {source.review_frequency}</div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {!!graph.alerts.length && (
          <section className="mt-5 rounded-md border border-border bg-white p-4">
            <h2 className="flex items-center gap-2 text-base font-semibold"><AlertTriangle size={17} /> Open Drift Alerts</h2>
            <div className="mt-3 space-y-2">
              {graph.alerts.map((alert) => (
                <div key={alert.id} className="rounded-md border border-border p-3 text-sm">
                  <div className="font-medium">{alert.title}</div>
                  <p className="mt-1 text-slate-700">{alert.description}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </section>
    </main>
  );
}
