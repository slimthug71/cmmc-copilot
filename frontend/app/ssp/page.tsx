"use client";

import { Download, FileArchive, FileText, Save, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";
import { api, CompanyProfile, SSPDocument, SSPSection, SystemProfile } from "@/lib/api";

const defaultProfile: CompanyProfile = {
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

const defaultSystem: SystemProfile = {
  system_name: "CUI Processing Environment",
  system_owner: "IT/Security Owner",
  data_owner: "Contracts Data Owner",
  business_function: "Supports contract execution, engineering collaboration, and CUI document handling.",
  description: "The system includes managed endpoints, Microsoft 365 GCC High collaboration services, identity services, backup, monitoring, and support workflows used by authorized personnel.",
  boundary_description: "The boundary includes managed Windows endpoints, Microsoft 365 GCC High, Entra ID, Intune, Defender, backup services, remote users, and approved external providers supporting CUI operations.",
  cui_description: "CUI consists of contract documents, technical data, controlled project communications, and related records stored in approved repositories.",
  infrastructure: "Microsoft 365 GCC High; Azure Government; managed Windows endpoints; remote users",
  security_stack: "Entra ID; Intune; Defender; Sentinel",
  external_providers: "MSP; Cloud Provider; Backup Vendor",
  cui_created: "CUI is created by authorized employees during contract, engineering, and project support activities.",
  cui_stored: "CUI is stored in GCC High SharePoint libraries and approved managed endpoints.",
  cui_transmitted: "CUI is transmitted through approved encrypted collaboration and email channels.",
  cui_archived: "CUI is archived in approved backup and retention repositories.",
};

const profileFields: Array<[keyof CompanyProfile, string]> = [
  ["company_name", "Company Name"],
  ["industry", "Industry"],
  ["employee_count", "Employee Count"],
  ["locations", "Locations"],
  ["cloud_environment", "Cloud Environment"],
  ["cui_environment", "CUI Environment"],
  ["msp_involvement", "MSP Involvement"],
  ["mfa_solution", "MFA Solution"],
  ["endpoint_management", "Endpoint Management"],
  ["backup_solution", "Backup Solution"],
  ["ticketing_system", "Ticketing System"],
  ["hr_onboarding_process", "HR Onboarding Process"],
  ["access_removal_process", "Access Removal Process"],
];

const systemFields: Array<[keyof SystemProfile, string]> = [
  ["system_name", "System Name"],
  ["system_owner", "System Owner"],
  ["data_owner", "Data Owner"],
  ["business_function", "Business Function"],
  ["description", "System Description"],
  ["boundary_description", "System Boundary"],
  ["cui_description", "CUI Environment"],
  ["infrastructure", "Infrastructure"],
  ["security_stack", "Security Stack"],
  ["external_providers", "External Providers"],
  ["cui_created", "CUI Created"],
  ["cui_stored", "CUI Stored"],
  ["cui_transmitted", "CUI Transmitted"],
  ["cui_archived", "CUI Archived"],
];

export default function SSPPage() {
  const [profile, setProfile] = useState<CompanyProfile>(defaultProfile);
  const [system, setSystem] = useState<SystemProfile>(defaultSystem);
  const [ssp, setSsp] = useState<SSPDocument | null>(null);
  const [activeSectionId, setActiveSectionId] = useState<number | null>(null);
  const [status, setStatus] = useState("Ready");

  async function generateSSP() {
    setStatus("Saving profile and generating SSP...");
    const savedProfile = await api.createProfile(profile);
    const savedSystem = await api.createSystem(system);
    const generated = await api.generateSSP(savedProfile.id ?? 0, savedSystem.id ?? 0);
    setSsp(generated);
    setActiveSectionId(generated.sections[0]?.id ?? null);
    setStatus(`Generated SSP with ${generated.completeness_score}% completeness.`);
  }

  async function saveSection(section: SSPSection) {
    const saved = await api.saveSSPSection(section);
    if (!ssp) return;
    setSsp({ ...ssp, sections: ssp.sections.map((item) => (item.id === saved.id ? saved : item)) });
    setStatus(`Saved ${saved.section_name}.`);
  }

  const activeSection = ssp?.sections.find((section) => section.id === (activeSectionId ?? ssp.sections[0]?.id));

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">SSP Builder</h1>
            <p className="text-sm text-slate-600">{status}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="/" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <ShieldCheck size={16} />
              Controls
            </a>
            <a href="/evidence" className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
              <FileArchive size={16} />
              Evidence
            </a>
            <button onClick={generateSSP} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
              <Sparkles size={16} />
              Generate SSP
            </button>
            {ssp && (
              <>
                <a href={api.sspExportUrl(ssp.id, "docx")} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                  <FileText size={16} />
                  SSP Word
                </a>
                <a href={api.sspExportUrl(ssp.id, "pdf")} className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white">
                  <Download size={16} />
                  SSP PDF
                </a>
                <a href={api.poamExportUrl(ssp.id)} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                  <Download size={16} />
                  POA&M Excel
                </a>
                <a href={api.continuousMonitoringExportUrl(ssp.id)} className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-white px-4 text-sm font-medium">
                  <FileText size={16} />
                  Monitoring Word
                </a>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-5 px-6 py-6 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-5">
          {ssp && (
            <div className="rounded-md border border-border bg-white p-4">
              <div className="text-xs font-medium uppercase text-slate-500">Completeness</div>
              <div className="mt-2 text-3xl font-semibold">{ssp.completeness_score}%</div>
              <div className="mt-1 text-sm text-slate-600">Version {ssp.version} - {ssp.status}</div>
            </div>
          )}

          <div className="rounded-md border border-border bg-white p-4">
            <h2 className="text-base font-semibold">System Profile</h2>
            <div className="mt-4 space-y-3">
              {systemFields.map(([key, label]) => (
                <label key={key} className="block">
                  <span className="text-xs font-medium text-slate-600">{label}</span>
                  <textarea
                    className="mt-1 min-h-10 w-full resize-y rounded-md border border-border px-3 py-2 text-sm outline-none focus:border-primary"
                    value={String(system[key] ?? "")}
                    onChange={(event) => setSystem({ ...system, [key]: event.target.value })}
                    rows={["description", "boundary_description", "cui_description", "infrastructure", "security_stack", "external_providers"].includes(key) ? 3 : 2}
                  />
                </label>
              ))}
            </div>
          </div>

          <div className="rounded-md border border-border bg-white p-4">
            <h2 className="text-base font-semibold">Company Profile</h2>
            <div className="mt-4 space-y-3">
              {profileFields.map(([key, label]) => (
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
            </div>
          </div>
        </aside>

        <div className="min-w-0 rounded-md border border-border bg-white p-5">
          {ssp && activeSection ? (
            <div className="grid gap-5 xl:grid-cols-[260px_1fr]">
              <nav className="space-y-2">
                {ssp.sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSectionId(section.id)}
                    className={`w-full rounded-md px-3 py-2 text-left text-sm ${activeSection.id === section.id ? "bg-primary text-white" : "bg-muted text-slate-700"}`}
                  >
                    {section.section_name}
                  </button>
                ))}
              </nav>
              <section>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-lg font-semibold">{activeSection.section_name}</h2>
                  <button onClick={() => saveSection(activeSection)} className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-white px-3 text-sm font-medium">
                    <Save size={15} />
                    Save Section
                  </button>
                </div>
                <textarea
                  className="mt-4 min-h-[calc(100vh-220px)] w-full rounded-md border border-border p-4 text-sm leading-6 outline-none focus:border-primary"
                  value={activeSection.section_content}
                  onChange={(event) =>
                    setSsp({
                      ...ssp,
                      sections: ssp.sections.map((section) =>
                        section.id === activeSection.id ? { ...section, section_content: event.target.value } : section
                      ),
                    })
                  }
                />
              </section>
            </div>
          ) : (
            <div className="rounded-md bg-muted p-5 text-sm leading-6 text-slate-700">
              Generate an SSP to edit system identification, boundary, users, external providers, CUI flow, network architecture, control implementations, continuous monitoring, POA&M references, and quality checks. The SSP exports separately from the POA&M Excel workbook and Continuous Monitoring Word document.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
