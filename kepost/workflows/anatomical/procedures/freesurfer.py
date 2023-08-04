from nipype.interfaces import utility as niu
from nipype.interfaces.freesurfer import ReconAll
from nipype.pipeline import engine as pe

from kepost import config


def init_freesurfer_wf(name: str = "freesurfer_wf") -> pe.Workflow:
    """
    Initialize the freesurfer workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "freesurfer_wf"

    Returns
    -------
    pe.Workflow
        The freesurfer workflow.
    """
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "anatomical_reference",
                "freesurfer_subjects_dir",
                "subject_id",
            ]
        ),
        name="inputnode",
    )
    freesurfer_node = pe.Node(
        interface=ReconAll(
            openmp=config.execution.omp_nthreads,
        ),
        name="freesurfer",
    )
    workflow.connect(
        [
            (
                inputnode,
                freesurfer_node,
                [
                    ("anatomical_reference", "T1_files"),
                    ("freesurfer_subjects_dir", "subjects_dir"),
                    ("subject_id", "subject_id"),
                ],
            ),
        ]
    )
    return workflow
