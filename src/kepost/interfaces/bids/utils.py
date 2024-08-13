from pathlib import Path

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
    participant_label: str,
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
