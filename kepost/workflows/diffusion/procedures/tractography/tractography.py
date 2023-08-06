from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost.workflows.diffusion.procedures.tractography.mrtrix import (
    init_mrtrix_tractography_wf,
)


def init_tractography_wf(
    name: str = "tractography_wf",
) -> pe.Workflow:
    """
    Initialize the tractography workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "tractography_wf"

    Returns
    -------
    pe.Workflow
        The tractography workflow
    """
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_reference",
                "dwi_nifti",
                "dwi_bvec",
                "dwi_bval",
                "dwi_grad",
                "dwi_mask",
                "t1w_file",
                "t1w_mask_file",
                "t1w_to_dwi_transform",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "unfiltered_tracts",
                "sift_tracts",
            ]
        ),
        name="outputnode",
    )

    mrtrix3_tractography_wf = init_mrtrix_tractography_wf()
    workflow.connect(
        [
            (
                inputnode,
                mrtrix3_tractography_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.dwi_file"),
                    ("dwi_reference", "inputnode.dwi_reference"),
                    ("dwi_grad", "inputnode.dwi_grad"),
                    ("dwi_mask", "inputnode.dwi_mask_file"),
                    ("t1w_file", "inputnode.t1w_file"),
                    ("t1w_mask_file", "inputnode.t1w_mask_file"),
                    ("t1w_to_dwi_transform", "inputnode.t1w_to_dwi_transform"),
                ],
            ),
            (
                mrtrix3_tractography_wf,
                outputnode,
                [
                    ("outputnode.unfiltered_tracts", "unfiltered_tracts"),
                    ("outputnode.sift_tracts", "sift_tracts"),
                ],
            ),
        ]
    )
    return workflow
