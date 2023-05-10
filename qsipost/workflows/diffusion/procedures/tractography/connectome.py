from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from qsipost import config
from qsipost.interfaces import mrtrix3 as mrt
from qsipost.interfaces.bids import DerivativesDataSink

SCALES = ["length", "invlength", "invnodevol", None]
METRICS = ["sum", "mean", "min", "max"]
COMBINATIONS = [(scale, metric) for scale in SCALES for metric in METRICS]


def init_connectome_wf(name: str = "connectome_wf") -> pe.Workflow:
    """
    Workflow to generate connectomes using MRtrix3.

    Parameters
    ----------
    name : str
        Name of the workflow.

    Returns
    -------
    workflow : pe.Workflow
        Workflow object.
    """
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "atlas_name",
                "in_tracts",
                "in_parc",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                f"out_scale-{scale}_metric-{metric}_connectome"
                for scale, metric in COMBINATIONS
            ]
            + [
                f"out_scale-{scale}_metric-{metric}_assignments"
                for scale, metric in COMBINATIONS
            ]
        ),
        name="outputnode",
    )
    for scale, metric in COMBINATIONS:
        connectome = pe.Node(
            mrt.BuildConnectome(
                stat_edge=metric,
                out_assignments="assignments.csv",
            ),
            name=f"connectome_scale-{scale}_metric-{metric}",
        )
        if scale is not None:
            connectome.inputs.scale = scale
        ds_connectome = pe.Node(
            DerivativesDataSink(
                suffix="connectome",
                desc=scale if scale is not None else "raw",
                measure=metric,
                extension=".csv",
            ),
            name=f"ds_connectome_scale-{scale}_metric-{metric}",
            run_without_submitting=True,
        )
        ds_assignments = pe.Node(
            DerivativesDataSink(
                suffix="assignments",
                desc=scale,
                measure=metric,
                extension=".csv",
            ),
            name=f"ds_assignments_scale-{scale}_metric-{metric}",
            run_without_submitting=True,
        )
        workflow.connect(
            [
                (
                    inputnode,
                    connectome,
                    [
                        ("in_tracts", "in_tracts"),
                        ("in_parc", "in_nodes"),
                    ],
                ),
                (
                    connectome,
                    ds_connectome,
                    [("out_connectome", "in_file")],
                ),
                (
                    inputnode,
                    ds_connectome,
                    [
                        ("base_directory", "base_directory"),
                        ("in_tracts", "source_file"),
                        ("atlas_name", "atlas"),
                    ],
                ),
                (
                    connectome,
                    ds_assignments,
                    [("out_assignments", "in_file")],
                ),
                (
                    inputnode,
                    ds_assignments,
                    [
                        ("base_directory", "base_directory"),
                        ("in_tracts", "source_file"),
                        ("atlas_name", "atlas"),
                    ],
                ),
                (
                    connectome,
                    outputnode,
                    [
                        (
                            "out_connectome",
                            f"out_scale-{scale}_metric-{metric}",
                        ),
                    ],
                ),
            ]
        )
    return workflow
