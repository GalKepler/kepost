from nipype.interfaces import fsl
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost.interfaces import mrtrix3 as mrt


def init_5tt_coreg_wf(name="coreg_5tt_wf") -> pe.Workflow:
    """
    Workflow to perform tractography using MRtrix3.
    """
    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "dwi_reference",
                "t1w_file",
                "t1w_mask_file",
                "5tt_file",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "t1w_coreg",
                "5tt_coreg",
            ]
        ),
        name="outputnode",
    )
    apply_mask_node = pe.Node(
        fsl.ApplyMask(
            out_file="t1w_masked.nii.gz",
        ),
        name="apply_mask",
    )
    flirt_node = pe.Node(
        fsl.FLIRT(
            out_matrix_file="diff2struct.mat",
            bins=256,
            cost="normmi",
            searchr_x=[-90, 90],
            searchr_y=[-90, 90],
            searchr_z=[-90, 90],
            dof=12,
        ),
        name="flirt",
    )
    transform_convert_node = pe.Node(
        mrt.TransformConvert(
            flirt_import=True,
        ),
        name="transform_convert",
    )
    listify_node = pe.Node(
        niu.Merge(
            numinputs=2,
        ),
        name="listify",
    )
    mrtransform_node = pe.MapNode(
        mrt.MRTransform(
            inverse=True,
        ),
        name="mrtransform",
        iterfield=["in_file"],
    )

    workflow.connect(
        [
            (
                inputnode,
                apply_mask_node,
                [("t1w_file", "in_file"), ("t1w_mask_file", "mask_file")],
            ),
            (
                inputnode,
                flirt_node,
                [("dwi_reference", "in_file")],
            ),
            (
                apply_mask_node,
                flirt_node,
                [("out_file", "reference")],
            ),
            (
                inputnode,
                transform_convert_node,
                [("dwi_reference", "in_file")],
            ),
            (
                flirt_node,
                transform_convert_node,
                [("out_matrix_file", "in_matrix_file")],
            ),
            (
                apply_mask_node,
                transform_convert_node,
                [("out_file", "reference")],
            ),
            (
                inputnode,
                listify_node,
                [("5tt_file", "in1"), ("t1w_file", "in2")],
            ),
            (
                listify_node,
                mrtransform_node,
                [("out", "in_file")],
            ),
            (
                transform_convert_node,
                mrtransform_node,
                [("out_file", "linear_transform")],
            ),
        ]
    )
    return workflow
