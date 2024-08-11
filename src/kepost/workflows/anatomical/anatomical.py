"""
Module for the anatomical postprocessing workflow.
"""

from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost import config
from kepost.atlases.utils import get_atlas_properties
from kepost.interfaces.reports.viz import OverlayRPT
from kepost.interfaces.utils.vis import plot_n_voxels_in_atlas
from kepost.workflows.anatomical.procedures import (
    init_derivatives_wf,
    init_five_tissue_type_wf,
    init_gm_cropping_wf,
    init_registration_wf,
)


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
                "t1w_preproc",
                "t2w_preproc",
                "t1w_mask",
                "mni_to_native_transform",
                "gm_probabilistic_segmentation",
                "probseg_threshold",
                "atlas_name",
                "subject_id",
            ]
        ),
        name="inputnode",
    )
    atlases_node = pe.Node(
        niu.IdentityInterface(fields=["atlas_name"]),
        name="atlases",
    )
    atlases_node.iterables = ("atlas_name", list(config.workflow.atlases))
    inputnode.inputs.probseg_threshold = config.workflow.gm_probseg_threshold
    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "atlas_name",
                "whole_brain_parcellation",
                "gm_cropped_parcellation",
                "five_tissue_type",
            ]
        ),
        name="outputnode",
    )
    get_atlas_info_node = pe.Node(
        niu.Function(
            input_names=["atlas"],
            output_names=["nifti", "description", "region_col", "index_col"],
            function=get_atlas_properties,
        ),
        name="get_atlas_info",
    )
    workflow.connect(
        [
            (
                inputnode,
                outputnode,
                [
                    ("atlas_name", "atlas_name"),
                ],
            ),
            (
                atlases_node,
                get_atlas_info_node,
                [
                    ("atlas_name", "atlas"),
                ],
            ),
        ]
    )

    registration_wf = init_registration_wf()
    workflow.connect(
        [
            (
                inputnode,
                registration_wf,
                [
                    ("t1w_preproc", "inputnode.t1w_preproc"),
                    (
                        "mni_to_native_transform",
                        "inputnode.mni_to_native_transform",
                    ),
                    ("atlas_name", "inputnode.atlas_name"),
                ],
            ),
            (
                get_atlas_info_node,
                registration_wf,
                [
                    ("nifti", "inputnode.atlas_nifti_file"),
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
    atlas_reg = pe.Node(interface=OverlayRPT(), name="atlas_registration_report")
    n_voxels_report = pe.Node(
        niu.Function(
            input_names=["wholebrain", "gm_cropped"],
            output_names=["out_report"],
            function=plot_n_voxels_in_atlas,
        ),
        name="n_voxels_in_atlas",
    )

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
            (
                gm_cropping_wf,
                atlas_reg,
                [("outputnode.gm_cropped_parcellation", "overlay_file")],
            ),
            (inputnode, atlas_reg, [("t1w_preproc", "background_file")]),
            (
                registration_wf,
                n_voxels_report,
                [
                    (
                        "outputnode.whole_brain_parcellation",
                        "wholebrain",
                    ),
                ],
            ),
            (
                gm_cropping_wf,
                n_voxels_report,
                [
                    (
                        "outputnode.gm_cropped_parcellation",
                        "gm_cropped",
                    ),
                ],
            ),
        ]
    )

    five_tissue_type = init_five_tissue_type_wf()
    workflow.connect(
        [
            (
                inputnode,
                five_tissue_type,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("t1w_preproc", "inputnode.t1w_preproc"),
                    ("subject_id", "inputnode.subject_id"),
                ],
            ),
            (
                five_tissue_type,
                outputnode,
                [("outputnode.five_tissue_type", "five_tissue_type")],
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
                        "t1w_preproc",
                        "inputnode.t1w_preproc",
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
                    )
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
            (
                atlas_reg,
                derivatives_wf,
                [("out_report", "inputnode.registration_report")],
            ),
            (
                n_voxels_report,
                derivatives_wf,
                [("out_report", "inputnode.n_voxels_report")],
            ),
        ]
    )
    return workflow
