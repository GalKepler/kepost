from kepost import config


def main():
    """
    The main entrypoint for kepost.
    """
    from kepost.cli.workflow import build_workflow

    config_file = config.execution.work_dir / config.execution.run_uuid / "config.toml"
    config_file.parent.mkdir(exist_ok=True, parents=True)
    config.to_filename(config_file)

    retval = build_workflow(config_file)
    kepost_wf = retval.get("workflow")
    config.load(config_file)

    if kepost_wf and config.execution.write_graph:
        kepost_wf.write_graph(graph2use="colored", format="svg", simple_form=True)

    config.loggers.workflow.log(
        25,
        "\n".join(
            ["kepost config:"] + ["\t\t%s" % s for s in config.dumps().splitlines()]
        ),
    )
    config.loggers.workflow.log(25, "kepost started!")
    try:
        kepost_wf.run(**config.nipype.get_plugin())
    except Exception as e:
        from fmriprep.utils.telemetry import process_crashfile

        crashfolders = [
            config.execution.kepost_dir / f"sub-{s}" / "log" / config.execution.run_uuid
            for s in config.execution.participant_label
        ]
        for crashfolder in crashfolders:
            for crashfile in crashfolder.glob("crash*.*"):
                process_crashfile(crashfile)
        config.loggers.workflow.critical(f"kepost failed: {e}")
        raise e
    else:
        config.loggers.workflow.log(25, "kepost finished successfully!")
