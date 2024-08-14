import json
import os
from pathlib import Path
from typing import Union

from bids.layout import BIDSLayout

from kepost.interfaces.bids.static.queries import QUERIES


def get_entity(in_file: str, entity: str) -> str:
    """
    Get the atlas name from the atlas nifti file.

    Parameters
    ----------
    atlas_nifti : str
        Path to the atlas nifti file.

    Returns
    -------
    atlas_name : str
        Name of the atlas.
    """
    from importlib.resources import files
    from json import loads
    from pathlib import Path

    from bids.layout import Config, parse_file_entities

    def resource_filename(package, resource):
        return str(files(package).joinpath(resource))

    _pybids_spec = loads(
        Path(
            resource_filename("kepost", "interfaces/bids/static/kepost.json")
        ).read_text()
    )
    config = Config(**_pybids_spec)
    entities = parse_file_entities(in_file, config=config)
    # if entity == "desc":
    #     if entities.get("desc") and entities.get("desc") in [
    #         "preproc",
    #         "unfiltered",
    #         "SIFT",
    #         "SIFT2",
    #     ]:
    #         return ""
    return entities.get(entity)


def collect_data(
    layout: BIDSLayout,
    participant_label: Union[str, list],
    queries: dict = QUERIES,
):
    """
    Uses pybids to retrieve the input data for a given participant
    """
    if isinstance(participant_label, list):
        participant_label = participant_label[0]
    try:
        subj_data = {
            dtype: sorted(
                layout.get(
                    return_type="file",
                    subject=participant_label,
                    **query["entities"],
                )
            )[0]
            for dtype, query in queries.items()
            if query["scope"] == "subject"
        }
        session_data = {}
        for session in layout.get_sessions(subject=participant_label):
            session_data[session] = {
                dtype: sorted(
                    layout.get(
                        return_type="file",
                        subject=participant_label,
                        session=session,
                        **query["entities"],
                    )
                )[0]
                for dtype, query in queries.items()
                if query["scope"] == "session"
            }
            root = Path(layout.root) / f"sub-{participant_label}" / f"ses-{session}"
            session_data[session].update({"eddy_qc": str(root / "dwi" / "eddy_qc")})

    except IndexError:
        raise Exception(
            "No data found for participant {} and session {}".format(
                participant_label, session
            )
        )

    return subj_data, session_data


def gen_acq_label(max_bval: int) -> str:
    """
    Generate the acquisition label

    Parameters
    ----------
    max_bval : int
        The maximum bval

    Returns
    -------
    str
        The acquisition label
    """
    return f"shell{int(max_bval)}"


def write_derivative_description(bids_dir, deriv_dir):
    from kepost import __version__

    DOWNLOAD_URL = (
        f"https://github.com/GalKepler/kepost/archive/refs/tags/v{__version__}.tar.gz"
    )

    desc = {
        "Name": "KePost output",
        "BIDSVersion": "1.9.0",
        "PipelineDescription": {
            "Name": "kepost",
            "Version": __version__,
            "CodeURL": DOWNLOAD_URL,
        },
        "GeneratedBy": [
            {
                "Name": "kepost",
                "Version": __version__,
                "CodeURL": DOWNLOAD_URL,
            }
        ],
        "CodeURL": "https://github.com/GalKepler/kepost",
        "HowToAcknowledge": "Please cite our paper and "
        "include the generated citation boilerplate within the Methods "
        "section of the text.",
    }

    # Keys deriving from source dataset
    fname = os.path.join(bids_dir, "dataset_description.json")
    if os.path.exists(fname):
        with open(fname) as fobj:
            orig_desc = json.load(fobj)
    else:
        orig_desc = {}

    if "DatasetDOI" in orig_desc:
        desc["SourceDatasetsURLs"] = [
            "https://doi.org/{}".format(orig_desc["DatasetDOI"])
        ]
    if "License" in orig_desc:
        desc["License"] = orig_desc["License"]

    with open(os.path.join(deriv_dir, "dataset_description.json"), "w") as fobj:
        json.dump(desc, fobj, indent=4)


def write_bidsignore(deriv_dir):
    bids_ignore = (
        "*.html",
        "logs/",
        "figures/",  # Reports
        "*_xfm.*",  # Unspecified transform files
        "*.surf.gii",  # Unspecified structural outputs
        # Unspecified diffusion outputs
        "*.tck",
        "*.mif",
        "*.b",
        "qc",
        "mrtrix3",
        "dipy",
    )
    ignore_file = Path(deriv_dir) / ".bidsignore"

    ignore_file.write_text("\n".join(bids_ignore) + "\n")
