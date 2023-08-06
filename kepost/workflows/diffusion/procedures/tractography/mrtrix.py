from typing import Union

from pathlib import Path

from nipype.interfaces import mrtrix3 as mrt_nipype
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost import config
from kepost.interfaces import mrtrix3 as mrt
from kepost.interfaces.bids import DerivativesDataSink
from kepost.workflows.diffusion.procedures.tractography.coregisteration import (
    init_5tt_coreg_wf,
)


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

    data = nib.load(in_file)
    pixdim = data.header["pixdim"][1]
    stepscale = stepscale * pixdim
    lenscale_min = lenscale_min * pixdim
    lenscale_max = lenscale_max * pixdim
    return stepscale, lenscale_min, lenscale_max


def _find_freesurfer_dir(dwi_file: str, freesurfer_dir: str = None) -> str:
    """
    Locates the freesurfer directory for a given subject

    Parameters
    ----------
    freesurfer_dir : Union[Path,str]
        Base directory for freesurfer output
    subject : str
        Subject ID

    Returns
    -------
    str
        Path to freesurfer directory
    """
    from pathlib import Path

    from bids.layout import parse_file_entities

    from kepost import config

    subject = parse_file_entities(dwi_file)["subject"]

    if not freesurfer_dir:
        keprep_dir = config.execution.keprep_dir
        freesurfer_dir = Path(keprep_dir) / "freesurfer"
    if not subject.startswith("sub-"):
        subject = f"sub-{subject}"
    return freesurfer_dir / subject


def init_mrtrix_tractography_wf(
    name="mrtrix_tractography_wf",
) -> pe.Workflow:
    """
    Workflow to perform tractography using MRtrix3.
    """
    keprep_dir = config.execution.keprep_dir
    freesurfer_dir = Path(keprep_dir) / "freesurfer"

    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_file",
                "dwi_reference",
                "dwi_grad",
                "dwi_mask_file",
                "t1w_file",
                "t1w_mask_file",
                "t1w_to_dwi_transform",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "unfiltered_tracts",
                "sift_tracts",
            ]
        ),
        name="outputnode",
    )
    dwi2response_node = pe.Node(
        mrt.ResponseSD(
            nthreads=config.nipype.omp_nthreads,
            algorithm="dhollander",
            wm_file="wm.txt",
            gm_file="gm.txt",
            csf_file="csf.txt",
            voxels_file="voxels.mif",
        ),
        name="dwi2response",
    )
    dwi2fod_node = pe.Node(
        mrt.EstimateFOD(
            nthreads=config.nipype.omp_nthreads,
            algorithm="msmt_csd",
        ),
        name="dwi2fod",
    )
    mtnormalise_node = pe.Node(
        mrt.MTNormalise(nthreads=config.nipype.omp_nthreads),
        name="mtnormalise",
    )
    get_freesurfer_node = pe.Node(
        niu.Function(
            function=_find_freesurfer_dir,
            input_names=["freesurfer_dir", "dwi_file"],
            output_names=["freesurfer_dir"],
        ),
        name="get_freesurfer_dir",
    )
    get_freesurfer_node.inputs.freesurfer_dir = freesurfer_dir
    gen_5tt_node = pe.Node(
        mrt.Generate5tt(
            nthreads=config.nipype.omp_nthreads,
            algorithm="hsvs",
            sgm_amyg_hipp=True,
            white_stem=True,
        ),
        name="gen_5tt",
    )
    coreg_5tt_wf = init_5tt_coreg_wf()
    estimate_tracts_parameters_node = pe.Node(
        niu.Function(
            function=estimate_tractography_parameters,
            input_names=[
                "in_file",
                "stepscale",
                "lenscale_min",
                "lenscale_max",
            ],
            output_names=["stepscale", "lenscale_min", "lenscale_max"],
        ),
        name="estimate_tractography_parameters",
    )
    estimate_tracts_parameters_node.inputs.stepscale = config.workflow.stepscale
    estimate_tracts_parameters_node.inputs.lenscale_min = config.workflow.lenscale_min
    estimate_tracts_parameters_node.inputs.lenscale_max = config.workflow.lenscale_max

    tckgen_node = pe.Node(
        mrt_nipype.Tractography(
            nthreads=config.nipype.omp_nthreads,
            algorithm=config.workflow.tractography_algorithm,
            select=config.workflow.n_tracts,
            angle=config.workflow.angle,
        ),
        name="tckgen",
    )

    ds_tracts = pe.Node(
        DerivativesDataSink(
            suffix="tracts",
            extension=".tck",
            desc="unfiltered",
            reconstruction="mrtrix",
        ),
        name="ds_unfiltered_tracts",
        run_without_submitting=True,
    )
    workflow.connect(
        [
            (
                inputnode,
                dwi2response_node,
                [
                    ("dwi_file", "in_file"),
                    ("dwi_grad", "grad_file"),
                    ("dwi_mask_file", "in_mask"),
                ],
            ),
            (
                inputnode,
                dwi2fod_node,
                [
                    ("dwi_file", "in_file"),
                    ("dwi_grad", "grad_file"),
                    ("dwi_mask_file", "in_mask"),
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
                dwi2fod_node,
                mtnormalise_node,
                [
                    ("wm_odf", "in_wm_fod"),
                    ("gm_odf", "in_gm_fod"),
                    ("csf_odf", "in_csf_fod"),
                ],
            ),
            (
                inputnode,
                mtnormalise_node,
                [
                    ("dwi_mask_file", "in_mask"),
                ],
            ),
            (
                inputnode,
                get_freesurfer_node,
                [
                    ("dwi_file", "dwi_file"),
                ],
            ),
            (
                get_freesurfer_node,
                gen_5tt_node,
                [
                    ("freesurfer_dir", "freesurfer_dir"),
                ],
            ),
            (
                inputnode,
                coreg_5tt_wf,
                [
                    ("dwi_reference", "inputnode.dwi_reference"),
                    ("t1w_file", "inputnode.t1w_file"),
                    ("t1w_to_dwi_transform", "inputnode.t1w_to_dwi_transform"),
                ],
            ),
            (gen_5tt_node, coreg_5tt_wf, [("out_file", "inputnode.5tt_file")]),
            (
                mtnormalise_node,
                tckgen_node,
                [
                    ("out_wm_fod", "in_file"),
                ],
            ),
            (
                inputnode,
                estimate_tracts_parameters_node,
                [
                    ("dwi_file", "in_file"),
                ],
            ),
            (
                coreg_5tt_wf,
                tckgen_node,
                [
                    ("outputnode.5tt_coreg", "act_file"),
                ],
            ),
            (
                estimate_tracts_parameters_node,
                tckgen_node,
                [
                    ("stepscale", "step_size"),
                    ("lenscale_min", "min_length"),
                    ("lenscale_max", "max_length"),
                ],
            ),
            (
                inputnode,
                tckgen_node,
                [
                    ("dwi_mask_file", "seed_image"),
                ],
            ),
            (
                tckgen_node,
                ds_tracts,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                inputnode,
                ds_tracts,
                [
                    ("base_directory", "base_directory"),
                    ("dwi_file", "source_file"),
                ],
            ),
            (
                ds_tracts,
                outputnode,
                [
                    ("out_file", "unfiltered_tracts"),
                ],
            ),
        ]
    )
    in_tracts = "unfiltered_tracts"
    if config.workflow.do_sift_filtering:
        in_tracts = "sift_tracts"
        tcksift_kwargs = {}
        if config.workflow.sift_term_number:
            tcksift_kwargs["term_number"] = config.workflow.sift_term_number
        elif config.workflow.sift_term_ratio:
            tcksift_kwargs["term_ratio"] = config.workflow.sift_term_ratio
        else:
            raise ValueError(
                """
                Either sift_term_number or sift_term_ratio must be specified 
                if sift_filtering is set to True.
                """
            )
        tcksift_node = pe.Node(
            mrt.TCKSift(
                nthreads=config.nipype.omp_nthreads,
                **tcksift_kwargs,
                fd_scale_gm=True,
            ),
            name="tcksift",
        )
        ds_tcksift_node = pe.Node(
            DerivativesDataSink(
                suffix="tracts",
                extension=".tck",
                desc="sift",
                reconstruction="mrtrix",
            ),
            name="ds_sift_tracts",
            run_without_submitting=True,
        )
        workflow.connect(
            [
                (
                    tckgen_node,
                    tcksift_node,
                    [
                        ("out_file", "in_tracks"),
                    ],
                ),
                (
                    mtnormalise_node,
                    tcksift_node,
                    [
                        ("out_wm_fod", "in_fod"),
                    ],
                ),
                (
                    coreg_5tt_wf,
                    tcksift_node,
                    [
                        ("outputnode.5tt_coreg", "act_file"),
                    ],
                ),
                (
                    tcksift_node,
                    outputnode,
                    [
                        ("out_file", "tck_file"),
                    ],
                ),
                (
                    tcksift_node,
                    ds_tcksift_node,
                    [
                        ("out_file", "in_file"),
                    ],
                ),
                (
                    inputnode,
                    ds_tcksift_node,
                    [
                        ("base_directory", "base_directory"),
                        ("dwi_file", "source_file"),
                    ],
                ),
                (
                    ds_tcksift_node,
                    outputnode,
                    [
                        ("out_file", "sift_tracts"),
                    ],
                ),
            ]
        )

    return workflow
