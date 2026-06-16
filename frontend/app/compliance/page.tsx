"use client";

import { Bot, FileSearch, FileText, Gauge, Network, RefreshCw, Search, ShieldCheck, Trash2, Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, ComplianceDocument, ComplianceGraph, ComplianceReadiness, ComplianceSearchResult } from "@/lib/api";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

const emptyGraph: ComplianceGraph = {
  documents: 0,
  mapped_controls: 0,
  policies: 0,
  procedures: 0,
  ssp_documents: 0,
  poam_documents: 0,
  entities: {},
  recent_alerts: [],
};

const emptyReadiness: ComplianceReadiness = {
  documentation_score: 0,
  evidence_score: 0,
  poam_score: 0,
  overall_score: 0,
  findings: [],
};

const documentTypes = ["", "SSP", "POA&M", "Policy", "Procedure", "Incident Response Plan", "Contingency Plan", "Network Diagram", "CUI Flow Diagram"];
const dataClassifications = ["", "Public", "Internal", "Confidential"];

export default function CompliancePage() {
  const [documents, setDocuments] = useState<ComplianceDocument[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [graph, setGraph] = useState<ComplianceGraph>(emptyGraph);
  const [readiness, setReadiness] = useState<ComplianceReadiness>(emptyReadiness);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [controlFilter, setControlFilter] = useState("");
  const [uploadType, setUploadType] = useState("");
  const [uploadClassification, setUploadClassification] = useState("");
  const [containsCui, setContainsCui] = useState(false);
  const [containsItar, setContainsItar] = useState(false);
  const [containsPii, setContainsPii] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [searchResults, setSearchResults] = useState<ComplianceSearchResult[]>([]);
  const [question, setQuestion] = useState("What evidence supports AC.L2-3.1.1?");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [status, setStatus] = useState("Ready");

  async function refresh(preferredId?: number | null) {
    const [docs, graphSummary, readinessSummary] = await Promise.all([
      api.complianceDocuments(query, typeFilter, controlFilter),
      api.complianceGraph(),
      api.complianceReadiness(),
    ]);
    setDocuments(docs);
    setGraph(graphSummary);
    setReadiness(readinessSummary);
    setActiveId((current) => {
      if (preferredId !== undefined) return preferredId;
      return docs.some((item) => item.id === current) ? current : docs[0]?.id ?? null;
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
  }, [query, typeFilter, controlFilter]);

  const activeDocument = useMemo(
    () => documents.find((item) => item.id === activeId) ?? documents[0],
    [activeId, documents]
  );

  function uploadMetadata() {
    return {
      document_type: uploadType,
      data_classification: uploadClassification,
      contains_cui: containsCui,
      contains_itar: containsItar,
      contains_pii: containsPii,
    };
  }

  function uploadAllowed() {
    if (!uploadType) {
      setStatus("Document Type is required before upload.");
      return false;
    }
    if (!uploadClassification) {
      setStatus("Data Classification is required before upload.");
      return false;
    }
    if (containsCui || containsItar) {
      setStatus("Upload blocked. Azure Commercial is not approved for CUI or ITAR.");
      return false;
    }
    return true;
  }

  async function uploadDocument(file: File | null) {
    if (!file) return;
    if (!uploadAllowed()) return;
    setStatus(`Parsing ${file.name}...`);
    const content = await fileToBase64(file);
    const uploaded = await api.uploadComplianceDocument({ file_name: file.name, content_base64: content, ...uploadMetadata() });
    await refresh(uploaded.id);
    setStatus(`Parsed ${uploaded.title}.`);
  }

  async function replaceDocument(file: File | null) {
    if (!file || !activeDocument) return;
    if (!uploadAllowed()) return;
    setStatus(`Replacing ${activeDocument.file_name}...`);
    const content = await fileToBase64(file);
    const replaced = await api.replaceComplianceDocument(activeDocument.id, {
      file_name: file.name,
      content_base64: content,
      ...uploadMetadata(),
      owner: activeDocument.owner,
    });
    await refresh(replaced.id);
    setStatus(`Replaced and re-parsed ${replaced.title}.`);
  }

  async function removeDocument() {
    if (!activeDocument) return;
    if (!window.confirm(`Remove ${activeDocument.file_name} and its parsed mappings/entities?`)) return;
    setStatus(`Removing ${activeDocument.file_name}...`);
    await api.deleteComplianceDocument(activeDocument.id);
    const remaining = documents.filter((document) => document.id !== activeDocument.id);
    await refresh(remaining[0]?.id ?? null);
    setStatus(`Removed ${activeDocument.file_name}.`);
  }

  async function runSearch() {
    if (!searchText.trim()) {
      setSearchResults([]);
      return;
    }
    setSearchResults(await api.complianceSearch(searchText));
  }

  async function askQuestion() {
    if (!question.trim()) return;
    setStatus("Answering from compliance graph...");
    const response = await api.complianceChat(question);
    setAnswer(response.answer);
    setSources(response.sources);
    setStatus("Ready");
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Compliance Intelligence</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href="/evidence" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileSearch size={16} />
              Evidence
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 md:grid-cols-4">
          {[
            ["Overall Readiness", `${readiness.overall_score}%`],
            ["Documents", graph.documents],
            ["Mapped Controls", graph.mapped_controls],
            ["POA&M Files", graph.poam_documents],
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

        <div className="mt-5 grid gap-5 lg:grid-cols-[380px_1fr]">
          <aside className="space-y-5">
            <section className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Upload Compliance Artifact</h2>
              <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
                This Azure Commercial environment is not approved for CUI. Users must not upload CUI, ITAR, export-controlled data, classified data, or sensitive government contract information.
              </div>
              <select
                className="mt-3 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                value={uploadType}
                onChange={(event) => setUploadType(event.target.value)}
              >
                {documentTypes.map((type) => <option key={type || "Select"} value={type}>{type || "Select document type"}</option>)}
              </select>
              <select
                className="mt-3 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                value={uploadClassification}
                onChange={(event) => setUploadClassification(event.target.value)}
              >
                {dataClassifications.map((classification) => <option key={classification || "Select"} value={classification}>{classification || "Select data classification"}</option>)}
              </select>
              <div className="mt-3 grid gap-2 text-sm">
                {[
                  ["Contains CUI?", containsCui, setContainsCui],
                  ["Contains ITAR?", containsItar, setContainsItar],
                  ["Contains PII?", containsPii, setContainsPii],
                ].map(([label, value, setter]) => (
                  <label key={String(label)} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <span>{String(label)}</span>
                    <input type="checkbox" checked={Boolean(value)} onChange={(event) => (setter as (checked: boolean) => void)(event.target.checked)} />
                  </label>
                ))}
              </div>
              <label className="mt-3 flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-slate-300 bg-muted px-4 py-6 text-center text-sm text-slate-600">
                <Upload size={22} />
                <span className="mt-2 font-medium">SSP, POA&M, policies, procedures, diagrams, ZIPs</span>
                <input className="sr-only" type="file" onChange={(event) => uploadDocument(event.target.files?.[0] ?? null)} />
              </label>
            </section>

            <section className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Document Library</h2>
              <div className="mt-3 space-y-2">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                  <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm outline-none focus:border-primary" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search documents" />
                </div>
                <select className="h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
                  {documentTypes.map((type) => <option key={type || "All"} value={type}>{type || "All document types"}</option>)}
                </select>
                <input className="h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary" value={controlFilter} onChange={(event) => setControlFilter(event.target.value)} placeholder="Filter by control, e.g. AC.L2-3.1.1" />
              </div>
              <div className="mt-4 space-y-2">
                {documents.map((document) => (
                  <button key={document.id} onClick={() => setActiveId(document.id)} className={`w-full rounded-md border px-3 py-2 text-left text-sm ${activeDocument?.id === document.id ? "border-primary bg-blue-50" : "border-border bg-white"}`}>
                    <div className="font-medium">{document.title}</div>
                    <div className="mt-1 text-xs text-slate-500">{document.document_type} | {document.data_classification} | {document.mappings.length} controls | {document.entities.length} entities</div>
                  </button>
                ))}
                {!documents.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">No compliance documents uploaded yet.</div>}
              </div>
            </section>
          </aside>

          <div className="space-y-5">
            <section className="grid gap-3 md:grid-cols-3">
              {[
                ["Documentation", `${readiness.documentation_score}%`],
                ["Evidence", `${readiness.evidence_score}%`],
                ["POA&M", `${readiness.poam_score}%`],
              ].map(([label, value]) => (
                <div key={label} className="rounded-md border border-border bg-white p-4">
                  <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
                  <div className="mt-2 text-2xl font-semibold">{value}</div>
                </div>
              ))}
            </section>

            {activeDocument ? (
              <section className="rounded-md border border-border bg-white p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">{activeDocument.title}</h2>
                    <p className="text-sm text-slate-600">{activeDocument.file_name} | {activeDocument.document_type} | {activeDocument.data_classification} | CUI: {activeDocument.contains_cui} | ITAR: {activeDocument.contains_itar} | PII: {activeDocument.contains_pii} | {activeDocument.status}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <label className="inline-flex h-9 cursor-pointer items-center gap-2 rounded-md border border-border bg-white px-3 text-sm font-medium">
                      <RefreshCw size={15} />
                      Replace
                      <input className="sr-only" type="file" onChange={(event) => replaceDocument(event.target.files?.[0] ?? null)} />
                    </label>
                    <button onClick={removeDocument} className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-white px-3 text-sm font-medium text-red-700">
                      <Trash2 size={15} />
                      Remove
                    </button>
                    <FileText className="mt-1 text-slate-500" size={24} />
                  </div>
                </div>
                <div className="mt-4 grid gap-3 md:grid-cols-3">
                  <div className="rounded-md bg-muted p-3 text-sm">Owner: {activeDocument.owner || "Not extracted"}</div>
                  <div className="rounded-md bg-muted p-3 text-sm">Version: {activeDocument.version || "Not extracted"}</div>
                  <div className="rounded-md bg-muted p-3 text-sm">Review: {activeDocument.review_date || "Not extracted"}</div>
                </div>
                <div className="mt-5 grid gap-5 lg:grid-cols-2">
                  <div>
                    <h3 className="text-sm font-semibold">Control Mappings</h3>
                    <div className="mt-2 space-y-2">
                      {activeDocument.mappings.slice(0, 14).map((mapping) => (
                        <div key={`${mapping.control_id}-${mapping.mapping_type}`} className="rounded-md border border-border p-3 text-sm">
                          <div className="font-medium">{mapping.control_id} - {mapping.control_title}</div>
                          <div className="mt-1 text-xs text-slate-600">{mapping.confidence_score}% | {mapping.rationale}</div>
                        </div>
                      ))}
                      {!activeDocument.mappings.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">No controls extracted yet.</div>}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold">Extracted Entities</h3>
                    <div className="mt-2 space-y-2">
                      {activeDocument.entities.slice(0, 14).map((entity, index) => (
                        <div key={`${entity.entity_type}-${index}`} className="rounded-md border border-border p-3 text-sm">
                          <div className="text-xs font-medium uppercase text-slate-500">{entity.entity_type}</div>
                          <div className="mt-1">{entity.entity_value}</div>
                        </div>
                      ))}
                      {!activeDocument.entities.length && <div className="rounded-md bg-muted p-3 text-sm text-slate-600">No entities extracted yet.</div>}
                    </div>
                  </div>
                </div>
              </section>
            ) : null}

            <section className="grid gap-5 lg:grid-cols-2">
              <div className="rounded-md border border-border bg-white p-5">
                <h2 className="flex items-center gap-2 text-base font-semibold"><Network size={17} /> Compliance Graph</h2>
                <div className="mt-3 grid gap-2 text-sm">
                  {Object.entries(graph.entities).map(([type, count]) => (
                    <div key={type} className="flex justify-between rounded-md bg-muted px-3 py-2">
                      <span>{type}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                  {!Object.keys(graph.entities).length && <div className="rounded-md bg-muted p-3 text-slate-600">Upload artifacts to populate the digital twin.</div>}
                </div>
                <div className="mt-4 space-y-2">
                  {readiness.findings.map((finding) => <div key={finding} className="rounded-md border border-border p-3 text-sm text-slate-700">{finding}</div>)}
                </div>
              </div>

              <div className="rounded-md border border-border bg-white p-5">
                <h2 className="flex items-center gap-2 text-base font-semibold"><Bot size={17} /> Compliance Chat</h2>
                <textarea className="mt-3 min-h-24 w-full rounded-md border border-border px-3 py-2 text-sm outline-none focus:border-primary" value={question} onChange={(event) => setQuestion(event.target.value)} />
                <button onClick={askQuestion} className="mt-2 inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">Ask</button>
                {answer && <div className="mt-4 rounded-md bg-muted p-3 text-sm">{answer}</div>}
                {!!sources.length && <div className="mt-3 text-xs text-slate-600">Sources: {sources.join(", ")}</div>}
              </div>
            </section>

            <section className="rounded-md border border-border bg-white p-5">
              <h2 className="text-base font-semibold">Compliance Search</h2>
              <div className="mt-3 flex gap-2">
                <input className="h-10 flex-1 rounded-md border border-border px-3 text-sm outline-none focus:border-primary" value={searchText} onChange={(event) => setSearchText(event.target.value)} placeholder="Search boundary, vendors, controls, owners, POA&M terms" />
                <button onClick={runSearch} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium"><Search size={16} /> Search</button>
              </div>
              <div className="mt-4 space-y-2">
                {searchResults.map((result, index) => (
                  <div key={`${result.result_type}-${index}`} className="rounded-md border border-border p-3 text-sm">
                    <div className="font-medium">{result.title}</div>
                    <div className="text-xs text-slate-500">{result.result_type} | {result.subtitle}</div>
                    <p className="mt-2 text-slate-700">{result.excerpt}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}
