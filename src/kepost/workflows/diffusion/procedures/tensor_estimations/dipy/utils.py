def estimate_sigma(in_file: str, in_mask: str) -> float:
    """
    Estimate the sigma value (1.5267 * std(background_noise))

    Parameters
    ----------
    in_file : str
        The input file

    Returns
    -------
    float
        The sigma value
    """
    import nibabel as nib
    import numpy as np

    data = nib.load(in_file).get_fdata()  # type: ignore[attr-defined]
    mask = nib.load(in_mask).get_fdata().astype(bool)  # type: ignore[attr-defined]
    background = data[~mask]
    return 1.5267 * np.std(background)
