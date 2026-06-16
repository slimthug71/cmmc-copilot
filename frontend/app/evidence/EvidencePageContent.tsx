"use client";

import { Download, FileArchive, Gauge, RefreshCw, Search, ShieldCheck, Trash2, Upload } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, AuditLogItem, Control, ControlCoverage, EvidenceDashboard, EvidenceItem } from "@/lib/api";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

const emptyDashboard: EvidenceDashboard = {
  evidence_uploaded: 0,
  controls_with_evidence: 0,
  total_controls: 110,
  objectives_with_evidence: 0,
  total_objectives: 320,
  objective_coverage_score: 0,
  average_coverage: 0,
  missing_evidence: 0,
  strong_evidence: 0,
  weak_evidence: 0,
  uploaded_evidence: 0,
  under_review_evidence: 0,
  accepted_evidence: 0,
  needs_replacement_evidence: 0,
  rejected_evidence: 0,
  stale_evidence: 0,
  objectives_at_risk: 0,
  controls_at_risk: 0,
  assessment_readiness_score: 0,
};

export default function EvidencePageContent() {
  const searchParams = useSearchParams();
  const [dashboard, setDashboard] = useState<EvidenceDashboard>(emptyDashboard);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [controls, setControls] = useState<Control[]>([]);
  const [coverage, setCoverage] = useState<ControlCoverage[]>([]);
  const [activeEvidenceId, setActiveEvidenceId] = useState<number | null>(null);
  const [selectedControlId, setSelectedControlId] = useState("AC.L2-3.1.9");
  const [controlSearch, setControlSearch] = useState("");
  const [query, setQuery] = useState("");
  const [controlFilter, setControlFilter] = useState("");
  const [reviewFilter, setReviewFilter] = useState("");
  const [driftFilter, setDriftFilter] = useState("");
  const [status, setStatus] = useState("Ready");
  const [reviewer, setReviewer] = useState("Compliance Reviewer");
  const [reviewNotes, setReviewNotes] = useState("");
  const [activity, setActivity] = useState<AuditLogItem[]>([]);
  const [uploadDocumentType, setUploadDocumentType] = useState("Evidence Artifact");
  const [uploadClassification, setUploadClassification] = useState("Public");
  const [containsCui, setContainsCui] = useState(false);
  const [containsItar, setContainsItar] = useState(false);
  const [containsPii, setContainsPii] = useState(false);

  function uploadMetadata() {
    return {
      document_type: uploadDocumentType,
      data_classification: uploadClassification,
      contains_cui: containsCui,
      contains_itar: containsItar,
      contains_pii: containsPii,
    };
  }

  function uploadAllowed() {
    if (!uploadDocumentType || !uploadClassification) {
      setStatus("Document Type and Data Classification are required before upload.");
      return false;
    }
    if (containsCui || containsItar) {
      setStatus("Upload blocked. Azure Commercial is not approved for CUI or ITAR.");
      return false;
    }
    return true;
  }

  async function refresh(q = query, control = controlFilter, preferredActiveId?: number | null) {
    const [dash, library, controlCoverage] = await Promise.all([
      api.evidenceDashboard(),
      api.evidence(q, control, reviewFilter, driftFilter),
      api.evidenceCoverage(),
    ]);
    setDashboard(dash);
    setEvidence(library);
    setCoverage(controlCoverage);
    setActiveEvidenceId((current) => {
      if (preferredActiveId !== undefined) return preferredActiveId;
      return library.some((item) => item.id === current) ? current : library[0]?.id ?? null;
    });
  }

  useEffect(() => {
    const initialControl = searchParams?.get("control") ?? "";
    if (initialControl) setControlFilter(initialControl);
    refresh(query, initialControl || controlFilter).catch(() => setStatus("Start the FastAPI backend on port 8000."));
    api.controls().then((items) => {
      setControls(items);
      setSelectedControlId(items.find((item) => item.control_id === "AC.L2-3.1.9")?.control_id ?? items[0]?.control_id ?? "AC.L2-3.1.1");
    }).catch(() => undefined);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh(query, controlFilter).catch(() => setStatus("Start the FastAPI backend on port 8000."));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query, controlFilter, reviewFilter, driftFilter]);

  async function uploadEvidence(file: File | null) {
    if (!file) return;
    if (!uploadAllowed()) return;
    setStatus(`Analyzing ${file.name} for ${selectedControlId}...`);
    const content = await fileToBase64(file);
    const uploaded = await api.uploadEvidence({ file_name: file.name, content_base64: content, control_id: selectedControlId, ...uploadMetadata() });
    await refresh(query, controlFilter, uploaded.id);
    setStatus(`Mapped ${uploaded.file_name} to ${selectedControlId}.`);
  }

  async function replaceEvidence(file: File | null) {
    if (!file || !activeEvidence) return;
    if (!uploadAllowed()) return;
    setStatus(`Replacing ${activeEvidence.file_name}...`);
    const content = await fileToBase64(file);
    const replaced = await api.replaceEvidence(activeEvidence.id, {
      file_name: file.name,
      content_base64: content,
      ...uploadMetadata(),
      title: activeEvidence.title,
      owner: activeEvidence.owner,
      control_id: selectedControlId || activeEvidence.analyses[0]?.control_id,
    });
    await refresh(query, controlFilter, replaced.id);
    setStatus(`Replaced ${replaced.file_name} and remapped it to ${selectedControlId || replaced.analyses[0]?.control_id}.`);
  }

  async function removeEvidence() {
    if (!activeEvidence) return;
    if (!window.confirm(`Remove ${activeEvidence.file_name} and its analysis?`)) return;
    setStatus(`Removing ${activeEvidence.file_name}...`);
    await api.deleteEvidence(activeEvidence.id);
    const remaining = evidence.filter((item) => item.id !== activeEvidence.id);
    await refresh(query, controlFilter, remaining[0]?.id ?? null);
    setStatus(`Removed ${activeEvidence.file_name}.`);
  }

  async function reviewEvidence(reviewStatus: string) {
    if (!activeEvidence) return;
    setStatus(`Marking ${activeEvidence.file_name} as ${reviewStatus}...`);
    const reviewed = await api.reviewEvidence(activeEvidence.id, {
      review_status: reviewStatus,
      reviewer,
      review_notes: reviewNotes || activeEvidence.review_notes,
    });
    await refresh(query, controlFilter, reviewed.id);
    setActivity(await api.auditLogs("", "", "Evidence", String(reviewed.id)));
    setReviewNotes(reviewed.review_notes);
    setStatus(`Marked ${reviewed.file_name} as ${reviewStatus}.`);
  }

  const activeEvidence = useMemo(
    () => evidence.find((item) => item.id === activeEvidenceId) ?? evidence[0],
    [activeEvidenceId, evidence]
  );
  const topCoverage = coverage.filter((item) => item.evidence_count > 0).slice(0, 12);
  const matchingControls = controls
    .filter((control) => `${control.control_id} ${control.title} ${control.family}`.toLowerCase().includes(controlSearch.toLowerCase()))
    .slice(0, 8);
  const selectedControl = controls.find((control) => control.control_id === selectedControlId);

  useEffect(() => {
    setReviewNotes(activeEvidence?.review_notes ?? "");
    if (activeEvidence?.id) {
      api.auditLogs("", "", "Evidence", String(activeEvidence.id)).then(setActivity).catch(() => setActivity([]));
    } else {
      setActivity([]);
    }
  }, [activeEvidence?.id, activeEvidence?.review_notes]);

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Evidence Intelligence</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href={api.evidencePackageExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <Download size={16} />
              Evidence Package
            </a>
            <a href={api.objectiveMatrixExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <Download size={16} />
              Matrix
            </a>
            <a href="/poam" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileArchive size={16} />
              Manage POA&M
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 md:grid-cols-5">
          {[
            ["Readiness", `${dashboard.assessment_readiness_score}%`],
            ["Evidence Uploaded", dashboard.evidence_uploaded],
            ["Controls Covered", `${dashboard.controls_with_evidence}/${dashboard.total_controls}`],
            ["Objectives Covered", `${dashboard.objectives_with_evidence}/${dashboard.total_objectives}`],
            ["Missing Evidence", dashboard.missing_evidence],
            ["Accepted", dashboard.accepted_evidence],
            ["Under Review", dashboard.under_review_evidence],
            ["Needs Replacement", dashboard.needs_replacement_evidence],
            ["Rejected", dashboard.rejected_evidence],
            ["Stale", dashboard.stale_evidence],
            ["Objectives At Risk", dashboard.objectives_at_risk],
            ["Controls At Risk", dashboard.controls_at_risk],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-[360px_1fr]">
          <aside className="space-y-5">
            <div className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Upload Evidence</h2>
              <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
                This Azure Commercial environment is not approved for CUI. Users must not upload CUI, ITAR, export-controlled data, classified data, or sensitive government contract information.
              </div>
              <div className="mt-4 space-y-2">
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">Document Type</span>
                  <input
                    required
                    className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                    value={uploadDocumentType}
                    onChange={(event) => setUploadDocumentType(event.target.value)}
                    placeholder="Evidence Artifact"
                  />
                </label>
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">Data Classification</span>
                  <select
                    required
                    className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                    value={uploadClassification}
                    onChange={(event) => setUploadClassification(event.target.value)}
                  >
                    <option value="Public">Public</option>
                    <option value="Internal">Internal</option>
                    <option value="Confidential">Confidential</option>
                  </select>
                </label>
                <div className="grid gap-2 text-sm">
                  <label className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    Contains CUI?
                    <input type="checkbox" checked={containsCui} onChange={(event) => setContainsCui(event.target.checked)} />
                  </label>
                  <label className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    Contains ITAR?
                    <input type="checkbox" checked={containsItar} onChange={(event) => setContainsItar(event.target.checked)} />
                  </label>
                  <label className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    Contains PII?
                    <input type="checkbox" checked={containsPii} onChange={(event) => setContainsPii(event.target.checked)} />
                  </label>
                </div>
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">Control</span>
                  <div className="relative mt-1">
                    <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                    <input
                      className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm outline-none focus:border-primary"
                      value={controlSearch}
                      onChange={(event) => setControlSearch(event.target.value)}
                      placeholder="Search controls"
                    />
                  </div>
                </label>
                {controlSearch && (
                  <div className="max-h-52 overflow-y-auto rounded-md border border-border bg-white">
                    {matchingControls.map((control) => (
                      <button
                        key={control.control_id}
                        onClick={() => {
                          setSelectedControlId(control.control_id);
                          setControlSearch("");
                        }}
                        className="block w-full border-b border-border px-3 py-2 text-left text-xs hover:bg-muted"
                      >
                        <span className="font-medium">{control.control_id}</span> - {control.title}
                        <span className="block text-slate-500">{control.family}</span>
                      </button>
                    ))}
                    {!matchingControls.length && <div className="px-3 py-2 text-xs text-slate-500">No matching controls.</div>}
                  </div>
                )}
                <select
                  className="h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                  value={selectedControlId}
                  onChange={(event) => setSelectedControlId(event.target.value)}
                >
                  {controls.map((control) => (
                    <option key={control.control_id} value={control.control_id}>
                      {control.control_id} - {control.title}
                    </option>
                  ))}
                </select>
                <div className="rounded-md bg-muted p-3 text-xs leading-5 text-slate-600">
                  Selected: {selectedControl ? `${selectedControl.control_id} - ${selectedControl.title}` : selectedControlId}
                </div>
              </div>
              <label className="mt-4 flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-slate-300 bg-muted px-4 py-6 text-center text-sm text-slate-600">
                <Upload size={22} />
                <span className="mt-2 font-medium">PDF, DOCX, XLSX, CSV, TXT, PNG, JPEG, ZIP</span>
                <input className="sr-only" type="file" onChange={(event) => uploadEvidence(event.target.files?.[0] ?? null)} />
              </label>
            </div>

            <div className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Evidence Library</h2>
              <form
                className="mt-3 flex gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  refresh(query, controlFilter).catch(() => setStatus("Start the FastAPI backend on port 8000."));
                }}
              >
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                  <input
                    className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm outline-none focus:border-primary"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search evidence"
                  />
                </div>
                <button type="submit" className="h-10 rounded-md border border-border bg-white px-3 text-sm font-medium">
                  Search
                </button>
              </form>
              <input
                className="mt-2 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                value={controlFilter}
                onChange={(event) => setControlFilter(event.target.value)}
                placeholder="Filter by control, e.g. AC.L2-3.1.1"
                list="evidence-control-filter-options"
              />
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                <select
                  className="h-10 rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                  value={reviewFilter}
                  onChange={(event) => setReviewFilter(event.target.value)}
                >
                  <option value="">All review statuses</option>
                  <option value="Under Review">Under Review</option>
                  <option value="Accepted">Accepted</option>
                  <option value="Needs Replacement">Needs Replacement</option>
                  <option value="Rejected">Rejected</option>
                </select>
                <select
                  className="h-10 rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                  value={driftFilter}
                  onChange={(event) => setDriftFilter(event.target.value)}
                >
                  <option value="">All drift states</option>
                  <option value="Current">Current</option>
                  <option value="Stale">Stale</option>
                  <option value="Needs Replacement">Needs Replacement</option>
                  <option value="Rejected">Rejected</option>
                  <option value="No Accepted Evidence">No Accepted Evidence</option>
                </select>
              </div>
              <datalist id="evidence-control-filter-options">
                {controls.map((control) => (
                  <option key={control.control_id} value={control.control_id}>
                    {control.title}
                  </option>
                ))}
              </datalist>
              <div className="mt-4 space-y-2">
                {evidence.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveEvidenceId(item.id)}
                    className={`w-full rounded-md border px-3 py-2 text-left text-sm ${activeEvidence?.id === item.id ? "border-primary bg-blue-50" : "border-border bg-white"}`}
                  >
                    <div className="font-medium">{item.title}</div>
                    <div className="mt-1 text-xs text-slate-500">{item.intended_control_id || "Unassigned"} | {item.evidence_type} | {item.file_type} | {item.review_status} | {item.drift_state}</div>
                  </button>
                ))}
                {!evidence.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">No evidence uploaded yet.</div>}
              </div>
            </div>
          </aside>

          <div className="space-y-5">
            {activeEvidence ? (
              <section className="rounded-md border border-border bg-white p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">{activeEvidence.title}</h2>
                    <p className="text-sm text-slate-600">
                      {activeEvidence.file_name} | {activeEvidence.intended_control_id || "Unassigned"} | {activeEvidence.document_type} | {activeEvidence.data_classification} | CUI {activeEvidence.contains_cui} | ITAR {activeEvidence.contains_itar} | PII {activeEvidence.contains_pii} | {activeEvidence.evidence_type} | {activeEvidence.status} | {activeEvidence.review_status} | {activeEvidence.drift_state}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <label className="inline-flex h-9 cursor-pointer items-center gap-2 rounded-md border border-border bg-white px-3 text-sm font-medium">
                      <RefreshCw size={15} />
                      Replace
                      <input className="sr-only" type="file" onChange={(event) => replaceEvidence(event.target.files?.[0] ?? null)} />
                    </label>
                    <button onClick={removeEvidence} className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-white px-3 text-sm font-medium text-red-700">
                      <Trash2 size={15} />
                      Remove
                    </button>
                    <FileArchive className="mt-1 text-slate-500" size={22} />
                  </div>
                </div>
                <div className="mt-4 rounded-md border border-border bg-muted p-4">
                  <div className="grid gap-3 md:grid-cols-[220px_1fr]">
                    <label className="block">
                      <span className="text-xs font-medium text-slate-600">Reviewer</span>
                      <input
                        className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                        value={reviewer}
                        onChange={(event) => setReviewer(event.target.value)}
                      />
                    </label>
                    <label className="block">
                      <span className="text-xs font-medium text-slate-600">Review notes</span>
                      <input
                        className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                        value={reviewNotes}
                        onChange={(event) => setReviewNotes(event.target.value)}
                        placeholder="Reviewer observations, replacement reason, or acceptance notes"
                      />
                    </label>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {["Under Review", "Accepted", "Needs Replacement", "Rejected"].map((reviewStatus) => (
                      <button
                        key={reviewStatus}
                        onClick={() => reviewEvidence(reviewStatus)}
                        className={`inline-flex h-9 items-center rounded-md px-3 text-sm font-medium ${
                          activeEvidence.review_status === reviewStatus ? "bg-primary text-white" : "border border-border bg-white"
                        }`}
                      >
                        {reviewStatus}
                      </button>
                    ))}
                  </div>
                  {(activeEvidence.reviewer || activeEvidence.review_date) && (
                    <div className="mt-2 text-xs text-slate-600">
                      Last reviewed by {activeEvidence.reviewer || "Unassigned"} on {activeEvidence.review_date || "not dated"}.
                    </div>
                  )}
                </div>
                <div className="mt-4 grid gap-3 md:grid-cols-3">
                  {activeEvidence.analyses.slice(0, 3).map((analysis) => (
                    <div key={analysis.id} className="rounded-md border border-border p-3">
                      <div className="text-sm font-semibold">{analysis.control_id}</div>
                      <div className="mt-1 text-xs text-slate-500">{analysis.control_title}</div>
                      <div className="mt-3 flex items-center gap-2 text-sm">
                        <Gauge size={15} />
                        {analysis.coverage_score}% coverage | {analysis.confidence_score}% confidence
                      </div>
                      <div className="mt-2 text-xs font-medium text-primary">{analysis.assessment_strength}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-5 space-y-4">
                  {activeEvidence.analyses.map((analysis) => (
                    <div key={analysis.id} className="rounded-md border border-border p-4">
                      <div className="flex flex-wrap justify-between gap-3">
                        <h3 className="font-semibold">{analysis.control_id} - {analysis.control_title}</h3>
                        <span className="text-sm text-slate-600">{analysis.assessment_strength}</span>
                      </div>
                      <p className="mt-2 text-sm text-slate-700">{analysis.assessor_observations}</p>
                      <div className="mt-4 grid gap-4 lg:grid-cols-2">
                        <div>
                          <div className="text-xs font-medium uppercase text-slate-500">Objective Mapping</div>
                          <ul className="mt-2 space-y-2 text-sm">
                            {analysis.objectives.map((objective) => (
                              <li key={objective.id} className="rounded-md bg-muted p-2">
                                <span className="font-medium">{objective.supported}</span> - {objective.objective}
                                <div className="mt-1 text-xs text-slate-600">{objective.notes}</div>
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <div className="text-xs font-medium uppercase text-slate-500">Recommendations</div>
                          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                            {analysis.recommendations.map((item) => <li key={item}>{item}</li>)}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
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
                    {!activity.length && <div className="text-sm text-slate-600">No activity has been recorded for this evidence item yet.</div>}
                  </div>
                </div>
              </section>
            ) : (
              <section className="rounded-md border border-border bg-white p-5 text-sm text-slate-700">
                Upload evidence to generate control mappings, objective support, confidence scores, missing evidence, and assessor observations.
              </section>
            )}

            <section className="rounded-md border border-border bg-white p-5">
              <h2 className="text-base font-semibold">Control Coverage</h2>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[720px] text-left text-sm">
                  <thead className="border-b border-border text-xs uppercase text-slate-500">
                    <tr>
                      <th className="py-2">Control</th>
                      <th className="py-2">Family</th>
                      <th className="py-2">Evidence</th>
                      <th className="py-2">Objectives</th>
                      <th className="py-2">Coverage</th>
                      <th className="py-2">Confidence</th>
                      <th className="py-2">Strength</th>
                      <th className="py-2">Drift</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topCoverage.map((item) => (
                      <tr key={item.control_id} className="border-b border-border">
                        <td className="py-2 font-medium">{item.control_id}</td>
                        <td className="py-2">{item.family}</td>
                        <td className="py-2">{item.evidence_count}</td>
                        <td className="py-2">{item.objectives_with_evidence}/{item.total_objectives}</td>
                        <td className="py-2">{item.objective_coverage_score || item.coverage_score}%</td>
                        <td className="py-2">{item.confidence_score}%</td>
                        <td className="py-2">{item.assessment_strength}</td>
                        <td className="py-2">{item.drift_state}</td>
                      </tr>
                    ))}
                    {!topCoverage.length && (
                      <tr>
                        <td className="py-4 text-slate-600" colSpan={8}>No control coverage yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}
