import nipype.interfaces.utility as niu
from nipype.pipeline import engine as pe

from kepost.workflows.diffusion.procedures.quality_control.utils import parse_eddyqc


def init_eddyqc_wf(name: str = "eddyqc_wf"):
    """
    Initialize the eddy quality control workflow
    """
    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "eddy_qc",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["eddy_qc_report", "strip_score"]),
        name="outputnode",
    )

    eddyqc_node = pe.Node(
        niu.Function(
            input_names=["eddyqc_dir"],
            output_names="eddyqc_report",
            function=parse_eddyqc,
        ),
        name="eddyqc_node",
    )
    workflow.connect(
        [
            (inputnode, eddyqc_node, [("eddy_qc", "eddyqc_dir")]),
            (eddyqc_node, outputnode, [("eddyqc_report", "eddy_qc_report")]),
        ]
    )

    return workflow
