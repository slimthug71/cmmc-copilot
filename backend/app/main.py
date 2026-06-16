import base64
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import inspect, text
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import (
    AssessmentObjective,
    AuditLog,
    CmmcControl,
    CompanyProfile,
    ComplianceDocument,
    ControlReview,
    ControlEvidenceSource,
    ControlMapping,
    DocumentEntity,
    DriftAlert,
    DocumentVersion,
    Evidence,
    EvidenceAnalysis,
    EvidenceObjective,
    EvidenceRequest,
    EvidenceRelationship,
    EvidenceRequirement,
    GeneratedOutput,
    ManagedPoamItem,
    MonitoringRule,
    Organization,
    Policy,
    Procedure,
    PoamItem,
    RoleAssignment,
    SSPDocument,
    SSPSection,
    System,
    UploadedEvidence,
    User,
)
from .document_intelligence.document_parser import parse_document
from .document_intelligence.poam_parser import parse_poam
from .document_intelligence.policy_parser import parse_policy
from .document_intelligence.ssp_parser import parse_ssp
from .schemas import AssessmentPackageControlOut, AssessmentPackageSummaryOut, AssessmentSimulationIn, AssessmentSimulationOut, AuditLogOut, ChatQueryIn, CompanyProfileIn, CompanyProfileOut, ComplianceCalendarOut, ComplianceChatIn, ComplianceChatOut, ComplianceDocumentOut, ComplianceDocumentUploadIn, ComplianceGraphOut, ComplianceReadinessOut, ComplianceSearchResultOut, ComplianceTaskOut, ControlEvidenceMapOut, ControlEvidenceSourceOut, ControlGraphItemOut, ControlGraphOut, ControlHealthDashboardOut, ControlHealthRowOut, ControlMappingOut, ControlObjectiveOut, ControlObjectiveWorkspaceOut, ControlOut, ControlReviewDashboardOut, ControlReviewOut, ControlReviewUpdate, CopilotDashboardOut, DocumentEntityOut, DocumentGenerateIn, DocumentOut, DocumentUpdate, DriftAlertOut, EvidenceAnalysisOut, EvidenceDashboardOut, EvidenceObjectiveOut, EvidenceObjectiveUpdate, EvidenceOut, EvidenceRequestDashboardOut, EvidenceRequestIn, EvidenceRequestOut, EvidenceReviewUpdate, EvidenceUploadIn, GeneratedOutputOut, GeneratedOutputUpdate, GenerateIn, ManagedPoamGenerateOut, ManagedPoamItemOut, ManagedPoamUpdate, MonitoringRuleOut, ObjectiveEvidenceItemOut, OwnerDashboardOut, OwnerWorkItemOut, OwnershipCoverageOut, PersonIn, PersonOut, RoleAssignmentIn, RoleAssignmentOut, SSPDocumentOut, SSPGenerateIn, SSPSectionOut, SSPSectionUpdate, SystemIn, SystemOut
from .seed_data import ASSESSMENT_OBJECTIVES, CONTROL_ROWS, DEFAULT_EVIDENCE
from .services import analyze_evidence_against_control, classify_evidence_type, evidence_for_control, extract_evidence_text, generate_output, generate_policy_document, generate_procedure_document, render_docx, render_pdf, render_ssp_docx, render_xlsx, score_control_match

app = FastAPI(title="CMMC MVP API")
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "storage" / "evidence"
COMPLIANCE_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "storage" / "compliance"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def seed(db: Session) -> None:
    if db.query(CmmcControl).count():
        return
    org = Organization(name="Default Organization")
    db.add(org)
    for control_id, family, title, requirement in CONTROL_ROWS:
        control = CmmcControl(control_id=control_id, family=family, title=title, requirement=requirement)
        db.add(control)
        db.flush()
        for label, objective in ASSESSMENT_OBJECTIVES.get(control_id, []):
            db.add(AssessmentObjective(control_id=control.id, label=label, objective=objective))
        for artifact in DEFAULT_EVIDENCE:
            db.add(EvidenceRequirement(control_id=control.id, artifact=artifact))
    db.commit()


MICROSOFT_SOURCE_MAP = {
    "AC": [
        ("Entra Users and Groups Export", "Identity", "Microsoft Entra ID", "Graph API", "Monthly", "Maps authorized users, groups, guest users, disabled accounts, and privileged role membership."),
        ("M365 Audit Log Access Events", "Audit Log", "Microsoft 365 Audit Logs", "Graph API", "Monthly", "Supports review of access, sharing, privilege changes, and account activity."),
    ],
    "IA": [
        ("MFA Registration and Conditional Access State", "Identity", "Microsoft Entra ID", "Graph API", "Continuous", "Tracks MFA status, conditional access coverage, authentication methods, and sign-in risk."),
        ("Password and Authentication Policy Export", "Identity", "Microsoft Entra ID", "Graph API", "Quarterly", "Supports password, authentication, and replay-resistant control validation."),
    ],
    "CM": [
        ("Device Compliance and Configuration Baselines", "Endpoint", "Microsoft Intune", "Graph API", "Weekly", "Tracks managed devices, compliance policies, baselines, patch posture, and configuration drift."),
        ("Change Ticket Evidence", "Ticketing", "ServiceNow/Jira", "API", "Monthly", "Links configuration changes to approvals, impact analysis, and implementation records."),
    ],
    "AU": [
        ("Audit Log Retention and Review Evidence", "Audit Log", "Microsoft 365 Audit Logs", "Graph API", "Weekly", "Collects auditable events, review records, and privilege/activity traces."),
    ],
    "IR": [
        ("Defender Incident and Alert Export", "Security Alert", "Microsoft Defender", "Graph API", "Weekly", "Collects endpoint alerts, incident state, severity, and response records."),
    ],
    "SC": [
        ("Endpoint Encryption and Network Protection State", "Endpoint", "Microsoft Intune", "Graph API", "Weekly", "Tracks encryption, firewall, supported OS, and data protection posture."),
    ],
    "SI": [
        ("Defender Device Health and Threat Status", "Endpoint", "Microsoft Defender", "Graph API", "Weekly", "Tracks malware protection, endpoint health, vulnerabilities, and high severity alerts."),
        ("Vulnerability Scan Results", "Vulnerability Scanner", "Nessus/Qualys", "API", "Monthly", "Supports flaw remediation and vulnerability management evidence."),
    ],
    "MP": [
        ("Device Encryption and Removable Media Policy", "Endpoint", "Microsoft Intune", "Graph API", "Monthly", "Supports media protection, encryption, removable media, and backup protection checks."),
    ],
    "CA": [
        ("Assessment Readiness and Control Monitoring Records", "Compliance Record", "CMMC Pilot", "Automated Analysis", "Monthly", "Aggregates mapped documents, evidence, open alerts, and POA&M state."),
    ],
}


MONITORING_RULE_TEMPLATES = {
    "AC": [
        ("New Privileged Account Detected", "Microsoft Entra ID", "Alert when a new user receives privileged directory or cloud application role membership.", "High"),
        ("Inactive or Guest Account Requires Review", "Microsoft Entra ID", "Alert when guest, stale, or disabled account state conflicts with authorized access records.", "Medium"),
    ],
    "IA": [
        ("MFA Coverage Drift", "Microsoft Entra ID", "Alert when any enabled user lacks MFA registration or is excluded from Conditional Access.", "High"),
    ],
    "CM": [
        ("Unmanaged or Non-Compliant Device", "Microsoft Intune", "Alert when active endpoints are not enrolled, not compliant, or missing required baselines.", "High"),
    ],
    "SC": [
        ("Encryption or Boundary Protection Drift", "Microsoft Intune", "Alert when encryption, firewall, data protection, or network protection settings are missing.", "High"),
    ],
    "SI": [
        ("High Severity Endpoint Alert", "Microsoft Defender", "Alert when Defender reports high severity alerts, malware, or unhealthy endpoint protection.", "High"),
    ],
    "AU": [
        ("Audit Review Gap", "Microsoft 365 Audit Logs", "Alert when audit log review evidence is older than the required review interval.", "Medium"),
    ],
    "IR": [
        ("Incident Response Evidence Gap", "Microsoft Defender", "Alert when incident records lack disposition, owner, or closure evidence.", "Medium"),
    ],
}


def seed_control_evidence_engine(db: Session) -> None:
    if db.query(ControlEvidenceSource).count():
        return
    controls = db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    for control in controls:
        family_code = control.control_id.split(".")[0]
        stored_evidence = [row.artifact for row in db.query(EvidenceRequirement).filter_by(control_id=control.id).all()]
        for artifact in evidence_for_control(control, stored_evidence):
            db.add(
                ControlEvidenceSource(
                    control_id=control.id,
                    evidence_name=artifact,
                    source_type="Assessment Artifact",
                    connected_system="CMMC Pilot",
                    collection_method="Manual Upload",
                    review_frequency="Quarterly",
                    required="true",
                    description=f"Required assessor-facing evidence for {control.control_id}.",
                )
            )
        for evidence_name, source_type, system_name, method, frequency, description in MICROSOFT_SOURCE_MAP.get(family_code, []):
            db.add(
                ControlEvidenceSource(
                    control_id=control.id,
                    evidence_name=evidence_name,
                    source_type=source_type,
                    connected_system=system_name,
                    collection_method=method,
                    review_frequency=frequency,
                    required="false",
                    description=description,
                )
            )
        for rule_name, system_name, condition, severity in MONITORING_RULE_TEMPLATES.get(family_code, []):
            db.add(MonitoringRule(control_id=control.id, rule_name=rule_name, source_system=system_name, condition=condition, severity=severity))
    db.commit()


@app.on_event("startup")
def startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    COMPLIANCE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    with SessionLocal() as db:
        seed(db)
        sync_assessment_objectives(db)
        seed_control_evidence_engine(db)
        backfill_intended_evidence_controls(db)


def sync_assessment_objectives(db: Session) -> None:
    updated = False
    controls = db.query(CmmcControl).all()
    for control in controls:
        expected = ASSESSMENT_OBJECTIVES.get(control.control_id, [])
        if not expected:
            continue
        existing_by_label = {objective.label: objective for objective in db.query(AssessmentObjective).filter_by(control_id=control.id).all()}
        for label, objective_text in expected:
            existing = existing_by_label.get(label)
            if existing:
                if existing.objective != objective_text:
                    existing.objective = objective_text
                    updated = True
            else:
                db.add(AssessmentObjective(control_id=control.id, label=label, objective=objective_text))
                updated = True
    if updated:
        db.commit()


def ensure_schema_updates() -> None:
    inspector = inspect(engine)
    if "evidence" not in inspector.get_table_names():
        return
    evidence_columns = {column["name"] for column in inspector.get_columns("evidence")}
    if "intended_control_id" not in evidence_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE evidence ADD COLUMN intended_control_id VARCHAR(50) NOT NULL DEFAULT ''"))
    evidence_columns = {column["name"] for column in inspect(engine).get_columns("evidence")}
    evidence_review_columns = {
        "managed_poam_id": "INTEGER",
        "evidence_request_id": "INTEGER",
        "document_type": "VARCHAR(100) NOT NULL DEFAULT 'Evidence'",
        "data_classification": "VARCHAR(100) NOT NULL DEFAULT 'Public'",
        "contains_cui": "VARCHAR(10) NOT NULL DEFAULT 'No'",
        "contains_itar": "VARCHAR(10) NOT NULL DEFAULT 'No'",
        "contains_pii": "VARCHAR(10) NOT NULL DEFAULT 'No'",
        "review_status": "VARCHAR(100) NOT NULL DEFAULT 'Under Review'",
        "reviewer": "VARCHAR(255) NOT NULL DEFAULT ''",
        "review_date": "VARCHAR(50) NOT NULL DEFAULT ''",
        "review_notes": "TEXT NOT NULL DEFAULT ''",
    }
    with engine.begin() as connection:
        for column_name, column_type in evidence_review_columns.items():
            if column_name not in evidence_columns:
                connection.execute(text(f"ALTER TABLE evidence ADD COLUMN {column_name} {column_type}"))
    if "audit_logs" in inspect(engine).get_table_names():
        audit_columns = {column["name"] for column in inspect(engine).get_columns("audit_logs")}
        audit_updates = {
            "user_name": "VARCHAR(255) NOT NULL DEFAULT 'MVP User'",
            "control_id": "VARCHAR(50) NOT NULL DEFAULT ''",
            "details": "TEXT NOT NULL DEFAULT ''",
        }
        with engine.begin() as connection:
            for column_name, column_type in audit_updates.items():
                if column_name not in audit_columns:
                    connection.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {column_name} {column_type}"))
    if "users" in inspect(engine).get_table_names():
        user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
        user_updates = {
            "department": "VARCHAR(255) NOT NULL DEFAULT ''",
            "title": "VARCHAR(255) NOT NULL DEFAULT ''",
            "status": "VARCHAR(50) NOT NULL DEFAULT 'Active'",
        }
        with engine.begin() as connection:
            for column_name, column_type in user_updates.items():
                if column_name not in user_columns:
                    connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
    if "documents" in inspect(engine).get_table_names():
        document_columns = {column["name"] for column in inspect(engine).get_columns("documents")}
        document_updates = {
            "data_classification": "VARCHAR(100) NOT NULL DEFAULT 'Public'",
            "contains_cui": "VARCHAR(10) NOT NULL DEFAULT 'No'",
            "contains_itar": "VARCHAR(10) NOT NULL DEFAULT 'No'",
            "contains_pii": "VARCHAR(10) NOT NULL DEFAULT 'No'",
        }
        with engine.begin() as connection:
            for column_name, column_type in document_updates.items():
                if column_name not in document_columns:
                    connection.execute(text(f"ALTER TABLE documents ADD COLUMN {column_name} {column_type}"))


def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def enforce_upload_data_rules(payload: EvidenceUploadIn | ComplianceDocumentUploadIn) -> None:
    if payload.contains_cui or payload.contains_itar:
        raise HTTPException(
            status_code=400,
            detail=(
                "Upload blocked. This Azure Commercial environment is not approved for CUI, ITAR, "
                "export-controlled data, classified data, or sensitive government contract information."
            ),
        )


def backfill_intended_evidence_controls(db: Session) -> None:
    updated = False
    evidence_rows = db.query(Evidence).all()
    for evidence in evidence_rows:
        if evidence.intended_control_id or len(evidence.analyses) != 1:
            continue
        control = db.get(CmmcControl, evidence.analyses[0].control_id)
        if not control:
            continue
        evidence.intended_control_id = control.control_id
        updated = True
    if updated:
        db.commit()


def log_activity(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: object,
    details: str,
    control_id: str = "",
    user_name: str = "MVP User",
) -> None:
    db.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            user_name=user_name,
            control_id=control_id,
            details=details,
        )
    )


def audit_log_response(item: AuditLog) -> AuditLogOut:
    return AuditLogOut(
        id=item.id,
        action=item.action,
        entity_type=item.entity_type,
        entity_id=item.entity_id,
        user_name=item.user_name,
        control_id=item.control_id,
        details=item.details,
        created_at=item.created_at.isoformat(),
    )


def parse_calendar_date(value: str) -> datetime | None:
    cleaned = (value or "").strip()
    if not cleaned or "annual review" in cleaned.lower() or "upon significant" in cleaned.lower():
        return None
    for pattern in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y"]:
        try:
            return datetime.strptime(cleaned, pattern)
        except ValueError:
            continue
    return None


def frequency_days(frequency: str) -> int:
    lowered = (frequency or "").lower()
    if "continuous" in lowered or "daily" in lowered:
        return 1
    if "weekly" in lowered:
        return 7
    if "monthly" in lowered:
        return 30
    if "quarter" in lowered:
        return 90
    if "annual" in lowered:
        return 365
    return 90


def calendar_task_status(due_date: datetime | None, completed: bool = False) -> str:
    if completed:
        return "Completed"
    if due_date is None:
        return "Unscheduled"
    days = (due_date.date() - datetime.utcnow().date()).days
    if days < 0:
        return "Overdue"
    if days <= 30:
        return "Due Soon"
    return "Upcoming"


def compliance_calendar_tasks(db: Session) -> list[ComplianceTaskOut]:
    tasks: list[ComplianceTaskOut] = []
    now = datetime.utcnow()
    for control in db.query(CmmcControl).order_by(CmmcControl.control_id).all():
        review = latest_control_review(db, control)
        if review and review.review_status == "Approved":
            due = parse_calendar_date(review.next_review_date) or (review.updated_at + timedelta(days=365))
            owner = review.approver or review.reviewer or "Control Owner"
            detail = f"Approved by {review.approver or 'Pending approver'}; next review validates current evidence, POA&M, and implementation status."
        else:
            due = parse_calendar_date(review.next_review_date) if review else None
            owner = (review.reviewer or review.approver) if review else "Control Owner"
            detail = "Control package requires owner review and formal sign-off before assessment package approval."
        tasks.append(
            ComplianceTaskOut(
                id=f"control-review-{control.id}",
                task_type="Control Owner Review",
                title=f"Review {control.control_id} - {control.title}",
                owner=owner,
                due_date=due.strftime("%Y-%m-%d") if due else "",
                status=calendar_task_status(due, bool(review and review.review_status == "Approved" and due and due.date() >= now.date())),
                control_id=control.control_id,
                entity_type="Control Review",
                entity_id=str(review.id if review else control.id),
                detail=detail,
                link=f"/reviews?control={control.control_id}",
            )
        )
    for request in db.query(EvidenceRequest).all():
        due = parse_calendar_date(request.due_date)
        tasks.append(
            ComplianceTaskOut(
                id=f"evidence-request-{request.id}",
                task_type="Evidence Request",
                title=request.request_title,
                owner=request.requested_from,
                due_date=due.strftime("%Y-%m-%d") if due else "",
                status=calendar_task_status(due, request.status in {"Accepted", "Rejected"}),
                control_id=request.control_id,
                entity_type="Evidence Request",
                entity_id=str(request.id),
                detail=f"Priority: {request.priority}. Status: {request.status}. Evidence needed: {request.evidence_needed[:180]}",
                link=f"/evidence-requests?request={request.id}",
            )
        )
    for item in db.query(ManagedPoamItem).all():
        due = parse_calendar_date(item.due_date)
        tasks.append(
            ComplianceTaskOut(
                id=f"poam-{item.id}",
                task_type="POA&M Due Date",
                title=f"{item.control_id} objective {item.objective_label}: {item.gap_statement[:100]}",
                owner=item.owner,
                due_date=due.strftime("%Y-%m-%d") if due else "",
                status=calendar_task_status(due, item.status == "Closed"),
                control_id=item.control_id,
                entity_type="Managed POA&M",
                entity_id=str(item.id),
                detail=f"Risk: {item.risk}. Status: {item.status}. Evidence needed: {item.evidence_needed[:180]}",
                link="/poam",
            )
        )
    for evidence in db.query(Evidence).all():
        base = parse_calendar_date(evidence.review_date) or evidence.uploaded_at
        due = base + timedelta(days=evidence_freshness_days(evidence))
        tasks.append(
            ComplianceTaskOut(
                id=f"evidence-{evidence.id}",
                task_type="Evidence Freshness Review",
                title=f"Review {evidence.title}",
                owner=evidence.reviewer or evidence.owner,
                due_date=due.strftime("%Y-%m-%d"),
                status=calendar_task_status(due, False),
                control_id=evidence.intended_control_id,
                entity_type="Evidence",
                entity_id=str(evidence.id),
                detail=f"{evidence.file_name} is {evidence.review_status}; freshness window is {evidence_freshness_days(evidence)} days.",
                link=f"/evidence?control={evidence.intended_control_id}" if evidence.intended_control_id else "/evidence",
            )
        )
        if evidence.review_status == "Under Review":
            tasks.append(
                ComplianceTaskOut(
                    id=f"evidence-review-{evidence.id}",
                    task_type="Evidence Review Pending",
                    title=f"Complete review for {evidence.title}",
                    owner=evidence.reviewer or "Compliance Reviewer",
                    due_date="",
                    status="Unscheduled",
                    control_id=evidence.intended_control_id,
                    entity_type="Evidence",
                    entity_id=str(evidence.id),
                    detail="Evidence remains under review and requires an acceptance, replacement, or rejection decision.",
                    link=f"/evidence?control={evidence.intended_control_id}" if evidence.intended_control_id else "/evidence",
                )
            )
    for document_type, model, name_field in [("Policy Review", Policy, "policy_name"), ("Procedure Review", Procedure, "procedure_name")]:
        for document in db.query(model).all():
            control = db.get(CmmcControl, document.control_id)
            due = parse_calendar_date(document.review_date)
            if due is None:
                due = document.updated_at + timedelta(days=365)
            tasks.append(
                ComplianceTaskOut(
                    id=f"{document_type.lower().replace(' ', '-')}-{document.id}",
                    task_type=document_type,
                    title=f"Review {getattr(document, name_field)}",
                    owner=document.author,
                    due_date=due.strftime("%Y-%m-%d"),
                    status=calendar_task_status(due),
                    control_id=control.control_id if control else "",
                    entity_type=document_type.split()[0],
                    entity_id=str(document.id),
                    detail=f"Version {document.version}; current status {document.status}.",
                    link="/",
                )
            )
    for ssp in db.query(SSPDocument).all():
        system = db.get(System, ssp.system_id)
        due = ssp.created_at + timedelta(days=365)
        tasks.append(
            ComplianceTaskOut(
                id=f"ssp-review-{ssp.id}",
                task_type="SSP Review",
                title=f"Review {system.system_name if system else 'System Security Plan'}",
                owner=system.system_owner if system else "System Owner",
                due_date=due.strftime("%Y-%m-%d"),
                status=calendar_task_status(due),
                control_id="",
                entity_type="SSP",
                entity_id=str(ssp.id),
                detail=f"SSP version {ssp.version}; current status {ssp.status}; completeness {ssp.completeness_score}%.",
                link="/ssp",
            )
        )
    for source in db.query(ControlEvidenceSource).filter(ControlEvidenceSource.collection_method != "Manual Upload").all():
        control = db.get(CmmcControl, source.control_id)
        due = now + timedelta(days=frequency_days(source.review_frequency))
        tasks.append(
            ComplianceTaskOut(
                id=f"source-{source.id}",
                task_type="Recurring Evidence Collection",
                title=f"Collect {source.evidence_name}",
                owner="Compliance Owner",
                due_date=due.strftime("%Y-%m-%d"),
                status=calendar_task_status(due),
                control_id=control.control_id if control else "",
                entity_type="Evidence Source",
                entity_id=str(source.id),
                detail=f"{source.collection_method} from {source.connected_system}; frequency {source.review_frequency}.",
                link=f"/controls/{control.control_id}/graph" if control else "/health",
            )
        )
    return sorted(tasks, key=lambda task: ({"Overdue": 0, "Due Soon": 1, "Unscheduled": 2, "Upcoming": 3, "Completed": 4}.get(task.status, 5), task.due_date, task.title))


def latest_control_review(db: Session, control: CmmcControl) -> ControlReview | None:
    return db.query(ControlReview).filter_by(control_id=control.id).order_by(ControlReview.updated_at.desc(), ControlReview.id.desc()).first()


def control_review_response(db: Session, control: CmmcControl, review: ControlReview | None = None) -> ControlReviewOut:
    review = review if review is not None else latest_control_review(db, control)
    package = assessment_package_control_row(db, control)
    if review:
        return ControlReviewOut(
            id=review.id,
            control_id=control.control_id,
            control_title=control.title,
            family=control.family,
            review_status=review.review_status,
            reviewer=review.reviewer,
            approver=review.approver,
            review_notes=review.review_notes,
            signoff_date=review.signoff_date,
            next_review_date=review.next_review_date,
            package_readiness_score=review.package_readiness_score or package.readiness_score,
            warnings=package.warnings,
            updated_at=review.updated_at.isoformat(),
        )
    return ControlReviewOut(
        control_id=control.control_id,
        control_title=control.title,
        family=control.family,
        review_status="Not Started",
        reviewer="",
        approver="",
        review_notes="",
        signoff_date="",
        next_review_date="",
        package_readiness_score=package.readiness_score,
        warnings=package.warnings,
    )


def control_review_rows(db: Session, q: str = "", family: str = "", status: str = "") -> list[ControlReviewOut]:
    rows = [control_review_response(db, control) for control in db.query(CmmcControl).order_by(CmmcControl.family, CmmcControl.control_id).all()]
    if q:
        needle = q.lower()
        rows = [row for row in rows if needle in f"{row.control_id} {row.control_title} {row.family} {row.reviewer} {row.approver} {row.review_notes}".lower()]
    if family:
        rows = [row for row in rows if row.family == family]
    if status:
        rows = [row for row in rows if row.review_status == status]
    return rows


def control_review_dashboard_response(db: Session, q: str = "", family: str = "", status: str = "") -> ControlReviewDashboardOut:
    all_rows = control_review_rows(db)
    filtered = control_review_rows(db, q, family, status)
    today = datetime.utcnow().date()
    due_soon = 0
    overdue = 0
    for row in all_rows:
        due = parse_calendar_date(row.next_review_date)
        if not due or row.review_status == "Approved":
            continue
        days = (due.date() - today).days
        if days < 0:
            overdue += 1
        elif days <= 30:
            due_soon += 1
    return ControlReviewDashboardOut(
        total_controls=len(all_rows),
        not_started=sum(1 for row in all_rows if row.review_status == "Not Started"),
        in_review=sum(1 for row in all_rows if row.review_status == "In Review"),
        approved=sum(1 for row in all_rows if row.review_status == "Approved"),
        rejected=sum(1 for row in all_rows if row.review_status == "Rejected"),
        due_soon=due_soon,
        overdue=overdue,
        rows=filtered,
    )


GENERIC_OWNERS = {
    "",
    "pending",
    "unassigned",
    "to be assigned",
    "compliance owner",
    "system owner",
    "data owner",
    "it/security owner",
    "mvp user",
}


def default_organization_id(db: Session) -> int:
    org = db.query(Organization).order_by(Organization.id).first()
    if not org:
        org = Organization(name="Default Organization")
        db.add(org)
        db.commit()
        db.refresh(org)
    return org.id


def has_real_owner(value: str | None) -> bool:
    cleaned = (value or "").strip().lower()
    return bool(cleaned and cleaned not in GENERIC_OWNERS)


def role_assignment_response(assignment: RoleAssignment) -> RoleAssignmentOut:
    return RoleAssignmentOut(
        id=assignment.id,
        user_id=assignment.user_id,
        person_name=assignment.person_name,
        person_email=assignment.person_email,
        compliance_role=assignment.compliance_role,
        scope_type=assignment.scope_type,
        scope_value=assignment.scope_value,
        notes=assignment.notes,
    )


def control_has_owner_assignment(db: Session, control: CmmcControl) -> bool:
    rows = db.query(RoleAssignment).all()
    owner_roles = {"control owner", "system owner", "it owner", "evidence owner", "approver", "reviewer"}
    for row in rows:
        if row.compliance_role.lower() not in owner_roles:
            continue
        if row.scope_type == "Organization":
            return True
        if row.scope_type == "Family" and row.scope_value == control.family:
            return True
        if row.scope_type == "Control" and row.scope_value == control.control_id:
            return True
    return False


def ownership_coverage_summary(db: Session) -> OwnershipCoverageOut:
    controls_without_owner = sum(1 for control in db.query(CmmcControl).all() if not control_has_owner_assignment(db, control))
    poam_without_owner = db.query(ManagedPoamItem).all()
    evidence_rows = db.query(Evidence).all()
    policy_rows = db.query(Policy).all()
    procedure_rows = db.query(Procedure).all()
    systems = db.query(System).all()
    tasks = compliance_calendar_tasks(db)
    findings = []
    missing_poam = sum(1 for item in poam_without_owner if not has_real_owner(item.owner))
    missing_evidence_owner = sum(1 for item in evidence_rows if not has_real_owner(item.owner))
    missing_reviewer = sum(1 for item in evidence_rows if item.review_status != "Accepted" and not has_real_owner(item.reviewer))
    missing_approver = sum(1 for item in [*policy_rows, *procedure_rows] if not has_real_owner(item.approver))
    missing_system_owner = sum(1 for item in systems if not has_real_owner(item.system_owner))
    if controls_without_owner:
        findings.append(f"{controls_without_owner} controls do not have a role assignment at organization, family, or control scope.")
    if missing_poam:
        findings.append(f"{missing_poam} POA&M items still use placeholder or blank owners.")
    if missing_evidence_owner or missing_reviewer:
        findings.append(f"{missing_evidence_owner} evidence items need owners and {missing_reviewer} pending evidence reviews need reviewers.")
    if missing_approver:
        findings.append(f"{missing_approver} policies/procedures need named approvers.")
    if not findings:
        findings.append("Ownership coverage is complete for current records.")
    return OwnershipCoverageOut(
        people=db.query(User).count(),
        role_assignments=db.query(RoleAssignment).count(),
        controls_without_owner=controls_without_owner,
        poam_without_owner=missing_poam,
        evidence_without_owner=missing_evidence_owner,
        evidence_without_reviewer=missing_reviewer,
        documents_without_approver=missing_approver,
        systems_without_owner=missing_system_owner,
        upcoming_owner_tasks=sum(1 for task in tasks if task.status in {"Overdue", "Due Soon", "Unscheduled"} and has_real_owner(task.owner)),
        findings=findings,
    )


def owner_dashboard(db: Session, owner: str) -> OwnerDashboardOut:
    needle = owner.strip().lower()
    work_items: list[OwnerWorkItemOut] = []
    assignments = [
        row
        for row in db.query(RoleAssignment).all()
        if needle and needle in f"{row.person_name} {row.person_email}".lower()
    ]
    for item in db.query(Evidence).all():
        if needle and needle in f"{item.owner} {item.reviewer}".lower():
            work_items.append(OwnerWorkItemOut(item_type="Evidence", title=item.title, owner=item.owner or item.reviewer, status=item.review_status, due_date=item.review_date, control_id=item.intended_control_id, link=f"/evidence?control={item.intended_control_id}"))
    for item in db.query(ManagedPoamItem).all():
        if needle and needle in item.owner.lower():
            work_items.append(OwnerWorkItemOut(item_type="POA&M", title=item.gap_statement[:120], owner=item.owner, status=item.status, due_date=item.due_date, control_id=item.control_id, link="/poam"))
    for request in db.query(EvidenceRequest).all():
        if needle and needle in request.requested_from.lower():
            work_items.append(OwnerWorkItemOut(item_type="Evidence Request", title=request.request_title, owner=request.requested_from, status=request.status, due_date=request.due_date, control_id=request.control_id, link=f"/evidence-requests?request={request.id}"))
    for task in compliance_calendar_tasks(db):
        if needle and needle in task.owner.lower() and task.status != "Completed":
            work_items.append(OwnerWorkItemOut(item_type=task.task_type, title=task.title, owner=task.owner, status=task.status, due_date=task.due_date, control_id=task.control_id, link=task.link))
    return OwnerDashboardOut(
        owner=owner,
        controls=len(assignments),
        evidence=sum(1 for item in work_items if item.item_type == "Evidence"),
        poam_items=sum(1 for item in work_items if item.item_type == "POA&M"),
        upcoming_tasks=sum(1 for item in work_items if item.status in {"Overdue", "Due Soon", "Unscheduled", "Open", "Under Review", "Draft", "Sent", "Submitted"}),
        work_items=work_items[:200],
    )


def output_response(db: Session, output: GeneratedOutput) -> GeneratedOutputOut:
    control = db.get(CmmcControl, output.control_id)
    return GeneratedOutputOut(
        id=output.id,
        control_id=control.control_id if control else "",
        implementation_statement=output.implementation_statement,
        responsible_parties=output.responsible_parties,
        evidence_artifacts=output.evidence_artifacts,
        assessment_notes=output.assessment_notes,
        gaps_assumptions=output.gaps_assumptions,
    )


def document_response(db: Session, document: Policy | Procedure, document_type: str) -> DocumentOut:
    control = db.get(CmmcControl, document.control_id)
    if document_type == "policy":
        name = document.policy_name
        text = document.policy_text
    else:
        name = document.procedure_name
        text = document.procedure_text
    return DocumentOut(
        id=document.id,
        document_type=document_type,
        control_id=control.control_id if control else "",
        name=name,
        text=text,
        responsibility_matrix=document.responsibility_matrix,
        version=document.version,
        author=document.author,
        approver=document.approver,
        approval_date=document.approval_date,
        review_date=document.review_date,
        status=document.status,
    )


def evidence_analysis_response(db: Session, analysis: EvidenceAnalysis) -> EvidenceAnalysisOut:
    control = db.get(CmmcControl, analysis.control_id)
    result = json.loads(analysis.analysis_result or "{}")
    objective_rows = []
    for objective_link in analysis.objectives:
        objective = db.get(AssessmentObjective, objective_link.objective_id)
        objective_rows.append(
            EvidenceObjectiveOut(
                id=objective_link.id,
                objective=f"{objective.label}. {objective.objective}" if objective else "",
                supported=objective_link.supported,
                notes=objective_link.notes,
            )
        )
    return EvidenceAnalysisOut(
        id=analysis.id,
        control_id=control.control_id if control else "",
        control_title=control.title if control else "",
        confidence_score=analysis.confidence_score,
        coverage_score=analysis.coverage_score,
        assessment_strength=analysis.assessment_strength,
        missing_evidence=result.get("missing_evidence", []),
        recommendations=result.get("recommendations", []),
        assessor_observations=result.get("assessor_observations", ""),
        objectives=objective_rows,
    )


def evidence_freshness_days(evidence: Evidence) -> int:
    haystack = f"{evidence.title} {evidence.file_name} {evidence.evidence_type}".lower()
    if any(term in haystack for term in ["vulnerability", "scan", "nessus", "qualys"]):
        return 30
    if any(term in haystack for term in ["access review", "quarterly", "account review"]):
        return 90
    if any(term in haystack for term in ["policy", "procedure", "training", "awareness"]):
        return 365
    return 180


def evidence_drift_state(evidence: Evidence) -> str:
    if evidence.review_status in {"Needs Replacement", "Rejected"}:
        return evidence.review_status
    if evidence.review_status != "Accepted":
        return evidence.review_status or "Under Review"
    if not evidence.review_date:
        return "Stale"
    try:
        reviewed_on = datetime.strptime(evidence.review_date, "%Y-%m-%d")
    except ValueError:
        return "Stale"
    age_days = (datetime.utcnow() - reviewed_on).days
    return "Stale" if age_days > evidence_freshness_days(evidence) else "Current"


def evidence_response(db: Session, evidence: Evidence) -> EvidenceOut:
    return EvidenceOut(
        id=evidence.id,
        title=evidence.title,
        file_name=evidence.file_name,
        file_type=evidence.file_type,
        document_type=evidence.document_type,
        data_classification=evidence.data_classification,
        contains_cui=evidence.contains_cui,
        contains_itar=evidence.contains_itar,
        contains_pii=evidence.contains_pii,
        intended_control_id=evidence.intended_control_id,
        managed_poam_id=evidence.managed_poam_id,
        evidence_request_id=evidence.evidence_request_id,
        evidence_type=evidence.evidence_type,
        owner=evidence.owner,
        status=evidence.status,
        review_status=evidence.review_status,
        reviewer=evidence.reviewer,
        review_date=evidence.review_date,
        review_notes=evidence.review_notes,
        drift_state=evidence_drift_state(evidence),
        uploaded_by=evidence.uploaded_by,
        uploaded_at=evidence.uploaded_at.isoformat(),
        analyses=[evidence_analysis_response(db, analysis) for analysis in evidence.analyses],
    )


def evidence_request_response(db: Session, request: EvidenceRequest) -> EvidenceRequestOut:
    linked = db.query(Evidence).filter_by(evidence_request_id=request.id).all()
    return EvidenceRequestOut(
        id=request.id,
        control_id=request.control_id,
        objective_label=request.objective_label,
        request_title=request.request_title,
        evidence_needed=request.evidence_needed,
        requested_from=request.requested_from,
        due_date=request.due_date,
        priority=request.priority,
        status=request.status,
        source_type=request.source_type,
        source_id=request.source_id,
        notes=request.notes,
        linked_evidence_count=len(linked),
        accepted_evidence_count=sum(1 for item in linked if item.review_status == "Accepted"),
        created_at=request.created_at.isoformat(),
        updated_at=request.updated_at.isoformat(),
    )


def evidence_request_dashboard(db: Session, q: str = "", status: str = "", control_id: str = "", owner: str = "") -> EvidenceRequestDashboardOut:
    rows = db.query(EvidenceRequest).order_by(EvidenceRequest.updated_at.desc()).all()
    today = datetime.utcnow().date()
    filtered = []
    for request in rows:
        haystack = f"{request.request_title} {request.evidence_needed} {request.control_id} {request.objective_label} {request.requested_from} {request.priority} {request.status} {request.notes}".lower()
        if q and q.lower() not in haystack:
            continue
        if status and request.status != status:
            continue
        if control_id and control_id.lower() not in request.control_id.lower():
            continue
        if owner and owner.lower() not in request.requested_from.lower():
            continue
        filtered.append(request)

    def is_overdue(request: EvidenceRequest) -> bool:
        due = parse_calendar_date(request.due_date)
        return bool(due and due.date() < today and request.status not in {"Accepted", "Rejected"})

    return EvidenceRequestDashboardOut(
        total=len(rows),
        draft=sum(1 for item in rows if item.status == "Draft"),
        sent=sum(1 for item in rows if item.status == "Sent"),
        submitted=sum(1 for item in rows if item.status == "Submitted"),
        accepted=sum(1 for item in rows if item.status == "Accepted"),
        rejected=sum(1 for item in rows if item.status == "Rejected"),
        overdue=sum(1 for item in rows if is_overdue(item)),
        rows=[evidence_request_response(db, item) for item in filtered],
    )


def sync_evidence_request_status(db: Session, request_id: int | None) -> None:
    if not request_id:
        return
    request = db.get(EvidenceRequest, request_id)
    if not request:
        return
    linked = db.query(Evidence).filter_by(evidence_request_id=request.id).all()
    if any(item.review_status == "Accepted" for item in linked):
        request.status = "Accepted"
    elif any(item.review_status in {"Under Review", "Needs Replacement", "Rejected"} for item in linked):
        request.status = "Submitted"


def analyze_and_store_evidence(db: Session, evidence: Evidence, intended_control_id: str = "") -> None:
    intended_control = db.query(CmmcControl).filter_by(control_id=intended_control_id).first() if intended_control_id else None
    controls = [intended_control] if intended_control else db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    ranked = []
    for control in controls:
        if not control:
            continue
        objectives = [f"{objective.label}. {objective.objective}" for objective in control.objectives]
        stored_evidence = [row.artifact for row in db.query(EvidenceRequirement).filter_by(control_id=control.id).all()]
        evidence_items = evidence_for_control(control, stored_evidence)
        score = score_control_match(control, objectives, evidence_items, evidence.extracted_text, evidence.file_name)
        if intended_control or score >= 18:
            ranked.append((score, control, objectives, evidence_items))
    ranked.sort(key=lambda item: item[0], reverse=True)
    for _, control, objectives, evidence_items in ranked[:5]:
        result = analyze_evidence_against_control(control, objectives, evidence_items, evidence.extracted_text, evidence.file_name)
        analysis = EvidenceAnalysis(
            evidence_id=evidence.id,
            control_id=control.id,
            confidence_score=int(result["confidence_score"]),
            coverage_score=int(result["coverage_score"]),
            assessment_strength=str(result["assessment_strength"]),
            analysis_result=json.dumps(result),
        )
        db.add(analysis)
        db.flush()
        objective_results = result.get("objective_results", [])
        objective_rows = db.query(AssessmentObjective).filter_by(control_id=control.id).order_by(AssessmentObjective.label).all()
        for objective, objective_result in zip(objective_rows, objective_results):
            db.add(
                EvidenceObjective(
                    evidence_analysis_id=analysis.id,
                    objective_id=objective.id,
                    supported=str(objective_result.get("supported", "Not Supported")),
                    notes=str(objective_result.get("notes", "")),
                )
            )


def clear_evidence_analysis(db: Session, evidence_id: int) -> None:
    analyses = db.query(EvidenceAnalysis).filter_by(evidence_id=evidence_id).all()
    for analysis in analyses:
        db.query(EvidenceObjective).filter_by(evidence_analysis_id=analysis.id).delete()
        db.delete(analysis)


def save_evidence_payload(payload: EvidenceUploadIn, org_id: int, existing_path: str = "") -> tuple[Path, str, str]:
    allowed = {"pdf", "docx", "xlsx", "csv", "txt", "png", "jpg", "jpeg", "zip"}
    suffix = Path(payload.file_name or "evidence.txt").suffix.lower().lstrip(".")
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Supported evidence types: PDF, DOCX, XLSX, CSV, TXT, PNG, JPEG, ZIP.")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", payload.file_name or f"evidence.{suffix}")
    storage_path = UPLOAD_DIR / f"{org_id}_{safe_name}"
    counter = 1
    while storage_path.exists() and str(storage_path) != existing_path:
        storage_path = UPLOAD_DIR / f"{org_id}_{counter}_{safe_name}"
        counter += 1
    try:
        storage_path.write_bytes(base64.b64decode(payload.content_base64))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="File content must be valid base64.") from exc
    return storage_path, suffix, safe_name


def save_compliance_payload(payload: ComplianceDocumentUploadIn, org_id: int) -> tuple[Path, str, str]:
    allowed = {"pdf", "docx", "xlsx", "csv", "txt", "png", "jpg", "jpeg", "zip"}
    suffix = Path(payload.file_name or "document.txt").suffix.lower().lstrip(".")
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Supported document types: PDF, DOCX, XLSX, CSV, TXT, PNG, JPEG, ZIP.")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", payload.file_name or f"document.{suffix}")
    storage_path = COMPLIANCE_UPLOAD_DIR / f"{org_id}_{safe_name}"
    counter = 1
    while storage_path.exists():
        storage_path = COMPLIANCE_UPLOAD_DIR / f"{org_id}_{counter}_{safe_name}"
        counter += 1
    try:
        storage_path.write_bytes(base64.b64decode(payload.content_base64))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="File content must be valid base64.") from exc
    return storage_path, suffix, safe_name


def classify_compliance_document(file_name: str, text: str, requested_type: str = "") -> str:
    if requested_type:
        return requested_type
    haystack = f"{file_name} {text}".lower()
    candidates = [
        ("SSP", ["system security plan", "ssp", "system boundary", "cui data flow"]),
        ("POA&M", ["poa&m", "poam", "plan of action", "milestone", "weakness", "due date"]),
        ("Policy", ["policy", "scope", "enforcement", "review cycle"]),
        ("Procedure", ["procedure", "step", "responsible", "records", "trigger"]),
        ("Incident Response Plan", ["incident response", "incident handling", "ir plan"]),
        ("Contingency Plan", ["contingency", "backup", "recovery", "restore"]),
        ("Network Diagram", ["network diagram", "firewall", "router", "vlan", "architecture"]),
        ("CUI Flow Diagram", ["cui flow", "data flow", "cui created", "cui stored", "cui transmitted"]),
    ]
    for label, keywords in candidates:
        if any(keyword in haystack for keyword in keywords):
            return label
    return "Compliance Document"


def extract_control_refs(db: Session, text: str, file_name: str) -> list[tuple[CmmcControl, int, str]]:
    haystack = f"{file_name}\n{text}"
    refs = {match.upper() for match in re.findall(r"\b[A-Z]{2}\.L2-\d\.\d+\.\d+\b", haystack, flags=re.IGNORECASE)}
    mapped: dict[str, tuple[CmmcControl, int, str]] = {}
    lowered = haystack.lower()
    for control in db.query(CmmcControl).order_by(CmmcControl.control_id).all():
        if control.control_id in refs:
            mapped[control.control_id] = (control, 95, "Control ID explicitly referenced in uploaded document.")
        elif control.title.lower() in lowered:
            mapped[control.control_id] = (control, 75, "Control title appears in uploaded document.")
    return sorted(mapped.values(), key=lambda item: item[0].control_id)


def first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()[:255]
    return ""


def extract_document_metadata(document_type: str, text: str, file_name: str) -> dict[str, object]:
    if document_type == "SSP":
        parsed = parse_ssp(file_name, text)
    elif document_type == "POA&M":
        parsed = parse_poam(file_name, text)
    elif document_type == "Policy":
        parsed = parse_policy(file_name, text)
    else:
        parsed = parse_document(file_name, text, document_type)
    owners = parsed.get("owners", [])
    review_dates = parsed.get("review_dates", [])
    return {
        "title": parsed.get("document_name") or first_match([r"^(.*?(?:Policy|Procedure|Plan|SSP|System Security Plan).*)$", r"^Title[:\s]+(.+)$"], text) or Path(file_name).stem.replace("_", " "),
        "version": parsed.get("version") or first_match([r"\bVersion[:\s]+([A-Za-z0-9.\-]+)", r"\bRev(?:ision)?[:\s]+([A-Za-z0-9.\-]+)"], text),
        "owner": owners[0] if isinstance(owners, list) and owners else first_match([r"\bOwner[:\s]+(.+)", r"\bDocument Owner[:\s]+(.+)", r"\bSystem Owner[:\s]+(.+)"], text),
        "review_date": review_dates[0] if isinstance(review_dates, list) and review_dates else first_match([r"\bReview Date[:\s]+([A-Za-z0-9,./\- ]+)", r"\bLast Reviewed[:\s]+([A-Za-z0-9,./\- ]+)"], text),
        "document_type": document_type,
        "controls": parsed.get("controls", []),
        "owners": owners,
        "review_dates": review_dates,
        "evidence_references": parsed.get("evidence_references", []),
        "parsed": parsed,
    }


def extract_entities(document_type: str, text: str) -> list[dict[str, str]]:
    entity_patterns = {
        "System Boundary": [r"(?:System Boundary|Boundary Description)[:\s]+(.{20,500})"],
        "CUI Asset": [r"(?:CUI Assets?|CUI Environment|CUI Description)[:\s]+(.{10,400})"],
        "External Provider": [r"(?:External (?:Service )?Providers?|MSP|MSSP|Cloud Provider)[:\s]+(.{5,300})"],
        "Role": [r"(?:Roles and Responsibilities|Responsible Parties|Owner)[:\s]+(.{5,300})"],
        "Review Date": [r"(?:Review Date|Last Reviewed)[:\s]+([A-Za-z0-9,./\- ]+)"],
        "POA&M Status": [r"(?:Status)[:\s]+([A-Za-z ]{3,40})"],
        "Due Date": [r"(?:Due Date|Target Date)[:\s]+([A-Za-z0-9,./\- ]+)"],
    }
    entities: list[dict[str, str]] = []
    for entity_type, patterns in entity_patterns.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                value = re.sub(r"\s+", " ", match.group(1)).strip(" .|-")[:500]
                if value:
                    entities.append({"entity_type": entity_type, "entity_value": value, "source_excerpt": match.group(0)[:700]})
    for provider in ["Microsoft 365 GCC High", "GCC High", "Entra ID", "Intune", "Defender", "Sentinel", "Duo", "CrowdStrike", "Nessus", "Kahua", "K2", "Azure", "AWS", "Google Cloud"]:
        if provider.lower() in text.lower():
            entities.append({"entity_type": "Technology", "entity_value": provider, "source_excerpt": provider})
    return entities[:80]


def compliance_document_response(db: Session, document: ComplianceDocument) -> ComplianceDocumentOut:
    mappings = []
    for mapping in db.query(ControlMapping).filter_by(document_id=document.id).all():
        control = db.get(CmmcControl, mapping.control_id)
        mappings.append(ControlMappingOut(control_id=control.control_id if control else "", control_title=control.title if control else "", mapping_type=mapping.mapping_type, confidence_score=mapping.confidence_score, rationale=mapping.rationale))
    entities = [
        DocumentEntityOut(entity_type=row.entity_type, entity_value=row.entity_value, source_excerpt=row.source_excerpt)
        for row in db.query(DocumentEntity).filter_by(document_id=document.id).order_by(DocumentEntity.entity_type).all()
    ]
    return ComplianceDocumentOut(
        id=document.id,
        title=document.title,
        document_type=document.document_type,
        data_classification=document.data_classification,
        contains_cui=document.contains_cui,
        contains_itar=document.contains_itar,
        contains_pii=document.contains_pii,
        file_name=document.file_name,
        file_type=document.file_type,
        version=document.version,
        owner=document.owner,
        review_date=document.review_date,
        status=document.status,
        uploaded_at=document.uploaded_at.isoformat(),
        mappings=mappings,
        entities=entities,
    )


def clear_compliance_document_graph(db: Session, document_id: int) -> None:
    db.query(ControlMapping).filter_by(document_id=document_id).delete()
    db.query(DocumentEntity).filter_by(document_id=document_id).delete()
    db.query(EvidenceRelationship).filter_by(source_type="document", source_id=document_id).delete()


def rebuild_compliance_document_graph(db: Session, document: ComplianceDocument) -> None:
    clear_compliance_document_graph(db, document.id)
    for control, confidence, rationale in extract_control_refs(db, document.extracted_text, document.file_name):
        db.add(ControlMapping(document_id=document.id, control_id=control.id, mapping_type="Document Reference", confidence_score=confidence, rationale=rationale))
        db.add(EvidenceRelationship(source_type="document", source_id=document.id, target_type="control", target_id=control.control_id, relationship_type="maps_to", notes=rationale))
    for entity in extract_entities(document.document_type, document.extracted_text):
        db.add(DocumentEntity(document_id=document.id, **entity))


def control_evidence_source_response(source: ControlEvidenceSource) -> ControlEvidenceSourceOut:
    return ControlEvidenceSourceOut(
        id=source.id,
        evidence_name=source.evidence_name,
        source_type=source.source_type,
        connected_system=source.connected_system,
        collection_method=source.collection_method,
        review_frequency=source.review_frequency,
        required=source.required,
        description=source.description,
    )


def monitoring_rule_response(rule: MonitoringRule) -> MonitoringRuleOut:
    return MonitoringRuleOut(
        id=rule.id,
        rule_name=rule.rule_name,
        source_system=rule.source_system,
        condition=rule.condition,
        severity=rule.severity,
        enabled=rule.enabled,
    )


def drift_alert_response(db: Session, alert: DriftAlert) -> DriftAlertOut:
    control = db.get(CmmcControl, alert.control_id)
    return DriftAlertOut(
        id=alert.id,
        control_id=control.control_id if control else "",
        control_title=control.title if control else "",
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        description=alert.description,
        recommended_action=alert.recommended_action,
        status=alert.status,
        created_at=alert.created_at.isoformat(),
    )


def primary_evidence_by_control(db: Session) -> dict[str, list[EvidenceAnalysis]]:
    grouped: dict[str, list[EvidenceAnalysis]] = {}
    for control_id, _evidence, analysis in primary_evidence_analyses(db):
        grouped.setdefault(control_id, []).append(analysis)
    return grouped


def documentation_by_control(db: Session) -> set[str]:
    mapped = set()
    for mapping in db.query(ControlMapping).all():
        control = db.get(CmmcControl, mapping.control_id)
        if control:
            mapped.add(control.control_id)
    return mapped


def ensure_drift_alerts(db: Session) -> None:
    evidence_map = primary_evidence_by_control(db)
    document_map = documentation_by_control(db)
    controls = db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    updated = False
    for control in controls:
        has_evidence = bool(evidence_map.get(control.control_id))
        has_documentation = control.control_id in document_map
        should_alert = has_documentation and not has_evidence
        existing = db.query(DriftAlert).filter_by(control_id=control.id, alert_type="Missing Evidence", status="Open").first()
        if should_alert and not existing:
            db.add(
                DriftAlert(
                    control_id=control.id,
                    alert_type="Missing Evidence",
                    severity="Medium",
                    title=f"{control.control_id} evidence collection gap",
                    description=f"{control.control_id} is mapped to uploaded compliance documentation, but no primary evidence item is assigned to this control.",
                    recommended_action="Upload or automatically collect evidence that supports the mapped assessment objectives, then re-run readiness review.",
                )
            )
            updated = True
        if not should_alert and existing:
            existing.status = "Resolved"
            updated = True
    if updated:
        db.commit()


def control_status(control_id: str, evidence_count: int, required_sources: int, open_alerts: int, documented: bool) -> str:
    if open_alerts:
        return "At Risk"
    if evidence_count and documented:
        return "Implemented"
    if evidence_count or documented:
        return "Partially Implemented"
    if required_sources:
        return "Not Implemented"
    return "Not Implemented"


def control_evidence_map_response(db: Session, control: CmmcControl, evidence_map: dict[str, list[EvidenceAnalysis]] | None = None, document_map: set[str] | None = None) -> ControlEvidenceMapOut:
    evidence_map = evidence_map if evidence_map is not None else primary_evidence_by_control(db)
    document_map = document_map if document_map is not None else documentation_by_control(db)
    sources = db.query(ControlEvidenceSource).filter_by(control_id=control.id).order_by(ControlEvidenceSource.required.desc(), ControlEvidenceSource.source_type, ControlEvidenceSource.evidence_name).all()
    rules = db.query(MonitoringRule).filter_by(control_id=control.id).order_by(MonitoringRule.severity.desc(), MonitoringRule.rule_name).all()
    open_alerts = db.query(DriftAlert).filter_by(control_id=control.id, status="Open").count()
    evidence_count = len(evidence_map.get(control.control_id, []))
    required_sources = sum(1 for source in sources if source.required == "true")
    connected_sources = sum(1 for source in sources if source.collection_method != "Manual Upload")
    manual_sources = sum(1 for source in sources if source.collection_method == "Manual Upload")
    frequencies = [source.review_frequency for source in sources if source.required == "true"]
    return ControlEvidenceMapOut(
        control_id=control.control_id,
        control_title=control.title,
        family=control.family,
        status=control_status(control.control_id, evidence_count, required_sources, open_alerts, control.control_id in document_map),
        evidence_count=evidence_count,
        required_sources=required_sources,
        connected_sources=connected_sources,
        manual_sources=manual_sources,
        open_alerts=open_alerts,
        review_frequency=frequencies[0] if frequencies else "Quarterly",
        evidence_sources=[control_evidence_source_response(source) for source in sources],
        monitoring_rules=[monitoring_rule_response(rule) for rule in rules],
    )


def graph_item(id_value: object, name: str, item_type: str, source: str, status: str = "", detail: str = "") -> ControlGraphItemOut:
    return ControlGraphItemOut(id=str(id_value), name=name, item_type=item_type, source=source, status=status, detail=detail)


def control_graph_response(db: Session, control: CmmcControl) -> ControlGraphOut:
    ensure_drift_alerts(db)
    mapping = control_evidence_map_response(db, control)
    policies: list[ControlGraphItemOut] = []
    procedures: list[ControlGraphItemOut] = []
    ssp_refs: list[ControlGraphItemOut] = []
    evidence_items: list[ControlGraphItemOut] = []
    poam_items: list[ControlGraphItemOut] = []

    for document_mapping in db.query(ControlMapping).filter_by(control_id=control.id).all():
        document = db.get(ComplianceDocument, document_mapping.document_id)
        if not document:
            continue
        item = graph_item(document.id, document.title, document.document_type, "Uploaded Document", document.status, document_mapping.rationale)
        document_type = document.document_type.lower()
        if "policy" in document_type:
            policies.append(item)
        elif "procedure" in document_type:
            procedures.append(item)
        elif "ssp" in document_type or "system security plan" in document_type:
            ssp_refs.append(item)
        else:
            ssp_refs.append(item)

    policy = db.query(Policy).filter_by(control_id=control.id).order_by(Policy.updated_at.desc()).first()
    if policy:
        policies.append(graph_item(policy.id, policy.policy_name, "Policy", "Generated Document", policy.status, f"Version {policy.version}"))

    procedure = db.query(Procedure).filter_by(control_id=control.id).order_by(Procedure.updated_at.desc()).first()
    if procedure:
        procedures.append(graph_item(procedure.id, procedure.procedure_name, "Procedure", "Generated Document", procedure.status, f"Version {procedure.version}"))

    for evidence in db.query(Evidence).order_by(Evidence.uploaded_at.desc()).all():
        if control.control_id not in evidence_control_ids(db, evidence):
            continue
        best = next((analysis for analysis in evidence.analyses if db.get(CmmcControl, analysis.control_id) and db.get(CmmcControl, analysis.control_id).control_id == control.control_id), None)
        detail = f"Coverage {best.coverage_score}%, confidence {best.confidence_score}%" if best else evidence.evidence_type
        evidence_items.append(graph_item(evidence.id, evidence.title, evidence.file_type, "Evidence Library", evidence.status, detail))

    for output in db.query(GeneratedOutput).filter_by(control_id=control.id).all():
        for item in db.query(PoamItem).filter_by(generated_output_id=output.id).all():
            poam_items.append(graph_item(item.id, item.gap[:100], "POA&M Item", "POA&M", item.status, item.owner))
    for item in db.query(ManagedPoamItem).filter_by(control_id=control.control_id).all():
        poam_items.append(graph_item(f"managed-{item.id}", item.gap_statement[:100], "Managed POA&M Item", "POA&M Management", item.status, item.owner))

    alerts = db.query(DriftAlert).filter_by(control_id=control.id, status="Open").order_by(DriftAlert.created_at.desc()).all()
    return ControlGraphOut(
        control_id=control.control_id,
        control_title=control.title,
        family=control.family,
        requirement=control.requirement,
        status=mapping.status,
        policies=policies,
        procedures=procedures,
        ssp_references=ssp_refs,
        evidence=evidence_items,
        poam_items=poam_items,
        alerts=[drift_alert_response(db, alert) for alert in alerts],
        evidence_sources=mapping.evidence_sources,
        monitoring_rules=mapping.monitoring_rules,
    )


def objective_workspace_response(db: Session, control: CmmcControl) -> ControlObjectiveWorkspaceOut:
    objective_rows = db.query(AssessmentObjective).filter_by(control_id=control.id).order_by(AssessmentObjective.label).all()
    output_rows: list[ControlObjectiveOut] = []
    supported_total = 0
    partial_total = 0

    for objective in objective_rows:
        evidence_items: list[ObjectiveEvidenceItemOut] = []
        recommendations: list[str] = []
        missing_evidence: list[str] = []
        notes: list[str] = []
        for support in db.query(EvidenceObjective).filter_by(objective_id=objective.id).all():
            analysis = db.get(EvidenceAnalysis, support.evidence_analysis_id)
            if not analysis or analysis.control_id != control.id:
                continue
            evidence = db.get(Evidence, analysis.evidence_id)
            if not evidence:
                continue
            result = json.loads(analysis.analysis_result or "{}")
            recommendations.extend(str(item) for item in result.get("recommendations", []))
            missing_evidence.extend(str(item) for item in result.get("missing_evidence", []))
            if support.notes:
                notes.append(support.notes)
            evidence_items.append(
                ObjectiveEvidenceItemOut(
                    evidence_id=evidence.id,
                    evidence_title=evidence.title,
                    file_name=evidence.file_name,
                    evidence_type=evidence.evidence_type,
                    support_record_id=support.id,
                    supported=support.supported,
                    notes=support.notes,
                    coverage_score=analysis.coverage_score,
                    confidence_score=analysis.confidence_score,
                )
            )

        statuses = [item.supported for item in evidence_items]
        if "Supported" in statuses:
            status = "Supported"
            supported_total += 1
        elif "Partially Supported" in statuses:
            status = "Partially Supported"
            partial_total += 1
        else:
            status = "Not Supported"
        coverage_score = round(({"Supported": 1, "Partially Supported": 0.5}.get(status, 0) * 100))
        output_rows.append(
            ControlObjectiveOut(
                id=objective.id,
                label=objective.label,
                objective=objective.objective,
                status=status,
                evidence_count=len({item.evidence_id for item in evidence_items}),
                coverage_score=coverage_score,
                missing_evidence=list(dict.fromkeys(missing_evidence))[:5],
                recommendations=list(dict.fromkeys(recommendations))[:5],
                assessor_notes="\n".join(dict.fromkeys(notes)),
                evidence=evidence_items,
            )
        )

    total = len(objective_rows)
    readiness = round(((supported_total + partial_total * 0.5) / total) * 100) if total else 0
    return ControlObjectiveWorkspaceOut(
        control_id=control.control_id,
        control_title=control.title,
        family=control.family,
        requirement=control.requirement,
        readiness_score=readiness,
        supported_objectives=supported_total,
        partial_objectives=partial_total,
        total_objectives=total,
        objectives=output_rows,
    )


def primary_evidence_analyses(db: Session) -> list[tuple[str, Evidence, EvidenceAnalysis]]:
    primary = []
    for evidence in db.query(Evidence).all():
        if evidence.intended_control_id:
            analysis = next(
                (
                    item
                    for item in evidence.analyses
                    if (db.get(CmmcControl, item.control_id).control_id if db.get(CmmcControl, item.control_id) else "") == evidence.intended_control_id
                ),
                None,
            )
            if analysis:
                primary.append((evidence.intended_control_id, evidence, analysis))
            continue
        if len(evidence.analyses) == 1:
            control = db.get(CmmcControl, evidence.analyses[0].control_id)
            if control:
                primary.append((control.control_id, evidence, evidence.analyses[0]))
    return primary


def objective_coverage_for_analyses(db: Session, analyses: list[EvidenceAnalysis], control_id: int | None = None) -> tuple[int, int, int, int]:
    query = db.query(AssessmentObjective)
    if control_id is not None:
        query = query.filter_by(control_id=control_id)
    total_objectives = query.count()
    supported: set[int] = set()
    partial: set[int] = set()
    for analysis in analyses:
        for objective in analysis.objectives:
            if control_id is not None:
                objective_row = db.get(AssessmentObjective, objective.objective_id)
                if not objective_row or objective_row.control_id != control_id:
                    continue
            if objective.supported == "Supported":
                supported.add(objective.objective_id)
                partial.discard(objective.objective_id)
            elif objective.supported == "Partially Supported" and objective.objective_id not in supported:
                partial.add(objective.objective_id)
    objectives_with_evidence = len(supported | partial)
    coverage_score = round(((len(supported) + (len(partial) * 0.5)) / total_objectives) * 100) if total_objectives else 0
    return objectives_with_evidence, total_objectives, coverage_score, len(partial)


def objective_is_at_risk(db: Session, objective: AssessmentObjective) -> bool:
    supports = db.query(EvidenceObjective).filter_by(objective_id=objective.id).all()
    if not supports:
        return True
    has_supported_current = False
    for support in supports:
        if support.supported != "Supported":
            continue
        analysis = db.get(EvidenceAnalysis, support.evidence_analysis_id)
        evidence = db.get(Evidence, analysis.evidence_id) if analysis else None
        if evidence and evidence_drift_state(evidence) == "Current":
            has_supported_current = True
            break
    return not has_supported_current


def control_is_at_risk(db: Session, control: CmmcControl) -> bool:
    objectives = db.query(AssessmentObjective).filter_by(control_id=control.id).all()
    return any(objective_is_at_risk(db, objective) for objective in objectives)


def control_health_status(
    objective_coverage_score: int,
    accepted_evidence: int,
    needs_replacement: int,
    rejected: int,
    stale: int,
    poam_candidates: int,
) -> str:
    if rejected or needs_replacement or objective_coverage_score < 35:
        return "Critical"
    if stale or poam_candidates or accepted_evidence == 0 or objective_coverage_score < 75:
        return "At Risk"
    if objective_coverage_score < 100:
        return "Monitor"
    return "Healthy"


def control_health_rows(db: Session) -> list[ControlHealthRowOut]:
    rows: list[ControlHealthRowOut] = []
    primary_by_control: dict[str, list[tuple[Evidence, EvidenceAnalysis]]] = {}
    for control_id, evidence, analysis in primary_evidence_analyses(db):
        primary_by_control.setdefault(control_id, []).append((evidence, analysis))
    for control in db.query(CmmcControl).order_by(CmmcControl.family, CmmcControl.control_id).all():
        primary_rows = primary_by_control.get(control.control_id, [])
        analyses = [analysis for _evidence, analysis in primary_rows]
        objectives_with_evidence, total_objectives, objective_coverage_score, partial_objectives = objective_coverage_for_analyses(db, analyses, control.id)
        evidence_rows = [evidence for evidence, _analysis in primary_rows]
        accepted = sum(1 for evidence in evidence_rows if evidence.review_status == "Accepted")
        under_review = sum(1 for evidence in evidence_rows if evidence.review_status == "Under Review")
        needs_replacement = sum(1 for evidence in evidence_rows if evidence.review_status == "Needs Replacement")
        rejected = sum(1 for evidence in evidence_rows if evidence.review_status == "Rejected")
        stale = sum(1 for evidence in evidence_rows if evidence_drift_state(evidence) == "Stale")
        states = {evidence_drift_state(evidence) for evidence in evidence_rows}
        if not evidence_rows or accepted == 0:
            drift_state = "No Accepted Evidence"
        elif "Rejected" in states:
            drift_state = "Rejected"
        elif "Needs Replacement" in states:
            drift_state = "Needs Replacement"
        elif "Stale" in states:
            drift_state = "Stale"
        else:
            drift_state = "Current"
        poam_candidates = max(total_objectives - objectives_with_evidence, 0) + partial_objectives
        health_status = control_health_status(objective_coverage_score, accepted, needs_replacement, rejected, stale, poam_candidates)
        rows.append(
            ControlHealthRowOut(
                control_id=control.control_id,
                title=control.title,
                family=control.family,
                objective_coverage_score=objective_coverage_score,
                objectives_with_evidence=objectives_with_evidence,
                total_objectives=total_objectives,
                accepted_evidence=accepted,
                under_review_evidence=under_review,
                needs_replacement_evidence=needs_replacement,
                rejected_evidence=rejected,
                stale_evidence=stale,
                poam_candidates=poam_candidates,
                drift_state=drift_state,
                health_status=health_status,
            )
        )
    return rows


def evidence_control_ids(db: Session, evidence: Evidence) -> set[str]:
    control_ids = {evidence.intended_control_id} if evidence.intended_control_id else set()
    for analysis in evidence.analyses:
        control = db.get(CmmcControl, analysis.control_id)
        if control:
            control_ids.add(control.control_id)
    return {control_id for control_id in control_ids if control_id}


def evidence_control_terms(db: Session, evidence: Evidence) -> set[str]:
    terms = set(evidence_control_ids(db, evidence))
    for analysis in evidence.analyses:
        control = db.get(CmmcControl, analysis.control_id)
        if control:
            terms.update([control.control_id, control.title, control.family])
    return {term for term in terms if term}


def evidence_matches_query(db: Session, evidence: Evidence, query: str) -> bool:
    needle = query.strip().lower()
    if not needle:
        return True
    fields = [
        evidence.title,
        evidence.file_name,
        evidence.file_type,
        evidence.evidence_type,
        evidence.owner,
        evidence.status,
        evidence.uploaded_by,
        evidence.intended_control_id,
        evidence.extracted_text,
    ]
    for analysis in evidence.analyses:
        control = db.get(CmmcControl, analysis.control_id)
        fields.extend(
            [
                control.control_id if control else "",
                control.title if control else "",
                control.family if control else "",
                analysis.assessment_strength,
                analysis.analysis_result,
            ]
        )
    return any(needle in str(field or "").lower() for field in fields)


def evidence_matches_control_filter(db: Session, evidence: Evidence, control_filter: str) -> bool:
    raw_filter = control_filter.strip()
    needle = raw_filter.lower()
    if not needle:
        return True
    control_id_match = re.search(r"[A-Z]{2}\.L2-\d\.\d+\.\d+", raw_filter, flags=re.IGNORECASE)
    if control_id_match:
        selected_control_id = control_id_match.group(0).lower()
        return any(selected_control_id == control_id.lower() for control_id in evidence_control_ids(db, evidence))
    return any(needle in term.lower() for term in evidence_control_terms(db, evidence))


def create_document_version(db: Session, document: Policy | Procedure, document_type: str) -> None:
    text = document.policy_text if document_type == "policy" else document.procedure_text
    db.add(
        DocumentVersion(
            document_type=document_type,
            document_id=document.id,
            version=document.version,
            document_text=text,
            responsibility_matrix=document.responsibility_matrix,
            author=document.author,
            status=document.status,
        )
    )


def ssp_response(db: Session, ssp: SSPDocument) -> SSPDocumentOut:
    sections = db.query(SSPSection).filter_by(ssp_document_id=ssp.id).order_by(SSPSection.sort_order).all()
    return SSPDocumentOut(
        id=ssp.id,
        system_id=ssp.system_id,
        version=ssp.version,
        status=ssp.status,
        completeness_score=ssp.completeness_score,
        sections=[
            SSPSectionOut(id=s.id, section_name=s.section_name, section_content=s.section_content, sort_order=s.sort_order)
            for s in sections
        ],
    )


def latest_control_implementations(db: Session) -> str:
    rows = []
    controls = db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    for control in controls:
        output = db.query(GeneratedOutput).filter_by(control_id=control.id).order_by(GeneratedOutput.updated_at.desc()).first()
        statement = output.implementation_statement if output else "Implementation statement has not been generated; document during SSP review."
        rows.append(f"{control.control_id} - {control.title}\nImplementation: {statement}")
    return "\n\n".join(rows)


def ssp_completeness(system: System, sections: list[tuple[str, str]]) -> int:
    checks = [
        system.system_name,
        system.system_owner,
        system.description,
        system.boundary_description,
        system.cui_description,
        system.external_providers,
        any("Implementation statement has not been generated" not in content for name, content in sections if name == "Control Implementations"),
        system.cui_created or system.cui_stored or system.cui_transmitted or system.cui_archived,
        system.infrastructure,
        system.security_stack,
    ]
    return int((sum(1 for item in checks if item) / len(checks)) * 100)


def build_network_diagram(system: System, profile: CompanyProfile) -> str:
    infra = system.infrastructure or profile.cloud_environment
    stack = system.security_stack or f"{profile.mfa_solution}; {profile.endpoint_management}"
    return "\n".join(
        [
            "Remote Users",
            "  |",
            f"{profile.mfa_solution or 'Identity Provider + MFA'}",
            "  |",
            infra or "Cloud / On-Prem Environment",
            "  |",
            profile.cui_environment or "CUI applications and repositories",
            "  |",
            profile.endpoint_management or "Managed endpoints",
            "  |",
            stack or "Security monitoring stack",
        ]
    )


def build_ssp_sections(db: Session, profile: CompanyProfile, system: System) -> list[tuple[str, str]]:
    controls = latest_control_implementations(db)
    cui_flow = (
        f"CUI is created at: {system.cui_created or 'To be confirmed'}. "
        f"CUI is stored in: {system.cui_stored or profile.cui_environment}. "
        f"CUI is transmitted through: {system.cui_transmitted or 'approved encrypted business channels'}. "
        f"CUI is archived in: {system.cui_archived or profile.backup_solution or 'approved backup/archive repositories'}."
    )
    return [
        ("System Identification", f"System Name: {system.system_name}\nSystem Owner: {system.system_owner}\nData Owner: {system.data_owner or 'To be assigned'}\nVersion: 1.0\nStatus: Draft"),
        ("System Description", f"{system.description}\n\nBusiness Function: {system.business_function or 'Supports business operations involving CUI.'}"),
        ("System Boundary", f"{system.boundary_description}\n\nThe boundary includes systems, users, endpoints, cloud services, external providers, and data flows used to store, process, transmit, or protect CUI."),
        ("Authorized Users", f"Authorized users include employees, contractors, administrators, system owners, and external support personnel approved through {profile.ticketing_system or 'the access request process'}. Access is removed through {profile.access_removal_process}."),
        ("Environment of Operation", f"Locations: {profile.locations}\nInfrastructure: {system.infrastructure or profile.cloud_environment}\nSecurity Stack: {system.security_stack or profile.mfa_solution + '; ' + profile.endpoint_management}"),
        ("External Service Providers", system.external_providers or profile.msp_involvement or "External service providers must be identified and documented."),
        ("Roles and Responsibilities", f"System Owner: {system.system_owner}\nData Owner: {system.data_owner or 'To be assigned'}\nIT/Security: operates identity, endpoint, monitoring, backup, and access controls.\nCompliance Owner: maintains SSP, policies, procedures, POA&M references, and assessment evidence."),
        ("Control Implementations", controls),
        ("Connections to Other Systems", f"Connections include {system.infrastructure or profile.cloud_environment}, identity services, managed endpoints, backup services, security monitoring, and approved external provider connections. Each connection must have an owner, purpose, authorization, and CUI impact review."),
        ("CUI Data Flow", cui_flow),
        ("Network Architecture", f"Architecture Narrative:\nRemote users authenticate through {profile.mfa_solution or 'MFA'} to access {system.infrastructure or profile.cloud_environment}. Managed endpoints are controlled by {profile.endpoint_management or 'endpoint management tooling'} and monitored by the security stack.\n\nDiagram:\n{build_network_diagram(system, profile)}"),
        ("Security Requirements", "The SSP maps CMMC Level 2 / NIST SP 800-171 requirements across AC, AT, AU, CM, IA, IR, MA, MP, PE, PS, RA, CA, SC, and SI. Detailed implementation statements are pulled into the Control Implementations section."),
        ("Continuous Monitoring", f"Control effectiveness is monitored through access reviews, vulnerability management, audit log review, incident tracking, backup monitoring, endpoint compliance, and POA&M updates recorded in {profile.ticketing_system or 'the tracking system'}."),
        ("POA&M References", "Open findings, missing evidence, assumptions, and incomplete implementations should be recorded as POA&M items with owner, target date, risk, milestones, and closure evidence."),
        ("SSP Quality Checks", "\n".join([
            f"Missing boundary: {'No' if system.boundary_description else 'Yes'}",
            f"Missing owner: {'No' if system.system_owner else 'Yes'}",
            f"Missing CUI description: {'No' if system.cui_description else 'Yes'}",
            f"Missing external service provider: {'No' if system.external_providers or profile.msp_involvement else 'Yes'}",
            "Missing control implementation: Review Control Implementations section for placeholder text.",
        ])),
    ]


def poam_rows(db: Session, ssp: SSPDocument) -> list[list[str]]:
    rows = []
    outputs = db.query(GeneratedOutput).order_by(GeneratedOutput.updated_at.desc()).all()
    for output in outputs:
        control = db.get(CmmcControl, output.control_id)
        if not output.gaps_assumptions.strip():
            continue
        status = "Open" if any(word in output.gaps_assumptions.lower() for word in ["missing", "must", "assumption", "gap", "confirm"]) else "Monitor"
        rows.append(
            [
                control.control_id if control else "",
                control.title if control else "",
                output.gaps_assumptions,
                "Compliance Owner",
                status,
                "Medium",
                "Assign owner, validate evidence, update implementation statement, and attach closure evidence.",
                "To be assigned",
                "Open",
            ]
        )
    for item in db.query(PoamItem).order_by(PoamItem.id).all():
        output = db.get(GeneratedOutput, item.generated_output_id)
        control = db.get(CmmcControl, output.control_id) if output else None
        rows.append(
            [
                control.control_id if control else "",
                control.title if control else "",
                item.gap,
                item.owner,
                item.status,
                "To be assessed",
                "Document corrective action milestones and required evidence.",
                "To be assigned",
                item.status,
            ]
        )
    if rows:
        return rows
    system = db.get(System, ssp.system_id)
    return [[
        "",
        system.system_name if system else "System",
        "No open POA&M items have been generated yet.",
        "Compliance Owner",
        "Draft",
        "To be assessed",
        "Generate control outputs and record gaps to populate this workbook.",
        "To be assigned",
        "Not started",
    ]]


def family_items_for_control(db: Session, control: CmmcControl) -> list[dict[str, object]]:
    family_controls = db.query(CmmcControl).filter_by(family=control.family).order_by(CmmcControl.control_id).all()
    items = []
    for family_control in family_controls:
        objectives = [
            f"{objective.label}. {objective.objective}"
            for objective in db.query(AssessmentObjective).filter_by(control_id=family_control.id).order_by(AssessmentObjective.label).all()
        ]
        items.append(
            {
                "control_id": family_control.control_id,
                "title": family_control.title,
                "requirement": family_control.requirement,
                "objectives": objectives,
            }
        )
    return items


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/company-profiles", response_model=CompanyProfileOut)
def create_company_profile(payload: CompanyProfileIn, db: Session = Depends(get_db)) -> CompanyProfile:
    org = db.query(Organization).first() or Organization(name="Default Organization")
    db.add(org)
    db.flush()
    profile = CompanyProfile(organization_id=org.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/api/company-profiles/latest", response_model=CompanyProfileOut)
def latest_company_profile(db: Session = Depends(get_db)) -> CompanyProfile:
    profile = db.query(CompanyProfile).order_by(CompanyProfile.updated_at.desc()).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No company profile exists yet.")
    return profile


@app.post("/api/systems", response_model=SystemOut)
def create_system(payload: SystemIn, db: Session = Depends(get_db)) -> System:
    org = db.query(Organization).first() or Organization(name="Default Organization")
    db.add(org)
    db.flush()
    system = System(organization_id=org.id, **payload.model_dump())
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


@app.get("/api/systems", response_model=list[SystemOut])
def list_systems(db: Session = Depends(get_db)) -> list[System]:
    return db.query(System).order_by(System.updated_at.desc()).all()


@app.get("/api/controls", response_model=list[ControlOut])
def list_controls(db: Session = Depends(get_db)) -> list[ControlOut]:
    controls = db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    return [
        ControlOut(id=c.id, control_id=c.control_id, family=c.family, title=c.title, requirement=c.requirement)
        for c in controls
    ]


@app.get("/api/controls/{control_id}", response_model=ControlOut)
def get_control(control_id: str, db: Session = Depends(get_db)) -> ControlOut:
    control = db.query(CmmcControl).filter_by(control_id=control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    objectives = [f"{obj.label}. {obj.objective}" for obj in control.objectives]
    stored_evidence = [row.artifact for row in db.query(EvidenceRequirement).filter_by(control_id=control.id).all()]
    evidence = evidence_for_control(control, stored_evidence)
    return ControlOut(
        id=control.id,
        control_id=control.control_id,
        family=control.family,
        title=control.title,
        requirement=control.requirement,
        objectives=objectives,
        evidence=evidence,
    )


@app.get("/api/controls/{control_id}/graph", response_model=ControlGraphOut)
def get_control_graph(control_id: str, db: Session = Depends(get_db)) -> ControlGraphOut:
    control = db.query(CmmcControl).filter_by(control_id=control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    return control_graph_response(db, control)


@app.get("/api/controls/{control_id}/objectives", response_model=ControlObjectiveWorkspaceOut)
def get_control_objectives(control_id: str, db: Session = Depends(get_db)) -> ControlObjectiveWorkspaceOut:
    control = db.query(CmmcControl).filter_by(control_id=control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    return objective_workspace_response(db, control)


@app.put("/api/evidence/objectives/{support_record_id}", response_model=ControlObjectiveWorkspaceOut)
def update_evidence_objective(support_record_id: int, payload: EvidenceObjectiveUpdate, db: Session = Depends(get_db)) -> ControlObjectiveWorkspaceOut:
    support = db.get(EvidenceObjective, support_record_id)
    if not support:
        raise HTTPException(status_code=404, detail="Objective support record not found.")
    if payload.supported not in {"Supported", "Partially Supported", "Not Supported"}:
        raise HTTPException(status_code=400, detail="Supported status must be Supported, Partially Supported, or Not Supported.")
    previous_status = support.supported
    support.supported = payload.supported
    support.notes = payload.notes
    analysis = db.get(EvidenceAnalysis, support.evidence_analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Evidence analysis not found.")
    control = db.get(CmmcControl, analysis.control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    objective_results = [
        {"supported": objective.supported, "notes": objective.notes}
        for objective in db.query(EvidenceObjective).filter_by(evidence_analysis_id=analysis.id).all()
    ]
    total = max(len(objective_results), 1)
    supported_count = sum(1 for objective in objective_results if objective["supported"] == "Supported")
    partial_count = sum(1 for objective in objective_results if objective["supported"] == "Partially Supported")
    analysis.coverage_score = round(((supported_count + partial_count * 0.5) / total) * 100)
    if analysis.coverage_score >= 80 and analysis.confidence_score >= 75:
        analysis.assessment_strength = "Strong"
    elif analysis.coverage_score >= 45 and analysis.confidence_score >= 50:
        analysis.assessment_strength = "Moderate"
    else:
        analysis.assessment_strength = "Weak"
    result = json.loads(analysis.analysis_result or "{}")
    result["objective_results"] = objective_results
    analysis.analysis_result = json.dumps(result)
    objective = db.get(AssessmentObjective, support.objective_id)
    log_activity(
        db,
        "Objective Support Overridden",
        "Assessment Objective",
        support.objective_id,
        f"Objective {objective.label if objective else support.objective_id} changed from {previous_status} to {payload.supported}. Notes: {payload.notes}",
        control.control_id,
        "Compliance Reviewer",
    )
    db.commit()
    return objective_workspace_response(db, control)


@app.get("/api/copilot/dashboard", response_model=CopilotDashboardOut)
def copilot_dashboard(db: Session = Depends(get_db)) -> CopilotDashboardOut:
    ensure_drift_alerts(db)
    evidence_map = primary_evidence_by_control(db)
    document_map = documentation_by_control(db)
    controls = db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    maps = [control_evidence_map_response(db, control, evidence_map, document_map) for control in controls]
    healthy = sum(1 for item in maps if item.status == "Implemented")
    at_risk = sum(1 for item in maps if item.status == "At Risk")
    partial = sum(1 for item in maps if item.status == "Partially Implemented")
    not_implemented = sum(1 for item in maps if item.status == "Not Implemented")
    automated_sources = db.query(ControlEvidenceSource).filter(ControlEvidenceSource.collection_method != "Manual Upload").count()
    manual_sources = db.query(ControlEvidenceSource).filter_by(collection_method="Manual Upload").count()
    alerts = db.query(DriftAlert).filter_by(status="Open").order_by(DriftAlert.created_at.desc()).limit(8).all()
    readiness = int(((healthy / len(controls)) * 70) + ((partial / len(controls)) * 30)) if controls else 0
    return CopilotDashboardOut(
        overall_readiness=readiness,
        healthy_controls=healthy,
        at_risk_controls=at_risk,
        partially_implemented_controls=partial,
        not_implemented_controls=not_implemented,
        open_alerts=db.query(DriftAlert).filter_by(status="Open").count(),
        automated_sources=automated_sources,
        manual_sources=manual_sources,
        mapped_controls=sum(1 for item in maps if item.required_sources or item.connected_sources),
        total_controls=len(controls),
        recent_alerts=[drift_alert_response(db, alert) for alert in alerts],
    )


@app.get("/api/copilot/control-mappings", response_model=list[ControlEvidenceMapOut])
def list_control_evidence_mappings(q: str = "", status: str = "", source_system: str = "", db: Session = Depends(get_db)) -> list[ControlEvidenceMapOut]:
    ensure_drift_alerts(db)
    evidence_map = primary_evidence_by_control(db)
    document_map = documentation_by_control(db)
    controls = db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    rows = [control_evidence_map_response(db, control, evidence_map, document_map) for control in controls]
    needle = q.strip().lower()
    if needle:
        control_id_match = re.search(r"[A-Z]{2}\.L2-\d\.\d+\.\d+", q, flags=re.IGNORECASE)
        if control_id_match:
            selected_control_id = control_id_match.group(0).lower()
            rows = [row for row in rows if row.control_id.lower() == selected_control_id]
        else:
            rows = [
                row
                for row in rows
                if needle in f"{row.control_id} {row.control_title} {row.family}".lower()
                or any(needle in f"{source.evidence_name} {source.source_type} {source.connected_system}".lower() for source in row.evidence_sources)
            ]
    if status:
        rows = [row for row in rows if row.status.lower() == status.lower()]
    if source_system:
        rows = [row for row in rows if any(source_system.lower() in source.connected_system.lower() for source in row.evidence_sources)]
    return rows


@app.get("/api/copilot/control-mappings/{control_id}", response_model=ControlEvidenceMapOut)
def get_control_evidence_mapping(control_id: str, db: Session = Depends(get_db)) -> ControlEvidenceMapOut:
    ensure_drift_alerts(db)
    control = db.query(CmmcControl).filter_by(control_id=control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    return control_evidence_map_response(db, control)


@app.get("/api/copilot/alerts", response_model=list[DriftAlertOut])
def list_drift_alerts(status: str = "Open", db: Session = Depends(get_db)) -> list[DriftAlertOut]:
    ensure_drift_alerts(db)
    query = db.query(DriftAlert).order_by(DriftAlert.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    return [drift_alert_response(db, alert) for alert in query.limit(100).all()]


@app.post("/api/compliance/documents/upload", response_model=ComplianceDocumentOut)
def upload_compliance_document(payload: ComplianceDocumentUploadIn, db: Session = Depends(get_db)) -> ComplianceDocumentOut:
    enforce_upload_data_rules(payload)
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Default Organization")
        db.add(org)
        db.commit()
        db.refresh(org)
    storage_path, suffix, safe_name = save_compliance_payload(payload, org.id)
    extracted_text = extract_evidence_text(storage_path, suffix)
    document_type = classify_compliance_document(payload.file_name or safe_name, extracted_text, payload.document_type)
    metadata = extract_document_metadata(document_type, extracted_text, payload.file_name or safe_name)
    document = ComplianceDocument(
        organization_id=org.id,
        title=payload.title or str(metadata.get("title") or Path(safe_name).stem),
        document_type=document_type,
        data_classification=payload.data_classification,
        contains_cui=yes_no(payload.contains_cui),
        contains_itar=yes_no(payload.contains_itar),
        contains_pii=yes_no(payload.contains_pii),
        file_name=payload.file_name or safe_name,
        file_type=suffix.upper(),
        version=str(metadata.get("version") or ""),
        owner=payload.owner if payload.owner and payload.owner != "Compliance Owner" else str(metadata.get("owner") or "Compliance Owner"),
        review_date=str(metadata.get("review_date") or ""),
        storage_path=str(storage_path),
        extracted_text=extracted_text[:160000],
        parsed_json=json.dumps(metadata),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    rebuild_compliance_document_graph(db, document)
    db.commit()
    db.refresh(document)
    return compliance_document_response(db, document)


@app.post("/documents/upload", response_model=ComplianceDocumentOut)
def document_upload_alias(payload: ComplianceDocumentUploadIn, db: Session = Depends(get_db)) -> ComplianceDocumentOut:
    return upload_compliance_document(payload, db)


@app.post("/api/documents/upload", response_model=ComplianceDocumentOut)
def api_document_upload_alias(payload: ComplianceDocumentUploadIn, db: Session = Depends(get_db)) -> ComplianceDocumentOut:
    return upload_compliance_document(payload, db)


@app.put("/api/compliance/documents/{document_id}/replace", response_model=ComplianceDocumentOut)
def replace_compliance_document(document_id: int, payload: ComplianceDocumentUploadIn, db: Session = Depends(get_db)) -> ComplianceDocumentOut:
    enforce_upload_data_rules(payload)
    document = db.get(ComplianceDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Compliance document not found.")
    old_path = Path(document.storage_path)
    storage_path, suffix, safe_name = save_compliance_payload(payload, document.organization_id)
    extracted_text = extract_evidence_text(storage_path, suffix)
    document_type = classify_compliance_document(payload.file_name or safe_name, extracted_text, payload.document_type or document.document_type)
    metadata = extract_document_metadata(document_type, extracted_text, payload.file_name or safe_name)
    document.title = payload.title or str(metadata.get("title") or Path(safe_name).stem)
    document.document_type = document_type
    document.data_classification = payload.data_classification
    document.contains_cui = yes_no(payload.contains_cui)
    document.contains_itar = yes_no(payload.contains_itar)
    document.contains_pii = yes_no(payload.contains_pii)
    document.file_name = payload.file_name or safe_name
    document.file_type = suffix.upper()
    document.version = str(metadata.get("version") or "")
    document.owner = payload.owner if payload.owner and payload.owner != "Compliance Owner" else str(metadata.get("owner") or document.owner or "Compliance Owner")
    document.review_date = str(metadata.get("review_date") or "")
    document.storage_path = str(storage_path)
    document.extracted_text = extracted_text[:160000]
    document.parsed_json = json.dumps(metadata)
    document.status = "Parsed"
    rebuild_compliance_document_graph(db, document)
    db.commit()
    if old_path.exists() and old_path != storage_path:
        old_path.unlink()
    db.refresh(document)
    return compliance_document_response(db, document)


@app.delete("/api/compliance/documents/{document_id}")
def delete_compliance_document(document_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    document = db.get(ComplianceDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Compliance document not found.")
    storage_path = Path(document.storage_path)
    clear_compliance_document_graph(db, document.id)
    db.delete(document)
    db.commit()
    if storage_path.exists():
        storage_path.unlink()
    return {"status": "deleted"}


@app.get("/api/compliance/documents", response_model=list[ComplianceDocumentOut])
def list_compliance_documents(q: str = "", document_type: str = "", control_id: str = "", db: Session = Depends(get_db)) -> list[ComplianceDocumentOut]:
    rows = db.query(ComplianceDocument).order_by(ComplianceDocument.uploaded_at.desc()).all()
    needle = q.strip().lower()
    type_filter = document_type.strip().lower()
    control_filter = control_id.strip().lower()
    filtered = []
    for document in rows:
        mappings = db.query(ControlMapping).filter_by(document_id=document.id).all()
        controls = [db.get(CmmcControl, mapping.control_id) for mapping in mappings]
        fields = [document.title, document.file_name, document.document_type, document.owner, document.extracted_text, *[control.control_id if control else "" for control in controls], *[control.title if control else "" for control in controls]]
        if needle and not any(needle in str(field or "").lower() for field in fields):
            continue
        if type_filter and type_filter not in document.document_type.lower():
            continue
        if control_filter and not any(control and control_filter in f"{control.control_id} {control.title}".lower() for control in controls):
            continue
        filtered.append(document)
    return [compliance_document_response(db, document) for document in filtered]


@app.get("/api/compliance/search", response_model=list[ComplianceSearchResultOut])
def compliance_search(q: str, db: Session = Depends(get_db)) -> list[ComplianceSearchResultOut]:
    needle = q.strip().lower()
    if not needle:
        return []
    results: list[ComplianceSearchResultOut] = []
    for document in db.query(ComplianceDocument).order_by(ComplianceDocument.uploaded_at.desc()).all():
        haystack = f"{document.title} {document.document_type} {document.file_name} {document.extracted_text}".lower()
        if needle in haystack:
            index = max(haystack.find(needle), 0)
            excerpt = document.extracted_text[max(index - 120, 0): index + 260] if document.extracted_text else document.file_name
            results.append(ComplianceSearchResultOut(result_type="Document", title=document.title, subtitle=document.document_type, excerpt=re.sub(r"\s+", " ", excerpt).strip()))
    for entity in db.query(DocumentEntity).all():
        if needle in f"{entity.entity_type} {entity.entity_value}".lower():
            document = db.get(ComplianceDocument, entity.document_id)
            results.append(ComplianceSearchResultOut(result_type="Entity", title=entity.entity_value[:120], subtitle=f"{entity.entity_type} from {document.title if document else 'document'}", excerpt=entity.source_excerpt))
    return results[:25]


@app.get("/api/compliance/graph", response_model=ComplianceGraphOut)
def compliance_graph(db: Session = Depends(get_db)) -> ComplianceGraphOut:
    documents = db.query(ComplianceDocument).all()
    mapped_controls = db.query(ControlMapping.control_id).distinct().count()
    entity_rows = db.query(DocumentEntity.entity_type, func.count(DocumentEntity.id)).group_by(DocumentEntity.entity_type).all()
    alerts = compliance_readiness(db).findings
    return ComplianceGraphOut(
        documents=len(documents),
        mapped_controls=mapped_controls,
        policies=sum(1 for document in documents if "policy" in document.document_type.lower()),
        procedures=sum(1 for document in documents if "procedure" in document.document_type.lower()),
        ssp_documents=sum(1 for document in documents if "ssp" in document.document_type.lower() or "system security plan" in document.document_type.lower()),
        poam_documents=sum(1 for document in documents if "poa" in document.document_type.lower()),
        entities={entity_type: count for entity_type, count in entity_rows},
        recent_alerts=alerts[:6],
    )


@app.get("/api/compliance/readiness", response_model=ComplianceReadinessOut)
def compliance_readiness(db: Session = Depends(get_db)) -> ComplianceReadinessOut:
    documents = db.query(ComplianceDocument).all()
    mapped_controls = db.query(ControlMapping.control_id).distinct().count()
    has_ssp = any("ssp" in document.document_type.lower() or "system security plan" in document.document_type.lower() for document in documents)
    has_poam = any("poa" in document.document_type.lower() for document in documents)
    policy_count = sum(1 for document in documents if "policy" in document.document_type.lower())
    procedure_count = sum(1 for document in documents if "procedure" in document.document_type.lower())
    evidence_count = db.query(Evidence).count()
    findings = []
    if not has_ssp:
        findings.append("No uploaded SSP has been parsed into the knowledge graph.")
    if policy_count < 3:
        findings.append("Policy coverage is light; upload existing family policies for better assessor readiness.")
    if procedure_count < 3:
        findings.append("Procedure coverage is light; upload operational procedures tied to control families.")
    if not has_poam:
        findings.append("No uploaded POA&M has been parsed; overdue milestone checks are limited.")
    if mapped_controls < 30:
        findings.append(f"Only {mapped_controls} CMMC controls are mapped to uploaded documentation.")
    if evidence_count < 10:
        findings.append("Evidence repository is still sparse for continuous assessment readiness.")
    documentation_score = min(100, (20 if has_ssp else 0) + min(policy_count * 8, 32) + min(procedure_count * 8, 32) + min(mapped_controls, 16))
    evidence_score = min(100, evidence_count * 8)
    poam_score = 85 if has_poam else 35
    overall = int((documentation_score * 0.45) + (evidence_score * 0.35) + (poam_score * 0.20))
    return ComplianceReadinessOut(documentation_score=documentation_score, evidence_score=evidence_score, poam_score=poam_score, overall_score=overall, findings=findings)


@app.post("/api/compliance/chat", response_model=ComplianceChatOut)
def compliance_chat(payload: ComplianceChatIn, db: Session = Depends(get_db)) -> ComplianceChatOut:
    question = payload.question.strip()
    lowered = question.lower()
    if "overdue" in lowered or "poa" in lowered:
        poams = db.query(ComplianceDocument).filter(ComplianceDocument.document_type.ilike("%poa%")).all()
        if not poams:
            return ComplianceChatOut(answer="No uploaded POA&M document is currently parsed. Upload the POA&M workbook to enable overdue milestone checks.", sources=[])
        entities = db.query(DocumentEntity).filter(DocumentEntity.entity_type.in_(["Due Date", "POA&M Status"])).all()
        return ComplianceChatOut(answer="POA&M artifacts are present. Review these extracted milestone/status fields: " + "; ".join(f"{item.entity_type}: {item.entity_value}" for item in entities[:8]), sources=[document.title for document in poams])
    control_match = re.search(r"[A-Z]{2}\.L2-\d\.\d+\.\d+", question, flags=re.IGNORECASE)
    if control_match:
        control_id = control_match.group(0).upper()
        documents = list_compliance_documents(control_id=control_id, db=db)
        evidence_items = list_evidence(control_id=control_id, db=db)
        sources = [document.title for document in documents] + [item.title for item in evidence_items]
        return ComplianceChatOut(answer=f"{control_id} is supported by {len(documents)} parsed document(s) and {len(evidence_items)} evidence item(s) currently in CMMC Pilot.", sources=sources[:12])
    if "access control policy" in lowered or "controls supported" in lowered:
        documents = list_compliance_documents(q="Access Control Policy", db=db)
        if not documents:
            documents = list_compliance_documents(q="access control", document_type="Policy", db=db)
        mapped = sorted({mapping.control_id for document in documents for mapping in document.mappings})
        return ComplianceChatOut(answer="Mapped controls: " + (", ".join(mapped) if mapped else "No mapped controls found for Access Control Policy yet."), sources=[document.title for document in documents])
    results = compliance_search(q=question, db=db)
    return ComplianceChatOut(answer=f"I found {len(results)} matching knowledge graph result(s).", sources=[f"{item.result_type}: {item.title}" for item in results[:10]])


@app.post("/chat/query", response_model=ComplianceChatOut)
def chat_query(payload: ChatQueryIn, db: Session = Depends(get_db)) -> ComplianceChatOut:
    return compliance_chat(ComplianceChatIn(question=payload.query), db)


@app.post("/api/chat/query", response_model=ComplianceChatOut)
def api_chat_query(payload: ChatQueryIn, db: Session = Depends(get_db)) -> ComplianceChatOut:
    return chat_query(payload, db)


@app.get("/readiness", response_model=ComplianceReadinessOut)
def readiness_alias(db: Session = Depends(get_db)) -> ComplianceReadinessOut:
    return compliance_readiness(db)


@app.get("/api/readiness", response_model=ComplianceReadinessOut)
def api_readiness_alias(db: Session = Depends(get_db)) -> ComplianceReadinessOut:
    return compliance_readiness(db)


def simulate_assessment_for_control(payload: AssessmentSimulationIn, db: Session) -> AssessmentSimulationOut:
    control = db.query(CmmcControl).filter_by(control_id=payload.control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    evidence_items = []
    if payload.provided_evidence_ids:
        evidence_items = [item for item in (db.get(Evidence, evidence_id) for evidence_id in payload.provided_evidence_ids) if item]
    else:
        evidence_items = [evidence for _control_id, evidence, _analysis in primary_evidence_analyses(db) if _control_id == control.control_id]
    analyses = []
    for evidence in evidence_items:
        analyses.extend([analysis for analysis in evidence.analyses if db.get(CmmcControl, analysis.control_id) and db.get(CmmcControl, analysis.control_id).control_id == control.control_id])
    reviewed = [evidence.title for evidence in evidence_items]
    supported_objectives = sum(
        1
        for analysis in analyses
        for objective in analysis.objectives
        if objective.supported in {"Supported", "Partially Supported"}
    )
    total_objectives = db.query(AssessmentObjective).filter_by(control_id=control.id).count()
    required_sources = db.query(ControlEvidenceSource).filter_by(control_id=control.id, required="true").all()
    missing = [source.evidence_name for source in required_sources[:8]]
    for evidence in evidence_items:
        evidence_text = f"{evidence.title} {evidence.file_name} {evidence.evidence_type}".lower()
        missing = [item for item in missing if item.lower() not in evidence_text]
    if analyses and total_objectives and supported_objectives >= total_objectives:
        assessment_status = "Met"
    elif analyses or reviewed:
        assessment_status = "Partially Met"
    else:
        assessment_status = "Not Met"
    question = payload.assessor_question or f"Show me how {control.title.lower()} is implemented and evidenced."
    feedback = (
        f"{control.control_id} was evaluated against {len(reviewed)} evidence item(s). "
        f"Current evidence supports {supported_objectives} objective mapping record(s)."
    )
    return AssessmentSimulationOut(
        control_id=control.control_id,
        assessment_question=question,
        assessment_status=assessment_status,
        evidence_reviewed=reviewed,
        missing=missing[:6],
        assessor_feedback=feedback,
        recommended_next_steps=[
            "Upload missing evidence artifacts or connect the mapped source system.",
            "Confirm evidence is current, scoped to the CUI environment, and tied to assessment objectives.",
            "Create a POA&M item for any unmet objective that cannot be closed before assessment.",
        ],
    )


@app.post("/assessment/simulate", response_model=AssessmentSimulationOut)
def assessment_simulate(payload: AssessmentSimulationIn, db: Session = Depends(get_db)) -> AssessmentSimulationOut:
    return simulate_assessment_for_control(payload, db)


@app.post("/api/assessment/simulate", response_model=AssessmentSimulationOut)
def api_assessment_simulate(payload: AssessmentSimulationIn, db: Session = Depends(get_db)) -> AssessmentSimulationOut:
    return simulate_assessment_for_control(payload, db)


@app.post("/api/evidence/upload", response_model=EvidenceOut)
def upload_evidence(payload: EvidenceUploadIn, db: Session = Depends(get_db)) -> EvidenceOut:
    enforce_upload_data_rules(payload)
    org = db.query(Organization).first() or Organization(name="Default Organization")
    db.add(org)
    db.flush()
    intended_control_id = payload.control_id
    if payload.managed_poam_id is not None:
        poam = db.get(ManagedPoamItem, payload.managed_poam_id)
        if not poam:
            raise HTTPException(status_code=404, detail="Selected POA&M item not found.")
        if intended_control_id and intended_control_id != poam.control_id:
            raise HTTPException(status_code=400, detail="Evidence control does not match the selected POA&M item.")
        intended_control_id = poam.control_id
    if payload.evidence_request_id is not None:
        request = db.get(EvidenceRequest, payload.evidence_request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Selected evidence request not found.")
        if intended_control_id and request.control_id and intended_control_id != request.control_id:
            raise HTTPException(status_code=400, detail="Evidence control does not match the selected evidence request.")
        intended_control_id = request.control_id or intended_control_id
    storage_path, suffix, safe_name = save_evidence_payload(payload, org.id)
    extracted_text = extract_evidence_text(storage_path, suffix)
    evidence = Evidence(
        organization_id=org.id,
        title=payload.title or Path(payload.file_name or safe_name).stem,
        file_name=payload.file_name or safe_name,
        file_type=suffix.upper(),
        document_type=payload.document_type,
        data_classification=payload.data_classification,
        contains_cui=yes_no(payload.contains_cui),
        contains_itar=yes_no(payload.contains_itar),
        contains_pii=yes_no(payload.contains_pii),
        intended_control_id=intended_control_id,
        managed_poam_id=payload.managed_poam_id,
        evidence_request_id=payload.evidence_request_id,
        storage_path=str(storage_path),
        extracted_text=extracted_text[:120000],
        evidence_type=classify_evidence_type(extracted_text, payload.file_name or safe_name),
        owner=payload.owner,
        review_status="Under Review",
        uploaded_by="MVP User",
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    analyze_and_store_evidence(db, evidence, intended_control_id)
    poam_detail = f" and linked to POA&M item {payload.managed_poam_id}" if payload.managed_poam_id else ""
    request_detail = f" and linked to evidence request {payload.evidence_request_id}" if payload.evidence_request_id else ""
    log_activity(db, "Evidence Uploaded", "Evidence", evidence.id, f"{evidence.file_name} uploaded and mapped to {intended_control_id or 'unassigned control'}{poam_detail}{request_detail}.", intended_control_id)
    if payload.managed_poam_id:
        log_activity(db, "Evidence Linked", "Managed POA&M", payload.managed_poam_id, f"{evidence.file_name} uploaded and linked to this POA&M item.", intended_control_id)
    if payload.evidence_request_id:
        sync_evidence_request_status(db, payload.evidence_request_id)
        log_activity(db, "Evidence Submitted", "Evidence Request", payload.evidence_request_id, f"{evidence.file_name} uploaded for this request.", intended_control_id)
    db.commit()
    db.refresh(evidence)
    return evidence_response(db, evidence)


@app.put("/api/evidence/{evidence_id}/replace", response_model=EvidenceOut)
def replace_evidence(evidence_id: int, payload: EvidenceUploadIn, db: Session = Depends(get_db)) -> EvidenceOut:
    enforce_upload_data_rules(payload)
    evidence = db.get(Evidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    old_path = Path(evidence.storage_path)
    storage_path, suffix, safe_name = save_evidence_payload(payload, evidence.organization_id, evidence.storage_path)
    if old_path.exists() and old_path != storage_path:
        old_path.unlink()
    clear_evidence_analysis(db, evidence.id)
    extracted_text = extract_evidence_text(storage_path, suffix)
    evidence.title = payload.title or Path(payload.file_name or safe_name).stem
    evidence.file_name = payload.file_name or safe_name
    evidence.file_type = suffix.upper()
    evidence.document_type = payload.document_type
    evidence.data_classification = payload.data_classification
    evidence.contains_cui = yes_no(payload.contains_cui)
    evidence.contains_itar = yes_no(payload.contains_itar)
    evidence.contains_pii = yes_no(payload.contains_pii)
    evidence.intended_control_id = payload.control_id or evidence.intended_control_id
    evidence.managed_poam_id = payload.managed_poam_id or evidence.managed_poam_id
    evidence.evidence_request_id = payload.evidence_request_id or evidence.evidence_request_id
    evidence.storage_path = str(storage_path)
    evidence.extracted_text = extracted_text[:120000]
    evidence.evidence_type = classify_evidence_type(extracted_text, payload.file_name or safe_name)
    evidence.owner = payload.owner
    evidence.status = "Analyzed"
    evidence.review_status = "Under Review"
    evidence.reviewer = ""
    evidence.review_date = ""
    evidence.review_notes = ""
    analyze_and_store_evidence(db, evidence, payload.control_id)
    sync_evidence_request_status(db, evidence.evidence_request_id)
    log_activity(db, "Evidence Replaced", "Evidence", evidence.id, f"{evidence.file_name} replaced and reanalyzed.", evidence.intended_control_id)
    db.commit()
    db.refresh(evidence)
    return evidence_response(db, evidence)


@app.put("/api/evidence/{evidence_id}/review", response_model=EvidenceOut)
def review_evidence(evidence_id: int, payload: EvidenceReviewUpdate, db: Session = Depends(get_db)) -> EvidenceOut:
    evidence = db.get(Evidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    allowed = {"Uploaded", "Under Review", "Accepted", "Needs Replacement", "Rejected"}
    if payload.review_status not in allowed:
        raise HTTPException(status_code=400, detail="Review status must be Uploaded, Under Review, Accepted, Needs Replacement, or Rejected.")
    previous_status = evidence.review_status
    evidence.review_status = payload.review_status
    evidence.reviewer = payload.reviewer
    evidence.review_notes = payload.review_notes
    evidence.review_date = datetime.utcnow().strftime("%Y-%m-%d")
    sync_evidence_request_status(db, evidence.evidence_request_id)
    log_activity(db, "Evidence Review Updated", "Evidence", evidence.id, f"{evidence.file_name} changed from {previous_status} to {payload.review_status}. Reviewer: {payload.reviewer}. Notes: {payload.review_notes}", evidence.intended_control_id, payload.reviewer)
    db.commit()
    db.refresh(evidence)
    return evidence_response(db, evidence)


@app.get("/api/evidence-requests", response_model=EvidenceRequestDashboardOut)
def list_evidence_requests(q: str = "", status: str = "", control_id: str = "", owner: str = "", db: Session = Depends(get_db)) -> EvidenceRequestDashboardOut:
    return evidence_request_dashboard(db, q, status, control_id, owner)


@app.post("/api/evidence-requests", response_model=EvidenceRequestOut)
def create_evidence_request(payload: EvidenceRequestIn, db: Session = Depends(get_db)) -> EvidenceRequestOut:
    request = EvidenceRequest(organization_id=default_organization_id(db), **payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    log_activity(db, "Evidence Request Created", "Evidence Request", request.id, f"{request.request_title} assigned to {request.requested_from}. Due: {request.due_date or 'Not set'}.", request.control_id, request.requested_from)
    return evidence_request_response(db, request)


@app.put("/api/evidence-requests/{request_id}", response_model=EvidenceRequestOut)
def update_evidence_request(request_id: int, payload: EvidenceRequestIn, db: Session = Depends(get_db)) -> EvidenceRequestOut:
    request = db.get(EvidenceRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Evidence request not found.")
    previous_status = request.status
    for key, value in payload.model_dump().items():
        setattr(request, key, value)
    db.commit()
    db.refresh(request)
    log_activity(db, "Evidence Request Updated", "Evidence Request", request.id, f"{request.request_title} changed from {previous_status} to {request.status}. Owner: {request.requested_from}.", request.control_id, request.requested_from)
    return evidence_request_response(db, request)


@app.delete("/api/evidence-requests/{request_id}")
def delete_evidence_request(request_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    request = db.get(EvidenceRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Evidence request not found.")
    for evidence in db.query(Evidence).filter_by(evidence_request_id=request.id).all():
        evidence.evidence_request_id = None
    db.delete(request)
    db.commit()
    return {"status": "deleted"}


@app.post("/api/evidence-requests/generate/poam")
def generate_evidence_requests_from_poam(db: Session = Depends(get_db)) -> dict[str, int]:
    created = 0
    existing = 0
    for item in db.query(ManagedPoamItem).filter(ManagedPoamItem.status != "Closed").all():
        source_id = str(item.id)
        found = db.query(EvidenceRequest).filter_by(source_type="Managed POA&M", source_id=source_id).first()
        if found:
            existing += 1
            continue
        db.add(
            EvidenceRequest(
                organization_id=item.organization_id,
                control_id=item.control_id,
                objective_label=item.objective_label,
                request_title=f"{item.control_id} objective {item.objective_label} evidence request",
                evidence_needed=item.evidence_needed or item.corrective_action or item.gap_statement,
                requested_from=item.owner,
                due_date=item.due_date,
                priority=item.risk if item.risk in {"High", "Medium", "Low"} else "Medium",
                status="Sent",
                source_type="Managed POA&M",
                source_id=source_id,
                notes=item.gap_statement,
            )
        )
        created += 1
    db.commit()
    return {"created": created, "existing": existing}


@app.post("/api/evidence-requests/generate/package")
def generate_evidence_requests_from_package(db: Session = Depends(get_db)) -> dict[str, int]:
    created = 0
    existing = 0
    for control in db.query(CmmcControl).order_by(CmmcControl.control_id).all():
        row = assessment_package_control_row(db, control)
        if row.accepted_evidence > 0:
            continue
        source_id = control.control_id
        found = db.query(EvidenceRequest).filter_by(source_type="Assessment Package Warning", source_id=source_id).first()
        if found:
            existing += 1
            continue
        db.add(
            EvidenceRequest(
                organization_id=default_organization_id(db),
                control_id=control.control_id,
                objective_label="",
                request_title=f"{control.control_id} accepted evidence needed",
                evidence_needed="Accepted evidence is needed to support this control in the assessment package. Upload sufficient artifacts and complete evidence review.",
                requested_from="Evidence Owner",
                due_date="",
                priority="Medium",
                status="Draft",
                source_type="Assessment Package Warning",
                source_id=source_id,
                notes="Generated because the assessment package has no accepted evidence for this control.",
            )
        )
        created += 1
    db.commit()
    return {"created": created, "existing": existing}


@app.get("/api/evidence-requests/export/xlsx")
def export_evidence_request_register(db: Session = Depends(get_db)) -> Response:
    headers = ["Status", "Priority", "Due Date", "Control", "Objective", "Title", "Evidence Needed", "Requested From", "Linked Evidence", "Accepted Evidence", "Source", "Notes"]
    rows = [
        [
            row.status,
            row.priority,
            row.due_date,
            row.control_id,
            row.objective_label,
            row.request_title,
            row.evidence_needed,
            row.requested_from,
            str(row.linked_evidence_count),
            str(row.accepted_evidence_count),
            f"{row.source_type} {row.source_id}",
            row.notes,
        ]
        for row in evidence_request_dashboard(db).rows
    ]
    return Response(render_xlsx("Evidence Requests", headers, rows), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": 'attachment; filename="CMMC_Evidence_Request_Register.xlsx"'})


@app.get("/api/evidence-requests/export/owner/docx")
def export_owner_evidence_requests(owner: str = "", db: Session = Depends(get_db)) -> Response:
    dashboard = evidence_request_dashboard(db, owner=owner)
    sections = {
        "Request Summary": f"Owner: {owner or 'All Owners'}\nRequests: {len(dashboard.rows)}\nDraft: {dashboard.draft}\nSent: {dashboard.sent}\nSubmitted: {dashboard.submitted}\nAccepted: {dashboard.accepted}\nOverdue: {dashboard.overdue}",
        "Requests": "\n\n".join(f"{row.control_id} - {row.request_title}\nStatus: {row.status}\nPriority: {row.priority}\nDue: {row.due_date or 'Not scheduled'}\nRequested From: {row.requested_from}\nEvidence Needed: {row.evidence_needed}" for row in dashboard.rows) or "No evidence requests match this owner.",
    }
    filename = (owner or "All_Owners").replace(" ", "_")
    return Response(render_docx("Evidence Request Owner List", sections), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="Evidence_Requests_{filename}.docx"'})


@app.delete("/api/evidence/{evidence_id}")
def delete_evidence(evidence_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    evidence = db.get(Evidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    storage_path = Path(evidence.storage_path)
    request_id = evidence.evidence_request_id
    clear_evidence_analysis(db, evidence.id)
    log_activity(db, "Evidence Removed", "Evidence", evidence.id, f"{evidence.file_name} and its analyses were removed.", evidence.intended_control_id)
    db.delete(evidence)
    sync_evidence_request_status(db, request_id)
    db.commit()
    if storage_path.exists():
        storage_path.unlink()
    return {"status": "deleted"}


@app.get("/api/evidence", response_model=list[EvidenceOut])
def list_evidence(q: str = "", control_id: str = "", review_status: str = "", drift_state: str = "", managed_poam_id: int | None = None, evidence_request_id: int | None = None, db: Session = Depends(get_db)) -> list[EvidenceOut]:
    rows = db.query(Evidence).order_by(Evidence.uploaded_at.desc()).all()
    rows = [
        evidence
        for evidence in rows
        if evidence_matches_query(db, evidence, q)
        and evidence_matches_control_filter(db, evidence, control_id)
        and (not review_status or evidence.review_status.lower() == review_status.lower())
        and (not drift_state or evidence_drift_state(evidence).lower() == drift_state.lower())
        and (managed_poam_id is None or evidence.managed_poam_id == managed_poam_id)
        and (evidence_request_id is None or evidence.evidence_request_id == evidence_request_id)
    ]
    return [evidence_response(db, evidence) for evidence in rows]


@app.get("/api/evidence/dashboard", response_model=EvidenceDashboardOut)
def evidence_dashboard(db: Session = Depends(get_db)) -> EvidenceDashboardOut:
    total_controls = db.query(CmmcControl).count()
    evidence_count = db.query(Evidence).count()
    primary_analyses = primary_evidence_analyses(db)
    controls_with_evidence = len({control_id for control_id, _evidence, _analysis in primary_analyses})
    analyses_only = [analysis for _control_id, _evidence, analysis in primary_analyses]
    objectives_with_evidence, total_objectives, objective_coverage_score, _partial_objectives = objective_coverage_for_analyses(db, analyses_only)
    average_coverage = int(sum(analysis.coverage_score for _control_id, _evidence, analysis in primary_analyses) / len(primary_analyses)) if primary_analyses else 0
    missing_evidence = 0
    for _control_id, _evidence, analysis in primary_analyses:
        result = json.loads(analysis.analysis_result or "{}")
        missing_evidence += len(result.get("missing_evidence", []))
    strong = sum(1 for _control_id, _evidence, analysis in primary_analyses if analysis.assessment_strength == "Strong")
    weak = sum(1 for _control_id, _evidence, analysis in primary_analyses if analysis.assessment_strength == "Weak")
    uploaded_review = db.query(Evidence).filter_by(review_status="Uploaded").count()
    under_review = db.query(Evidence).filter_by(review_status="Under Review").count()
    accepted = db.query(Evidence).filter_by(review_status="Accepted").count()
    needs_replacement = db.query(Evidence).filter_by(review_status="Needs Replacement").count()
    rejected = db.query(Evidence).filter_by(review_status="Rejected").count()
    all_evidence = db.query(Evidence).all()
    stale = sum(1 for item in all_evidence if evidence_drift_state(item) == "Stale")
    objectives_at_risk = sum(1 for objective in db.query(AssessmentObjective).all() if objective_is_at_risk(db, objective))
    controls_at_risk = sum(1 for control in db.query(CmmcControl).all() if control_is_at_risk(db, control))
    readiness = int(((controls_with_evidence / total_controls) * 35) + (objective_coverage_score * 0.65)) if total_controls else 0
    return EvidenceDashboardOut(
        evidence_uploaded=evidence_count,
        controls_with_evidence=controls_with_evidence,
        total_controls=total_controls,
        objectives_with_evidence=objectives_with_evidence,
        total_objectives=total_objectives,
        objective_coverage_score=objective_coverage_score,
        average_coverage=average_coverage,
        missing_evidence=missing_evidence,
        strong_evidence=strong,
        weak_evidence=weak,
        uploaded_evidence=uploaded_review,
        under_review_evidence=under_review,
        accepted_evidence=accepted,
        needs_replacement_evidence=needs_replacement,
        rejected_evidence=rejected,
        stale_evidence=stale,
        objectives_at_risk=objectives_at_risk,
        controls_at_risk=controls_at_risk,
        assessment_readiness_score=min(readiness, 100),
    )


@app.get("/api/evidence/control-coverage")
def evidence_control_coverage(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    rows = []
    primary_by_control: dict[str, list[tuple[Evidence, EvidenceAnalysis]]] = {}
    for control_id, evidence, analysis in primary_evidence_analyses(db):
        primary_by_control.setdefault(control_id, []).append((evidence, analysis))
    controls = db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    for control in controls:
        primary_rows = primary_by_control.get(control.control_id, [])
        analyses = [analysis for _evidence, analysis in primary_rows]
        objectives_with_evidence, total_objectives, objective_coverage_score, partially_supported_objectives = objective_coverage_for_analyses(db, analyses, control.id)
        if primary_rows:
            score = max(analysis.coverage_score for analysis in analyses)
            confidence = max(analysis.confidence_score for analysis in analyses)
            strength = max((analysis.assessment_strength for analysis in analyses), key=lambda value: {"Weak": 1, "Moderate": 2, "Strong": 3}.get(value, 0))
        else:
            score = 0
            confidence = 0
            strength = "Missing"
        if not primary_rows:
            drift_state = "No Accepted Evidence"
        else:
            states = {evidence_drift_state(evidence) for evidence, _analysis in primary_rows}
            if "Rejected" in states:
                drift_state = "Rejected"
            elif "Needs Replacement" in states:
                drift_state = "Needs Replacement"
            elif "Stale" in states:
                drift_state = "Stale"
            elif "Current" in states:
                drift_state = "Current"
            else:
                drift_state = "No Accepted Evidence"
        rows.append(
            {
                "control_id": control.control_id,
                "title": control.title,
                "family": control.family,
                "evidence_count": len({evidence.id for evidence, _analysis in primary_rows}),
                "coverage_score": score,
                "objective_coverage_score": objective_coverage_score,
                "objectives_with_evidence": objectives_with_evidence,
                "partially_supported_objectives": partially_supported_objectives,
                "total_objectives": total_objectives,
                "confidence_score": confidence,
                "assessment_strength": strength,
                "drift_state": drift_state,
            }
        )
    return rows


@app.get("/api/control-health", response_model=ControlHealthDashboardOut)
def control_health_dashboard(db: Session = Depends(get_db)) -> ControlHealthDashboardOut:
    rows = control_health_rows(db)
    return ControlHealthDashboardOut(
        healthy_controls=sum(1 for row in rows if row.health_status == "Healthy"),
        monitor_controls=sum(1 for row in rows if row.health_status == "Monitor"),
        at_risk_controls=sum(1 for row in rows if row.health_status == "At Risk"),
        critical_controls=sum(1 for row in rows if row.health_status == "Critical"),
        stale_evidence=sum(row.stale_evidence for row in rows),
        poam_candidates=sum(row.poam_candidates for row in rows),
        rows=rows,
    )


def audit_log_query(
    db: Session,
    q: str = "",
    action: str = "",
    entity_type: str = "",
    entity_id: str = "",
    control_id: str = "",
    user_name: str = "",
) -> list[AuditLog]:
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    if q:
        needle = q.lower()
        rows = [item for item in rows if needle in f"{item.action} {item.entity_type} {item.entity_id} {item.user_name} {item.control_id} {item.details}".lower()]
    if action:
        rows = [item for item in rows if item.action.lower() == action.lower()]
    if entity_type:
        rows = [item for item in rows if item.entity_type.lower() == entity_type.lower()]
    if entity_id:
        rows = [item for item in rows if item.entity_id == entity_id]
    if control_id:
        rows = [item for item in rows if item.control_id.lower() == control_id.lower()]
    if user_name:
        rows = [item for item in rows if item.user_name.lower() == user_name.lower()]
    return rows


@app.get("/api/audit", response_model=list[AuditLogOut])
def list_audit_logs(q: str = "", action: str = "", entity_type: str = "", entity_id: str = "", control_id: str = "", user_name: str = "", db: Session = Depends(get_db)) -> list[AuditLogOut]:
    return [audit_log_response(item) for item in audit_log_query(db, q, action, entity_type, entity_id, control_id, user_name)]


@app.get("/api/people", response_model=list[PersonOut])
def list_people(q: str = "", db: Session = Depends(get_db)) -> list[PersonOut]:
    rows = db.query(User).order_by(User.full_name).all()
    if q:
        needle = q.lower()
        rows = [row for row in rows if needle in f"{row.full_name} {row.email} {row.department} {row.title} {row.role}".lower()]
    return rows


@app.post("/api/people", response_model=PersonOut)
def create_person(payload: PersonIn, db: Session = Depends(get_db)) -> PersonOut:
    existing = db.query(User).filter_by(email=payload.email).first()
    if existing:
        existing.full_name = payload.full_name
        existing.role = payload.role
        existing.department = payload.department
        existing.title = payload.title
        existing.status = payload.status
        db.commit()
        db.refresh(existing)
        return existing
    person = User(
        organization_id=default_organization_id(db),
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        department=payload.department,
        title=payload.title,
        status=payload.status,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    log_activity(db, "Person Saved", "User", person.id, f"{person.full_name} / {person.email} saved.", user_name=person.full_name)
    return person


@app.put("/api/people/{person_id}", response_model=PersonOut)
def update_person(person_id: int, payload: PersonIn, db: Session = Depends(get_db)) -> PersonOut:
    person = db.get(User, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found.")
    person.email = payload.email
    person.full_name = payload.full_name
    person.role = payload.role
    person.department = payload.department
    person.title = payload.title
    person.status = payload.status
    db.commit()
    db.refresh(person)
    log_activity(db, "Person Updated", "User", person.id, f"{person.full_name} / {person.email} updated.", user_name=person.full_name)
    return person


@app.delete("/api/people/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    person = db.get(User, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found.")
    for assignment in db.query(RoleAssignment).filter_by(user_id=person.id).all():
        assignment.user_id = None
    db.delete(person)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/roles", response_model=list[RoleAssignmentOut])
def list_role_assignments(q: str = "", db: Session = Depends(get_db)) -> list[RoleAssignmentOut]:
    rows = db.query(RoleAssignment).order_by(RoleAssignment.compliance_role, RoleAssignment.scope_type, RoleAssignment.scope_value).all()
    if q:
        needle = q.lower()
        rows = [row for row in rows if needle in f"{row.person_name} {row.person_email} {row.compliance_role} {row.scope_type} {row.scope_value} {row.notes}".lower()]
    return [role_assignment_response(row) for row in rows]


@app.post("/api/roles", response_model=RoleAssignmentOut)
def create_role_assignment(payload: RoleAssignmentIn, db: Session = Depends(get_db)) -> RoleAssignmentOut:
    person = db.get(User, payload.user_id) if payload.user_id else None
    assignment = RoleAssignment(
        organization_id=default_organization_id(db),
        user_id=payload.user_id,
        person_name=payload.person_name or (person.full_name if person else ""),
        person_email=payload.person_email or (person.email if person else ""),
        compliance_role=payload.compliance_role,
        scope_type=payload.scope_type,
        scope_value=payload.scope_value,
        notes=payload.notes,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    log_activity(db, "Role Assigned", "Role Assignment", assignment.id, f"{assignment.compliance_role} assigned to {assignment.person_name or assignment.person_email} for {assignment.scope_type} {assignment.scope_value}.", user_name=assignment.person_name or "MVP User")
    return role_assignment_response(assignment)


@app.put("/api/roles/{assignment_id}", response_model=RoleAssignmentOut)
def update_role_assignment(assignment_id: int, payload: RoleAssignmentIn, db: Session = Depends(get_db)) -> RoleAssignmentOut:
    assignment = db.get(RoleAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Role assignment not found.")
    person = db.get(User, payload.user_id) if payload.user_id else None
    assignment.user_id = payload.user_id
    assignment.person_name = payload.person_name or (person.full_name if person else "")
    assignment.person_email = payload.person_email or (person.email if person else "")
    assignment.compliance_role = payload.compliance_role
    assignment.scope_type = payload.scope_type
    assignment.scope_value = payload.scope_value
    assignment.notes = payload.notes
    db.commit()
    db.refresh(assignment)
    log_activity(db, "Role Assignment Updated", "Role Assignment", assignment.id, f"{assignment.compliance_role} assigned to {assignment.person_name or assignment.person_email} for {assignment.scope_type} {assignment.scope_value}.", user_name=assignment.person_name or "MVP User")
    return role_assignment_response(assignment)


@app.delete("/api/roles/{assignment_id}")
def delete_role_assignment(assignment_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    assignment = db.get(RoleAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Role assignment not found.")
    db.delete(assignment)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/ownership/coverage", response_model=OwnershipCoverageOut)
def get_ownership_coverage(db: Session = Depends(get_db)) -> OwnershipCoverageOut:
    return ownership_coverage_summary(db)


@app.get("/api/ownership/owner-dashboard", response_model=OwnerDashboardOut)
def get_owner_dashboard(owner: str, db: Session = Depends(get_db)) -> OwnerDashboardOut:
    return owner_dashboard(db, owner)


@app.get("/api/ownership/export/matrix/xlsx")
def export_responsibility_matrix(db: Session = Depends(get_db)) -> Response:
    headers = ["Role", "Person", "Email", "Scope Type", "Scope Value", "Department/Title", "Notes"]
    rows = []
    for assignment in db.query(RoleAssignment).order_by(RoleAssignment.compliance_role, RoleAssignment.scope_type, RoleAssignment.scope_value).all():
        person = db.get(User, assignment.user_id) if assignment.user_id else None
        rows.append(
            [
                assignment.compliance_role,
                assignment.person_name or (person.full_name if person else ""),
                assignment.person_email or (person.email if person else ""),
                assignment.scope_type,
                assignment.scope_value,
                f"{person.department} / {person.title}" if person else "",
                assignment.notes,
            ]
        )
    if not rows:
        rows.append(["Control Owner", "Unassigned", "", "Organization", "", "", "Create role assignments to complete the responsibility matrix."])
    return Response(
        render_xlsx("Responsibility Matrix", headers, rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Responsibility_Matrix.xlsx"'},
    )


@app.get("/api/ownership/export/roles/docx")
def export_role_assignments(db: Session = Depends(get_db)) -> Response:
    coverage = ownership_coverage_summary(db)
    assignment_lines = []
    for assignment in db.query(RoleAssignment).order_by(RoleAssignment.compliance_role, RoleAssignment.scope_type, RoleAssignment.scope_value).all():
        assignment_lines.append(f"{assignment.compliance_role}: {assignment.person_name or assignment.person_email or 'Unassigned'} - {assignment.scope_type} {assignment.scope_value}. {assignment.notes}")
    sections = {
        "Ownership Coverage": "\n".join(
            [
                f"People: {coverage.people}",
                f"Role assignments: {coverage.role_assignments}",
                f"Controls without owner: {coverage.controls_without_owner}",
                f"POA&M without owner: {coverage.poam_without_owner}",
                f"Evidence without owner: {coverage.evidence_without_owner}",
                f"Evidence without reviewer: {coverage.evidence_without_reviewer}",
                f"Documents without approver: {coverage.documents_without_approver}",
            ]
        ),
        "Findings": "\n".join(coverage.findings),
        "Role Assignments": "\n".join(assignment_lines) if assignment_lines else "No role assignments have been created.",
    }
    return Response(
        render_docx("CMMC Role Assignments", sections),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Role_Assignments.docx"'},
    )


@app.get("/api/control-reviews", response_model=ControlReviewDashboardOut)
def list_control_reviews(q: str = "", family: str = "", status: str = "", db: Session = Depends(get_db)) -> ControlReviewDashboardOut:
    return control_review_dashboard_response(db, q, family, status)


@app.get("/api/control-reviews/{control_id}", response_model=ControlReviewOut)
def get_control_review(control_id: str, db: Session = Depends(get_db)) -> ControlReviewOut:
    control = db.query(CmmcControl).filter_by(control_id=control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    return control_review_response(db, control)


@app.put("/api/control-reviews/{control_id}", response_model=ControlReviewOut)
def update_control_review(control_id: str, payload: ControlReviewUpdate, db: Session = Depends(get_db)) -> ControlReviewOut:
    control = db.query(CmmcControl).filter_by(control_id=control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    package = assessment_package_control_row(db, control)
    review = latest_control_review(db, control)
    if not review:
        review = ControlReview(organization_id=default_organization_id(db), control_id=control.id)
        db.add(review)
    review.review_status = payload.review_status
    review.reviewer = payload.reviewer
    review.approver = payload.approver
    review.review_notes = payload.review_notes
    review.signoff_date = payload.signoff_date or (datetime.utcnow().strftime("%Y-%m-%d") if payload.review_status == "Approved" else "")
    review.next_review_date = payload.next_review_date
    review.package_readiness_score = package.readiness_score
    db.commit()
    db.refresh(review)
    log_activity(
        db,
        f"Control Review {payload.review_status}",
        "Control Review",
        review.id,
        f"{control.control_id} changed to {payload.review_status}. Reviewer: {payload.reviewer or 'Unassigned'}. Approver: {payload.approver or 'Unassigned'}. Notes: {payload.review_notes}",
        control.control_id,
        payload.approver or payload.reviewer or "MVP User",
    )
    return control_review_response(db, control, review)


@app.get("/api/control-reviews/export/xlsx")
def export_control_review_register(db: Session = Depends(get_db)) -> Response:
    headers = ["Family", "Control", "Title", "Status", "Reviewer", "Approver", "Sign-Off Date", "Next Review", "Readiness", "Warnings", "Notes"]
    rows = [
        [
            row.family,
            row.control_id,
            row.control_title,
            row.review_status,
            row.reviewer,
            row.approver,
            row.signoff_date,
            row.next_review_date,
            f"{row.package_readiness_score}%",
            "; ".join(row.warnings),
            row.review_notes,
        ]
        for row in control_review_rows(db)
    ]
    return Response(
        render_xlsx("Control Sign-Off", headers, rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Control_Signoff_Register.xlsx"'},
    )


@app.get("/api/control-reviews/{control_id}/export/docx")
def export_control_review_memo(control_id: str, db: Session = Depends(get_db)) -> Response:
    control = db.query(CmmcControl).filter_by(control_id=control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found.")
    row = control_review_response(db, control)
    package = assessment_package_control_row(db, control)
    sections = {
        "Control": f"{row.control_id} - {row.control_title}\nFamily: {row.family}\nRequirement: {control.requirement}",
        "Review Decision": "\n".join(
            [
                f"Status: {row.review_status}",
                f"Reviewer: {row.reviewer or 'Unassigned'}",
                f"Approver: {row.approver or 'Unassigned'}",
                f"Sign-Off Date: {row.signoff_date or 'Not signed'}",
                f"Next Review Date: {row.next_review_date or 'Not scheduled'}",
                f"Package Readiness: {row.package_readiness_score}%",
            ]
        ),
        "Readiness Summary": "\n".join(
            [
                f"Implementation: {package.implementation_status}",
                f"Policy: {package.policy_status}",
                f"Procedure: {package.procedure_status}",
                f"Accepted Evidence: {package.accepted_evidence}/{package.evidence_total}",
                f"Open POA&M: {package.open_poam}",
                f"Stale Evidence: {package.stale_evidence}",
            ]
        ),
        "Warnings": "\n".join(row.warnings) if row.warnings else "No package warnings recorded.",
        "Review Notes": row.review_notes or "No review notes recorded.",
    }
    filename = control.control_id.replace(".", "_")
    return Response(
        render_docx(f"{control.control_id} Control Approval Memo", sections),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}_Control_Approval_Memo.docx"'},
    )


@app.get("/api/audit/export/xlsx")
def export_audit_logs(db: Session = Depends(get_db)) -> Response:
    headers = ["Timestamp", "User", "Action", "Entity Type", "Entity ID", "Control", "Details"]
    rows = [[item.created_at.isoformat(), item.user_name, item.action, item.entity_type, item.entity_id, item.control_id, item.details] for item in audit_log_query(db)]
    return Response(
        render_xlsx("Audit Log", headers, rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Audit_Log.xlsx"'},
    )


@app.get("/api/calendar", response_model=ComplianceCalendarOut)
def compliance_calendar(status: str = "", task_type: str = "", owner: str = "", control_id: str = "", q: str = "", db: Session = Depends(get_db)) -> ComplianceCalendarOut:
    tasks = compliance_calendar_tasks(db)
    if status:
        tasks = [task for task in tasks if task.status.lower() == status.lower()]
    if task_type:
        tasks = [task for task in tasks if task.task_type.lower() == task_type.lower()]
    if owner:
        tasks = [task for task in tasks if owner.lower() in task.owner.lower()]
    if control_id:
        tasks = [task for task in tasks if task.control_id.lower() == control_id.lower()]
    if q:
        needle = q.lower()
        tasks = [task for task in tasks if needle in f"{task.title} {task.detail} {task.owner} {task.control_id}".lower()]
    all_tasks = compliance_calendar_tasks(db)
    return ComplianceCalendarOut(
        overdue=sum(1 for task in all_tasks if task.status == "Overdue"),
        due_soon=sum(1 for task in all_tasks if task.status == "Due Soon"),
        upcoming=sum(1 for task in all_tasks if task.status == "Upcoming"),
        unscheduled=sum(1 for task in all_tasks if task.status == "Unscheduled"),
        completed=sum(1 for task in all_tasks if task.status == "Completed"),
        tasks=tasks,
    )


@app.get("/api/calendar/export/xlsx")
def export_compliance_calendar(db: Session = Depends(get_db)) -> Response:
    headers = ["Status", "Due Date", "Task Type", "Title", "Owner", "Control", "Entity Type", "Entity ID", "Detail", "Link"]
    rows = [[task.status, task.due_date, task.task_type, task.title, task.owner, task.control_id, task.entity_type, task.entity_id, task.detail, task.link] for task in compliance_calendar_tasks(db)]
    return Response(
        render_xlsx("Compliance Calendar", headers, rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Compliance_Calendar.xlsx"'},
    )


@app.get("/api/evidence/package/export/docx")
def export_evidence_package(db: Session = Depends(get_db)) -> Response:
    rows = []
    controls = db.query(CmmcControl).order_by(CmmcControl.control_id).all()
    for control in controls:
        analyses = db.query(EvidenceAnalysis).filter_by(control_id=control.id).order_by(EvidenceAnalysis.coverage_score.desc()).all()
        if not analyses:
            continue
        output = db.query(GeneratedOutput).filter_by(control_id=control.id).order_by(GeneratedOutput.updated_at.desc()).first()
        policy = db.query(Policy).filter_by(control_id=control.id).order_by(Policy.updated_at.desc()).first()
        procedure = db.query(Procedure).filter_by(control_id=control.id).order_by(Procedure.updated_at.desc()).first()
        evidence_lines = []
        missing = set()
        for analysis in analyses[:5]:
            evidence = db.get(Evidence, analysis.evidence_id)
            result = json.loads(analysis.analysis_result or "{}")
            evidence_lines.append(f"{evidence.file_name if evidence else 'Evidence'} - coverage {analysis.coverage_score}%, confidence {analysis.confidence_score}%, strength {analysis.assessment_strength}")
            missing.update(result.get("missing_evidence", []))
        rows.append(
            (
                f"{control.control_id} - {control.title}",
                "\n".join(
                    [
                        f"Implementation Statement:\n{output.implementation_statement if output else 'Not generated.'}",
                        f"Policy:\n{policy.policy_name if policy else 'No policy generated.'}",
                        f"Procedure:\n{procedure.procedure_name if procedure else 'No procedure generated.'}",
                        f"Evidence:\n" + "\n".join(evidence_lines),
                        f"Missing Evidence:\n" + ("\n".join(sorted(missing)[:8]) if missing else "No missing evidence flagged by current analysis."),
                    ]
                ),
            )
        )
    sections = dict(rows) if rows else {"Evidence Package": "No analyzed evidence exists yet. Upload evidence to build an assessment package."}
    return Response(
        render_docx("CMMC Evidence Assessment Package", sections),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Evidence_Assessment_Package.docx"'},
    )


def objective_export_rows(db: Session) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    controls = db.query(CmmcControl).order_by(CmmcControl.family, CmmcControl.control_id).all()
    for control in controls:
        workspace = objective_workspace_response(db, control)
        for objective in workspace.objectives:
            evidence_files = "; ".join(dict.fromkeys(item.file_name for item in objective.evidence))
            evidence_titles = "; ".join(dict.fromkeys(item.evidence_title for item in objective.evidence))
            evidence_reviews = []
            evidence_drifts = []
            for item in objective.evidence:
                evidence = db.get(Evidence, item.evidence_id)
                if evidence:
                    evidence_reviews.append(f"{evidence.file_name}: {evidence.review_status}")
                    evidence_drifts.append(f"{evidence.file_name}: {evidence_drift_state(evidence)}")
            if not objective.evidence:
                drift_state = "No Accepted Evidence"
            else:
                states = {part.split(": ", 1)[1] for part in evidence_drifts}
                if "Rejected" in states:
                    drift_state = "Rejected"
                elif "Needs Replacement" in states:
                    drift_state = "Needs Replacement"
                elif "Stale" in states:
                    drift_state = "Stale"
                elif objective.status == "Supported" and "Current" in states:
                    drift_state = "Current"
                else:
                    drift_state = "No Accepted Evidence"
            rows.append(
                {
                    "family": workspace.family,
                    "control_id": workspace.control_id,
                    "control_title": workspace.control_title,
                    "requirement": workspace.requirement,
                    "objective_label": objective.label,
                    "objective": objective.objective,
                    "status": objective.status,
                    "coverage_score": objective.coverage_score,
                    "evidence_count": objective.evidence_count,
                    "evidence_files": evidence_files,
                    "evidence_titles": evidence_titles,
                    "evidence_review_status": "; ".join(dict.fromkeys(evidence_reviews)),
                    "drift_state": drift_state,
                    "assessor_notes": objective.assessor_notes,
                    "missing_evidence": "; ".join(objective.missing_evidence),
                    "recommendations": "; ".join(objective.recommendations),
                }
            )
    return rows


@app.get("/api/evidence/objective-matrix/export/xlsx")
def export_objective_matrix(db: Session = Depends(get_db)) -> Response:
    headers = [
        "Family",
        "Control",
        "Title",
        "Objective",
        "Objective Statement",
        "Status",
        "Coverage",
        "Evidence Count",
        "Evidence Files",
        "Evidence Review Status",
        "Drift State",
        "Assessor Notes",
        "Missing Evidence",
        "Recommendations",
    ]
    rows = [
        [
            str(row["family"]),
            str(row["control_id"]),
            str(row["control_title"]),
            str(row["objective_label"]),
            str(row["objective"]),
            str(row["status"]),
            f"{row['coverage_score']}%",
            str(row["evidence_count"]),
            str(row["evidence_files"]),
            str(row["evidence_review_status"]),
            str(row["drift_state"]),
            str(row["assessor_notes"]),
            str(row["missing_evidence"]),
            str(row["recommendations"]),
        ]
        for row in objective_export_rows(db)
    ]
    return Response(
        render_xlsx("Objective Matrix", headers, rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Objective_Coverage_Matrix.xlsx"'},
    )


def assessment_package_controls(db: Session, scope: str = "all", value: str = "", q: str = "") -> list[CmmcControl]:
    query = db.query(CmmcControl).order_by(CmmcControl.family, CmmcControl.control_id)
    scope_value = value.strip()
    if scope == "family" and scope_value:
        query = query.filter(CmmcControl.family == scope_value)
    elif scope == "control" and scope_value:
        query = query.filter(CmmcControl.control_id == scope_value)
    controls = query.all()
    needle = q.strip().lower()
    if needle:
        controls = [
            control
            for control in controls
            if needle in f"{control.control_id} {control.title} {control.family} {control.requirement}".lower()
        ]
    return controls


def control_evidence_items(db: Session, control: CmmcControl) -> list[Evidence]:
    rows = []
    for evidence in db.query(Evidence).order_by(Evidence.uploaded_at.desc()).all():
        if control.control_id in evidence_control_ids(db, evidence):
            rows.append(evidence)
    return rows


def control_open_poam_items(db: Session, control: CmmcControl) -> list[str]:
    items = [
        f"{item.objective_label}: {item.gap_statement}"
        for item in db.query(ManagedPoamItem).filter_by(control_id=control.control_id).all()
        if item.status != "Closed"
    ]
    for output in db.query(GeneratedOutput).filter_by(control_id=control.id).all():
        for item in db.query(PoamItem).filter_by(generated_output_id=output.id).all():
            if item.status != "Closed":
                items.append(item.gap)
    return items


def assessment_package_control_row(db: Session, control: CmmcControl) -> AssessmentPackageControlOut:
    output = db.query(GeneratedOutput).filter_by(control_id=control.id).order_by(GeneratedOutput.updated_at.desc()).first()
    policy = db.query(Policy).filter_by(control_id=control.id).order_by(Policy.updated_at.desc()).first()
    procedure = db.query(Procedure).filter_by(control_id=control.id).order_by(Procedure.updated_at.desc()).first()
    mapped_docs = db.query(ControlMapping).filter_by(control_id=control.id).all()
    policy_mapped = policy or any("policy" in (db.get(ComplianceDocument, mapping.document_id).document_type.lower() if db.get(ComplianceDocument, mapping.document_id) else "") for mapping in mapped_docs)
    procedure_mapped = procedure or any("procedure" in (db.get(ComplianceDocument, mapping.document_id).document_type.lower() if db.get(ComplianceDocument, mapping.document_id) else "") for mapping in mapped_docs)
    evidence_items = control_evidence_items(db, control)
    accepted = [item for item in evidence_items if item.review_status == "Accepted"]
    stale = [item for item in evidence_items if evidence_drift_state(item) == "Stale"]
    open_poam = control_open_poam_items(db, control)

    warnings = []
    if not output:
        warnings.append("Missing implementation statement")
    if not policy_mapped:
        warnings.append("Missing policy reference")
    if not procedure_mapped:
        warnings.append("Missing procedure reference")
    if not accepted:
        warnings.append("No accepted evidence")
    if open_poam:
        warnings.append(f"{len(open_poam)} open POA&M item(s)")
    if stale:
        warnings.append(f"{len(stale)} stale evidence item(s)")

    readiness = 0
    readiness += 20 if output else 0
    readiness += 15 if policy_mapped else 0
    readiness += 15 if procedure_mapped else 0
    readiness += 35 if accepted else 0
    readiness += 15 if not open_poam else 0
    if stale:
        readiness = max(0, readiness - 10)

    return AssessmentPackageControlOut(
        control_id=control.control_id,
        title=control.title,
        family=control.family,
        readiness_score=readiness,
        implementation_status="Present" if output else "Missing",
        policy_status="Present" if policy_mapped else "Missing",
        procedure_status="Present" if procedure_mapped else "Missing",
        accepted_evidence=len(accepted),
        evidence_total=len(evidence_items),
        open_poam=len(open_poam),
        stale_evidence=len(stale),
        warnings=warnings,
    )


def assessment_package_summary(db: Session, scope: str = "all", value: str = "", q: str = "") -> AssessmentPackageSummaryOut:
    rows = [assessment_package_control_row(db, control) for control in assessment_package_controls(db, scope, value, q)]
    total = len(rows)
    ready = sum(1 for row in rows if not row.warnings)
    return AssessmentPackageSummaryOut(
        scope=value if scope in {"family", "control"} and value else "All Level 2 controls",
        total_controls=total,
        ready_controls=ready,
        warning_controls=sum(1 for row in rows if row.warnings),
        missing_implementation=sum(1 for row in rows if row.implementation_status == "Missing"),
        missing_policy=sum(1 for row in rows if row.policy_status == "Missing"),
        missing_procedure=sum(1 for row in rows if row.procedure_status == "Missing"),
        controls_without_accepted_evidence=sum(1 for row in rows if row.accepted_evidence == 0),
        open_poam_items=sum(row.open_poam for row in rows),
        stale_evidence=sum(row.stale_evidence for row in rows),
        completeness_score=round(sum(row.readiness_score for row in rows) / total) if total else 0,
        controls=rows,
    )


def assessment_package_sections(db: Session, controls: list[CmmcControl], include_documents: bool, include_evidence: bool, include_poam: bool, include_warnings: bool) -> dict[str, str]:
    sections: dict[str, str] = {
        "Package Summary": f"Assessment package prepared on {datetime.utcnow().strftime('%Y-%m-%d')}.\nControls included: {len(controls)}.\nThis package assembles control requirements, assessment objectives, implementation statements, document references, evidence status, POA&M status, and readiness warnings from the current CMMC Pilot records.",
    }
    for control in controls:
        output = db.query(GeneratedOutput).filter_by(control_id=control.id).order_by(GeneratedOutput.updated_at.desc()).first()
        objectives = db.query(AssessmentObjective).filter_by(control_id=control.id).order_by(AssessmentObjective.label).all()
        policy = db.query(Policy).filter_by(control_id=control.id).order_by(Policy.updated_at.desc()).first()
        procedure = db.query(Procedure).filter_by(control_id=control.id).order_by(Procedure.updated_at.desc()).first()
        evidence_items = control_evidence_items(db, control)
        open_poam = control_open_poam_items(db, control)
        row = assessment_package_control_row(db, control)
        lines = [
            f"Requirement:\n{control.requirement}",
            "Assessment Objectives:\n" + ("\n".join(f"{objective.label}. {objective.objective}" for objective in objectives) if objectives else "No assessment objectives loaded."),
            f"Implementation Statement:\n{output.implementation_statement if output else 'Not generated.'}",
            f"Responsible Parties:\n{output.responsible_parties if output else 'Not documented.'}",
            f"Assessment Notes:\n{output.assessment_notes if output else 'Not documented.'}",
        ]
        if include_documents:
            lines.append(f"Policy Reference:\n{policy.policy_name if policy else 'No generated policy found. Check uploaded compliance documents for mapped references.'}")
            lines.append(f"Procedure Reference:\n{procedure.procedure_name if procedure else 'No generated procedure found. Check uploaded compliance documents for mapped references.'}")
        if include_evidence:
            evidence_lines = [
                f"{item.title} ({item.file_name}) - review {item.review_status}; drift {evidence_drift_state(item)}"
                for item in evidence_items
            ]
            lines.append("Evidence:\n" + ("\n".join(evidence_lines) if evidence_lines else "No evidence mapped to this control."))
        if include_poam:
            lines.append("POA&M Items:\n" + ("\n".join(open_poam[:12]) if open_poam else "No open POA&M items recorded."))
        if include_warnings:
            lines.append("Readiness Warnings:\n" + ("\n".join(row.warnings) if row.warnings else "No package warnings for this control."))
        sections[f"{control.control_id} - {control.title}"] = "\n\n".join(lines)
    return sections


@app.get("/api/assessment-package/summary", response_model=AssessmentPackageSummaryOut)
def get_assessment_package_summary(scope: str = "all", value: str = "", q: str = "", db: Session = Depends(get_db)) -> AssessmentPackageSummaryOut:
    return assessment_package_summary(db, scope, value, q)


@app.get("/api/assessment-package/export/{kind}")
def export_assessment_package(
    kind: str,
    scope: str = "all",
    value: str = "",
    include_documents: bool = True,
    include_evidence: bool = True,
    include_poam: bool = True,
    include_warnings: bool = True,
    db: Session = Depends(get_db),
) -> Response:
    controls = assessment_package_controls(db, scope, value)
    sections = assessment_package_sections(db, controls, include_documents, include_evidence, include_poam, include_warnings)
    suffix = value.replace(" ", "_").replace("/", "_") if value else "All_Controls"
    filename = f"CMMC_Assessment_Package_{suffix}"
    if kind == "docx":
        return Response(
            render_docx("CMMC Assessment Package", sections),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}.docx"'},
        )
    if kind == "pdf":
        return Response(
            render_pdf("CMMC Assessment Package", sections),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
        )
    raise HTTPException(status_code=400, detail="Export kind must be docx or pdf.")


@app.get("/api/assessment-package/export/matrix/xlsx")
def export_assessment_package_matrix(scope: str = "all", value: str = "", db: Session = Depends(get_db)) -> Response:
    summary = assessment_package_summary(db, scope, value)
    headers = [
        "Family",
        "Control",
        "Title",
        "Readiness",
        "Implementation",
        "Policy",
        "Procedure",
        "Accepted Evidence",
        "Total Evidence",
        "Open POAM",
        "Stale Evidence",
        "Warnings",
    ]
    rows = [
        [
            row.family,
            row.control_id,
            row.title,
            f"{row.readiness_score}%",
            row.implementation_status,
            row.policy_status,
            row.procedure_status,
            str(row.accepted_evidence),
            str(row.evidence_total),
            str(row.open_poam),
            str(row.stale_evidence),
            "; ".join(row.warnings),
        ]
        for row in summary.controls
    ]
    return Response(
        render_xlsx("Assessment Matrix", headers, rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Assessment_Package_Matrix.xlsx"'},
    )


def managed_poam_response(item: ManagedPoamItem) -> ManagedPoamItemOut:
    return ManagedPoamItemOut(
        id=item.id,
        control_id=item.control_id,
        control_title=item.control_title,
        objective_label=item.objective_label,
        objective=item.objective,
        gap_statement=item.gap_statement,
        evidence_needed=item.evidence_needed,
        corrective_action=item.corrective_action,
        owner=item.owner,
        due_date=item.due_date,
        risk=item.risk,
        status=item.status,
        notes=item.notes,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


def managed_poam_query(db: Session, q: str = "", status: str = "", risk: str = "", control_id: str = "") -> list[ManagedPoamItem]:
    rows = db.query(ManagedPoamItem).order_by(ManagedPoamItem.status, ManagedPoamItem.risk.desc(), ManagedPoamItem.control_id).all()
    if q:
        needle = q.lower()
        rows = [item for item in rows if needle in f"{item.control_id} {item.control_title} {item.objective} {item.gap_statement} {item.evidence_needed} {item.owner}".lower()]
    if status:
        rows = [item for item in rows if item.status.lower() == status.lower()]
    if risk:
        rows = [item for item in rows if item.risk.lower() == risk.lower()]
    if control_id:
        rows = [item for item in rows if item.control_id.lower() == control_id.lower()]
    return rows


def poam_evidence_needed(db: Session, control_id: str, objective: str) -> str:
    control = db.query(CmmcControl).filter_by(control_id=control_id).first()
    if not control:
        return "Confirm the required evidence artifacts for this objective."
    stored_evidence = [row.artifact for row in db.query(EvidenceRequirement).filter_by(control_id=control.id).all()]
    candidates = evidence_for_control(control, stored_evidence)
    objective_terms = set(re.findall(r"[a-z0-9]{3,}", f"{objective} {control.title} {control.requirement}".lower()))
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (
            -len(objective_terms & set(re.findall(r"[a-z0-9]{3,}", item[1].lower()))),
            item[0],
        ),
    )
    selected = [candidate for _index, candidate in ranked[:4]]
    return "\n".join(f"- {candidate}" for candidate in selected)


def combined_poam_evidence_needed(db: Session, row: dict[str, object]) -> str:
    control_id = str(row["control_id"])
    items = [line.removeprefix("- ").strip() for line in poam_evidence_needed(db, control_id, str(row["objective"])).splitlines() if line.strip()]
    items.extend(item.strip() for item in str(row["missing_evidence"]).split(";") if item.strip())
    return "\n".join(f"- {item}" for item in dict.fromkeys(items))


@app.get("/api/poam", response_model=list[ManagedPoamItemOut])
def list_managed_poam(q: str = "", status: str = "", risk: str = "", control_id: str = "", db: Session = Depends(get_db)) -> list[ManagedPoamItemOut]:
    return [managed_poam_response(item) for item in managed_poam_query(db, q, status, risk, control_id)]


@app.post("/api/poam/generate", response_model=ManagedPoamGenerateOut)
def generate_managed_poam(db: Session = Depends(get_db)) -> ManagedPoamGenerateOut:
    org = db.query(Organization).first() or Organization(name="Default Organization")
    db.add(org)
    db.flush()
    created = 0
    existing = 0
    for row in objective_export_rows(db):
        objective_status = str(row["status"])
        drift = str(row["drift_state"])
        if objective_status == "Supported" and drift == "Current":
            continue
        control_id = str(row["control_id"])
        objective_label = str(row["objective_label"])
        evidence_needed = combined_poam_evidence_needed(db, row)
        current = db.query(ManagedPoamItem).filter_by(control_id=control_id, objective_label=objective_label).filter(ManagedPoamItem.status != "Closed").first()
        if current:
            if current.notes == "Generated from objective evidence coverage and drift analysis.":
                current.evidence_needed = evidence_needed
                current.corrective_action = str(row["recommendations"]) or f"Collect, review, and accept the listed evidence for {control_id} objective {objective_label}."
            existing += 1
            continue
        risk = "High" if drift in {"Rejected", "Needs Replacement", "No Accepted Evidence"} or objective_status == "Not Supported" else "Medium"
        item = ManagedPoamItem(
            organization_id=org.id,
            control_id=control_id,
            control_title=str(row["control_title"]),
            objective_label=objective_label,
            objective=str(row["objective"]),
            gap_statement=f"{control_id} objective {objective_label} is {objective_status.lower()} with drift state {drift}.",
            evidence_needed=evidence_needed,
            corrective_action=str(row["recommendations"]) or f"Collect, review, and accept the listed evidence for {control_id} objective {objective_label}.",
            owner="Compliance Owner",
            risk=risk,
            status="Open",
            notes="Generated from objective evidence coverage and drift analysis.",
        )
        db.add(item)
        db.flush()
        created += 1
        log_activity(db, "POA&M Created", "Managed POA&M", item.id, f"POA&M created from {objective_status} objective with drift state {drift}.", control_id)
    db.commit()
    total_open = db.query(ManagedPoamItem).filter(ManagedPoamItem.status != "Closed").count()
    return ManagedPoamGenerateOut(created=created, existing=existing, total_open=total_open)


@app.put("/api/poam/{poam_id}", response_model=ManagedPoamItemOut)
def update_managed_poam(poam_id: int, payload: ManagedPoamUpdate, db: Session = Depends(get_db)) -> ManagedPoamItemOut:
    item = db.get(ManagedPoamItem, poam_id)
    if not item:
        raise HTTPException(status_code=404, detail="POA&M item not found.")
    previous_status = item.status
    item.gap_statement = payload.gap_statement
    item.evidence_needed = payload.evidence_needed
    item.corrective_action = payload.corrective_action
    item.owner = payload.owner
    item.due_date = payload.due_date
    item.risk = payload.risk
    item.status = payload.status
    item.notes = payload.notes
    action = "POA&M Status Changed" if previous_status != payload.status else "POA&M Updated"
    detail = (
        f"{item.control_id} objective {item.objective_label} changed from {previous_status} to {payload.status}."
        if previous_status != payload.status
        else f"{item.control_id} objective {item.objective_label} was updated with status {payload.status}."
    )
    log_activity(db, action, "Managed POA&M", item.id, f"{detail} Owner: {payload.owner}. Due: {payload.due_date or 'Not set'}. Risk: {payload.risk}.", item.control_id, payload.owner)
    db.commit()
    db.refresh(item)
    return managed_poam_response(item)


@app.get("/api/poam/export/xlsx")
def export_managed_poam(db: Session = Depends(get_db)) -> Response:
    headers = ["Control", "Title", "Objective", "Objective Statement", "Gap Statement", "Evidence Needed", "Corrective Action", "Owner", "Due Date", "Risk", "Status", "Notes"]
    rows = [
        [item.control_id, item.control_title, item.objective_label, item.objective, item.gap_statement, item.evidence_needed, item.corrective_action, item.owner, item.due_date, item.risk, item.status, item.notes]
        for item in managed_poam_query(db)
    ]
    return Response(
        render_xlsx("Managed POAM", headers, rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CMMC_Managed_POAM.xlsx"'},
    )


@app.post("/api/generate", response_model=GeneratedOutputOut)
def generate(payload: GenerateIn, db: Session = Depends(get_db)) -> GeneratedOutputOut:
    profile = db.get(CompanyProfile, payload.company_profile_id)
    control = db.query(CmmcControl).filter_by(control_id=payload.control_id).first()
    if not profile or not control:
        raise HTTPException(status_code=404, detail="Profile or control not found.")
    objectives = [f"{obj.label}. {obj.objective}" for obj in control.objectives]
    stored_evidence = [row.artifact for row in db.query(EvidenceRequirement).filter_by(control_id=control.id).all()]
    evidence = evidence_for_control(control, stored_evidence)
    generated = generate_output(control, objectives, profile, evidence)
    output = GeneratedOutput(company_profile_id=profile.id, control_id=control.id, **generated)
    db.add(output)
    db.commit()
    db.refresh(output)
    return output_response(db, output)


@app.put("/api/outputs/{output_id}", response_model=GeneratedOutputOut)
def update_output(output_id: int, payload: GeneratedOutputUpdate, db: Session = Depends(get_db)) -> GeneratedOutputOut:
    output = db.get(GeneratedOutput, output_id)
    if not output:
        raise HTTPException(status_code=404, detail="Output not found.")
    for key, value in payload.model_dump().items():
        setattr(output, key, value)
    db.commit()
    db.refresh(output)
    return output_response(db, output)


@app.get("/api/outputs/{output_id}/export/{kind}")
def export_output(output_id: int, kind: str, db: Session = Depends(get_db)) -> Response:
    output = db.get(GeneratedOutput, output_id)
    if not output:
        raise HTTPException(status_code=404, detail="Output not found.")
    control = db.get(CmmcControl, output.control_id)
    title = f"{control.control_id} - {control.title}" if control else "CMMC Generated Output"
    sections = {
        "Implementation Statement": output.implementation_statement,
        "Responsible Parties": output.responsible_parties,
        "Evidence Artifacts": output.evidence_artifacts,
        "Assessment Notes": output.assessment_notes,
        "Gaps or Assumptions": output.gaps_assumptions,
    }
    if kind == "docx":
        content = render_docx(title, sections)
        return Response(content, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="{control.control_id}.docx"'})
    if kind == "pdf":
        content = render_pdf(title, sections)
        return Response(content, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{control.control_id}.pdf"'})
    raise HTTPException(status_code=400, detail="Export kind must be docx or pdf.")


@app.post("/api/ssp/generate", response_model=SSPDocumentOut)
def generate_ssp(payload: SSPGenerateIn, db: Session = Depends(get_db)) -> SSPDocumentOut:
    profile = db.get(CompanyProfile, payload.company_profile_id)
    system = db.get(System, payload.system_id)
    if not profile or not system:
        raise HTTPException(status_code=404, detail="Profile or system not found.")
    sections = build_ssp_sections(db, profile, system)
    score = ssp_completeness(system, sections)
    ssp = SSPDocument(
        organization_id=system.organization_id,
        system_id=system.id,
        version="1.0",
        status="Draft",
        completeness_score=score,
        document_json=json.dumps({name: content for name, content in sections}),
    )
    db.add(ssp)
    db.commit()
    db.refresh(ssp)
    log_activity(db, "SSP Generated", "SSP", ssp.id, f"SSP generated for system {system.system_name} with completeness score {score}%.", user_name="CMMC Pilot")
    for index, (name, content) in enumerate(sections, start=1):
        db.add(SSPSection(ssp_document_id=ssp.id, section_name=name, section_content=content, sort_order=index))
    db.commit()
    return ssp_response(db, ssp)


@app.put("/api/ssp/sections/{section_id}", response_model=SSPSectionOut)
def update_ssp_section(section_id: int, payload: SSPSectionUpdate, db: Session = Depends(get_db)) -> SSPSectionOut:
    section = db.get(SSPSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="SSP section not found.")
    section.section_content = payload.section_content
    log_activity(db, "SSP Section Updated", "SSP", section.ssp_document_id, f"Section '{section.section_name}' was updated.")
    db.commit()
    db.refresh(section)
    return SSPSectionOut(id=section.id, section_name=section.section_name, section_content=section.section_content, sort_order=section.sort_order)


@app.get("/api/ssp/{ssp_id}/export/{kind}")
def export_ssp(ssp_id: int, kind: str, db: Session = Depends(get_db)) -> Response:
    ssp = db.get(SSPDocument, ssp_id)
    if not ssp:
        raise HTTPException(status_code=404, detail="SSP not found.")
    system = db.get(System, ssp.system_id)
    sections = db.query(SSPSection).filter_by(ssp_document_id=ssp.id).order_by(SSPSection.sort_order).all()
    title = f"{system.system_name if system else 'System'} SSP"
    export_sections = {
        "Title Page": f"{title}\nVersion: {ssp.version}\nStatus: {ssp.status}\nCompleteness Score: {ssp.completeness_score}%",
        "Revision History": f"Version {ssp.version} generated as {ssp.status}.",
    }
    standalone_sections = {"Continuous Monitoring", "POA&M References"}
    export_sections.update(
        {
            section.section_name: section.section_content
            for section in sections
            if section.section_name not in standalone_sections
        }
    )
    filename = title.replace(" ", "_")
    if kind == "docx":
        metadata = {
            "System Name": system.system_name if system else "System",
            "System Owner": system.system_owner if system else "To be assigned",
            "Version": ssp.version,
            "Status": ssp.status,
            "Completeness Score": f"{ssp.completeness_score}%",
            "Author": "CMMC Pilot",
            "Review Date": "Annual review or upon significant system change",
        }
        return Response(render_ssp_docx(title, export_sections, metadata), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="{filename}.docx"'})
    if kind == "pdf":
        return Response(render_pdf(title, export_sections), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'})
    raise HTTPException(status_code=400, detail="Export kind must be docx or pdf.")


@app.get("/api/ssp/{ssp_id}/export/continuous-monitoring/docx")
def export_continuous_monitoring(ssp_id: int, db: Session = Depends(get_db)) -> Response:
    ssp = db.get(SSPDocument, ssp_id)
    if not ssp:
        raise HTTPException(status_code=404, detail="SSP not found.")
    system = db.get(System, ssp.system_id)
    section = db.query(SSPSection).filter_by(ssp_document_id=ssp.id, section_name="Continuous Monitoring").first()
    title = f"{system.system_name if system else 'System'} Continuous Monitoring Plan"
    sections = {
        "Document Metadata": f"Version: {ssp.version}\nStatus: {ssp.status}\nSource SSP ID: {ssp.id}",
        "Continuous Monitoring": section.section_content if section else "Continuous monitoring content has not been generated yet.",
        "Monitoring Records": "Maintain recurring evidence for access reviews, vulnerability scans, audit log reviews, incident handling, endpoint compliance, backup monitoring, and POA&M status updates.",
    }
    filename = title.replace(" ", "_")
    return Response(
        render_docx(title, sections),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}.docx"'},
    )


@app.get("/api/ssp/{ssp_id}/export/poam/xlsx")
def export_poam(ssp_id: int, db: Session = Depends(get_db)) -> Response:
    ssp = db.get(SSPDocument, ssp_id)
    if not ssp:
        raise HTTPException(status_code=404, detail="SSP not found.")
    headers = [
        "Control ID",
        "Control Title",
        "Weakness / Gap",
        "Owner",
        "Finding Status",
        "Risk Rating",
        "Corrective Action / Milestones",
        "Target Date",
        "Closure Status",
    ]
    content = render_xlsx("POAM", headers, poam_rows(db, ssp))
    system = db.get(System, ssp.system_id)
    filename = f"{(system.system_name if system else 'System').replace(' ', '_')}_POAM.xlsx"
    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/documents/policies/generate", response_model=DocumentOut)
def generate_policy(payload: DocumentGenerateIn, db: Session = Depends(get_db)) -> DocumentOut:
    profile = db.get(CompanyProfile, payload.company_profile_id)
    control = db.query(CmmcControl).filter_by(control_id=payload.control_id).first()
    if not profile or not control:
        raise HTTPException(status_code=404, detail="Profile or control not found.")
    generated = generate_policy_document(control, profile, family_items_for_control(db, control))
    policy = Policy(
        organization_id=profile.organization_id,
        control_id=control.id,
        policy_name=generated["name"],
        policy_text=generated["text"],
        responsibility_matrix=generated["responsibility_matrix"],
        version="1.0",
        author="CMMC Pilot",
        approver="Pending",
        review_date="Annual review or upon significant system change",
        status="Draft",
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    log_activity(db, "Policy Generated", "Policy", policy.id, f"{policy.policy_name} generated as version {policy.version}.", control.control_id, "CMMC Pilot")
    create_document_version(db, policy, "policy")
    db.commit()
    return document_response(db, policy, "policy")


@app.post("/api/documents/procedures/generate", response_model=DocumentOut)
def generate_procedure(payload: DocumentGenerateIn, db: Session = Depends(get_db)) -> DocumentOut:
    profile = db.get(CompanyProfile, payload.company_profile_id)
    control = db.query(CmmcControl).filter_by(control_id=payload.control_id).first()
    if not profile or not control:
        raise HTTPException(status_code=404, detail="Profile or control not found.")
    generated = generate_procedure_document(control, profile, family_items_for_control(db, control))
    procedure = Procedure(
        organization_id=profile.organization_id,
        control_id=control.id,
        procedure_name=generated["name"],
        procedure_text=generated["text"],
        responsibility_matrix=generated["responsibility_matrix"],
        version="1.0",
        author="CMMC Pilot",
        approver="Pending",
        review_date="Annual review or upon significant system change",
        status="Draft",
    )
    db.add(procedure)
    db.commit()
    db.refresh(procedure)
    log_activity(db, "Procedure Generated", "Procedure", procedure.id, f"{procedure.procedure_name} generated as version {procedure.version}.", control.control_id, "CMMC Pilot")
    create_document_version(db, procedure, "procedure")
    db.commit()
    return document_response(db, procedure, "procedure")


@app.put("/api/documents/{document_type}/{document_id}", response_model=DocumentOut)
def update_document(document_type: str, document_id: int, payload: DocumentUpdate, db: Session = Depends(get_db)) -> DocumentOut:
    model = Policy if document_type == "policy" else Procedure if document_type == "procedure" else None
    if model is None:
        raise HTTPException(status_code=400, detail="Document type must be policy or procedure.")
    document = db.get(model, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    if document_type == "policy":
        document.policy_name = payload.name
        document.policy_text = payload.text
    else:
        document.procedure_name = payload.name
        document.procedure_text = payload.text
    document.responsibility_matrix = payload.responsibility_matrix
    document.version = payload.version
    document.author = payload.author
    document.approver = payload.approver
    document.approval_date = payload.approval_date
    document.review_date = payload.review_date
    document.status = payload.status
    control = db.get(CmmcControl, document.control_id)
    log_activity(db, f"{document_type.title()} Updated", document_type.title(), document.id, f"{payload.name} saved as version {payload.version} with status {payload.status}.", control.control_id if control else "", payload.author)
    db.commit()
    db.refresh(document)
    create_document_version(db, document, document_type)
    db.commit()
    return document_response(db, document, document_type)


@app.get("/api/documents/{document_type}/{document_id}/export/{kind}")
def export_document(document_type: str, document_id: int, kind: str, db: Session = Depends(get_db)) -> Response:
    model = Policy if document_type == "policy" else Procedure if document_type == "procedure" else None
    if model is None:
        raise HTTPException(status_code=400, detail="Document type must be policy or procedure.")
    document = db.get(model, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    response = document_response(db, document, document_type)
    title = response.name
    sections = {
        "Document Control": "\n".join(
            [
                f"Version: {response.version}",
                f"Status: {response.status}",
                f"Author: {response.author}",
                f"Approver: {response.approver}",
                f"Approval Date: {response.approval_date or 'Pending'}",
                f"Review Date: {response.review_date}",
            ]
        ),
        "Document Text": response.text,
        "Responsibility Matrix": response.responsibility_matrix,
    }
    filename = response.name.replace(" ", "_")
    if kind == "docx":
        content = render_docx(title, sections)
        return Response(content, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="{filename}.docx"'})
    if kind == "pdf":
        content = render_pdf(title, sections)
        return Response(content, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'})
    raise HTTPException(status_code=400, detail="Export kind must be docx or pdf.")


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict[str, int]:
    total = db.query(CmmcControl).count()
    generated = db.query(GeneratedOutput.control_id).distinct().count()
    evidence = db.query(Evidence).count()
    poams = db.query(PoamItem).filter(PoamItem.status != "Closed").count() + db.query(ManagedPoamItem).filter(ManagedPoamItem.status != "Closed").count()
    readiness = int((generated / total) * 100) if total else 0
    open_gaps = db.query(GeneratedOutput).filter(GeneratedOutput.gaps_assumptions.ilike("%must%")).count()
    tasks = compliance_calendar_tasks(db)
    reviews = control_review_dashboard_response(db)
    requests = evidence_request_dashboard(db)
    return {
        "controls_complete": generated,
        "total_controls": total,
        "evidence_uploaded": evidence,
        "open_gaps": open_gaps,
        "poam_items": poams,
        "overdue_tasks": sum(1 for task in tasks if task.status == "Overdue"),
        "due_soon_tasks": sum(1 for task in tasks if task.status == "Due Soon"),
        "unscheduled_tasks": sum(1 for task in tasks if task.status == "Unscheduled"),
        "reviews_in_review": reviews.in_review,
        "reviews_approved": reviews.approved,
        "reviews_rejected": reviews.rejected,
        "evidence_requests_open": requests.draft + requests.sent + requests.submitted,
        "evidence_requests_overdue": requests.overdue,
        "assessment_readiness_score": readiness,
    }
