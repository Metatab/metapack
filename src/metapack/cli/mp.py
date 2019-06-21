# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Root program for metapack programs

"""

import argparse
import logging
import sys
from pkg_resources import (
    DistributionNotFound,
    get_distribution,
    iter_entry_points
)
from textwrap import dedent

from metapack import Downloader
from metapack.cli.core import cli_init

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
   # package is not installed
   pass


def base_parser():
    """Entry program for running Metapack commands.
    """
    parser = argparse.ArgumentParser(
        prog='mp',
        description=base_parser.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )


    parser.add_argument('--exceptions', '-e', default=False, action='store_true',
                        help='Show full stack tract for some unhandled exceptions')

    parser.add_argument('--debug', '-d', default=False, action='store_true',
                        help='Turn on debug logging ( Basic Config ) ')

    parser.add_argument('--no-cache', '-n', default=False, action='store_true',
                        help='Ignore the download cache')

    subparsers = parser.add_subparsers(help='Commands')

    for ep in iter_entry_points(group='mt.subcommands'):

        f = ep.load()
        f(subparsers)

    return parser

def mp():
    from .core import prt, err

    parser = base_parser()

    args = parser.parse_args()

    cli_init(log_level=logging.DEBUG if args.debug else logging.INFO)

    if args.no_cache:
        downloader = Downloader.get_instance()
        downloader.use_cache = False

    try:
        args.run_command # Happens when no commands are specified
    except AttributeError:
        parser.print_help()
        sys.exit(2)

    try:
        args.run_command(args)
    except Exception as e:
        if args.exceptions:
            raise e
        else:
            if e.__cause__:
                err(f"{e.__class__.__name__} {str(e)}\nCaused by: {type(e.__cause__)} {str(e.__cause__)}")
            else:
                err(f"{e.__class__.__name__}  {str(e)}")
