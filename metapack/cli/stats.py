# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

from metapack.cli.core import prt, err
from metapack.package import *
from .core import MetapackCliMemo as _MetapackCliMemo, list_rr
from tabulate import tabulate
import sys
from itertools import islice

downloader = Downloader()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)


def stats_args(subparsers):

    parser = subparsers.add_parser(
        'stats',
        help='Create statistical report for a resource'
    )

    parser.add_argument('-n', '--rows', type=int, help='Estimate of number of rows, for sampling')

    parser.add_argument('-s', '--sample', type=int, help='Sample a subset of <SAMPLE> rows')

    parser.add_argument('-H', '--head', type=int, help='Use only the first <HEAD> rows. Can substitute for --rows')

    parser.add_argument('-d', '--descriptive', default=False, action='store_true',
                       help="Calculate descriptive stats; min, max, mean, std, quartiles")

    parser.add_argument('-D', '--distribution', default=False, action='store_true',
                        help="Calculate distribution stats; histogram, skew, kurtosis")

    parser.add_argument('-V', '--values', default=False, action='store_true',
                        help="Display a set of unique values")

    parser.set_defaults(run_command=stats)

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")


def stats(args):

    m = MetapackCliMemo(args, downloader)

    if m.args.sample and (m.args.head and not m.args.rows):
        m.args.rows = m.args.head

    if bool(m.args.rows) ^ bool(m.args.sample):
        err("Either both or neither of ( --rows or --head) and --sample must be specified")

    if not m.resource:
        prt("ERROR: No resource or reference specified in the URL. Valid resources are:")
        list_rr(m.doc)
        sys.exit(1)

    if m.args.values and (m.args.distribution or m.args.descriptive):
        err("The --values option can be used with neither --descriptive nor --distribution ")

    from tableintuit import Stats

    r = m.doc.resource(m.resource)

    schema = [(c['name'],c['datatype']) for c in r.columns() ]

    if m.args.head:
        source = islice(r.iterdict, m.args.head)
    else:
        source = r.iterdict

    s = Stats( source, schema, n_rows=m.args.rows, sample_size=m.args.sample,
               descriptive=m.args.descriptive,
               distribution=m.args.distribution,
               sample_values=m.args.values)
    s.run()

    if m.args.values:
        for k,v in s.dict.items():
            print("==== {} ".format(k))
            for val, count in v.uvalues.items():
                print("   {} {}".format(count, val))
    else:
        print(s)