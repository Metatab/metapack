# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import sys
from os import getenv
from metapack import Downloader
from metapack.cli.core import prt, err, MetapackCliMemo, cli_init
from metapack.appurl import SearchUrl
from tabulate import tabulate
import shutil
from itertools import islice
from bisect import bisect
from terminaltables import AsciiTable, SingleTable, DoubleTable, GithubFlavoredMarkdownTable

downloader = Downloader()


def run(subparsers):

    parser = subparsers.add_parser(
        'run',
        help='Generate rows for a resource or reference ',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_run)

    #
    # What resource to run

    reference_group = parser.add_argument_group("Resource or Reference specification")

    group = reference_group.add_mutually_exclusive_group()

    group.add_argument('-r', '--resource',
                        help="Name of the Root.Resource to run  ")

    group.add_argument('-f', '--reference',
                        help="Name of the Root.Reference to run  ")



    #
    # Output format

    format_group = parser.add_argument_group("Output format")

    group = format_group.add_mutually_exclusive_group()

    group.add_argument('-c', '--CSV', default=False, action='store_true',
                             help='Output as CSV')

    group.add_argument('-t', '--tabs', default=False, action='store_true',
                       help='Output as tab-delimited rows')

    group.add_argument('-j', '--json', default=False, action='store_true',
                       help='Output JSON lines. Each line is a completel JSON object')

    group.add_argument('-y', '--yaml', default=False, action='store_true',
                       help='Output YAML')

    group.add_argument('-T', '--table', default=False, action='store_true',
                       help='Output 20 rows in a table format. Truncates columns to width of terminal')

    #
    # Table format options

    table_group = parser.add_argument_group('Options for Table ( -T ) format')

    table_group.add_argument('-p', '--pivot', default=False, action='store_true',
                       help='When outputting a table, transpose rows for columns')

    table_group.add_argument('-m', '--markdown', default=False, action='store_true',
                       help='When outputting a table, use Markdown format')

    table_group.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    #
    # Other options

    output_group = parser.add_argument_group("General output options")

    output_group.add_argument('-S', '--sample', type=str, help="Sample values from a column")

    output_group.add_argument('-L', '--limit', type=int,
                       help="Limit the number of output rows ")

    parser.set_defaults(handler=None)

def list_rr(doc):

    d = []
    for r in doc.resources():
        d.append(('Resource', r.name, r.url))

    for r in doc.references():
        d.append(('Reference', r.name, r.url))

    prt(tabulate(d, 'Type Name Url'.split()))


def get_resource(m):


    if m.resource:
        r = m.doc.resource(m.resource)
        return r if r else m.doc.reference(m.resource)
    elif m.args.resource:
        return m.doc.resource(m.args.resource)
    elif m.args.reference:
        return m.doc.reference(m.args.reference)
    else:
        return None


def run_run(args):

    m = MetapackCliMemo(args, downloader)

    r = get_resource(m)

    doc = m.doc

    if not r:
        list_rr(doc)
        sys.exit(0)


    if not r:
        prt("ERROR: No resource or reference for '{}' valid terms are:\n".format(m.args.resource))
        list_rr(doc)
        sys.exit(1)

    if m.args.sample:

        from collections import Counter

        limit = args.limit if args.limit else 5000

        c = Counter( r[m.args.sample] for r in islice(r.iterrows, None, limit))

        prt(tabulate(c.most_common(10), headers='Value Count'.split()))


    elif m.args.table:

        limit = args.limit if args.limit else 20

        t_width = shutil.get_terminal_size()[0]

        rows = list(islice(r, None, limit))

        if m.args.pivot:
            rows = list(zip(*rows))
            header = ['Column Name'] + ['Column{}'.format(i) for i in range(1,len(rows[1])) ]
            rows = [header] + rows

        # Only display the colums that will fit in the terminal window
        # If I were good, this would be a comprehension
        max_lengths = [0] * len(rows[0])
        for row in rows:
            for i, col in enumerate(row):
                v = str(col)
                if '\n' in v:
                    ln = max(len(l)+3 for l in v.splitlines() )
                else:
                    ln = len(str(col))+3

                max_lengths[i] = max(max_lengths[i], ln )

        display_cols = bisect([ sum(max_lengths[:i]) for i in range(1,len(max_lengths)+1)],t_width-4)

        # print(tabulate( [row[:display_cols] for row in rows], tablefmt="psql"))

        if m.args.markdown:
            table_class = GithubFlavoredMarkdownTable
        else:
            table_class = SingleTable

        at = table_class([row[:display_cols] for row in rows])
        at.inner_row_border = True
        print (at.table)

    else:
        import csv

        if args.limit:
            gen_wrap = lambda g: islice(g, None, args.limit)
        else:
            gen_wrap = lambda g: g

        if m.args.json:
            for i,j in enumerate(gen_wrap(r.iterjson())):
                print(j)

        elif m.args.yaml:
            for i,j in enumerate(gen_wrap(r.iteryaml())):
                print(j, j,end='')
        elif m.args.tabs:
            w = csv.writer(sys.stdout, delimiter='\t')
            for i,j in enumerate(gen_wrap(r)):
                w.writerow(j)

        else: # m.args.csv:
            w = csv.writer(sys.stdout)
            for i,j in enumerate(gen_wrap(r)):
                w.writerow(j)

