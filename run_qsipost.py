from pathlib import Path

from qsipost import config
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
    path = "/media/groot/Minerva/ConnectomePlasticity/MRI/derivatives"
    # database_file = (
    #     "/media/groot/Minerva/ConnectomePlasticity/MRI/derivatives/qsiprep_layout.db"
    # )
    # reset_database = True

    # work_dir = "/media/groot/Minerva/ConnectomePlasticity/MRI/work"

    # atlas = "brainnetome"
    # brainnetome = Atlas("brainnetome", load_existing=True)

    # layout = get_or_create_database(
    #     path,
    #     database_path=database_file,
    #     reset_database=reset_database,
    # )

    config_file = Path(path) / "qsipost" / "config.toml"
    config.load(config_file)
    subjects = config.execution.participant_label
    if not subjects:
        subjects = config.execution.layout.get_subjects()

    for subject in subjects:
        # config.execution.layout.get_sessions(subject)
        # break
        try:
            config.execution.participant_label = [subject]
            workflow = init_qsipost_wf()
            workflow.run()
        except Exception as e:
            print(e)
            continue
