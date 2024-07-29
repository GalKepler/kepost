from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu
from nipype.interfaces.base import isdefined
from nipype.pipeline import engine as pe

from kepost import config
from kepost.interfaces.mrtrix3 import MRConvert
from kepost.workflows.diffusion.procedures.tensor_estimations.dipy import (
    init_dipy_tensor_wf,
)

# from kepost.workflows.diffusion.procedures.tensor_estimations.mrtrix3 import (
#     init_mrtrix3_tensor_wf,
# )


def detect_shells(bvals: str, max_bval: int, bval_tol: int = 50) -> list:
    """
    Detect the shells from the bvals file

    Parameters
    ----------
    bvals : str
        The bvals file
    max_bval : int
        The maximum bval

    Returns
    -------
    list
        The shells
    """
    import numpy as np

    bvals = np.loadtxt(bvals)
    bvals = np.unique(bvals)
    max_bval = max_bval if max_bval is not None else np.max(bvals)
    bvals = bvals[bvals <= max_bval + bval_tol]
    bvals = bvals[bvals > 0]
    return list(set(np.round(bvals, -2))), max_bval


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
                "dwi_bzero",
                "dipy_fit_method",
                "native_to_mni_transform",
                "dwi_to_t1w_transform",
                "t1w_reference",
            ]
        ),
        name="inputnode",
    )
    max_bval = config.workflow.tensor_max_bval
    max_bval = max_bval if isdefined(max_bval) else None
    detect_shells_node = pe.Node(
        niu.Function(
            input_names=["bvals", "max_bval"],
            output_names=["shells", "max_bval"],
            function=detect_shells,
        ),
        name="detect_shells",
    )
    detect_shells_node.inputs.max_bval = max_bval
    dwiextract_node = pe.Node(
        interface=mrt.DWIExtract(
            out_file="dwi_max_bval.mif",
        ),
        name="dwiextract",
    )
    mrconvert_node = pe.Node(
        interface=MRConvert(
            out_file="dwi_max_bval.nii.gz",
            out_bvec="dwi_max_bval.bvec",
            out_bval="dwi_max_bval.bval",
            out_mrtrix_grad="dwi_max_bval.b",
        ),
        name="mrconvert",
    )
    workflow.connect(
        [
            (
                inputnode,
                detect_shells_node,
                [
                    ("dwi_bval", "bvals"),
                ],
            ),
            (
                inputnode,
                dwiextract_node,
                [
                    ("dwi_nifti", "in_file"),
                    ("dwi_grad", "grad_file"),
                ],
            ),
            (
                detect_shells_node,
                dwiextract_node,
                [
                    ("shells", "shell"),
                ],
            ),
            (
                dwiextract_node,
                mrconvert_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
        ]
    )
    dipy_tensor_wf = init_dipy_tensor_wf()
    workflow.connect(
        [
            (
                inputnode,
                dipy_tensor_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.source_file"),
                    ("dwi_mask", "inputnode.dwi_mask"),
                    ("dwi_bzero", "inputnode.dwi_bzero"),
                    ("dipy_fit_method", "inputnode.fit_method"),
                    ("native_to_mni_transform", "inputnode.native_to_mni_transform"),
                    ("dwi_to_t1w_transform", "inputnode.dwi_to_t1w_transform"),
                    ("t1w_reference", "inputnode.t1w_reference"),
                ],
            ),
            (
                detect_shells_node,
                dipy_tensor_wf,
                [
                    ("max_bval", "inputnode.max_bval"),
                ],
            ),
            (
                mrconvert_node,
                dipy_tensor_wf,
                [
                    ("out_file", "inputnode.dwi_nifti"),
                    ("out_bvec", "inputnode.dwi_bvec"),
                    ("out_bval", "inputnode.dwi_bval"),
                ],
            ),
        ]
    )
    return workflow
    # return workflow
    # mrtrix3_tensor_wf = init_mrtrix3_tensor_wf()
    # workflow.connect(
    #     [
    #         (
    #             inputnode,
    #             mrtrix3_tensor_wf,
    #             [
    #                 ("base_directory", "inputnode.base_directory"),
    #                 ("dwi_nifti", "inputnode.dwi_nifti"),
    #                 ("dwi_grad", "inputnode.dwi_grad"),
    #                 ("dwi_mask", "inputnode.dwi_mask"),
    #                 (
    #                     "native_to_mni_transform",
    #                     "inputnode.native_to_mni_transform",
    #                 ),
    #                 ("dwi_to_t1w_transform", "inputnode.dwi_to_t1w_transform"),
    #                 ("t1w_reference", "inputnode.t1w_reference"),
    #             ],
    #         ),
    #     ]
    # )
    # return workflow
