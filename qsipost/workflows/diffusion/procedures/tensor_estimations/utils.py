TENSOR_PARAMETERS = [
    "tensor",
    "fa",
    "ga",
    "rgb",
    "md",
    "ad",
    "rd",
    "mode",
    "evec",
    "eval",
]


def estimate_tensors(
    dwi_nifti: str,
    dwi_bvec: str,
    dwi_bval: str,
    dwi_mask: str,
    fit_method: str = "NLLS",
):
    from dipy.workflows.reconst import ReconstDtiFlow

    TENSOR_PARAMETERS = dict(
        tensor="tensors",
        fa="fa",
        ga="ga",
        rgb="rgb",
        md="md",
        ad="ad",
        rd="rd",
        mode="mode",
        evec="evecs",
        eval="evals",
    )
    outputs = {
        f"out_{key}": f"{value}.nii.gz" for key, value in TENSOR_PARAMETERS.items()
    }
    reconst_flow = ReconstDtiFlow()
    reconst_flow.run(
        input_files=dwi_nifti,
        bvalues_files=dwi_bval,
        bvectors_files=dwi_bvec,
        mask_files=dwi_mask,
        fit_method=fit_method,
        **outputs,
    )
    return tuple(list(outputs.values()))
