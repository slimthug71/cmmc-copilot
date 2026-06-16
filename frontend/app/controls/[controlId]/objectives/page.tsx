"use client";

import { AlertTriangle, ArrowLeft, CheckCircle2, FileSearch, GitBranch, Save, ShieldCheck } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, ControlObjectiveWorkspace, ObjectiveEvidenceItem } from "@/lib/api";

function statusClass(status: string) {
  if (status === "Supported") return "bg-emerald-50 text-emerald-700";
  if (status === "Partially Supported") return "bg-amber-50 text-amber-700";
  return "bg-red-50 text-red-700";
}

function EvidenceEditor({
  item,
  onSave,
}: {
  item: ObjectiveEvidenceItem;
  onSave: (id: number, supported: string, notes: string) => Promise<void>;
}) {
  const [supported, setSupported] = useState(item.supported);
  const [notes, setNotes] = useState(item.notes);
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    await onSave(item.support_record_id, supported, notes);
    setSaving(false);
  }

  return (
    <div className="rounded-md border border-border p-3 text-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-medium">{item.evidence_title}</div>
          <div className="mt-1 text-xs text-slate-500">{item.file_name} | {item.evidence_type} | {item.confidence_score}% confidence</div>
        </div>
        <select
          value={supported}
          onChange={(event) => setSupported(event.target.value)}
          className="h-9 rounded-md border border-border px-2 text-xs"
        >
          <option>Supported</option>
          <option>Partially Supported</option>
          <option>Not Supported</option>
        </select>
      </div>
      <textarea
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
        className="mt-3 min-h-20 w-full rounded-md border border-border p-2 text-sm leading-5 outline-none focus:border-primary"
      />
      <button onClick={save} className="mt-2 inline-flex h-9 items-center gap-2 rounded-md border border-border bg-white px-3 text-xs font-medium">
        <Save size={14} />
        {saving ? "Saving..." : "Save Override"}
      </button>
    </div>
  );
}

export default function ControlObjectivesPage() {
  const params = useParams<{ controlId: string }>();
  const controlId = decodeURIComponent(params?.controlId ?? "");
  const [workspace, setWorkspace] = useState<ControlObjectiveWorkspace | null>(null);
  const [status, setStatus] = useState("Loading objectives...");

  async function refresh() {
    if (!controlId) return;
    setWorkspace(await api.controlObjectives(controlId));
    setStatus("Ready");
  }

  useEffect(() => {
    refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, [controlId]);

  const unsupported = useMemo(() => workspace?.objectives.filter((objective) => objective.status !== "Supported") ?? [], [workspace]);

  async function saveSupport(id: number, supported: string, notes: string) {
    const updated = await api.updateEvidenceObjective(id, { supported, notes });
    setWorkspace(updated);
  }

  if (!workspace) {
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
            <h1 className="text-xl font-semibold tracking-normal">{workspace.control_id} Objective Workspace</h1>
            <p className="text-sm text-slate-600">{workspace.control_title} | {workspace.family}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href={`/controls/${workspace.control_id}/graph`} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <GitBranch size={16} />
              Control Graph
            </a>
            <a href="/evidence" className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <FileSearch size={16} />
              Upload Evidence
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="rounded-md border border-border bg-white p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-primary">{workspace.requirement}</div>
              <p className="mt-2 text-sm text-slate-600">{status}</p>
            </div>
            <div className="rounded-md bg-muted p-4 text-right">
              <div className="text-xs font-medium uppercase text-slate-500">Objective Readiness</div>
              <div className="mt-1 text-3xl font-semibold">{workspace.readiness_score}%</div>
            </div>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-4">
            {[
              ["Supported", workspace.supported_objectives],
              ["Partial", workspace.partial_objectives],
              ["Open", unsupported.length],
              ["Total", workspace.total_objectives],
            ].map(([label, value]) => (
              <div key={label} className="rounded-md bg-muted p-3">
                <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
                <div className="mt-2 text-xl font-semibold">{value}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-5 space-y-4">
          {workspace.objectives.map((objective) => (
            <section key={objective.id} className="rounded-md border border-border bg-white p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="max-w-4xl">
                  <div className="flex items-center gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-md bg-muted text-sm font-semibold">{objective.label}</span>
                    <span className={`rounded px-2 py-1 text-xs font-medium ${statusClass(objective.status)}`}>{objective.status}</span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-800">{objective.objective}</p>
                </div>
                <div className="text-right text-sm">
                  <div className="font-semibold">{objective.coverage_score}%</div>
                  <div className="text-xs text-slate-500">{objective.evidence_count} evidence file(s)</div>
                </div>
              </div>

              <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_320px]">
                <div className="space-y-3">
                  {objective.evidence.map((item) => (
                    <EvidenceEditor key={item.support_record_id} item={item} onSave={saveSupport} />
                  ))}
                  {!objective.evidence.length && (
                    <div className="rounded-md bg-muted p-3 text-sm text-slate-600">
                      No evidence has been mapped to this objective yet.
                    </div>
                  )}
                </div>

                <aside className="space-y-3">
                  <div className="rounded-md bg-muted p-3">
                    <h3 className="flex items-center gap-2 text-sm font-semibold"><AlertTriangle size={15} /> Missing Evidence</h3>
                    <ul className="mt-2 space-y-2 text-xs text-slate-700">
                      {(objective.missing_evidence.length ? objective.missing_evidence : ["Upload evidence that directly demonstrates this objective."]).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-md bg-muted p-3">
                    <h3 className="flex items-center gap-2 text-sm font-semibold"><CheckCircle2 size={15} /> Recommendations</h3>
                    <ul className="mt-2 space-y-2 text-xs text-slate-700">
                      {(objective.recommendations.length ? objective.recommendations : ["Map current, scoped, assessor-facing evidence to this objective."]).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </aside>
              </div>
            </section>
          ))}
        </div>
      </section>
    </main>
  );
}
