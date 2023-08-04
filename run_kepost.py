from pathlib import Path

from kepost import config
from kepost.workflows.base import init_kepost_wf

if __name__ == "__main__":
    # path = "/media/groot/Minerva/ConnectomePlasticity/MRI/derivatives_dwipa"
    path = "/media/groot/Minerva/TheBase/MRI/derivatives_dwipa/"
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

    config_file = Path(path) / "kepost" / "config.toml"
    config.load(config_file)
    subjects = config.execution.participant_label
    if not subjects:
        subjects = config.execution.layout.get_subjects()

    for subject in subjects:
        out_dir = config.execution.output_dir / f"sub-{subject}"
        if out_dir.exists():
            continue
        keprep_dir = Path(config.execution.layout.root) / f"sub-{subject}"
        # print(qsiprep_dir)
        if not keprep_dir.exists():
            continue
        # config.execution.layout.get_sessions(subject)
        # break
        # print(subject)
        try:
            config.execution.participant_label = [subject]
            workflow = init_kepost_wf()
            workflow.run()
        except Exception as e:
            # print(qsiprep_dir)
            print(e)
            continue
        #     break
