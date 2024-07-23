import logging
from os import PathLike

import polars as pl
import psycopg

from bio_data_to_db.utils.postgresql import (
    create_db_if_not_exists,
    create_schema_if_not_exists,
    polars_write_database,
)

logger = logging.getLogger(__name__)


def create_empty_table(
    uri: str,
):
    uri_wo_dbname, dbname = uri.rsplit("/", 1)
    create_db_if_not_exists(uri_wo_dbname, dbname)
    create_schema_if_not_exists(uri, "public")

    with psycopg.connect(
        conninfo=uri,
    ) as conn:
        try:
            cursor = conn.cursor()
            conn.autocommit = True
            cursor.execute(
                query="""
                CREATE TABLE public.uniprot_info (
                  uniprot_pk_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                  accessions TEXT[],
                  names TEXT[],
                  protein_names TEXT[],
                  gene_names TEXT[],
                  organism_scientific TEXT,
                  organism_commons TEXT[],
                  organism_synonyms TEXT[],
                  ncbi_taxonomy_id INT,
                  deargen_ncbi_taxonomy_id INT,
                  lineage TEXT[],
                  keywords TEXT[],
                  geneontology_ids TEXT[],
                  geneontology_names TEXT[],
                  sequence TEXT,
                  deargen_molecular_functions TEXT[]
                )
            """
            )
            logger.info(f"Database '{dbname}.public.uniprot_info' created successfully")

        except psycopg.Error:
            logger.exception(f"Error creating database '{dbname}.public.uniprot_info'")


def create_accession_to_pk_id(uri: str):
    with psycopg.connect(
        conninfo=uri,
    ) as conn:
        try:
            cursor = conn.cursor()
            conn.autocommit = True
            cursor.execute(
                query="""
                CREATE TABLE public.accession_to_pk_id (
                  accession TEXT,
                  uniprot_pk_id BIGINT
                )
            """
            )
            logger.info(
                "Table structure 'uniprot.public.accession_to_pk_id' created successfully"
            )

            cursor.execute(
                query="""
                INSERT INTO public.accession_to_pk_id (accession, uniprot_pk_id)
                SELECT UNNEST(accessions), uniprot_pk_id
                FROM public.uniprot_info
            """
            )
            logger.info(
                "Table 'uniprot.public.accession_to_pk_id' insert content successfully"
            )

            cursor.execute(
                query="""
                CREATE TABLE public.accession_to_pk_id_list (
                  accession TEXT PRIMARY KEY,
                  uniprot_pk_ids BIGINT[]
                )
            """
            )
            logger.info(
                "Table structure 'uniprot.public.accession_to_pk_id_list' created successfully"
            )

            cursor.execute(
                query="""
                INSERT INTO public.accession_to_pk_id_list (accession, uniprot_pk_ids)
                SELECT accession, ARRAY_AGG(uniprot_pk_id) AS uniprot_pk_ids
                FROM public.accession_to_pk_id
                GROUP BY accession;
            """
            )
            logger.info(
                "Table 'uniprot.public.accession_to_pk_id_list' content added successfully"
            )

        except psycopg.Error:
            logger.exception("Error creating table 'uniprot.public.accession_to_pk_id'")


def keywords_tsv_to_postgresql(
    keywords_tsv_file: str | PathLike,
    uri: str,
    schema_name="public",
    table_name="keywords",
):
    tsv_columns = [
        "Keyword ID",
        "Name",
        "Category",
        "Gene Ontologies",
    ]
    polars_columns = [
        "keyword_id",
        "name",
        "category",
        "geneontology_names",
    ]
    rename_dict = dict(zip(tsv_columns, polars_columns, strict=True))
    polars_dtypes = [
        pl.Utf8,
        pl.Utf8,
        pl.Utf8,
        pl.Utf8,
    ]

    df = pl.read_csv(
        str(keywords_tsv_file),
        separator="\t",
        columns=tsv_columns,
        # NOTE: Do not use new_columns with columns. It will result in wrong data.
        # new_columns=polars_columns,
        schema_overrides=polars_dtypes,
    )

    df = df.rename(rename_dict)

    # geneontology_names is a list of strings
    df = df.with_columns(
        geneontology_names=pl.col("geneontology_names")
        .str.split(", ")
        .cast(pl.List(pl.Utf8))
    )

    polars_write_database(df, schema_name=schema_name, table_name=table_name, uri=uri)
