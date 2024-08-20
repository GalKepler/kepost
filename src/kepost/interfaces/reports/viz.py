import os

from nipype.interfaces.base import File, Str, isdefined, traits
from nipype.interfaces.mixins import reporting
from niworkflows.viz.utils import (
    _3d_in_file,
    compose_view,
    cuts_from_bbox,
    extract_svg,
    rotate_affine,
    rotation2canonical,
    uuid4,
)


def plot_overlay(
    image_nii,
    atlas,
    out_file,
    bbox_nii=None,
    masked=False,
    colors=None,
    compress="auto",
    plot_params=None,
):
    """
    Generate a static mosaic with ROIs represented by their delimiting contour.

    Plot segmentation as contours over the image (e.g. anatomical).
    seg_niis should be a list of files. mask_nii helps determine the cut
    coordinates. plot_params will be passed on to nilearn plot_* functions. If
    seg_niis is a list of size one, it behaves as if it was plotting the mask.
    """
    from nilearn import image as nlimage
    from svgutils.transform import fromstring

    plot_params = {} if plot_params is None else plot_params

    image_nii = _3d_in_file(image_nii)
    canonical_r = rotation2canonical(image_nii)
    image_nii = rotate_affine(image_nii, rot=canonical_r)
    atlas = rotate_affine(_3d_in_file(atlas), rot=canonical_r)

    # plot_params = robust_set_limits(data, plot_params)

    bbox_nii = (
        image_nii
        if bbox_nii is None
        else rotate_affine(_3d_in_file(bbox_nii), rot=canonical_r)
    )

    if masked:
        bbox_nii = nlimage.threshold_img(bbox_nii, 1e-3)

    cuts = cuts_from_bbox(bbox_nii, cuts=7)
    plot_params["colors"] = colors or plot_params.get("colors", None)
    out_files = []
    for d in plot_params.pop("dimensions", ("z", "x", "y")):
        plot_params["display_mode"] = d
        plot_params["cut_coords"] = cuts[d]
        svg = _plot_overlay(image_nii, atlas=atlas, compress=compress, **plot_params)
        # Find and replace the figure_1 id.
        svg = svg.replace("figure_1", "segmentation-%s-%s" % (d, uuid4()), 1)
        out_files.append(fromstring(svg))

    return out_files


def _plot_overlay(image, atlas, compress="auto", **plot_params):
    from nilearn.plotting import plot_anat

    plot_params = plot_params or {}
    # plot_params' values can be None, however they MUST NOT
    # be None for colors and levels from this point on.
    colors = plot_params.pop("colors", None) or []
    colors = [[c] if not isinstance(c, list) else c for c in colors]

    display = plot_anat(
        image,
        **{k: v for k, v in plot_params.items() if k not in ["threshold", "cmap"]},
    )

    # remove plot_anat -specific parameters
    plot_params.pop("display_mode")
    plot_params.pop("cut_coords")
    plot_params["alpha"] = 0.7
    # plot_params["colors"] = colors[0]
    display.add_overlay(atlas, **plot_params)

    svg = extract_svg(display, compress=compress)
    display.close()
    return svg


class OverlayRPTInputSpec(reporting.ReportCapableInputSpec):
    background_file = File(mandatory=True, exists=True, desc="Background file")
    overlay_file = File(mandatory=True, exists=True, desc="Parcellation atlas file")
    colormap = Str(
        default_value="hsv",
        usedefault=True,
        desc="Colormap to use for overlaying the image",
    )
    threshold = traits.Float(
        mandatory=False, desc="Threshold to use for overlaying the image"
    )
    out_report = File(
        "report.svg",
        usedefault=True,
        hash_files=False,
        desc="filename for the visual report",
    )


class OverlayRPTOutputsSpec(reporting.ReportCapableOutputSpec):
    out_report = File(
        desc="filename for the visual report",
    )


class OverlayRPT(reporting.ReportCapableInterface):
    """An abstract mixin to segmentation nipype interfaces."""

    input_spec = OverlayRPTInputSpec
    output_spec = OverlayRPTOutputsSpec

    def _run_interface(self, runtime):
        self._generate_report()
        return runtime

    def _generate_report(self):
        self.inputs.out_report = f"{os.getcwd()}/{self.inputs.out_report}"
        plot_params = {"cmap": self.inputs.colormap}
        if isdefined(self.inputs.threshold):
            plot_params["threshold"] = self.inputs.threshold
        compose_view(
            plot_overlay(
                image_nii=self.inputs.background_file,
                atlas=self.inputs.overlay_file,
                out_file=self.inputs.out_report,
                masked=False,
                compress=False,
                plot_params=plot_params,
            ),
            fg_svgs=None,
            out_file=self.inputs.out_report,
        )

    def _list_outputs(self):
        outputs = {}
        outputs["out_report"] = self.inputs.out_report
        return outputs
