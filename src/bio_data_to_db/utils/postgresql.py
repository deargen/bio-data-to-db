import logging
from collections.abc import Sequence

import polars as pl
import psycopg
from polars._typing import DbWriteMode
from psycopg import sql
from sqlalchemy import Engine, create_engine, types

logger = logging.getLogger(__name__)


# def polars_datatype_to_postgresql_type(dtype: pl.datatypes.DataType) -> str:
#     match dtype:
#         case pl.Utf8:
#             pg_element_type = "text"
#         case pl.UInt64:
#             # WARN: ignore unsigned because PostgreSQL doesn't support unsigned
#             pg_element_type = "bigint"
#         case pl.Int64:
#             pg_element_type = "bigint"
#         case pl.Int32:
#             pg_element_type = "integer"
#         case pl.Int16:
#             pg_element_type = "smallint"
#         case pl.Float64:
#             pg_element_type = "double precision"
#         case pl.Float32:
#             pg_element_type = "real"
#         case _:
#             raise ValueError(f"Unsupported inner dtype: {dtype}")
#
#     return pg_element_type


def polars_datatype_to_sqlalchemy_type(
    dtype: pl.datatypes.DataType,
) -> types.TypeEngine:
    match dtype:
        case pl.Utf8:
            sqlalchemy_type = types.TEXT()
        case pl.UInt64:
            # WARN: ignore unsigned because PostgreSQL doesn't support unsigned. Possible loss of data
            sqlalchemy_type = types.BIGINT()
        case pl.Int64:
            sqlalchemy_type = types.BIGINT()
        case pl.UInt32:
            sqlalchemy_type = types.BIGINT()
        case pl.Int32:
            sqlalchemy_type = types.INTEGER()
        case pl.UInt16:
            sqlalchemy_type = types.INTEGER()
        case pl.Int16:
            sqlalchemy_type = types.SMALLINT()
        case pl.Float64:
            sqlalchemy_type = types.DOUBLE_PRECISION()
        case pl.Float32:
            sqlalchemy_type = types.REAL()
        case pl.Boolean:
            sqlalchemy_type = types.BOOLEAN()
        case pl.List:
            inner_dtype = dtype.inner
            assert inner_dtype is not None
            inner_sqlalchemy_type = polars_datatype_to_sqlalchemy_type(inner_dtype)
            sqlalchemy_type = types.ARRAY(inner_sqlalchemy_type)
        case _:
            raise ValueError(f"Unsupported dtype: {dtype}")

    return sqlalchemy_type


def create_db_if_not_exists(uri_wo_db: str, db_name: str, comment: str | None = None):
    """
    Create a database if it doesn't exist.
    """
    with psycopg.connect(
        conninfo=f"{uri_wo_db}",
    ) as conn:
        try:
            cursor = conn.cursor()
            conn.autocommit = True
            cursor.execute(
                query=sql.SQL("""CREATE DATABASE {db_name};""").format(
                    db_name=sql.Identifier(db_name)
                )
            )
            if comment is not None:
                cursor.execute(
                    query=sql.SQL(
                        """COMMENT ON DATABASE {db_name} IS {comment};"""
                    ).format(
                        db_name=sql.Identifier(db_name),
                        comment=sql.Literal(comment),
                    )
                )
            logger.info(f"Database '{db_name}' created successfully")
        except psycopg.errors.DuplicateDatabase:
            logger.info(f"Database '{db_name}' already exists, Skip creating database.")
            if comment is not None:
                conn.rollback()
                cursor = conn.cursor()
                cursor.execute(
                    query=sql.SQL(
                        """COMMENT ON DATABASE {db_name} IS {comment};"""
                    ).format(
                        db_name=sql.Identifier(db_name),
                        comment=sql.Literal(comment),
                    )
                )

        except psycopg.Error:
            logger.exception(f"Error creating database '{db_name}'")


def create_schema_if_not_exists(uri: str, schema_name: str, comment: str | None = None):
    """
    Create a schema if it doesn't exist. The DB should already exist.
    """
    db_name = uri.split("/")[-1]
    with psycopg.connect(
        conninfo=uri,
    ) as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                query=sql.SQL("""CREATE SCHEMA {schema_name};""").format(
                    schema_name=sql.Identifier(schema_name)
                )
            )
            if comment is not None:
                cursor.execute(
                    query=sql.SQL(
                        """COMMENT ON SCHEMA {schema_name} IS {comment};"""
                    ).format(
                        schema_name=sql.Identifier(schema_name),
                        comment=sql.Literal(comment),
                    )
                )
            conn.commit()

            logger.info(
                f"Schema '{schema_name}' created successfully in DB '{db_name}'"
            )
        except psycopg.errors.DuplicateSchema:
            logger.info(
                f"Schema '{schema_name}' in DB '{db_name}' already exists, Skip creating schema."
            )
            if comment is not None:
                # cancel the transaction and try to add comment
                conn.rollback()
                cursor = conn.cursor()
                cursor.execute(
                    query=sql.SQL(
                        """COMMENT ON SCHEMA {schema_name} IS {comment};"""
                    ).format(
                        schema_name=sql.Identifier(schema_name),
                        comment=sql.Literal(comment),
                    )
                )
                conn.commit()
        except psycopg.Error:
            logger.exception(f"Error creating schema '{schema_name}' in DB '{db_name}'")


def make_int_column_primary_key_identity(
    uri: str,
    *,
    schema_name: str = "public",
    table_name: str,
    column_name: str = "index",
):
    """
    Make an existing index column (integer type) as primary key with auto increment (identity).

    This is used because pl.DataFrame.write_database() doesn't support writing index column as primary key.
    Also, it will automatically set the start value of auto increment to the max value in the column.

    Example:
        >>> df = pl.DataFrame({"smiles": ["CCO", "CCN", "CCC"]})  # doctest: +SKIP
        ... df = df.with_row_index("pk_id")
        ... df.write_database(...)
        ... set_column_as_primary_key(uri=uri, table_name="table", column_name="pk_id")
        ... df2 = pl.DataFrame({"smiles": ["CCC", "CCN", "CCO"]})  # append without pk_id
        ... df2.write_database(..., if_table_exists="append")  # it will auto increment pk_id
    """
    with psycopg.connect(
        conninfo=uri,
    ) as conn:
        try:
            cursor = conn.cursor()
            # NOTE: since there are already values in the column, we need to set the start value to max+1

            cursor.execute(
                sql.SQL("""
            SELECT MAX({column}) FROM {table}
            """).format(
                    column=sql.Identifier(column_name),
                    table=sql.Identifier(schema_name, table_name),
                )
            )
            max_id = cursor.fetchone()
            if max_id is None:
                logger.error(
                    f"Error setting primary key for column '{column_name}' in table '{table_name}': no max value found"
                )
                return

            max_id = max_id[0]

            cursor.execute(
                sql.SQL("""
            ALTER TABLE {table}
            ALTER COLUMN {column} SET NOT NULL,
            ALTER COLUMN {column} ADD GENERATED BY DEFAULT AS IDENTITY
              (START WITH {start_with}),
            ADD PRIMARY KEY ({column});
            """).format(
                    table=sql.Identifier(schema_name, table_name),
                    column=sql.Identifier(column_name),
                    start_with=sql.Literal(max_id + 1),
                )
            )
            conn.commit()

        except psycopg.Error:
            logger.exception(
                f"Error setting primary key for column '{column_name}' in table '{table_name}'"
            )


def make_columns_primary_key(
    uri: str,
    *,
    schema_name: str = "public",
    table_name: str,
    column_names: str | Sequence[str],
):
    """
    Make multiple columns as primary key but without auto increment (identity).

    This is similar to make_columns_unique() but with primary key constraint.
    """
    with psycopg.connect(
        conninfo=uri,
    ) as conn:
        try:
            cursor = conn.cursor()

            if isinstance(column_names, str):
                column_names = [column_names]

            cursor.execute(
                sql.SQL("""
                    ALTER TABLE {table}
                    ADD PRIMARY KEY ({columns});
                """).format(
                    table=sql.Identifier(schema_name, table_name),
                    columns=sql.SQL(",").join(
                        sql.Identifier(col) for col in column_names
                    ),
                )
            )
            conn.commit()

        except psycopg.Error:
            logger.exception(
                f"Error setting primary key for column '{column_names}' in table '{table_name}'"
            )


def make_columns_unique(
    uri: str,
    *,
    schema_name: str = "public",
    table_name: str,
    column_names: str | Sequence[str],
):
    """
    Set unique constraint on a column or columns in a table.

    If multiple columns are provided, the unique constraint will be on the combination of the columns.
    """
    with psycopg.connect(
        conninfo=uri,
    ) as conn:
        try:
            cursor = conn.cursor()

            if isinstance(column_names, str):
                column_names = [column_names]

            cursor.execute(
                query=sql.SQL("""
                    ALTER TABLE {table}
                    ADD CONSTRAINT {table_unique_constraint}
                      UNIQUE ({columns});
                """).format(
                    table=sql.Identifier(schema_name, table_name),
                    table_unique_constraint=sql.Identifier(
                        f"{schema_name}-{table_name}-{'-'.join(column_names)}-unique_constraint"
                    ),
                    columns=sql.SQL(",").join(
                        sql.Identifier(col) for col in column_names
                    ),
                )
            )
            conn.commit()

        except psycopg.Error:
            logger.exception(
                f"Error setting unique constraint for column '{column_names}' in table '{table_name}'"
            )


def make_large_columns_unique(
    uri: str,
    *,
    schema_name: str = "public",
    table_name: str,
    column_names: str | Sequence[str],
):
    """
    Use this when the values are large texts, e.g. fasta sequences.

    Reference:
        - https://stackoverflow.com/questions/71379137/how-to-solve-postgresql-index-width-problem
    """
    with psycopg.connect(
        conninfo=uri,
    ) as conn:
        try:
            cursor = conn.cursor()

            if isinstance(column_names, str):
                column_names = [column_names]

            cursor.execute(
                query=sql.SQL("""
                CREATE UNIQUE INDEX ON {table} (
                  {columns}
                );
                """).format(
                    table=sql.Identifier(schema_name, table_name),
                    columns=sql.SQL(",").join(
                        sql.SQL("md5(") + sql.Identifier(col) + sql.SQL(")")
                        for col in column_names
                    ),
                )
            )
            conn.commit()

        except psycopg.Error:
            logger.exception(
                f"Error setting unique index for column '{column_names}' in table '{table_name}'"
            )


def split_column_str_to_list(
    uri: str,
    *,
    schema_name: str = "public",
    table_name: str,
    in_column: str,
    out_column: str,
    separator: str,
    pg_element_type: str = "text",
):
    """
    Split a string column into a list column.
    """
    if pg_element_type.lower() not in {
        "text",
    }:
        raise ValueError(f"Unsupported PostgreSQL element type: {pg_element_type}")

    list_type = sql.SQL(f"{pg_element_type}[]")  # type: ignore

    with psycopg.connect(
        conninfo=uri,
    ) as conn:
        try:
            cursor = conn.cursor()

            # split the string into a list, and write it to a new column
            # plus remove the old column
            cursor.execute(
                query=sql.SQL("""
                ALTER TABLE {table}
                ADD COLUMN {out_column} {list_type};
                """).format(
                    table=sql.Identifier(schema_name, table_name),
                    out_column=sql.Identifier(out_column),
                    list_type=list_type,
                )
            )
            cursor.execute(
                query=sql.SQL("""
                UPDATE {table}
                SET {out_column} = STRING_TO_ARRAY({in_column}, %s)::{list_type};
                """).format(
                    table=sql.Identifier(schema_name, table_name),
                    out_column=sql.Identifier(out_column),
                    in_column=sql.Identifier(in_column),
                    list_type=list_type,
                ),
                params=(separator,),
            )

            cursor.execute(
                query=sql.SQL("""
                ALTER TABLE {table}
                DROP COLUMN {in_column};
                """).format(
                    table=sql.Identifier(schema_name, table_name),
                    in_column=sql.Identifier(in_column),
                )
            )
            conn.commit()

        except psycopg.Error:
            logger.exception(
                f"Error splitting column '{in_column}' in table '{table_name}'"
            )


# def polars_write_database(
#     df: pl.DataFrame,
#     *,
#     schema_name: str = "public",
#     table_name: str,
#     connection: str,
#     if_table_exists: DbWriteMode = "fail",
#     engine: DbWriteEngine = "sqlalchemy",
# ):
#     """
#     pl.DataFrame.write_database() but address the issue of writing unsigned and list columns to database.
#
#     Save all list columns as string columns, then split them back to list columns in the database.
#     This takes some time.
#     """
#     # UInt64 to Int64
#     for col in df.columns:
#         if df[col].dtype == pl.UInt64:
#             df = df.with_columns(pl.col(col).cast(pl.Int64).alias(col))
#
#     # List to string
#     columns_with_list = [col for col in df.columns if df[col].dtype == pl.List]
#     col_to_inner_dtype: dict[str, pl.datatypes.DataType] = {}
#     for col in columns_with_list:
#         dtype = df[col].dtype
#         assert isinstance(dtype, pl.List)
#         inner_dtype = dtype.inner
#         assert inner_dtype is not None
#         col_to_inner_dtype[col] = inner_dtype
#
#         df = df.with_columns(
#             pl.col(col)
#             .cast(pl.List(pl.Utf8))
#             .list.join("/@#DSLKF")
#             .alias(f"{col}_strjoinedAOIFDSIUH")
#         )
#         df.drop_in_place(col)
#
#     # Make safe table_name with schema_name.
#     # pl.DataFrame.write_database() only has table_name, so we need to add schema_name.
#     table_with_schema_str = None
#     with psycopg.connect(
#         conninfo=connection,
#     ) as conn:
#         cursor = conn.cursor()
#         table_with_schema_str = (
#             sql.SQL("""{table_name}""")
#             .format(table_name=sql.Identifier(schema_name, table_name))
#             .as_string(cursor)
#         )
#     if table_with_schema_str is None:
#         raise ValueError(
#             "Failed to get table name with schema. Maybe we can't connect to the database."
#         )
#
#     df.write_database(
#         table_name=table_with_schema_str,
#         connection=connection,
#         if_table_exists=if_table_exists,
#         engine=engine,
#     )
#
#     for col in columns_with_list:
#         split_column_str_to_list(
#             uri=connection,
#             schema_name=schema_name,
#             table_name=table_name,
#             in_column=f"{col}_strjoinedAOIFDSIUH",
#             out_column=col,
#             separator="/@#DSLKF",
#             pg_element_type=polars_datatype_to_postgresql_type(col_to_inner_dtype[col]),
#         )


def polars_write_database(
    df: pl.DataFrame,
    *,
    schema_name: str = "public",
    table_name: str,
    connection: str | Engine,
    if_table_exists: DbWriteMode = "fail",
):
    """
    pl.DataFrame.write_database() but address the issue of writing unsigned and list columns to database.

    Reference:
        - https://stackoverflow.com/questions/77098480/polars-psycopg2-write-column-of-lists-to-postgresql
    """
    if isinstance(connection, str):
        connection = create_engine(connection)

    columns_dtype = {col: df[col].dtype for col in df.columns}
    column_name_to_sqlalchemy_type = {
        col: polars_datatype_to_sqlalchemy_type(dtype)
        for col, dtype in columns_dtype.items()
    }

    pd_df = df.to_pandas(use_pyarrow_extension_array=True)

    # If any column has type list[number] in Polars, the pandas DataFrame will have a numpy array.
    # We need to convert it to a list, because `to_sql` doesn't support numpy arrays.
    for col, dtype in columns_dtype.items():
        if isinstance(dtype, pl.List):
            if isinstance(dtype.inner, pl.Utf8):
                continue
            pd_df[col] = pd_df[col].apply(lambda x: x.tolist())

    # ic(pd_df)
    pd_df.to_sql(
        schema=schema_name,
        name=table_name,
        con=connection,
        if_exists=if_table_exists,
        index=False,
        dtype=column_name_to_sqlalchemy_type,  # type: ignore
    )
