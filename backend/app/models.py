from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), default="MVP User")
    role: Mapped[str] = mapped_column(String(100), default="admin")
    department: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(50), default="Active")


class RoleAssignment(Base):
    __tablename__ = "role_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    person_name: Mapped[str] = mapped_column(String(255), default="")
    person_email: Mapped[str] = mapped_column(String(255), default="")
    compliance_role: Mapped[str] = mapped_column(String(100))
    scope_type: Mapped[str] = mapped_column(String(50), default="Organization")
    scope_value: Mapped[str] = mapped_column(String(255), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ControlReview(Base):
    __tablename__ = "control_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    review_status: Mapped[str] = mapped_column(String(100), default="Not Started")
    reviewer: Mapped[str] = mapped_column(String(255), default="")
    approver: Mapped[str] = mapped_column(String(255), default="")
    review_notes: Mapped[str] = mapped_column(Text, default="")
    signoff_date: Mapped[str] = mapped_column(String(50), default="")
    next_review_date: Mapped[str] = mapped_column(String(50), default="")
    package_readiness_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    company_name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str] = mapped_column(String(255))
    employee_count: Mapped[str] = mapped_column(String(100))
    locations: Mapped[str] = mapped_column(Text)
    cloud_environment: Mapped[str] = mapped_column(Text)
    cui_environment: Mapped[str] = mapped_column(Text)
    msp_involvement: Mapped[str] = mapped_column(Text)
    mfa_solution: Mapped[str] = mapped_column(Text)
    endpoint_management: Mapped[str] = mapped_column(Text)
    backup_solution: Mapped[str] = mapped_column(Text)
    ticketing_system: Mapped[str] = mapped_column(Text)
    hr_onboarding_process: Mapped[str] = mapped_column(Text)
    access_removal_process: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CmmcControl(Base):
    __tablename__ = "cmmc_controls"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    family: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    requirement: Mapped[str] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer, default=2)
    objectives: Mapped[list["AssessmentObjective"]] = relationship(back_populates="control")


class AssessmentObjective(Base):
    __tablename__ = "assessment_objectives"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    label: Mapped[str] = mapped_column(String(50))
    objective: Mapped[str] = mapped_column(Text)
    control: Mapped[CmmcControl] = relationship(back_populates="objectives")


class EvidenceRequirement(Base):
    __tablename__ = "evidence_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    artifact: Mapped[str] = mapped_column(Text)


class ControlEvidenceSource(Base):
    __tablename__ = "control_evidence_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    evidence_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(100))
    connected_system: Mapped[str] = mapped_column(String(100), default="")
    collection_method: Mapped[str] = mapped_column(String(100), default="Manual Upload")
    review_frequency: Mapped[str] = mapped_column(String(100), default="Quarterly")
    required: Mapped[str] = mapped_column(String(10), default="true")
    description: Mapped[str] = mapped_column(Text, default="")


class MonitoringRule(Base):
    __tablename__ = "monitoring_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    rule_name: Mapped[str] = mapped_column(String(255))
    source_system: Mapped[str] = mapped_column(String(100))
    condition: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(50), default="Medium")
    enabled: Mapped[str] = mapped_column(String(10), default="true")


class DriftAlert(Base):
    __tablename__ = "drift_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    alert_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50), default="Medium")
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(100), default="Open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GeneratedOutput(Base):
    __tablename__ = "generated_outputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_profile_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id"))
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    implementation_statement: Mapped[str] = mapped_column(Text)
    responsible_parties: Mapped[str] = mapped_column(Text)
    evidence_artifacts: Mapped[str] = mapped_column(Text)
    assessment_notes: Mapped[str] = mapped_column(Text)
    gaps_assumptions: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    policy_name: Mapped[str] = mapped_column(String(255))
    policy_text: Mapped[str] = mapped_column(Text)
    responsibility_matrix: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    author: Mapped[str] = mapped_column(String(255), default="CMMC Pilot")
    approver: Mapped[str] = mapped_column(String(255), default="Pending")
    approval_date: Mapped[str] = mapped_column(String(50), default="")
    review_date: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(100), default="Draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Procedure(Base):
    __tablename__ = "procedures"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    procedure_name: Mapped[str] = mapped_column(String(255))
    procedure_text: Mapped[str] = mapped_column(Text)
    responsibility_matrix: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    author: Mapped[str] = mapped_column(String(255), default="CMMC Pilot")
    approver: Mapped[str] = mapped_column(String(255), default="Pending")
    approval_date: Mapped[str] = mapped_column(String(50), default="")
    review_date: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(100), default="Draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PolicyTemplate(Base):
    __tablename__ = "policy_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(255), unique=True)
    control_family: Mapped[str] = mapped_column(String(100))
    template_text: Mapped[str] = mapped_column(Text)


class ProcedureTemplate(Base):
    __tablename__ = "procedure_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    procedure_name: Mapped[str] = mapped_column(String(255), unique=True)
    control_family: Mapped[str] = mapped_column(String(100))
    template_text: Mapped[str] = mapped_column(Text)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_type: Mapped[str] = mapped_column(String(50))
    document_id: Mapped[int] = mapped_column(Integer)
    version: Mapped[str] = mapped_column(String(50))
    document_text: Mapped[str] = mapped_column(Text)
    responsibility_matrix: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(255), default="CMMC Pilot")
    status: Mapped[str] = mapped_column(String(100), default="Draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DocumentApproval(Base):
    __tablename__ = "document_approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_type: Mapped[str] = mapped_column(String(50))
    document_id: Mapped[int] = mapped_column(Integer)
    approver: Mapped[str] = mapped_column(String(255))
    approval_date: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(100), default="Pending")
    comments: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class System(Base):
    __tablename__ = "systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    system_name: Mapped[str] = mapped_column(String(255))
    system_owner: Mapped[str] = mapped_column(String(255))
    data_owner: Mapped[str] = mapped_column(String(255), default="")
    business_function: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text)
    boundary_description: Mapped[str] = mapped_column(Text)
    cui_description: Mapped[str] = mapped_column(Text)
    infrastructure: Mapped[str] = mapped_column(Text, default="")
    security_stack: Mapped[str] = mapped_column(Text, default="")
    external_providers: Mapped[str] = mapped_column(Text, default="")
    cui_created: Mapped[str] = mapped_column(Text, default="")
    cui_stored: Mapped[str] = mapped_column(Text, default="")
    cui_transmitted: Mapped[str] = mapped_column(Text, default="")
    cui_archived: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SSPDocument(Base):
    __tablename__ = "ssp_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    system_id: Mapped[int] = mapped_column(ForeignKey("systems.id"))
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    status: Mapped[str] = mapped_column(String(100), default="Draft")
    document_json: Mapped[str] = mapped_column(Text)
    generated_docx_path: Mapped[str] = mapped_column(Text, default="")
    generated_pdf_path: Mapped[str] = mapped_column(Text, default="")
    completeness_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SSPSection(Base):
    __tablename__ = "ssp_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    ssp_document_id: Mapped[int] = mapped_column(ForeignKey("ssp_documents.id"))
    section_name: Mapped[str] = mapped_column(String(255))
    section_content: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer)


class PoamItem(Base):
    __tablename__ = "poam_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    generated_output_id: Mapped[int] = mapped_column(ForeignKey("generated_outputs.id"))
    gap: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(255), default="Unassigned")
    status: Mapped[str] = mapped_column(String(100), default="Open")


class ManagedPoamItem(Base):
    __tablename__ = "managed_poam_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    control_id: Mapped[str] = mapped_column(String(50))
    control_title: Mapped[str] = mapped_column(String(255))
    objective_label: Mapped[str] = mapped_column(String(50))
    objective: Mapped[str] = mapped_column(Text)
    gap_statement: Mapped[str] = mapped_column(Text)
    evidence_needed: Mapped[str] = mapped_column(Text, default="")
    corrective_action: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(255), default="Compliance Owner")
    due_date: Mapped[str] = mapped_column(String(50), default="")
    risk: Mapped[str] = mapped_column(String(50), default="Medium")
    status: Mapped[str] = mapped_column(String(100), default="Open")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UploadedEvidence(Base):
    __tablename__ = "uploaded_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    storage_url: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ComplianceDocument(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    title: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(100), default="Unclassified")
    data_classification: Mapped[str] = mapped_column(String(100), default="Public")
    contains_cui: Mapped[str] = mapped_column(String(10), default="No")
    contains_itar: Mapped[str] = mapped_column(String(10), default="No")
    contains_pii: Mapped[str] = mapped_column(String(10), default="No")
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    version: Mapped[str] = mapped_column(String(50), default="")
    owner: Mapped[str] = mapped_column(String(255), default="Compliance Owner")
    review_date: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(100), default="Parsed")
    storage_path: Mapped[str] = mapped_column(Text)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    parsed_json: Mapped[str] = mapped_column(Text, default="{}")
    uploaded_by: Mapped[str] = mapped_column(String(255), default="MVP User")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ControlMapping(Base):
    __tablename__ = "control_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    mapping_type: Mapped[str] = mapped_column(String(100), default="Referenced")
    confidence_score: Mapped[int] = mapped_column(Integer, default=60)
    rationale: Mapped[str] = mapped_column(Text, default="")


class DocumentEntity(Base):
    __tablename__ = "document_entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_value: Mapped[str] = mapped_column(Text)
    source_excerpt: Mapped[str] = mapped_column(Text, default="")


class EvidenceRelationship(Base):
    __tablename__ = "evidence_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[int] = mapped_column(Integer)
    target_type: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[str] = mapped_column(String(100))
    relationship_type: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str] = mapped_column(Text, default="")


class EvidenceRequest(Base):
    __tablename__ = "evidence_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    control_id: Mapped[str] = mapped_column(String(50), default="")
    objective_label: Mapped[str] = mapped_column(String(50), default="")
    request_title: Mapped[str] = mapped_column(String(255))
    evidence_needed: Mapped[str] = mapped_column(Text)
    requested_from: Mapped[str] = mapped_column(String(255), default="Evidence Owner")
    due_date: Mapped[str] = mapped_column(String(50), default="")
    priority: Mapped[str] = mapped_column(String(50), default="Medium")
    status: Mapped[str] = mapped_column(String(100), default="Draft")
    source_type: Mapped[str] = mapped_column(String(100), default="Manual")
    source_id: Mapped[str] = mapped_column(String(100), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    title: Mapped[str] = mapped_column(String(255))
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    document_type: Mapped[str] = mapped_column(String(100), default="Evidence")
    data_classification: Mapped[str] = mapped_column(String(100), default="Public")
    contains_cui: Mapped[str] = mapped_column(String(10), default="No")
    contains_itar: Mapped[str] = mapped_column(String(10), default="No")
    contains_pii: Mapped[str] = mapped_column(String(10), default="No")
    intended_control_id: Mapped[str] = mapped_column(String(50), default="")
    managed_poam_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_request_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_path: Mapped[str] = mapped_column(Text)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    evidence_type: Mapped[str] = mapped_column(String(100), default="Unclassified")
    owner: Mapped[str] = mapped_column(String(255), default="Compliance Owner")
    status: Mapped[str] = mapped_column(String(100), default="Analyzed")
    review_status: Mapped[str] = mapped_column(String(100), default="Under Review")
    reviewer: Mapped[str] = mapped_column(String(255), default="")
    review_date: Mapped[str] = mapped_column(String(50), default="")
    review_notes: Mapped[str] = mapped_column(Text, default="")
    uploaded_by: Mapped[str] = mapped_column(String(255), default="MVP User")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    analyses: Mapped[list["EvidenceAnalysis"]] = relationship(back_populates="evidence")


class EvidenceAnalysis(Base):
    __tablename__ = "evidence_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence.id"))
    control_id: Mapped[int] = mapped_column(ForeignKey("cmmc_controls.id"))
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    coverage_score: Mapped[int] = mapped_column(Integer, default=0)
    assessment_strength: Mapped[str] = mapped_column(String(100), default="Needs Review")
    analysis_result: Mapped[str] = mapped_column(Text)
    evidence: Mapped[Evidence] = relationship(back_populates="analyses")
    objectives: Mapped[list["EvidenceObjective"]] = relationship(back_populates="analysis")


class EvidenceObjective(Base):
    __tablename__ = "evidence_objectives"

    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_analysis_id: Mapped[int] = mapped_column(ForeignKey("evidence_analysis.id"))
    objective_id: Mapped[int] = mapped_column(ForeignKey("assessment_objectives.id"))
    supported: Mapped[str] = mapped_column(String(50), default="Not Supported")
    notes: Mapped[str] = mapped_column(Text, default="")
    analysis: Mapped[EvidenceAnalysis] = relationship(back_populates="objectives")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str] = mapped_column(String(100))
    user_name: Mapped[str] = mapped_column(String(255), default="MVP User")
    control_id: Mapped[str] = mapped_column(String(50), default="")
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
