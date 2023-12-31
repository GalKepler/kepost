"""Base module variables."""

try:
    from kepost._version import __version__
except ImportError:
    __version__ = "0+unknown"

__packagename__ = "kepost"
__copyright__ = "Copyright 2023, Gal Kepler"
__credits__ = (
    "Contributors: please check the ``.zenodo.json`` file at the top-level folder"
    "of the repository"
)
__url__ = "https://github.com/GalKepler/kepost"

DOWNLOAD_URL = "https://github.com/GalKepler/kepost/{name}/archive/{ver}.tar.gz".format(
    name=__packagename__, ver=__version__
)
