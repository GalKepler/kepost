from nipype.interfaces import utility as niu
from nipype.interfaces.fsl import ExtractROI, ImageMaths
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost.interfaces.mrtrix3 import MRConvert


def add_gm_from_probseg(in_file: str, probseg: str, threshold: float = 0.0001):
    """
    Add the gm from the probabilistic segmentation.

    Parameters
    ----------
    in_file : str
        The input file.
    probseg : str
        The probabilistic segmentation.
    threshold : float, optional
        The threshold, by default 0.0001

    Returns
    -------
    out_file : str
        The output file.
    """
    import os

    import nibabel as nib
    from nilearn.image import resample_to_img

    in_image = nib.load(in_file)
    probseg_image = nib.load(probseg)
    probseg_image = resample_to_img(probseg_image, in_image, interpolation="nearest")
    in_data = in_image.get_fdata().astype(int)
    probseg_data = probseg_image.get_fdata() > threshold
    in_data[probseg_data] = 1
    out_image = nib.Nifti1Image(in_data, in_image.affine, in_image.header)
    out_file = os.path.abspath("gm_mask.nii.gz")
    nib.save(out_image, out_file)
    return out_file


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
                "gm_probabilistic_segmentation",
                "probseg_threshold",
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
    # add the gm from the probabilistic segmentation
    add_gm = pe.Node(
        niu.Function(
            input_names=["in_file", "probseg", "threshold"],
            output_names=["out_file"],
            function=add_gm_from_probseg,
        ),
        name="add_gm_from_probseg",
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
                inputnode,
                add_gm,
                [
                    ("gm_probabilistic_segmentation", "probseg"),
                    ("probseg_threshold", "threshold"),
                ],
            ),
            (
                fslmaths_cortical_subcortical_pathological,
                add_gm,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                add_gm,
                outputnode,
                [
                    ("out_file", "gm_mask"),
                ],
            ),
        ]
    )
    return workflow
