from pathlib import Path

from kepost.atlases.available_atlases import AVAILABLE_ATLASES
from kepost.atlases.utils import get_atlas_properties


def test_available_atlases():
    atlases = []
    for key, value in AVAILABLE_ATLASES.items():
        atlases.append(key)
        assert "nifti" in value
        assert value["nifti"].is_file()
        assert "description_file" in value
        assert value["description_file"].is_file()
        assert "region_col" in value
        assert isinstance(value["region_col"], str)
        assert "index_col" in value
        if value["index_col"] is not None:
            assert isinstance(value["index_col"], int)


def test_atlas_properties():
    for key in AVAILABLE_ATLASES:
        nifti, description, region_col, index_col = get_atlas_properties(key)
        assert isinstance(nifti, Path)
        assert nifti.is_file()
        assert isinstance(description, Path)
        assert description.is_file()
        assert isinstance(region_col, str)
        if index_col is not None:
            assert isinstance(index_col, int)
