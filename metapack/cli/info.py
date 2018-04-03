# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

from metapack.cli.core import prt
from metapack.package import *
from .core import MetapackCliMemo as _MetapackCliMemo

downloader = Downloader()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)
        self


def info_args(subparsers):

    parser = subparsers.add_parser(
        'info',
        help='Print info about a package '
    )

    parser.set_defaults(run_command=info)

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-n', '--name', default=False, action='store_true',
                             help="Print the name, with version")
    group.add_argument('-N', '--root-name', default=False, action='store_true',
                       help="Print the name, without the version")

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

def info(args):

    m = MetapackCliMemo(args, downloader)

    if m.args.name:
        prt(m.doc.name)
    elif m.args.root_name:
        prt(m.doc.as_version(None))