import pytest

from kepost.workflows.diffusion.procedures.tensor_estimations.dipy import (
    init_dipy_tensor_wf,
)
from kepost.workflows.diffusion.procedures.tensor_estimations.mrtrix3 import (
    init_mrtrix3_tensor_wf,
)
from kepost.workflows.diffusion.procedures.tensor_estimations.tensor_estimation import (
    init_tensor_estimation_wf,
)


@pytest.fixture
def tensor_wf():
    return init_tensor_estimation_wf()


@pytest.fixture
def dipy_wf():
    return init_dipy_tensor_wf()


@pytest.fixture
def mrtrix3_wf():
    return init_mrtrix3_tensor_wf()


def test_init_tensor_estimation_wf(tensor_wf):
    assert tensor_wf.name == "tensor_estimation_wf"
    assert tensor_wf.base_dir is None


def test_inputnode_fields(tensor_wf):
    assert list(tensor_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "dwi_nifti",
        "dwi_bvec",
        "dwi_bval",
        "dwi_grad",
        "dwi_mask",
        "dwi_bzero",
        "dipy_fit_method",
        "native_to_mni_transform",
        "dwi_to_t1w_transform",
        "t1w_reference",
    ]


def test_init_dipy_tensor_wf(dipy_wf):
    assert dipy_wf.name == "dipy_tensor_wf"
    assert dipy_wf.base_dir is None


def test_dipy_inputnode_fields(dipy_wf):
    assert list(dipy_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "dwi_nifti",
        "dwi_bvec",
        "dwi_bval",
        "dwi_mask",
        "dwi_bzero",
        "fit_method",
        "source_file",
        "max_bval",
        "native_to_mni_transform",
        "dwi_to_t1w_transform",
        "t1w_reference",
    ]


def test_init_mrtrix3_tensor_wf(mrtrix3_wf):
    assert mrtrix3_wf.name == "mrtrix3_tensor_wf"
    assert mrtrix3_wf.base_dir is None


def test_mrtrix3_inputnode_fields(mrtrix3_wf):
    assert list(mrtrix3_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "source_file",
        "dwi_mif",
        "dwi_mask",
        "native_to_mni_transform",
        "dwi_to_t1w_transform",
        "t1w_reference",
        "max_bval",
        "wm_mask",
    ]
