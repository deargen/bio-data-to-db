# bio-data-to-db: make Uniprot PostgreSQL database

[![image](https://img.shields.io/pypi/v/bio-data-to-db.svg)](https://pypi.python.org/pypi/bio-data-to-db)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/bio-data-to-db)](https://pypi.python.org/pypi/bio-data-to-db)
[![image](https://img.shields.io/pypi/l/bio-data-to-db.svg)](https://pypi.python.org/pypi/bio-data-to-db)
[![image](https://img.shields.io/pypi/pyversions/bio-data-to-db.svg)](https://pypi.python.org/pypi/bio-data-to-db)

|  |  |
|--|--|
|[![Ruff](https://img.shields.io/badge/Ruff-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://github.com/astral-sh/ruff) [![rustfmt](https://img.shields.io/badge/rustfmt-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)](https://github.com/rust-lang/rustfmt) |[![Actions status](https://github.com/deargen/bio-data-to-db/workflows/Style%20checking/badge.svg)](https://github.com/deargen/bio-data-to-db/actions)|
| [![Ruff](https://img.shields.io/badge/Ruff-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://github.com/astral-sh/ruff) [![Clippy](https://img.shields.io/badge/clippy-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)](https://github.com/rust-lang/rust-clippy) | [![Actions status](https://github.com/deargen/bio-data-to-db/workflows/Linting/badge.svg)](https://github.com/deargen/bio-data-to-db/actions) |
| [![doctest](https://img.shields.io/badge/doctest-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://docs.python.org/3/library/doctest.html) | [![Actions status](https://github.com/deargen/bio-data-to-db/workflows/Tests/badge.svg)](https://github.com/deargen/bio-data-to-db/actions) |
| [![uv](https://img.shields.io/badge/uv-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://github.com/astral-sh/uv) | [![Actions status](https://github.com/deargen/bio-data-to-db/workflows/Check%20pip%20compile%20sync/badge.svg)](https://github.com/deargen/bio-data-to-db/actions) |
|[![Built with Material for MkDocs](https://img.shields.io/badge/Material_for_MkDocs-526CFE?style=for-the-badge&logo=MaterialForMkDocs&logoColor=white)](https://squidfunk.github.io/mkdocs-material/)|[![Actions status](https://github.com/deargen/bio-data-to-db/workflows/Deploy%20MkDocs%20on%20latest%20commit/badge.svg)](https://github.com/deargen/bio-data-to-db/actions)|


Bio data is a little messy to work with, and everybody deserves a clean database. This package helps you to convert bio data to a database.

Partially written in Rust, thus equipped with an extremely fast uniprot xml parser. Packaged for python, so anyone can easily install and use it.

This package focuses more on parsing the data and inserting it into the database, rather than curating the data. Main features include:

- **Uniprot**: Parse the uniprot xml file and insert the data into the database.
- **BindingDB**: Fix the HTML entities in the assay table.
- **PostgreSQL Helpers**: Useful functions to work with PostgreSQL.
- **SMILES**: Canonicalize SMILES strings.
- **Polars**: Useful functions to work with Polars.

[📚 Documentation](https://deargen.github.io/bio-data-to-db/) has the API reference and the usage.

## 🛠️ Installation

```bash
pip install bio-data-to-db
```

## 🚦 Usage

You can use the command line interface or the python API.

### Uniprot

```bash
# It will create a db 'uniprot' and a table named 'public.uniprot_info' in the database.
# If you want another name, you can optionally pass it as the last argument.
bio-data-to-db uniprot create-empty-table 'postgresql://username@localhost:5432/uniprot'

# It will parse the xml file and insert the data into the table.
# It requires that the table is already created.
bio-data-to-db uniprot xml-to-postgresql '~/Downloads/uniprot_sprot.xml' 'postgresql://username@localhost:5432/uniprot'

# Create a table that maps accession to pk_id.
# Columns: accession (text), uniprot_pk_ids (integer[])
bio-data-to-db uniprot create-accession-to-pk-id 'postgresql://username@localhost:5432/uniprot'

# It will parse the keywords tsv file and insert the data into the table.
bio-data-to-db uniprot keywords-tsv-to-postgresql '~/Downloads/keywords_all_2024_06_26.tsv' 'postgresql://username@localhost/uniprot'
```

```python
from bio_data_to_db.uniprot import (
    create_accession_to_pk_id_table,
    create_empty_table,
    uniprot_xml_to_postgresql,
    keywords_tsv_to_postgresql,
)

create_empty_table("postgresql://user:password@localhost:5432/uniprot")
# It requires that the table is already created.
uniprot_xml_to_postgresql("~/Downloads/uniprot_sprot.xml", "postgresql://user:password@localhost:5432/uniprot")
create_accession_to_pk_id_table("postgresql://user:password@localhost:5432/uniprot")
keywords_tsv_to_postgresql("~/Downloads/keywords_all_2024_06_26.tsv", "postgresql://user:password@localhost:5432/uniprot")
```

### BindingDB

```bash
# Decode HTML entities and strip the strings in the `assay` table (column: description and assay_name).
# Currently, only assay table is supported.
bio-data-to-db bindingdb fix-table assay 'mysql://username:password@localhost/bind'
```

```python
from bio_data_to_db.bindingdb.fix_tables import fix_assay_table

fix_assay_table("mysql://username:password@localhost/bind")
```

### PostgreSQL Helpers, SMILES, Polars utils and more

This package also provides some useful functions to work with PostgreSQL, SMILES, Polars and more.

```python
from bio_data_to_db.utils.postgresql import (
    create_db_if_not_exists,
    create_schema_if_not_exists,
    make_int_column_primary_key_identity,
    make_columns_primary_key,
    make_columns_unique,
    make_large_columns_unique,
    split_column_str_to_list,
    polars_write_database,  # addressed issues with list columns
)

from bio_data_to_db.utils.smiles import (
    canonical_smiles_wo_salt,
    polars_canonical_smiles_wo_salt,
)

from bio_data_to_db.utils.fasta import (
    polars_standardize_fasta,
)

from bio_data_to_db.utils.polars import (
    w_pbar,
)
```

You can find the usage in the [📚 documentation](https://deargen.github.io/bio-data-to-db/).


## 👨‍💻️ Maintenance Notes

### Install from source

Install `uv`, `rustup` and `maturin`. Activate a virtual environment. Then,

```bash
bash scripts/install.sh
uv pip install -r deps/requirements_dev.in
```

### Generate lockfiles

Use GitHub Actions: `apply-pip-compile.yml`. Manually launch the workflow and it will make a commit with the updated lockfiles.

### Publish a new version to PyPI

Use GitHub Actions: `deploy.yml`. Manually launch the workflow and it will compile on all architectures and publish the new version to PyPI.

### About sqlx

Sqlx offline mode should be configured so you can compile the code without a database present.

First, you need to make sure the database is connected to enable the offline mode.

```bash
# .env file
DATABASE_URL=postgresql://postgres:password@localhost:5432/uniprot
SQLX_OFFLINE=true  # force offline mode. Otherwise, use the DATABASE_URL to connect to the database.
```

The database needs to have the table. It can be empty but the structure has to be accessible.  
If it doesn't already exist, you can create the table with the following command.

```bash
bio-data-to-db uniprot create-empty-table 'postgresql://username@localhost:5432/uniprot'
```

Then, you can run the following command to prepare the SQL queries. This defines the type information for the queries.

```bash
cargo install sqlx-cli --no-default-features --features postgres
cargo sqlx prepare
```

This will make `.sqlx/` directory with the type information for the queries.

