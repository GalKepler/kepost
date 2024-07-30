import nipype.pipeline.engine as pe
from nipype.interfaces import fsl
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu

from kepost.interfaces.bids import DerivativesDataSink
from kepost.interfaces.mrtrix3 import MRFilter
from kepost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)


def init_qc_wf(name: str = "qc_wf") -> pe.Workflow:
    """
    Workflow to perform tractography using MRtrix3.
    """
    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_file",
                "dwi_grad",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "qc_report",
            ]
        ),
        name="outputnode",
    )

    extract_b0_node = pe.Node(
        mrt.DWIExtract(bzero=True, out_file="b0.mif"),
        name="extract_b0",
    )
    calc_mean_b0_node = pe.Node(
        mrt.MRMath(operation="mean", axis=3, out_file="mean_b0.nii.gz"),
        name="calc_mean_b0",
    )
    calc_std_b0_node = pe.Node(
        mrt.MRMath(operation="std", axis=3, out_file="std_b0.nii.gz"),
        name="calc_std_b0",
    )
    calc_snr_node = pe.Node(
        fsl.BinaryMaths(operation="div", out_file="snr.nii.gz"),
        name="calc_snr",
    )
    median_filter_node = pe.Node(
        MRFilter(
            filter="median",
            out_file="snr_filtered.nii.gz",
        ),
        name="median_filter",
    )
    ds_snr = pe.Node(
        interface=DerivativesDataSink(
            **DIFFUSION_WF_OUTPUT_ENTITIES["snr_image"],
            dismiss_entities="reconstruction_software",
        ),
        name="ds_snr",
    )
    workflow.connect(
        [
            (
                inputnode,
                extract_b0_node,
                [
                    ("dwi_file", "in_file"),
                    ("dwi_grad", "grad_file"),
                ],
            ),
            (
                extract_b0_node,
                calc_mean_b0_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                extract_b0_node,
                calc_std_b0_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                calc_mean_b0_node,
                calc_snr_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                calc_std_b0_node,
                calc_snr_node,
                [
                    ("out_file", "operand_file"),
                ],
            ),
            (
                calc_snr_node,
                median_filter_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                median_filter_node,
                outputnode,
                [
                    ("out_file", "qc_report"),
                ],
            ),
            (
                median_filter_node,
                ds_snr,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_snr,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_file", "source_file"),
                ],
            ),
        ]
    )
    return workflow
