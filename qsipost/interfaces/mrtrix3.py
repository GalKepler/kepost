import os.path as op

from nipype.interfaces.base import (
    CommandLine,
    CommandLineInputSpec,
    Directory,
    File,
    InputMultiObject,
    TraitedSpec,
    Undefined,
    isdefined,
    traits,
)
from nipype.interfaces.mrtrix3.base import MRTrix3Base, MRTrix3BaseInputSpec


class ResponseSDInputSpec(MRTrix3BaseInputSpec):
    algorithm = traits.Enum(
        "msmt_5tt",
        "dhollander",
        "tournier",
        "tax",
        argstr="%s",
        position=1,
        mandatory=True,
        desc="response estimation algorithm (multi-tissue)",
    )
    in_file = File(
        exists=True,
        argstr="%s",
        position=-5,
        mandatory=True,
        desc="input DWI image",
    )
    wm_file = File(
        "wm.txt",
        argstr="%s",
        position=-3,
        usedefault=True,
        desc="output WM response text file",
    )
    gm_file = File(argstr="%s", position=-2, desc="output GM response text file")
    csf_file = File(argstr="%s", position=-1, desc="output CSF response text file")
    voxels_file = File(
        argstr="-voxels %s",
        desc="output an image showing the final voxel selection(s)",
    )
    in_mask = File(exists=True, argstr="-mask %s", desc="provide initial mask image")


class ResponseSDOutputSpec(TraitedSpec):
    wm_file = File(argstr="%s", desc="output WM response text file")
    gm_file = File(argstr="%s", desc="output GM response text file")
    csf_file = File(argstr="%s", desc="output CSF response text file")
    voxels_file = File(
        argstr="-voxels %s",
        desc="output an image showing the final voxel selection(s)",
    )


class ResponseSD(MRTrix3Base):
    """
    Estimate response function(s) for spherical deconvolution using the specified algorithm.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> resp = mrt.ResponseSD()
    >>> resp.inputs.in_file = 'dwi.mif'
    >>> resp.inputs.algorithm = 'tournier'
    >>> resp.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> resp.cmdline                               # doctest: +ELLIPSIS
    'dwi2response tournier -fslgrad bvecs bvals dwi.mif wm.txt'
    >>> resp.run()                                 # doctest: +SKIP

    # We can also pass in multiple harmonic degrees in the case of multi-shell
    >>> resp.inputs.max_sh = [6,8,10]
    >>> resp.cmdline
    'dwi2response tournier -fslgrad bvecs bvals -lmax 6,8,10 dwi.mif wm.txt'
    """

    _cmd = "dwi2response"
    input_spec = ResponseSDInputSpec
    output_spec = ResponseSDOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["wm_file"] = op.abspath(self.inputs.wm_file)
        if self.inputs.gm_file != Undefined:
            outputs["gm_file"] = op.abspath(self.inputs.gm_file)
        if self.inputs.csf_file != Undefined:
            outputs["csf_file"] = op.abspath(self.inputs.csf_file)
        if self.inputs.voxels_file != Undefined:
            outputs["voxels_file"] = op.abspath(self.inputs.voxels_file)
        return outputs


class EstimateFODInputSpec(MRTrix3BaseInputSpec):
    algorithm = traits.Enum(
        "csd",
        "msmt_csd",
        argstr="%s",
        position=0,
        mandatory=True,
        desc="FOD algorithm",
    )
    in_file = File(
        exists=True,
        argstr="%s",
        position=1,
        mandatory=True,
        desc="input DWI image",
    )
    wm_txt = File(
        argstr="%s", position=-6, mandatory=True, desc="WM response text file"
    )
    wm_odf = File(
        "wm.mif",
        argstr="%s",
        position=-5,
        usedefault=True,
        mandatory=True,
        desc="output WM ODF",
    )
    gm_txt = File(argstr="%s", position=-4, desc="GM response text file")
    gm_odf = File(
        "gm.mif",
        usedefault=True,
        argstr="%s",
        position=-3,
        desc="output GM ODF",
    )
    csf_txt = File(argstr="%s", position=-2, desc="CSF response text file")
    csf_odf = File(
        "csf.mif",
        usedefault=True,
        argstr="%s",
        position=-1,
        desc="output CSF ODF",
    )
    in_mask = File(exists=True, argstr="-mask %s", desc="mask image")

    # DW Shell selection options
    shell = traits.List(
        traits.Float,
        sep=",",
        argstr="-shells %s",
        desc="specify one or more dw gradient shells",
    )
    max_sh = InputMultiObject(
        traits.Int,
        value=[8],
        usedefault=False,
        argstr="-lmax %s",
        sep=",",
        desc=(
            "maximum harmonic degree of response function - single value for single-shell response, list for multi-shell response"
        ),
    )
    in_dirs = File(
        exists=True,
        argstr="-directions %s",
        desc=(
            "specify the directions over which to apply the non-negativity "
            "constraint (by default, the built-in 300 direction set is "
            "used). These should be supplied as a text file containing the "
            "[ az el ] pairs for the directions."
        ),
    )
    predicted_signal = File(
        argstr="-predicted_signal %s",
        desc=(
            "specify a file to contain the predicted signal from the FOD "
            "estimates. This can be used to calculate the residual signal."
            "Note that this is only valid if algorithm == 'msmt_csd'. "
            "For single shell reconstructions use a combination of SHConv "
            "and SH2Amp instead."
        ),
    )


class EstimateFODOutputSpec(TraitedSpec):
    wm_odf = File(argstr="%s", desc="output WM ODF")
    gm_odf = File(argstr="%s", desc="output GM ODF")
    csf_odf = File(argstr="%s", desc="output CSF ODF")
    predicted_signal = File(desc="output predicted signal")


class EstimateFOD(MRTrix3Base):
    """
    Estimate fibre orientation distributions from diffusion data using spherical deconvolution

    .. warning::

       The CSD algorithm does not work as intended, but fixing it in this interface could break
       existing workflows. This interface has been superseded by
       :py:class:`.ConstrainedSphericalDecomposition`.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> fod = mrt.EstimateFOD()
    >>> fod.inputs.algorithm = 'msmt_csd'
    >>> fod.inputs.in_file = 'dwi.mif'
    >>> fod.inputs.wm_txt = 'wm.txt'
    >>> fod.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> fod.cmdline
    'dwi2fod -fslgrad bvecs bvals -lmax 8 msmt_csd dwi.mif wm.txt wm.mif gm.mif csf.mif'
    >>> fod.run()  # doctest: +SKIP
    """

    _cmd = "dwi2fod"
    input_spec = EstimateFODInputSpec
    output_spec = EstimateFODOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["wm_odf"] = op.abspath(self.inputs.wm_odf)
        if isdefined(self.inputs.gm_odf):
            outputs["gm_odf"] = op.abspath(self.inputs.gm_odf)
        if isdefined(self.inputs.csf_odf):
            outputs["csf_odf"] = op.abspath(self.inputs.csf_odf)
        if isdefined(self.inputs.predicted_signal):
            if self.inputs.algorithm != "msmt_csd":
                raise Exception(
                    "'predicted_signal' option can only be used with "
                    "the 'msmt_csd' algorithm"
                )
            outputs["predicted_signal"] = op.abspath(self.inputs.predicted_signal)
        return outputs


class Generate5ttInputSpec(MRTrix3BaseInputSpec):
    algorithm = traits.Enum(
        "fsl",
        "gif",
        "freesurfer",
        argstr="%s",
        position=0,
        mandatory=True,
        desc="tissue segmentation algorithm",
    )
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="input image",
    )
    in_mask = File(
        exists=True,
        argstr="-mask %s",
        desc="input mask image",
    )
    out_file = File(
        "5TT.mif",
        usedefault=True,
        argstr="%s",
        mandatory=True,
        position=-1,
        desc="output image",
    )


class Generate5ttOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output image")


class Generate5tt(MRTrix3Base):
    """
    Generate a 5TT image suitable for ACT using the selected algorithm


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> gen5tt = mrt.Generate5tt()
    >>> gen5tt.inputs.in_file = 'T1.nii.gz'
    >>> gen5tt.inputs.algorithm = 'fsl'
    >>> gen5tt.inputs.out_file = '5tt.mif'
    >>> gen5tt.cmdline                             # doctest: +ELLIPSIS
    '5ttgen fsl T1.nii.gz 5tt.mif'
    >>> gen5tt.run()                               # doctest: +SKIP
    """

    _cmd = "5ttgen"
    input_spec = Generate5ttInputSpec
    output_spec = Generate5ttOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class TransformConvertInputSpec(MRTrix3BaseInputSpec):
    in_matrix_file = File(
        exists=True,
        argstr="%s",
        position=0,
        mandatory=True,
        desc="input transformation matrix provided by other registration softwares",
    )
    in_file = File(
        exists=True,
        argstr="%s",
        position=1,
        desc="input image to apply transformation to",
    )
    reference = File(
        exists=True,
        argstr="%s",
        position=2,
        desc="reference image to apply transformation to",
    )
    out_file = File(
        "transform_matrix.txt",
        argstr="%s",
        position=-1,
        usedefault=True,
        desc="output file containing the transformation matrix in MRTrix format",
    )
    flirt_import = traits.Bool(
        False,
        argstr="flirt_import",
        position=3,
        desc="import a transformation matrix from FSL FLIRT",
    )


class TransformConvertOutputSpec(TraitedSpec):
    out_file = File(
        argstr="%s",
        desc="output file containing the transformation matrix in MRTrix format",
    )


class TransformConvert(MRTrix3Base):
    """
    Convert a transformation matrix to MRTrix format

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> transform = mrt.TransformConvert()
    >>> transform.inputs.in_matrix_file = 'transform_flirt.mat'
    >>> transform.inputs.in_file = 'flirt_in.nii'
    >>> transform.inputs.reference = 'flirt_ref.nii'
    >>> transform.flirt_import = True
    >>> transform.cmdline                               # doctest: +ELLIPSIS
    'transformconvert transform_flirt.mat flirt_in.nii flirt_ref.nii flirt_import transform_mrtrix.txt'
    >>> transform.run()                                 # doctest: +SKIP
    """

    _cmd = "transformconvert"
    input_spec = TransformConvertInputSpec
    output_spec = TransformConvertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class MRTransformInputSpec(MRTrix3BaseInputSpec):
    linear_transform = File(
        exists=True,
        argstr="-linear %s",
        desc="specify a linear transform to apply, in the form of a 3x4 or 4x4 ascii file.",
    )
    in_file = File(
        exists=True,
        argstr="%s",
        position=-2,
        desc="input image to be transformed.",
    )
    out_file = File(
        "mrtransformed.mif",
        argstr="%s",
        position=-1,
        usedefault=True,
        desc=" the output image.",
    )
    flip_axes = traits.List(
        traits.Enum(0, 1, 2),
        argstr="-flip %s",
        sep=",",
        desc="flip the specified axes, provided as a comma-separated list of indices (0:x, 1:y, 2:z).",
    )
    inverse = traits.Bool(
        argstr="-inverse",
        desc="invert the transformation matrix before applying it.",
    )
    half = traits.Bool(
        argstr="-half",
        desc="apply the matrix square root of the transformation. This can be combined with the inverse option.",
    )
    template = File(
        exists=True,
        argstr="-template %s",
        desc="specify the template image to which the input image is to be transformed.",
    )
    interp = traits.Enum(
        "cubic",
        "nearest",
        "linear",
        "sinc",
        argstr="-interp %s",
        desc="specify the interpolation method to use when transforming the image. Options are: nearest, linear, cubic.",
    )


class MRTransformOutputSpec(TraitedSpec):
    out_file = File(
        argstr="%s",
        desc="the output image.",
    )


class MRTransform(MRTrix3Base):
    """
    Transform an image using a linear transformation matrix

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> transform = mrt.MRTransform()
    >>> transform.inputs.linear_transform = 'transform_mrtrix.txt'
    >>> transform.inputs.in_file = 'dwi.mif'
    >>> transform.inputs.out_file = 'dwi_transformed.mif'
    >>> transform.cmdline                               # doctest: +ELLIPSIS
    'mrtransform -linear transform_mrtrix.txt dwi.mif dwi_transformed.mif'
    >>> transform.run()                                 # doctest: +SKIP
    """

    _cmd = "mrtransform"
    input_spec = MRTransformInputSpec
    output_spec = MRTransformOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs
