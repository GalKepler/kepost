import numpy as np
from scipy.stats import median_abs_deviation


# Custom measures
def zfmean(data: np.ndarray, threshold=3) -> float:
    """
    Z Filtered Mean

    Parameters
    ----------
    data : np.ndarray
        Input data.
    threshold : float, optional
        Z-score threshold, by default 3.

    Returns
    -------
    float
        Z Filtered Mean
    """
    m = np.nanmean(data)
    s = np.nanstd(data)
    z_scores = np.abs((data - m) / s)
    return np.nanmean(data[z_scores < threshold])


def madmedian(data: np.ndarray, threshold=3) -> float:
    """
    Median of MAD-filtered data

    Parameters
    ----------
    data : np.ndarray
        Input data.
    threshold : float, optional
        Z-score threshold, by default 3.

    Returns
    -------
    float
        Median of MAD-filtered data
    """
    m = np.nanmedian(data)
    # calculate the median absolute deviation where data is not NaN
    mad = median_abs_deviation(data, nan_policy="omit")
    filtered_data = data[np.abs(data - m) < threshold * mad]
    return np.nanmedian(filtered_data)


def qfmean(data: np.ndarray, lower_quantile=10, upper_quantile=90) -> float:
    """
    Quantile Filtered Mean

    Parameters
    ----------
    data : np.ndarray
        Input data.
    lower_quantile : int, optional
        Lower quantile, by default 10.
    upper_quantile : int, optional
        Upper quantile, by default 90.

    Returns
    -------
    float
        Quantile Filtered Mean
    """
    lower = np.nanpercentile(data, lower_quantile)
    upper = np.nanpercentile(data, upper_quantile)
    return np.nanmean(data[(data > lower) & (data < upper)])


def iqrmean(data: np.ndarray) -> float:
    """
    IQR Filtered Mean

    Parameters
    ----------
    data : np.ndarray
        Input data.
    threshold : float, optional
        IQR threshold, by default 1.5.

    Returns
    -------
    float
        IQR Filtered Mean
    """
    q75 = np.nanpercentile(data, 75)
    q25 = np.nanpercentile(data, 25)
    return np.nanmean(data[(data >= q25) & (data <= q75)])


AVAILABLE_MEASURES = {
    "zfmean": zfmean,
    "madmedian": madmedian,
    "qfmean": qfmean,
    "iqrmean": iqrmean,
    "nanmean": np.nanmean,
    "nanmedian": np.nanmedian,
}
