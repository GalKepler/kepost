import pytest

from kepost.workflows.diffusion.procedures.coregisterations import (
    init_5tt_coreg_wf,
    init_coregistration_wf,
    init_tissue_coregistration_wf,
)


@pytest.fixture
def coregister_5tt_wf():
    return init_5tt_coreg_wf()


@pytest.fixture
def atlas_coregistration_wf():
    return init_coregistration_wf()


@pytest.fixture
def tissue_coregistration_wf():
    return init_tissue_coregistration_wf()


def test_init_5tt_coreg_wf(coregister_5tt_wf):
    assert coregister_5tt_wf.name == "coreg_5tt_wf"
    assert coregister_5tt_wf.base_dir is None


def test_5tt_coreg_inputnode_fields(coregister_5tt_wf):
    assert list(coregister_5tt_wf.get_node("inputnode").inputs.get().keys()) == [
        "dwi_reference",
        "t1w_to_dwi_transform",
        "t1w_reference",
        "5tt_file",
    ]


def test_init_coregistration_wf(atlas_coregistration_wf):
    assert atlas_coregistration_wf.name == "atlas_coregistration_wf"
    assert atlas_coregistration_wf.base_dir is None


def test_coregistration_inputnode_fields(atlas_coregistration_wf):
    assert list(atlas_coregistration_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "dwi_reference",
        "t1w_preproc",
        "t1w_to_dwi_transform",
        "atlas_name",
        "whole_brain_parcellation",
        "gm_cropped_parcellation",
    ]


def test_init_tissue_coregistration_wf(tissue_coregistration_wf):
    assert tissue_coregistration_wf.name == "tissues_coregistration_wf"
    assert tissue_coregistration_wf.base_dir is None


def test_tissue_coregistration_inputnode_fields(tissue_coregistration_wf):
    assert list(tissue_coregistration_wf.get_node("inputnode").inputs.get().keys()) == [
        "base_directory",
        "dwi_reference",
        "t1w_preproc",
        "t1w_to_dwi_transform",
        "gm_probseg",
        "wm_probseg",
        "csf_probseg",
    ]
