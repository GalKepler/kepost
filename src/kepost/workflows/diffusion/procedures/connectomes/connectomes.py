from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost.interfaces import mrtrix3 as mrt
from kepost.interfaces.bids import DerivativesDataSink
from kepost.interfaces.bids.utils import get_entity
from kepost.workflows.diffusion.procedures.connectomes.utils import COMBINATIONS


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
                "atlas_nifti",
                "tracts_sifted",
                "tracts_unsifted",
                "atlas_name",
                "tck_weights",
            ]
        ),
        name="inputnode",
    )
    fields = []
    for in_tracts in ["tracts_sifted", "tracts_unsifted"]:
        for combination in COMBINATIONS:
            scale, metric = combination["scale"], combination["stat_edge"]
            fields.append(
                f"connectome_scale-{scale}_metric-{metric}_in-tracts-{in_tracts}"
            )
            fields.append(
                f"assignments_scale-{scale}_metric-{metric}_in-tracts-{in_tracts}"
            )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=fields + ["atlas_name"]),
        name="outputnode",
    )
    get_atlas_name_node = pe.Node(
        niu.Function(
            input_names=["in_file", "entity"],
            output_names=[
                "atlas_name",
            ],
            function=get_entity,
        ),
        name="get_atlas_name",
    )
    get_atlas_name_node.inputs.entity = "atlas"
    get_reconstruction_software = pe.Node(
        niu.Function(
            function=get_entity,
            input_names=["in_file", "entity"],
            output_names=["reconstruction_software"],
        ),
        name="get_reconstruction_software",
    )
    get_reconstruction_software.inputs.entity = "reconstruction"
    workflow.connect(
        [
            (
                inputnode,
                get_atlas_name_node,
                [("atlas_nifti", "in_file")],
            ),
            (
                inputnode,
                get_reconstruction_software,
                [("tracts_unsifted", "in_file")],
            ),
            (
                get_atlas_name_node,
                outputnode,
                [("atlas_name", "atlas_name")],
            ),
        ]
    )
    for in_tracts in ["tracts_sifted", "tracts_unsifted"]:
        for combination in COMBINATIONS:
            scale, metric = combination["scale"], combination["stat_edge"]
            connectome = pe.Node(
                mrt.BuildConnectome(
                    stat_edge=metric,
                    out_assignments="assignments.csv",
                ),
                name=f"connectome_scale-{scale}_metric-{metric}_in-tracts-{in_tracts}",
            )
            if scale is not None:
                connectome.inputs.scale = scale
            ds_connectome = pe.Node(
                DerivativesDataSink(
                    suffix="connectome",
                    scale=scale if scale is not None else "raw",
                    measure=metric,
                    subtype="connectomes",
                    extension=".csv",
                    weight="SIFT2" if "unsifted" in in_tracts else "SIFT",
                ),
                name=f"ds_connectome_scale-{scale}_metric-{metric}_in-tracts-{in_tracts}",
                run_without_submitting=True,
            )
            ds_assignments = pe.Node(
                DerivativesDataSink(
                    suffix="assignments",
                    scale=scale,
                    measure=metric,
                    subtype="connectomes",
                    extension=".csv",
                    weight="SIFT2" if "unsifted" in in_tracts else "SIFT",
                ),
                name=f"ds_assignments_scale-{scale}_metric-{metric}_in-tracts-{in_tracts}",
                run_without_submitting=True,
            )
            workflow.connect(
                [
                    (
                        inputnode,
                        connectome,
                        [
                            (in_tracts, "in_tracts"),
                            ("atlas_nifti", "in_nodes"),
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
                            ("tracts_unsifted", "source_file"),
                        ],
                    ),
                    (
                        get_atlas_name_node,
                        ds_connectome,
                        [
                            ("atlas_name", "atlas"),
                        ],
                    ),
                    (
                        get_reconstruction_software,
                        ds_connectome,
                        [
                            ("reconstruction_software", "reconstruction_software"),
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
                            ("tracts_unsifted", "source_file"),
                        ],
                    ),
                    (
                        get_atlas_name_node,
                        ds_assignments,
                        [
                            ("atlas_name", "atlas"),
                        ],
                    ),
                    (
                        get_reconstruction_software,
                        ds_assignments,
                        [
                            ("reconstruction_software", "reconstruction_software"),
                        ],
                    ),
                    (
                        connectome,
                        outputnode,
                        [
                            (
                                "out_connectome",
                                f"out_scale-{scale}_metric-{metric}_in-tracts-{in_tracts}",
                            ),
                        ],
                    ),
                ]
            )
            if "unsifted" in in_tracts:
                workflow.connect(
                    [
                        (
                            inputnode,
                            connectome,
                            [
                                ("tck_weights", "tck_weights_in"),
                            ],
                        ),
                    ]
                )
    return workflow