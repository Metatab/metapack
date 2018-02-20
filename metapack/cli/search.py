# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

from metapack import Downloader
from metapack.cli.core import prt, err, MetapackCliMemo
from metapack.appurl import SearchUrl
from rowgenerators import AppUrlError, parse_app_url

downloader = Downloader()

def search(subparsers):

    parser = subparsers.add_parser(
        'search',
        help='Search for packages',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.add_argument('-l', '--list', default=False, action='store_true',
                        help="List the packages that would be indexed ( Only from the JSON index")

    parser.set_defaults(run_command=run_search)

    parser.add_argument('search', nargs='?', help="Path or URL to a metatab file")

def run_search(args):

    if not args.search or args.list:
        import json
        from tabulate import tabulate

        index_file = Downloader().cache.getsyspath('index.json')

        with open(index_file) as f:
            print(tabulate(sorted([(k,v) for k,v in json.load(f).items()]),
                                   headers='Key Url'.split()))


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



