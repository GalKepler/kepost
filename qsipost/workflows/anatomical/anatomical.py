from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from qsipost.workflows.anatomical.procedures.derivatives import init_derivatives_wf


def init_anatomical_wf(
    name: str = "anatomical_postprocess",
    probseg_threshold: float = 0.01,
):
    """
    Initialize the anatomical postprocessing workflow.

    Parameters
    ----------
    parcellation_atlas : Atlas
        The parcellation atlas.
    probseg_threshold : float, optional
        The threshold for the probabilistic segmentation, by default 0.01
    name : str, optional
        The name of the workflow, by default "anatomical_postprocess"
    """
    from qsipost.workflows.anatomical.procedures.crop_to_gm import init_gm_cropping_wf
    from qsipost.workflows.anatomical.procedures.register_atlas import (
        init_registration_wf,
    )

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
            ]
        ),
        name="inputnode",
    )
    inputnode.inputs.probseg_threshold = probseg_threshold
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
