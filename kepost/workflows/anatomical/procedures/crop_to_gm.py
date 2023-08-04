from nipype.interfaces import utility as niu
from nipype.interfaces.fsl import ApplyMask, Threshold
from nipype.pipeline import engine as pe


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
    workflow = pe.Workflow(name=name)
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
                threshold,
                [
                    ("gm_probabilistic_segmentation", "in_file"),
                    ("probseg_threshold", "thresh"),
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
