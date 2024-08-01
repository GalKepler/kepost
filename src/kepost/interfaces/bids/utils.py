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
    from bids.layout import parse_file_entities

    entities = parse_file_entities(in_file)
    return entities[entity]


def collect_data(
    layout: BIDSLayout,
    participant_label: str,
    queries: dict = QUERIES,
):
    """
    Uses pybids to retrieve the input data for a given participant
    """
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
