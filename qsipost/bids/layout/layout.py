from typing import Union

from pathlib import Path

from bids import BIDSLayout
from bids.exceptions import ConfigError
from bids.layout import add_config_paths

from qsipost.bids.config.configurations import CONFIGURATIONS


# Create a new class that is specific to qsiprep's layout
class QSIPREPLayout(BIDSLayout):
    """
    A class that extends the BIDSLayout class to include
    qsiprep-specific functionality.
    """

    DATABASE_FILE_NAME = "qsiprep_layout.db"

    def __init__(
        self,
        root: Union[Path, str] = None,
        database_path: Union[Path, str] = None,
        reset_database: bool = False,
        configurations: dict = CONFIGURATIONS,
    ) -> None:
        """
        Initialize a QSIPREPLayout object.

        Parameters
        ----------
        path : Union[Path, str]
            The path to the entity directory.
        """
        self.path = Path(root)
        config_names = self.add_configurations(configurations=configurations)
        super().__init__(
            self.path,
            validate=False,
            database_path=database_path,
            reset_database=reset_database,
            config=config_names,
        )
        # self.layout = BIDSLayout(
        #     self.path,
        #     validate=False,
        #     database_path=database_path,
        #     reset_database=reset_database,
        #     config=config_names,
        # )

    def add_configurations(self, configurations: dict = CONFIGURATIONS) -> None:
        """
        Add configuration files to the layout.

        Parameters
        ----------
        configurations : dict
            A dictionary containing the configuration files.
        """
        config_names = ["bids"]
        for name, configuration_file in configurations.items():
            try:
                add_config_paths(**{name: configuration_file})
            except ConfigError:
                pass
            config_names.append(name)
        return config_names

    def get_file_by_entities(self, entities: dict):
        """
        Get a file from the layout by entities.

        Parameters
        ----------
        entities : dict
            A dictionary containing the entities.

        Returns
        -------
        str
            The path to the file.
        """
        result = self.get(**entities, return_type="file")
        if len(result) > 1:
            raise ValueError(f"More than one file found for {entities}")
        return result[0]
