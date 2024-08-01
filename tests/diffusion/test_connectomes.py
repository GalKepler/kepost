import pytest

from kepost.workflows.diffusion.procedures import init_connectome_wf


@pytest.fixture
def connectome_wf():
    return init_connectome_wf()


def test_init_connectome_wf(connectome_wf):
    assert connectome_wf.name == "connectome_wf"
    assert connectome_wf.base_dir is None


def test_connectome_inputnode_fields(connectome_wf):
    assert list(connectome_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "atlas_nifti",
        "tracts_sifted",
        "tracts_unsifted",
        "atlas_name",
        "tck_weights",
    ]
