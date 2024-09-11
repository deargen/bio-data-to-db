# ruff: noqa: T201
import os
import urllib.parse
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def get_uri_from_env(
    db_name: Annotated[str | None, typer.Argument(..., help="Database name")] = None,
):
    """
    Get connection URI from environment variables for .env file.

    The following environment variables are required:

    - POSTGRESQL_HOST (default: localhost)
    - POSTGRESQL_PORT (default: 5432)
    - POSTGRESQL_USER
    - POSTGRESQL_PASSWORD
    """
    from dotenv import find_dotenv, load_dotenv

    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path != "":
        load_dotenv(dotenv_path)

    host = os.getenv("POSTGRESQL_HOST")
    if host is None:
        host = "localhost"
    port = os.getenv("POSTGRESQL_PORT")
    if port is None:
        port = "5432"

    user = os.getenv("POSTGRESQL_USER")
    if user is None:
        print("❌ POSTGRESQL_USER is required.")
        typer.Exit(code=1)
        return
    password = os.getenv("POSTGRESQL_PASSWORD")
    if password is None:
        print("❌ POSTGRESQL_PASSWORD is required.")
        typer.Exit(code=1)
        return

    if db_name is not None:
        print(
            f"postgresql://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{db_name}"
        )
    else:
        print(f"postgresql://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}")


def main():
    app()


if __name__ == "__main__":
    main()
