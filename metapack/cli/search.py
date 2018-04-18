# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

import sys
from metapack import Downloader
from metapack.cli.core import prt, err

from rowgenerators import parse_app_url
from rowgenerators.exceptions import AppUrlError
from metapack.index import SearchIndex, search_index_file

downloader = Downloader()

def search(subparsers):

    parser = subparsers.add_parser(
        'search',
        help='Search for packages',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.add_argument('-l', '--list', default=False, action='store_true',
                        help="List the packages that would be indexed ( Only from the JSON index")

    parser.add_argument('-f', '--format', help='Select a specific package format')

    parser.add_argument('-1', '--one', action='store_true',
                        help='Find only one result, using the same resolution process used when building packages')

    parser.add_argument('-c', '--config', default=False, action='store_true',
                        help="Show the path to the index file")

    parser.set_defaults(run_command=run_search)

    parser.add_argument('search', nargs='?', help="Path or URL to a metatab file")

def run_search(args):

    from tabulate import tabulate

    if args.config:
        prt(search_index_file())
        sys.exit(0)

    if not args.search or args.list:

        idx = SearchIndex(search_index_file())

        packages = [ (e['name'], e['format'], e['url']) for e in idx.list()
                     if args.format is None or args.format == e['format']]

        print(tabulate(packages, headers='Name Format Url'.split()))

    elif args.one:

        if args.search.startswith('index'):
            url_s = args.search
        else:
            url_s = 'index:' + args.search

        try:
            u = parse_app_url(url_s)

            prt(str(u.get_resource()))

        except AppUrlError as e:
            err(f"Failed to resolve: {str(u)}; {str(e)}")

    else:

        idx = SearchIndex(search_index_file())

        prt('Index file:', idx.path)

        p = idx.search(args.search, args.format)

        packages = []
        for e in p:
            packages.append((e['name'], e['format'], e['url']))

        print(tabulate(packages, headers='Name Format Url'.split()))




