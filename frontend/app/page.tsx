"use client";

import { BookOpen, Bot, CalendarDays, ClipboardList, Download, FileArchive, FileCheck2, FileSearch, FileText, Gauge, GitBranch, HeartPulse, History, LogIn, Save, ShieldCheck, Sparkles, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, CompanyProfile, Control, DocumentOutput, GeneratedOutput } from "@/lib/api";

const emptyProfile: CompanyProfile = {
  company_name: "Example Defense Supplier",
  industry: "Aerospace manufacturing",
  employee_count: "75",
  locations: "Akron, OH headquarters; remote engineering staff",
  cloud_environment: "Microsoft 365 GCC High and Azure Government",
  cui_environment: "CUI is stored in GCC High SharePoint sites and processed on managed Windows endpoints.",
  msp_involvement: "MSP supports Microsoft 365, endpoint management, and backup monitoring.",
  mfa_solution: "Microsoft Entra ID MFA with conditional access",
  endpoint_management: "Microsoft Intune",
  backup_solution: "Azure Backup with immutable retention",
  ticketing_system: "ServiceNow",
  hr_onboarding_process: "HR opens onboarding ticket after signed offer and manager approval.",
  access_removal_process: "HR termination ticket triggers same-day account disablement and access review.",
};

const fields: Array<[keyof CompanyProfile, string]> = [
  ["company_name", "Company name"],
  ["industry", "Industry"],
  ["employee_count", "Employee count"],
  ["locations", "Locations"],
  ["cloud_environment", "Cloud environment"],
  ["cui_environment", "CUI environment"],
  ["msp_involvement", "MSP involvement"],
  ["mfa_solution", "MFA solution"],
  ["endpoint_management", "Endpoint management"],
  ["backup_solution", "Backup solution"],
  ["ticketing_system", "Ticketing system"],
  ["hr_onboarding_process", "HR onboarding process"],
  ["access_removal_process", "Access removal process"],
];

function readSignedInState() {
  try {
    return window.localStorage.getItem("cmmc_signed_in") === "true";
  } catch {
    return false;
  }
}

function saveSignedInState() {
  try {
    window.localStorage.setItem("cmmc_signed_in", "true");
  } catch {
    // Storage can be unavailable in embedded browsers; React state still signs the user in.
  }
}

export default function Home() {
  const [profile, setProfile] = useState<CompanyProfile>(emptyProfile);
  const [profileId, setProfileId] = useState<number | null>(null);
  const [controls, setControls] = useState<Control[]>([]);
  const [selectedId, setSelectedId] = useState("AC.L2-3.1.1");
  const [selected, setSelected] = useState<Control | null>(null);
  const [output, setOutput] = useState<GeneratedOutput | null>(null);
  const [policy, setPolicy] = useState<DocumentOutput | null>(null);
  const [procedure, setProcedure] = useState<DocumentOutput | null>(null);
  const [dashboard, setDashboard] = useState<Record<string, number> | null>(null);
  const [status, setStatus] = useState("Ready");
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    setSignedIn(readSignedInState());
  }, []);

  useEffect(() => {
    api.controls().then(setControls).catch(() => setStatus("Start the FastAPI backend on port 8000."));
    api.dashboard().then(setDashboard).catch(() => undefined);
  }, []);

  useEffect(() => {
    api.control(selectedId).then(setSelected).catch(() => undefined);
  }, [selectedId]);

  const groupedControls = useMemo(() => {
    return controls.reduce<Record<string, Control[]>>((acc, control) => {
      acc[control.family] = [...(acc[control.family] ?? []), control];
      return acc;
    }, {});
  }, [controls]);

  async function saveProfile() {
    setStatus("Saving company profile...");
    const saved = await api.createProfile(profile);
    setProfileId(saved.id ?? null);
    setStatus("Company profile saved.");
  }

  async function ensureProfile() {
    const id = profileId ?? (await api.createProfile(profile)).id;
    if (!id) throw new Error("Company profile could not be saved.");
    setProfileId(id);
    return id;
  }

  async function generate() {
    setStatus("Generating control documentation...");
    const id = await ensureProfile();
    const generated = await api.generate(id, selectedId);
    setOutput(generated);
    setDashboard(await api.dashboard());
    setStatus("Generated editable output.");
  }

  async function generatePolicy() {
    await generatePolicyForControl(selectedId);
  }

  async function generatePolicyForControl(controlId: string) {
    setStatus("Generating policy...");
    setSelectedId(controlId);
    const id = await ensureProfile();
    setPolicy(await api.generatePolicy(id, controlId));
    setStatus("Generated editable policy.");
  }

  async function generateProcedure() {
    await generateProcedureForControl(selectedId);
  }

  async function generateProcedureForControl(controlId: string) {
    setStatus("Generating procedure...");
    setSelectedId(controlId);
    const id = await ensureProfile();
    setProcedure(await api.generateProcedure(id, controlId));
    setStatus("Generated editable procedure.");
  }

  async function saveOutput() {
    if (!output) return;
    setStatus("Saving revisions...");
    setOutput(await api.saveOutput(output.id, output));
    setStatus("Revisions saved.");
  }

  async function saveDocument(document: DocumentOutput, setter: (document: DocumentOutput) => void) {
    setStatus(`Saving ${document.document_type} version...`);
    setter(await api.saveDocument(document));
    setStatus(`Saved ${document.document_type} version ${document.version}.`);
  }

  if (!signedIn) {
    return (
      <main className="grid min-h-screen place-items-center bg-background px-6">
        <section className="w-full max-w-sm rounded-md border border-border bg-white p-6 shadow-sm">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-white">
            <ShieldCheck size={22} />
          </div>
          <h1 className="mt-5 text-2xl font-semibold">CMMC Pilot</h1>
          <div className="mt-5 space-y-3">
            <label className="block">
              <span className="text-xs font-medium text-slate-600">Email</span>
              <input className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary" defaultValue="assessor@example.com" />
            </label>
            <label className="block">
              <span className="text-xs font-medium text-slate-600">Password</span>
              <input className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary" type="password" defaultValue="mvp-password" />
            </label>
            <button
              onClick={() => {
                setSignedIn(true);
                saveSignedInState();
              }}
              className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white"
            >
              <LogIn size={16} />
              Sign In
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">CMMC Pilot</h1>
            <p className="text-sm text-slate-600">Level 2 implementation statement and evidence checklist generator</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/ssp" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileText size={16} />
              SSP Builder
            </a>
            <a href="/evidence" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileArchive size={16} />
              Evidence
            </a>
            <a href="/evidence-requests" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileText size={16} />
              Requests
            </a>
            <a href="/health" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <HeartPulse size={16} />
              Health
            </a>
            <a href="/poam" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ClipboardList size={16} />
              POA&M
            </a>
            <a href="/audit" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <History size={16} />
              Audit
            </a>
            <a href="/people" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <Users size={16} />
              People
            </a>
            <a href="/reviews" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileCheck2 size={16} />
              Reviews
            </a>
            <a href="/calendar" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <CalendarDays size={16} />
              Calendar
            </a>
            <a href="/assessment-package" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileArchive size={16} />
              Package
            </a>
            <a href="/compliance" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileSearch size={16} />
              Compliance
            </a>
            <a href="/copilot" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <Bot size={16} />
              Copilot
            </a>
            <button className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <LogIn size={16} />
              MVP Sign In
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-4 px-6 py-5 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Controls complete", `${dashboard?.controls_complete ?? 0}/${dashboard?.total_controls ?? 110}`],
          ["Evidence uploaded", String(dashboard?.evidence_uploaded ?? 0)],
          ["Open gaps", String(dashboard?.open_gaps ?? 0)],
          ["POA&M items", String(dashboard?.poam_items ?? 0)],
          ["Readiness score", `${dashboard?.assessment_readiness_score ?? 0}%`],
          ["Overdue tasks", String(dashboard?.overdue_tasks ?? 0)],
          ["Due soon", String(dashboard?.due_soon_tasks ?? 0)],
          ["Unscheduled", String(dashboard?.unscheduled_tasks ?? 0)],
          ["Reviews approved", String(dashboard?.reviews_approved ?? 0)],
          ["Reviews rejected", String(dashboard?.reviews_rejected ?? 0)],
          ["Evidence requests", String(dashboard?.evidence_requests_open ?? 0)],
          ["Requests overdue", String(dashboard?.evidence_requests_overdue ?? 0)],
        ].map(([label, value]) => (
          <div key={label} className="rounded-md border border-border bg-white p-4">
            <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500">
              <Gauge size={14} />
              {label}
            </div>
            <div className="mt-2 text-2xl font-semibold">{value}</div>
          </div>
        ))}
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-6 pb-8 lg:grid-cols-[390px_1fr]">
        <aside className="space-y-5">
          <div className="rounded-md border border-border bg-white p-4">
            <h2 className="text-base font-semibold">Organization Profile</h2>
            <div className="mt-4 space-y-3">
              {fields.map(([key, label]) => (
                <label key={key} className="block">
                  <span className="text-xs font-medium text-slate-600">{label}</span>
                  <textarea
                    className="mt-1 min-h-10 w-full resize-y rounded-md border border-border px-3 py-2 text-sm outline-none focus:border-primary"
                    value={String(profile[key] ?? "")}
                    onChange={(event) => setProfile({ ...profile, [key]: event.target.value })}
                    rows={key.includes("process") || key.includes("environment") ? 2 : 1}
                  />
                </label>
              ))}
              <button onClick={saveProfile} className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border border-border bg-white text-sm font-medium">
                <Save size={16} />
                Save Profile
              </button>
            </div>
          </div>
        </aside>

        <div className="space-y-5">
          <div className="rounded-md border border-border bg-white p-4">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold">Control Library</h2>
                <p className="text-sm text-slate-600">Select from the seeded CMMC Level 2 controls.</p>
              </div>
              <select
                className="h-10 min-w-72 rounded-md border border-border px-3 text-sm"
                value={selectedId}
                onChange={(event) => setSelectedId(event.target.value)}
              >
                {Object.entries(groupedControls).map(([family, familyControls]) => (
                  <optgroup key={family} label={family}>
                    {familyControls.map((control) => (
                      <option key={control.control_id} value={control.control_id}>
                        {control.control_id} - {control.title}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
          </div>

          {selected && (
            <div className="rounded-md border border-border bg-white p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="text-sm font-medium text-primary">{selected.control_id}</div>
                  <h2 className="text-2xl font-semibold">{selected.title}</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">{selected.requirement}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button onClick={generate} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                    <Sparkles size={16} />
                    Control Response
                  </button>
                  <button onClick={generatePolicy} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                    <BookOpen size={16} />
                    Family Policy
                  </button>
                  <button onClick={generateProcedure} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                    <ClipboardList size={16} />
                    Family Procedure
                  </button>
                  <a href={`/controls/${selected.control_id}/graph`} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                    <GitBranch size={16} />
                    Control Graph
                  </a>
                  <a href={`/controls/${selected.control_id}/objectives`} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                    <FileSearch size={16} />
                    Objectives
                  </a>
                </div>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold">Assessment Objectives</h3>
                  <ul className="mt-2 space-y-2 text-sm text-slate-700">
                    {selected.objectives.map((objective) => (
                      <li key={objective} className="rounded-md bg-muted p-3">{objective}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-semibold">Evidence Checklist</h3>
                  <ul className="mt-2 space-y-2 text-sm text-slate-700">
                    {selected.evidence.map((item) => (
                      <li key={item} className="rounded-md bg-muted p-3">{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {output && (
            <div className="rounded-md border border-border bg-white p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold">Generated Workspace</h2>
                  <p className="text-sm text-slate-600">{status}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button onClick={saveOutput} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                    <Save size={16} />
                    Save
                  </button>
                  <a href={api.exportUrl(output.id, "docx")} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                    <FileText size={16} />
                    Word
                  </a>
                  <a href={api.exportUrl(output.id, "pdf")} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                    <Download size={16} />
                    PDF
                  </a>
                </div>
              </div>

              <div className="mt-4 grid gap-4">
                {[
                  ["implementation_statement", "Implementation Statement"],
                  ["responsible_parties", "Responsible Parties"],
                  ["evidence_artifacts", "Evidence Artifacts"],
                  ["assessment_notes", "Assessment Notes"],
                  ["gaps_assumptions", "Gaps or Assumptions"],
                ].map(([key, label]) => (
                  <label key={key} className="block">
                    <span className="text-sm font-semibold">{label}</span>
                    <textarea
                      className="mt-2 min-h-32 w-full rounded-md border border-border p-3 text-sm leading-6 outline-none focus:border-primary"
                      value={String(output[key as keyof GeneratedOutput])}
                      onChange={(event) => setOutput({ ...output, [key]: event.target.value })}
                    />
                  </label>
                ))}
              </div>
            </div>
          )}

          {[policy, procedure].map((document) =>
            document ? (
              <div key={`${document.document_type}-${document.id}`} className="rounded-md border border-border bg-white p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-primary">{document.control_id}</div>
                    <h2 className="text-base font-semibold">{document.name}</h2>
                    <p className="text-sm text-slate-600">Version {document.version} - {document.status}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() =>
                        saveDocument(document, document.document_type === "policy" ? setPolicy : setProcedure)
                      }
                      className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium"
                    >
                      <Save size={16} />
                      Save Version
                    </button>
                    <a href={api.documentExportUrl(document, "docx")} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                      <FileText size={16} />
                      Word
                    </a>
                    <a href={api.documentExportUrl(document, "pdf")} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                      <Download size={16} />
                      PDF
                    </a>
                  </div>
                </div>

                <div className="mt-4 grid gap-4 md:grid-cols-3">
                  {[
                    ["version", "Version"],
                    ["author", "Author"],
                    ["approver", "Approver"],
                    ["approval_date", "Approval Date"],
                    ["review_date", "Review Date"],
                    ["status", "Status"],
                  ].map(([key, label]) => (
                    <label key={key} className="block">
                      <span className="text-xs font-medium text-slate-600">{label}</span>
                      <input
                        className="mt-1 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                        value={String(document[key as keyof DocumentOutput] ?? "")}
                        onChange={(event) => {
                          const updated = { ...document, [key]: event.target.value };
                          document.document_type === "policy" ? setPolicy(updated) : setProcedure(updated);
                        }}
                      />
                    </label>
                  ))}
                </div>

                <div className="mt-4 grid gap-4">
                  <label className="block">
                    <span className="text-sm font-semibold">Document Name</span>
                    <input
                      className="mt-2 h-10 w-full rounded-md border border-border px-3 text-sm outline-none focus:border-primary"
                      value={document.name}
                      onChange={(event) => {
                        const updated = { ...document, name: event.target.value };
                        document.document_type === "policy" ? setPolicy(updated) : setProcedure(updated);
                      }}
                    />
                  </label>
                  <label className="block">
                    <span className="text-sm font-semibold">{document.document_type === "policy" ? "Policy" : "Procedure"}</span>
                    <textarea
                      className="mt-2 min-h-80 w-full rounded-md border border-border p-3 text-sm leading-6 outline-none focus:border-primary"
                      value={document.text}
                      onChange={(event) => {
                        const updated = { ...document, text: event.target.value };
                        document.document_type === "policy" ? setPolicy(updated) : setProcedure(updated);
                      }}
                    />
                  </label>
                  <label className="block">
                    <span className="text-sm font-semibold">Responsibility Matrix</span>
                    <textarea
                      className="mt-2 min-h-36 w-full rounded-md border border-border p-3 font-mono text-xs leading-5 outline-none focus:border-primary"
                      value={document.responsibility_matrix}
                      onChange={(event) => {
                        const updated = { ...document, responsibility_matrix: event.target.value };
                        document.document_type === "policy" ? setPolicy(updated) : setProcedure(updated);
                      }}
                    />
                  </label>
                </div>
              </div>
            ) : null
          )}

        </div>
      </section>
    </main>
  );
}
