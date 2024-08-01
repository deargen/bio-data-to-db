def uniprot_xml_to_postgresql(
    *,
    uniprot_xml_path: str,
    uri: str,
) -> None:
    """
    (🦀 Rust) Load UniProt XML file into PostgreSQL database.

    This creates a `uniprot` database and a `uniprot_info` table.
    """
