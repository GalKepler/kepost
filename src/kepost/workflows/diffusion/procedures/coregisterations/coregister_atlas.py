from nipype.interfaces import fsl
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost.interfaces.bids import DerivativesDataSink
from kepost.interfaces.bids.utils import get_entity
from kepost.workflows.diffusion.descriptions.coregisterations import (
    COREGISTERATIONS_WORKFLOW_DESCRIPTION,
)
from kepost.workflows.diffusion.procedures.utils import DIFFUSION_WF_OUTPUT_ENTITIES


def init_coregistration_wf(
    name: str = "atlas_coregistration_wf",
    workflow_entities: dict = DIFFUSION_WF_OUTPUT_ENTITIES,
) -> Workflow:
    """
    Initialize the coregistration workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "coregistration"

    Returns
    -------
    Workflow
        The coregistration workflow
    """
    workflow = Workflow(name=name)
    workflow.__desc__ = COREGISTERATIONS_WORKFLOW_DESCRIPTION
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_reference",
                "t1w_preproc",
                "t1w_to_dwi_transform",
                "atlas_name",
                "whole_brain_parcellation",
                "gm_cropped_parcellation",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "whole_brain_parcellation",
                "gm_cropped_parcellation",
                "t1w_in_dwi_space",
                "dwi_brain_mask",
            ]
        ),
        name="outputnode",
    )
    get_atlas_name_node = pe.Node(
        niu.Function(
            input_names=["in_file", "entity"],
            output_names=[
                "atlas_name",
            ],
            function=get_entity,
        ),
        name="get_atlas_name",
    )
    get_atlas_name_node.inputs.entity = "atlas"
    get_atlas_den_node = pe.Node(
        niu.Function(
            input_names=["in_file", "entity"],
            output_names=[
                "atlas_den",
            ],
            function=get_entity,
        ),
        name="get_atlas_den",
    )
    get_atlas_den_node.inputs.entity = "den"
    get_atlas_div_node = pe.Node(
        niu.Function(
            input_names=["in_file", "entity"],
            output_names=[
                "atlas_division",
            ],
            function=get_entity,
        ),
        name="get_atlas_div",
    )
    get_atlas_div_node.inputs.entity = "division"

    workflow.connect(
        [
            (
                inputnode,
                get_atlas_name_node,
                [
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
            (
                inputnode,
                get_atlas_den_node,
                [
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
            (
                inputnode,
                get_atlas_div_node,
                [
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
        ]
    )
    # run apply transforms on both parcellations, naming them appropriately
    apply_transforms_wholebrain = pe.Node(
        fsl.ApplyXFM(interp="nearestneighbour", apply_xfm=True),
        name="apply_transforms_wholebrain",
    )
    apply_transforms_gm_cropped = pe.Node(
        fsl.ApplyXFM(interp="nearestneighbour", apply_xfm=True),
        name="apply_transforms_gm_cropped",
    )
    apply_transforms_t1w = pe.Node(
        fsl.ApplyXFM(
            apply_xfm=True,
        ),
        name="apply_transforms_t1w",
    )

    ds_wholebrain = pe.Node(
        interface=DerivativesDataSink(
            **workflow_entities["wholebrain_parcellation"],
        ),
        name="ds_wholebrain",
    )

    ds_gm_cropped = pe.Node(
        interface=DerivativesDataSink(
            **workflow_entities["gm_cropped_parcellation"],
        ),
        name="ds_gm_cropped",
    )
    ds_t1w = pe.Node(
        interface=DerivativesDataSink(
            **workflow_entities["t1w_in_dwi_space"],
        ),
        name="ds_t1w",
    )
    workflow.connect(
        [
            (
                inputnode,
                apply_transforms_wholebrain,
                [
                    ("whole_brain_parcellation", "in_file"),
                    ("dwi_reference", "reference"),
                    ("t1w_to_dwi_transform", "in_matrix_file"),
                ],
            ),
            (
                inputnode,
                apply_transforms_gm_cropped,
                [
                    ("gm_cropped_parcellation", "in_file"),
                    ("dwi_reference", "reference"),
                    ("t1w_to_dwi_transform", "in_matrix_file"),
                ],
            ),
            (
                inputnode,
                apply_transforms_t1w,
                [
                    ("t1w_preproc", "in_file"),
                    ("dwi_reference", "reference"),
                    ("t1w_to_dwi_transform", "in_matrix_file"),
                ],
            ),
            (
                apply_transforms_t1w,
                outputnode,
                [
                    ("out_file", "t1w_in_dwi_space"),
                ],
            ),
            (
                inputnode,
                ds_wholebrain,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                ],
            ),
            (
                get_atlas_name_node,
                ds_wholebrain,
                [
                    ("atlas_name", "atlas"),
                ],
            ),
            (
                get_atlas_den_node,
                ds_wholebrain,
                [
                    ("atlas_den", "den"),
                ],
            ),
            (
                get_atlas_div_node,
                ds_wholebrain,
                [
                    ("atlas_division", "division"),
                ],
            ),
            (
                apply_transforms_wholebrain,
                ds_wholebrain,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                ds_wholebrain,
                outputnode,
                [
                    ("out_file", "whole_brain_parcellation"),
                ],
            ),
            (
                get_atlas_name_node,
                ds_gm_cropped,
                [
                    ("atlas_name", "atlas"),
                ],
            ),
            (
                get_atlas_den_node,
                ds_gm_cropped,
                [
                    ("atlas_den", "den"),
                ],
            ),
            (
                get_atlas_div_node,
                ds_gm_cropped,
                [
                    ("atlas_division", "division"),
                ],
            ),
            (
                apply_transforms_gm_cropped,
                ds_gm_cropped,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                ds_gm_cropped,
                outputnode,
                [
                    ("out_file", "gm_cropped_parcellation"),
                ],
            ),
            (
                inputnode,
                ds_gm_cropped,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_t1w,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                ],
            ),
            (
                outputnode,
                ds_t1w,
                [
                    ("t1w_in_dwi_space", "in_file"),
                ],
            ),
        ]
    )
    return workflow
