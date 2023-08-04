from typing import Any, Callable, Union

import pickle
import shutil
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd


class Atlas:
    """
    A class used to represent a parcellation atlas
    """

    CONFIGURED_ATLASES_PATH = Path(__file__).parent / "configured"

    def __init__(
        self,
        name: str,
        path: Union[Path, str] = None,
        load_existing: bool = True,
    ):
        """
        Initialize an Atlas object.

        Parameters
        ----------
        name : str
            The name of the atlas.
        """
        self.path = self.get_atlas_path(name=name, path=path)
        self.load_if_existing(name=name, load_existing=load_existing)

    def get_atlas_path(self, name: str, path: Union[Path, str] = None):
        """
        Get the path to the database.

        Parameters
        ----------
        name : str
            The name of the atlas.
        path : Union[Path,str], optional
            The path to the atlas, by default None
        """
        path = Path(path) if path is not None else self.CONFIGURED_ATLASES_PATH / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def load_if_existing(self, name: str, load_existing: bool = True):
        """
        Load an atlas if it exists.

        Parameters
        ----------
        name : str
            The name of the atlas.
        load_existing : bool, optional
            Whether to load an existing atlas, by default True
        """
        path = self.path / f"{name}.obj"
        if path.exists() and load_existing:
            atlas = pickle.load(open(path, "rb"))
            self.__dict__ = atlas.__dict__
        else:
            self.name = name.lower()

    def associate(self, title: str, data: Any):
        """
        Associate a file with the atlas.

        Parameters
        ----------
        title : str
            The title of the file.
        path : str
            The path to the file.
        """
        if isinstance(data, Path) or isinstance(data, str):
            if Path(data).exists():
                data = Path(data).absolute()
                shutil.copy(data, self.path)
                data = self.path / Path(data).name
        setattr(self, title, data)

    def to_json(self):
        """
        Convert the atlas to a JSON string.

        Returns
        -------
        str
            The JSON string.
        """
        data = {}
        for key, value in self.__dict__.items():
            data[key] = value
        return data

    def save(self, path: Union[Path, str] = None):
        """
        Save the atlas to a file.

        Parameters
        ----------
        path : Union[Path, str]
            The path to the file.
        """
        if path is None:
            path = self.path / f"{self.name}.obj"
        else:
            path = Path(path)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    def parcellate(
        self,
        metric_image: Path,
        atlas_image: Path,
        parcellation_function: Callable = np.nanmedian,
        name: str = None,
    ) -> pd.Series:
        """
        Parcellate an image using the atlas.

        Parameters
        ----------
        atlas_image : Path
            The path to the atlas image.
        metric_image : Path
            The path to the metric image.
        parcellation_function : Callable, optional
            The function to use for parcellation, by default np.nanmedian
        name : str, optional
            The name of the parcellation, by default None

        Returns
        -------
        pd.Series
            The parcellation.
        """
        atlas = nib.load(atlas_image).get_fdata()
        metric = nib.load(metric_image).get_fdata()
        n_parcels = atlas.max()
        if n_parcels != np.max(self.labels):
            raise ValueError(
                f"Number of parcels in atlas ({n_parcels}) does not match number of labels ({np.max(self.labels)})"  # noqa E501
            )
        parcellation = pd.Series(index=self.labels, name=name)
        for label in self.labels:
            parcellation[label] = parcellation_function(metric[atlas == label])
        return parcellation

    @property
    def json(self) -> dict:
        """
        Return the atlas as a JSON string.

        Returns
        -------
        str
            The JSON string.
        """
        return self.to_json()
