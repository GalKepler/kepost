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
    "native_to_mni_transform": {
        "scope": "subject",
        "entities": {
            "to": "MNI152NLin2009cAsym",
            "from": "T1w",
            "suffix": "xfm",
            "mode": "image",
            "extension": "h5",
        },
    },
    "t1w_preproc": {
        "scope": "subject",
        "entities": {
            "desc": "preproc",
            "suffix": "T1w",
            "datatype": "anat",
            "space": None,
            "extension": ".nii.gz",
        },
    },
    "t1w_brain_mask": {
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
            "space": "dwi",
            "extension": ".nii.gz",
        },
    },
    "dwi_nifti": {
        "scope": "session",
        "entities": {
            "desc": "preproc",
            "datatype": "dwi",
            "suffix": "dwi",
            "space": "dwi",
            "extension": ".nii.gz",
        },
    },
    "dwi_bval": {
        "scope": "session",
        "entities": {
            "desc": "preproc",
            "datatype": "dwi",
            "suffix": "dwi",
            "space": "dwi",
            "extension": ".bval",
        },
    },
    "dwi_bvec": {
        "scope": "session",
        "entities": {
            "desc": "preproc",
            "datatype": "dwi",
            "suffix": "dwi",
            "space": "dwi",
            "extension": ".bvec",
        },
    },
    "dwi_mask": {
        "scope": "session",
        "entities": {
            "desc": "brain",
            "datatype": "dwi",
            "suffix": "mask",
            "space": "dwi",
            "extension": ".nii.gz",
        },
    },
    "dwi_grad": {
        "scope": "session",
        "entities": {
            "desc": "preproc",
            "datatype": "dwi",
            "suffix": "dwi",
            "space": "dwi",
            "extension": ".b",
        },
    },
    "streamlines_unsifted": {
        "scope": "session",
        "entities": {
            "desc": "unsifted",
            "datatype": "dwi",
            "suffix": "streamlines",
            "extension": ".tck",
        },
    },
    "streamlines_sifted": {
        "scope": "session",
        "entities": {
            "desc": "sifted",
            "datatype": "dwi",
            "suffix": "streamlines",
            "extension": ".tck",
        },
    },
    "t1w_to_dwi_transform": {
        "scope": "session",
        "entities": {
            "from": "T1w",
            "to": "dwi",
            "suffix": "xfm",
            "mode": "image",
            "extension": "txt",
        },
    },
    "dwi_to_t1w_transform": {
        "scope": "session",
        "entities": {
            "from": "dwi",
            "to": "T1w",
            "suffix": "xfm",
            "mode": "image",
            "extension": "txt",
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
    "wm_probabilistic_segmentation": {
        "scope": "subject",
        "entities": {
            "suffix": "probseg",
            "label": "WM",
            "space": None,
            "extension": ".nii.gz",
        },
    },
    "csf_probabilistic_segmentation": {
        "scope": "subject",
        "entities": {
            "suffix": "probseg",
            "label": "CSF",
            "space": None,
            "extension": ".nii.gz",
        },
    },
}
