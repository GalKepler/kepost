from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from packaging.version import Version

from kepost import config
from kepost.atlases.available_atlases.available_atlases import AVAILABLE_ATLASES
from kepost.interfaces.bids.utils import collect_data


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
    atlases = {atlas: AVAILABLE_ATLASES[atlas] for atlas in atlases}

    ver = Version(config.environment.version)
    kepost_wf = pe.Workflow(name=f"kepost_{ver.major}_{ver.minor}_wf")
    kepost_wf.base_dir = config.execution.work_dir
    for subject_id in config.execution.participant_label:
        name = f"single_subject_{subject_id}_wf"
        single_subject_wf = init_single_subject_wf(
            subject_id=subject_id, atlases=atlases, name=name
        )
        single_subject_wf.config["execution"]["crashdump_dir"] = str(
            config.execution.output_dir
            / f"sub-{subject_id}"
            / "log"
            / config.execution.run_uuid
        )


def init_single_subject_wf(subject_id: str, atlases: dict, name: str):
    """
    Initialize the single subject workflow
    """
    single_subject_wf = pe.Workflow(name=name)  # noqa: F841
    kepost_dir = config.execution.output_dir
    keprep_dir = config.execution.keprep_dir  # noqa: F841
    subject_data, sessions_data = collect_data(
        layout=config.execution.layout, participant_label=subject_id
    )
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "anatomical_reference",
                "anatomical_brain_mask",
                "mni_to_native_transform",
                "native_to_mni_transform",
                "gm_probabilistic_segmentation",
                "atlases",
                "subject_id",
            ]
        ),
        name="inputnode_subject",
    )
    inputnode.inputs.base_directory = kepost_dir
    inputnode.inputs.atlases = atlases
    inputnode.inputs.anatomical_reference = subject_data["anatomical_reference"]
    inputnode.inputs.anatomical_brain_mask = subject_data["anatomical_brain_mask"]
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
