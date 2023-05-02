QUERIES = {
    "mni_to_native_transform": {
        "scope": "subject",
        "entities": {
            "from": "MNI152NLin2009cAsym",
            "to": "T1w",
            "suffix": "xfm",
            "mode": "image",
            "extension": "h5",
        },
    },
    "anatomical_reference": {
        "scope": "subject",
        "entities": {
            "desc": "preproc",
            "suffix": "T1w",
            "datatype": "anat",
            "space": None,
            "extension": ".nii.gz",
        },
    },
    "anatomical_brain_mask": {
        "scope": "subject",
        "entities": {
            "desc": "brain",
            "suffix": "mask",
            "datatype": "anat",
            "space": None,
            "extension": ".nii.gz",
        },
    },
    "dwi_reference": {
        "scope": "session",
        "entities": {
            "datatype": "dwi",
            "suffix": "dwiref",
            "space": "T1w",
            "extension": ".nii.gz",
        },
    },
    "dwi_nifti": {
        "scope": "session",
        "entities": {
            "desc": "preproc",
            "datatype": "dwi",
            "suffix": "dwi",
            "space": "T1w",
            "extension": ".nii.gz",
        },
    },
    "dwi_bval": {
        "scope": "session",
        "entities": {
            "desc": "preproc",
            "datatype": "dwi",
            "suffix": "dwi",
            "space": "T1w",
            "extension": ".bval",
        },
    },
    "dwi_bvec": {
        "scope": "session",
        "entities": {
            "desc": "preproc",
            "datatype": "dwi",
            "suffix": "dwi",
            "space": "T1w",
            "extension": ".bvec",
        },
    },
    "dwi_mask": {
        "scope": "session",
        "entities": {
            "desc": "brain",
            "datatype": "dwi",
            "suffix": "mask",
            "space": "T1w",
            "extension": ".nii.gz",
        },
    },
    "dwi_grad": {
        "scope": "session",
        "entities": {
            "desc": "preproc",
            "datatype": "dwi",
            "suffix": "dwi",
            "space": "T1w",
            "extension": ".b",
        },
    },
    "gm_probabilistic_segmentation": {
        "scope": "subject",
        "entities": {
            "suffix": "probseg",
            "label": "GM",
            "space": None,
            "extension": ".nii.gz",
        },
    },
}
