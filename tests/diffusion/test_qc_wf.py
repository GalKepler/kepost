import pytest

from kepost.workflows.diffusion.procedures.quality_control.eddy_qc import init_eddyqc_wf
from kepost.workflows.diffusion.procedures.quality_control.quality_control import (
    init_qc_wf,
)
from kepost.workflows.diffusion.procedures.quality_control.snr import init_snr_wf


@pytest.fixture
def eddyqc_wf():
    return init_eddyqc_wf()


@pytest.fixture
def qc_wf():
    return init_qc_wf()


@pytest.fixture
def snr_wf():
    return init_snr_wf()


def test_init_eddyqc_wf(eddyqc_wf):
    assert eddyqc_wf.name == "eddyqc_wf"
    assert eddyqc_wf.base_dir is None


def test_eddyqc_inputnode_fields(eddyqc_wf):
    assert list(eddyqc_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "source_file",
        "eddy_qc",
    ]


def test_init_qc_wf(qc_wf):
    assert qc_wf.name == "qc_wf"
    assert qc_wf.base_dir is None


def test_qc_inputnode_fields(qc_wf):
    assert list(qc_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "dwi_file",
        "dwi_grad",
        "dwi_bval",
        "brain_mask",
        "eddy_qc",
        "gm_probseg",
        "wm_probseg",
        "csf_probseg",
    ]


def test_init_snr_wf(snr_wf):
    assert snr_wf.name == "snr_wf"
    assert snr_wf.base_dir is None


def test_snr_inputnode_fields(snr_wf):
    assert list(snr_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "dwi_file",
        "dwi_grad",
        "dwi_bval",
        "brain_mask",
        "gm_probseg",
        "wm_probseg",
        "csf_probseg",
    ]
