"use client";

import { Download, FileCheck2, FileText, GitBranch, Save, Search, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, ControlReview, ControlReviewDashboard } from "@/lib/api";

const emptyDashboard: ControlReviewDashboard = {
  total_controls: 0,
  not_started: 0,
  in_review: 0,
  approved: 0,
  rejected: 0,
  due_soon: 0,
  overdue: 0,
  rows: [],
};

function today() {
  return new Date().toISOString().slice(0, 10);
}

function statusClass(status: string) {
  if (status === "Approved") return "bg-emerald-50 text-emerald-700";
  if (status === "In Review") return "bg-blue-50 text-blue-700";
  if (status === "Rejected") return "bg-red-50 text-red-700";
  return "bg-slate-100 text-slate-700";
}

function nextYear() {
  const date = new Date();
  date.setFullYear(date.getFullYear() + 1);
  return date.toISOString().slice(0, 10);
}

export default function ReviewsPage() {
  const [dashboard, setDashboard] = useState<ControlReviewDashboard>(emptyDashboard);
  const [query, setQuery] = useState("");
  const [family, setFamily] = useState("");
  const [reviewStatus, setReviewStatus] = useState("");
  const [activeId, setActiveId] = useState("");
  const [draft, setDraft] = useState<ControlReview | null>(null);
  const [status, setStatus] = useState("Loading control reviews...");

  async function refresh(preferredControl?: string) {
    const data = await api.controlReviews(query, family, reviewStatus);
    setDashboard(data);
    const param = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("control") : "";
    const nextActive = preferredControl || activeId || param || data.rows[0]?.control_id || "";
    setActiveId(nextActive);
    const selected = data.rows.find((row) => row.control_id === nextActive) ?? data.rows[0] ?? null;
    setDraft(selected);
    setStatus("Ready");
  }

  useEffect(() => {
    refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => refresh().catch(() => setStatus("Start the FastAPI backend on port 8000.")), 250);
    return () => window.clearTimeout(timer);
  }, [query, family, reviewStatus]);

  const families = useMemo(() => Array.from(new Set(dashboard.rows.map((row) => row.family))).sort(), [dashboard.rows]);
  const active = draft;

  async function choose(controlId: string) {
    setActiveId(controlId);
    const row = await api.controlReview(controlId);
    setDraft(row);
  }

  async function save(nextStatus?: string) {
    if (!active) return;
    const statusValue = nextStatus || active.review_status;
    setStatus(`Saving ${active.control_id} review...`);
    const saved = await api.saveControlReview(active.control_id, {
      review_status: statusValue,
      reviewer: active.reviewer,
      approver: active.approver,
      review_notes: active.review_notes,
      signoff_date: statusValue === "Approved" ? active.signoff_date || today() : active.signoff_date,
      next_review_date: active.next_review_date || (statusValue === "Approved" ? nextYear() : ""),
    });
    setDraft(saved);
    await refresh(saved.control_id);
    setStatus(`${saved.control_id} review saved as ${saved.review_status}.`);
  }

  function patch(patchValue: Partial<ControlReview>) {
    if (!active) return;
    setDraft({ ...active, ...patchValue });
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Control Review & Sign-Off</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href={api.controlReviewRegisterExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <Download size={16} />
              Register
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          {[
            ["Total", dashboard.total_controls],
            ["Not Started", dashboard.not_started],
            ["In Review", dashboard.in_review],
            ["Approved", dashboard.approved],
            ["Rejected", dashboard.rejected],
            ["Overdue", dashboard.overdue],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500"><FileCheck2 size={14} />{label}</div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <section className="mt-5 grid gap-5 lg:grid-cols-[1fr_430px]">
          <div className="rounded-md border border-border bg-white p-4">
            <div className="grid gap-3 lg:grid-cols-[1fr_220px_170px]">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search controls, reviewers, notes" />
              </div>
              <select className="h-10 rounded-md border border-border px-3 text-sm" value={family} onChange={(event) => setFamily(event.target.value)}>
                <option value="">All families</option>
                {families.map((item) => <option key={item}>{item}</option>)}
              </select>
              <select className="h-10 rounded-md border border-border px-3 text-sm" value={reviewStatus} onChange={(event) => setReviewStatus(event.target.value)}>
                <option value="">All statuses</option>
                <option>Not Started</option>
                <option>In Review</option>
                <option>Approved</option>
                <option>Rejected</option>
              </select>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[980px] text-left text-sm">
                <thead className="border-b border-border text-xs uppercase text-slate-500">
                  <tr>
                    <th className="py-2">Control</th>
                    <th className="py-2">Family</th>
                    <th className="py-2">Status</th>
                    <th className="py-2">Reviewer</th>
                    <th className="py-2">Approver</th>
                    <th className="py-2">Readiness</th>
                    <th className="py-2">Warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.rows.map((row) => (
                    <tr key={row.control_id} onClick={() => choose(row.control_id)} className={`cursor-pointer border-b border-border align-top ${row.control_id === activeId ? "bg-slate-50" : ""}`}>
                      <td className="py-3">
                        <div className="font-medium">{row.control_id}</div>
                        <div className="text-xs text-slate-500">{row.control_title}</div>
                      </td>
                      <td className="py-3">{row.family}</td>
                      <td className="py-3"><span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(row.review_status)}`}>{row.review_status}</span></td>
                      <td className="py-3">{row.reviewer || "-"}</td>
                      <td className="py-3">{row.approver || "-"}</td>
                      <td className="py-3">{row.package_readiness_score}%</td>
                      <td className="py-3">{row.warnings.length ? row.warnings.join("; ") : "Ready"}</td>
                    </tr>
                  ))}
                  {!dashboard.rows.length && <tr><td colSpan={7} className="py-5 text-slate-600">No reviews match the current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>

          <aside className="rounded-md border border-border bg-white p-4">
            {active ? (
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold">{active.control_id}</h2>
                    <p className="text-sm text-slate-600">{active.control_title}</p>
                  </div>
                  <span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(active.review_status)}`}>{active.review_status}</span>
                </div>

                <div className="mt-4 grid gap-3">
                  <label className="block">
                    <span className="text-xs font-medium text-slate-600">Review status</span>
                    <select className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.review_status} onChange={(event) => patch({ review_status: event.target.value })}>
                      <option>Not Started</option>
                      <option>In Review</option>
                      <option>Approved</option>
                      <option>Rejected</option>
                    </select>
                  </label>
                  <label className="block">
                    <span className="text-xs font-medium text-slate-600">Reviewer</span>
                    <input className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.reviewer} onChange={(event) => patch({ reviewer: event.target.value })} />
                  </label>
                  <label className="block">
                    <span className="text-xs font-medium text-slate-600">Approver</span>
                    <input className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.approver} onChange={(event) => patch({ approver: event.target.value })} />
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="block">
                      <span className="text-xs font-medium text-slate-600">Sign-off date</span>
                      <input type="date" className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.signoff_date} onChange={(event) => patch({ signoff_date: event.target.value })} />
                    </label>
                    <label className="block">
                      <span className="text-xs font-medium text-slate-600">Next review</span>
                      <input type="date" className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm" value={active.next_review_date} onChange={(event) => patch({ next_review_date: event.target.value })} />
                    </label>
                  </div>
                  <label className="block">
                    <span className="text-xs font-medium text-slate-600">Review notes</span>
                    <textarea className="mt-1 min-h-28 w-full rounded-md border border-border px-3 py-2 text-sm" value={active.review_notes} onChange={(event) => patch({ review_notes: event.target.value })} />
                  </label>
                </div>

                <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm">
                  <div className="font-medium">Package readiness: {active.package_readiness_score}%</div>
                  <div className="mt-2 text-slate-700">{active.warnings.length ? active.warnings.join("; ") : "No package warnings."}</div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <button onClick={() => save()} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                    <Save size={16} />
                    Save
                  </button>
                  <button onClick={() => save("Approved")} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                    <FileCheck2 size={16} />
                    Approve
                  </button>
                  <button onClick={() => save("Rejected")} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                    Reject
                  </button>
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  <a href={`/controls/${active.control_id}/graph`} className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm">
                    <GitBranch size={15} />
                    Graph
                  </a>
                  <a href={`/assessment-package?scope=control&value=${active.control_id}`} className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm">
                    <FileText size={15} />
                    Package
                  </a>
                  <a href={api.controlReviewMemoExportUrl(active.control_id)} className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm">
                    <Download size={15} />
                    Memo
                  </a>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-600">Select a control to review.</p>
            )}
          </aside>
        </section>
      </section>
    </main>
  );
}
