import typer

from . import uniprot

app = typer.Typer(no_args_is_help=True)

app.add_typer(uniprot.app, name="uniprot")


def main():
    app()


if __name__ == "__main__":
    main()
