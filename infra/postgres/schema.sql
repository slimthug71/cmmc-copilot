CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS organizations (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255) NOT NULL DEFAULT 'MVP User',
  role VARCHAR(100) NOT NULL DEFAULT 'admin'
);

CREATE TABLE IF NOT EXISTS company_profiles (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  company_name VARCHAR(255) NOT NULL,
  industry VARCHAR(255) NOT NULL,
  employee_count VARCHAR(100) NOT NULL,
  locations TEXT NOT NULL,
  cloud_environment TEXT NOT NULL,
  cui_environment TEXT NOT NULL,
  msp_involvement TEXT NOT NULL,
  mfa_solution TEXT NOT NULL,
  endpoint_management TEXT NOT NULL,
  backup_solution TEXT NOT NULL,
  ticketing_system TEXT NOT NULL,
  hr_onboarding_process TEXT NOT NULL,
  access_removal_process TEXT NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cmmc_controls (
  id SERIAL PRIMARY KEY,
  control_id VARCHAR(50) UNIQUE NOT NULL,
  family VARCHAR(100) NOT NULL,
  title VARCHAR(255) NOT NULL,
  requirement TEXT NOT NULL,
  level INTEGER NOT NULL DEFAULT 2
);

CREATE TABLE IF NOT EXISTS assessment_objectives (
  id SERIAL PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  label VARCHAR(50) NOT NULL,
  objective TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_requirements (
  id SERIAL PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  artifact TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_evidence_sources (
  id SERIAL PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  evidence_name VARCHAR(255) NOT NULL,
  source_type VARCHAR(100) NOT NULL,
  connected_system VARCHAR(100) NOT NULL DEFAULT '',
  collection_method VARCHAR(100) NOT NULL DEFAULT 'Manual Upload',
  review_frequency VARCHAR(100) NOT NULL DEFAULT 'Quarterly',
  required VARCHAR(10) NOT NULL DEFAULT 'true',
  description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS monitoring_rules (
  id SERIAL PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  rule_name VARCHAR(255) NOT NULL,
  source_system VARCHAR(100) NOT NULL,
  condition TEXT NOT NULL,
  severity VARCHAR(50) NOT NULL DEFAULT 'Medium',
  enabled VARCHAR(10) NOT NULL DEFAULT 'true'
);

CREATE TABLE IF NOT EXISTS drift_alerts (
  id SERIAL PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  alert_type VARCHAR(100) NOT NULL,
  severity VARCHAR(50) NOT NULL DEFAULT 'Medium',
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  recommended_action TEXT NOT NULL DEFAULT '',
  status VARCHAR(100) NOT NULL DEFAULT 'Open',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_outputs (
  id SERIAL PRIMARY KEY,
  company_profile_id INTEGER NOT NULL REFERENCES company_profiles(id),
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  implementation_statement TEXT NOT NULL,
  responsible_parties TEXT NOT NULL,
  evidence_artifacts TEXT NOT NULL,
  assessment_notes TEXT NOT NULL,
  gaps_assumptions TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policies (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  policy_name VARCHAR(255) NOT NULL,
  policy_text TEXT NOT NULL,
  responsibility_matrix TEXT NOT NULL,
  version VARCHAR(50) NOT NULL DEFAULT '1.0',
  author VARCHAR(255) NOT NULL DEFAULT 'CMMC Pilot',
  approver VARCHAR(255) NOT NULL DEFAULT 'Pending',
  approval_date VARCHAR(50) NOT NULL DEFAULT '',
  review_date VARCHAR(50) NOT NULL DEFAULT '',
  status VARCHAR(100) NOT NULL DEFAULT 'Draft',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS procedures (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  procedure_name VARCHAR(255) NOT NULL,
  procedure_text TEXT NOT NULL,
  responsibility_matrix TEXT NOT NULL,
  version VARCHAR(50) NOT NULL DEFAULT '1.0',
  author VARCHAR(255) NOT NULL DEFAULT 'CMMC Pilot',
  approver VARCHAR(255) NOT NULL DEFAULT 'Pending',
  approval_date VARCHAR(50) NOT NULL DEFAULT '',
  review_date VARCHAR(50) NOT NULL DEFAULT '',
  status VARCHAR(100) NOT NULL DEFAULT 'Draft',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policy_templates (
  id SERIAL PRIMARY KEY,
  policy_name VARCHAR(255) UNIQUE NOT NULL,
  control_family VARCHAR(100) NOT NULL,
  template_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS procedure_templates (
  id SERIAL PRIMARY KEY,
  procedure_name VARCHAR(255) UNIQUE NOT NULL,
  control_family VARCHAR(100) NOT NULL,
  template_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_versions (
  id SERIAL PRIMARY KEY,
  document_type VARCHAR(50) NOT NULL,
  document_id INTEGER NOT NULL,
  version VARCHAR(50) NOT NULL,
  document_text TEXT NOT NULL,
  responsibility_matrix TEXT NOT NULL,
  author VARCHAR(255) NOT NULL DEFAULT 'CMMC Pilot',
  status VARCHAR(100) NOT NULL DEFAULT 'Draft',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_approvals (
  id SERIAL PRIMARY KEY,
  document_type VARCHAR(50) NOT NULL,
  document_id INTEGER NOT NULL,
  approver VARCHAR(255) NOT NULL,
  approval_date VARCHAR(50) NOT NULL,
  status VARCHAR(100) NOT NULL DEFAULT 'Pending',
  comments TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS systems (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  system_name VARCHAR(255) NOT NULL,
  system_owner VARCHAR(255) NOT NULL,
  data_owner VARCHAR(255) NOT NULL DEFAULT '',
  business_function TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL,
  boundary_description TEXT NOT NULL,
  cui_description TEXT NOT NULL,
  infrastructure TEXT NOT NULL DEFAULT '',
  security_stack TEXT NOT NULL DEFAULT '',
  external_providers TEXT NOT NULL DEFAULT '',
  cui_created TEXT NOT NULL DEFAULT '',
  cui_stored TEXT NOT NULL DEFAULT '',
  cui_transmitted TEXT NOT NULL DEFAULT '',
  cui_archived TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ssp_documents (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  system_id INTEGER NOT NULL REFERENCES systems(id),
  version VARCHAR(50) NOT NULL DEFAULT '1.0',
  status VARCHAR(100) NOT NULL DEFAULT 'Draft',
  document_json TEXT NOT NULL,
  generated_docx_path TEXT NOT NULL DEFAULT '',
  generated_pdf_path TEXT NOT NULL DEFAULT '',
  completeness_score INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ssp_sections (
  id SERIAL PRIMARY KEY,
  ssp_document_id INTEGER NOT NULL REFERENCES ssp_documents(id),
  section_name VARCHAR(255) NOT NULL,
  section_content TEXT NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS poam_items (
  id SERIAL PRIMARY KEY,
  generated_output_id INTEGER NOT NULL REFERENCES generated_outputs(id),
  gap TEXT NOT NULL,
  owner VARCHAR(255) NOT NULL DEFAULT 'Unassigned',
  status VARCHAR(100) NOT NULL DEFAULT 'Open'
);

CREATE TABLE IF NOT EXISTS uploaded_evidence (
  id SERIAL PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  file_name VARCHAR(255) NOT NULL,
  storage_url TEXT NOT NULL,
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  title VARCHAR(255) NOT NULL,
  document_type VARCHAR(100) NOT NULL DEFAULT 'Unclassified',
  file_name VARCHAR(255) NOT NULL,
  file_type VARCHAR(50) NOT NULL,
  version VARCHAR(50) NOT NULL DEFAULT '',
  owner VARCHAR(255) NOT NULL DEFAULT 'Compliance Owner',
  review_date VARCHAR(50) NOT NULL DEFAULT '',
  status VARCHAR(100) NOT NULL DEFAULT 'Parsed',
  storage_path TEXT NOT NULL,
  extracted_text TEXT NOT NULL DEFAULT '',
  parsed_json TEXT NOT NULL DEFAULT '{}',
  uploaded_by VARCHAR(255) NOT NULL DEFAULT 'MVP User',
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS control_mappings (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id),
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  mapping_type VARCHAR(100) NOT NULL DEFAULT 'Referenced',
  confidence_score INTEGER NOT NULL DEFAULT 60,
  rationale TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS document_entities (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id),
  entity_type VARCHAR(100) NOT NULL,
  entity_value TEXT NOT NULL,
  source_excerpt TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS evidence_relationships (
  id SERIAL PRIMARY KEY,
  source_type VARCHAR(100) NOT NULL,
  source_id INTEGER NOT NULL,
  target_type VARCHAR(100) NOT NULL,
  target_id VARCHAR(100) NOT NULL,
  relationship_type VARCHAR(100) NOT NULL,
  notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS evidence (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  title VARCHAR(255) NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  file_type VARCHAR(50) NOT NULL,
  intended_control_id VARCHAR(50) NOT NULL DEFAULT '',
  storage_path TEXT NOT NULL,
  extracted_text TEXT NOT NULL DEFAULT '',
  evidence_type VARCHAR(100) NOT NULL DEFAULT 'Unclassified',
  owner VARCHAR(255) NOT NULL DEFAULT 'Compliance Owner',
  status VARCHAR(100) NOT NULL DEFAULT 'Analyzed',
  uploaded_by VARCHAR(255) NOT NULL DEFAULT 'MVP User',
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_analysis (
  id SERIAL PRIMARY KEY,
  evidence_id INTEGER NOT NULL REFERENCES evidence(id),
  control_id INTEGER NOT NULL REFERENCES cmmc_controls(id),
  confidence_score INTEGER NOT NULL DEFAULT 0,
  coverage_score INTEGER NOT NULL DEFAULT 0,
  assessment_strength VARCHAR(100) NOT NULL DEFAULT 'Needs Review',
  analysis_result TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_objectives (
  id SERIAL PRIMARY KEY,
  evidence_analysis_id INTEGER NOT NULL REFERENCES evidence_analysis(id),
  objective_id INTEGER NOT NULL REFERENCES assessment_objectives(id),
  supported VARCHAR(50) NOT NULL DEFAULT 'Not Supported',
  notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  action VARCHAR(255) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  entity_id VARCHAR(100) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
