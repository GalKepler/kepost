from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from qsipost.interfaces.dipy import ReconstDTI
from qsipost.workflows.diffusion.procedures.tensor_estimations.utils import (
    TENSOR_PARAMETERS,
    estimate_tensors,
)


def init_dipy_tensor_wf(
    name: str = "dipy_tensor_wf",
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
                "dwi_nifti",
                "dwi_bvec",
                "dwi_bval",
                "dwi_mask",
                "fit_method",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        interface=niu.IdentityInterface(fields=TENSOR_PARAMETERS),
        name="outputnode",
    )
    # tensor_wf = pe.Node(
    #     interface=niu.Function(
    #         input_names=[
    #             "dwi_nifti",
    #             "dwi_bvec",
    #             "dwi_bval",
    #             "dwi_mask",
    #             "fit_method",
    #         ],
    #         output_names=TENSOR_PARAMETERS,
    #         function=estimate_tensors,
    #     ),
    #     name="dipy_tensor_wf",
    # )
    tensor_wf = pe.Node(interface=ReconstDTI(), name="dipy_tensor_wf")
    workflow.connect(
        [
            (
                inputnode,
                tensor_wf,
                [
                    ("dwi_nifti", "in_file"),
                    ("dwi_bvec", "in_bvec"),
                    ("dwi_bval", "in_bval"),
                    ("dwi_mask", "mask_file"),
                    ("fit_method", "fit_method"),
                ],
            ),
            (
                tensor_wf,
                outputnode,
                [(f"{param}_file", param) for param in TENSOR_PARAMETERS],
            ),
        ]
    )
    return workflow
