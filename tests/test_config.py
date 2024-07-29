import logging
import os
import tempfile
from pathlib import Path

import pytest

from kepost import config

_fs_license = os.getenv("FS_LICENSE")
if not _fs_license and os.getenv("FREESURFER_HOME"):
    _fs_home = os.getenv("FREESURFER_HOME")
    if _fs_home and (Path(_fs_home) / "license.txt").is_file():
        _fs_license = str(Path(_fs_home) / "license.txt")
    del _fs_home


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
        yield Path(tmpdirname)


def test_environment_config():
    assert config.environment.cpu_count == os.cpu_count()
    assert config.environment.exec_env is not None
    assert config.environment.nipype_version is not None
    assert config.environment.version is not None


def test_nipype_config():
    assert config.nipype.crashfile_format == "txt"
    assert config.nipype.get_linked_libs is False
    assert config.nipype.memory_gb is None
    assert config.nipype.nprocs == os.cpu_count()
    assert config.nipype.plugin == "MultiProc"
    assert config.nipype.plugin_args == {
        "maxtasksperchild": 1,
        "raise_insufficient": False,
    }


def test_execution_config():
    assert config.execution.keprep_dir is None
    assert config.execution.keprep_database_dir is None
    assert config.execution.debug == []
    if _fs_license is not None:
        assert config.execution.fs_license_file is not None
    else:
        assert config.execution.fs_license_file is None
    assert config.execution.work_dir == Path("work").absolute()


def test_workflow_config():
    assert config.workflow.atlases == ["all"]
    assert config.workflow.dipy_reconstruction_method == "NLLS"
    assert config.workflow.gm_probseg_threshold == 0.0001


def test_seeds_config():
    assert config.seeds.master is None
    assert config.seeds.ants is None
    assert config.seeds.numpy is None


def test_from_dict(temp_dir):
    keprep_dir = temp_dir / "keprep"
    keprep_dir.mkdir(exist_ok=True, parents=True)
    settings = {
        "keprep_dir": keprep_dir,
        "work_dir": temp_dir / "work",
        "nprocs": 4,
        "plugin": "Linear",
    }
    config.from_dict(settings, init=False)
    assert config.execution.keprep_dir == Path(temp_dir / "keprep").absolute()
    assert config.execution.work_dir == Path(temp_dir / "work").absolute()
    assert config.nipype.nprocs == 4
    assert config.nipype.plugin == "Linear"


def test_to_filename_load(temp_dir):
    keprep_dir = temp_dir / "keprep"
    work_dir = temp_dir / "work"
    keprep_dir.mkdir()
    work_dir.mkdir()

    settings = {
        "keprep_dir": keprep_dir,
        "work_dir": work_dir,
        "nprocs": 4,
        "plugin": "Linear",
    }

    with tempfile.TemporaryDirectory() as tmpdirname:
        config_file = Path(tmpdirname) / "test_config.toml"
        config.from_dict(settings, init=False)
        config.to_filename(config_file)

        assert config_file.exists()

        config.load(config_file, init=False)
        assert config.execution.keprep_dir == Path(keprep_dir).absolute()
        assert config.execution.work_dir == Path(work_dir).absolute()
        assert config.nipype.nprocs == 4
        assert config.nipype.plugin == "Linear"


def test_logging_levels():
    assert logging.getLevelName(25) == "IMPORTANT"
    assert logging.getLevelName(15) == "VERBOSE"
