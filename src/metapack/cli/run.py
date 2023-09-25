# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import shutil
import sys
from bisect import bisect
from itertools import islice
from os import environ

from tabulate import tabulate
from terminaltables import GithubFlavoredMarkdownTable, SingleTable

from metapack import Downloader
from metapack.cli.core import MetapackCliMemo, err, list_rr, prt
from metapack.exc import MetatabFileNotFound
from metapack.util import get_materialized_data_cache

downloader = Downloader.get_instance()

Downloader.context.update(environ)

def run(subparsers):

    parser = subparsers.add_parser(
        'run',
        help='Generate rows for a resource or reference ')

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

    table_group.add_argument('-R', '--truncate', type=int, help='Truncate the width of column values ')

    table_group.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")


    #
    # Other options

    output_group = parser.add_argument_group("General output options")

    output_group.add_argument('-S', '--sample', type=str, help="Sample values from a column")
    output_group.add_argument('-L', '--limit', type=int,  help="Limit the number of output rows ")
    output_group.add_argument('-N', '--number', action='store_true', help="Add line numbers as the first column")
    output_group.add_argument('-n', '--no-schema', action='store_true', help="Don't use the schema to tansform the "
                                                                             "data ")

    parser.set_defaults(handler=None)


def run_run(args):

    m = MetapackCliMemo(args, downloader)

    r = m.get_resource()

    if m.args.no_schema:
        r = r.row_generator

    try:
        doc = m.doc
    except MetatabFileNotFound as e:
        err(str(e) +'\nPerhaps you meant .#{}?'.format(m.args.metatabfile))

    # Remove any data that may have been cached , for instance, from Jupyter notebooks
    shutil.rmtree(get_materialized_data_cache(doc), ignore_errors=True)

    if not r:
        prt('Select a resource to run:')
        list_rr(doc)
        sys.exit(0)

    if not r:
        prt("ERROR: No resource or reference for '{}' valid terms are:\n".format(m.args.resource))
        list_rr(doc)
        sys.exit(1)

    if m.args.sample:

        from collections import Counter

        limit = m.args.limit if m.args.limit else 5000

        c = Counter( r[m.args.sample] for r in islice(r.iterrows, None, limit))

        prt(tabulate(c.most_common(10), headers='Value Count'.split()))

    elif m.args.table:

        limit = m.args.limit if m.args.limit else 20

        t_width = shutil.get_terminal_size()[0]

        if m.args.truncate and not m.args.pivot:
            rows = []
            for row in islice(r, None, limit):
                rows.append( str(c)[:m.args.truncate] for c in row)

        elif m.args.truncate and m.args.pivot:
            # Don't truncate the column names when pivoting
            rows = []
            for i, row in enumerate(islice(r, None, limit)):
                if i == 0:
                    rows.append(row)
                else:
                    rows.append(str(c)[:m.args.truncate] for c in row)

        else:
            rows = list(islice(r, None, limit))

        if m.args.pivot:
            rows = list(zip(*rows))
            header = ['Column Name'] + ['Row {}'.format(i) for i in range(1,len(rows[1])) ]
            rows = [header] + rows

        # Only display the columns that will fit in the terminal window
        # If I were a good python programmer, this would be a comprehension
        max_lengths = [0] * len(list(rows[0]))
        for row in rows:
            for i, col in enumerate(row):
                v = str(col)
                if '\n' in v:
                    ln = max(len(l)+3 for l in v.splitlines() )
                else:
                    ln = len(str(col))+3

                try:
                    max_lengths[i] = max(max_lengths[i], ln )
                except IndexError:
                    max_lengths.extend([0])
                    max_lengths[i] = max(max_lengths[i], ln)


        display_cols = bisect([ sum(max_lengths[:i]) for i in range(1,len(max_lengths)+1)],t_width-4)

        # print(tabulate( [row[:display_cols] for row in rows], tablefmt="psql"))

        if m.args.markdown:
            table_class = GithubFlavoredMarkdownTable
        else:
            table_class = SingleTable

        at = table_class([list(row)[:display_cols] for row in rows])
        at.inner_row_border = True
        print (at.table)

    else:
        import csv

        if args.limit:
            gen_wrap = lambda g: islice(g, None, args.limit)
        else:
            gen_wrap = lambda g: g

        if args.number:
            def add_number(gen_wrap, g):

                for i,r in enumerate(gen_wrap(g)):
                    yield [i]+r

            from functools import partial
            gen_wrap = partial(add_number, gen_wrap)

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
