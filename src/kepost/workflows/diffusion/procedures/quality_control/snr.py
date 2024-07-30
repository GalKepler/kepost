import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu

from kepost.interfaces.bids import DerivativesDataSink
from kepost.workflows.diffusion.procedures.quality_control.utils import (
    calculate_strip_score,
)
from kepost.workflows.diffusion.procedures.utils.derivatives import (
    DIFFUSION_WF_OUTPUT_ENTITIES,
)


def calc_snr(
    dwi_file: str, tissue_mask: str, brain_mask: str, probseg_threshold: float = 0.001
) -> str:
    """
    Calculate the signal-to-noise ratio (SNR) of the diffusion-weighted images.

    Parameters
    ----------
    dwi_file : str
        Path to the diffusion-weighted image.
    tissue_mask : str
        Path to the tissue mask.
    brain_mask : str
        Path to the brain mask.

    Returns
    -------
    snr_values : list
        List of SNR values.
    """
    import nibabel as nib
    import numpy as np

    snr_values = []
    dwi_img = nib.load(dwi_file)
    dwi_data = dwi_img.get_fdata()
    tissue_mask_data = nib.load(tissue_mask).get_fdata() > probseg_threshold
    brain_mask_data = nib.load(brain_mask).get_fdata().astype(bool)
    n_volumes = dwi_data.shape[-1]
    for volume in range(n_volumes):
        signal = dwi_data[..., volume]
        signal_tissue = signal[tissue_mask_data]
        background = signal[~brain_mask_data]
        noise = np.std(background)
        snr = np.nanmean(signal_tissue) / noise
        snr_values.append(snr)

    return snr_values


def tissue_snr_to_csv(
    snr_values: list, striping_scores: list, tissues: list, dwi_bval: str, out_file: str
) -> str:
    """
    Convert the SNR values to a CSV file.

    Parameters
    ----------
    snr_values : list
        List of SNR values.
    tissues : list
        List of tissues.
    dwi_bval : list
        List of b-values.
    out_file : str
        Path to the output CSV file.

    Returns
    -------
    out_file : str
        Path to the output CSV file.
    """
    import os

    import numpy as np
    import pandas as pd

    cur_path = os.getcwd()
    bvals = np.loadtxt(dwi_bval)
    n_volumes = len(bvals)
    df = pd.DataFrame(index=tissues + ["bval"], columns=range(n_volumes))
    for tissue, snr in zip(tissues, snr_values):
        df.loc[tissue] = snr
    df.loc["bval"] = bvals
    df.loc["volume"] = df.columns
    df = df.T.melt(
        id_vars=["bval", "volume"],
        var_name="tissue",
        value_name="SNR",
    )
    df.loc[df["tissue"] == "wholebrain", "striping_score"] = striping_scores
    out_file = f"{cur_path}/{out_file}"
    df.to_csv(out_file, index=True)
    return out_file


def init_snr_wf(name: str = "snr_wf") -> pe.Workflow:
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
                "dwi_bval",
                "brain_mask",
                "gm_probseg",
                "wm_probseg",
                "csf_probseg",
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

    calc_snr_node = pe.MapNode(
        interface=niu.Function(
            input_names=["dwi_file", "tissue_mask", "brain_mask"],
            output_names="snr_values",
            function=calc_snr,
        ),
        name="calc_snr",
        iterfield=["tissue_mask"],
    )
    listify_probsegs = pe.Node(
        niu.Merge(4),
        name="listify_probsegs",
    )
    snrs_to_csv = pe.Node(
        niu.Function(
            input_names=[
                "snr_values",
                "striping_scores",
                "tissues",
                "dwi_bval",
                "out_file",
            ],
            output_names="out_file",
            function=tissue_snr_to_csv,
        ),
        name="snrs_to_csv",
    )
    snrs_to_csv.inputs.tissues = ["gm", "wm", "csf", "wholebrain"]
    snrs_to_csv.inputs.out_file = "snr_report.csv"
    ds_snr_csv = pe.Node(
        DerivativesDataSink(
            **DIFFUSION_WF_OUTPUT_ENTITIES["snr_csv"],
        ),
        name="ds_snr_csv",
    )
    workflow.connect(
        [
            (
                inputnode,
                listify_probsegs,
                [
                    ("gm_probseg", "in1"),
                    ("wm_probseg", "in2"),
                    ("csf_probseg", "in3"),
                    ("brain_mask", "in4"),
                ],
            ),
            (
                listify_probsegs,
                calc_snr_node,
                [
                    ("out", "tissue_mask"),
                ],
            ),
            (
                inputnode,
                calc_snr_node,
                [
                    ("dwi_file", "dwi_file"),
                    ("brain_mask", "brain_mask"),
                ],
            ),
            (
                calc_snr_node,
                snrs_to_csv,
                [
                    ("snr_values", "snr_values"),
                ],
            ),
            (
                inputnode,
                snrs_to_csv,
                [("dwi_bval", "dwi_bval")],
            ),
            (
                snrs_to_csv,
                ds_snr_csv,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_snr_csv,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_file", "source_file"),
                ],
            ),
            (
                snrs_to_csv,
                outputnode,
                [
                    ("out_file", "qc_report"),
                ],
            ),
        ]
    )
    striping_scores_node = pe.Node(
        niu.Function(
            input_names=["input_file", "brain_mask"],
            output_names="strip_scores",
            function=calculate_strip_score,
        ),
        name="striping_scores_node",
    )
    workflow.connect(
        [
            (
                inputnode,
                striping_scores_node,
                [
                    ("dwi_file", "input_file"),
                    ("brain_mask", "brain_mask"),
                ],
            ),
            (
                striping_scores_node,
                snrs_to_csv,
                [
                    ("strip_scores", "striping_scores"),
                ],
            ),
        ]
    )
    return workflow
