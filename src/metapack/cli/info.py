# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""
import argparse
import sys
from pkg_resources import (
    DistributionNotFound,
    get_distribution,
    iter_entry_points
)

from tabulate import tabulate

from metapack.cli.core import err, prt, warn
from metapack.package import Downloader
from metapack.util import iso8601_duration_as_seconds

from .core import MetapackCliMemo as _MetapackCliMemo

downloader = Downloader.get_instance()


class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)
        self


def info_args(subparsers):
    """
    Entry program for running Metapack commands.
    """

    parser = subparsers.add_parser(
        'info',
        help='Print info about a package ',
        description=info_args.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.set_defaults(run_command=info)

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-n', '--name', default=False, action='store_true',
                       help="Print the name, with version")
    group.add_argument('-N', '--root-name', default=False, action='store_true',
                       help="Print the name, without the version")

    group.add_argument('-r', '--resources', default=False, action='store_true',
                       help="List the resources in the package")

    group.add_argument('-D', '--distributions', default=False, action='store_true',
                       help="Show distribution URLS")

    group.add_argument('-s', '--schema', default=False, action='store_true',
                       help="Print a table of the common schema for all resources, or "
                            "if the metatab file ref has a resource, only that one")

    group.add_argument('-R', '--row-table', default=False, action='store_true',
                       help="Print the row-processor table, including transforms and valuetypes")

    group.add_argument('-p', '--package-url', default=False, action='store_true',
                       help="Print the package url")

    group.add_argument('-P', '--package-root', default=False, action='store_true',
                       help="Print the package root url")

    group.add_argument('-T', '--value-types', default=False, action='store_true',
                       help='Print a list of available value types')

    group.add_argument('-t', '--transforms', default=False, action='store_true',
                       help='Print a list of available transform functions')

    group.add_argument('-U', '--next-update', default=False, action='store_true',
                       help='Print the date of the next update, based on Root.Modified and Root.UpdateFrequency')

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")


def info(args):
    from metapack.exc import MetatabFileNotFound

    m = MetapackCliMemo(args, downloader)

    rc = None

    try:
        if m.args.name:
            prt(m.doc.name)

        elif m.args.resources:
            list_rr(m.doc)

        elif m.args.root_name:
            prt(m.doc.as_version(None))

        elif m.args.package_url:
            prt(m.package_url)

        elif m.args.package_root:
            prt(m.package_root)

        elif m.args.schema:
            dump_schemas(m)

        elif m.args.row_table:
            dump_rptable(m)

        elif m.resource:
            resource_info(m)

        elif args.value_types:
            print_value_types(m)

        elif args.transforms:
            print_transforms(m)

        elif args.next_update:
            rc = next_update(m)

        elif args.distributions:
            print_distributions(m)

        else:
            prt(m.doc.name)

    except MetatabFileNotFound:
        err('No metatab file found')

    return rc


def resource_info(m):
    from rowgenerators.exceptions import RowGeneratorError

    r = m.get_resource()

    ru = r.resolved_url
    rsu = ru.get_resource()
    tu = rsu.get_target()
    rows = [
        ('Value', r.url),
        ("Expanded", r.expanded_url),
        ('Resolved', ru),
        ('URL Resource', rsu),
        ('URL path', tu),
        ('Target Path', tu.fspath)
    ]

    props = ['fragment_query', 'resource_file', 'resource_format',
             'target_file', 'segment', 'target_format',
             'encoding', 'headers', 'start', 'end']

    rows += [(p, getattr(tu, p, '')) for p in props]

    rows.append(('URL Type', type(ru)))

    try:
        rows.append(('Generator', type(ru.generator)))
    except RowGeneratorError:
        rows.append(('Generator', "Error: Can't locate"))

    prt(tabulate(rows))


def print_versions(m):
    main_packages = ('metapack', 'metatab', 'metatabdecl', 'rowgenerators', 'publicdata', 'tableintuit')

    packages = []
    for pkg_name in main_packages:
        try:
            d = get_distribution(pkg_name)
            packages.append([d.project_name, d.version])

        except (DistributionNotFound, ModuleNotFoundError):
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

    if d:
        prt('== Resources ==')
        prt(tabulate(d, 'Type Name Url'.split()))
        prt('')

    d = []
    for r in doc.references():
        d.append(('Reference', r.name, r.url))

    if d:
        prt('== References ==')
        prt(tabulate(d, 'Type Name Url'.split()))


def get_resource(m):
    r = m.doc.resource(m.resource)

    if not r:
        prt('\nSelect a resource to display the schema for:\n')
        list_rr(m.doc)
        prt('')
        prt("Specify the resource as a fragment, escaping it if the '#' is the first character. For instance: ")
        prt("  mp info -s .#resource_name")
        prt('')
        sys.exit(0)

    return r


def dump_schemas(m):
    r = get_resource(m)

    st = r.schema_term

    if not st:
        err("No schema term for resource {}".format(r.name))

    rows_about_columns = []

    has_vt = any(c.get_value('valuetype') for c in st.find('Table.Column'))

    if has_vt:
        headers = 'Name AltName DataType ValueType Description'.split()

        def cols(c):
            return (c.name, c.get_value('altname'), c.get_value('datatype'), c.get_value('valuetype'),
                    c.get_value('description'))
    else:
        headers = 'Name AltName DataType Description'.split()

        def cols(c):
            return (c.name, c.get_value('altname'), c.get_value('datatype'), c.get_value('description'))

    for c in st.find('Table.Column'):
        rows_about_columns.append(cols(c))

    prt(tabulate(rows_about_columns, headers=headers))


def dump_rptable(m):
    r = get_resource(m)

    print(r.row_processor_table())


def print_declare(m):
    from metatab.util import declaration_path

    prt(declaration_path('metatab-latest'))


def print_value_types(m):
    from rowgenerators.valuetype import value_types

    rows = [(k, v.__name__, v.__doc__) for k, v in value_types.items()]

    print(tabulate(sorted(rows), headers='Code Class Description'.split()))


def print_transforms(m):
    env = m.doc.env

    print(env)
    return

    # rows = [(k, v.__name__, v.__doc__) for k, v in value_types.items()]

    # print(tabulate(sorted(rows), headers='Code Class Description'.split()))

def print_distributions(m):
    from pathlib import Path
    import yaml
    from metapack import open_package
    from metapack_build.cli.build import last_dist_marker_path

    try:
        with last_dist_marker_path('.').open() as f:
            ld = yaml.safe_load(f)

        print(yaml.safe_dump(ld))

    except (IOError) as e:
        warn('No distributions found. Run `mp s3`')



def next_update(m):
    from datetime import datetime, timedelta
    from dateutil.parser import parse

    last_mod = m.doc['Root'].find_first_value('Root.Modified')

    if not last_mod:
        prt('No Root.Modified')
        return 2

    last_mod = parse(last_mod)

    uf = m.doc['Root'].find_first_value('Root.UpdateFrequency')

    now = datetime.now().date()

    if not uf:
        prt(now.isoformat())
        return 1

    td = timedelta(seconds=iso8601_duration_as_seconds(uf))

    update_time = (last_mod + td).date()

    if update_time <= now:
        print('UPDATE', update_time.isoformat())
        return 0
    else:
        print('OK', update_time.isoformat())
        return 1
