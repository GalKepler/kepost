"""
This file contains the available atlases that can be used in the pipeline.
"""

from pathlib import Path

# flake8: noqa: E501


parent = Path(__file__).resolve().parent


def generate_schaefer_dict() -> dict:
    """
    Generate a dictionary with the Schaefer 2018 atlases.

    Returns
    -------
    dict
        Dictionary with the Schaefer 2018 atlases.
    """
    schaefer_dict = {}
    for n_regions in range(100, 1001, 100):
        for n_networks in [7, 17]:
            schaefer_dict[f"schaefer2018_{n_regions}_{n_networks}"] = {
                "nifti": parent
                / f"schaefer2018/MNI152/space-MNI152_atlas-schaefer2018_res-1mm_den-{n_regions}_desc-{n_networks}networks_dseg.nii.gz",
                "description_file": parent
                / f"schaefer2018/MNI152/space-MNI152_atlas-schaefer2018_res-1mm_den-{n_regions}_desc-{n_networks}networks_dseg.csv",
                "region_col": "index",
                "index_col": 0,
            }
    return schaefer_dict


AVAILABLE_ATLASES = {
    "fan2016": {
        "nifti": parent
        / "fan2016/MNI152/space-MNI152_atlas-fan2016_res-1mm_dseg.nii.gz",
        "description_file": parent
        / "fan2016/MNI152/space-MNI152_atlas-fan2016_res-1mm_dseg.csv",
        "region_col": "Label",
        "index_col": None,
    },
    "huang2022": {
        "nifti": parent
        / "huang2022/MNI152/space-MNI152_atlas-huang2022_res-1mm_dseg.nii.gz",
        "description_file": parent
        / "huang2022/MNI152/space-MNI152_atlas-huang2022_res-1mm_dseg.csv",
        "region_col": "HCPex_label",
        "index_col": 0,
    },
    **generate_schaefer_dict(),
}
