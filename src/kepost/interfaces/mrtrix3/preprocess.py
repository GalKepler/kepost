import os.path as op

from nipype.interfaces.base import File, TraitedSpec, traits
from nipype.interfaces.mrtrix3.base import MRTrix3Base, MRTrix3BaseInputSpec


class MTNormaliseInputSpec(MRTrix3BaseInputSpec):
    wm_odf = File(
        "wm.mif",
        argstr="%s",
        position=-5,
        mandatory=True,
        desc="output WM ODF",
        exists=True,
    )
    out_wm_odf = File(
        "wm.mif",
        argstr="%s",
        position=-4,
        mandatory=False,
        desc="output WM ODF",
        exists=True,
    )
    gm_odf = File(
        "gm.mif",
        argstr="%s",
        position=-3,
        mandatory=True,
        desc="output GM ODF",
        exists=True,
    )
    out_gm_odf = File(
        "gm.mif",
        argstr="%s",
        position=-2,
        mandatory=False,
        desc="output GM ODF",
        exists=True,
    )
    csf_odf = File(
        "csf.mif",
        argstr="%s",
        position=-1,
        mandatory=True,
        desc="output CSF ODF",
        exists=True,
    )
    out_csf_odf = File(
        "csf.mif",
        argstr="%s",
        position=0,
        mandatory=False,
        desc="output CSF ODF",
        exists=True,
    )
    in_mask = File(
        exists=True,
        argstr="-mask %s",
        desc=(
            "only perform computation within the specified " "binary brain mask image"
        ),
    )
    order = traits.Int(
        3,
        argstr="-order %d",
        desc="order of the spherical harmonics basis functions",
    )


class MTNormaliseOutputSpec(TraitedSpec):
    out_wm_odf = File(
        exists=True,
        desc="output WM ODF",
    )
    out_gm_odf = File(
        exists=True,
        desc="output GM ODF",
    )
    out_csf_odf = File(
        exists=True,
        desc="output CSF ODF",
    )


class MTNormalise(MRTrix3Base):
    """
    Multi-tissue informed log-domain intensity normalisation

    Examples
    --------
    >>> from nipype import Workflow
    >>> from nipype.interfaces.mrtrix3 import MTNormalise
    >>> mt_normalise = MTNormalise()
    >>> mt_normalise.inputs.wm_odf = "wm.mif"
    >>> mt_normalise.inputs.out_wm_odf = "wm.mif"
    >>> mt_normalise.inputs.gm_odf = "gm.mif"
    mt_normalise.cmdline
    'mt_normalise -mask mask.mif wm.mif wm.mif gm.mif gm.mif csf.mif csf.mif'
    >>> mt_normalise.run()  # doctest: +SKIP
    """

    _cmd = "mtnormalise"
    input_spec = MTNormaliseInputSpec
    output_spec = MTNormaliseOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_wm_odf"] = op.abspath(self.inputs.out_wm_odf)
        outputs["out_gm_odf"] = op.abspath(self.inputs.out_gm_odf)
        outputs["out_csf_odf"] = op.abspath(self.inputs.out_csf_odf)
        return outputs
