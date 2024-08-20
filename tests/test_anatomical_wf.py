from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from kepost.workflows.anatomical.anatomical import init_anatomical_wf


def test_init_anatomical_wf():
    wf = init_anatomical_wf()
    assert isinstance(wf, Workflow)
    assert wf.name == "anatomical_postprocess"
    assert wf.base_dir is None
