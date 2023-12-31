from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost.workflows.diffusion.procedures.tensor_estimations.dipy import (
    init_dipy_tensor_wf,
)
from kepost.workflows.diffusion.procedures.tensor_estimations.mrtrix3 import (
    init_mrtrix3_tensor_wf,
)


def init_tensor_estimation_wf(
    name: str = "tensor_estimation_wf",
) -> pe.Workflow:
    """
    Initialize the tensor estimation workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "tensor_estimation_wf"

    Returns
    -------
    pe.Workflow
        The tensor estimation workflow
    """
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_nifti",
                "dwi_bvec",
                "dwi_bval",
                "dwi_grad",
                "dwi_mask",
                "dipy_fit_method",
                "native_to_mni_transform",
                "dwi_to_t1w_transform",
                "t1w_reference",
            ]
        ),
        name="inputnode",
    )
    dipy_tensor_wf = init_dipy_tensor_wf()
    workflow.connect(
        [
            (
                inputnode,
                dipy_tensor_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.dwi_nifti"),
                    ("dwi_bvec", "inputnode.dwi_bvec"),
                    ("dwi_bval", "inputnode.dwi_bval"),
                    ("dwi_mask", "inputnode.dwi_mask"),
                    ("dipy_fit_method", "inputnode.fit_method"),
                    (
                        "native_to_mni_transform",
                        "inputnode.native_to_mni_transform",
                    ),
                    ("dwi_to_t1w_transform", "inputnode.dwi_to_t1w_transform"),
                    ("t1w_reference", "inputnode.t1w_reference"),
                ],
            ),
        ]
    )
    mrtrix3_tensor_wf = init_mrtrix3_tensor_wf()
    workflow.connect(
        [
            (
                inputnode,
                mrtrix3_tensor_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.dwi_nifti"),
                    ("dwi_grad", "inputnode.dwi_grad"),
                    ("dwi_mask", "inputnode.dwi_mask"),
                    (
                        "native_to_mni_transform",
                        "inputnode.native_to_mni_transform",
                    ),
                    ("dwi_to_t1w_transform", "inputnode.dwi_to_t1w_transform"),
                    ("t1w_reference", "inputnode.t1w_reference"),
                ],
            ),
        ]
    )
    return workflow
