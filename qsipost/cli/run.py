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
