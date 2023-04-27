from qsipost.bids.layout.layout import QSIPREPLayout
from qsipost.workflows.utils.queries import QUERIES


def collect_data(
    layout: QSIPREPLayout,
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

    except IndexError:
        raise Exception(
            "No data found for participant {} and session {}".format(
                participant_label, session
            )
        )

    return subj_data, session_data
