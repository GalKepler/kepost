"""Console script for kepost."""

import typer
from rich.console import Console

import kepost

app = typer.Typer()
console = Console()


@app.command()
def main():
    """Console script for kepost."""
    console.print("Replace this message by putting your code into " "kepost.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")


if __name__ == "__main__":
    app()
