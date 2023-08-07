import os.path as op

from matplotlib import use
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
        "hsvs",
        argstr="%s",
        position=0,
        mandatory=True,
        desc="tissue segmentation algorithm",
    )
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=False,
        position=-2,
        desc="input image",
    )
    freesurfer_dir = Directory(
        exists=True,
        mandatory=False,
        argstr="%s",
        position=-2,
        desc="Freesurfer directory",
    )
    in_mask = File(
        exists=True,
        argstr="-mask %s",
        desc="input mask image",
    )
    sgm_amyg_hipp = traits.Bool(
        argstr="-sgm_amyg_hipp",
        desc="Represent the amygdalae and hippocampi as sub-cortical grey matter in the 5TT image",
    )
    white_stem = traits.Bool(
        argstr="-white_stem",
        desc="Classify the brainstem as white matter",
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


class GMWMInterfaceInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="input 5TT image.",
    )
    out_file = File(
        "gmwmi.mif",
        usedefault=True,
        argstr="%s",
        mandatory=False,
        position=-1,
        desc="output GM-WM interface image.",
    )


class GMWMInterfaceOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output GM-WM interface image.")


class GMWMInterface(MRTrix3Base):
    """
    Generate a GM-WM interface image from a 5TT image


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> gmwm = mrt.GMWMInterface()
    >>> gmwm.inputs.in_file = '5TT.mif'
    >>> gmwm.inputs.out_file = 'gmwmi.mif'
    >>> gmwm.cmdline                             # doctest: +ELLIPSIS
    '5tt2gmwmi 5TT.mif gmwmi.mif'
    >>> gmwm.run()                               # doctest: +SKIP
    """

    _cmd = "5tt2gmwmi"
    input_spec = GMWMInterfaceInputSpec
    output_spec = GMWMInterfaceOutputSpec

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


class MTNormaliseInputSpec(MRTrix3BaseInputSpec):
    in_wm_fod = File(
        exists=True,
        argstr="%s",
        position=0,
        mandatory=True,
        desc="input image containing the white matter FODs.",
    )
    out_wm_fod = File(
        "wm_norm_fod.mif",
        argstr="%s",
        position=1,
        usedefault=True,
        desc="output image containing the normalised white matter FODs.",
    )
    in_gm_fod = File(
        exists=True,
        argstr="%s",
        position=2,
        desc="input image containing the grey matter FODs.",
    )
    out_gm_fod = File(
        "gm_norm_fod.mif",
        argstr="%s",
        position=3,
        usedefault=True,
        desc="output image containing the normalised grey matter FODs.",
    )
    in_csf_fod = File(
        exists=True,
        argstr="%s",
        position=4,
        desc="input image containing the CSF FODs.",
    )
    out_csf_fod = File(
        "csf_norm_fod.mif",
        argstr="%s",
        position=5,
        usedefault=True,
        desc="output image containing the normalised CSF FODs.",
    )
    in_mask = File(exists=True, argstr="-mask %s", desc="provide initial mask image")
    order = traits.Int(
        3,
        argstr="-order %d",
        usedefault=False,
        desc="spherical harmonic order of the output FODs.",
    )


class MTNormaliseOutputSpec(TraitedSpec):
    out_wm_fod = File(
        argstr="%s",
        desc="output image containing the normalised white matter FODs.",
    )
    out_gm_fod = File(
        argstr="%s",
        desc="output image containing the normalised grey matter FODs.",
    )
    out_csf_fod = File(
        argstr="%s",
        desc="output image containing the normalised CSF FODs.",
    )


class MTNormalise(MRTrix3Base):
    """
    Normalise the intensity of multi-tissue FOD images

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> normalise = mrt.MTNormalise()
    >>> normalise.inputs.in_wm_fod = 'wm_fod.mif'
    >>> normalise.inputs.in_gm_fod = 'gm_fod.mif'
    >>> normalise.inputs.in_csf_fod = 'csf_fod.mif'
    >>> normalise.cmdline                               # doctest: +ELLIPSIS
    'mtnormalise -order 3 wm_fod.mif wm_norm_fod.mif gm_fod.mif gm_norm_fod.mif csf_fod.mif csf_norm_fod.mif'
    >>> normalise.run()                                 # doctest: +SKIP
    """

    _cmd = "mtnormalise"
    input_spec = MTNormaliseInputSpec
    output_spec = MTNormaliseOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_wm_fod"] = op.abspath(self.inputs.out_wm_fod)
        if isdefined(self.inputs.in_gm_fod):
            outputs["out_gm_fod"] = op.abspath(self.inputs.in_gm_fod)
        if isdefined(self.inputs.in_csf_fod):
            outputs["out_csf_fod"] = op.abspath(self.inputs.in_csf_fod)
        return outputs


class TCKSiftInputSpec(MRTrix3BaseInputSpec):
    in_tracks = File(
        exists=True,
        argstr="%s",
        position=-3,
        mandatory=True,
        desc="input track file.",
    )
    in_fod = File(
        exists=True,
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="input image containing the FODs.",
    )
    out_file = File(
        "sift.tck",
        argstr="%s",
        position=-1,
        usedefault=True,
        desc="output track file containing the selected streamlines.",
    )
    act_file = File(
        exists=True,
        argstr="-act %s",
        desc="Anatomically-Constrained Tractography image",
    )
    fd_scale_gm = traits.Bool(
        argstr="-fd_scale_gm",
        desc="heuristically downsize the fibre density estimates based on the presence of GM in the voxel.",
    )
    term_number = traits.Int(
        100000,
        argstr="-term_number %d",
        usedefault=False,
        desc="number of streamlines to select.",
    )
    term_ratio = traits.Float(
        argstr="-term_ratio %f",
        desc="proportion of streamlines to select.",
    )


class TCKSiftOutputSpec(TraitedSpec):
    out_file = File(
        argstr="%s",
        desc="output track file containing the selected streamlines.",
    )


class TCKSift(MRTrix3Base):
    """
    Filter a whole-brain fibre-tracking data set such that the streamline densities match the FOD lobe integrals


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> sift = mrt.TCKSift()
    >>> sift.inputs.in_tracks = 'tracks.tck'
    >>> sift.inputs.in_fod = 'fod.mif'
    >>> sift.cmdline                               # doctest: +ELLIPSIS
    'tcksift tracks.tck fod.mif sift.tck'
    >>> sift.run()                                 # doctest: +SKIP
    """

    _cmd = "tcksift"
    input_spec = TCKSiftInputSpec
    output_spec = TCKSiftOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class BuildConnectomeInputSpec(MRTrix3BaseInputSpec):
    in_tracts = File(
        exists=True,
        argstr="%s",
        position=-3,
        mandatory=True,
        desc="input tracts file.",
    )
    in_nodes = File(
        exists=True,
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="input nodes (atlas) file.",
    )
    out_connectome = File(
        "connectome.csv",
        argstr="%s",
        position=-1,
        usedefault=True,
        desc="output connectome file.",
    )
    scale = traits.Enum(
        "length",
        "invlength",
        "invnodevol",
        argstr="-scale_%s",
        desc="scale the contribution of each streamline segment by its length, the inverse length, or the inverse of the sum of the volumes of the nodes it passes through.",
        usedefault=False,
    )
    # scale_length = traits.Bool(
    #     argstr="-scale_length",
    #     desc="scale the contribution of each streamline segment by its length.",
    # )
    # scale_invlength = traits.Bool(
    #     argstr="-scale_invlength",
    #     desc="scale the contribution of each streamline segment by its inverse length.",
    # )
    # scale_invnodevol = traits.Bool(
    #     argstr="-scale_invnodevol",
    #     desc="scale the contribution of each streamline segment by the inverse of the sum of the volumes of the nodes it passes through.",
    # )
    symmetric = traits.Bool(
        default_value=True,
        usedefault=True,
        argstr="-symmetric",
        desc="output a symmetric matrix.",
    )
    zero_diagonal = traits.Bool(
        argstr="-zero_diagonal",
        desc="zero the main diagonal in the output matrix.",
    )
    out_assignments = File(
        "assignments.csv",
        argstr="-out_assignments %s",
        desc="output assignments file.",
        use_default=True,
    )
    stat_edge = traits.Enum(
        "sum",
        "mean",
        "min",
        "max",
        argstr="-stat_edge %s",
        desc="select the statistic to compute for each edge.",
    )


class BuildConnectomeOutputSpec(TraitedSpec):
    out_connectome = File(
        argstr="%s",
        desc="output connectome file.",
    )
    out_assignments = File(
        argstr="-out_assignments %s",
        desc="output assignments file.",
    )


class BuildConnectome(MRTrix3Base):
    """
    Build a connectome from a streamlines tractogram


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> connectome = mrt.BuildConnectome()
    >>> connectome.inputs.in_tracts = 'tracks.tck'
    >>> connectome.inputs.in_nodes = 'nodes.nii.gz'
    >>> connectome.cmdline                               # doctest: +ELLIPSIS
    'tck2connectome tracks.tck nodes.nii.gz connectome.csv'
    >>> connectome.run()                                 # doctest: +SKIP
    """

    _cmd = "tck2connectome"
    input_spec = BuildConnectomeInputSpec
    output_spec = BuildConnectomeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_connectome"] = op.abspath(self.inputs.out_connectome)
        if isdefined(self.inputs.out_assignments):
            outputs["out_assignments"] = op.abspath(self.inputs.out_assignments)
        return outputs


class MRFilterInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=-3,
        mandatory=True,
        desc="input tracts file.",
    )
    filter = traits.Enum(
        "fft",
        "gradient",
        "median",
        "smooth",
        "normalise",
        "zclean",
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="type of filter to be applied.",
    )
    out_file = File(
        "filtered.mif",
        argstr="%s",
        position=-1,
        usedefault=True,
        desc="output filtered image.",
    )


class MRFilterOutputSpec(TraitedSpec):
    out_file = File(
        argstr="%s",
        desc="output filtered image.",
    )


class MRFilter(MRTrix3Base):
    """
    Perform filtering operations on 3D/4D images.


    Example
    -------
    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> filter = mrt.MRFilter()
    >>> filter.inputs.in_file = 'dwi.mif'
    >>> filter.inputs.filter = 'median'
    >>> filter.cmdline                               # doctest: +ELLIPSIS
    'mrfilter dwi.mif median filtered.mif'
    >>> filter.run()                                 # doctest: +SKIP
    """

    _cmd = "mrfilter"
    input_spec = MRFilterInputSpec
    output_spec = MRFilterOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs
