DHOLLANDER = """
Fiber response function estimation was performed using
the `dhollander` algorithm [@dhollander_2016; @dhollander_2019]
as implemented in *MRtrix*'s [@mrtrix3] `dwi2response`.
This method estimates multi-tissue response functions for WM,
GM, and CSF from the DWI data. The dhollander algorithm is an
unsupervised approach that utilizes a combination of tissue-specific
signal characteristics and data-driven selection criteria to robustly
identify appropriate response functions.
"""

RESPONSE_ALGORITHMS = {"dhollander": DHOLLANDER}

MSMT_CSD = """Multi-shell multi-tissue constrained spherical deconvolution (`MSMT-CSD`) [@msmt5tt]
was performed using *MRtrix*'s `dwi2fod` with the estimated response functions
and the multi-shell DWI data. This method estimates the fiber orientation
distribution (FOD) in each voxel while simultaneously accounting for
the presence of multiple tissue types. This is achieved by utilizing the
multi-tissue response functions estimated by the `dhollander` algorithm
to constrain the FOD estimation to the expected signal behavior of each
tissue type. The MSMT-CSD algorithm is particularly useful for resolving
crossing fibers in regions where multiple tissue types are present.
"""

FOD_ALGORITHMS = {"msmt_csd": MSMT_CSD}

SD_STREAM = """Deterministic tractography was conducted using *MRtrix*'s `tckgen` command
with the `SD_Stream` algorithm, which implements deterministic tracking based on
Spherical Deconvolution (SD) [@tournier_SD_2012]. The tracking was conducted using the Anatomically-Constrained
Tractography (ACT) framework, which incorporates anatomical priors, which are described above, to improve the
biological accuracy of the generated streamlines.
Streamlines were seeded throughout the white matter mask derived from the FOD image. Streamlines were terminated
according to the following criteria:
A minimum FOD amplitude of 0.1, maximum angle of {tracking_max_angle} degrees, minimum length of {tracking_min_length}
mm, and a maximum length of {tracking_max_length} mm.
A total of {n_streamlines} streamlines were generated with a step size of {step_size} mm.
"""

DET_TRACTOGRAPHY_DESCRIPTIONS = {"sd_stream": SD_STREAM}

IFOD2 = """For probabilistic tractography, the iFOD2 algorithm [@tournier_iFOD2_2010]
was used with the same parameters as the deterministic tractography. The iFOD2 algorithm
is a second-order integration method for fiber orientation distribution-based probabilistic
tractography. It accounts for the inherent uncertainty in fiber orientation estimates by
sampling from the full distribution of possible directions within each voxel. This approach
allows for more accurate tracking in regions with complex microstructure, such as areas with
crossing, kissing, or branching fibers.
"""

PROB_TRACTOGRAPHY_DESCRIPTIONS = {"ifod2": IFOD2}

SIFT = """To enhance the biological accuracy and quantitative interpretation of the tractography
results, the generated streamlines were post-processed using the Spherical-deconvolution Informed
Filtering of Tractograms (SIFT) and SIFT2 algorithms [@sift_2013; @sift2_2015], as implemented in *MRtrix* via `tcksift` and
`tcksift2` accordingly.
"""
