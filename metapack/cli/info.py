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
from pkg_resources import get_distribution, DistributionNotFound, iter_entry_points

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

    group.add_argument('-r', '--resources', default=False, action='store_true',
                       help="List the resources in the package")

    group.add_argument('-s', '--schema', default=False, action='store_true',
                       help="Print a table of the common schema for all resources, or if the metatab file ref has a resource, only that one")

    parser.add_argument('-v', '--version', default=False, action='store_true',
                             help='Print Metapack versions')

    parser.add_argument('-V', '--versions', default=False, action='store_true',
                        help='Print version of several important packages')

    parser.add_argument('-C', '--cache', default=False, action='store_true',
                        help='Print the location of the cache')

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

def info(args):
    from metapack.exc import MetatabFileNotFound

    m = MetapackCliMemo(args, downloader)

    try:
        m.doc

        if m.args.name:
            prt(m.doc.name)
        elif m.args.resources:
            list_rr(m.doc)
        elif m.args.root_name:
            prt(m.doc.as_version(None))
        elif m.args.schema:
            dump_schemas(m)
        else:
            prt(m.doc.name)


    except MetatabFileNotFound:

        if args.version:
            prt(get_distribution('metapack'))

        elif args.cache:
            from shlex import quote

            prt(quote(downloader.cache.getsyspath('/')))

        elif args.versions:
            print_versions(m)

        else:
            print_versions(m)



def print_versions(m):
    from pkg_resources import EntryPoint
    from tabulate import tabulate

    main_packages = ('metapack', 'metatab', 'metatabdecl', 'rowgenerators', 'publicdata', 'tableintuit')

    packages = []
    for pkg_name in main_packages:
        try:
            d = get_distribution(pkg_name)
            packages.append([d.project_name, d.version])

        except (DistributionNotFound, ModuleNotFoundError) as e:
            # package is not installed

            pass

    prt(tabulate(packages, headers='Package Version'.split()))
    prt('')
    prt(tabulate([(ep.name, ep.dist) for ep in iter_entry_points(group='mt.subcommands')],
                                                                headers='Subcommand Package Version'.split()))


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
        prt("Specify the resource as a fragment, escaping it if the '#' is the first character. For instance: ")
        prt("  mp info -s \#resource_name")
        prt('')
        sys.exit(0)

    dump_schema(m, r)
