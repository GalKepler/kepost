from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost.interfaces.bids import DerivativesDataSink
from kepost.interfaces.bids.utils import get_entity

# from niworkflows.interfaces.bids import DerivativesDataSink as RPTDerivativesDataSink


wholebrain_entities = {
    "space": "T1w",
    "subtype": "atlases",
    "desc": "",
    "label": "WholeBrain",
    "suffix": "dseg",
    "extension": ".nii.gz",
}

gm_cropped_entities = {
    "space": "T1w",
    "subtype": "atlases",
    "desc": "",
    "label": "GM",
    "suffix": "dseg",
    "extension": ".nii.gz",
}


def init_derivatives_wf(name: str = "derivatives_wf") -> Workflow:
    """
    Initialize the derivatives workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "derivatives_wf"

    Returns
    -------
    Workflow
        The derivatives workflow
    """
    workflow = Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "base_directory",
                "t1w_preproc",
                "atlas_name",
                "whole_brain_parcellation",
                "gm_cropped_parcellation",
                "registration_report",
                "n_voxels_report",
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

    ds_wholebrain = pe.Node(
        interface=DerivativesDataSink(**wholebrain_entities),
        name="ds_wholebrain",
    )
    ds_gm_cropped = pe.Node(
        interface=DerivativesDataSink(**gm_cropped_entities),
        name="ds_gm_cropped",
    )

    ds_registration = pe.Node(
        interface=DerivativesDataSink(
            datatype="figures",
            suffix="dseg",
            space="T1w",
            dismiss_entities=["ceagent"],
        ),
        name="ds_registration_report",
    )
    ds_n_voxels = pe.Node(
        interface=DerivativesDataSink(
            datatype="figures",
            suffix="dseg",
            space="cropped",
            dismiss_entities=["ceagent"],
        ),
        name="ds_n_voxels_report",
    )

    workflow.connect(
        [
            (
                inputnode,
                get_atlas_name_node,
                [
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
            (
                inputnode,
                get_atlas_den_node,
                [
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
            (
                inputnode,
                get_atlas_div_node,
                [
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_wholebrain,
                [
                    ("base_directory", "base_directory"),
                    ("t1w_preproc", "source_file"),
                    ("whole_brain_parcellation", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_gm_cropped,
                [
                    ("base_directory", "base_directory"),
                    ("t1w_preproc", "source_file"),
                    ("gm_cropped_parcellation", "in_file"),
                ],
            ),
            (
                get_atlas_name_node,
                ds_wholebrain,
                [
                    ("atlas_name", "atlas"),
                ],
            ),
            (
                get_atlas_den_node,
                ds_wholebrain,
                [
                    ("atlas_den", "den"),
                ],
            ),
            (
                get_atlas_div_node,
                ds_wholebrain,
                [
                    ("atlas_division", "division"),
                ],
            ),
            (
                get_atlas_name_node,
                ds_gm_cropped,
                [
                    ("atlas_name", "atlas"),
                ],
            ),
            (
                get_atlas_den_node,
                ds_gm_cropped,
                [
                    ("atlas_den", "den"),
                ],
            ),
            (
                get_atlas_div_node,
                ds_gm_cropped,
                [
                    ("atlas_division", "division"),
                ],
            ),
            (
                inputnode,
                ds_registration,
                [
                    ("base_directory", "base_directory"),
                    ("t1w_preproc", "source_file"),
                    ("registration_report", "in_file"),
                ],
            ),
            (get_atlas_name_node, ds_registration, [("atlas_name", "atlas")]),
            (get_atlas_den_node, ds_registration, [("atlas_den", "den")]),
            (get_atlas_div_node, ds_registration, [("atlas_division", "division")]),
            (
                inputnode,
                ds_n_voxels,
                [
                    ("base_directory", "base_directory"),
                    ("t1w_preproc", "source_file"),
                    ("n_voxels_report", "in_file"),
                ],
            ),
            (get_atlas_name_node, ds_n_voxels, [("atlas_name", "atlas")]),
            (get_atlas_den_node, ds_n_voxels, [("atlas_den", "den")]),
            (get_atlas_div_node, ds_n_voxels, [("atlas_division", "division")]),
        ]
    )
    return workflow
