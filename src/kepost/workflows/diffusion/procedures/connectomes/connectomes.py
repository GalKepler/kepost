from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost.interfaces import mrtrix3 as mrt
from kepost.interfaces.bids import DerivativesDataSink
from kepost.interfaces.bids.utils import get_entity
from kepost.workflows.diffusion.procedures.connectomes.utils import COMBINATIONS


def init_connectome_wf(name: str = "connectome_wf") -> Workflow:
    """
    Workflow to generate connectomes using MRtrix3.

    Parameters
    ----------
    name : str
        Name of the workflow.

    Returns
    -------
    workflow : Workflow
        Workflow object.
    """
    workflow = Workflow(name=name)
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
    get_atlas_den_node = pe.Node(
        niu.Function(
            input_names=["in_file", "entity"],
            output_names=[
                "atlas_den",
            ],
            function=get_entity,
        ),
        name="get_atlas_den",
    )
    get_atlas_den_node.inputs.entity = "den"
    get_atlas_div_node = pe.Node(
        niu.Function(
            input_names=["in_file", "entity"],
            output_names=[
                "atlas_division",
            ],
            function=get_entity,
        ),
        name="get_atlas_div",
    )
    get_atlas_div_node.inputs.entity = "division"

    workflow.connect(
        [
            (
                inputnode,
                get_atlas_name_node,
                [
                    ("atlas_nifti", "in_file"),
                ],
            ),
            (
                inputnode,
                get_atlas_den_node,
                [
                    ("atlas_nifti", "in_file"),
                ],
            ),
            (
                inputnode,
                get_atlas_div_node,
                [
                    ("atlas_nifti", "in_file"),
                ],
            ),
        ]
    )

    fields = []
    for combination in COMBINATIONS:
        in_tracts, scale, metric = (
            combination["in_tracts"],
            combination["scale"],
            combination["stat_edge"],
        )
        fields.append(f"connectome_scale-{scale}_metric-{metric}_in-tracts-{in_tracts}")
        fields.append(
            f"assignments_scale-{scale}_metric-{metric}_in-tracts-{in_tracts}"
        )
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=fields + ["atlas_name", "atlas_den", "atlas_division"]
        ),
        name="outputnode",
    )

    workflow.connect(
        [
            (
                get_atlas_name_node,
                outputnode,
                [("atlas_name", "atlas")],
            ),
            (
                get_atlas_den_node,
                outputnode,
                [("atlas_den", "den")],
            ),
            (
                get_atlas_div_node,
                outputnode,
                [("atlas_division", "division")],
            ),
        ]
    )
    for combination in COMBINATIONS:
        in_tracts, scale, metric = (
            combination["in_tracts"],
            combination["scale"],
            combination["stat_edge"],
        )
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
                dismiss_entities=["desc"],
                reconstruction_software="mrtrix3",
                filter="SIFT2" if "unsifted" in in_tracts else "SIFT",  # type: ignore[operator]
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
                dismiss_entities=["desc"],
                reconstruction_software="mrtrix3",
                filter="SIFT2" if "unsifted" in in_tracts else "SIFT",  # type: ignore[operator]
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
                    get_atlas_den_node,
                    ds_connectome,
                    [
                        ("atlas_den", "den"),
                    ],
                ),
                (
                    get_atlas_div_node,
                    ds_connectome,
                    [
                        ("atlas_division", "division"),
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
                    get_atlas_den_node,
                    ds_assignments,
                    [
                        ("atlas_den", "den"),
                    ],
                ),
                (
                    get_atlas_div_node,
                    ds_assignments,
                    [
                        ("atlas_division", "division"),
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
        if "unsifted" in in_tracts:  # type: ignore[operator]
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
