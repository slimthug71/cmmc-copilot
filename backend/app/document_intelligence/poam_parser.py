from .document_parser import parse_document


def parse_poam(file_name: str, text: str) -> dict[str, object]:
    result = parse_document(file_name, text, "POA&M")
    result["poam_terms"] = [line.strip() for line in (text or "").splitlines() if any(term in line.lower() for term in ["open", "closed", "risk", "due", "owner", "finding"])][:50]
    return result
