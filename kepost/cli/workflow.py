from typing import Union

from pathlib import Path

from nipype.pipeline import engine as pe


def build_workflow(config_file: Union[Path, str], retval: dict = {}) -> pe.Workflow:
    """
    Build the workflow from the configuration file.

    Parameters
    ----------
    config_file : Union[Path,str]
        The configuration file for the workflow.
    retval : dict, optional
        The dictionary to return, by default {}.

    Returns
    -------
    pe.Workflow
        The workflow.
    """
    from niworkflows.utils.bids import collect_participants

    from kepost import config
    from kepost.workflows.base import init_kepost_wf

    config.load(config_file)
    build_log = config.loggers.workflow

    kepost_dir = Path(config.execution.kepost_dir)
    version = config.environment.version

    retval["return_code"] = 1
    retval["workflow"] = None

    banner = f"Running kepost version {version}"
    build_log.log(25, banner)

    input_dataset_description = config.execution.layout.description

    subject_list = collect_participants(
        config.execution.layout,
        config.execution.participant_label,
        bids_validate=False,
    )

    init_message = [
        "Running kepost workflow:",
        f"QSIprep dataset path: {config.execution.layout.root}",
        f"Participant list: {subject_list}",
        f"Run identifier: {config.execution.run_uuid}",
        f"Output directory: {kepost_dir}",
    ]

    build_log.log(25, "\n".join(init_message))

    retval["workflow"] = init_kepost_wf()
    config.to_filename(config_file)

    build_log.info(
        "kepost workflow graph with %d nodes built successfully.",
        len(retval["workflow"].nodes()),
    )
    retval["return_code"] = 0
    return retval["workflow"]
