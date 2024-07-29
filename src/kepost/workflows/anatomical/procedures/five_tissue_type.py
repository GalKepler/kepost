import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu

from kepost import config
from kepost.interfaces.bids import DerivativesDataSink

five_tissue_type_entities = {
    "space": "T1w",
    "suffix": "5TT",
    "extension": ".mif",
}


def locate_fs_subject_dir(subject_id: str, fs_subjects_dir: str) -> str:
    """
    Locate the freesurfer subject directory

    Parameters
    ----------
    subject_id : str
        subject id
    fs_subjects_dir : str
        freesurfer subjects directory

    Returns
    -------
    str
        path to the freesurfer subject directory
    """
    from pathlib import Path

    for prefix in ["sub-", ""]:
        result = Path(fs_subjects_dir) / f"{prefix}{subject_id}"
        if result.exists():
            return str(result)

    raise FileNotFoundError(
        f"Could not find freesurfer subject directory for {subject_id}"
    )


def init_five_tissue_type_wf(name: str = "five_tissue_type_wf") -> pe.Workflow:
    """
    Initialize the post-anatomical processing

    Parameters
    ----------
    name : str, optional
        name of the workflow (default: "five_tissue_type_wf")

    Returns
    -------
    pe.Workflow
        the workflow
    """
    wf = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "base_directory",
                "t1w_preproc",
                "t2w_preproc",
                "t1w_mask",
                "fs_subjects_dir",
                "subject_id",
            ]
        ),
        name="inputnode",
    )
    inputnode.inputs.fs_subjects_dir = config.execution.fs_subjects_dir
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["five_tissue_type"]),
        name="outputnode",
    )

    algo_5tt = config.workflow.five_tissue_type_algorithm

    five_tissue_type = pe.Node(
        mrt.Generate5tt(
            algorithm=algo_5tt,
            out_file="5tt.mif",
            nthreads=config.nipype.omp_nthreads,
        ),
        name="five_tissue_type",
    )
    ds_five_tissue_type = pe.Node(
        interface=DerivativesDataSink(
            **five_tissue_type_entities,
            reconstruction=algo_5tt,
        ),
        name="ds_five_tissue_type",
    )

    if algo_5tt == "fsl":
        wf.connect(
            [
                (
                    inputnode,
                    five_tissue_type,
                    [
                        ("t1w_preproc", "in_file"),
                    ],
                ),
            ]
        )
    elif algo_5tt == "hsvs":
        fs_subject_dir = pe.Node(
            niu.Function(
                input_names=["subject_id", "fs_subjects_dir"],
                output_names=["fs_subject_dir"],
                function=locate_fs_subject_dir,
            ),
            name="fs_subject_dir",
        )
        wf.connect(
            [
                (
                    inputnode,
                    fs_subject_dir,
                    [
                        ("subject_id", "subject_id"),
                        ("fs_subjects_dir", "fs_subjects_dir"),
                    ],
                ),
                (fs_subject_dir, five_tissue_type, [("fs_subject_dir", "in_file")]),
            ]
        )

    wf.connect(
        [
            (five_tissue_type, outputnode, [("out_file", "five_tissue_type")]),
            (
                inputnode,
                ds_five_tissue_type,
                [
                    ("base_directory", "base_directory"),
                    ("t1w_preproc", "source_file"),
                ],
            ),
            (five_tissue_type, ds_five_tissue_type, [("out_file", "in_file")]),
        ]
    )
    return wf
