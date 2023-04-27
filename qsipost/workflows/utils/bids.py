from qsipost.bids.layout.layout import QSIPREPLayout
from qsipost.workflows.utils.queries import QUERIES


def collect_data(
    layout: QSIPREPLayout,
    participant_label: str,
    session: str,
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
                    session=session if query["scope"] == "session" else None,
                    **query["entities"],
                )
            )[0]
            for dtype, query in queries.items()
        }
    except IndexError:
        raise Exception(
            "No data found for participant {} and session {}".format(
                participant_label, session
            )
        )

    return subj_data
