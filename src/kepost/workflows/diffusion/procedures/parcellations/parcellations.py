from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

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
    from pathlib import Path

    import pandas as pd
    from bids.layout import parse_file_entities

    from kepost.atlases.utils import get_atlas_properties, parcellate
    from kepost.workflows.diffusion.procedures.parcellations.available_measures import (
        AVAILABLE_MEASURES,
    )

    atlas_name = parse_file_entities(atlas_nifti)["atlas"]
    if "schaefer2018" in atlas_name:
        atlas_name_part = [i for i in Path(atlas_nifti).parts if "_atlas_name_" in i]
        atlas_name = atlas_name_part[0].replace("_atlas_name_", "")
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
) -> Workflow:
    """
    Workflow to parcellate the brain
    """
    workflow = Workflow(name=f"{software}_{name}")
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

    nodes = {}
    for i, p in enumerate(inputs):
        nodes[f"parcellate_node_{i}"] = pe.Node(
            niu.Function(
                input_names=["in_file", "atlas_nifti"],
                output_names=["out_file", "atlas_name"],
                function=parcellate_all_measures,
            ),
            name=f"parcellate_node_{i}",
        )
        nodes[f"ds_parcellation_node_{i}"] = pe.Node(
            DerivativesDataSink(  # type: ignore[arg-type]
                **DIFFUSION_WF_OUTPUT_ENTITIES.get("parcellations"),
                reconstruction_software=software,
                dismiss_entities="direction",
                desc=p,
            ),
            name=f"ds_parcellation_node_{i}",
        )
        workflow.connect(
            [
                (
                    inputnode,
                    nodes[f"parcellate_node_{i}"],
                    [(p, "in_file")],
                ),
                (
                    inputnode,
                    nodes[f"parcellate_node_{i}"],
                    [("atlas_nifti", "atlas_nifti")],
                ),
                (
                    nodes[f"parcellate_node_{i}"],
                    nodes[f"ds_parcellation_node_{i}"],
                    [("out_file", "in_file"), ("atlas_name", "atlas")],
                ),
                (
                    inputnode,
                    nodes[f"ds_parcellation_node_{i}"],
                    [
                        ("acq_label", "acquisition"),
                        ("source_file", "source_file"),
                        ("base_directory", "base_directory"),
                    ],
                ),
            ]
        )

    return workflow
