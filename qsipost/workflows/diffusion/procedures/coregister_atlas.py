from nipype.interfaces import utility as niu
from nipype.interfaces.ants import ApplyTransforms
from nipype.pipeline import engine as pe

from qsipost.interfaces.bids import DerivativesDataSink
from qsipost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)


def init_coregistration_wf(
    name: str = "atlas_coregistration",
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
            ]
        ),
        name="outputnode",
    )
    # run apply transforms on both parcellations, naming them appropriately
    apply_transforms_wholebrain = pe.Node(
        interface=ApplyTransforms(
            interpolation="NearestNeighbor",
            transforms="identity",
        ),
        name="apply_transforms_wholebrain",
    )
    apply_transforms_gm_cropped = pe.Node(
        interface=ApplyTransforms(
            interpolation="NearestNeighbor",
            transforms="identity",
        ),
        name="apply_transforms_gm_cropped",
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
    workflow.connect(
        [
            (
                inputnode,
                apply_transforms_wholebrain,
                [
                    ("whole_brain_parcellation", "input_image"),
                    ("dwi_reference", "reference_image"),
                ],
            ),
            (
                inputnode,
                apply_transforms_gm_cropped,
                [
                    ("gm_cropped_parcellation", "input_image"),
                    ("dwi_reference", "reference_image"),
                ],
            ),
            (
                apply_transforms_wholebrain,
                outputnode,
                [
                    ("output_image", "whole_brain_parcellation"),
                ],
            ),
            (
                apply_transforms_gm_cropped,
                outputnode,
                [
                    ("output_image", "gm_cropped_parcellation"),
                ],
            ),
            (
                inputnode,
                ds_wholebrain,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                    ("atlas_name", "atlas"),
                ],
            ),
            (
                outputnode,
                ds_wholebrain,
                [
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_gm_cropped,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                    ("atlas_name", "atlas"),
                ],
            ),
            (
                outputnode,
                ds_gm_cropped,
                [
                    ("gm_cropped_parcellation", "in_file"),
                ],
            ),
        ]
    )
    return workflow
