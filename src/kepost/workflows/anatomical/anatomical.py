"""
Module for the anatomical postprocessing workflow.
"""

from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost import config
from kepost.workflows.anatomical.procedures.crop_to_gm import init_gm_cropping_wf
from kepost.workflows.anatomical.procedures.derivatives import init_derivatives_wf
from kepost.workflows.anatomical.procedures.register_atlas import init_registration_wf


def init_anatomical_wf(
    name: str = "anatomical_postprocess",
):
    """
    Initialize the anatomical postprocessing workflow.
    """

    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "base_directory",
                "anatomical_reference",
                "mni_to_native_transform",
                "gm_probabilistic_segmentation",
                "probseg_threshold",
                "atlas_name",
                "atlas_nifti_file",
                "subject_id",
                "freesurfer_dir",
            ]
        ),
        name="inputnode",
    )
    inputnode.inputs.probseg_threshold = config.workflow.gm_probseg_threshold
    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "whole_brain_parcellation",
                "gm_cropped_parcellation",
            ]
        ),
        name="outputnode",
    )

    registration_wf = init_registration_wf()
    workflow.connect(
        [
            (
                inputnode,
                registration_wf,
                [
                    ("anatomical_reference", "inputnode.anatomical_reference"),
                    (
                        "mni_to_native_transform",
                        "inputnode.mni_to_native_transform",
                    ),
                    ("atlas_name", "inputnode.atlas_name"),
                    ("atlas_nifti_file", "inputnode.atlas_nifti_file"),
                ],
            ),
            (
                registration_wf,
                outputnode,
                [
                    (
                        "outputnode.whole_brain_parcellation",
                        "whole_brain_parcellation",
                    ),
                ],
            ),
        ]
    )
    gm_cropping_wf = init_gm_cropping_wf()
    workflow.connect(
        [
            (
                inputnode,
                gm_cropping_wf,
                [
                    (
                        "gm_probabilistic_segmentation",
                        "inputnode.gm_probabilistic_segmentation",
                    ),
                    ("probseg_threshold", "inputnode.probseg_threshold"),
                ],
            ),
            (
                registration_wf,
                gm_cropping_wf,
                [
                    (
                        "outputnode.whole_brain_parcellation",
                        "inputnode.whole_brain_parcellation",
                    )
                ],
            ),
            (
                gm_cropping_wf,
                outputnode,
                [
                    (
                        "outputnode.gm_cropped_parcellation",
                        "gm_cropped_parcellation",
                    ),
                ],
            ),
        ]
    )
    derivatives_wf = init_derivatives_wf()
    workflow.connect(
        [
            (
                inputnode,
                derivatives_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    (
                        "anatomical_reference",
                        "inputnode.anatomical_reference",
                    ),
                    ("atlas_name", "inputnode.atlas_name"),
                ],
            ),
            (
                registration_wf,
                derivatives_wf,
                [
                    (
                        "outputnode.whole_brain_parcellation",
                        "inputnode.whole_brain_parcellation",
                    ),
                ],
            ),
            (
                gm_cropping_wf,
                derivatives_wf,
                [
                    (
                        "outputnode.gm_cropped_parcellation",
                        "inputnode.gm_cropped_parcellation",
                    ),
                ],
            ),
        ]
    )
    return workflow
