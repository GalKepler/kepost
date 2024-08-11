import nipype.interfaces.utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost.interfaces.bids import DerivativesDataSink
from kepost.workflows.diffusion.procedures.quality_control.utils import parse_eddyqc
from kepost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)


def init_eddyqc_wf(name: str = "eddyqc_wf"):
    """
    Initialize the eddy quality control workflow
    """
    workflow = Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "source_file",
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

    ds_eddyqc = pe.Node(
        DerivativesDataSink(
            **DIFFUSION_WF_OUTPUT_ENTITIES["eddy_qc"],
        ),
        name="ds_eddyqc",
    )

    workflow.connect(
        [
            (inputnode, eddyqc_node, [("eddy_qc", "eddyqc_dir")]),
            (eddyqc_node, outputnode, [("eddyqc_report", "eddy_qc_report")]),
            (
                inputnode,
                ds_eddyqc,
                [("source_file", "source_file"), ("base_directory", "base_directory")],
            ),
            (eddyqc_node, ds_eddyqc, [("eddyqc_report", "in_file")]),
        ]
    )

    return workflow
