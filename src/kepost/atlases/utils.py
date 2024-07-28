import os
from pathlib import Path
from typing import Union

from nilearn import plotting

GM_5TT_CMDS = [
    "mrconvert {five_tissue_type} {out_file} -force",
    "fslroi {out_file} {out_file} 0 2",
    "fslmaths {out_file} -Tmax -thr 0.5 -bin {out_file} -odt float",
]


def generate_gm_mask_from_smriprep(
    gm_probseg: Union[str, Path], out_file: Union[str, Path], force: bool = False
):
    """
    Generate a grey matter mask from a probabilistic segmentation.

    Parameters
    ----------
    gm_probseg : Union[str, Path]
        Path to the gray matter probabilistic segmentation.
    out_file : Union[str, Path]
        Path to the output gray matter mask.
    force : bool, optional
        Force the generation of the mask, by default False
    """
    gm_probseg = Path(gm_probseg)
    out_file = Path(out_file)
    if out_file.exists() and not force:
        print(f"Gray matter mask {out_file} already exists.")
        return
    if not gm_probseg.is_file():
        raise FileNotFoundError(
            f"Gray matter probabilistic segmentation {gm_probseg} not found."
        )
    os.system(f"mrthreshold {gm_probseg} {out_file}")  # noqa: S605


def generate_gm_mask_from_5tt(
    five_tissue_type: Union[str, Path], out_file: Union[str, Path], force: bool = False
):
    """
    Generate a grey matter mask from a 5TT image.

    Parameters
    ----------
    five_tissue_type : Union[str, Path]
        Path to the 5TT image.
    out_dir : Union[str, Path]
        Path to the output directory.
    force : bool, optional
        Force the generation of the mask, by default False
    """
    five_tissue_type = Path(five_tissue_type)
    out_file = Path(out_file)
    if out_file.exists() and not force:
        print(f"Grey matter mask {out_file} already exists.")
        return
    if not five_tissue_type.is_file():
        raise FileNotFoundError(f"5TT image {five_tissue_type} not found.")
    for cmd in GM_5TT_CMDS:
        cmd = cmd.format(five_tissue_type=five_tissue_type, out_file=out_file)
        os.system(cmd)  # noqa: S605


def qc_atlas_registration(
    atlas: Union[str, Path],
    reference: Union[str, Path],
    atlas_name: str,
    reference_name: str,
    force: bool = False,
):
    """
    Check if the registration of an atlas to a reference image was successful.

    Parameters
    ----------
    atlas : Union[str,Path]
        Path to the atlas image.
    reference : Union[str,Path]
        Path to the reference image.
    atlas_name : str
        Name of the atlas.
    reference_name : str
        Name of the reference image.
    force : bool, optional
        Force the registration, by default False
    """
    atlas = Path(atlas)
    reference = Path(reference)
    out_file = atlas.parent / atlas.name.replace("dseg.nii.gz", "QC.png")
    if out_file.exists() and not force:
        print(f"QC image {out_file} already exists.")
        return
    if not atlas.is_file():
        raise FileNotFoundError(f"Atlas {atlas} not found.")
    if not reference.is_file():
        raise FileNotFoundError(f"Reference {reference} not found.")

    _ = plotting.plot_roi(
        roi_img=atlas,
        bg_img=reference,
        title=f"{atlas_name} registration to {reference_name}",
        draw_cross=False,
        display_mode="ortho",
        annotate=False,
        alpha=0.5,
        output_file=out_file,
    )
