from nipype.interfaces import mrtrix3 as mrt_nipype
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from qsipost.interfaces import mrtrix3 as mrt
from qsipost.interfaces.bids import DerivativesDataSink


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


def init_mrtrix_tractography_wf(
    name="mrtrix_tractography_wf",
    n_tracts: int = 1000,
    angle: int = 45,
) -> pe.Workflow:
    """
    Workflow to perform tractography using MRtrix3.
    """
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
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "tck_file",
            ]
        ),
        name="outputnode",
    )
    dwi2response_node = pe.Node(
        mrt.ResponseSD(
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
            algorithm="msmt_csd",
        ),
        name="dwi2fod",
    )
    mtnormalise_node = pe.Node(
        mrt.MTNormalise(),
        name="mtnormalise",
    )
    gen_5tt_node = pe.Node(
        mrt.Generate5tt(
            algorithm="fsl",
        ),
        name="gen_5tt",
    )
    estimate_tracts_parameters_node = pe.Node(
        niu.Function(
            function=estimate_tractography_parameters,
            input_names=["in_file"],
            output_names=["stepscale", "lenscale_min", "lenscale_max"],
        ),
        name="estimate_tractography_parameters",
    )

    tckgen_node = pe.Node(
        mrt_nipype.Tractography(
            algorithm="SD_Stream",
            select=int(n_tracts * 100),
            angle=angle,
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
    tcksift_node = pe.Node(
        mrt.TCKSift(
            term_number=int(n_tracts),
            fd_scale_gm=True,
        ),
        name="tcksift",
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
                gen_5tt_node,
                [
                    ("t1w_file", "in_file"),
                    ("t1w_mask_file", "in_mask"),
                ],
            ),
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
                gen_5tt_node,
                tckgen_node,
                [
                    ("out_file", "act_file"),
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
                gen_5tt_node,
                tcksift_node,
                [
                    ("out_file", "act_file"),
                ],
            ),
        ]
    )
    return workflow
