# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Root program for metapack programs

"""

from pkg_resources import iter_entry_points, get_distribution, DistributionNotFound
from .core import prt, err
import argparse
import logging
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
   # package is not installed
   pass

from metapack.cli.core import  cli_init


def mp():


    parser = argparse.ArgumentParser(
        prog='mp',
        description='Create and manipulate metatab data packages. ')

    parser.add_argument('-v', '--version', default=False, action='store_true',
                             help='Print Metapack versions')

    parser.add_argument('-V', '--versions', default=False, action='store_true',
                        help='Print version of several important packages')

    parser.add_argument('--exceptions', default=False, action='store_true',
                        help='Show full stack tract for some unhandled exceptions')

    parser.add_argument('--debug', default=False, action='store_true',
                        help='Turn on debug logging ( Basic Config ')

    parser.add_argument('-C', '--cache', default=False, action='store_true',
                        help='Print the location of the cache')

    subparsers = parser.add_subparsers(help='Commands')

    for ep in iter_entry_points(group='mt.subcommands'):

        f = ep.load()
        f(subparsers)

    args = parser.parse_args()

    cli_init(log_level=logging.DEBUG if args.debug else logging.INFO)

    if args.version:
        prt(get_distribution('metapack'))

    elif args.cache:
        from shlex import quote
        from metapack import Downloader
        downloader = Downloader()

        prt(quote(downloader.cache.getsyspath('/')))

    elif args.versions:

        from pkg_resources import EntryPoint

        prt('--- Main Packages')

        main_packages = ('metapack', 'metatab','rowgenerators','publicdata')

        for pkg_name in main_packages:
            try:
                prt(get_distribution(pkg_name))
            except (DistributionNotFound, ModuleNotFoundError) as e:
                # package is not installed

                pass

        prt('')
        prt('--- Subcommands')

        for ep in iter_entry_points(group='mt.subcommands'):
            prt(ep.name,  ep.dist)

    else:
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