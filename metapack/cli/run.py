# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import sys
from metapack import Downloader
from metapack.cli.core import prt, err, MetapackCliMemo
from metapack.jupyter.convert import convert_documentation, convert_notebook, extract_metatab, convert_hugo
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

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-r', '--resource',
                        help="Name of the Root.Resource to run  ")

    group.add_argument('-f', '--reference',
                        help="Name of the Root.Reference to run  ")

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-c', '--CSV', default=False, action='store_true',
                             help='Output as CSV')

    group.add_argument('-t', '--tabs', default=False, action='store_true',
                       help='Output as tab-delimited rows')

    group.add_argument('-T', '--table', default=False, action='store_true',
                       help='Output 20 rows in a table format. Truncates columns to width of terminal')

    group.add_argument('-j', '--json', default=False, action='store_true',
                       help='Output JSON')

    group.add_argument('-y', '--yaml', default=False, action='store_true',
                       help='Output YAML')

    # Arguments for Table
    parser.add_argument('-p', '--pivot', default=False, action='store_true',
                       help='When outputting a table, transpose rows for columns')

    parser.add_argument('-m', '--markdown', default=False, action='store_true',
                       help='When outputting a table, use Markdown format')

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    parser.set_defaults(handler=None)

def list_rr(doc):

    d = []
    for r in doc.resources():
        d.append(('Resource', r.name, r.url))

    for r in doc.references():
        d.append(('Reference', r.name, r.url))

    prt(tabulate(d, 'Type Name Url'.split()))

def run_run(args):


    m = MetapackCliMemo(args, downloader)

    doc = m.doc

    if not m.args.resource and not m.args.reference:
        list_rr(doc)
        sys.exit(0)

    else:

        if m.args.resource:
            r = doc.resource(m.args.resource)

        else:
            r = doc.reference(m.args.reference)

        if not r:
            prt("ERROR: No resource or reference for '{}' valid terms are:\n".format(m.args.resource))
            list_rr(doc)
            sys.exit(1)

        if m.args.table:
            t_width = shutil.get_terminal_size()[0]

            rows = list(islice(r, None, 20))

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

        elif m.args.json:
            print('[')
            for i,j in enumerate(r.iterjson()):
                term = ",\n" if i > 0 else ""
                print(term, j,end='')
            print(']')

        else:

            for row in r:
                print(row)
