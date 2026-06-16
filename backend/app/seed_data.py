CONTROL_ROWS = [
    ("AC.L2-3.1.1", "Access Control", "Authorized Access Control", "Limit system access to authorized users, processes acting on behalf of authorized users, and devices, including other systems."),
    ("AC.L2-3.1.2", "Access Control", "Transaction and Function Control", "Limit system access to the types of transactions and functions that authorized users are permitted to execute."),
    ("AC.L2-3.1.3", "Access Control", "Control CUI Flow", "Control the flow of CUI in accordance with approved authorizations."),
    ("AC.L2-3.1.4", "Access Control", "Separation of Duties", "Separate the duties of individuals to reduce the risk of malevolent activity without collusion."),
    ("AC.L2-3.1.5", "Access Control", "Least Privilege", "Employ the principle of least privilege, including for specific security functions and privileged accounts."),
    ("AC.L2-3.1.6", "Access Control", "Non-Privileged Account Use", "Use non-privileged accounts or roles when accessing nonsecurity functions."),
    ("AC.L2-3.1.7", "Access Control", "Privileged Functions", "Prevent non-privileged users from executing privileged functions and capture the execution of such functions in audit logs."),
    ("AC.L2-3.1.8", "Access Control", "Unsuccessful Logon Attempts", "Limit unsuccessful logon attempts."),
    ("AC.L2-3.1.9", "Access Control", "Privacy and Security Notices", "Provide privacy and security notices consistent with applicable CUI rules."),
    ("AC.L2-3.1.10", "Access Control", "Session Lock", "Use session lock with pattern-hiding displays to prevent access and viewing of data after a period of inactivity."),
    ("AC.L2-3.1.11", "Access Control", "Session Termination", "Terminate user sessions automatically after a defined condition."),
    ("AC.L2-3.1.12", "Access Control", "Remote Access Control", "Monitor and control remote access sessions."),
    ("AC.L2-3.1.13", "Access Control", "Remote Access Confidentiality", "Employ cryptographic mechanisms to protect the confidentiality of remote access sessions."),
    ("AC.L2-3.1.14", "Access Control", "Remote Access Routing", "Route remote access via managed access control points."),
    ("AC.L2-3.1.15", "Access Control", "Privileged Remote Access", "Authorize remote execution of privileged commands and remote access to security-relevant information."),
    ("AC.L2-3.1.16", "Access Control", "Wireless Access Authorization", "Authorize wireless access prior to allowing such connections."),
    ("AC.L2-3.1.17", "Access Control", "Wireless Access Protection", "Protect wireless access using authentication and encryption."),
    ("AC.L2-3.1.18", "Access Control", "Mobile Device Connection", "Control connection of mobile devices."),
    ("AC.L2-3.1.19", "Access Control", "Encrypt CUI on Mobile Devices", "Encrypt CUI on mobile devices and mobile computing platforms."),
    ("AC.L2-3.1.20", "Access Control", "External System Connections", "Verify and control or limit connections to and use of external systems."),
    ("AC.L2-3.1.21", "Access Control", "Portable Storage Use", "Limit use of portable storage devices on external systems."),
    ("AC.L2-3.1.22", "Access Control", "Control Public Information", "Control CUI posted or processed on publicly accessible systems."),
    ("AT.L2-3.2.1", "Awareness and Training", "Security Literacy", "Ensure personnel are aware of security risks associated with their activities and of applicable policies, standards, and procedures."),
    ("AT.L2-3.2.2", "Awareness and Training", "Role-Based Training", "Ensure personnel are trained to carry out assigned information security-related duties and responsibilities."),
    ("AT.L2-3.2.3", "Awareness and Training", "Insider Threat Awareness", "Provide security awareness training on recognizing and reporting potential indicators of insider threat."),
    ("AU.L2-3.3.1", "Audit and Accountability", "System Auditing", "Create and retain system audit logs and records to enable monitoring, analysis, investigation, and reporting of unlawful or unauthorized activity."),
    ("AU.L2-3.3.2", "Audit and Accountability", "User Accountability", "Ensure actions of individual system users can be uniquely traced to those users."),
    ("AU.L2-3.3.3", "Audit and Accountability", "Event Review", "Review and update logged events."),
    ("AU.L2-3.3.4", "Audit and Accountability", "Audit Failure Alerting", "Alert in the event of an audit logging process failure."),
    ("AU.L2-3.3.5", "Audit and Accountability", "Audit Correlation", "Correlate audit record review, analysis, and reporting processes for investigation and response."),
    ("AU.L2-3.3.6", "Audit and Accountability", "Reduction and Reporting", "Provide audit record reduction and report generation to support analysis and reporting."),
    ("AU.L2-3.3.7", "Audit and Accountability", "Authoritative Time Source", "Provide a system capability that compares and synchronizes internal clocks with an authoritative source."),
    ("AU.L2-3.3.8", "Audit and Accountability", "Audit Protection", "Protect audit information and logging tools from unauthorized access, modification, and deletion."),
    ("AU.L2-3.3.9", "Audit and Accountability", "Audit Management", "Limit management of audit logging functionality to a subset of privileged users."),
    ("CM.L2-3.4.1", "Configuration Management", "Baseline Configuration", "Establish and maintain baseline configurations and inventories of organizational systems."),
    ("CM.L2-3.4.2", "Configuration Management", "Security Configuration Enforcement", "Establish and enforce security configuration settings for information technology products."),
    ("CM.L2-3.4.3", "Configuration Management", "System Change Management", "Track, review, approve or disapprove, and log changes to organizational systems."),
    ("CM.L2-3.4.4", "Configuration Management", "Security Impact Analysis", "Analyze the security impact of changes prior to implementation."),
    ("CM.L2-3.4.5", "Configuration Management", "Access Restrictions for Change", "Define, document, approve, and enforce physical and logical access restrictions associated with changes."),
    ("CM.L2-3.4.6", "Configuration Management", "Least Functionality", "Employ the principle of least functionality by configuring systems to provide only essential capabilities."),
    ("CM.L2-3.4.7", "Configuration Management", "Nonessential Functionality", "Restrict, disable, or prevent use of nonessential programs, functions, ports, protocols, and services."),
    ("CM.L2-3.4.8", "Configuration Management", "Application Execution Policy", "Apply deny-by-exception policy to prevent unauthorized software execution."),
    ("CM.L2-3.4.9", "Configuration Management", "User-Installed Software", "Control and monitor user-installed software."),
    ("IA.L2-3.5.1", "Identification and Authentication", "Identify Users", "Identify system users, processes acting on behalf of users, and devices."),
    ("IA.L2-3.5.2", "Identification and Authentication", "Authenticate Users", "Authenticate or verify identities of users, processes, and devices as a prerequisite to system access."),
    ("IA.L2-3.5.3", "Identification and Authentication", "Multifactor Authentication", "Use multifactor authentication for local and network access to privileged accounts and for network access to non-privileged accounts."),
    ("IA.L2-3.5.4", "Identification and Authentication", "Replay-Resistant Authentication", "Employ replay-resistant authentication mechanisms for network access to privileged and non-privileged accounts."),
    ("IA.L2-3.5.5", "Identification and Authentication", "Identifier Reuse", "Prevent reuse of identifiers for a defined period."),
    ("IA.L2-3.5.6", "Identification and Authentication", "Identifier Disablement", "Disable identifiers after a defined period of inactivity."),
    ("IA.L2-3.5.7", "Identification and Authentication", "Password Complexity", "Enforce minimum password complexity and change of characters when new passwords are created."),
    ("IA.L2-3.5.8", "Identification and Authentication", "Password Reuse", "Prohibit password reuse for a specified number of generations."),
    ("IA.L2-3.5.9", "Identification and Authentication", "Temporary Passwords", "Allow temporary password use for system logons with immediate change to a permanent password."),
    ("IA.L2-3.5.10", "Identification and Authentication", "Cryptographic Password Storage", "Store and transmit only cryptographically protected passwords."),
    ("IA.L2-3.5.11", "Identification and Authentication", "Obscure Feedback", "Obscure feedback of authentication information."),
    ("IR.L2-3.6.1", "Incident Response", "Incident Handling", "Establish an operational incident-handling capability for organizational systems."),
    ("IR.L2-3.6.2", "Incident Response", "Incident Reporting", "Track, document, and report incidents to designated officials and authorities."),
    ("IR.L2-3.6.3", "Incident Response", "Incident Response Testing", "Test the organizational incident response capability."),
    ("MA.L2-3.7.1", "Maintenance", "Perform Maintenance", "Perform maintenance on organizational systems."),
    ("MA.L2-3.7.2", "Maintenance", "System Maintenance Control", "Provide controls on tools, techniques, mechanisms, and personnel used to conduct system maintenance."),
    ("MA.L2-3.7.3", "Maintenance", "Equipment Sanitization", "Ensure equipment removed for off-site maintenance is sanitized of CUI."),
    ("MA.L2-3.7.4", "Maintenance", "Media Inspection", "Check media containing diagnostic and test programs for malicious code before use."),
    ("MA.L2-3.7.5", "Maintenance", "Nonlocal Maintenance", "Require multifactor authentication for nonlocal maintenance sessions and terminate connections when complete."),
    ("MA.L2-3.7.6", "Maintenance", "Maintenance Personnel", "Supervise maintenance activities of personnel without required access authorization."),
    ("MP.L2-3.8.1", "Media Protection", "Media Protection", "Protect system media containing CUI, both paper and digital."),
    ("MP.L2-3.8.2", "Media Protection", "Media Access", "Limit access to CUI on system media to authorized users."),
    ("MP.L2-3.8.3", "Media Protection", "Media Sanitization", "Sanitize or destroy system media containing CUI before disposal or release for reuse."),
    ("MP.L2-3.8.4", "Media Protection", "Media Markings", "Mark media with necessary CUI markings and distribution limitations."),
    ("MP.L2-3.8.5", "Media Protection", "Media Accountability", "Control access to media containing CUI and maintain accountability for media during transport."),
    ("MP.L2-3.8.6", "Media Protection", "Portable Storage Encryption", "Implement cryptographic mechanisms to protect CUI stored on digital media during transport."),
    ("MP.L2-3.8.7", "Media Protection", "Removable Media", "Control use of removable media on system components."),
    ("MP.L2-3.8.8", "Media Protection", "Shared Media", "Prohibit use of portable storage devices when such devices have no identifiable owner."),
    ("MP.L2-3.8.9", "Media Protection", "Protect Backups", "Protect the confidentiality of backup CUI at storage locations."),
    ("PE.L2-3.10.1", "Physical Protection", "Physical Access Authorization", "Limit physical access to organizational systems, equipment, and operating environments to authorized individuals."),
    ("PE.L2-3.10.2", "Physical Protection", "Monitor Facility", "Protect and monitor the physical facility and support infrastructure."),
    ("PE.L2-3.10.3", "Physical Protection", "Escort Visitors", "Escort visitors and monitor visitor activity."),
    ("PE.L2-3.10.4", "Physical Protection", "Physical Access Logs", "Maintain audit logs of physical access."),
    ("PE.L2-3.10.5", "Physical Protection", "Manage Physical Access Devices", "Control and manage physical access devices."),
    ("PE.L2-3.10.6", "Physical Protection", "Alternate Work Sites", "Enforce safeguarding measures for CUI at alternate work sites."),
    ("PS.L2-3.9.1", "Personnel Security", "Screen Individuals", "Screen individuals prior to authorizing access to organizational systems containing CUI."),
    ("PS.L2-3.9.2", "Personnel Security", "Personnel Actions", "Ensure CUI and systems are protected during and after personnel actions such as terminations and transfers."),
    ("RA.L2-3.11.1", "Risk Assessment", "Risk Assessments", "Periodically assess risk to organizational operations, assets, and individuals from system operation and CUI processing."),
    ("RA.L2-3.11.2", "Risk Assessment", "Vulnerability Scanning", "Scan for vulnerabilities in organizational systems and applications periodically and when new vulnerabilities are identified."),
    ("RA.L2-3.11.3", "Risk Assessment", "Vulnerability Remediation", "Remediate vulnerabilities in accordance with risk assessments."),
    ("CA.L2-3.12.1", "Security Assessment", "Security Control Assessment", "Periodically assess security controls to determine effectiveness."),
    ("CA.L2-3.12.2", "Security Assessment", "Plan of Action", "Develop and implement plans of action to correct deficiencies and reduce or eliminate vulnerabilities."),
    ("CA.L2-3.12.3", "Security Assessment", "Control Monitoring", "Monitor security controls on an ongoing basis to ensure continued effectiveness."),
    ("CA.L2-3.12.4", "Security Assessment", "System Security Plan", "Develop, document, and periodically update system security plans."),
    ("SC.L2-3.13.1", "System and Communications Protection", "Boundary Protection", "Monitor, control, and protect communications at external boundaries and key internal boundaries."),
    ("SC.L2-3.13.2", "System and Communications Protection", "Security Engineering", "Employ architectural designs, software development techniques, and systems engineering principles that promote effective information security."),
    ("SC.L2-3.13.3", "System and Communications Protection", "Role Separation", "Separate user functionality from system management functionality."),
    ("SC.L2-3.13.4", "System and Communications Protection", "Shared Resource Control", "Prevent unauthorized and unintended information transfer via shared system resources."),
    ("SC.L2-3.13.5", "System and Communications Protection", "Public Access System Separation", "Implement subnetworks for publicly accessible system components that are physically or logically separated from internal networks."),
    ("SC.L2-3.13.6", "System and Communications Protection", "Network Communication Deny", "Deny network communications traffic by default and allow by exception."),
    ("SC.L2-3.13.7", "System and Communications Protection", "Split Tunneling", "Prevent remote devices from simultaneously establishing non-remote connections with organizational systems and external networks."),
    ("SC.L2-3.13.8", "System and Communications Protection", "Data in Transit", "Implement cryptographic mechanisms to prevent unauthorized disclosure of CUI during transmission."),
    ("SC.L2-3.13.9", "System and Communications Protection", "Connection Termination", "Terminate network connections associated with communications sessions at session end or after inactivity."),
    ("SC.L2-3.13.10", "System and Communications Protection", "Key Management", "Establish and manage cryptographic keys when cryptography is employed."),
    ("SC.L2-3.13.11", "System and Communications Protection", "FIPS-Validated Cryptography", "Employ FIPS-validated cryptography when used to protect the confidentiality of CUI."),
    ("SC.L2-3.13.12", "System and Communications Protection", "Collaborative Device Control", "Prohibit remote activation of collaborative computing devices and provide indication of use."),
    ("SC.L2-3.13.13", "System and Communications Protection", "Mobile Code", "Control and monitor use of mobile code."),
    ("SC.L2-3.13.14", "System and Communications Protection", "VoIP", "Control and monitor use of Voice over Internet Protocol technologies."),
    ("SC.L2-3.13.15", "System and Communications Protection", "Communications Authenticity", "Protect authenticity of communications sessions."),
    ("SC.L2-3.13.16", "System and Communications Protection", "Data at Rest", "Protect confidentiality of CUI at rest."),
    ("SI.L2-3.14.1", "System and Information Integrity", "Flaw Remediation", "Identify, report, and correct system flaws in a timely manner."),
    ("SI.L2-3.14.2", "System and Information Integrity", "Malicious Code Protection", "Provide protection from malicious code at designated locations."),
    ("SI.L2-3.14.3", "System and Information Integrity", "Monitor Security Alerts", "Monitor security alerts and advisories and take appropriate actions."),
    ("SI.L2-3.14.4", "System and Information Integrity", "Update Malicious Code Protection", "Update malicious code protection mechanisms when new releases are available."),
    ("SI.L2-3.14.5", "System and Information Integrity", "System and File Scanning", "Perform periodic scans and real-time scans of files from external sources."),
    ("SI.L2-3.14.6", "System and Information Integrity", "Monitor Communications", "Monitor organizational systems including inbound and outbound communications traffic."),
    ("SI.L2-3.14.7", "System and Information Integrity", "Identify Unauthorized Use", "Identify unauthorized use of organizational systems."),
]


DEFAULT_OBJECTIVES = [
    ("a", "Authorized users are identified."),
    ("b", "Processes acting on behalf of authorized users are identified."),
    ("c", "Devices and other systems authorized to connect are identified."),
    ("d", "System access is limited to authorized users, processes, and devices."),
]


OBJECTIVE_FAMILY_TARGETS = {
    "Access Control": 64,
    "Awareness and Training": 8,
    "Audit and Accountability": 25,
    "Configuration Management": 26,
    "Identification and Authentication": 32,
    "Incident Response": 9,
    "Maintenance": 16,
    "Media Protection": 25,
    "Physical Protection": 17,
    "Personnel Security": 6,
    "Risk Assessment": 9,
    "Security Assessment": 12,
    "System and Communications Protection": 50,
    "System and Information Integrity": 21,
}


OBJECTIVE_OVERRIDES = {
    "AC.L2-3.1.1": DEFAULT_OBJECTIVES,
    "AC.L2-3.1.2": [
        ("a", "The types of transactions and functions that authorized users are permitted to execute are defined."),
        ("b", "System access is limited to the defined transactions and functions for authorized users."),
    ],
    "IA.L2-3.5.1": [
        ("a", "System users are identified."),
        ("b", "Processes acting on behalf of users are identified."),
        ("c", "Devices accessing the system are identified."),
    ],
    "IA.L2-3.5.2": [
        ("a", "The identities of system users are authenticated or verified before system access is granted."),
        ("b", "The identities of processes acting on behalf of users are authenticated or verified before system access is granted."),
        ("c", "The identities of devices accessing the system are authenticated or verified before system access is granted."),
    ],
    "IA.L2-3.5.3": [
        ("a", "Multifactor authentication is used for local access to privileged accounts."),
        ("b", "Multifactor authentication is used for network access to privileged accounts."),
        ("c", "Multifactor authentication is used for network access to non-privileged accounts."),
    ],
    "SC.L2-3.13.11": [
        ("a", "FIPS-validated cryptography is employed to protect the confidentiality of CUI when cryptography is used."),
        ("b", "Cryptographic modules and services used for CUI protection are identified and documented."),
        ("c", "Evidence of FIPS validation is retained for cryptographic products and services used to protect CUI confidentiality."),
    ],
}


def _split_requirement(requirement: str) -> list[str]:
    cleaned = requirement.strip().rstrip(".")
    fragments = [cleaned]
    for separator in ["; ", ", including ", ", and ", " and "]:
        fragments = [part for fragment in fragments for part in fragment.split(separator)]
    return [fragment.strip(" ,.;") for fragment in fragments if len(fragment.strip(" ,.;")) > 8]


def _objective_count_by_control() -> dict[str, int]:
    counts: dict[str, int] = {}
    by_family: dict[str, list[str]] = {}
    for control_id, family, _title, _requirement in CONTROL_ROWS:
        by_family.setdefault(family, []).append(control_id)
    for family, control_ids in by_family.items():
        target = OBJECTIVE_FAMILY_TARGETS[family]
        base = target // len(control_ids)
        remainder = target % len(control_ids)
        for index, control_id in enumerate(control_ids):
            counts[control_id] = base + (1 if index < remainder else 0)
    return counts


def build_assessment_objectives() -> dict[str, list[tuple[str, str]]]:
    counts = _objective_count_by_control()
    objectives: dict[str, list[tuple[str, str]]] = {}
    label_names = "abcdefghijklmnopqrstuvwxyz"
    for control_id, family, title, requirement in CONTROL_ROWS:
        if control_id in OBJECTIVE_OVERRIDES:
            objectives[control_id] = OBJECTIVE_OVERRIDES[control_id]
            continue
        target = counts[control_id]
        fragments = _split_requirement(requirement)
        statements = [fragment[0].upper() + fragment[1:] + "." for fragment in fragments[:target]]
        fallbacks = [
            f"{title} is defined for the in-scope CUI environment.",
            f"{title} is implemented using approved organizational processes and assigned responsible parties.",
            f"{title} implementation records are retained as assessment evidence.",
            f"{title} is reviewed at the frequency required by the {family} program.",
        ]
        for fallback in fallbacks:
            if len(statements) >= target:
                break
            statements.append(fallback)
        objectives[control_id] = [(label_names[index], statement) for index, statement in enumerate(statements[:target])]
    return objectives


ASSESSMENT_OBJECTIVES = build_assessment_objectives()


DEFAULT_EVIDENCE = [
    "Access control policy and account management procedures",
    "System security plan and CUI boundary description",
    "Current user and privileged account listings",
    "Access authorization records and approval tickets",
    "Recent access review evidence",
    "Audit logs or monitoring records showing access enforcement",
]
