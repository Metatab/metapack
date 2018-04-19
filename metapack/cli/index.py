# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""


from metapack.package import *
from metapack.index import SearchIndex, search_index_file
from metapack.exc import MetatabFileNotFound
from rowgenerators import parse_app_url
from rowgenerators.appurl.file import FileUrl
from rowgenerators.exceptions import RowGeneratorError
from .core import MetapackCliMemo as _MetapackCliMemo, new_search_index
from .core import err, prt, debug_logger

from tabulate import tabulate

downloader = Downloader()


class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)
        self


def index_args(subparsers):
    parser = subparsers.add_parser(
        'index',
        help='Index packages for searching. '
    )

    parser.set_defaults(run_command=index)

    parser.add_argument('-l', '--list', default=False, action='store_true',
                        help="List the packages that would be indexed")

    parser.add_argument('-c', '--clear', default=False, action='store_true',
                        help="Clear the index")

    parser.add_argument('-d', '--directory', default=downloader.cache.getsyspath('/'),
                        help="Directory where index will be stored")

    parser.add_argument('metatab_url', nargs='?', default='./',
                        help='URL to a metatab package or container for packages')

def walk_packages(args, u):
    from os import walk
    from os.path import islink, join, isdir

    seen = set()

    if not isdir(u.path):
        try:
            yield open_package(u.path)
        except (RowGeneratorError, MetatabFileNotFound) as e:
            pass

        return

    for root, dirs, files in walk(u.path):

        try:
            p = open_package(root)
            # This was a package, so only recurse if it is a source package and has a _packages dir

            if '_packages' in dirs:
                del dirs[:]
                dirs.append('_packages')
            else:
                del dirs[:]

            if str(p.ref) not in seen:
                yield p
            seen.add(str(p.ref))
            continue

        except (RowGeneratorError, MetatabFileNotFound) as e:
            # directory is not a package, carry on
            pass

        for f in files:
            if not islink(join(root,f)):
                try:
                    p = open_package(join(root,f))
                    if str(p.ref) not in seen:
                        yield p
                    seen.add(str(p.ref))
                except (RowGeneratorError, MetatabFileNotFound) as e:
                    # directory is not a package, carry on
                    pass


def index(args):

    idx = SearchIndex(search_index_file())

    prt('Index file:', idx.path)

    u = parse_app_url(args.metatab_url)

    if args.list:

        pkg_list = []
        for p in walk_packages(args, u):
            pkg_list.append((p.name, p.ref))

        prt(tabulate(pkg_list, headers='name Url'.split()))

    elif args.clear:
        idx.clear()
        prt('Cleared the index')
    else:
        if not isinstance(u, FileUrl):
            err(f"Can only index File urls, not {type(u)}")

        for p in walk_packages(args, u):
            idx.add(p)

        idx.write()
