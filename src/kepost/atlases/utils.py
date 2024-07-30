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
