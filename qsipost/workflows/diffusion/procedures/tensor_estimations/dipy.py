from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from qsipost.interfaces.bids import DerivativesDataSink
from qsipost.interfaces.dipy import ReconstDTI
from qsipost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)

TENSOR_PARAMETERS = [
    "tensor",
    "fa",
    "ga",
    "rgb",
    "md",
    "ad",
    "rd",
    "mode",
    "evec",
    "eval",
]


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
                "base_directory",
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
    tensor_wf = pe.Node(interface=ReconstDTI(), name="dipy_tensor_wf")
    listify_tensor_params = pe.Node(
        interface=niu.Merge(numinputs=len(TENSOR_PARAMETERS)),
        name="listify_tensor_params",
    )
    ds_tensor_wf = pe.MapNode(
        interface=DerivativesDataSink(
            **DIFFUSION_WF_OUTPUT_ENTITIES.get("dti_derived_parameters"),
            software="dipy",
            save_meta=False,
        ),
        iterfield=["in_file", "desc"],
        name="ds_tensor_wf",
    )
    ds_tensor_wf.inputs.desc = TENSOR_PARAMETERS
    # remove meta_dict from inputs
    # ds_tensor_wf.inputs.meta_dict = _Undefined

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
            (
                outputnode,
                listify_tensor_params,
                [(param, f"in{i+1}") for i, param in enumerate(TENSOR_PARAMETERS)],
            ),
            (
                listify_tensor_params,
                ds_tensor_wf,
                [("out", "in_file")],
            ),
            (
                inputnode,
                ds_tensor_wf,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
        ]
    )
    return workflow
