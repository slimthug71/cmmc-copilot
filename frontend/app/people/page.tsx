"use client";

import { Download, Save, Search, ShieldCheck, Trash2, UserPlus, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, Control, OwnerDashboard, OwnershipCoverage, Person, RoleAssignment } from "@/lib/api";

const emptyPerson: Person = {
  email: "",
  full_name: "",
  role: "user",
  department: "",
  title: "",
  status: "Active",
};

const emptyRole: RoleAssignment = {
  user_id: null,
  person_name: "",
  person_email: "",
  compliance_role: "Control Owner",
  scope_type: "Organization",
  scope_value: "",
  notes: "",
};

const emptyCoverage: OwnershipCoverage = {
  people: 0,
  role_assignments: 0,
  controls_without_owner: 0,
  poam_without_owner: 0,
  evidence_without_owner: 0,
  evidence_without_reviewer: 0,
  documents_without_approver: 0,
  systems_without_owner: 0,
  upcoming_owner_tasks: 0,
  findings: [],
};

const emptyOwnerDashboard: OwnerDashboard = {
  owner: "",
  controls: 0,
  evidence: 0,
  poam_items: 0,
  upcoming_tasks: 0,
  work_items: [],
};

const roleOptions = ["Control Owner", "System Owner", "Data Owner", "IT Owner", "Evidence Owner", "Approver", "Reviewer"];
const scopeOptions = ["Organization", "Family", "Control", "System"];

export default function PeoplePage() {
  const [people, setPeople] = useState<Person[]>([]);
  const [roles, setRoles] = useState<RoleAssignment[]>([]);
  const [controls, setControls] = useState<Control[]>([]);
  const [coverage, setCoverage] = useState<OwnershipCoverage>(emptyCoverage);
  const [personDraft, setPersonDraft] = useState<Person>(emptyPerson);
  const [roleDraft, setRoleDraft] = useState<RoleAssignment>(emptyRole);
  const [query, setQuery] = useState("");
  const [ownerQuery, setOwnerQuery] = useState("");
  const [ownerBoard, setOwnerBoard] = useState<OwnerDashboard>(emptyOwnerDashboard);
  const [status, setStatus] = useState("Loading ownership coverage...");

  async function refresh() {
    const [peopleRows, roleRows, coverageData, controlRows] = await Promise.all([
      api.people(query),
      api.roles(query),
      api.ownershipCoverage(),
      api.controls(),
    ]);
    setPeople(peopleRows);
    setRoles(roleRows);
    setCoverage(coverageData);
    setControls(controlRows);
    setStatus("Ready");
  }

  useEffect(() => {
    refresh().catch(() => setStatus("Start the FastAPI backend on port 8000."));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => refresh().catch(() => setStatus("Start the FastAPI backend on port 8000.")), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  const families = useMemo(() => Array.from(new Set(controls.map((control) => control.family))).sort(), [controls]);
  const selectedPerson = people.find((person) => person.id === roleDraft.user_id);
  const scopeValues = roleDraft.scope_type === "Family" ? families : roleDraft.scope_type === "Control" ? controls.map((control) => control.control_id) : [];

  async function savePerson() {
    setStatus("Saving person...");
    const saved = await api.savePerson(personDraft);
    setPersonDraft(emptyPerson);
    await refresh();
    setStatus(`Saved ${saved.full_name}.`);
  }

  async function saveRole() {
    setStatus("Saving role assignment...");
    const payload = {
      ...roleDraft,
      person_name: roleDraft.person_name || selectedPerson?.full_name || "",
      person_email: roleDraft.person_email || selectedPerson?.email || "",
    };
    const saved = await api.saveRole(payload);
    setRoleDraft(emptyRole);
    await refresh();
    setStatus(`Saved ${saved.compliance_role}.`);
  }

  async function loadOwnerDashboard(owner = ownerQuery) {
    if (!owner.trim()) return;
    setOwnerBoard(await api.ownerDashboard(owner));
  }

  function editPerson(person: Person) {
    setPersonDraft(person);
  }

  function editRole(role: RoleAssignment) {
    setRoleDraft(role);
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">People & Roles</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href={api.responsibilityMatrixExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <Download size={16} />
              Matrix
            </a>
            <a href={api.roleAssignmentsExportUrl()} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <Download size={16} />
              Roles DOCX
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {[
            ["People", coverage.people],
            ["Role Assignments", coverage.role_assignments],
            ["Controls Unowned", coverage.controls_without_owner],
            ["Evidence Needs Reviewer", coverage.evidence_without_reviewer],
            ["Upcoming Owner Tasks", coverage.upcoming_owner_tasks],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-border bg-white p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-slate-500"><Users size={14} />{label}</div>
              <div className="mt-2 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        <section className="mt-5 grid gap-5 lg:grid-cols-[420px_1fr]">
          <div className="space-y-5">
            <section className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Person</h2>
              <div className="mt-4 grid gap-3">
                <input className="h-10 rounded-md border border-border px-3 text-sm" value={personDraft.full_name} onChange={(event) => setPersonDraft({ ...personDraft, full_name: event.target.value })} placeholder="Full name" />
                <input className="h-10 rounded-md border border-border px-3 text-sm" value={personDraft.email} onChange={(event) => setPersonDraft({ ...personDraft, email: event.target.value })} placeholder="Email" />
                <input className="h-10 rounded-md border border-border px-3 text-sm" value={personDraft.department} onChange={(event) => setPersonDraft({ ...personDraft, department: event.target.value })} placeholder="Department" />
                <input className="h-10 rounded-md border border-border px-3 text-sm" value={personDraft.title} onChange={(event) => setPersonDraft({ ...personDraft, title: event.target.value })} placeholder="Title" />
                <div className="grid grid-cols-2 gap-3">
                  <select className="h-10 rounded-md border border-border px-3 text-sm" value={personDraft.role} onChange={(event) => setPersonDraft({ ...personDraft, role: event.target.value })}>
                    <option>admin</option>
                    <option>user</option>
                    <option>approver</option>
                    <option>reviewer</option>
                  </select>
                  <select className="h-10 rounded-md border border-border px-3 text-sm" value={personDraft.status} onChange={(event) => setPersonDraft({ ...personDraft, status: event.target.value })}>
                    <option>Active</option>
                    <option>Inactive</option>
                  </select>
                </div>
                <button onClick={savePerson} className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                  <UserPlus size={16} />
                  Save Person
                </button>
              </div>
            </section>

            <section className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Role Assignment</h2>
              <div className="mt-4 grid gap-3">
                <select className="h-10 rounded-md border border-border px-3 text-sm" value={roleDraft.user_id ?? ""} onChange={(event) => setRoleDraft({ ...roleDraft, user_id: event.target.value ? Number(event.target.value) : null })}>
                  <option value="">Unlinked person</option>
                  {people.map((person) => <option key={person.id} value={person.id}>{person.full_name} - {person.email}</option>)}
                </select>
                <div className="grid grid-cols-2 gap-3">
                  <input className="h-10 rounded-md border border-border px-3 text-sm" value={roleDraft.person_name || selectedPerson?.full_name || ""} onChange={(event) => setRoleDraft({ ...roleDraft, person_name: event.target.value })} placeholder="Person name" />
                  <input className="h-10 rounded-md border border-border px-3 text-sm" value={roleDraft.person_email || selectedPerson?.email || ""} onChange={(event) => setRoleDraft({ ...roleDraft, person_email: event.target.value })} placeholder="Person email" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <select className="h-10 rounded-md border border-border px-3 text-sm" value={roleDraft.compliance_role} onChange={(event) => setRoleDraft({ ...roleDraft, compliance_role: event.target.value })}>
                    {roleOptions.map((item) => <option key={item}>{item}</option>)}
                  </select>
                  <select className="h-10 rounded-md border border-border px-3 text-sm" value={roleDraft.scope_type} onChange={(event) => setRoleDraft({ ...roleDraft, scope_type: event.target.value, scope_value: "" })}>
                    {scopeOptions.map((item) => <option key={item}>{item}</option>)}
                  </select>
                </div>
                {scopeValues.length ? (
                  <select className="h-10 rounded-md border border-border px-3 text-sm" value={roleDraft.scope_value} onChange={(event) => setRoleDraft({ ...roleDraft, scope_value: event.target.value })}>
                    <option value="">Select {roleDraft.scope_type.toLowerCase()}</option>
                    {scopeValues.map((item) => <option key={item}>{item}</option>)}
                  </select>
                ) : (
                  <input className="h-10 rounded-md border border-border px-3 text-sm" value={roleDraft.scope_value} onChange={(event) => setRoleDraft({ ...roleDraft, scope_value: event.target.value })} placeholder="Scope value" />
                )}
                <textarea className="min-h-20 rounded-md border border-border px-3 py-2 text-sm" value={roleDraft.notes} onChange={(event) => setRoleDraft({ ...roleDraft, notes: event.target.value })} placeholder="Notes" />
                <button onClick={saveRole} className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                  <Save size={16} />
                  Save Assignment
                </button>
              </div>
            </section>
          </div>

          <div className="space-y-5">
            <section className="rounded-md border border-border bg-white p-4">
              <div className="grid gap-3 lg:grid-cols-[1fr_260px]">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                  <input className="h-10 w-full rounded-md border border-border pl-9 pr-3 text-sm" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search people and roles" />
                </div>
                <div className="flex gap-2">
                  <input className="h-10 min-w-0 flex-1 rounded-md border border-border px-3 text-sm" value={ownerQuery} onChange={(event) => setOwnerQuery(event.target.value)} placeholder="Owner dashboard" />
                  <button onClick={() => loadOwnerDashboard()} className="inline-flex h-10 items-center justify-center rounded-md border border-border bg-white px-3"><Search size={16} /></button>
                </div>
              </div>
            </section>

            <section className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Ownership Findings</h2>
              <div className="mt-3 grid gap-2 text-sm text-slate-700">
                {coverage.findings.map((finding) => <div key={finding} className="rounded-md bg-slate-50 p-3">{finding}</div>)}
              </div>
            </section>

            <section className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">People</h2>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="border-b border-border text-xs uppercase text-slate-500">
                    <tr><th className="py-2">Name</th><th className="py-2">Email</th><th className="py-2">Department</th><th className="py-2">Title</th><th className="py-2">Status</th><th className="py-2">Actions</th></tr>
                  </thead>
                  <tbody>
                    {people.map((person) => (
                      <tr key={person.id} className="border-b border-border">
                        <td className="py-3 font-medium">{person.full_name}</td>
                        <td className="py-3">{person.email}</td>
                        <td className="py-3">{person.department || "-"}</td>
                        <td className="py-3">{person.title || "-"}</td>
                        <td className="py-3">{person.status}</td>
                        <td className="py-3">
                          <div className="flex gap-2">
                            <button onClick={() => editPerson(person)} className="inline-flex h-8 items-center rounded-md border border-border px-2 text-xs">Edit</button>
                            {person.id && <button onClick={async () => { await api.deletePerson(person.id!); await refresh(); }} className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border"><Trash2 size={14} /></button>}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!people.length && <tr><td colSpan={6} className="py-5 text-slate-600">No people match the current search.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-md border border-border bg-white p-4">
              <h2 className="text-base font-semibold">Role Assignments</h2>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-[900px] text-left text-sm">
                  <thead className="border-b border-border text-xs uppercase text-slate-500">
                    <tr><th className="py-2">Role</th><th className="py-2">Person</th><th className="py-2">Scope</th><th className="py-2">Notes</th><th className="py-2">Actions</th></tr>
                  </thead>
                  <tbody>
                    {roles.map((role) => (
                      <tr key={role.id} className="border-b border-border align-top">
                        <td className="py-3 font-medium">{role.compliance_role}</td>
                        <td className="py-3">{role.person_name || role.person_email || "Unassigned"}<div className="text-xs text-slate-500">{role.person_email}</div></td>
                        <td className="py-3">{role.scope_type} {role.scope_value}</td>
                        <td className="py-3">{role.notes || "-"}</td>
                        <td className="py-3">
                          <div className="flex gap-2">
                            <button onClick={() => editRole(role)} className="inline-flex h-8 items-center rounded-md border border-border px-2 text-xs">Edit</button>
                            {role.id && <button onClick={async () => { await api.deleteRole(role.id!); await refresh(); }} className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border"><Trash2 size={14} /></button>}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!roles.length && <tr><td colSpan={5} className="py-5 text-slate-600">No role assignments exist yet.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            {ownerBoard.owner && (
              <section className="rounded-md border border-border bg-white p-4">
                <h2 className="text-base font-semibold">{ownerBoard.owner} Work Queue</h2>
                <div className="mt-3 grid gap-3 sm:grid-cols-4">
                  {[["Controls", ownerBoard.controls], ["Evidence", ownerBoard.evidence], ["POA&M", ownerBoard.poam_items], ["Tasks", ownerBoard.upcoming_tasks]].map(([label, value]) => (
                    <div key={label} className="rounded-md bg-slate-50 p-3"><div className="text-xs uppercase text-slate-500">{label}</div><div className="text-xl font-semibold">{value}</div></div>
                  ))}
                </div>
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full min-w-[760px] text-left text-sm">
                    <thead className="border-b border-border text-xs uppercase text-slate-500">
                      <tr><th className="py-2">Type</th><th className="py-2">Item</th><th className="py-2">Status</th><th className="py-2">Due</th><th className="py-2">Control</th><th className="py-2">Open</th></tr>
                    </thead>
                    <tbody>
                      {ownerBoard.work_items.map((item, index) => (
                        <tr key={`${item.item_type}-${index}`} className="border-b border-border">
                          <td className="py-3">{item.item_type}</td>
                          <td className="py-3">{item.title}</td>
                          <td className="py-3">{item.status}</td>
                          <td className="py-3">{item.due_date || "-"}</td>
                          <td className="py-3">{item.control_id || "-"}</td>
                          <td className="py-3"><a href={item.link || "/calendar"} className="font-medium text-primary">Open</a></td>
                        </tr>
                      ))}
                      {!ownerBoard.work_items.length && <tr><td colSpan={6} className="py-5 text-slate-600">No work items found for this owner.</td></tr>}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}
