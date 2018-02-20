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

    parser.set_defaults(run_command=run_search)

    parser.add_argument('search', nargs=1, help="Path or URL to a metatab file")

def run_search(args):

    if args.search[0].startswith('index'):
        url_s = args.search[0]
    else:
        url_s = 'index:'+args.search[0]

    try:
        u = parse_app_url(url_s)

        prt(str(u.get_resource()))

    except AppUrlError as e:
        err(f"Failed to resolve: {str(u)}; {str(e)}")



