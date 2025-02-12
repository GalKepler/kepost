import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost import config
from kepost.interfaces.bids import DerivativesDataSink
from kepost.interfaces.mrtrix3 import TckMap, TckSift, TckSift2
from kepost.workflows.diffusion.descriptions.tractography import (
    DET_TRACTOGRAPHY_DESCRIPTIONS,
    FOD_ALGORITHMS,
    PROB_TRACTOGRAPHY_DESCRIPTIONS,
    RESPONSE_ALGORITHMS,
    SIFT,
)
from kepost.workflows.diffusion.procedures.coregisterations import init_5tt_coreg_wf


def estimate_tractography_parameters(
    in_file: str,
    stepscale: float = 0.5,
    lenscale_min: int = 30,
    lenscale_max: int = 500,
):
    """
    Estimate parameters for tractography by normalizing them to the
    pixel size of the image.

    Parameters
    ----------
    in_file : str
        Path to the input file.
    stepscale : float
        Step size in mm.
    lenscale_min : int
        Minimum length of the tract in mm.
    lenscale_max : int
        Maximum length of the tract in mm.

    Returns
    -------
    stepscale : float
        Step size in mm.
    lenscale_min : int
        Minimum length of the tract in mm.
    lenscale_max : int
        Maximum length of the tract in mm.
    """
    import nibabel as nib

    from kepost import config

    data = nib.load(in_file)
    pixdim = data.header["pixdim"][1]  # type: ignore[index]
    stepscale = config.workflow.tracking_stepscale * pixdim
    lenscale_min = config.workflow.tracking_lenscale_min * pixdim
    lenscale_max = config.workflow.tracking_lenscale_max * pixdim
    return stepscale, lenscale_min, lenscale_max


def format_algorithm(algorithm: str) -> str:
    """
    Format the algorithm name.

    Parameters
    ----------
    algorithm : str
        the algorithm name

    Returns
    -------
    str
        the formatted algorithm name
    """
    return algorithm.replace("_", "")


def init_tractography_wf(name: str = "tractography_wf") -> Workflow:
    """
    Build the SDC and motion correction workflow.

    Parameters
    ----------
    name : str, optional
        name of the workflow (default: "eddy_wf")

    Returns
    -------
    Workflow
        the workflow
    """
    workflow = Workflow(name=name)

    response_desc = RESPONSE_ALGORITHMS.get(config.workflow.response_algorithm)
    fod_desc = FOD_ALGORITHMS.get(config.workflow.fod_algorithm)
    det_tractography_desc = DET_TRACTOGRAPHY_DESCRIPTIONS.get(
        config.workflow.det_tracking_algorithm.lower()
    )
    det_tractography_desc = det_tractography_desc.format(  # type: ignore[union-attr]
        tracking_max_angle=config.workflow.tracking_max_angle,
        tracking_min_length=config.workflow.tracking_lenscale_min,
        tracking_max_length=config.workflow.tracking_lenscale_max,
        n_streamlines=config.workflow.n_raw_tracts,
        step_size=config.workflow.tracking_stepscale,
    )
    prob_tractography_desc = PROB_TRACTOGRAPHY_DESCRIPTIONS.get(
        config.workflow.prob_tracking_algorithm.lower()
    )

    desc = (
        response_desc + fod_desc + det_tractography_desc + prob_tractography_desc + SIFT  # type: ignore[operator]
    )
    workflow.__desc__ = desc
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_nifti",
                "dwi_grad",
                "dwi_reference",
                "t1w_to_dwi_transform",
                "t1w_reference",
                "dwi_mask",
                "five_tissue_type",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "wm_response",
                "gm_response",
                "csf_response",
                "wm_fod",
                "gm_fod",
                "csf_fod",
                "predicted_signal",
                "unsifted_tck",
                "sifted_tck",
                "sift2_weights",
                "tdi_map",
            ]
        ),
        name="outputnode",
    )

    coreg_5tt_wf = init_5tt_coreg_wf()
    workflow.connect(
        [
            (
                inputnode,
                coreg_5tt_wf,
                [
                    ("dwi_reference", "inputnode.dwi_reference"),
                    ("t1w_to_dwi_transform", "inputnode.t1w_to_dwi_transform"),
                    ("t1w_reference", "inputnode.t1w_reference"),
                    ("five_tissue_type", "inputnode.5tt_file"),
                ],
            )
        ]
    )

    mrconvert_node = pe.Node(
        mrt.MRConvert(
            out_file="dwi.mif",
            nthreads=config.nipype.omp_nthreads,
        ),
        name="mrconvert",
    )
    # Estimate the response functions
    dwi2response_node = pe.Node(
        mrt.ResponseSD(
            algorithm=config.workflow.response_algorithm,
            wm_file="wm_response.txt",
            gm_file="gm_response.txt",
            csf_file="csf_response.txt",
            nthreads=config.nipype.omp_nthreads,
        ),
        name="dwi2response",
    )

    # Estimate the fiber orientation distribution
    dwi2fod_node = pe.Node(
        mrt.ConstrainedSphericalDeconvolution(
            algorithm=config.workflow.fod_algorithm,
            wm_odf="wm_fod.nii.gz",
            gm_odf="gm_fod.nii.gz",
            csf_odf="csf_fod.nii.gz",
            predicted_signal="predicted_signal.mif",
            nthreads=config.nipype.omp_nthreads,
        ),
        name="dwi2fod",
    )

    workflow.connect(
        [
            (
                inputnode,
                mrconvert_node,
                [
                    ("dwi_nifti", "in_file"),
                    ("dwi_grad", "grad_file"),
                ],
            ),
            (
                mrconvert_node,
                dwi2response_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                inputnode,
                dwi2response_node,
                [
                    ("dwi_mask", "in_mask"),
                ],
            ),
            (mrconvert_node, dwi2fod_node, [("out_file", "in_file")]),
            (
                inputnode,
                dwi2fod_node,
                [
                    ("dwi_mask", "mask_file"),
                ],
            ),
            (
                dwi2response_node,
                dwi2fod_node,
                [
                    ("wm_file", "wm_txt"),
                    ("gm_file", "gm_txt"),
                    ("csf_file", "csf_txt"),
                ],
            ),
            (
                dwi2response_node,
                outputnode,
                [
                    ("wm_file", "wm_response"),
                    ("gm_file", "gm_response"),
                    ("csf_file", "csf_response"),
                ],
            ),
            (
                dwi2fod_node,
                outputnode,
                [
                    ("wm_odf", "wm_fod"),
                    ("gm_odf", "gm_fod"),
                    ("csf_odf", "csf_fod"),
                    ("predicted_signal", "predicted_signal"),
                ],
            ),
        ]
    )

    tractography_algorithm = pe.Node(
        niu.IdentityInterface(fields=["algorithm"]),
        name="tractography_algorithm",
    )
    tractography_algorithm.iterables = (
        "algorithm",
        [
            config.workflow.det_tracking_algorithm,
            config.workflow.prob_tracking_algorithm,
        ],
    )

    tractography = pe.Node(
        mrt.Tractography(
            angle=config.workflow.tracking_max_angle,
            select=config.workflow.n_raw_tracts,
            out_file="tracks.tck",
            nthreads=config.nipype.omp_nthreads,
        ),
        name="tractography",
    )

    estimate_tracts_parameters_node = pe.Node(
        niu.Function(
            function=estimate_tractography_parameters,
            input_names=["in_file"],
            output_names=["stepscale", "lenscale_min", "lenscale_max"],
        ),
        name="estimate_tractography_parameters",
    )

    tcksift_node = pe.Node(
        TckSift(
            nthreads=config.nipype.omp_nthreads,
            out_file="sift.tck",
            out_csv="sift.csv",
            out_mu="sift_mu.txt",
            term_number=config.workflow.n_tracts,
            fd_scale_gm=config.workflow.fs_scale_gm,
        ),
        name="tcksift",
    )
    if config.workflow.debug_sift:
        tcksift_node.inputs.out_debug = "sift_debug"

    tcksift2_node = pe.Node(
        TckSift2(
            nthreads=config.nipype.omp_nthreads,
            out_file="sift2.txt",
            out_csv="sift2.csv",
            out_mu="sift2_mu.txt",
            out_coeffs="sift2_coeffs.txt",
            fd_scale_gm=config.workflow.fs_scale_gm,
        ),
        name="tcksift2",
    )
    if config.workflow.debug_sift:
        tcksift2_node.inputs.out_debug = "sift2_debug"

    workflow.connect(
        [
            (
                inputnode,
                estimate_tracts_parameters_node,
                [
                    ("dwi_nifti", "in_file"),
                ],
            ),
            (
                dwi2fod_node,
                tcksift_node,
                [
                    ("wm_odf", "in_fod"),
                ],
            ),
            (coreg_5tt_wf, tcksift_node, [("outputnode.5tt_coreg", "act_file")]),
            (
                dwi2fod_node,
                tcksift2_node,
                [
                    ("wm_odf", "in_fod"),
                ],
            ),
            (coreg_5tt_wf, tcksift2_node, [("outputnode.5tt_coreg", "act_file")]),
        ]
    )

    workflow.connect(
        [
            (
                tractography_algorithm,
                tractography,
                [
                    ("algorithm", "algorithm"),
                ],
            ),
            (
                estimate_tracts_parameters_node,
                tractography,
                [
                    ("stepscale", "step_size"),
                    ("lenscale_min", "min_length"),
                    ("lenscale_max", "max_length"),
                ],
            ),
            (
                inputnode,
                tractography,
                [("dwi_mask", "seed_image")],
            ),
            (
                coreg_5tt_wf,
                tractography,
                [
                    ("outputnode.5tt_coreg", "act_file"),
                ],
            ),
            (
                dwi2fod_node,
                tractography,
                [
                    ("wm_odf", "in_file"),
                ],
            ),
            (
                tractography,
                tcksift_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                tractography,
                tcksift2_node,
                [
                    ("out_file", "in_file"),
                ],
            ),
        ]
    )

    tckmap_node = pe.Node(
        TckMap(
            nthreads=config.nipype.omp_nthreads,
            out_file="fod_amp.nii.gz",
            contrast="fod_amp",
            precise=True,
            dec=True,
        ),
        name="tckmap",
    )
    workflow.connect(
        [
            (
                inputnode,
                tckmap_node,
                [("dwi_reference", "template")],
            ),
            (
                tractography,
                tckmap_node,
                [("out_file", "in_file")],
            ),
            (
                dwi2fod_node,
                tckmap_node,
                [("wm_odf", "scalar_image")],
            ),
            (
                tckmap_node,
                outputnode,
                [
                    ("out_file", "tdi_map"),
                ],
            ),
        ]
    )

    format_algorithm_node = pe.Node(
        niu.Function(
            input_names=["algorithm"],
            output_names=["algorithm"],
            function=format_algorithm,
        ),
        name="format_algorithm",
    )

    ds_tracts = pe.Node(
        DerivativesDataSink(
            suffix="tracts",
            extension=".tck",
            desc="unfiltered",
            copy=True,
        ),
        name="ds_unfiltered_tracts",
    )
    ds_sifted_tracts = pe.Node(
        DerivativesDataSink(
            suffix="tracts",
            extension=".tck",
            desc="SIFT",
            copy=True,
        ),
        name="ds_sifted_tracts",
    )
    ds_sift2_txt = pe.Node(
        DerivativesDataSink(
            suffix="weights",
            extension=".txt",
            desc="SIFT2",
            copy=True,
        ),
        name="ds_sift2_txt",
    )
    ds_wm_fod = pe.Node(
        DerivativesDataSink(
            label="wm",
            extension=".nii.gz",
            desc="FOD",
            suffix="dwiref",
            copy=True,
        ),
        name="ds_wm_fod",
    )
    ds_gm_fod = pe.Node(
        DerivativesDataSink(
            label="gm",
            extension=".nii.gz",
            desc="FOD",
            suffix="dwiref",
            copy=True,
        ),
        name="ds_gm_fod",
    )
    ds_csf_fod = pe.Node(
        DerivativesDataSink(
            label="csf",
            extension=".nii.gz",
            desc="FOD",
            suffix="dwiref",
            copy=True,
        ),
        name="ds_csf_fod",
    )
    workflow.connect(
        [
            (
                inputnode,
                ds_tracts,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (
                tractography_algorithm,
                format_algorithm_node,
                [
                    ("algorithm", "algorithm"),
                ],
            ),
            (
                format_algorithm_node,
                ds_tracts,
                [
                    ("algorithm", "reconstruction"),
                ],
            ),
            (
                tractography,
                ds_tracts,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_sifted_tracts,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (
                format_algorithm_node,
                ds_sifted_tracts,
                [
                    ("algorithm", "reconstruction"),
                ],
            ),
            (
                tcksift_node,
                ds_sifted_tracts,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_sift2_txt,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (
                format_algorithm_node,
                ds_sift2_txt,
                [
                    ("algorithm", "reconstruction"),
                ],
            ),
            (
                tcksift2_node,
                ds_sift2_txt,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                ds_tracts,
                outputnode,
                [
                    ("out_file", "unsifted_tck"),
                ],
            ),
            (
                ds_sifted_tracts,
                outputnode,
                [
                    ("out_file", "sifted_tck"),
                ],
            ),
            (
                ds_sift2_txt,
                outputnode,
                [
                    ("out_file", "sift2_weights"),
                ],
            ),
            (
                inputnode,
                ds_wm_fod,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (
                dwi2fod_node,
                ds_wm_fod,
                [
                    ("wm_odf", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_gm_fod,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (
                dwi2fod_node,
                ds_gm_fod,
                [
                    ("gm_odf", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_csf_fod,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (
                dwi2fod_node,
                ds_csf_fod,
                [
                    ("csf_odf", "in_file"),
                ],
            ),
        ]
    )

    return workflow
