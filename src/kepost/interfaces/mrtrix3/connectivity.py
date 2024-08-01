import os.path as op

from nipype.interfaces.base import File, TraitedSpec, isdefined, traits
from nipype.interfaces.mrtrix3.base import MRTrix3Base, MRTrix3BaseInputSpec


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
