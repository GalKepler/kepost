from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu
from nipype.interfaces.base import isdefined
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost import config
from kepost.interfaces.bids import DerivativesDataSink
from kepost.interfaces.bids.utils import gen_acq_label
from kepost.interfaces.mrtrix3 import MRConvert
from kepost.workflows.diffusion.procedures.tensor_estimations.dipy import (
    init_dipy_tensor_wf,
)
from kepost.workflows.diffusion.procedures.tensor_estimations.mrtrix3 import (
    init_mrtrix3_tensor_wf,
)


def detect_shells(bvals: str, max_bval: int, bval_tol: int = 50) -> tuple[list, int]:
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

    bvals = np.loadtxt(bvals)  # type: ignore[assignment]
    bvals = np.unique(bvals)  # type: ignore[assignment]
    max_bval = max_bval if max_bval is not None else np.max(bvals)
    bvals = bvals[bvals <= max_bval + bval_tol]  # type: ignore[operator]
    bvals = bvals[bvals > 0]  # type: ignore[operator]
    return list(set(np.round(bvals, -2))), max_bval  # type: ignore[call-overload]


def init_tensor_estimation_wf(
    name: str = "tensor_estimation_wf",
) -> Workflow:
    """
    Initialize the tensor estimation workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "tensor_estimation_wf"

    Returns
    -------
    Workflow
        The tensor estimation workflow
    """
    workflow = Workflow(name=name)
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
    max_bval = max_bval if isdefined(max_bval) else None  # type: ignore[assignment]

    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "acq_label",
            ]
        ),
        name="outputnode",
    )

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
            json_export="dwi_max_bval.json",
        ),
        name="mrconvert",
    )
    gen_acq_label_node = pe.Node(
        niu.Function(
            input_names=["max_bval"],
            output_names=["acq_label"],
            function=gen_acq_label,
        ),
        name="gen_acq_label",
    )
    ds_dwiextract_node = pe.Node(
        interface=DerivativesDataSink(
            compress=True,
            dismiss_entities=["direction"],
            datatype="dwi",
            space="dwi",
        ),
        name="ds_dwiextract",
    )
    listify_gradients = pe.Node(niu.Merge(4), name="listify_associated_gradients")
    ds_dwi_supp = pe.MapNode(
        DerivativesDataSink(
            suffix="dwi",
            datatype="dwi",
            dismiss_entities=["direction"],
        ),
        iterfield=["in_file"],
        name="ds_dwi_gradients",
        run_without_submitting=True,
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
                detect_shells_node,
                gen_acq_label_node,
                [
                    ("max_bval", "max_bval"),
                ],
            ),
            (
                dwiextract_node,
                mrconvert_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                mrconvert_node,
                ds_dwiextract_node,
                [("out_file", "in_file")],
            ),
            (
                gen_acq_label_node,
                ds_dwiextract_node,
                [("acq_label", "acquisition")],
            ),
            (
                inputnode,
                ds_dwiextract_node,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (
                mrconvert_node,
                listify_gradients,
                [
                    ("out_bvec", "in1"),
                    ("out_bval", "in2"),
                    ("out_mrtrix_grad", "in3"),
                    ("json_export", "in4"),
                ],
            ),
            (
                listify_gradients,
                ds_dwi_supp,
                [("out", "in_file")],
            ),
            (
                gen_acq_label_node,
                ds_dwi_supp,
                [("acq_label", "acquisition")],
            ),
            (
                inputnode,
                ds_dwi_supp,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (
                gen_acq_label_node,
                outputnode,
                [
                    ("acq_label", "acq_label"),
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
    mrtrix3_tensor_wf = init_mrtrix3_tensor_wf()
    workflow.connect(
        [
            (
                inputnode,
                mrtrix3_tensor_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.source_file"),
                    ("dwi_mask", "inputnode.dwi_mask"),
                    (
                        "native_to_mni_transform",
                        "inputnode.native_to_mni_transform",
                    ),
                    ("dwi_to_t1w_transform", "inputnode.dwi_to_t1w_transform"),
                    ("t1w_reference", "inputnode.t1w_reference"),
                ],
            ),
            (
                detect_shells_node,
                mrtrix3_tensor_wf,
                [
                    ("max_bval", "inputnode.max_bval"),
                ],
            ),
            (
                dwiextract_node,
                mrtrix3_tensor_wf,
                [
                    ("out_file", "inputnode.dwi_mif"),
                ],
            ),
        ]
    )
    return workflow
