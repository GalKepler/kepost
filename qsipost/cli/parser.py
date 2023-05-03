# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright 2023 The NiPreps Developers <nipreps@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
"""Parser."""
import sys

from qsipost import config


def _build_parser(**kwargs):
    """Build parser object.
    ``kwargs`` are passed to ``argparse.ArgumentParser`` (mainly useful for debugging).
    """
    from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
    from functools import partial
    from pathlib import Path

    from packaging.version import Version

    def _path_exists(path, parser):
        """Ensure a given path exists."""
        if path is None or not Path(path).exists():
            raise parser.error(f"Path does not exist: <{path}>.")
        return Path(path).absolute()

    def _is_file(path, parser):
        """Ensure a given path exists and it is a file."""
        path = _path_exists(path, parser)
        if not path.is_file():
            raise parser.error(
                f"Path should point to a file (or symlink of file): <{path}>."
            )
        return path

    def _min_one(value, parser):
        """Ensure an argument is not lower than 1."""
        value = int(value)
        if value < 1:
            raise parser.error("Argument can't be less than one.")
        return value

    def _to_gb(value):
        scale = {"G": 1, "T": 10**3, "M": 1e-3, "K": 1e-6, "B": 1e-9}
        digits = "".join([c for c in value if c.isdigit()])
        units = value[len(digits) :] or "M"
        return int(digits) * scale[units[0]]

    def _drop_sub(value):
        return value[4:] if value.startswith("sub-") else value

    verstr = f"QSIpost v{config.environment.version}"
    currentv = Version(config.environment.version)
    is_release = not any(
        (currentv.is_devrelease, currentv.is_prerelease, currentv.is_postrelease)
    )

    parser = ArgumentParser(
        description="QSIpost: Post-processing of QSIprep workflows v{}".format(
            config.environment.version
        ),
        formatter_class=ArgumentDefaultsHelpFormatter,
        **kwargs,
    )
    PathExists = partial(_path_exists, parser=parser)
    IsFile = partial(_is_file, parser=parser)
    PositiveInt = partial(_min_one, parser=parser)
    # Arguments as specified by BIDS-Apps
    # required, positional arguments
    # IMPORTANT: they must go directly with the parser object
    parser.add_argument(
        "qsiprep-dir",
        action="store",
        dest="qsiprep_dir",
        type=PathExists,
        help="The root folder of QSIprep's output directory (sub-XXXXX folders should "
        "be found at the top level in this folder).",
    )
    parser.add_argument(
        "output-dir",
        action="store",
        dest="output_dir",
        type=Path,
        help="The output path for the outcomes of preprocessing and visual reports",
    )
    parser.add_argument(
        "analysis_level",
        choices=["participant"],
        help='Processing stage to be run, only "participant" in the case of '
        "QSIpost (see BIDS-Apps specification).",
    )

    g_bids = parser.add_argument_group("Options for filtering BIDS queries")
    g_bids.add_argument(
        "--participant-label",
        "--participant_label",
        action="store",
        nargs="+",
        type=_drop_sub,
        help="A space delimited list of participant identifiers or a single "
        "identifier (the sub- prefix can be removed)",
    )
    # Re-enable when option is actually implemented
    # g_bids.add_argument('-s', '--session-id', action='store', default='single_session',
    #                     help='Select a specific session to be processed')
    # Re-enable when option is actually implemented
    # g_bids.add_argument('-r', '--run-id', action='store', default='single_run',
    #                     help='Select a specific run to be processed')
    g_bids.add_argument(
        "--qsiprep-database-dir",
        metavar="PATH",
        dest="qsiprep_database_dir",
        type=Path,
        help="Path to a PyBIDS database folder, for faster indexing (especially "
        "useful for large datasets). Will be created if not present.",
    )
    g_bids.add_argument(
        "--reset-database",
        type=bool,
        dest="reset_database",
        default=False,
        help="Reset the PyBIDS database and re-index the dataset",
    )

    g_perfm = parser.add_argument_group("Options to handle performance")
    g_perfm.add_argument(
        "--nprocs",
        "--nthreads",
        "--n_cpus",
        "--n-cpus",
        dest="nprocs",
        action="store",
        type=PositiveInt,
        help="Maximum number of threads across all processes",
    )
    g_perfm.add_argument(
        "--omp-nthreads",
        action="store",
        type=PositiveInt,
        help="Maximum number of threads per-process",
    )
    g_perfm.add_argument(
        "--mem",
        "--mem_mb",
        "--mem-mb",
        dest="memory_gb",
        action="store",
        type=_to_gb,
        metavar="MEMORY_MB",
        help="Upper bound memory limit for fMRIPrep processes",
    )
    g_perfm.add_argument(
        "--low-mem",
        action="store_true",
        help="Attempt to reduce memory usage (will increase disk usage in working directory)",
    )
    g_perfm.add_argument(
        "--use-plugin",
        "--nipype-plugin-file",
        action="store",
        metavar="FILE",
        type=IsFile,
        help="Nipype plugin configuration file",
    )

    g_subset = parser.add_argument_group(
        "Options for performing only a subset of the workflow"
    )
    g_subset.add_argument(
        "--anat-only", action="store_true", help="Run anatomical workflows only"
    )

    g_conf = parser.add_argument_group("Workflow configuration")
    g_conf.add_argument(
        "--parcellation-atlas",
        "--parcellation_atlas",
        action="store",
        default="brainnetome",
        dest="parcellation_atlas",
        type=str,
        help="Parcellation atlas to use for tractography",
    )
    g_conf.add_argument(
        "--dipy-reconstruction-method",
        "--dipy_reconstruction_method",
        action="store",
        default="NLLS",
        choices=["NLLS", "WLS", "LS", "RT"],
        help="Diffusion reconstruction method to use with Dipy",
    )
    g_conf.add_argument(
        "--do-tractography",
        "--do_tractography",
        action="store_false",
        default=True,
        dest="do_tractography",
        type=bool,
        help="Whether to perform tractography",
    )
    g_conf.add_argument(
        "--tractography-algorithm",
        "--tractography_algorithm",
        action="store",
        dest="tractography_algorithm",
        default="SD_Stream",
        type=str,
        choices=[
            "FACT",
            "iFOD1",
            "iFOD2",
            "Nulldist1",
            "Nulldist2",
            "SD_Stream",
            "Seedtest",
            "Tensor_Det",
            "Tensor_Prob",
        ],
        help="Algorithm to use for tractography",
    )
    g_conf.add_argument(
        "--stepscale",
        action="store",
        dest="stepscale",
        type=float,
        default=0.5,
        help="step size of the tractography algorithm in mm.",
    )
    g_conf.add_argument(
        "--lenscale-min",
        "--lenscale_min",
        action="store",
        default=30,
        type=float,
        help="Minimum length of any tract in mm.",
    )
    g_conf.add_argument(
        "--lenscale-max",
        "--lenscale_max",
        action="store",
        default=500,
        type=float,
        help="Maximum length of any tract in mm.",
    )
    g_conf.add_argument(
        "--angle",
        dest="angle",
        action="store",
        type=float,
        default=45,
        help="Maximum angle between successive steps in degrees.",
    )
    g_conf.add_argument(
        "--n-tracts",
        "--n_tracts",
        action="store",
        dest="n_tracts",
        type=int,
        default=500000,
        help="Number of tracts to generate.",
    )
    g_conf.add_argument(
        "--do-sift-filtering",
        "--do_sift_filtering",
        action="store_false",
        default=True,
        dest="do_sift_filtering",
        type=bool,
        help="Whether to perform SIFT filtering",
    )
    g_conf.add_argument(
        "--sift-term-number",
        "--sift_term_number",
        action="store",
        dest="sift_term_number",
        type=int,
        default=500000,
        help="Number of streamlines to keep after SIFT filtering.",
    )
    g_conf.add_argument(
        "--sift-term-ratio",
        "--sift_term_ratio",
        action="store",
        dest="sift_term_ratio",
        type=float,
        default=0.2,
        help="Ratio of streamlines to keep after SIFT filtering.",
    )

    g_outputs = parser.add_argument_group("Options for modulating outputs")

    # FreeSurfer options
    g_fs = parser.add_argument_group("Specific options for FreeSurfer preprocessing")
    g_fs.add_argument(
        "--fs-license-file",
        metavar="FILE",
        type=IsFile,
        help="Path to FreeSurfer license key file. Get it (for free) by registering"
        " at https://surfer.nmr.mgh.harvard.edu/registration.html",
    )
    g_fs.add_argument(
        "--fs-subjects-dir",
        metavar="PATH",
        type=Path,
        help="Path to existing FreeSurfer subjects directory to reuse. "
        "(default: OUTPUT_DIR/freesurfer)",
    )

    g_other = parser.add_argument_group("Other options")
    g_other.add_argument("--version", action="version", version=verstr)
    g_other.add_argument(
        "-w",
        "--work-dir",
        action="store",
        type=Path,
        default=Path("work").absolute(),
        help="Path where intermediate results should be stored",
    )
    g_other.add_argument(
        "--clean-workdir",
        action="store_true",
        default=False,
        help="Clears working directory of contents. Use of this flag is not "
        "recommended when running concurrent processes of fMRIPrep.",
    )
    g_other.add_argument(
        "--resource-monitor",
        action="store_true",
        default=False,
        help="Enable Nipype's resource monitoring to keep track of memory and CPU usage",
    )
    g_other.add_argument(
        "--config-file",
        action="store",
        metavar="FILE",
        help="Use pre-generated configuration file. Values in file will be overridden "
        "by command-line arguments.",
    )
    g_other.add_argument(
        "--write-graph",
        action="store_true",
        default=False,
        help="Write workflow graph.",
    )
    g_other.add_argument(
        "--stop-on-first-crash",
        action="store_true",
        default=False,
        help="Force stopping on first crash, even if a work directory was specified.",
    )
    g_other.add_argument(
        "--debug",
        action="store",
        nargs="+",
        choices=config.DEBUG_MODES + ("all",),
        help="Debug mode(s) to enable. 'all' is alias for all available modes.",
    )

    return parser


def parse_args(args=None, namespace=None):
    """Parse args and run further checks on the command line."""
    import logging

    from niworkflows.utils.spaces import Reference, SpatialReferences

    parser = _build_parser()
    opts = parser.parse_args(args, namespace)

    if opts.config_file:
        skip = {} if opts.reports_only else {"execution": ("run_uuid",)}
        config.load(opts.config_file, skip=skip, init=False)
        config.loggers.cli.info(
            f"Loaded previous configuration file {opts.config_file}"
        )

    config.execution.log_level = int(max(25 - 5 * opts.verbose_count, logging.DEBUG))
    config.from_dict(vars(opts), init=["nipype"])

    # Retrieve logging level
    build_log = config.loggers.cli

    # Resource management options
    # Note that we're making strong assumptions about valid plugin args
    # This may need to be revisited if people try to use batch plugins
    if 1 < config.nipype.nprocs < config.nipype.omp_nthreads:
        build_log.warning(
            f"Per-process threads (--omp-nthreads={config.nipype.omp_nthreads}) exceed "
            f"total threads (--nthreads/--n_cpus={config.nipype.nprocs})"
        )

    qsiprep_dir = config.execution.qsiprep_dir
    output_dir = config.execution.output_dir
    work_dir = config.execution.work_dir
    version = config.environment.version

    # Wipe out existing work_dir
    if opts.clean_workdir and work_dir.exists():
        from niworkflows.utils.misc import clean_directory

        build_log.info(f"Clearing previous QSIprep working directory: {work_dir}")
        if not clean_directory(work_dir):
            build_log.warning(
                f"Could not clear all contents of working directory: {work_dir}"
            )

    # Update the config with an empty dict to trigger initialization of all config
    # sections (we used `init=False` above).
    # This must be done after cleaning the work directory, or we could delete an
    # open SQLite database
    config.from_dict({})

    # Ensure input and output folders are not the same
    if output_dir == qsiprep_dir:
        parser.error(
            "The selected output folder is the same as the input BIDS folder. "
            "Please modify the output path (suggestion: %s)."
            % qsiprep_dir
            / "derivatives"
            / ("qsipost-%s" % version.split("+")[0])
        )

    if qsiprep_dir in work_dir.parents:
        parser.error(
            "The selected working directory is a subdirectory of the input BIDS folder. "
            "Please modify the output path."
        )

    # Setup directories
    config.execution.log_dir = config.execution.output_dir / "logs"
    # Check and create output and working directories
    config.execution.log_dir.mkdir(exist_ok=True, parents=True)
    work_dir.mkdir(exist_ok=True, parents=True)

    # Force initialization of the BIDSLayout
    config.execution.init()
    all_subjects = config.execution.layout.get_subjects()
    if config.execution.participant_label is None:
        config.execution.participant_label = all_subjects

    participant_label = set(config.execution.participant_label)
    missing_subjects = participant_label - set(all_subjects)
    if missing_subjects:
        parser.error(
            "One or more participant labels were not found in the BIDS directory: "
            "%s." % ", ".join(missing_subjects)
        )

    config.execution.participant_label = sorted(participant_label)
    config.workflow.skull_strip_template = config.workflow.skull_strip_template[0]
