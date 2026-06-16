"use client";

import { Download, FileSearch, Plus, Save, Search, ShieldCheck, Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, AuditLogItem, EvidenceItem, ManagedPoamItem } from "@/lib/api";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function riskClass(risk: string) {
  if (risk === "High") return "bg-red-50 text-red-700";
  if (risk === "Medium") return "bg-amber-50 text-amber-700";
  return "bg-blue-50 text-blue-700";
}

function statusClass(status: string) {
  if (status === "Closed") return "bg-emerald-50 text-emerald-700";
  if (status === "In Progress") return "bg-blue-50 text-blue-700";
  if (status === "Blocked") return "bg-red-50 text-red-700";
  return "bg-slate-100 text-slate-700";
}

export default function PoamPage() {
  const [items, setItems] = useState<ManagedPoamItem[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [controlFilter, setControlFilter] = useState("");
  const [linkedEvidence, setLinkedEvidence] = useState<EvidenceItem[]>([]);
  const [activity, setActivity] = useState<AuditLogItem[]>([]);
  const [status, setStatus] = useState("Ready");

  async function refresh(preferredId?: number | null) {
    const rows = await api.poamItems(query, statusFilter, riskFilter, controlFilter);
    setItems(rows);
    setActiveId((current) => {
      if (preferredId !== undefined) return preferredId;
      return rows.some((item) => item.id === current) ? current : rows[0]?.id ?? null;
    });
  }

  useEffect(() => {
    refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query, statusFilter, riskFilter, controlFilter]);

  const active = useMemo(() => items.find((item) => item.id === activeId) ?? items[0], [items, activeId]);

  useEffect(() => {
    if (!active?.id) {
      setLinkedEvidence([]);
      return;
    }
    api.evidence("", active.control_id, "", "", active.id).then(setLinkedEvidence).catch(() => setLinkedEvidence([]));
    api.auditLogs("", "", "Managed POA&M", String(active.id)).then(setActivity).catch(() => setActivity([]));
  }, [active?.id, active?.control_id]);

  const summary = useMemo(() => {
    return {
      open: items.filter((item) => item.status === "Open").length,
      progress: items.filter((item) => item.status === "In Progress").length,
      blocked: items.filter((item) => item.status === "Blocked").length,
      closed: items.filter((item) => item.status === "Closed").length,
      high: items.filter((item) => item.risk === "High").length,
    };
  }, [items]);

  async function generate() {
    setStatus("Generating POA&M items from objective gaps...");
    const result = await api.generatePoamItems();
    await refresh();
    setStatus(`Created ${result.created}; ${result.existing} already existed. ${result.total_open} open item(s).`);
  }

  async function save(item: ManagedPoamItem) {
    setStatus(`Saving ${item.control_id} objective ${item.objective_label}...`);
    const saved = await api.savePoamItem(item);
    setItems((current) => current.map((row) => (row.id === saved.id ? saved : row)));
    setActiveId(saved.id);
    setActivity(await api.auditLogs("", "", "Managed POA&M", String(saved.id)));
    setStatus("POA&M item saved.");
  }

  async function uploadEvidence(file: File | null) {
    if (!file || !active) return;
    setStatus(`Uploading and analyzing ${file.name} for ${active.control_id}...`);
    const content = await fileToBase64(file);
    const uploaded = await api.uploadEvidence({
      file_name: file.name,
      content_base64: content,
      control_id: active.control_id,
      document_type: "POA&M Evidence Artifact",
      data_classification: "Public",
      contains_cui: false,
      contains_itar: false,
      contains_pii: false,
      managed_poam_id: active.id,
      owner: active.owner,
      title: `${active.control_id} Objective ${active.objective_label} - ${file.name}`,
    });
    setLinkedEvidence(await api.evidence("", active.control_id, "", "", active.id));
    setActivity(await api.auditLogs("", "", "Managed POA&M", String(active.id)));
    setStatus(`Uploaded ${uploaded.file_name} to selected POA&M item ${active.id}. Review its objective mapping before closing the item.`);
  }

  function updateActive(patch: Partial<ManagedPoamItem>) {
    if (!active) return;
    setItems((current) => current.map((item) => (item.id === active.id ? { ...item, ...patch } : item)));
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">POA&M Management</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href="/health" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileSearch size={16} />
              Health
            </a>
            <button onClick={generate} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <Plus size={16} />
              Create POA&M Items
            </button>
            <a href={api.managedPoamExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <Download size={16} />
              Export XLSX
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 md:grid-cols-5">
          {[
            ["Open", summary.open],
            ["In Progress", summary.progress],
            ["Blocked", summary.blocked],
            ["Closed", summary.closed],
            ["High Risk", summary.high],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-[430px_1fr]">
          <aside className="rounded-md border border-border bg-white p-4">
            <div className="grid gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm outline-none focus:border-primary" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search POA&M" />
              </div>
              <div className="grid gap-2 md:grid-cols-3">
                <select className="h-10 rounded-md border border-border px-3 text-sm" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  <option value="">All status</option>
                  <option>Open</option>
                  <option>In Progress</option>
                  <option>Blocked</option>
                  <option>Closed</option>
                </select>
                <select className="h-10 rounded-md border border-border px-3 text-sm" value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>
                  <option value="">All risk</option>
                  <option>High</option>
                  <option>Medium</option>
                  <option>Low</option>
                </select>
                <input className="h-10 rounded-md border border-border px-3 text-sm" value={controlFilter} onChange={(event) => setControlFilter(event.target.value)} placeholder="Control" />
              </div>
            </div>
            <div className="mt-4 max-h-[680px] space-y-2 overflow-y-auto">
              {items.map((item) => (
                <button key={item.id} onClick={() => setActiveId(item.id)} className={`w-full rounded-md border p-3 text-left text-sm ${active?.id === item.id ? "border-primary bg-blue-50" : "border-border bg-white"}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{item.control_id} ({item.objective_label})</span>
                    <span className={`rounded px-2 py-1 text-xs font-medium ${riskClass(item.risk)}`}>{item.risk}</span>
                  </div>
                  <div className="mt-1 text-xs text-slate-500">{item.control_title}</div>
                  <div className="mt-2"><span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(item.status)}`}>{item.status}</span></div>
                </button>
              ))}
              {!items.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">No POA&M items match the filters.</div>}
            </div>
          </aside>

          {active ? (
            <section className="rounded-md border border-border bg-white p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium text-primary">{active.control_id} objective {active.objective_label}</div>
                  <h2 className="text-lg font-semibold">{active.control_title}</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{active.objective}</p>
                </div>
                <button onClick={() => save(active)} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                  <Save size={16} />
                  Save
                </button>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-4">
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">Owner</span>
                  <input className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.owner} onChange={(event) => updateActive({ owner: event.target.value })} />
                </label>
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">Due date</span>
                  <input className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.due_date} onChange={(event) => updateActive({ due_date: event.target.value })} placeholder="YYYY-MM-DD" />
                </label>
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">Risk</span>
                  <select className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.risk} onChange={(event) => updateActive({ risk: event.target.value })}>
                    <option>High</option>
                    <option>Medium</option>
                    <option>Low</option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">Status</span>
                  <select className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.status} onChange={(event) => updateActive({ status: event.target.value })}>
                    <option>Open</option>
                    <option>In Progress</option>
                    <option>Blocked</option>
                    <option>Closed</option>
                  </select>
                </label>
              </div>

              <div className="mt-4 grid gap-4">
                {[
                  ["gap_statement", "Gap Statement"],
                  ["evidence_needed", "Evidence Needed"],
                  ["corrective_action", "Corrective Action"],
                  ["notes", "Notes"],
                ].map(([key, label]) => (
                  <label key={key} className="block">
                    <span className="text-sm font-semibold">{label}</span>
                    <textarea
                      className="mt-2 min-h-24 w-full rounded-md border border-border p-3 text-sm leading-6 outline-none focus:border-primary"
                      value={String(active[key as keyof ManagedPoamItem] ?? "")}
                      onChange={(event) => updateActive({ [key]: event.target.value } as Partial<ManagedPoamItem>)}
                    />
                  </label>
                ))}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <div className="w-full rounded-md border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
                  Azure Commercial upload rule: do not upload CUI, ITAR, export-controlled data, classified data, or sensitive government contract information.
                </div>
                <label className="inline-flex h-10 cursor-pointer items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                  <Upload size={16} />
                  Upload Evidence
                  <input className="sr-only" type="file" onChange={(event) => uploadEvidence(event.target.files?.[0] ?? null)} />
                </label>
                <a href={`/controls/${active.control_id}/objectives`} className="inline-flex h-10 items-center rounded-md border border-border bg-white px-4 text-sm font-medium">Objective Workspace</a>
                <a href={`/evidence?control=${active.control_id}`} className="inline-flex h-10 items-center rounded-md border border-border bg-white px-4 text-sm font-medium">Evidence</a>
              </div>

              <div className="mt-5 rounded-md border border-border p-4">
                <h3 className="text-sm font-semibold">Evidence Linked to This POA&M</h3>
                <div className="mt-3 space-y-2">
                  {linkedEvidence.map((evidence) => (
                    <div key={evidence.id} className="rounded-md bg-muted p-3 text-sm">
                      <div className="font-medium">{evidence.title}</div>
                      <div className="mt-1 text-xs text-slate-600">{evidence.file_name} | {evidence.review_status} | {evidence.drift_state}</div>
                    </div>
                  ))}
                  {!linkedEvidence.length && <div className="text-sm text-slate-600">No evidence is linked to this selected POA&M item.</div>}
                </div>
              </div>

              <div className="mt-5 rounded-md border border-border p-4">
                <h3 className="text-sm font-semibold">Activity History</h3>
                <div className="mt-3 space-y-2">
                  {activity.slice(0, 8).map((item) => (
                    <div key={item.id} className="rounded-md bg-muted p-3 text-sm">
                      <div className="font-medium">{item.action}</div>
                      <div className="mt-1 text-xs text-slate-600">{item.details}</div>
                      <div className="mt-1 text-xs text-slate-500">{item.user_name} | {new Date(item.created_at).toLocaleString()}</div>
                    </div>
                  ))}
                  {!activity.length && <div className="text-sm text-slate-600">No activity has been recorded for this POA&M item yet.</div>}
                </div>
              </div>
            </section>
          ) : (
            <section className="rounded-md border border-border bg-white p-5 text-sm text-slate-700">
              Create POA&M items from objective gaps to begin tracking corrective actions.
            </section>
          )}
        </div>
      </section>
    </main>
  );
}
