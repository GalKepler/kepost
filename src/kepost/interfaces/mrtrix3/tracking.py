import os.path as op

from nipype.interfaces.base import Directory, File, TraitedSpec, traits
from nipype.interfaces.mrtrix3.base import MRTrix3Base, MRTrix3BaseInputSpec


class TckSift2InputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-3,
        desc="input tractogram",
    )
    in_fod = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="input FOD image",
    )
    out_file = File(
        "sift2_weights.txt",
        argstr="%s",
        mandatory=False,
        position=-1,
        usedefault=True,
        desc="output sift tractogram",
    )
    proc_mask = File(
        exists=True,
        argstr="-proc_mask %s",
        desc="mask image containing the processing mask weights for the model.",
    )
    act_file = File(
        exists=True,
        argstr="-act %s",
        desc="ACT five-tissue-type segmentation image",
    )
    fd_scale_gm = traits.Bool(
        default_value=True,
        argstr="-fd_scale_gm",
        desc="heuristically downsize the fibre density estimates based on the presence of GM in the voxel.",  # pylint: disable=line-too-long
    )
    no_dilate_lut = traits.Bool(
        default_value=False,
        argstr="-no_dilate_lut",
        desc="do NOT dilate FOD lobe lookup tables.",
    )
    make_null_lobes = traits.Bool(
        default_value=False,
        argstr="-make_null_lobes",
        desc="add an additional FOD lobe to each voxel, with zero integral, that covers all directions with zero / negative FOD amplitudes",  # pylint: disable=line-too-long
    )
    remove_untracked = traits.Bool(
        default_value=False,
        argstr="-remove_untracked",
        desc="Remove FOD lobes that do not have any streamline density attributed to them.",  # pylint: disable=line-too-long
    )
    fd_thresh = traits.Float(
        argstr="-fd_thresh %f",
        desc="fibre density threshold.",
    )
    out_csv = File(
        exists=False,
        argstr="-csv %s",
        desc="output statistics of execution per iteration to a .csv file",
    )
    out_mu = File(
        exists=False,
        argstr="-out_mu %s",
        desc="output the final value of SIFT proportionality coefficient mu to a text file",  # pylint: disable=line-too-long
    )
    output_debug = traits.Directory(
        exists=False,
        argstr="-output_debug %s",
        desc="output debugging information to a directory",
    )
    out_coeffs = File(
        exists=False,
        argstr="-out_coeffs %s",
        desc="output text file containing the weighting coefficient for each streamline",  # pylint: disable=line-too-long
    )


class TckSift2OutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output sift tractogram")
    out_csv = File(exists=True, desc="output statistics of execution per iteration")
    out_mu = File(
        exists=True,
        desc="output the final value of SIFT proportionality coefficient mu to a text file",  # pylint: disable=line-too-long
    )
    out_coeffs = File(
        exists=True,
        desc="output text file containing the weighting coefficient for each streamline",  # pylint: disable=line-too-long
    )


class TckSift2(MRTrix3Base):  # pylint: disable=abstract-method
    """
    Optimise per-streamline cross-section multipliers to match
    a whole-brain tractogram to fixel-wise fibre densities

    Example
    -------
    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> sift = mrt.TCKSift2()
    >>> sift.inputs.in_file = 'tracks.tck'
    >>> sift.inputs.in_fod = 'fod.mif'
    >>> sift.cmdline
    'tcksift2 tracks.tck fod.mif sift2_weights.txt'
    >>> sift.run()  # doctest: +SKIP
    """

    _cmd = "tcksift2"
    input_spec = TckSift2InputSpec
    output_spec = TckSift2OutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        if self.inputs.out_csv:
            outputs["out_csv"] = op.abspath(self.inputs.out_csv)
        if self.inputs.out_mu:
            outputs["out_mu"] = op.abspath(self.inputs.out_mu)
        if self.inputs.out_coeffs:
            outputs["out_coeffs"] = op.abspath(self.inputs.out_coeffs)
        return outputs


class TckSiftInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-3,
        desc="input tractogram",
    )
    in_fod = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="input FOD image",
    )
    out_file = File(
        "sift.tck",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output sift tractogram",
    )
    act_file = File(
        exists=True,
        argstr="-act %s",
        desc="ACT five-tissue-type segmentation image",
    )
    fd_scale_gm = traits.Bool(
        default_value=True,
        argstr="-fd_scale_gm",
        desc="heuristically downsize the fibre density estimates based on the presence of GM in the voxel.",  # pylint: disable=line-too-long
    )
    no_dilate_lut = traits.Bool(
        default_value=False,
        argstr="-no_dilate_lut",
        desc="do NOT dilate FOD lobe lookup tables.",
    )
    remove_untracked = traits.Bool(
        default_value=False,
        argstr="-remove_untracked",
        desc="Femove FOD lobes that do not have any streamline density attributed to them.",  # pylint: disable=line-too-long
    )
    fd_thresh = traits.Float(
        argstr="-fd_thresh %f",
        desc="fibre density threshold.",
    )
    out_csv = File(
        exists=False,
        argstr="-csv %s",
        desc="output statistics of execution per iteration to a .csv file",
    )
    out_mu = File(
        exists=False,
        argstr="-out_mu %s",
        desc="output the final value of SIFT proportionality coefficient mu to a text file",  # pylint: disable=line-too-long
    )
    output_debug = traits.Directory(
        exists=False,
        argstr="-output_debug %s",
        desc="output debugging information to a directory",
    )
    out_selection = File(
        exists=False,
        argstr="-out_selection %s",
        desc="output a text file containing the binary selection of streamlines",
    )
    term_number = traits.Int(
        argstr="-term_number %d",
        desc="continue filtering until this number of streamlines remain",
    )
    term_ratio = traits.Float(
        argstr="-term_ratio %f",
        desc="termination ratio; defined as the ratio between reduction in cost function, and reduction in density of streamlines",  # pylint: disable=line-too-long
    )
    term_mu = traits.Float(
        argstr="-term_mu %f",
        desc="terminate filtering once the SIFT proportionality coefficient reaches a given value",  # pylint: disable=line-too-long
    )


class TckSiftOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output sift tractogram")
    out_csv = File(exists=True, desc="output statistics of execution per iteration")
    out_mu = File(
        exists=True,
        desc="output the final value of SIFT proportionality coefficient mu to a text file",  # pylint: disable=line-too-long
    )
    out_selection = File(
        exists=True,
        desc="output a text file containing the binary selection of streamlines",
    )


class TckSift(MRTrix3Base):  # pylint: disable=abstract-method
    """
    Select the streamlines from a tractogram that are most consistent with the
    underlying FOD image.

    Example
    -------
    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> sift = mrt.TCKSift()
    >>> sift.inputs.in_file = 'tracks.tck'
    >>> sift.inputs.in_fod = 'fod.mif'
    >>> sift.cmdline
    'tcksift tracks.tck fod.mif sift.tck'
    >>> sift.run()  # doctest: +SKIP
    """

    _cmd = "tcksift"
    input_spec = TckSiftInputSpec
    output_spec = TckSiftOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        if self.inputs.out_csv:
            outputs["out_csv"] = op.abspath(self.inputs.out_csv)
        if self.inputs.out_mu:
            outputs["out_mu"] = op.abspath(self.inputs.out_mu)
        if self.inputs.out_selection:
            outputs["out_selection"] = op.abspath(self.inputs.out_selection)
        return outputs


class DWIPreprocInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=0,
        mandatory=True,
        desc="input DWI image",
    )
    out_file = File(
        "preproc.mif",
        argstr="%s",
        mandatory=True,
        position=1,
        usedefault=True,
        desc="output file after preprocessing",
    )
    rpe_options = traits.Enum(
        "none",
        "pair",
        "all",
        "header",
        argstr="-rpe_%s",
        position=2,
        mandatory=True,
        desc='Specify acquisition phase-encoding design. "none" for no reversed phase-encoding image, "all" for all DWIs have opposing phase-encoding acquisition, "pair" for using a pair of b0 volumes for inhomogeneity field estimation only, and "header" for phase-encoding information can be found in the image header(s)',
    )
    pe_dir = traits.Str(
        argstr="-pe_dir %s",
        desc="Specify the phase encoding direction of the input series, can be a signed axis number (e.g. -0, 1, +2), an axis designator (e.g. RL, PA, IS), or NIfTI axis codes (e.g. i-, j, k)",
    )
    ro_time = traits.Float(
        argstr="-readout_time %f",
        desc="Total readout time of input series (in seconds)",
    )
    in_epi = File(
        exists=True,
        argstr="-se_epi %s",
        desc="Provide an additional image series consisting of spin-echo EPI images, which is to be used exclusively by topup for estimating the inhomogeneity field (i.e. it will not form part of the output image series)",
    )
    align_seepi = traits.Bool(
        argstr="-align_seepi",
        desc="Achieve alignment between the SE-EPI images used for inhomogeneity field estimation, and the DWIs",
    )
    json_import = File(
        exists=True,
        argstr="-json_import %s",
        desc="Import image header information from an associated JSON file (may be necessary to determine phase encoding information)",
    )
    topup_options = traits.Str(
        argstr='-topup_options "%s"',
        desc="Manually provide additional command-line options to the topup command",
    )
    eddy_options = traits.Str(
        argstr='-eddy_options "%s"',
        desc="Manually provide additional command-line options to the eddy command",
    )
    eddy_mask = File(
        exists=True,
        argstr="-eddy_mask %s",
        desc="Provide a processing mask to use for eddy, instead of having dwifslpreproc generate one internally using dwi2mask",
    )
    eddy_slspec = File(
        exists=True,
        argstr="-eddy_slspec %s",
        desc="Provide a file containing slice groupings for eddy's slice-to-volume registration",
    )
    eddyqc_text = Directory(
        exists=False,
        argstr="-eddyqc_text %s",
        desc="Copy the various text-based statistical outputs generated by eddy, and the output of eddy_qc (if installed), into an output directory",
    )
    eddyqc_all = Directory(
        exists=False,
        argstr="-eddyqc_all %s",
        desc="Copy ALL outputs generated by eddy (including images), and the output of eddy_qc (if installed), into an output directory",
    )
    out_grad_mrtrix = File(
        "grad.b",
        argstr="-export_grad_mrtrix %s",
        desc="export new gradient files in mrtrix format",
    )
    out_grad_fsl = traits.Tuple(
        File("grad.bvecs", desc="bvecs"),
        File("grad.bvals", desc="bvals"),
        argstr="-export_grad_fsl %s, %s",
        desc="export gradient files in FSL format",
    )
