import pytest

from kepost.workflows.diffusion.procedures import init_tractography_wf


@pytest.fixture
def tractography_wf():
    return init_tractography_wf()


def test_init_tractography_wf(tractography_wf):
    assert tractography_wf.name == "tractography_wf"
    assert tractography_wf.base_dir is None


def test_tractography_inputnode_fields(tractography_wf):
    assert list(tractography_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "dwi_nifti",
        "dwi_grad",
        "dwi_reference",
        "t1w_to_dwi_transform",
        "t1w_reference",
        "dwi_mask",
        "five_tissue_type",
    ]
