# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

from metapack.cli.core import prt, err
from metapack.package import *
from .core import MetapackCliMemo as _MetapackCliMemo
from tabulate import tabulate
import sys

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

    group.add_argument('-s', '--schema', default=False, action='store_true',
                       help="Print a table of the common schema for all resources, or if the metatab file ref has a resource, only that one")

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

def info(args):

    m = MetapackCliMemo(args, downloader)

    if m.args.name:
        prt(m.doc.name)
    elif m.args.root_name:
        prt(m.doc.as_version(None))
    elif m.args.schema:
        dump_schemas(m)
    else:
        prt(m.doc.name)

def list_rr(doc):

    d = []
    for r in doc.resources():
        d.append(('Resource', r.name, r.url))

    prt(tabulate(d, 'Type Name Url'.split()))

def dump_schema(m, r):
    st = r.schema_term
    rows_about_columns = []
    for c in st.find('Table.Column'):
        rows_about_columns.append((c.name, c.get_value('altname'), c.get_value('datatype'), c.get_value('description')))

    prt(tabulate(rows_about_columns, headers='Name AltName DataType Description'.split()))

def dump_schemas(m):

    r = m.doc.resource(m.resource)

    if not r:
        prt('\nSelect a resource to display the schema for:\n')
        list_rr(m.doc)
        prt('')
        sys.exit(0)

    dump_schema(m, r)
