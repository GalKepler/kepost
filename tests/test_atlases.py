from kepost.atlases.available_atlases import AVAILABLE_ATLASES


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
