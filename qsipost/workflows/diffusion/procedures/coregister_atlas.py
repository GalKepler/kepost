from nipype.interfaces import utility as niu
from nipype.interfaces.ants import ApplyTransforms
from nipype.pipeline import engine as pe


def init_coregistration_wf(
    name: str = "atlas_coregistration",
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
                "dwi_reference",
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
        ]
    )
    return workflow
