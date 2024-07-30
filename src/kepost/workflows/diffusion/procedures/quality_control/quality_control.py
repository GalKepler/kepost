import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu

from kepost.workflows.diffusion.procedures.quality_control.eddy_qc import init_eddyqc_wf
from kepost.workflows.diffusion.procedures.quality_control.snr import init_snr_wf


def init_qc_wf(name: str = "qc_wf"):
    """
    Initialize the quality control workflow
    """
    qc_wf = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_file",
                "dwi_grad",
                "dwi_bval",
                "brain_mask",
                "eddy_qc",
                "gm_probseg",
                "wm_probseg",
                "csf_probseg",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["snr_file"]),
        name="outputnode",
    )

    snr_wf = init_snr_wf()
    qc_wf.connect(
        [
            (inputnode, snr_wf, [("dwi_file", "inputnode.dwi_file")]),
            (inputnode, snr_wf, [("dwi_grad", "inputnode.dwi_grad")]),
            (inputnode, snr_wf, [("dwi_bval", "inputnode.dwi_bval")]),
            (inputnode, snr_wf, [("brain_mask", "inputnode.brain_mask")]),
            (inputnode, snr_wf, [("base_directory", "inputnode.base_directory")]),
            (inputnode, snr_wf, [("gm_probseg", "inputnode.gm_probseg")]),
            (inputnode, snr_wf, [("wm_probseg", "inputnode.wm_probseg")]),
            (inputnode, snr_wf, [("csf_probseg", "inputnode.csf_probseg")]),
            (snr_wf, outputnode, [("outputnode.qc_report", "snr_file")]),
        ]
    )
    eddyqc_wf = init_eddyqc_wf()
    qc_wf.connect(
        [
            (
                inputnode,
                eddyqc_wf,
                [
                    ("eddy_qc", "inputnode.eddy_qc"),
                    ("dwi_file", "inputnode.source_file"),
                    ("base_directory", "inputnode.base_directory"),
                ],
            )
        ]
    )
    return qc_wf
