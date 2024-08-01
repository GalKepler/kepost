from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from kepost import config
from kepost.workflows.diffusion.procedures import (
    init_connectome_wf,
    init_coregistration_wf,
    init_parcellations_wf,
    init_qc_wf,
    init_tensor_estimation_wf,
    init_tissue_coregistration_wf,
    init_tractography_wf,
)
from kepost.workflows.diffusion.procedures.tensor_estimations.dipy.dipy import (
    TENSOR_PARAMETERS as dipy_parameters,
)
from kepost.workflows.diffusion.procedures.tensor_estimations.mrtrix3.mrtrix3 import (
    TENSOR_PARAMETERS as mrtrix3_parameters,
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
                "atlas_name",
                "dwi_reference",
                "dwi_nifti",
                "dwi_bval",
                "dwi_bvec",
                "dwi_grad",
                "dwi_mask",
                "dwi_to_t1w_transform",
                "t1w_to_dwi_transform",
                "atlas_name",
                "whole_brain_t1w_parcellation",
                "gm_cropped_t1w_parcellation",
                "dipy_fit_method",
                "t1w_preproc",
                "t1w_brain_mask",
                "gm_probabilistic_segmentation",
                "wm_probabilistic_segmentation",
                "csf_probabilistic_segmentation",
                "five_tissue_type",
                "native_to_mni_transform",
                "eddy_qc",
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
    inputnode.inputs.t1w_to_dwi_transform = dwi_data["t1w_to_dwi_transform"]
    inputnode.inputs.dwi_to_t1w_transform = dwi_data["dwi_to_t1w_transform"]
    inputnode.inputs.eddy_qc = dwi_data["eddy_qc"]
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
    workflow.connect(
        [
            (
                inputnode,
                coregister_wf,
                [
                    ("t1w_preproc", "inputnode.t1w_preproc"),
                    ("dwi_reference", "inputnode.dwi_reference"),
                    (
                        "t1w_to_dwi_transform",
                        "inputnode.t1w_to_dwi_transform",
                    ),
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
        ]
    )
    tissue_coreg_wf = init_tissue_coregistration_wf()
    tensor_estimation_wf = init_tensor_estimation_wf()
    workflow.connect(
        [
            (
                inputnode,
                tissue_coreg_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_reference", "inputnode.dwi_reference"),
                    ("t1w_preproc", "inputnode.t1w_preproc"),
                    ("t1w_to_dwi_transform", "inputnode.t1w_to_dwi_transform"),
                    ("gm_probabilistic_segmentation", "inputnode.gm_probseg"),
                    ("wm_probabilistic_segmentation", "inputnode.wm_probseg"),
                    (
                        "csf_probabilistic_segmentation",
                        "inputnode.csf_probseg",
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
                    ("dwi_reference", "inputnode.dwi_bzero"),
                    ("dipy_fit_method", "inputnode.dipy_fit_method"),
                    (
                        "native_to_mni_transform",
                        "inputnode.native_to_mni_transform",
                    ),
                    ("t1w_preproc", "inputnode.t1w_reference"),
                    ("dwi_to_t1w_transform", "inputnode.dwi_to_t1w_transform"),
                ],
            ),
        ]
    )
    qc_wf = init_qc_wf()
    workflow.connect(
        [
            (
                inputnode,
                qc_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.dwi_file"),
                    ("dwi_grad", "inputnode.dwi_grad"),
                    ("dwi_mask", "inputnode.brain_mask"),
                    ("dwi_bval", "inputnode.dwi_bval"),
                    ("eddy_qc", "inputnode.eddy_qc"),
                ],
            ),
            (
                tissue_coreg_wf,
                qc_wf,
                [
                    ("outputnode.gm_probseg_dwiref", "inputnode.gm_probseg"),
                    ("outputnode.wm_probseg_dwiref", "inputnode.wm_probseg"),
                    ("outputnode.csf_probseg_dwiref", "inputnode.csf_probseg"),
                ],
            ),
        ]
    )
    dipy_parcellations_wf = init_parcellations_wf(
        inputs=dipy_parameters, software="dipy"
    )
    mrtrix3_parcellations_wf = init_parcellations_wf(
        inputs=mrtrix3_parameters, software="mrtrix3"
    )
    workflow.connect(
        [
            (
                inputnode,
                dipy_parcellations_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.source_file"),
                    ("atlas_name", "inputnode.atlas_name"),
                ],
            ),
            (
                inputnode,
                mrtrix3_parcellations_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_nifti", "inputnode.source_file"),
                    ("atlas_name", "inputnode.atlas_name"),
                ],
            ),
            (
                tensor_estimation_wf,
                dipy_parcellations_wf,
                [
                    (f"dipy_tensor_wf.outputnode.{param}", f"inputnode.{param}")
                    for param in dipy_parameters
                ],
            ),
            (
                tensor_estimation_wf,
                mrtrix3_parcellations_wf,
                [
                    (f"mrtrix3_tensor_wf.outputnode.{param}", f"inputnode.{param}")
                    for param in mrtrix3_parameters
                ],
            ),
            (
                tensor_estimation_wf,
                dipy_parcellations_wf,
                [
                    (
                        "outputnode.acq_label",
                        "inputnode.acq_label",
                    )
                ],
            ),
            (
                tensor_estimation_wf,
                mrtrix3_parcellations_wf,
                [
                    (
                        "outputnode.acq_label",
                        "inputnode.acq_label",
                    )
                ],
            ),
        ]
    )
    if config.workflow.parcellate_gm:
        workflow.connect(
            [
                (
                    coregister_wf,
                    dipy_parcellations_wf,
                    [
                        (
                            "outputnode.gm_cropped_parcellation",
                            "inputnode.atlas_nifti",
                        ),
                    ],
                ),
                (
                    coregister_wf,
                    mrtrix3_parcellations_wf,
                    [
                        (
                            "outputnode.gm_cropped_parcellation",
                            "inputnode.atlas_nifti",
                        ),
                    ],
                ),
            ]
        )
    else:
        workflow.connect(
            [
                (
                    coregister_wf,
                    dipy_parcellations_wf,
                    [
                        (
                            "outputnode.whole_brain_parcellation",
                            "inputnode.atlas_nifti",
                        ),
                    ],
                ),
                (
                    coregister_wf,
                    mrtrix3_parcellations_wf,
                    [
                        (
                            "outputnode.whole_brain_parcellation",
                            "inputnode.atlas_nifti",
                        ),
                    ],
                ),
            ]
        )

    tractography_wf = init_tractography_wf()
    workflow.connect(
        [
            (
                inputnode,
                tractography_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("dwi_reference", "inputnode.dwi_reference"),
                    ("dwi_nifti", "inputnode.dwi_nifti"),
                    ("dwi_grad", "inputnode.dwi_grad"),
                    ("dwi_mask", "inputnode.dwi_mask"),
                    ("t1w_preproc", "inputnode.t1w_reference"),
                    (
                        "t1w_to_dwi_transform",
                        "inputnode.t1w_to_dwi_transform",
                    ),
                    ("five_tissue_type", "inputnode.five_tissue_type"),
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
                ],
            ),
            (
                coregister_wf,
                connectome_wf,
                [
                    (
                        "outputnode.whole_brain_parcellation",
                        "inputnode.atlas_nifti",
                    )
                ],
            ),
            (
                tractography_wf,
                connectome_wf,
                [
                    (
                        "outputnode.unsifted_tck",
                        "inputnode.tracts_unsifted",
                    ),
                    (
                        "outputnode.sifted_tck",
                        "inputnode.tracts_sifted",
                    ),
                    ("outputnode.sift2_weights", "inputnode.tck_weights"),
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
