# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

import sys
from metapack import Downloader
from metapack.cli.core import prt, err
from rowgenerators import parse_app_url
from rowgenerators.exceptions import AppUrlError

downloader = Downloader()

def search(subparsers):

    parser = subparsers.add_parser(
        'search',
        help='Search for packages',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.add_argument('-l', '--list', default=False, action='store_true',
                        help="List the packages that would be indexed ( Only from the JSON index")

    parser.add_argument('-c', '--config', default=False, action='store_true',
                        help="Show the path to the index file")

    parser.set_defaults(run_command=run_search)

    parser.add_argument('search', nargs='?', help="Path or URL to a metatab file")

def run_search(args):
    from .core import get_search_index, search_index_file
    from tabulate import tabulate

    if args.config:
        prt(search_index_file())
        sys.exit(0)

    if not args.search or args.list:

        print(tabulate(sorted([(k,v['type'],v['url']) for k,v in get_search_index().items()]),
                                headers='Key Type Url'.split()))

    else:

        if args.search.startswith('index'):
            url_s = args.search
        else:
            url_s = 'index:'+args.search

        try:
            u = parse_app_url(url_s)

            prt(str(u.get_resource()))

        except AppUrlError as e:
            err(f"Failed to resolve: {str(u)}; {str(e)}")



