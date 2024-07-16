from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


@app.command(no_args_is_help=True)
def create_empty_table(
    uri: Annotated[
        str,
        typer.Argument(help="URI to the PostgreSQL database"),
    ],
):
    from bio_data_to_db.uniprot import create_empty_table
    from bio_data_to_db.utils.log import setup_logging

    setup_logging()
    create_empty_table(uri)


@app.command(no_args_is_help=True)
def xml_to_postgresql(
    uniprot_xml_file: Annotated[
        str, typer.Argument(help="Path to the UniProt XML file")
    ],
    uri: Annotated[str, typer.Argument(help="URI to the PostgreSQL database")],
):
    """
    Convert a UniProt XML file to a PostgreSQL database.

    You must first create the table using the `create_empty_table` command.
    """
    from bio_data_to_db.uniprot import uniprot_xml_to_postgresql
    from bio_data_to_db.utils.log import setup_logging

    setup_logging()
    uniprot_xml_to_postgresql(uniprot_xml_path=uniprot_xml_file, uri=uri)


@app.command(no_args_is_help=True)
def create_accession_to_pk_id(
    uri: Annotated[
        str,
        typer.Argument(help="URI to the PostgreSQL database"),
    ],
):
    """
    Create a dictionary mapping UniProt accession numbers to primary key IDs.

    Note that it is not unique, as the same accession number can be associated with multiple primary key IDs.
    """
    from bio_data_to_db.uniprot import create_accession_to_pk_id
    from bio_data_to_db.utils.log import setup_logging

    setup_logging()
    create_accession_to_pk_id(uri)


@app.command(no_args_is_help=True)
def keywords_tsv_to_postgresql(
    keywords_tsv_file: Annotated[
        str, typer.Argument(help="Path to the UniProt keywords TSV file")
    ],
    uri: Annotated[
        str,
        typer.Argument(help="URI to the PostgreSQL database"),
    ],
):
    """
    Convert a UniProt keywords TSV file to a PostgreSQL database.
    """
    from bio_data_to_db.uniprot import keywords_tsv_to_postgresql
    from bio_data_to_db.utils.log import setup_logging

    setup_logging()
    keywords_tsv_to_postgresql(keywords_tsv_file=keywords_tsv_file, uri=uri)


def main():
    app()


if __name__ == "__main__":
    main()
