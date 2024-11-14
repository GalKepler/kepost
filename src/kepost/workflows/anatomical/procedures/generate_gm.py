from nipype.interfaces import utility as niu
from nipype.interfaces.fsl import ExtractROI, ImageMaths
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost.interfaces.mrtrix3 import MRConvert


def init_gm_from_5tt_wf(name: str = "gm_from_5tt"):
    """
    Initialize the gm from 5tt workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "gm_from_5tt"

    Returns
    -------
    workflow : nipype.pipeline.engine.Workflow
        The gm from 5tt workflow.
    """
    workflow = Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "five_tissue_type",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "gm_mask",
            ]
        ),
        name="outputnode",
    )
    mrconvert = pe.Node(
        interface=MRConvert(
            out_file="five_tissue_type.nii.gz",
        ),
        name="mrconvert",
    )
    fslroi_cortical_gm = pe.Node(
        interface=ExtractROI(
            t_min=0,
            t_size=1,
        ),
        name="fslroi_cortical_gm",
    )
    fslroi_subcortical_gm = pe.Node(
        interface=ExtractROI(
            t_min=1,
            t_size=1,
        ),
        name="fslroi_subcortical_gm",
    )
    fslroi_pathological_gm = pe.Node(
        interface=ExtractROI(
            t_min=4,
            t_size=1,
        ),
        name="fslroi_pathological_gm",
    )
    fslmaths_cortical_subcortical = pe.Node(
        interface=ImageMaths(
            op_string="-add",
        ),
        name="fslmaths_cortical_subcortical",
    )
    fslmaths_cortical_subcortical_pathological = pe.Node(
        interface=ImageMaths(
            op_string="-add",
        ),
        name="fslmaths_cortical_subcortical_pathological",
    )
    workflow.connect(
        [
            (
                inputnode,
                mrconvert,
                [
                    ("five_tissue_type", "in_file"),
                ],
            ),
            (
                mrconvert,
                fslroi_cortical_gm,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                mrconvert,
                fslroi_subcortical_gm,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                mrconvert,
                fslroi_pathological_gm,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                fslroi_cortical_gm,
                fslmaths_cortical_subcortical,
                [
                    ("roi_file", "in_file"),
                ],
            ),
            (
                fslroi_subcortical_gm,
                fslmaths_cortical_subcortical,
                [
                    ("roi_file", "in_file2"),
                ],
            ),
            (
                fslroi_pathological_gm,
                fslmaths_cortical_subcortical_pathological,
                [
                    ("roi_file", "in_file"),
                ],
            ),
            (
                fslmaths_cortical_subcortical,
                fslmaths_cortical_subcortical_pathological,
                [
                    ("out_file", "in_file2"),
                ],
            ),
            (
                fslmaths_cortical_subcortical_pathological,
                outputnode,
                [
                    ("out_file", "gm_mask"),
                ],
            ),
        ]
    )
    return workflow
