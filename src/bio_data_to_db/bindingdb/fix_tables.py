import html

import polars as pl
import sqlalchemy


def fix_assay_table(uri: str):
    """
    Fix the assay table in MySQL by decoding HTML entities like '&#39;' and strip empty spaces.

    Notes:
        - original types are VARCHAR but we are converting them to TEXT. The code should work for both cases.
        - the table is replaced.
        - primary key and foreign key constraints are reserved by manually adding them back just like the original table
    """
    query = """
        SELECT
          *
        FROM
          assay
    """
    assay_df = pl.read_database_uri(query=query, uri=uri)

    # the column might be "binary" type
    assay_df = assay_df.with_columns(
        pl.col("description")
        .cast(pl.Utf8)
        .map_elements(lambda s: html.unescape(s.strip()), return_dtype=pl.Utf8),
        pl.col("assay_name")
        .cast(pl.Utf8)
        .map_elements(lambda s: html.unescape(s.strip()), return_dtype=pl.Utf8),
    )

    assay_df.write_database(
        table_name="assay",
        connection=uri,
        if_table_exists="replace",
    )

    with sqlalchemy.create_engine(uri).connect() as conn:
        conn.execute(
            sqlalchemy.text("""
                ALTER TABLE assay MODIFY COLUMN `entryid` INT(11);
                ALTER TABLE assay MODIFY COLUMN `assayid` INT(11);
                ALTER TABLE assay ADD PRIMARY KEY (`entryid`,`assayid`);
                ALTER TABLE assay ADD CONSTRAINT `assay_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`);
            """)
        )


# if __name__ == "__main__":
#     fix_assay_table("mysql://username:@localhost:3306/bind")
