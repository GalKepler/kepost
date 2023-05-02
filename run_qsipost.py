from qsipost.bids.layout.layout import QSIPREPLayout
from qsipost.parcellations.atlases.atlas import Atlas
from qsipost.workflows.base import init_qsipost_wf


def get_or_create_database(
    path,
    database_path=None,
    reset_database=False,
):
    layout = QSIPREPLayout(
        path,
        database_path=database_path,
        reset_database=reset_database,
    )
    return layout


if __name__ == "__main__":
    path = "/media/groot/Minerva/ConnectomePlasticity/MRI/derivatives/qsiprep/"
    database_file = (
        "/media/groot/Minerva/ConnectomePlasticity/MRI/derivatives/qsiprep_layout.db"
    )
    reset_database = False

    work_dir = "/media/groot/Minerva/ConnectomePlasticity/MRI/work"

    atlas = "brainnetome"
    brainnetome = Atlas("brainnetome", load_existing=True)

    layout = get_or_create_database(
        path,
        database_path=database_file,
        reset_database=reset_database,
    )

    workflow = init_qsipost_wf(
        layout,
        parcellation_atlas=brainnetome,
        work_dir=work_dir,
        # subjects_list=["12"],
    )
    workflow.run()
