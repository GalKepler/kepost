import pytest

from kepost.workflows.diffusion.procedures.parcellations import init_parcellations_wf
from kepost.workflows.diffusion.procedures.tensor_estimations.dipy.dipy import (
    TENSOR_PARAMETERS as DIPY_,
)
from kepost.workflows.diffusion.procedures.tensor_estimations.mrtrix3.mrtrix3 import (
    TENSOR_PARAMETERS as MRTRIX3_,
)


@pytest.fixture
def dipy_parcellation_wf():
    return init_parcellations_wf(inputs=DIPY_, software="dipy")


@pytest.fixture
def mrtrix3_parcellation_wf():
    return init_parcellations_wf(inputs=MRTRIX3_, software="mrtrix3")


def test_init_dipy_parcellations_wf(dipy_parcellation_wf):
    assert dipy_parcellation_wf.name == "dipy_parcellations_wf"
    assert dipy_parcellation_wf.base_dir is None


def test_dipy_parcellation_inputnode_fields(dipy_parcellation_wf):
    assert (
        list(dipy_parcellation_wf.get_node("inputnode").inputs.get().keys())
        == [
            "base_directory",
            "acq_label",
            "source_file",
            "atlas_name",
            "atlas_nifti",
        ]
        + DIPY_
    )


def test_init_mrtrix3_parcellations_wf(mrtrix3_parcellation_wf):
    assert mrtrix3_parcellation_wf.name == "mrtrix3_parcellations_wf"
    assert mrtrix3_parcellation_wf.base_dir is None


def test_mrtrix3_parcellation_inputnode_fields(mrtrix3_parcellation_wf):
    assert (
        list(mrtrix3_parcellation_wf.get_node("inputnode").inputs.get().keys())
        == [
            "base_directory",
            "acq_label",
            "source_file",
            "atlas_name",
            "atlas_nifti",
        ]
        + MRTRIX3_
    )
