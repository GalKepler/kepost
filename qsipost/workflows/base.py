from typing import Union

from pathlib import Path

from nipype.pipeline import engine as pe

from qsipost.bids.layout import QSIPREPLayout
from qsipost.workflows.utils.bids import collect_data


def init_qsipost_wf(
    layout: QSIPREPLayout,
    subjects_list: list = [],
    work_dir: Union[str, Path] = None,
):
    """
    Initialize the qsipost workflow.

    Parameters
    ----------
    layout : QSIPREPLayout
        The BIDSLayout object.
    subjects_list : list, optional
        List of subjects to be processed. The default is [].
    work_dir : Union[str, Path], optional
        The working directory. The default is None.
    """
    subjects_list = subjects_list or layout.get_subjects()
    work_dir = Path(work_dir or "qsipost_wf")
    work_dir.mkdir(exist_ok=True, parents=True)

    qsipost_wf = pe.Workflow(name="qsipost_wf")
    qsipost_wf.base_dir = str(work_dir.resolve())
    reportlets_dir = work_dir / "reportlets"
    reportlets_dir.mkdir(exist_ok=True)
    for subject_id in subjects_list:
        single_subject_wf = init_single_subject_wf(
            layout=layout,
            subject_id=subject_id,
            name=f"single_subject_{subject_id}_wf",
        )


def init_single_subject_wf(
    layout: QSIPREPLayout,
    subject_id: str,
    name: str,
):
    """
    Initialize the qsipost workflow for a single subject.

    Parameters
    ----------
    layout : QSIPREPLayout
        The BIDSLayout object.
    subject_id : str
        The subject ID.
    """
    workflow = pe.Workflow(name=name)
