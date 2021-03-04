# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from pkg_resources import (
    DistributionNotFound,
    get_distribution,
    iter_entry_points
)

from tabulate import tabulate

from metapack.cli.core import err, prt
from metapack.package import Downloader

downloader = Downloader.get_instance()


def config_args(subparsers):
    parser = subparsers.add_parser(
        'config',
        help='Print configuration information about the metapack installation'
    )

    parser.set_defaults(run_command=config)

    parser.add_argument('-v', '--version', default=False, action='store_true',
                        help='Print Metapack versions')

    parser.add_argument('-V', '--versions', default=False, action='store_true',
                        help='Print version of several important packages')

    parser.add_argument('-c', '--cache', default=False, action='store_true',
                        help='Print the location of the cache')

    parser.add_argument('-d', '--declare', default=False, action='store_true',
                        help='Print the location of the default declarition document')

    parser.add_argument('-m', '--materialized', default=False, action='store_true',
                        help='Print the location of the materialized data cache')

    parser.add_argument('-t', '--value-types', default=False, action='store_true',
                        help='Print a list of available value types')


def config(args):
    from metapack.exc import MetatabFileNotFound

    try:

        if args.version:
            prt(get_distribution('metapack'))

        elif args.cache:

            prt(downloader.cache.getsyspath('/'))

        elif args.materialized:
            from metapack.util import get_materialized_data_cache
            prt(get_materialized_data_cache())

        elif args.versions:
            print_versions()

        elif args.declare:
            print_declare()

        elif args.value_types:
            print_value_types()

        else:
            print_versions()

    except MetatabFileNotFound:
        err('No metatab file found')


def print_versions():
    from tabulate import tabulate

    main_packages = ('metapack', 'metatab', 'metatabdecl', 'rowgenerators', 'tableintuit')

    packages = []
    for pkg_name in main_packages:
        try:
            d = get_distribution(pkg_name)
            packages.append([d.project_name, d.version])

        except (DistributionNotFound, ModuleNotFoundError) as e:
            # package is not installed
            print(e)

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


def print_declare():
    from metatab.util import declaration_path

    prt(declaration_path('metatab-latest'))


def print_value_types():
    from rowgenerators.valuetype import value_types

    rows = [(k, v.__name__, v.__doc__) for k, v in value_types.items()]

    print(tabulate(sorted(rows), headers='Code Class Description'.split()))
