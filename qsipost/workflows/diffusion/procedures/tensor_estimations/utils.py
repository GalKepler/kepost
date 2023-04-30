def parcellate_image(
    parcellation_image: str,
    parcellation_table: str,
    label_column: str,
    in_files: list,
    in_names: list,
    aggregation_func,
    out_name: str = "out.pkl",
):
    """
    Parcellate an image using a parcellation image.

    Parameters
    ----------
    parcellation_image : str
        The atlas parcellation image.
    parcellation_table : pd.DataFrame
        The parcellation table.
    in_file : str
        The image to parcellate.
    aggregation_func : Callable
        The aggregation function to use.
    """
    import nibabel as nib
    import numpy as np
    import pandas as pd

    parcellation_table = pd.read_csv(parcellation_table)
    atlas_data = nib.load(parcellation_image).get_fdata().astype(np.int32)
    result = parcellation_table.copy()
    for name, image in zip(in_names, in_files):
        data = nib.load(image).get_fdata()
        for label in parcellation_table[label_column]:
            result.loc[result[label_column] == label, name] = aggregation_func(
                data[atlas_data == label]
            )
    result.to_pickle(out_name)
    return out_name
