#!/home/groot/Projects/qsipost/.venv/bin/python
import re
import sys

import typer

from qsipost.cli.run import main

# if __name__ == '__main__':

app = typer.Typer(
    name="qsipost",
    help="Post-processing for QSIPrep's outputs",
    add_completion=False,
)


@app.command(name="")
def main():
    """
    The main entrypoint for qsipost.
    """
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
