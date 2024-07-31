import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu

from kepost import config


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
                "t1w_reference",
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
        mrt.TransformFSLConvert(
            flirt_import=True,
            nthreads=config.nipype.omp_nthreads,
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
                    ("t1w_reference", "in_file"),
                    ("dwi_reference", "reference"),
                    ("t1w_to_dwi_transform", "in_transform"),
                ],
            ),
            (
                inputnode,
                mrtransform_node,
                [("5tt_file", "in_files")],
            ),
            (
                transform_convert_node,
                mrtransform_node,
                [("out_transform", "linear_transform")],
            ),
            (
                mrtransform_node,
                outputnode,
                [("out_file", "5tt_coreg")],
            ),
        ]
    )
    return workflow
