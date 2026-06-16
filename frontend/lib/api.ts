export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export type CompanyProfile = {
  id?: number;
  company_name: string;
  industry: string;
  employee_count: string;
  locations: string;
  cloud_environment: string;
  cui_environment: string;
  msp_involvement: string;
  mfa_solution: string;
  endpoint_management: string;
  backup_solution: string;
  ticketing_system: string;
  hr_onboarding_process: string;
  access_removal_process: string;
};

export type Control = {
  id: number;
  control_id: string;
  family: string;
  title: string;
  requirement: string;
  objectives: string[];
  evidence: string[];
};

export type GeneratedOutput = {
  id: number;
  control_id: string;
  implementation_statement: string;
  responsible_parties: string;
  evidence_artifacts: string;
  assessment_notes: string;
  gaps_assumptions: string;
};

export type DocumentOutput = {
  id: number;
  document_type: "policy" | "procedure";
  control_id: string;
  name: string;
  text: string;
  responsibility_matrix: string;
  version: string;
  author: string;
  approver: string;
  approval_date: string;
  review_date: string;
  status: string;
};

export type SystemProfile = {
  id?: number;
  system_name: string;
  system_owner: string;
  data_owner: string;
  business_function: string;
  description: string;
  boundary_description: string;
  cui_description: string;
  infrastructure: string;
  security_stack: string;
  external_providers: string;
  cui_created: string;
  cui_stored: string;
  cui_transmitted: string;
  cui_archived: string;
};

export type SSPSection = {
  id: number;
  section_name: string;
  section_content: string;
  sort_order: number;
};

export type SSPDocument = {
  id: number;
  system_id: number;
  version: string;
  status: string;
  completeness_score: number;
  sections: SSPSection[];
};

export type EvidenceObjective = {
  id: number;
  objective: string;
  supported: string;
  notes: string;
};

export type EvidenceAnalysis = {
  id: number;
  control_id: string;
  control_title: string;
  confidence_score: number;
  coverage_score: number;
  assessment_strength: string;
  missing_evidence: string[];
  recommendations: string[];
  assessor_observations: string;
  objectives: EvidenceObjective[];
};

export type EvidenceItem = {
  id: number;
  title: string;
  file_name: string;
  file_type: string;
  document_type: string;
  data_classification: string;
  contains_cui: string;
  contains_itar: string;
  contains_pii: string;
  intended_control_id: string;
  managed_poam_id: number | null;
  evidence_request_id: number | null;
  evidence_type: string;
  owner: string;
  status: string;
  review_status: string;
  reviewer: string;
  review_date: string;
  review_notes: string;
  drift_state: string;
  uploaded_by: string;
  uploaded_at: string;
  analyses: EvidenceAnalysis[];
};

export type EvidenceDashboard = {
  evidence_uploaded: number;
  controls_with_evidence: number;
  total_controls: number;
  objectives_with_evidence: number;
  total_objectives: number;
  objective_coverage_score: number;
  average_coverage: number;
  missing_evidence: number;
  strong_evidence: number;
  weak_evidence: number;
  uploaded_evidence: number;
  under_review_evidence: number;
  accepted_evidence: number;
  needs_replacement_evidence: number;
  rejected_evidence: number;
  stale_evidence: number;
  objectives_at_risk: number;
  controls_at_risk: number;
  assessment_readiness_score: number;
};

export type ControlCoverage = {
  control_id: string;
  title: string;
  family: string;
  evidence_count: number;
  coverage_score: number;
  objective_coverage_score: number;
  objectives_with_evidence: number;
  partially_supported_objectives: number;
  total_objectives: number;
  confidence_score: number;
  assessment_strength: string;
  drift_state: string;
};

export type ControlMapping = {
  control_id: string;
  control_title: string;
  mapping_type: string;
  confidence_score: number;
  rationale: string;
};

export type DocumentEntity = {
  entity_type: string;
  entity_value: string;
  source_excerpt: string;
};

export type ComplianceDocument = {
  id: number;
  title: string;
  document_type: string;
  data_classification: string;
  contains_cui: string;
  contains_itar: string;
  contains_pii: string;
  file_name: string;
  file_type: string;
  version: string;
  owner: string;
  review_date: string;
  status: string;
  uploaded_at: string;
  mappings: ControlMapping[];
  entities: DocumentEntity[];
};

export type ComplianceGraph = {
  documents: number;
  mapped_controls: number;
  policies: number;
  procedures: number;
  ssp_documents: number;
  poam_documents: number;
  entities: Record<string, number>;
  recent_alerts: string[];
};

export type ComplianceSearchResult = {
  result_type: string;
  title: string;
  subtitle: string;
  excerpt: string;
};

export type ComplianceReadiness = {
  documentation_score: number;
  evidence_score: number;
  poam_score: number;
  overall_score: number;
  findings: string[];
};

export type ComplianceChat = {
  answer: string;
  sources: string[];
};

export type ControlEvidenceSource = {
  id: number;
  evidence_name: string;
  source_type: string;
  connected_system: string;
  collection_method: string;
  review_frequency: string;
  required: string;
  description: string;
};

export type MonitoringRule = {
  id: number;
  rule_name: string;
  source_system: string;
  condition: string;
  severity: string;
  enabled: string;
};

export type DriftAlert = {
  id: number;
  control_id: string;
  control_title: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  recommended_action: string;
  status: string;
  created_at: string;
};

export type ControlEvidenceMap = {
  control_id: string;
  control_title: string;
  family: string;
  status: string;
  evidence_count: number;
  required_sources: number;
  connected_sources: number;
  manual_sources: number;
  open_alerts: number;
  review_frequency: string;
  evidence_sources: ControlEvidenceSource[];
  monitoring_rules: MonitoringRule[];
};

export type CopilotDashboard = {
  overall_readiness: number;
  healthy_controls: number;
  at_risk_controls: number;
  partially_implemented_controls: number;
  not_implemented_controls: number;
  open_alerts: number;
  automated_sources: number;
  manual_sources: number;
  mapped_controls: number;
  total_controls: number;
  recent_alerts: DriftAlert[];
};

export type AssessmentSimulation = {
  control_id: string;
  assessment_question: string;
  assessment_status: string;
  evidence_reviewed: string[];
  missing: string[];
  assessor_feedback: string;
  recommended_next_steps: string[];
};

export type ControlGraphItem = {
  id: string;
  name: string;
  item_type: string;
  source: string;
  status: string;
  detail: string;
};

export type ControlGraph = {
  control_id: string;
  control_title: string;
  family: string;
  requirement: string;
  status: string;
  policies: ControlGraphItem[];
  procedures: ControlGraphItem[];
  ssp_references: ControlGraphItem[];
  evidence: ControlGraphItem[];
  poam_items: ControlGraphItem[];
  alerts: DriftAlert[];
  evidence_sources: ControlEvidenceSource[];
  monitoring_rules: MonitoringRule[];
};

export type ObjectiveEvidenceItem = {
  evidence_id: number;
  evidence_title: string;
  file_name: string;
  evidence_type: string;
  support_record_id: number;
  supported: string;
  notes: string;
  coverage_score: number;
  confidence_score: number;
};

export type ControlObjective = {
  id: number;
  label: string;
  objective: string;
  status: string;
  evidence_count: number;
  coverage_score: number;
  missing_evidence: string[];
  recommendations: string[];
  assessor_notes: string;
  evidence: ObjectiveEvidenceItem[];
};

export type ControlObjectiveWorkspace = {
  control_id: string;
  control_title: string;
  family: string;
  requirement: string;
  readiness_score: number;
  supported_objectives: number;
  partial_objectives: number;
  total_objectives: number;
  objectives: ControlObjective[];
};

export type ControlHealthRow = {
  control_id: string;
  title: string;
  family: string;
  objective_coverage_score: number;
  objectives_with_evidence: number;
  total_objectives: number;
  accepted_evidence: number;
  under_review_evidence: number;
  needs_replacement_evidence: number;
  rejected_evidence: number;
  stale_evidence: number;
  poam_candidates: number;
  drift_state: string;
  health_status: string;
};

export type ControlHealthDashboard = {
  healthy_controls: number;
  monitor_controls: number;
  at_risk_controls: number;
  critical_controls: number;
  stale_evidence: number;
  poam_candidates: number;
  rows: ControlHealthRow[];
};

export type ManagedPoamItem = {
  id: number;
  control_id: string;
  control_title: string;
  objective_label: string;
  objective: string;
  gap_statement: string;
  evidence_needed: string;
  corrective_action: string;
  owner: string;
  due_date: string;
  risk: string;
  status: string;
  notes: string;
  created_at: string;
  updated_at: string;
};

export type ManagedPoamGenerateResult = {
  created: number;
  existing: number;
  total_open: number;
};

export type AuditLogItem = {
  id: number;
  action: string;
  entity_type: string;
  entity_id: string;
  user_name: string;
  control_id: string;
  details: string;
  created_at: string;
};

export type ComplianceTask = {
  id: string;
  task_type: string;
  title: string;
  owner: string;
  due_date: string;
  status: string;
  control_id: string;
  entity_type: string;
  entity_id: string;
  detail: string;
  link: string;
};

export type ComplianceCalendar = {
  overdue: number;
  due_soon: number;
  upcoming: number;
  unscheduled: number;
  completed: number;
  tasks: ComplianceTask[];
};

export type AssessmentPackageControl = {
  control_id: string;
  title: string;
  family: string;
  readiness_score: number;
  implementation_status: string;
  policy_status: string;
  procedure_status: string;
  accepted_evidence: number;
  evidence_total: number;
  open_poam: number;
  stale_evidence: number;
  warnings: string[];
};

export type AssessmentPackageSummary = {
  scope: string;
  total_controls: number;
  ready_controls: number;
  warning_controls: number;
  missing_implementation: number;
  missing_policy: number;
  missing_procedure: number;
  controls_without_accepted_evidence: number;
  open_poam_items: number;
  stale_evidence: number;
  completeness_score: number;
  controls: AssessmentPackageControl[];
};

export type Person = {
  id?: number;
  email: string;
  full_name: string;
  role: string;
  department: string;
  title: string;
  status: string;
};

export type RoleAssignment = {
  id?: number;
  user_id: number | null;
  person_name: string;
  person_email: string;
  compliance_role: string;
  scope_type: string;
  scope_value: string;
  notes: string;
};

export type OwnershipCoverage = {
  people: number;
  role_assignments: number;
  controls_without_owner: number;
  poam_without_owner: number;
  evidence_without_owner: number;
  evidence_without_reviewer: number;
  documents_without_approver: number;
  systems_without_owner: number;
  upcoming_owner_tasks: number;
  findings: string[];
};

export type OwnerWorkItem = {
  item_type: string;
  title: string;
  owner: string;
  status: string;
  due_date: string;
  control_id: string;
  link: string;
};

export type OwnerDashboard = {
  owner: string;
  controls: number;
  evidence: number;
  poam_items: number;
  upcoming_tasks: number;
  work_items: OwnerWorkItem[];
};

export type ControlReview = {
  id: number | null;
  control_id: string;
  control_title: string;
  family: string;
  review_status: string;
  reviewer: string;
  approver: string;
  review_notes: string;
  signoff_date: string;
  next_review_date: string;
  package_readiness_score: number;
  warnings: string[];
  updated_at: string;
};

export type ControlReviewDashboard = {
  total_controls: number;
  not_started: number;
  in_review: number;
  approved: number;
  rejected: number;
  due_soon: number;
  overdue: number;
  rows: ControlReview[];
};

export type EvidenceRequest = {
  id: number;
  control_id: string;
  objective_label: string;
  request_title: string;
  evidence_needed: string;
  requested_from: string;
  due_date: string;
  priority: string;
  status: string;
  source_type: string;
  source_id: string;
  notes: string;
  linked_evidence_count: number;
  accepted_evidence_count: number;
  created_at: string;
  updated_at: string;
};

export type EvidenceRequestDashboard = {
  total: number;
  draft: number;
  sent: number;
  submitted: number;
  accepted: number;
  rejected: number;
  overdue: number;
  rows: EvidenceRequest[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export const api = {
  dashboard: () => request<Record<string, number>>("/api/dashboard"),
  controls: () => request<Control[]>("/api/controls"),
  control: (id: string) => request<Control>(`/api/controls/${id}`),
  createProfile: (profile: CompanyProfile) =>
    request<CompanyProfile>("/api/company-profiles", { method: "POST", body: JSON.stringify(profile) }),
  generate: (company_profile_id: number, control_id: string) =>
    request<GeneratedOutput>("/api/generate", { method: "POST", body: JSON.stringify({ company_profile_id, control_id }) }),
  saveOutput: (id: number, output: GeneratedOutput) =>
    request<GeneratedOutput>(`/api/outputs/${id}`, { method: "PUT", body: JSON.stringify(output) }),
  exportUrl: (id: number, kind: "docx" | "pdf") => `${API_BASE}/api/outputs/${id}/export/${kind}`,
  generatePolicy: (company_profile_id: number, control_id: string) =>
    request<DocumentOutput>("/api/documents/policies/generate", { method: "POST", body: JSON.stringify({ company_profile_id, control_id }) }),
  generateProcedure: (company_profile_id: number, control_id: string) =>
    request<DocumentOutput>("/api/documents/procedures/generate", { method: "POST", body: JSON.stringify({ company_profile_id, control_id }) }),
  saveDocument: (document: DocumentOutput) =>
    request<DocumentOutput>(`/api/documents/${document.document_type}/${document.id}`, { method: "PUT", body: JSON.stringify(document) }),
  documentExportUrl: (document: DocumentOutput, kind: "docx" | "pdf") => `${API_BASE}/api/documents/${document.document_type}/${document.id}/export/${kind}`,
  createSystem: (system: SystemProfile) =>
    request<SystemProfile>("/api/systems", { method: "POST", body: JSON.stringify(system) }),
  generateSSP: (company_profile_id: number, system_id: number) =>
    request<SSPDocument>("/api/ssp/generate", { method: "POST", body: JSON.stringify({ company_profile_id, system_id }) }),
  saveSSPSection: (section: SSPSection) =>
    request<SSPSection>(`/api/ssp/sections/${section.id}`, { method: "PUT", body: JSON.stringify({ section_content: section.section_content }) }),
  sspExportUrl: (sspId: number, kind: "docx" | "pdf") => `${API_BASE}/api/ssp/${sspId}/export/${kind}`,
  poamExportUrl: (sspId: number) => `${API_BASE}/api/ssp/${sspId}/export/poam/xlsx`,
  continuousMonitoringExportUrl: (sspId: number) => `${API_BASE}/api/ssp/${sspId}/export/continuous-monitoring/docx`,
  evidenceDashboard: () => request<EvidenceDashboard>("/api/evidence/dashboard"),
  evidence: (q = "", controlId = "", reviewStatus = "", driftState = "", managedPoamId?: number, evidenceRequestId?: number) =>
    request<EvidenceItem[]>(`/api/evidence?q=${encodeURIComponent(q)}&control_id=${encodeURIComponent(controlId)}&review_status=${encodeURIComponent(reviewStatus)}&drift_state=${encodeURIComponent(driftState)}${managedPoamId === undefined ? "" : `&managed_poam_id=${managedPoamId}`}${evidenceRequestId === undefined ? "" : `&evidence_request_id=${evidenceRequestId}`}`),
  uploadEvidence: (payload: { file_name: string; content_base64: string; document_type?: string; data_classification?: string; contains_cui?: boolean; contains_itar?: boolean; contains_pii?: boolean; title?: string; owner?: string; control_id?: string; managed_poam_id?: number; evidence_request_id?: number }) =>
    request<EvidenceItem>("/api/evidence/upload", { method: "POST", body: JSON.stringify(payload) }),
  replaceEvidence: (id: number, payload: { file_name: string; content_base64: string; document_type?: string; data_classification?: string; contains_cui?: boolean; contains_itar?: boolean; contains_pii?: boolean; title?: string; owner?: string; control_id?: string; managed_poam_id?: number; evidence_request_id?: number }) =>
    request<EvidenceItem>(`/api/evidence/${id}/replace`, { method: "PUT", body: JSON.stringify(payload) }),
  reviewEvidence: (id: number, payload: { review_status: string; reviewer?: string; review_notes?: string }) =>
    request<EvidenceItem>(`/api/evidence/${id}/review`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteEvidence: (id: number) => request<{ status: string }>(`/api/evidence/${id}`, { method: "DELETE" }),
  evidenceCoverage: () => request<ControlCoverage[]>("/api/evidence/control-coverage"),
  evidencePackageExportUrl: () => `${API_BASE}/api/evidence/package/export/docx`,
  objectiveMatrixExportUrl: () => `${API_BASE}/api/evidence/objective-matrix/export/xlsx`,
  poamItems: (q = "", status = "", risk = "", controlId = "") =>
    request<ManagedPoamItem[]>(`/api/poam?q=${encodeURIComponent(q)}&status=${encodeURIComponent(status)}&risk=${encodeURIComponent(risk)}&control_id=${encodeURIComponent(controlId)}`),
  generatePoamItems: () => request<ManagedPoamGenerateResult>("/api/poam/generate", { method: "POST" }),
  savePoamItem: (item: ManagedPoamItem) =>
    request<ManagedPoamItem>(`/api/poam/${item.id}`, { method: "PUT", body: JSON.stringify(item) }),
  managedPoamExportUrl: () => `${API_BASE}/api/poam/export/xlsx`,
  auditLogs: (q = "", action = "", entityType = "", entityId = "", controlId = "", userName = "") =>
    request<AuditLogItem[]>(`/api/audit?q=${encodeURIComponent(q)}&action=${encodeURIComponent(action)}&entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}&control_id=${encodeURIComponent(controlId)}&user_name=${encodeURIComponent(userName)}`),
  auditExportUrl: () => `${API_BASE}/api/audit/export/xlsx`,
  calendar: (q = "", status = "", taskType = "", owner = "", controlId = "") =>
    request<ComplianceCalendar>(`/api/calendar?q=${encodeURIComponent(q)}&status=${encodeURIComponent(status)}&task_type=${encodeURIComponent(taskType)}&owner=${encodeURIComponent(owner)}&control_id=${encodeURIComponent(controlId)}`),
  calendarExportUrl: () => `${API_BASE}/api/calendar/export/xlsx`,
  assessmentPackage: (scope = "all", value = "", q = "") =>
    request<AssessmentPackageSummary>(`/api/assessment-package/summary?scope=${encodeURIComponent(scope)}&value=${encodeURIComponent(value)}&q=${encodeURIComponent(q)}`),
  assessmentPackageExportUrl: (kind: "docx" | "pdf", scope = "all", value = "", includeDocuments = true, includeEvidence = true, includePoam = true, includeWarnings = true) =>
    `${API_BASE}/api/assessment-package/export/${kind}?scope=${encodeURIComponent(scope)}&value=${encodeURIComponent(value)}&include_documents=${includeDocuments}&include_evidence=${includeEvidence}&include_poam=${includePoam}&include_warnings=${includeWarnings}`,
  assessmentPackageMatrixExportUrl: (scope = "all", value = "") =>
    `${API_BASE}/api/assessment-package/export/matrix/xlsx?scope=${encodeURIComponent(scope)}&value=${encodeURIComponent(value)}`,
  people: (q = "") => request<Person[]>(`/api/people?q=${encodeURIComponent(q)}`),
  savePerson: (person: Person) =>
    request<Person>(person.id ? `/api/people/${person.id}` : "/api/people", { method: person.id ? "PUT" : "POST", body: JSON.stringify(person) }),
  deletePerson: (id: number) => request<{ status: string }>(`/api/people/${id}`, { method: "DELETE" }),
  roles: (q = "") => request<RoleAssignment[]>(`/api/roles?q=${encodeURIComponent(q)}`),
  saveRole: (assignment: RoleAssignment) =>
    request<RoleAssignment>(assignment.id ? `/api/roles/${assignment.id}` : "/api/roles", { method: assignment.id ? "PUT" : "POST", body: JSON.stringify(assignment) }),
  deleteRole: (id: number) => request<{ status: string }>(`/api/roles/${id}`, { method: "DELETE" }),
  ownershipCoverage: () => request<OwnershipCoverage>("/api/ownership/coverage"),
  ownerDashboard: (owner: string) => request<OwnerDashboard>(`/api/ownership/owner-dashboard?owner=${encodeURIComponent(owner)}`),
  responsibilityMatrixExportUrl: () => `${API_BASE}/api/ownership/export/matrix/xlsx`,
  roleAssignmentsExportUrl: () => `${API_BASE}/api/ownership/export/roles/docx`,
  controlReviews: (q = "", family = "", status = "") =>
    request<ControlReviewDashboard>(`/api/control-reviews?q=${encodeURIComponent(q)}&family=${encodeURIComponent(family)}&status=${encodeURIComponent(status)}`),
  controlReview: (controlId: string) => request<ControlReview>(`/api/control-reviews/${controlId}`),
  saveControlReview: (controlId: string, payload: { review_status: string; reviewer?: string; approver?: string; review_notes?: string; signoff_date?: string; next_review_date?: string }) =>
    request<ControlReview>(`/api/control-reviews/${controlId}`, { method: "PUT", body: JSON.stringify(payload) }),
  controlReviewRegisterExportUrl: () => `${API_BASE}/api/control-reviews/export/xlsx`,
  controlReviewMemoExportUrl: (controlId: string) => `${API_BASE}/api/control-reviews/${controlId}/export/docx`,
  evidenceRequests: (q = "", status = "", controlId = "", owner = "") =>
    request<EvidenceRequestDashboard>(`/api/evidence-requests?q=${encodeURIComponent(q)}&status=${encodeURIComponent(status)}&control_id=${encodeURIComponent(controlId)}&owner=${encodeURIComponent(owner)}`),
  saveEvidenceRequest: (requestItem: Partial<EvidenceRequest>) =>
    request<EvidenceRequest>(requestItem.id ? `/api/evidence-requests/${requestItem.id}` : "/api/evidence-requests", { method: requestItem.id ? "PUT" : "POST", body: JSON.stringify(requestItem) }),
  deleteEvidenceRequest: (id: number) => request<{ status: string }>(`/api/evidence-requests/${id}`, { method: "DELETE" }),
  generateEvidenceRequestsFromPoam: () => request<{ created: number; existing: number }>("/api/evidence-requests/generate/poam", { method: "POST" }),
  generateEvidenceRequestsFromPackage: () => request<{ created: number; existing: number }>("/api/evidence-requests/generate/package", { method: "POST" }),
  evidenceRequestRegisterExportUrl: () => `${API_BASE}/api/evidence-requests/export/xlsx`,
  evidenceRequestOwnerExportUrl: (owner = "") => `${API_BASE}/api/evidence-requests/export/owner/docx?owner=${encodeURIComponent(owner)}`,
  complianceDocuments: (q = "", documentType = "", controlId = "") =>
    request<ComplianceDocument[]>(`/api/compliance/documents?q=${encodeURIComponent(q)}&document_type=${encodeURIComponent(documentType)}&control_id=${encodeURIComponent(controlId)}`),
  uploadComplianceDocument: (payload: { file_name: string; content_base64: string; document_type?: string; data_classification?: string; contains_cui?: boolean; contains_itar?: boolean; contains_pii?: boolean; title?: string; owner?: string }) =>
    request<ComplianceDocument>("/api/compliance/documents/upload", { method: "POST", body: JSON.stringify(payload) }),
  replaceComplianceDocument: (id: number, payload: { file_name: string; content_base64: string; document_type?: string; data_classification?: string; contains_cui?: boolean; contains_itar?: boolean; contains_pii?: boolean; title?: string; owner?: string }) =>
    request<ComplianceDocument>(`/api/compliance/documents/${id}/replace`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteComplianceDocument: (id: number) => request<{ status: string }>(`/api/compliance/documents/${id}`, { method: "DELETE" }),
  complianceGraph: () => request<ComplianceGraph>("/api/compliance/graph"),
  complianceReadiness: () => request<ComplianceReadiness>("/api/compliance/readiness"),
  complianceSearch: (q: string) => request<ComplianceSearchResult[]>(`/api/compliance/search?q=${encodeURIComponent(q)}`),
  complianceChat: (question: string) =>
    request<ComplianceChat>("/api/compliance/chat", { method: "POST", body: JSON.stringify({ question }) }),
  copilotDashboard: () => request<CopilotDashboard>("/api/copilot/dashboard"),
  controlEvidenceMappings: (q = "", status = "", sourceSystem = "") =>
    request<ControlEvidenceMap[]>(`/api/copilot/control-mappings?q=${encodeURIComponent(q)}&status=${encodeURIComponent(status)}&source_system=${encodeURIComponent(sourceSystem)}`),
  controlEvidenceMapping: (controlId: string) => request<ControlEvidenceMap>(`/api/copilot/control-mappings/${controlId}`),
  driftAlerts: (status = "Open") => request<DriftAlert[]>(`/api/copilot/alerts?status=${encodeURIComponent(status)}`),
  controlHealth: () => request<ControlHealthDashboard>("/api/control-health"),
  controlGraph: (controlId: string) => request<ControlGraph>(`/api/controls/${controlId}/graph`),
  controlObjectives: (controlId: string) => request<ControlObjectiveWorkspace>(`/api/controls/${controlId}/objectives`),
  updateEvidenceObjective: (supportRecordId: number, payload: { supported: string; notes: string }) =>
    request<ControlObjectiveWorkspace>(`/api/evidence/objectives/${supportRecordId}`, { method: "PUT", body: JSON.stringify(payload) }),
  chatQuery: (query: string) =>
    request<ComplianceChat>("/api/chat/query", { method: "POST", body: JSON.stringify({ query }) }),
  readiness: () => request<ComplianceReadiness>("/api/readiness"),
  simulateAssessment: (payload: { control_id: string; assessor_question?: string; provided_evidence_ids?: number[]; notes?: string }) =>
    request<AssessmentSimulation>("/api/assessment/simulate", { method: "POST", body: JSON.stringify(payload) }),
};
