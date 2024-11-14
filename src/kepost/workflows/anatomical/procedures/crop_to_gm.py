from nipype.interfaces import utility as niu
from nipype.interfaces.ants import ApplyTransforms
from nipype.interfaces.fsl import ApplyMask, Threshold
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow


def init_gm_cropping_wf(
    name: str = "gm_cropping",
):
    """
    Initialize the gm cropping workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "gm_cropping"

    Returns
    -------
    workflow : nipype.pipeline.engine.Workflow
        The gm cropping workflow.
    """
    workflow = Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "gm_probabilistic_segmentation",
                "whole_brain_parcellation",
                "probseg_threshold",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "gm_cropped_parcellation",
            ]
        ),
        name="outputnode",
    )
    resample_gm = pe.Node(
        interface=ApplyTransforms(
            interpolation="NearestNeighbor",
            dimension=3,
            transforms="identity",
        ),
        name="resample_gm",
    )
    threshold = pe.Node(
        interface=Threshold(
            direction="below",
        ),
        name="threshold",
    )
    apply_mask = pe.Node(
        interface=ApplyMask(),
        name="apply_mask",
    )
    workflow.connect(
        [
            (
                inputnode,
                resample_gm,
                [
                    ("gm_probabilistic_segmentation", "input_image"),
                    ("whole_brain_parcellation", "reference_image"),
                ],
            ),
            (
                inputnode,
                threshold,
                [
                    ("probseg_threshold", "thresh"),
                ],
            ),
            (
                resample_gm,
                threshold,
                [
                    ("output_image", "in_file"),
                ],
            ),
            (
                inputnode,
                apply_mask,
                [
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
            (
                threshold,
                apply_mask,
                [
                    ("out_file", "mask_file"),
                ],
            ),
            (
                apply_mask,
                outputnode,
                [
                    ("out_file", "gm_cropped_parcellation"),
                ],
            ),
        ]
    )
    return workflow
