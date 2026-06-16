"use client";

import { Download, FileArchive, FileSpreadsheet, Search, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, AssessmentPackageSummary, Control } from "@/lib/api";

const emptySummary: AssessmentPackageSummary = {
  scope: "All Level 2 controls",
  total_controls: 0,
  ready_controls: 0,
  warning_controls: 0,
  missing_implementation: 0,
  missing_policy: 0,
  missing_procedure: 0,
  controls_without_accepted_evidence: 0,
  open_poam_items: 0,
  stale_evidence: 0,
  completeness_score: 0,
  controls: [],
};

function readinessClass(score: number) {
  if (score >= 90) return "bg-emerald-50 text-emerald-700";
  if (score >= 70) return "bg-blue-50 text-blue-700";
  if (score >= 45) return "bg-amber-50 text-amber-700";
  return "bg-red-50 text-red-700";
}

export default function AssessmentPackagePage() {
  const [controls, setControls] = useState<Control[]>([]);
  const [summary, setSummary] = useState<AssessmentPackageSummary>(emptySummary);
  const [scope, setScope] = useState("all");
  const [scopeValue, setScopeValue] = useState("");
  const [query, setQuery] = useState("");
  const [includeDocuments, setIncludeDocuments] = useState(true);
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [includePoam, setIncludePoam] = useState(true);
  const [includeWarnings, setIncludeWarnings] = useState(true);
  const [status, setStatus] = useState("Loading assessment package...");

  useEffect(() => {
    api.controls().then(setControls).catch(() => undefined);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      api.assessmentPackage(scope, scopeValue, query)
        .then((data) => {
          setSummary(data);
          setStatus("Ready");
        })
        .catch(() => setStatus("Start the FastAPI backend on port 8000."));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [scope, scopeValue, query]);

  const families = useMemo(() => Array.from(new Set(controls.map((control) => control.family))).sort(), [controls]);
  const controlOptions = useMemo(() => controls.map((control) => `${control.control_id} - ${control.title}`), [controls]);
  const selectedValue = scope === "all" ? "" : scopeValue;

  function changeScope(nextScope: string) {
    setScope(nextScope);
    setScopeValue("");
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Assessment Package</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href={api.assessmentPackageMatrixExportUrl(scope, selectedValue)} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileSpreadsheet size={16} />
              Matrix
            </a>
            <a href={api.assessmentPackageExportUrl("docx", scope, selectedValue, includeDocuments, includeEvidence, includePoam, includeWarnings)} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <Download size={16} />
              DOCX
            </a>
            <a href={api.assessmentPackageExportUrl("pdf", scope, selectedValue, includeDocuments, includeEvidence, includePoam, includeWarnings)} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <FileArchive size={16} />
              PDF
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {[
            ["Completeness", `${summary.completeness_score}%`],
            ["Controls", summary.total_controls],
            ["Ready", summary.ready_controls],
            ["Warnings", summary.warning_controls],
            ["Open POA&M", summary.open_poam_items],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500">
                <FileArchive size={14} />
                {label}
              </div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <section className="mt-5 rounded-md border border-border bg-white p-4">
          <div className="grid gap-3 lg:grid-cols-[150px_280px_1fr]">
            <select className="h-10 rounded-md border border-border px-3 text-sm" value={scope} onChange={(event) => changeScope(event.target.value)}>
              <option value="all">All Controls</option>
              <option value="family">Family</option>
              <option value="control">Control</option>
            </select>
            {scope === "family" && (
              <select className="h-10 rounded-md border border-border px-3 text-sm" value={scopeValue} onChange={(event) => setScopeValue(event.target.value)}>
                <option value="">Select family</option>
                {families.map((item) => <option key={item}>{item}</option>)}
              </select>
            )}
            {scope === "control" && (
              <select className="h-10 rounded-md border border-border px-3 text-sm" value={scopeValue} onChange={(event) => setScopeValue(event.target.value)}>
                <option value="">Select control</option>
                {controlOptions.map((item) => {
                  const controlId = item.split(" - ")[0];
                  return <option key={controlId} value={controlId}>{item}</option>;
                })}
              </select>
            )}
            {scope === "all" && <div className="h-10 rounded-md border border-border bg-slate-50 px-3 py-2 text-sm text-slate-600">All Level 2 controls</div>}
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
              <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search package controls" />
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            {[
              ["Documents", includeDocuments, setIncludeDocuments],
              ["Evidence", includeEvidence, setIncludeEvidence],
              ["POA&M", includePoam, setIncludePoam],
              ["Warnings", includeWarnings, setIncludeWarnings],
            ].map(([label, checked, setter]) => (
              <label key={String(label)} className="inline-flex items-center gap-2">
                <input type="checkbox" checked={Boolean(checked)} onChange={(event) => (setter as (value: boolean) => void)(event.target.checked)} />
                {String(label)}
              </label>
            ))}
          </div>
        </section>

        <section className="mt-5 rounded-md border border-border bg-white p-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {[
              ["Missing Impl.", summary.missing_implementation],
              ["Missing Policy", summary.missing_policy],
              ["Missing Procedure", summary.missing_procedure],
              ["No Accepted Evidence", summary.controls_without_accepted_evidence],
              ["Stale Evidence", summary.stale_evidence],
            ].map(([label, value]) => (
              <div key={label} className="rounded-md border border-border bg-slate-50 p-3">
                <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
                <div className="mt-1 text-xl font-semibold">{value}</div>
              </div>
            ))}
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[1180px] text-left text-sm">
              <thead className="border-b border-border text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-2">Control</th>
                  <th className="py-2">Family</th>
                  <th className="py-2">Ready</th>
                  <th className="py-2">Impl.</th>
                  <th className="py-2">Policy</th>
                  <th className="py-2">Procedure</th>
                  <th className="py-2">Evidence</th>
                  <th className="py-2">POA&M</th>
                  <th className="py-2">Warnings</th>
                  <th className="py-2">Open</th>
                </tr>
              </thead>
              <tbody>
                {summary.controls.map((row) => (
                  <tr key={row.control_id} className="border-b border-border align-top">
                    <td className="py-3">
                      <div className="font-medium">{row.control_id}</div>
                      <div className="text-xs text-slate-500">{row.title}</div>
                    </td>
                    <td className="py-3">{row.family}</td>
                    <td className="py-3"><span className={`rounded px-2 py-1 text-xs font-medium ${readinessClass(row.readiness_score)}`}>{row.readiness_score}%</span></td>
                    <td className="py-3">{row.implementation_status}</td>
                    <td className="py-3">{row.policy_status}</td>
                    <td className="py-3">{row.procedure_status}</td>
                    <td className="py-3">{row.accepted_evidence}/{row.evidence_total}</td>
                    <td className="py-3">{row.open_poam}</td>
                    <td className="py-3 text-slate-700">{row.warnings.length ? row.warnings.join("; ") : "Ready"}</td>
                    <td className="py-3">
                      <a href={`/controls/${row.control_id}/graph`} className="text-sm font-medium text-primary">Graph</a>
                    </td>
                  </tr>
                ))}
                {!summary.controls.length && (
                  <tr>
                    <td className="py-5 text-slate-600" colSpan={10}>No controls match the current package scope.</td>
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
