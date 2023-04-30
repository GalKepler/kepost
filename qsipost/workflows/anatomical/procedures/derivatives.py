from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from qsipost.interfaces.bids import DerivativesDataSink

wholebrain_entities = {
    # "atlas": "brainnetome",
    "res": "T1w",
    "space": "T1w",
    "desc": "",
    "label": "WholeBrain",
    "suffix": "dseg",
    "extension": ".nii.gz",
}

gm_cropped_entities = {
    # "atlas": "brainnetome",
    "res": "T1w",
    "space": "T1w",
    "desc": "",
    "label": "GM",
    "suffix": "dseg",
    "extension": ".nii.gz",
}


def init_derivatives_wf(name: str = "derivatives_wf") -> pe.Workflow:
    """
    Initialize the derivatives workflow.

    Parameters
    ----------
    name : str, optional
        The name of the workflow, by default "derivatives_wf"

    Returns
    -------
    pe.Workflow
        The derivatives workflow
    """
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "base_directory",
                "anatomical_reference",
                "atlas_name",
                "whole_brain_parcellation",
                "gm_cropped_parcellation",
            ]
        ),
        name="inputnode",
    )
    ds_wholebrain = pe.Node(
        interface=DerivativesDataSink(
            **wholebrain_entities,
        ),
        name="ds_wholebrain",
    )
    ds_gm_cropped = pe.Node(
        interface=DerivativesDataSink(
            **gm_cropped_entities,
        ),
        name="ds_gm_cropped",
    )
    workflow.connect(
        [
            (
                inputnode,
                ds_wholebrain,
                [
                    ("base_directory", "base_directory"),
                    ("anatomical_reference", "source_file"),
                    ("whole_brain_parcellation", "in_file"),
                    ("atlas_name", "atlas"),
                ],
            ),
            (
                inputnode,
                ds_gm_cropped,
                [
                    ("base_directory", "base_directory"),
                    ("anatomical_reference", "source_file"),
                    ("gm_cropped_parcellation", "in_file"),
                    ("atlas_name", "atlas"),
                ],
            ),
        ]
    )
    return workflow
