# bio-data-to-db: make Uniprot PostgreSQL database

[![image](https://img.shields.io/pypi/v/bio-data-to-db.svg)](https://pypi.python.org/pypi/bio-data-to-db)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/bio-data-to-db)](https://pypi.python.org/pypi/bio-data-to-db)
[![image](https://img.shields.io/pypi/l/bio-data-to-db.svg)](https://pypi.python.org/pypi/bio-data-to-db)
[![image](https://img.shields.io/pypi/pyversions/bio-data-to-db.svg)](https://pypi.python.org/pypi/bio-data-to-db)

|  |  |
|--|--|
|[![Ruff](https://img.shields.io/badge/Ruff-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://github.com/astral-sh/ruff) [![rustfmt](https://img.shields.io/badge/rustfmt-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)](https://github.com/rust-lang/rustfmt) |[![Actions status](https://github.com/deargen/bio-data-to-db/workflows/Style%20checking/badge.svg)](https://github.com/deargen/bio-data-to-db/actions)|
| [![Ruff](https://img.shields.io/badge/Ruff-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://github.com/astral-sh/ruff) [![Clippy](https://img.shields.io/badge/clippy-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)](https://github.com/rust-lang/rust-clippy) | [![Actions status](https://github.com/deargen/bio-data-to-db/workflows/Linting/badge.svg)](https://github.com/deargen/bio-data-to-db/actions) |
| [![uv](https://img.shields.io/badge/uv-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://github.com/astral-sh/uv) | [![Actions status](https://github.com/deargen/bio-data-to-db/workflows/Check%20pip%20compile%20sync/badge.svg)](https://github.com/deargen/bio-data-to-db/actions) |


Bio data is a little messy to work with, and everybody deserves a clean database. This package helps you to convert bio data to a database.

Written in Rust, thus equipped with extremely fast parsers. Packaged for python, so anyone can easily install and use it.

So far, there is only one function implemented: **convert uniprot data to postgresql**. This package focuses more on parsing the data and inserting it into the database, rather than curating the data.

## 🛠️ Installation

```bash
pip install bio-data-to-db
```

## 🚦 Usage

You can use the command line interface or the python API.

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

## 👨‍💻️ Maintenance Notes

### Install from source

Install `uv`, `rustup` and `maturin`. Activate a virtual environment. Then,

```bash
bash scripts/install.sh
uv pip install -r deps/requirements_dev.in
```

### Compile requirements (generate lockfiles)

Use GitHub Actions: `apply-pip-compile.yml`. Manually launch the workflow and it will make a commit with the updated lockfiles.

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

