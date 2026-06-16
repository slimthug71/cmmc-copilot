from .document_parser import parse_document


def parse_policy(file_name: str, text: str) -> dict[str, object]:
    result = parse_document(file_name, text, "Policy")
    result["policy_sections"] = [line.strip() for line in (text or "").splitlines() if "policy" in line.lower()][:20]
    return result

