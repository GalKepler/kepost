from neuromaps import datasets
from nipype.interfaces import ants, fsl
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost import config
from kepost.interfaces.bids import DerivativesDataSink
from kepost.interfaces.bids.utils import gen_acq_label
from kepost.interfaces.dipy import ReconstDTI
from kepost.workflows.diffusion.procedures.tensor_estimations.dipy.utils import (
    estimate_sigma,
)
from kepost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)

TENSOR_PARAMETERS = ["fa", "ga", "md", "ad", "rd", "mode"]


def init_dipy_tensor_wf(
    name: str = "dipy_tensor_wf",
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
                "dwi_mask",
                "dwi_bzero",
                "fit_method",
                "source_file",
                "max_bval",
                "native_to_mni_transform",
                "dwi_to_t1w_transform",
                "t1w_reference",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        interface=niu.IdentityInterface(fields=TENSOR_PARAMETERS),
        name="outputnode",
    )
    acq_label = pe.Node(
        niu.Function(
            input_names=["max_bval"],
            output_names=["acq_label"],
            function=gen_acq_label,
        ),
        name="acq_label",
    )
    tensor_wf = pe.Node(interface=ReconstDTI(), name="dipy_tensor_wf")
    listify_tensor_params = pe.Node(
        interface=niu.Merge(numinputs=len(TENSOR_PARAMETERS)),
        name="listify_tensor_params",
    )

    ds_tensor_wf = pe.MapNode(
        interface=DerivativesDataSink(  # type: ignore[arg-type]
            **DIFFUSION_WF_OUTPUT_ENTITIES.get("dti_derived_parameters"),
            reconstruction_software="dipy",
            save_meta=False,
        ),
        iterfield=["in_file", "desc"],
        name="ds_tensor_wf",
    )
    ds_tensor_wf.inputs.desc = TENSOR_PARAMETERS

    if config.workflow.dipy_reconstruction_method.lower() in ["rt", "restore"]:
        estimate_sigma_node = pe.Node(
            niu.Function(
                input_names=["in_file", "in_mask"],
                output_names=["sigma"],
                function=estimate_sigma,
            ),
            name="estimate_sigma",
        )
        workflow.connect(
            [
                (
                    inputnode,
                    estimate_sigma_node,
                    [("dwi_bzero", "in_file"), ("dwi_mask", "in_mask")],
                ),
                (
                    estimate_sigma_node,
                    tensor_wf,
                    [("sigma", "sigma")],
                ),
            ]
        )

    # Coregistrations
    coregister_tensor_wf = pe.MapNode(
        fsl.ApplyXFM(
            apply_xfm=True,
        ),
        iterfield=["in_file"],
        name="corgister_tensor_wf",
    )

    coreg_tensor_ds_entities = DIFFUSION_WF_OUTPUT_ENTITIES.get(  # type: ignore[union-attr]
        "dti_derived_parameters"
    ).copy()
    coreg_tensor_ds_entities.update({"space": "T1w"})
    ds_coreg_tensor_wf = pe.MapNode(
        interface=DerivativesDataSink(
            **coreg_tensor_ds_entities,
            reconstruction_software="dipy",
            save_meta=False,
        ),
        iterfield=["in_file", "desc"],
        name="ds_coreg_tensor_wf",
    )
    ds_coreg_tensor_wf.inputs.desc = TENSOR_PARAMETERS

    normalize_tensor_wf = pe.MapNode(
        ants.ApplyTransforms(
            reference_image=datasets.fetch_atlas(atlas="mni", density="1mm").get(
                "2009cAsym_T1w"
            ),
        ),
        iterfield=["input_image"],
        name="normalize_tensor_wf",
    )
    ds_tensor_mni_wf = pe.MapNode(
        interface=DerivativesDataSink(  # type: ignore[arg-type]
            **DIFFUSION_WF_OUTPUT_ENTITIES.get("dti_derived_parameters"),
            reconstruction_software="dipy",
            space="MNI152NLin2009cAsym",
            save_meta=False,
        ),
        iterfield=["in_file", "desc"],
        name="ds_tensor_mni_wf",
    )
    ds_tensor_mni_wf.inputs.desc = TENSOR_PARAMETERS

    workflow.connect(
        [
            (
                inputnode,
                acq_label,
                [("max_bval", "max_bval")],
            ),
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
                    ("source_file", "source_file"),
                ],
            ),
            (acq_label, ds_tensor_wf, [("acq_label", "acquisition")]),
            (
                listify_tensor_params,
                coregister_tensor_wf,
                [("out", "in_file")],
            ),
            (
                inputnode,
                coregister_tensor_wf,
                [
                    ("dwi_to_t1w_transform", "in_matrix_file"),
                    ("t1w_reference", "reference"),
                ],
            ),
            (
                coregister_tensor_wf,
                ds_coreg_tensor_wf,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (acq_label, ds_coreg_tensor_wf, [("acq_label", "acquisition")]),
            (
                inputnode,
                ds_coreg_tensor_wf,
                [
                    ("base_directory", "base_directory"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                normalize_tensor_wf,
                [
                    ("native_to_mni_transform", "transforms"),
                ],
            ),
            (
                inputnode,
                ds_tensor_mni_wf,
                [
                    ("base_directory", "base_directory"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                normalize_tensor_wf,
                ds_tensor_mni_wf,
                [
                    ("output_image", "in_file"),
                ],
            ),
            (acq_label, ds_tensor_mni_wf, [("acq_label", "acquisition")]),
            (
                coregister_tensor_wf,
                normalize_tensor_wf,
                [
                    ("out_file", "input_image"),
                ],
            ),
        ]
    )
    return workflow
