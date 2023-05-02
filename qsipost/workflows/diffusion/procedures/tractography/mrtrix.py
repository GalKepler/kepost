from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from qsipost.interfaces import mrtrix3 as mrt
from qsipost.workflows.diffusion.procedures.tractography.coregisteration import (
    init_5tt_coreg_wf,
)


def init_mrtrix_tractography_wf(name="mrtrix_tractography_wf") -> pe.Workflow:
    """
    Workflow to perform tractography using MRtrix3.
    """
    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "dwi_file",
                "dwi_reference",
                "dwi_grad",
                "dwi_mask_file",
                "t1w_file",
                "t1w_mask_file",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "tck_file",
            ]
        ),
        name="outputnode",
    )
    dwi2response_node = pe.Node(
        mrt.ResponseSD(
            algorithm="dhollander",
            wm_file="wm.txt",
            gm_file="gm.txt",
            csf_file="csf.txt",
            voxels_file="voxels.mif",
        ),
        name="dwi2response",
    )
    dwi2fod_node = pe.Node(
        mrt.EstimateFOD(
            algorithm="msmt_csd",
        ),
        name="dwi2fod",
    )
    gen_5tt_node = pe.Node(
        mrt.Generate5tt(
            algorithm="fsl",
        ),
        name="gen_5tt",
    )
    coreg_wf = init_5tt_coreg_wf()
    workflow.connect(
        [
            (
                inputnode,
                dwi2response_node,
                [
                    ("dwi_file", "in_file"),
                    ("dwi_grad", "grad_file"),
                    ("dwi_mask_file", "in_mask"),
                ],
            ),
            (
                inputnode,
                dwi2fod_node,
                [
                    ("dwi_file", "in_file"),
                    ("dwi_grad", "grad_file"),
                    ("dwi_mask_file", "in_mask"),
                ],
            ),
            (
                dwi2response_node,
                dwi2fod_node,
                [
                    ("wm_file", "wm_txt"),
                    ("gm_file", "gm_txt"),
                    ("csf_file", "csf_txt"),
                ],
            ),
            (
                inputnode,
                gen_5tt_node,
                [
                    ("t1w_file", "in_file"),
                    ("t1w_mask_file", "in_mask"),
                ],
            ),
            (
                inputnode,
                coreg_wf,
                [
                    ("dwi_reference", "inputnode.dwi_reference"),
                    ("t1w_file", "inputnode.t1w_file"),
                    ("t1w_mask_file", "inputnode.t1w_mask_file"),
                ],
            ),
            (
                gen_5tt_node,
                coreg_wf,
                [
                    ("out_file", "inputnode.5tt_file"),
                ],
            ),
        ]
    )
    return workflow
