from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost.interfaces.bids import DerivativesDataSink
from kepost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)


def init_derivatives_wf(
    name: str = "derivatives_wf",
    workflow_entities: dict = DIFFUSION_WF_OUTPUT_ENTITIES,
) -> pe.Workflow:
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
                "dwi_reference",
                "atlas_name",
                "whole_brain_parcellation",
                "gm_cropped_parcellation",
            ]
        ),
        name="inputnode",
    )
    ds_wholebrain = pe.Node(
        interface=DerivativesDataSink(
            **workflow_entities["wholebrain_parcellation"],
        ),
        name="ds_wholebrain",
    )
    ds_gm_cropped = pe.Node(
        interface=DerivativesDataSink(
            **workflow_entities["gm_cropped_parcellation"],
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
                    ("dwi_reference", "source_file"),
                    ("whole_brain_parcellation", "in_file"),
                    ("atlas_name", "atlas"),
                ],
            ),
            (
                inputnode,
                ds_gm_cropped,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_reference", "source_file"),
                    ("gm_cropped_parcellation", "in_file"),
                    ("atlas_name", "atlas"),
                ],
            ),
        ]
    )
    return workflow
