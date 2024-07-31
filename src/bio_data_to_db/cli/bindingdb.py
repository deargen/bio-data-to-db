import enum
import logging
from typing import Annotated

import typer

logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)


class FixTableOption(str, enum.Enum):
    assay = "assay"


@app.command(no_args_is_help=True)
def fix_table(
    table_name: Annotated[
        FixTableOption,
        typer.Argument(help="Table name to fix"),
    ],
    uri: Annotated[
        str,
        typer.Argument(help="URI to the MySQL database"),
    ],
):
    """
    Fix the assay table in MySQL by decoding HTML entities like '&#39;' and strip empty spaces.
    """
    from bio_data_to_db.bindingdb.fix_tables import fix_assay_table
    from bio_data_to_db.utils.log import setup_logging

    setup_logging()
    fix_assay_table(uri)
    logger.info(
        "In `assay` table, HTML entities are decoded and empty spaces are stripped."
    )


def main():
    app()


if __name__ == "__main__":
    main()
