from pathlib import Path
from typing import Callable, Union

import nibabel as nib
import numpy as np
import pandas as pd

GM_5TT_CMDS = [
    "mrconvert {five_tissue_type} {out_file} -force",
    "fslroi {out_file} {out_file} 0 2",
    "fslmaths {out_file} -Tmax -thr 0.5 -bin {out_file} -odt float",
]


def get_atlas_properties(atlas: str):
    """
    A simple function to get the properties of an atlas.

    Parameters
    ----------
    atlas : str
        The name of the atlas.

    Returns
    -------
    dict
        A dictionary with the properties of the atlas.
    """
    from kepost.atlases.available_atlases.available_atlases import AVAILABLE_ATLASES

    nifti, description, region_col, index_col = [
        AVAILABLE_ATLASES.get(atlas).get(key)  # type: ignore[union-attr]
        for key in ["nifti", "description_file", "region_col", "index_col"]
    ]
    return nifti, description, region_col, index_col


def parcellate(
    atlas_description: pd.DataFrame,
    index_col: int,
    atlas_nifti: Union[str, Path],
    region_col: str,
    metric_image: Union[str, Path],
    measure: Callable,
) -> pd.DataFrame:
    """
    Collects a measure for each region of an atlas.

    Parameters
    ----------
    atlas_entities : dict
        Dictionary with the entities of the atlas.
    metric_image : Union[str,Path]
        Path to the metric image.
    measure : Callable
        Measure function.

    Returns
    -------
    pd.DataFrame
        Dataframe with the measure for each region of the atlas.
    """
    atlas_description = pd.read_csv(atlas_description, index_col=index_col).copy()
    atlas_description["value"] = np.nan
    atlas_data = nib.load(atlas_nifti).get_fdata()  # type: ignore[attr-defined]
    metric_data = nib.load(metric_image).get_fdata()  # type: ignore[attr-defined]
    for i, row in atlas_description.iterrows():
        region = int(row[region_col])
        roi_mask = atlas_data == region
        measure_value = measure(metric_data[roi_mask])
        atlas_description.loc[i, "value"] = measure_value
    return atlas_description
