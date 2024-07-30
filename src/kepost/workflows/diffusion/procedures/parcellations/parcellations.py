from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost.interfaces.bids import DerivativesDataSink
from kepost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)


def parcellate_all_measures(in_file: str, atlas_nifti: str):
    """
    Parcellate the brain using a specific atlas

    Parameters
    ----------
    in_file : str
        The input file
    atlas_name : str
        The atlas name
    """
    import os

    import pandas as pd
    from bids.layout import parse_file_entities

    from kepost.atlases.utils import get_atlas_properties, parcellate
    from kepost.workflows.diffusion.procedures.parcellations.available_measures import (
        AVAILABLE_MEASURES,
    )

    atlas_name = parse_file_entities(atlas_nifti)["atlas"]
    _, description, region_col, index_col = get_atlas_properties(atlas_name)
    df = pd.read_csv(description, index_col=index_col).copy()
    for measure_name, measure_func in AVAILABLE_MEASURES.items():
        df[measure_name] = parcellate(
            atlas_description=description,
            index_col=index_col,
            atlas_nifti=atlas_nifti,
            region_col=region_col,
            metric_image=in_file,
            measure=measure_func,  # type: ignore[arg-type]
        )["value"]
    out_file = f"{os.getcwd()}/parcellations.pkl"
    df.to_pickle(out_file)
    return out_file, atlas_name


def init_parcellations_wf(
    inputs: list, software: str, name: str = "parcellations_wf"
) -> pe.Workflow:
    """
    Workflow to parcellate the brain
    """
    workflow = pe.Workflow(name=f"{software}_{name}")
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "acq_label",
                "source_file",
                "atlas_name",
                "atlas_nifti",
            ]
            + inputs
        ),
        name="inputnode",
    )

    parcellate_node = pe.MapNode(
        niu.Function(
            input_names=["in_file", "atlas_nifti"],
            output_names=["out_file", "atlas_name"],
            function=parcellate_all_measures,
        ),
        name="parcellate_node",
        iterfield=["in_file"],
    )
    listify_inputs_node = pe.Node(
        niu.Merge(len(inputs), ravel_inputs=True),
        name="listify_inputs_node",
    )
    ds_parcellation_node = pe.MapNode(
        DerivativesDataSink(  # type: ignore[arg-type]
            **DIFFUSION_WF_OUTPUT_ENTITIES.get("parcellations"),
        ),
        iterfield=["in_file", "desc"],
        name="ds_parcellation_node",
    )
    ds_parcellation_node.inputs.desc = inputs
    ds_parcellation_node.inputs.reconstruction_software = software
    select_node = pe.Node(
        niu.Select(index=[0]),
        name="select_node",
    )
    workflow.connect(
        [
            (
                inputnode,
                listify_inputs_node,
                [(p, f"in{i}") for i, p in enumerate(inputs)],
            ),
            (listify_inputs_node, parcellate_node, [("out", "in_file")]),
            (
                inputnode,
                parcellate_node,
                [("atlas_nifti", "atlas_nifti")],
            ),
            (
                parcellate_node,
                ds_parcellation_node,
                [("atlas_name", "atlas")],
            ),
            (
                parcellate_node,
                select_node,
                [("out_file", "inlist")],
            ),
            (
                select_node,
                ds_parcellation_node,
                [("out", "in_file")],
            ),
            (inputnode, ds_parcellation_node, [("acq_label", "acquisition")]),
        ]
    )

    return workflow
