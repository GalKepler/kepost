from nipype.interfaces import utility as niu
from nipype.interfaces.ants import ApplyTransforms
from nipype.pipeline import engine as pe

from kepost.interfaces.reports.viz import AtlasRegRPT


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
    workflow = pe.Workflow(name=name)
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
        interface=niu.IdentityInterface(
            fields=["whole_brain_parcellation", "registration_report"]
        ),
        name="outputnode",
    )
    apply_transforms = pe.Node(
        interface=ApplyTransforms(
            interpolation="NearestNeighbor",
            dimension=3,
        ),
        name="apply_transforms",
    )
    atlas_reg = pe.Node(interface=AtlasRegRPT(), name="atlas_registration_report")

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
            (inputnode, atlas_reg, [("t1w_preproc", "background_file")]),
            (apply_transforms, atlas_reg, [("output_image", "atlas_file")]),
            (atlas_reg, outputnode, [("out_report", "registration_report")]),
        ]
    )
    return workflow
