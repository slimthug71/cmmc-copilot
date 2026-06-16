"use client";

import { CalendarDays, Download, Search, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, ComplianceCalendar } from "@/lib/api";

const emptyCalendar: ComplianceCalendar = {
  overdue: 0,
  due_soon: 0,
  upcoming: 0,
  unscheduled: 0,
  completed: 0,
  tasks: [],
};

function statusClass(status: string) {
  if (status === "Overdue") return "bg-red-50 text-red-700";
  if (status === "Due Soon") return "bg-amber-50 text-amber-700";
  if (status === "Upcoming") return "bg-blue-50 text-blue-700";
  if (status === "Completed") return "bg-emerald-50 text-emerald-700";
  return "bg-slate-100 text-slate-700";
}

export default function CalendarPage() {
  const [calendar, setCalendar] = useState<ComplianceCalendar>(emptyCalendar);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [ownerFilter, setOwnerFilter] = useState("");
  const [controlFilter, setControlFilter] = useState("");
  const [status, setStatus] = useState("Loading compliance work queue...");

  async function refresh() {
    setCalendar(await api.calendar(query, statusFilter, typeFilter, ownerFilter, controlFilter));
    setStatus("Ready");
  }

  useEffect(() => {
    refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => refresh().catch(() => setStatus("Start the FastAPI backend on port 8000.")), 250);
    return () => window.clearTimeout(timer);
  }, [query, statusFilter, typeFilter, ownerFilter, controlFilter]);

  const taskTypes = useMemo(() => Array.from(new Set(calendar.tasks.map((task) => task.task_type))).sort(), [calendar.tasks]);

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Compliance Calendar</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href={api.calendarExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <Download size={16} />
              Export XLSX
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 md:grid-cols-5">
          {[
            ["Overdue", calendar.overdue],
            ["Due Soon", calendar.due_soon],
            ["Upcoming", calendar.upcoming],
            ["Unscheduled", calendar.unscheduled],
            ["Completed", calendar.completed],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500"><CalendarDays size={14} />{label}</div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <section className="mt-5 rounded-md border border-border bg-white p-4">
          <div className="grid gap-3 lg:grid-cols-[1fr_170px_230px_190px_180px]">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
              <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search tasks" />
            </div>
            <select className="h-10 rounded-md border border-border px-3 text-sm" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">All statuses</option>
              <option>Overdue</option>
              <option>Due Soon</option>
              <option>Upcoming</option>
              <option>Unscheduled</option>
              <option>Completed</option>
            </select>
            <select className="h-10 rounded-md border border-border px-3 text-sm" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
              <option value="">All task types</option>
              {taskTypes.map((item) => <option key={item}>{item}</option>)}
            </select>
            <input className="h-10 rounded-md border border-border px-3 text-sm" value={ownerFilter} onChange={(event) => setOwnerFilter(event.target.value)} placeholder="Owner" />
            <input className="h-10 rounded-md border border-border px-3 text-sm" value={controlFilter} onChange={(event) => setControlFilter(event.target.value)} placeholder="Control ID" />
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[1080px] text-left text-sm">
              <thead className="border-b border-border text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-2">Status</th>
                  <th className="py-2">Due</th>
                  <th className="py-2">Task</th>
                  <th className="py-2">Owner</th>
                  <th className="py-2">Control</th>
                  <th className="py-2">Details</th>
                  <th className="py-2">Open</th>
                </tr>
              </thead>
              <tbody>
                {calendar.tasks.map((task) => (
                  <tr key={task.id} className="border-b border-border align-top">
                    <td className="py-3"><span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(task.status)}`}>{task.status}</span></td>
                    <td className="py-3">{task.due_date || "Not scheduled"}</td>
                    <td className="py-3"><div className="font-medium">{task.title}</div><div className="text-xs text-slate-500">{task.task_type}</div></td>
                    <td className="py-3">{task.owner}</td>
                    <td className="py-3">{task.control_id || "-"}</td>
                    <td className="py-3 text-slate-700">{task.detail}</td>
                    <td className="py-3"><a href={task.link} className="text-sm font-medium text-primary">Open</a></td>
                  </tr>
                ))}
                {!calendar.tasks.length && <tr><td colSpan={7} className="py-5 text-slate-600">No tasks match the current filters.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}
