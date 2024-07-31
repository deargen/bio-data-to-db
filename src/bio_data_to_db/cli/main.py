import typer

from . import bindingdb, uniprot

app = typer.Typer(no_args_is_help=True)

app.add_typer(uniprot.app, name="uniprot")
app.add_typer(bindingdb.app, name="bindingdb")


def main():
    app()


if __name__ == "__main__":
    main()
