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

    outputs = {f"out_{key}": f"{key}.nii.gz" for key in TENSOR_PARAMETERS}
    reconst_flow = ReconstDtiFlow()
    reconst_flow.run(
        input_files=dwi_nifti,
        bvalues_files=dwi_bval,
        bvectors_files=dwi_bvec,
        mask_files=dwi_mask,
        fit_method=fit_method,
        save_metrics=TENSOR_PARAMETERS,
    )
    return tuple([outputs[key] for key in TENSOR_PARAMETERS])
