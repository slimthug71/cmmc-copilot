"use client";

import { Download, FileArchive, Plus, Save, Search, ShieldCheck, Trash2, Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, Control, EvidenceItem, EvidenceRequest, EvidenceRequestDashboard } from "@/lib/api";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

const emptyDashboard: EvidenceRequestDashboard = {
  total: 0,
  draft: 0,
  sent: 0,
  submitted: 0,
  accepted: 0,
  rejected: 0,
  overdue: 0,
  rows: [],
};

const emptyRequest: Partial<EvidenceRequest> = {
  control_id: "",
  objective_label: "",
  request_title: "",
  evidence_needed: "",
  requested_from: "Evidence Owner",
  due_date: "",
  priority: "Medium",
  status: "Draft",
  source_type: "Manual",
  source_id: "",
  notes: "",
};

function statusClass(status: string) {
  if (status === "Accepted") return "bg-emerald-50 text-emerald-700";
  if (status === "Submitted") return "bg-blue-50 text-blue-700";
  if (status === "Rejected") return "bg-red-50 text-red-700";
  if (status === "Sent") return "bg-amber-50 text-amber-700";
  return "bg-slate-100 text-slate-700";
}

export default function EvidenceRequestsPage() {
  const [dashboard, setDashboard] = useState<EvidenceRequestDashboard>(emptyDashboard);
  const [controls, setControls] = useState<Control[]>([]);
  const [linkedEvidence, setLinkedEvidence] = useState<EvidenceItem[]>([]);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [controlFilter, setControlFilter] = useState("");
  const [ownerFilter, setOwnerFilter] = useState("");
  const [activeId, setActiveId] = useState<number | null>(null);
  const [draft, setDraft] = useState<Partial<EvidenceRequest>>(emptyRequest);
  const [status, setStatus] = useState("Loading evidence requests...");

  async function refresh(preferredId?: number | null) {
    const data = await api.evidenceRequests(query, statusFilter, controlFilter, ownerFilter);
    setDashboard(data);
    const param = typeof window !== "undefined" ? Number(new URLSearchParams(window.location.search).get("request") || 0) : 0;
    const nextId = preferredId !== undefined ? preferredId : activeId || param || data.rows[0]?.id || null;
    setActiveId(nextId);
    const selected = data.rows.find((row) => row.id === nextId) ?? data.rows[0];
    setDraft(selected ?? emptyRequest);
    setStatus("Ready");
  }

  useEffect(() => {
    api.controls().then(setControls).catch(() => undefined);
    refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => refresh().catch(() => setStatus("Start the FastAPI backend on port 8000.")), 250);
    return () => window.clearTimeout(timer);
  }, [query, statusFilter, controlFilter, ownerFilter]);

  useEffect(() => {
    if (!draft.id) {
      setLinkedEvidence([]);
      return;
    }
    api.evidence("", draft.control_id ?? "", "", "", undefined, draft.id).then(setLinkedEvidence).catch(() => setLinkedEvidence([]));
  }, [draft.id, draft.control_id]);

  const families = useMemo(() => Array.from(new Set(controls.map((control) => control.family))).sort(), [controls]);

  async function choose(request: EvidenceRequest) {
    setActiveId(request.id);
    setDraft(request);
  }

  async function save() {
    if (!draft.request_title || !draft.evidence_needed) return;
    setStatus("Saving evidence request...");
    const saved = await api.saveEvidenceRequest(draft);
    await refresh(saved.id);
    setStatus(`Saved ${saved.request_title}.`);
  }

  async function remove() {
    if (!draft.id || !window.confirm(`Remove ${draft.request_title}?`)) return;
    await api.deleteEvidenceRequest(draft.id);
    await refresh(null);
  }

  async function upload(file: File | null) {
    if (!file || !draft.id) return;
    setStatus(`Uploading ${file.name} for request ${draft.id}...`);
    const content = await fileToBase64(file);
    const uploaded = await api.uploadEvidence({
      file_name: file.name,
      content_base64: content,
      control_id: draft.control_id || "",
      document_type: "Evidence Request Artifact",
      data_classification: "Public",
      contains_cui: false,
      contains_itar: false,
      contains_pii: false,
      evidence_request_id: draft.id,
      owner: draft.requested_from || "Evidence Owner",
      title: `${draft.control_id || "Evidence"} Request ${draft.id} - ${file.name}`,
    });
    await refresh(draft.id);
    setStatus(`Uploaded ${uploaded.file_name}; request is ready for evidence review.`);
  }

  async function generatePoam() {
    setStatus("Generating evidence requests from open POA&M items...");
    const result = await api.generateEvidenceRequestsFromPoam();
    await refresh();
    setStatus(`Created ${result.created}; ${result.existing} already existed.`);
  }

  async function generatePackage() {
    setStatus("Generating evidence requests from assessment package warnings...");
    const result = await api.generateEvidenceRequestsFromPackage();
    await refresh();
    setStatus(`Created ${result.created}; ${result.existing} already existed.`);
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Evidence Requests</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium"><ShieldCheck size={16} />Controls</a>
            <a href={api.evidenceRequestRegisterExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium"><Download size={16} />Register</a>
            <a href={api.evidenceRequestOwnerExportUrl(ownerFilter)} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white"><Download size={16} />Owner DOCX</a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-7">
          {[
            ["Total", dashboard.total],
            ["Draft", dashboard.draft],
            ["Sent", dashboard.sent],
            ["Submitted", dashboard.submitted],
            ["Accepted", dashboard.accepted],
            ["Rejected", dashboard.rejected],
            ["Overdue", dashboard.overdue],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500"><FileArchive size={14} />{label}</div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <section className="mt-5 grid gap-5 lg:grid-cols-[1fr_430px]">
          <div className="rounded-md border border-border bg-white p-4">
            <div className="grid gap-3 lg:grid-cols-[1fr_150px_170px_170px]">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search requests" />
              </div>
              <select className="h-10 rounded-md border border-border px-3 text-sm" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">All statuses</option>
                <option>Draft</option><option>Sent</option><option>Submitted</option><option>Accepted</option><option>Rejected</option>
              </select>
              <input className="h-10 rounded-md border border-border px-3 text-sm" value={controlFilter} onChange={(event) => setControlFilter(event.target.value)} placeholder="Control" />
              <input className="h-10 rounded-md border border-border px-3 text-sm" value={ownerFilter} onChange={(event) => setOwnerFilter(event.target.value)} placeholder="Owner" />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button onClick={() => { setActiveId(null); setDraft(emptyRequest); }} className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm"><Plus size={15} />New</button>
              <button onClick={generatePoam} className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm">From POA&M</button>
              <button onClick={generatePackage} className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm">From Package Warnings</button>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[980px] text-left text-sm">
                <thead className="border-b border-border text-xs uppercase text-slate-500">
                  <tr><th className="py-2">Request</th><th className="py-2">Control</th><th className="py-2">Owner</th><th className="py-2">Due</th><th className="py-2">Priority</th><th className="py-2">Status</th><th className="py-2">Evidence</th></tr>
                </thead>
                <tbody>
                  {dashboard.rows.map((row) => (
                    <tr key={row.id} onClick={() => choose(row)} className={`cursor-pointer border-b border-border align-top ${row.id === activeId ? "bg-slate-50" : ""}`}>
                      <td className="py-3"><div className="font-medium">{row.request_title}</div><div className="text-xs text-slate-500">{row.evidence_needed.slice(0, 120)}</div></td>
                      <td className="py-3">{row.control_id || "-"}</td>
                      <td className="py-3">{row.requested_from}</td>
                      <td className="py-3">{row.due_date || "-"}</td>
                      <td className="py-3">{row.priority}</td>
                      <td className="py-3"><span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(row.status)}`}>{row.status}</span></td>
                      <td className="py-3">{row.accepted_evidence_count}/{row.linked_evidence_count}</td>
                    </tr>
                  ))}
                  {!dashboard.rows.length && <tr><td colSpan={7} className="py-5 text-slate-600">No evidence requests match the current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>

          <aside className="rounded-md border border-border bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold">{draft.id ? `Request ${draft.id}` : "New Request"}</h2>
                <p className="text-sm text-slate-600">{draft.source_type || "Manual"}</p>
              </div>
              {draft.status && <span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(draft.status)}`}>{draft.status}</span>}
            </div>

            <div className="mt-4 grid gap-3">
              <input className="h-10 rounded-md border border-border px-3 text-sm" value={draft.request_title ?? ""} onChange={(event) => setDraft({ ...draft, request_title: event.target.value })} placeholder="Request title" />
              <select className="h-10 rounded-md border border-border px-3 text-sm" value={draft.control_id ?? ""} onChange={(event) => setDraft({ ...draft, control_id: event.target.value })}>
                <option value="">Select control</option>
                {families.map((family) => <option disabled key={family}>{family}</option>)}
                {controls.map((control) => <option key={control.control_id} value={control.control_id}>{control.control_id} - {control.title}</option>)}
              </select>
              <input className="h-10 rounded-md border border-border px-3 text-sm" value={draft.objective_label ?? ""} onChange={(event) => setDraft({ ...draft, objective_label: event.target.value })} placeholder="Objective label" />
              <textarea className="min-h-24 rounded-md border border-border px-3 py-2 text-sm" value={draft.evidence_needed ?? ""} onChange={(event) => setDraft({ ...draft, evidence_needed: event.target.value })} placeholder="Evidence needed" />
              <input className="h-10 rounded-md border border-border px-3 text-sm" value={draft.requested_from ?? ""} onChange={(event) => setDraft({ ...draft, requested_from: event.target.value })} placeholder="Requested from" />
              <div className="grid grid-cols-3 gap-3">
                <input type="date" className="h-10 rounded-md border border-border px-3 text-sm" value={draft.due_date ?? ""} onChange={(event) => setDraft({ ...draft, due_date: event.target.value })} />
                <select className="h-10 rounded-md border border-border px-3 text-sm" value={draft.priority ?? "Medium"} onChange={(event) => setDraft({ ...draft, priority: event.target.value })}>
                  <option>High</option><option>Medium</option><option>Low</option>
                </select>
                <select className="h-10 rounded-md border border-border px-3 text-sm" value={draft.status ?? "Draft"} onChange={(event) => setDraft({ ...draft, status: event.target.value })}>
                  <option>Draft</option><option>Sent</option><option>Submitted</option><option>Accepted</option><option>Rejected</option>
                </select>
              </div>
              <textarea className="min-h-20 rounded-md border border-border px-3 py-2 text-sm" value={draft.notes ?? ""} onChange={(event) => setDraft({ ...draft, notes: event.target.value })} placeholder="Notes" />
              <div className="flex flex-wrap gap-2">
                <button onClick={save} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white"><Save size={16} />Save</button>
                {draft.id && <button onClick={remove} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium"><Trash2 size={16} />Remove</button>}
              </div>
            </div>

            {draft.id && (
              <section className="mt-5 border-t border-border pt-4">
                <h3 className="text-sm font-semibold">Linked Evidence</h3>
                <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
                  Azure Commercial upload rule: do not upload CUI, ITAR, export-controlled data, classified data, or sensitive government contract information.
                </div>
                <label className="mt-3 inline-flex h-10 cursor-pointer items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                  <Upload size={16} />
                  Upload Evidence
                  <input className="hidden" type="file" onChange={(event) => upload(event.target.files?.[0] ?? null)} />
                </label>
                <div className="mt-3 space-y-2">
                  {linkedEvidence.map((item) => (
                    <div key={item.id} className="rounded-md bg-slate-50 p-3 text-sm">
                      <div className="font-medium">{item.file_name}</div>
                      <div className="text-slate-600">{item.review_status} / {item.drift_state}</div>
                    </div>
                  ))}
                  {!linkedEvidence.length && <div className="rounded-md bg-slate-50 p-3 text-sm text-slate-600">No evidence uploaded for this request yet.</div>}
                </div>
              </section>
            )}
          </aside>
        </section>
      </section>
    </main>
  );
}
