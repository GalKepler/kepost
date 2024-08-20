import json
from pathlib import Path

KEPOST_DDS_CONFIGURATIONS_FILE = Path(__file__).parent / "kepost.json"
with open(str(KEPOST_DDS_CONFIGURATIONS_FILE), "r") as infile:
    KEPOST_DDS_CONFIGURATIONS = json.load(infile)
