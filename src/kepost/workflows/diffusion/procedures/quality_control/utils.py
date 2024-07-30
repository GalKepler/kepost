def calculate_strip_score(
    input_file: str,
    brain_mask: str,
    axis=2,
    target_freq=0.25,
    freq_tolerance=0.05,
) -> list:
    """
    Calculate the striping score of a given NIfTI file along a given axis.

    Parameters
    ----------
    input_file : Union[str, Path]
        The input NIfTI file
    axis : int, optional
        The axis along which to calculate the striping score, by default 2
    target_freq : float, optional
        The target frequency to detect striping, by default 0.25
    freq_tolerance : float, optional
        The frequency tolerance to detect striping, by default 0.05

    Returns
    -------
    list
        The striping scores
    """
    from pathlib import Path

    import nibabel as nib
    import numpy as np
    from scipy.fft import fft, fftfreq

    if isinstance(input_file, str) or isinstance(input_file, Path):
        input_file = nib.load(input_file)
    if isinstance(brain_mask, str) or isinstance(brain_mask, Path):
        brain_mask = nib.load(brain_mask)
    all_volumes = input_file.get_fdata()
    brain_mask = brain_mask.get_fdata().astype(bool)

    strip_scores = []
    n_volumes = all_volumes.shape[-1]
    for volume in range(n_volumes):
        data = all_volumes[..., volume]
        data[~brain_mask] = 0
        # Compute the mean signal profile along the given axis
        mean_profile = np.mean(
            data, axis=tuple(i for i in range(data.ndim) if i != axis)
        )

        # Perform Fourier transform to compute the power spectrum
        N = len(mean_profile)
        yf = fft(mean_profile)
        xf = fftfreq(N, 1)[: N // 2]

        # Compute the power spectrum
        power_spectrum = 2.0 / N * np.abs(yf[: N // 2])

        # Find the indices of the frequencies that match the target frequency
        freq_indices = np.where(
            (xf >= target_freq - freq_tolerance) & (xf <= target_freq + freq_tolerance)
        )[0]

        # Calculate the sum of the power spectrum at the target frequency
        strip_score = np.sum(power_spectrum[freq_indices])

        strip_scores.append(strip_score)

    return strip_scores


def parse_pct_b_outliers(
    qc_dict: dict,
    key: str = "qc_outliers_b",
    pct_key: str = "pct_outliers_b",
    unique_b_key="data_unique_bvals",
):
    """
    Parse the percentage of outliers per b value.

    Parameters
    ----------
    pcts : list
        The list of percentages
    """
    result = {}
    pcts = qc_dict[key]
    bvalues = qc_dict[unique_b_key]
    for bval, pct in zip(bvalues, pcts):
        result[f"{pct_key}{bval}"] = pct
    return result


def parse_params_avg(qc_dict: dict, key: str = "qc_params_avg"):
    """
    Parse the average parameters
    """
    result = {}
    keys = []
    for i in ["translation", "rotation"]:
        for j in ["x", "y", "z"]:
            keys.append(f"avg_{i}_{j}")
    keys += [f"std_ec_term_{j}" for j in ["x", "y", "z"]]
    params = qc_dict[key]
    for key, param in zip(keys, params):
        result[key] = param
    return result


def get(qc_dict: dict, key: str):
    """
    Get the value from the dictionary
    """
    return qc_dict[key]


EDDY_QC_JSON_PARSER = {
    "avg_abs_mot": {"func": get, "keys": {"key": "qc_mot_abs"}},
    "avg_rel_mot": {"func": get, "keys": {"key": "qc_mot_rel"}},
    "pct_outliers_b": {"func": parse_pct_b_outliers, "keys": {"key": "qc_outliers_b"}},
    "pct_outliers_total": {"func": get, "keys": {"key": "qc_outliers_tot"}},
    "qc_params_avg": {"func": parse_params_avg, "keys": {"key": "qc_params_avg"}},
}

BASE_JSON_KEYS = [
    "avg_abs_mot",
    "avg_rel_mot",
    "pct_outliers_b1000",
    "pct_outliers_b2000",
    "pct_outliers_b4000",
    "pct_outliers_total",
    "avg_translation_x",
    "avg_translation_y",
    "avg_translation_z",
    "avg_rotation_x",
    "avg_rotation_y",
    "avg_rotation_z",
    "std_ec_term_x",
    "std_ec_term_y",
    "std_ec_term_z",
]


def parse_eddyqc(eddyqc_dir: str) -> dict:
    """
    Parse the eddy quality control string
    """
    import json
    from pathlib import Path

    from kepost.workflows.diffusion.procedures.quality_control.utils import (
        EDDY_QC_JSON_PARSER,
    )

    result = {}
    qc_json = Path(eddyqc_dir) / "quad" / "qc.json"
    if not qc_json.exists():
        raise FileNotFoundError(f"Could not find {qc_json}")
    with qc_json.open("r") as f:
        qc_dict = json.load(f)
    for key, value in EDDY_QC_JSON_PARSER.items():
        value = value["func"](qc_dict, **value["keys"])
        if isinstance(value, dict):
            result.update(value)
        else:
            result[key] = value
    return result
