def plot_n_voxels_in_atlas(wholebrain: str, gm_cropped: str):
    """
    Plot the number of voxels in each region of the atlas.

    Parameters
    ----------
    wholebrain : str
        Path to the whole brain parcellation.
    gm_cropped : str
        Path to the grey matter cropped parcellation.
    """
    import os
    from pathlib import Path

    import matplotlib.pyplot as plt
    import nibabel as nib
    import pandas as pd
    import seaborn as sns
    from bids.layout import parse_file_entities

    from kepost.atlases.utils import get_atlas_properties

    atlas_name = parse_file_entities(wholebrain)["atlas"]
    if "schaefer2018" in atlas_name:
        atlas_name_part = [i for i in Path(wholebrain).parts if "_atlas_name_" in i]
        atlas_name = atlas_name_part[0].replace("_atlas_name_", "")
    _, description, region_col, index_col = get_atlas_properties(atlas_name)
    df = pd.read_csv(description, index_col=index_col)
    wb = nib.load(wholebrain).get_fdata()
    gm = nib.load(gm_cropped).get_fdata()
    for column, data in zip(["Uncropped", "GM-cropped"], [wb, gm]):
        for i, row in df.iterrows():
            roi = row[region_col]
            df.loc[i, f"{column}"] = (data == roi).sum()
    df_long = df.melt(id_vars=[region_col], value_vars=["Uncropped", "GM-cropped"])
    sns.set_context("talk")
    sns.set_style("whitegrid")
    plt.figure(figsize=(15, 8))
    sns.lineplot(
        x=region_col,
        y="value",
        hue="variable",
        data=df_long,
        palette=sns.color_palette("tab10", n_colors=2),
    )
    plt.ylabel("Number of voxels")
    plt.xlabel("Region")
    plt.title(f"Number of voxels in each region of the {atlas_name} atlas")
    plt.tight_layout()
    out_file = f"{os.getcwd()}/n_voxels_in_atlas.svg"
    plt.savefig(out_file)
    return out_file
