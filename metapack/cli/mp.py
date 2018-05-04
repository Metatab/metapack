# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Root program for metapack programs

"""

from pkg_resources import get_distribution, DistributionNotFound, iter_entry_points
import argparse
import logging
import sys

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
   # package is not installed
   pass

from metapack.cli.core import  cli_init

def base_parser():

    parser = argparse.ArgumentParser(
        prog='mp',
        description='Create and manipulate metatab data packages. ')


    parser.add_argument('--exceptions', default=False, action='store_true',
                        help='Show full stack tract for some unhandled exceptions')

    parser.add_argument('--debug', default=False, action='store_true',
                        help='Turn on debug logging ( Basic Config ')


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

    try:
        # Happens when no commands are specified
        args.run_command
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