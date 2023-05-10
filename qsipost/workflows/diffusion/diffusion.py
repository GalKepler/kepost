from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from qsipost import config
from qsipost.workflows.diffusion.procedures.coregister_atlas import (
    init_coregistration_wf,
)
from qsipost.workflows.diffusion.procedures.tensor_estimations.tensor_estimation import (
    init_tensor_estimation_wf,
)
from qsipost.workflows.diffusion.procedures.tractography.connectome import (
    init_connectome_wf,
)
from qsipost.workflows.diffusion.procedures.tractography.tractography import (
    init_tractography_wf,
)


def init_diffusion_wf(
    dwi_data: dict,
) -> pe.Workflow:
    """
    Initialize the diffusion postprocessing workflow.

    Parameters
    ----------
    dwi_data : dict
        The dictionary of data for the diffusion data.
    prefix : str, optional
        The name of the workflow, by default "dwi_postprocess"

    Returns
    -------
    pe.Workflow
        The diffusion postprocessing workflow
    """
    name = _get_wf_name(dwi_data["dwi_nifti"])
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "base_directory",
                "dwi_reference",
                "dwi_nifti",
                "dwi_bval",
                "dwi_bvec",
                "dwi_grad",
                "dwi_mask",
                "atlas_name",
                "whole_brain_t1w_parcellation",
                "gm_cropped_t1w_parcellation",
                "dipy_fit_method",
                "t1w_file",
                "t1w_mask_file",
            ]
        ),
        name="inputnode",
    )
    inputnode.inputs.dwi_nifti = dwi_data["dwi_nifti"]
    inputnode.inputs.dwi_bvec = dwi_data["dwi_bvec"]
    inputnode.inputs.dwi_bval = dwi_data["dwi_bval"]
    inputnode.inputs.dwi_grad = dwi_data["dwi_grad"]
    inputnode.inputs.dwi_mask = dwi_data["dwi_mask"]
    inputnode.inputs.dwi_reference = dwi_data["dwi_reference"]
    inputnode.inputs.dipy_fit_method = config.workflow.dipy_reconstruction_method

    outputnode = pe.Node(
        interface=niu.IdentityInterface(
            fields=[
                "whole_brain_parcellation",
                "gm_cropped_parcellation",
            ]
        ),
        name="outputnode",
    )
    coregister_wf = init_coregistration_wf()
    tensor_estimation_wf = init_tensor_estimation_wf()
    tractography_wf = init_tractography_wf()
    workflow.connect(
        [
            (
                inputnode,
                coregister_wf,
                [
                    ("dwi_nifti", "inputnode.dwi_reference"),
                    (
                        "whole_brain_t1w_parcellation",
                        "inputnode.whole_brain_parcellation",
                    ),
                    (
                        "gm_cropped_t1w_parcellation",
                        "inputnode.gm_cropped_parcellation",
                    ),
                    ("atlas_name", "inputnode.atlas_name"),
                    ("base_directory", "inputnode.base_directory"),
                ],
            ),
            (
                coregister_wf,
                outputnode,
                [
                    (
                        "outputnode.whole_brain_parcellation",
                        "whole_brain_parcellation",
                    ),
                    (
                        "outputnode.gm_cropped_parcellation",
                        "gm_cropped_parcellation",
                    ),
                ],
            ),
            (
                inputnode,
                tensor_estimation_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.dwi_nifti"),
                    ("dwi_bval", "inputnode.dwi_bval"),
                    ("dwi_bvec", "inputnode.dwi_bvec"),
                    ("dwi_grad", "inputnode.dwi_grad"),
                    ("dwi_mask", "inputnode.dwi_mask"),
                    ("dipy_fit_method", "inputnode.dipy_fit_method"),
                ],
            ),
        ]
    )
    if config.workflow.do_tractography:
        workflow.connect(
            [
                (
                    inputnode,
                    tractography_wf,
                    [
                        ("base_directory", "inputnode.base_directory"),
                        ("dwi_reference", "inputnode.dwi_reference"),
                        ("dwi_nifti", "inputnode.dwi_nifti"),
                        ("dwi_bval", "inputnode.dwi_bval"),
                        ("dwi_bvec", "inputnode.dwi_bvec"),
                        ("dwi_grad", "inputnode.dwi_grad"),
                        ("dwi_mask", "inputnode.dwi_mask"),
                        ("t1w_file", "inputnode.t1w_file"),
                        ("t1w_mask_file", "inputnode.t1w_mask_file"),
                    ],
                ),
            ]
        )
        connectome_wf = init_connectome_wf()
        workflow.connect(
            [
                (
                    inputnode,
                    connectome_wf,
                    [
                        ("base_directory", "inputnode.base_directory"),
                        ("atlas_name", "inputnode.atlas_name"),
                    ],
                ),
                (
                    coregister_wf,
                    connectome_wf,
                    [
                        (
                            "outputnode.whole_brain_parcellation",
                            "inputnode.in_parc",
                        )
                    ],
                ),
            ]
        )
        if config.workflow.do_sift_filtering:
            workflow.connect(
                [
                    (
                        tractography_wf,
                        connectome_wf,
                        [
                            (
                                "mrtrix_tractography_wf.outputnode.sift_tracts",
                                "inputnode.in_tracts",
                            ),
                        ],
                    ),
                ]
            )
        else:
            workflow.connect(
                [
                    (
                        tractography_wf,
                        connectome_wf,
                        [
                            (
                                "mrtrix_tractography_wf.outputnode.unfiltered_tracts",
                                "inputnode.in_tracts",
                            ),
                        ],
                    ),
                ]
            )
    return workflow


def _get_wf_name(filename):
    """
    Derive the workflow name for supplied DWI file.
    Examples
    --------
    >>> _get_wf_name("/completely/made/up/path/sub-01_dir-AP_acq-64grad_dwi.nii.gz")
    'dwi_preproc_dir_AP_acq_64grad_wf'
    >>> _get_wf_name("/completely/made/up/path/sub-01_dir-RL_run-01_echo-1_dwi.nii.gz")
    'dwi_preproc_dir_RL_run_01_echo_1_wf'
    """
    from pathlib import Path

    fname = Path(filename).name.rpartition(".nii")[0].replace("_dwi", "_wf")
    fname_nosub = "_".join(fname.split("_")[1:])
    return f"dwi_postproc_{fname_nosub.replace('.', '_').replace(' ', '').replace('-', '_')}"
