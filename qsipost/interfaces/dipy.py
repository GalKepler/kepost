import nibabel as nb
import numpy as np
from nipype import logging
from nipype.interfaces.base import File, TraitedSpec, isdefined, traits
from nipype.interfaces.dipy.base import (
    DipyBaseInterfaceInputSpec,
    DipyDiffusionInterface,
)

IFLOGGER = logging.getLogger("nipype.interface")


class ReconstDTIInputSpec(DipyBaseInterfaceInputSpec):
    mask_file = File(exists=True, desc="An optional white matter mask")
    fit_method = traits.Str(desc="The method to fit the tensor", default="WLS")


class ReconstDTIOutputSpec(TraitedSpec):
    tensor_file = File(exists=True, desc="The output tensor file")
    fa_file = File(exists=True, desc="The output fractional anisotropy file")
    ga_file = File(exists=True, desc="The output geodesic anisotropy file")
    rgb_file = File(exists=True, desc="The output RGB file")
    md_file = File(exists=True, desc="The output mean diffusivity file")
    ad_file = File(exists=True, desc="The output axial diffusivity file")
    rd_file = File(exists=True, desc="The output radial diffusivity file")
    mode_file = File(exists=True, desc="The output mode file")
    evec_file = File(exists=True, desc="The output eigenvectors file")
    eval_file = File(exists=True, desc="The output eigenvalues file")


class ReconstDTI(DipyDiffusionInterface):
    """
    Calculates the diffusion tensor model parameters
    Example
    -------
    >>> import nipype.interfaces.dipy as dipy
    >>> dti = dipy.DTI()
    >>> dti.inputs.in_file = 'diffusion.nii'
    >>> dti.inputs.in_bvec = 'bvecs'
    >>> dti.inputs.in_bval = 'bvals'
    >>> dti.run()                                   # doctest: +SKIP
    """

    input_spec = ReconstDTIInputSpec
    output_spec = ReconstDTIOutputSpec

    def _run_interface(self, runtime):
        from dipy.workflows.reconst import ReconstDtiFlow

        flow = ReconstDtiFlow()
        flow.run(
            input_files=self.inputs.in_file,
            bvalues_files=self.inputs.in_bval,
            bvectors_files=self.inputs.in_bvec,
            mask_files=self.inputs.mask_file,
            fit_method=self.inputs.fit_method,
            out_tensor=self._gen_filename("tensor"),
            out_fa=self._gen_filename("fa"),
            out_ga=self._gen_filename("ga"),
            out_rgb=self._gen_filename("rgb"),
            out_md=self._gen_filename("md"),
            out_ad=self._gen_filename("ad"),
            out_rd=self._gen_filename("rd"),
            out_mode=self._gen_filename("mode"),
            out_evec=self._gen_filename("evec"),
            out_eval=self._gen_filename("eval"),
        )

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for metric in [
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
        ]:
            outputs[f"{metric}_file"] = self._gen_filename(metric)

        return outputs
