from nipype.interfaces import fsl
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost.interfaces.bids import DerivativesDataSink
from kepost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)


def init_tissue_coregistration_wf(
    name: str = "tissues_coregistration",
    workflow_entities: dict = DIFFUSION_WF_OUTPUT_ENTITIES,
) -> pe.Workflow:
    """
    Initialize the coregistration workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "coregistration"

    Returns
    -------
    pe.Workflow
        The coregistration workflow
    """
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_reference",
                "t1w_preproc",
                "t1w_to_dwi_transform",
                "gm_probseg",
                "wm_probseg",
                "csf_probseg",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "gm_probseg_dwiref",
                "wm_probseg_dwiref",
                "csf_probseg_dwiref",
            ]
        ),
        name="outputnode",
    )
    # run apply transforms on both parcellations, naming them appropriately
    apply_transforms_gm = pe.Node(
        fsl.ApplyXFM(
            interp="nearestneighbour",
            apply_xfm=True,
        ),
        name="apply_transforms_gm",
    )
    apply_transforms_wm = pe.Node(
        fsl.ApplyXFM(
            interp="nearestneighbour",
            apply_xfm=True,
        ),
        name="apply_transforms_wm",
    )
    apply_transforms_csf = pe.Node(
        fsl.ApplyXFM(
            interp="nearestneighbour",
            apply_xfm=True,
        ),
        name="apply_transforms_csf",
    )
    ds_gm = pe.Node(
        interface=DerivativesDataSink(
            **workflow_entities["tissue_dwiref_probseg"],
            label="GM",
        ),
        name="ds_gm",
    )
    ds_wm = pe.Node(
        interface=DerivativesDataSink(
            **workflow_entities["tissue_dwiref_probseg"],
            label="WM",
        ),
        name="ds_wm",
    )
    ds_csf = pe.Node(
        interface=DerivativesDataSink(
            **workflow_entities["tissue_dwiref_probseg"],
            label="CSF",
        ),
        name="ds_csf",
    )
    workflow.connect(
        [
            (
                inputnode,
                apply_transforms_gm,
                [
                    ("gm_probseg", "in_file"),
                    ("dwi_reference", "reference"),
                    ("t1w_to_dwi_transform", "in_matrix_file"),
                ],
            ),
            (
                inputnode,
                apply_transforms_wm,
                [
                    ("wm_probseg", "in_file"),
                    ("dwi_reference", "reference"),
                    ("t1w_to_dwi_transform", "in_matrix_file"),
                ],
            ),
            (
                inputnode,
                apply_transforms_csf,
                [
                    ("csf_probseg", "in_file"),
                    ("dwi_reference", "reference"),
                    ("t1w_to_dwi_transform", "in_matrix_file"),
                ],
            ),
            (
                apply_transforms_gm,
                ds_gm,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                apply_transforms_wm,
                ds_wm,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                apply_transforms_csf,
                ds_csf,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_gm,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_wm,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_csf,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                ],
            ),
            (
                apply_transforms_gm,
                outputnode,
                [
                    ("out_file", "gm_probseg_dwiref"),
                ],
            ),
            (
                apply_transforms_wm,
                outputnode,
                [
                    ("out_file", "wm_probseg_dwiref"),
                ],
            ),
            (
                apply_transforms_csf,
                outputnode,
                [
                    ("out_file", "csf_probseg_dwiref"),
                ],
            ),
        ]
    )
    return workflow
