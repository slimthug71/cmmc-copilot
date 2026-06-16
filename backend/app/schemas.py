from pydantic import BaseModel


class CompanyProfileIn(BaseModel):
    company_name: str
    industry: str
    employee_count: str
    locations: str
    cloud_environment: str
    cui_environment: str
    msp_involvement: str
    mfa_solution: str
    endpoint_management: str
    backup_solution: str
    ticketing_system: str
    hr_onboarding_process: str
    access_removal_process: str


class CompanyProfileOut(CompanyProfileIn):
    id: int

    class Config:
        from_attributes = True


class PersonIn(BaseModel):
    email: str
    full_name: str
    role: str = "user"
    department: str = ""
    title: str = ""
    status: str = "Active"


class PersonOut(PersonIn):
    id: int

    class Config:
        from_attributes = True


class RoleAssignmentIn(BaseModel):
    user_id: int | None = None
    person_name: str = ""
    person_email: str = ""
    compliance_role: str
    scope_type: str = "Organization"
    scope_value: str = ""
    notes: str = ""


class RoleAssignmentOut(RoleAssignmentIn):
    id: int

    class Config:
        from_attributes = True


class OwnershipCoverageOut(BaseModel):
    people: int
    role_assignments: int
    controls_without_owner: int
    poam_without_owner: int
    evidence_without_owner: int
    evidence_without_reviewer: int
    documents_without_approver: int
    systems_without_owner: int
    upcoming_owner_tasks: int
    findings: list[str]


class OwnerWorkItemOut(BaseModel):
    item_type: str
    title: str
    owner: str
    status: str
    due_date: str = ""
    control_id: str = ""
    link: str = ""


class OwnerDashboardOut(BaseModel):
    owner: str
    controls: int
    evidence: int
    poam_items: int
    upcoming_tasks: int
    work_items: list[OwnerWorkItemOut]


class ControlReviewUpdate(BaseModel):
    review_status: str
    reviewer: str = ""
    approver: str = ""
    review_notes: str = ""
    signoff_date: str = ""
    next_review_date: str = ""


class ControlReviewOut(BaseModel):
    id: int | None = None
    control_id: str
    control_title: str
    family: str
    review_status: str
    reviewer: str
    approver: str
    review_notes: str
    signoff_date: str
    next_review_date: str
    package_readiness_score: int
    warnings: list[str]
    updated_at: str = ""


class ControlReviewDashboardOut(BaseModel):
    total_controls: int
    not_started: int
    in_review: int
    approved: int
    rejected: int
    due_soon: int
    overdue: int
    rows: list[ControlReviewOut]


class ControlOut(BaseModel):
    id: int
    control_id: str
    family: str
    title: str
    requirement: str
    objectives: list[str] = []
    evidence: list[str] = []


class GenerateIn(BaseModel):
    company_profile_id: int
    control_id: str


class GeneratedOutputOut(BaseModel):
    id: int
    control_id: str
    implementation_statement: str
    responsible_parties: str
    evidence_artifacts: str
    assessment_notes: str
    gaps_assumptions: str


class GeneratedOutputUpdate(BaseModel):
    implementation_statement: str
    responsible_parties: str
    evidence_artifacts: str
    assessment_notes: str
    gaps_assumptions: str


class DocumentGenerateIn(BaseModel):
    company_profile_id: int
    control_id: str


class DocumentOut(BaseModel):
    id: int
    document_type: str
    control_id: str
    name: str
    text: str
    responsibility_matrix: str
    version: str
    author: str
    approver: str
    approval_date: str
    review_date: str
    status: str


class DocumentUpdate(BaseModel):
    name: str
    text: str
    responsibility_matrix: str
    version: str
    author: str
    approver: str
    approval_date: str
    review_date: str
    status: str


class SystemIn(BaseModel):
    system_name: str
    system_owner: str
    data_owner: str = ""
    business_function: str = ""
    description: str
    boundary_description: str
    cui_description: str
    infrastructure: str = ""
    security_stack: str = ""
    external_providers: str = ""
    cui_created: str = ""
    cui_stored: str = ""
    cui_transmitted: str = ""
    cui_archived: str = ""


class SystemOut(SystemIn):
    id: int

    class Config:
        from_attributes = True


class SSPGenerateIn(BaseModel):
    company_profile_id: int
    system_id: int


class SSPSectionOut(BaseModel):
    id: int
    section_name: str
    section_content: str
    sort_order: int


class SSPDocumentOut(BaseModel):
    id: int
    system_id: int
    version: str
    status: str
    completeness_score: int
    sections: list[SSPSectionOut]


class SSPSectionUpdate(BaseModel):
    section_content: str


class EvidenceObjectiveOut(BaseModel):
    id: int
    objective: str
    supported: str
    notes: str


class EvidenceObjectiveUpdate(BaseModel):
    supported: str
    notes: str


class EvidenceAnalysisOut(BaseModel):
    id: int
    control_id: str
    control_title: str
    confidence_score: int
    coverage_score: int
    assessment_strength: str
    missing_evidence: list[str]
    recommendations: list[str]
    assessor_observations: str
    objectives: list[EvidenceObjectiveOut]


class EvidenceOut(BaseModel):
    id: int
    title: str
    file_name: str
    file_type: str
    document_type: str
    data_classification: str
    contains_cui: str
    contains_itar: str
    contains_pii: str
    intended_control_id: str
    managed_poam_id: int | None
    evidence_request_id: int | None
    evidence_type: str
    owner: str
    status: str
    review_status: str
    reviewer: str
    review_date: str
    review_notes: str
    drift_state: str
    uploaded_by: str
    uploaded_at: str
    analyses: list[EvidenceAnalysisOut] = []


class EvidenceDashboardOut(BaseModel):
    evidence_uploaded: int
    controls_with_evidence: int
    total_controls: int
    objectives_with_evidence: int
    total_objectives: int
    objective_coverage_score: int
    average_coverage: int
    missing_evidence: int
    strong_evidence: int
    weak_evidence: int
    uploaded_evidence: int
    under_review_evidence: int
    accepted_evidence: int
    needs_replacement_evidence: int
    rejected_evidence: int
    stale_evidence: int
    objectives_at_risk: int
    controls_at_risk: int
    assessment_readiness_score: int


class EvidenceUploadIn(BaseModel):
    file_name: str
    content_base64: str
    document_type: str = "Evidence"
    data_classification: str = "Public"
    contains_cui: bool = False
    contains_itar: bool = False
    contains_pii: bool = False
    title: str = ""
    owner: str = "Compliance Owner"
    control_id: str = ""
    managed_poam_id: int | None = None
    evidence_request_id: int | None = None


class EvidenceReviewUpdate(BaseModel):
    review_status: str
    reviewer: str = "Compliance Reviewer"
    review_notes: str = ""


class EvidenceRequestIn(BaseModel):
    control_id: str = ""
    objective_label: str = ""
    request_title: str
    evidence_needed: str
    requested_from: str = "Evidence Owner"
    due_date: str = ""
    priority: str = "Medium"
    status: str = "Draft"
    source_type: str = "Manual"
    source_id: str = ""
    notes: str = ""


class EvidenceRequestOut(EvidenceRequestIn):
    id: int
    linked_evidence_count: int = 0
    accepted_evidence_count: int = 0
    created_at: str
    updated_at: str


class EvidenceRequestDashboardOut(BaseModel):
    total: int
    draft: int
    sent: int
    submitted: int
    accepted: int
    rejected: int
    overdue: int
    rows: list[EvidenceRequestOut]


class ControlEvidenceSourceOut(BaseModel):
    id: int
    evidence_name: str
    source_type: str
    connected_system: str
    collection_method: str
    review_frequency: str
    required: str
    description: str


class MonitoringRuleOut(BaseModel):
    id: int
    rule_name: str
    source_system: str
    condition: str
    severity: str
    enabled: str


class DriftAlertOut(BaseModel):
    id: int
    control_id: str
    control_title: str
    alert_type: str
    severity: str
    title: str
    description: str
    recommended_action: str
    status: str
    created_at: str


class ControlEvidenceMapOut(BaseModel):
    control_id: str
    control_title: str
    family: str
    status: str
    evidence_count: int
    required_sources: int
    connected_sources: int
    manual_sources: int
    open_alerts: int
    review_frequency: str
    evidence_sources: list[ControlEvidenceSourceOut]
    monitoring_rules: list[MonitoringRuleOut]


class CopilotDashboardOut(BaseModel):
    overall_readiness: int
    healthy_controls: int
    at_risk_controls: int
    partially_implemented_controls: int
    not_implemented_controls: int
    open_alerts: int
    automated_sources: int
    manual_sources: int
    mapped_controls: int
    total_controls: int
    recent_alerts: list[DriftAlertOut]


class ComplianceDocumentUploadIn(BaseModel):
    file_name: str
    content_base64: str
    document_type: str = ""
    data_classification: str = "Public"
    contains_cui: bool = False
    contains_itar: bool = False
    contains_pii: bool = False
    title: str = ""
    owner: str = "Compliance Owner"


class ControlMappingOut(BaseModel):
    control_id: str
    control_title: str
    mapping_type: str
    confidence_score: int
    rationale: str


class DocumentEntityOut(BaseModel):
    entity_type: str
    entity_value: str
    source_excerpt: str = ""


class ComplianceDocumentOut(BaseModel):
    id: int
    title: str
    document_type: str
    data_classification: str
    contains_cui: str
    contains_itar: str
    contains_pii: str
    file_name: str
    file_type: str
    version: str
    owner: str
    review_date: str
    status: str
    uploaded_at: str
    mappings: list[ControlMappingOut] = []
    entities: list[DocumentEntityOut] = []


class ComplianceGraphOut(BaseModel):
    documents: int
    mapped_controls: int
    policies: int
    procedures: int
    ssp_documents: int
    poam_documents: int
    entities: dict[str, int]
    recent_alerts: list[str]


class ComplianceSearchResultOut(BaseModel):
    result_type: str
    title: str
    subtitle: str
    excerpt: str


class ComplianceChatIn(BaseModel):
    question: str


class ComplianceChatOut(BaseModel):
    answer: str
    sources: list[str]


class ComplianceReadinessOut(BaseModel):
    documentation_score: int
    evidence_score: int
    poam_score: int
    overall_score: int
    findings: list[str]


class AssessmentPackageControlOut(BaseModel):
    control_id: str
    title: str
    family: str
    readiness_score: int
    implementation_status: str
    policy_status: str
    procedure_status: str
    accepted_evidence: int
    evidence_total: int
    open_poam: int
    stale_evidence: int
    warnings: list[str]


class AssessmentPackageSummaryOut(BaseModel):
    scope: str
    total_controls: int
    ready_controls: int
    warning_controls: int
    missing_implementation: int
    missing_policy: int
    missing_procedure: int
    controls_without_accepted_evidence: int
    open_poam_items: int
    stale_evidence: int
    completeness_score: int
    controls: list[AssessmentPackageControlOut]


class ChatQueryIn(BaseModel):
    query: str


class AssessmentSimulationIn(BaseModel):
    control_id: str
    assessor_question: str = ""
    provided_evidence_ids: list[int] = []
    notes: str = ""


class AssessmentSimulationOut(BaseModel):
    control_id: str
    assessment_question: str
    assessment_status: str
    evidence_reviewed: list[str]
    missing: list[str]
    assessor_feedback: str
    recommended_next_steps: list[str]


class ControlGraphItemOut(BaseModel):
    id: str
    name: str
    item_type: str
    source: str
    status: str = ""
    detail: str = ""


class ControlGraphOut(BaseModel):
    control_id: str
    control_title: str
    family: str
    requirement: str
    status: str
    policies: list[ControlGraphItemOut]
    procedures: list[ControlGraphItemOut]
    ssp_references: list[ControlGraphItemOut]
    evidence: list[ControlGraphItemOut]
    poam_items: list[ControlGraphItemOut]
    alerts: list[DriftAlertOut]
    evidence_sources: list[ControlEvidenceSourceOut]
    monitoring_rules: list[MonitoringRuleOut]


class ObjectiveEvidenceItemOut(BaseModel):
    evidence_id: int
    evidence_title: str
    file_name: str
    evidence_type: str
    support_record_id: int
    supported: str
    notes: str
    coverage_score: int
    confidence_score: int


class ControlObjectiveOut(BaseModel):
    id: int
    label: str
    objective: str
    status: str
    evidence_count: int
    coverage_score: int
    missing_evidence: list[str]
    recommendations: list[str]
    assessor_notes: str
    evidence: list[ObjectiveEvidenceItemOut]


class ControlObjectiveWorkspaceOut(BaseModel):
    control_id: str
    control_title: str
    family: str
    requirement: str
    readiness_score: int
    supported_objectives: int
    partial_objectives: int
    total_objectives: int
    objectives: list[ControlObjectiveOut]


class ControlHealthRowOut(BaseModel):
    control_id: str
    title: str
    family: str
    objective_coverage_score: int
    objectives_with_evidence: int
    total_objectives: int
    accepted_evidence: int
    under_review_evidence: int
    needs_replacement_evidence: int
    rejected_evidence: int
    stale_evidence: int
    poam_candidates: int
    drift_state: str
    health_status: str


class ControlHealthDashboardOut(BaseModel):
    healthy_controls: int
    monitor_controls: int
    at_risk_controls: int
    critical_controls: int
    stale_evidence: int
    poam_candidates: int
    rows: list[ControlHealthRowOut]


class ManagedPoamItemOut(BaseModel):
    id: int
    control_id: str
    control_title: str
    objective_label: str
    objective: str
    gap_statement: str
    evidence_needed: str
    corrective_action: str
    owner: str
    due_date: str
    risk: str
    status: str
    notes: str
    created_at: str
    updated_at: str


class ManagedPoamUpdate(BaseModel):
    gap_statement: str
    evidence_needed: str
    corrective_action: str
    owner: str
    due_date: str
    risk: str
    status: str
    notes: str


class ManagedPoamGenerateOut(BaseModel):
    created: int
    existing: int
    total_open: int


class AuditLogOut(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: str
    user_name: str
    control_id: str
    details: str
    created_at: str


class ComplianceTaskOut(BaseModel):
    id: str
    task_type: str
    title: str
    owner: str
    due_date: str
    status: str
    control_id: str
    entity_type: str
    entity_id: str
    detail: str
    link: str


class ComplianceCalendarOut(BaseModel):
    overdue: int
    due_soon: int
    upcoming: int
    unscheduled: int
    completed: int
    tasks: list[ComplianceTaskOut]
