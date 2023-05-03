from qsipost import config


def main():
    """
    The main entrypoint for qsipost.
    """
    config_file = config.execution.work_dir / config.execution.run_uuid / "config.toml"
    config_file.parent.mkdir(exist_ok=True, parents=True)
    config.to_filename(config_file)
