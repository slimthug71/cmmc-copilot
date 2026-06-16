import re
from pathlib import Path


CONTROL_PATTERN = re.compile(r"\b[A-Z]{2}\.L2-\d\.\d+\.\d+\b", re.IGNORECASE)


def extract_controls(text: str) -> list[str]:
    return sorted({match.upper() for match in CONTROL_PATTERN.findall(text or "")})


def first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text or "", flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def detect_document_type(file_name: str, text: str) -> str:
    haystack = f"{file_name} {text}".lower()
    if "system security plan" in haystack or "ssp" in Path(file_name).stem.lower():
        return "SSP"
    if "poa&m" in haystack or "poam" in haystack or "plan of action" in haystack:
        return "POA&M"
    if "procedure" in haystack:
        return "Procedure"
    if "policy" in haystack:
        return "Policy"
    return "Compliance Document"


def parse_document(file_name: str, text: str, document_type: str = "") -> dict[str, object]:
    resolved_type = document_type or detect_document_type(file_name, text)
    return {
        "document_type": resolved_type,
        "document_name": first_match([r"^(.*?(?:Policy|Procedure|Plan|SSP|System Security Plan).*)$", r"^Title[:\s]+(.+)$"], text) or Path(file_name).stem.replace("_", " "),
        "version": first_match([r"\bVersion[:\s]+([A-Za-z0-9.\-]+)", r"\bRev(?:ision)?[:\s]+([A-Za-z0-9.\-]+)"], text),
        "owners": extract_owners(text),
        "review_dates": extract_review_dates(text),
        "controls": extract_controls(text),
        "evidence_references": extract_evidence_references(text),
    }


def extract_owners(text: str) -> list[str]:
    owners = []
    for pattern in [r"\bOwner[:\s]+(.+)", r"\bDocument Owner[:\s]+(.+)", r"\bSystem Owner[:\s]+(.+)"]:
        owners.extend(match.strip() for match in re.findall(pattern, text or "", flags=re.IGNORECASE))
    return list(dict.fromkeys(owner[:255] for owner in owners if owner.strip()))


def extract_review_dates(text: str) -> list[str]:
    dates = []
    for pattern in [r"\bReview Date[:\s]+([A-Za-z0-9,./\- ]+)", r"\bLast Reviewed[:\s]+([A-Za-z0-9,./\- ]+)"]:
        dates.extend(match.strip() for match in re.findall(pattern, text or "", flags=re.IGNORECASE))
    return list(dict.fromkeys(date[:80] for date in dates if date.strip()))


def extract_evidence_references(text: str) -> list[str]:
    references = []
    for line in (text or "").splitlines():
        lowered = line.lower()
        if any(keyword in lowered for keyword in ["evidence", "artifact", "record", "report", "export", "screenshot", "ticket"]):
            references.append(re.sub(r"\s+", " ", line).strip()[:300])
    return references[:40]

