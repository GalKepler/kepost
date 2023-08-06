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
                "t1w_to_dwi_transform",
                "t1w_file",
                "5tt_file",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "5tt_coreg",
            ]
        ),
        name="outputnode",
    )
    transform_convert_node = pe.Node(
        mrt.TransformConvert(
            flirt_import=True,
        ),
        name="transform_convert",
    )
    mrtransform_node = pe.Node(
        mrt.MRTransform(
            # inverse=True,
        ),
        name="mrtransform",
    )

    workflow.connect(
        [
            (
                inputnode,
                transform_convert_node,
                [
                    ("t1w_file", "in_file"),
                    ("dwi_reference", "reference"),
                    ("t1w_to_dwi_transform", "in_matrix_file"),
                ],
            ),
            (
                inputnode,
                mrtransform_node,
                [("5tt_file", "in_file")],
            ),
            (
                transform_convert_node,
                mrtransform_node,
                [("out_file", "linear_transform")],
            ),
            (
                mrtransform_node,
                outputnode,
                [("out_file", "5tt_coreg")],
            ),
        ]
    )
    return workflow
