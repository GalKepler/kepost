from nipype.interfaces import utility as niu
from nipype.interfaces.ants import ApplyTransforms
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow


def init_registration_wf(
    name: str = "atlas_registration",
):
    """
    Initialize the registration workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "registration"
    """
    workflow = Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "t1w_preproc",
                "mni_to_native_transform",
                "atlas_name",
                "atlas_nifti_file",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        interface=niu.IdentityInterface(fields=["whole_brain_parcellation"]),
        name="outputnode",
    )
    apply_transforms = pe.Node(
        interface=ApplyTransforms(
            interpolation="NearestNeighbor",
            dimension=3,
        ),
        name="apply_transforms",
    )

    workflow.connect(
        [
            (
                inputnode,
                apply_transforms,
                [
                    ("atlas_nifti_file", "input_image"),
                    ("mni_to_native_transform", "transforms"),
                    ("t1w_preproc", "reference_image"),
                ],
            ),
            (
                apply_transforms,
                outputnode,
                [
                    ("output_image", "whole_brain_parcellation"),
                ],
            ),
        ]
    )
    return workflow
