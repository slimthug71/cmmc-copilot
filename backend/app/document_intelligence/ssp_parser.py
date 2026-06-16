from .document_parser import first_match, parse_document


def parse_ssp(file_name: str, text: str) -> dict[str, object]:
    result = parse_document(file_name, text, "SSP")
    result["system_boundary"] = first_match([r"(?:System Boundary|Boundary Description)[:\s]+(.{20,700})"], text)
    result["cui_environment"] = first_match([r"(?:CUI Environment|CUI Description|CUI Assets?)[:\s]+(.{10,500})"], text)
    result["external_providers"] = first_match([r"(?:External (?:Service )?Providers?|MSP|MSSP)[:\s]+(.{5,400})"], text)
    return result

