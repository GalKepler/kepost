from qsipost import config


def main():
    """
    The main entrypoint for qsipost.
    """
    from qsipost.cli.workflow import build_workflow

    config_file = config.execution.work_dir / config.execution.run_uuid / "config.toml"
    config_file.parent.mkdir(exist_ok=True, parents=True)
    config.to_filename(config_file)

    retval = build_workflow(config_file)
    qsipost_wf = retval.get("workflow")
    config.load(config_file)

    if qsipost_wf and config.execution.write_graph:
        qsipost_wf.write_graph(graph2use="colored", format="svg", simple_form=True)

    config.loggers.workflow.log(
        25,
        "\n".join(
            ["QSIpost config:"] + ["\t\t%s" % s for s in config.dumps().splitlines()]
        ),
    )
    config.loggers.workflow.log(25, "QSIpost started!")
    try:
        qsipost_wf.run(**config.nipype.get_plugin())
    except Exception as e:
        from fmriprep.utils.telemetry import process_crashfile

        crashfolders = [
            config.execution.qsipost_dir
            / f"sub-{s}"
            / "log"
            / config.execution.run_uuid
            for s in config.execution.participant_label
        ]
        for crashfolder in crashfolders:
            for crashfile in crashfolder.glob("crash*.*"):
                process_crashfile(crashfile)
        config.loggers.workflow.critical(f"QSIpost failed: {e}")
        raise e
    else:
        config.loggers.workflow.log(25, "QSIpost finished successfully!")
