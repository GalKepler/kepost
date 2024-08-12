import sys
from copy import deepcopy
from pathlib import Path

import dipy
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from niworkflows.interfaces.bids import BIDSInfo
from niworkflows.interfaces.nilearn import NILEARN_VERSION
from packaging.version import Version

from kepost import config
from kepost.atlases.available_atlases.available_atlases import AVAILABLE_ATLASES
from kepost.interfaces.bids import BIDSDataGrabber, collect_data
from kepost.interfaces.bids.bids import DerivativesDataSink
from kepost.interfaces.reports import AboutSummary, SubjectSummary
from kepost.workflows.anatomical import init_anatomical_wf
from kepost.workflows.descriptions import BASE_POSTDESC, BASE_WORKFLOW_DESCRIPTION
from kepost.workflows.diffusion.diffusion import init_diffusion_wf

# from niworkflows.interfaces.bids import BIDSInfo, DerivativesDataSink


# DerivativesDataSink.out_path_base = ""


def init_kepost_wf():
    """
    Initialize the kepost workflow
    """
    atlases = config.workflow.atlases
    if (atlases is None) or (atlases == "all") or (atlases == ["all"]):
        atlases = list(AVAILABLE_ATLASES.keys())
    else:
        if isinstance(atlases, str):
            atlases = [atlases]
    # Validate atlases
    all_atlases = "\n".join(list(AVAILABLE_ATLASES.keys()))
    for atlas in atlases:
        if atlas not in AVAILABLE_ATLASES:
            raise ValueError(
                f"""
                Atlas '{atlas}' not available.
                Please choose from:
                {all_atlases}
                or contact the developers.
                """
            )
    config.workflow.atlases = atlases

    ver = Version(config.environment.version)
    kepost_wf = Workflow(name=f"kepost_{ver.major}_{ver.minor}_wf")
    kepost_wf.base_dir = config.execution.work_dir
    for subject_id in config.execution.participant_label:
        name = f"single_subject_{subject_id}_wf"
        single_subject_wf = init_single_subject_wf(subject_id=subject_id, name=name)
        single_subject_wf.config["execution"]["crashdump_dir"] = str(
            config.execution.output_dir
            / f"sub-{subject_id}"
            / "log"
            / config.execution.run_uuid
        )
        for node in single_subject_wf._get_all_nodes():
            node.config = deepcopy(single_subject_wf.config)
        kepost_wf.add_nodes([single_subject_wf])
    # Dump a copy of the config file into the log directory
    log_dir = (
        Path(config.execution.output_dir)  # type: ignore[operator, attr-defined]
        / f"sub-{subject_id}"
        / "log"
        / config.execution.run_uuid
    )
    log_dir.mkdir(exist_ok=True, parents=True)
    config.to_filename(log_dir / "kepost.toml")
    return kepost_wf


def init_single_subject_wf(subject_id: str, name: str):
    """
    Initialize the single subject workflow
    """

    workflow = Workflow(name=name)  # noqa: F841
    workflow.__desc__ = BASE_WORKFLOW_DESCRIPTION.format(
        kepost_ver=config.environment.version,
        nipype_ver=config.environment.nipype_version,
    )
    workflow.__postdesc__ = BASE_POSTDESC.format(
        nilearn_ver=NILEARN_VERSION,
        mrtrix_ver=mrt.base.Info().version(),
        dipy_ver=dipy.__version__,
    )
    kepost_dir = config.execution.output_dir
    keprep_dir = config.execution.keprep_dir  # noqa: F841
    subject_data, sessions_data = collect_data(
        layout=config.execution.layout, participant_label=subject_id
    )
    combined_data = subject_data.copy()
    for session in sessions_data.keys():
        for value in sessions_data[session].keys():
            if value in combined_data:
                combined_data[value].append(sessions_data[session][value])
            else:
                combined_data[value] = [sessions_data[session][value]]

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "t1w_preproc",
                "t1w_brain_mask",
                "mni_to_native_transform",
                "native_to_mni_transform",
                "gm_probabilistic_segmentation",
                "atlases",
                "subject_id",
                "subjects_dir",
            ]
        ),
        name="inputnode_subject",
    )
    inputnode.inputs.base_directory = kepost_dir
    inputnode.inputs.t1w_preproc = subject_data["t1w_preproc"]
    inputnode.inputs.t1w_brain_mask = subject_data["t1w_brain_mask"]
    inputnode.inputs.mni_to_native_transform = subject_data["mni_to_native_transform"]
    inputnode.inputs.native_to_mni_transform = subject_data["native_to_mni_transform"]
    inputnode.inputs.gm_probabilistic_segmentation = subject_data[
        "gm_probabilistic_segmentation"
    ]
    inputnode.inputs.wm_probabilistic_segmentation = subject_data[
        "wm_probabilistic_segmentation"
    ]
    inputnode.inputs.csf_probabilistic_segmentation = subject_data[
        "csf_probabilistic_segmentation"
    ]
    inputnode.inputs.subject_id = subject_id
    inputnode.inputs.subjects_dir = config.execution.fs_subjects_dir

    bidssrc = pe.Node(
        BIDSDataGrabber(
            subject_data=combined_data,
            subject_id=subject_id,
        ),
        name="bidssrc",
    )
    bids_info = pe.Node(
        BIDSInfo(bids_dir=config.execution.keprep_dir, bids_validate=False),
        name="bids_info",
    )
    summary = pe.Node(
        SubjectSummary(atlases=config.workflow.atlases),
        name="summary",
        run_without_submitting=True,
    )

    about = pe.Node(
        AboutSummary(version=config.environment.version, command=" ".join(sys.argv)),
        name="about",
        run_without_submitting=True,
    )

    ds_report_summary = pe.Node(
        DerivativesDataSink(
            base_directory=str(kepost_dir),  # type: ignore[attr-defined] # noqa: E501
            desc="summary",
            datatype="figures",
            dismiss_entities=["session", "space"],
        ),
        name="ds_report_summary",
        run_without_submitting=True,
    )

    ds_report_about = pe.Node(
        DerivativesDataSink(
            base_directory=str(kepost_dir),  # type: ignore[attr-defined] # noqa: E501
            desc="about",
            datatype="figures",
            dismiss_entities=["session", "space"],
        ),
        name="ds_report_about",
        run_without_submitting=True,
    )
    workflow.connect(
        [
            (bidssrc, bids_info, [("t1w_preproc", "in_file")]),
            (inputnode, summary, [("subjects_dir", "subjects_dir")]),
            (bids_info, summary, [("subject", "subject_id")]),
            (
                bidssrc,
                summary,
                [("t1w_preproc", "t1w"), ("dwi_nifti", "dwi")],
            ),
            (
                bidssrc,
                ds_report_summary,
                [
                    ("dwi_nifti", "source_file"),
                ],
            ),
            (summary, ds_report_summary, [("out_report", "in_file")]),
            (
                bidssrc,
                ds_report_about,
                [("dwi_nifti", "source_file")],
            ),
            (about, ds_report_about, [("out_report", "in_file")]),
        ]
    )
    # Anatomical postprocessing
    anatomical_wf = init_anatomical_wf()
    workflow.connect(
        [
            (
                inputnode,
                anatomical_wf,
                [
                    ("base_directory", "inputnode.base_directory"),
                    ("t1w_preproc", "inputnode.t1w_preproc"),
                    ("t1w_brain_mask", "inputnode.t1w_mask"),
                    ("mni_to_native_transform", "inputnode.mni_to_native_transform"),
                    (
                        "gm_probabilistic_segmentation",
                        "inputnode.gm_probabilistic_segmentation",
                    ),
                    ("subject_id", "inputnode.subject_id"),
                ],
            ),
        ]
    )
    # Diffusion postprocessing
    diffusion_workflows = []
    # num_sessions = len(sessions_data)
    # diffusion_processing_desc = f"""
    # For each of the {num_sessions} DWI runs found per subject {subject_id},
    # the following steps were performed:
    # """
    for session_inputs in sessions_data.values():
        session_workflow = init_diffusion_wf(dwi_data=session_inputs)
        workflow.connect(
            [
                (
                    inputnode,
                    session_workflow,
                    [
                        ("base_directory", "inputnode.base_directory"),
                        ("t1w_preproc", "inputnode.t1w_preproc"),
                        ("t1w_brain_mask", "inputnode.t1w_brain_mask"),
                        (
                            "gm_probabilistic_segmentation",
                            "inputnode.gm_probabilistic_segmentation",
                        ),
                        (
                            "wm_probabilistic_segmentation",
                            "inputnode.wm_probabilistic_segmentation",
                        ),
                        (
                            "csf_probabilistic_segmentation",
                            "inputnode.csf_probabilistic_segmentation",
                        ),
                        (
                            "native_to_mni_transform",
                            "inputnode.native_to_mni_transform",
                        ),
                    ],
                ),
                (
                    anatomical_wf,
                    session_workflow,
                    [
                        (
                            "outputnode.whole_brain_parcellation",
                            "inputnode.whole_brain_t1w_parcellation",
                        ),
                        (
                            "outputnode.gm_cropped_parcellation",
                            "inputnode.gm_cropped_t1w_parcellation",
                        ),
                        (
                            "outputnode.atlas_name",
                            "inputnode.atlas_name",
                        ),
                        (
                            "outputnode.five_tissue_type",
                            "inputnode.five_tissue_type",
                        ),
                    ],
                ),
            ]
        )

        diffusion_workflows.append(session_workflow)
    return workflow
