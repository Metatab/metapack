# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import re

from metapack import MetapackDoc, Downloader
from metapack.cli.core import prt, err, warn, metatab_info, write_doc, \
    update_name, process_schemas, extract_path_name, MetapackCliMemo
from metapack.util import make_metatab_file, datetime_now
from rowgenerators import parse_app_url
from rowgenerators.exceptions import SourceError
from rowgenerators.util import clean_cache
from tableintuit import RowIntuitError

downloader = Downloader()

def update(subparsers):
    parser = subparsers.add_parser(
        'update',
        help='Update a metatab file',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_update)

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")



    parser.set_defaults(handler=None)

    ##
    ## Build Group

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-s', '--schemas', default=False, action='store_true',
                             help='Rebuild the schemas for files referenced in the resource section')

    group.add_argument('-n', '--name', action='store_true', default=False,
                             help="Update the Name from the Datasetname, Origin and Version terms")

    parser.add_argument('-C', '--clean', action='store_true', default=False,
                        help='When building a schema, rebuild completely')

    parser.add_argument('-F', '--force', action='store_true', default=False,
                             help='Force the operation')


def run_update(args):

    m = MetapackCliMemo(args, downloader)


    if m.args.schemas:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        process_schemas(m.mt_file, cache=m.cache, clean=m.args.clean)

    if m.mtfile_url.scheme == 'file' and m.args.name:
        update_name(m.mt_file, fail_on_missing=True, force=m.args.force)
