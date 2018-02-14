# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

from metapack import Downloader, parse_app_url
from metapack.cli.core import prt, err, MetapackCliMemo
from metapack.appurl import SearchUrl
from rowgenerators import AppUrlError

downloader = Downloader()

def search(subparsers):

    parser = subparsers.add_parser(
        'search',
        help='Search for packages',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_search)

    parser.add_argument('metatabfile', nargs=1,help="Path or URL to a metatab file")

def run_search(args):

    m = MetapackCliMemo(args, downloader)

    try:
        u = parse_app_url('search:'+m.mtfile_arg)

        prt(str(u.get_resource()))
    except AppUrlError:
        err(f"Nothing found for '{m.mtfile_arg}'")



