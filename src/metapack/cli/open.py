# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Metapack CLI program for creating new metapack package directories
"""

import argparse
import sys

from metapack import Downloader
from metapack.cli.core import MetapackCliMemo, list_rr, prt

from .core import MetapackCliMemo as _MetapackCliMemo

downloader = Downloader.get_instance()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)

def open_args(subparsers):
    """
    The `mp open` command will open a resource with the system application, such as Excel or OpenOffice

    """
    parser = subparsers.add_parser(
        'open',
        help='open a CSV resource with a system application',
        description=open_args.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.set_defaults(run_command=open_cmd)

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    return parser


def open_cmd(args):

    m = MetapackCliMemo(args, downloader)

    r = m.get_resource()

    doc = m.doc

    if not r:
        list_rr(doc)
        sys.exit(1)
