"use client";

import { Download, History, Search, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, AuditLogItem } from "@/lib/api";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [query, setQuery] = useState("");
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [controlId, setControlId] = useState("");
  const [userName, setUserName] = useState("");
  const [status, setStatus] = useState("Loading audit history...");

  async function refresh() {
    setLogs(await api.auditLogs(query, action, entityType, "", controlId, userName));
    setStatus("Ready");
  }

  useEffect(() => {
    refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => refresh().catch(() => setStatus("Start the FastAPI backend on port 8000.")), 250);
    return () => window.clearTimeout(timer);
  }, [query, action, entityType, controlId, userName]);

  const actions = useMemo(() => Array.from(new Set(logs.map((item) => item.action))).sort(), [logs]);
  const entityTypes = useMemo(() => Array.from(new Set(logs.map((item) => item.entity_type))).sort(), [logs]);

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Audit Log</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href={api.auditExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <Download size={16} />
              Export XLSX
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 md:grid-cols-4">
          {[
            ["Activities", logs.length],
            ["Users", new Set(logs.map((item) => item.user_name)).size],
            ["Controls", new Set(logs.map((item) => item.control_id).filter(Boolean)).size],
            ["Entity Types", new Set(logs.map((item) => item.entity_type)).size],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500"><History size={14} />{label}</div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <section className="mt-5 rounded-md border border-border bg-white p-4">
          <div className="grid gap-3 lg:grid-cols-[1fr_210px_190px_180px_190px]">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
              <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search activity details" />
            </div>
            <select className="h-10 rounded-md border border-border px-3 text-sm" value={action} onChange={(event) => setAction(event.target.value)}>
              <option value="">All actions</option>
              {actions.map((item) => <option key={item}>{item}</option>)}
            </select>
            <select className="h-10 rounded-md border border-border px-3 text-sm" value={entityType} onChange={(event) => setEntityType(event.target.value)}>
              <option value="">All entities</option>
              {entityTypes.map((item) => <option key={item}>{item}</option>)}
            </select>
            <input className="h-10 rounded-md border border-border px-3 text-sm" value={controlId} onChange={(event) => setControlId(event.target.value)} placeholder="Control ID" />
            <input className="h-10 rounded-md border border-border px-3 text-sm" value={userName} onChange={(event) => setUserName(event.target.value)} placeholder="User" />
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[1000px] text-left text-sm">
              <thead className="border-b border-border text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-2">Timestamp</th>
                  <th className="py-2">User</th>
                  <th className="py-2">Action</th>
                  <th className="py-2">Entity</th>
                  <th className="py-2">Control</th>
                  <th className="py-2">Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((item) => (
                  <tr key={item.id} className="border-b border-border align-top">
                    <td className="py-3 text-xs text-slate-600">{new Date(item.created_at).toLocaleString()}</td>
                    <td className="py-3">{item.user_name}</td>
                    <td className="py-3 font-medium">{item.action}</td>
                    <td className="py-3">{item.entity_type} #{item.entity_id}</td>
                    <td className="py-3">{item.control_id || "-"}</td>
                    <td className="py-3 text-slate-700">{item.details}</td>
                  </tr>
                ))}
                {!logs.length && <tr><td colSpan={6} className="py-5 text-slate-600">No audit activity matches the filters.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}
