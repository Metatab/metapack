# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

from os import listdir
from os.path import join, exists

from metapack.package import *
from rowgenerators import FileUrl, RowGeneratorError, parse_app_url
from .core import MetapackCliMemo as _MetapackCliMemo
from .core import err, PACKAGE_PREFIX, add_package_to_index, prt
import dbm
import json

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

    parser.add_argument('-b', '--dbm', default=False, action='store_true',
                        help="Output a DBM index")

    parser.add_argument('-d', '--directory', default=downloader.cache.getsyspath('/'),
                        help="Directory where index will be stored")

    parser.add_argument('metatab_url', nargs='?', default='./',
                        help='URL to a metatab package or container for packages')

def try_open(path):
    try:
        p = open_package(path)
        if p.get_value('Root.Issued'):
            yield p
        else:
            if exists(join(path, PACKAGE_PREFIX)):
                yield from yield_packages(parse_app_url((join(path, PACKAGE_PREFIX))))

    except RowGeneratorError as e:
        return

def yield_packages(u):

    if u.isdir():
        yield from try_open(u.path)
        for e in listdir(u.path):
            yield from try_open(join(u.path,e))
    else:
        yield from try_open(u)

def yield_unique_packages(u):
    seen = set()

    for p in yield_packages(u):
        if str(p.ref) not in seen:
            yield p
            seen.add(str(p.ref))

def index(args):

    if args.dbm:
        index_file = join(args.directory, 'index.db')
        db = dbm.open(index_file, 'c')
        f = None
    else:
        index_file = join(args.directory, 'index.json')

        try:
            with open(index_file,'r') as f:
                db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            db = {}

        f = open(index_file, 'w')

    prt('Index file:', index_file)

    u = parse_app_url(args.metatab_url)

    if not isinstance(u, FileUrl):
        err(f"Can only index File urls, not {type(u)}")

    key_vals = []

    for p in yield_unique_packages(u):
        keys = add_package_to_index(p, db)
        for key in keys:
            key_vals.append((key, p.package_url))

    if f:
        # DBM expects bytes, json expects strings.
        db = {k:(v.decode('utf8') if not isinstance(v, str) else v) for k, v in db.items()}
        json.dump(db, f, indent=4)
        f.close()
    else:
        db.close()

    from tabulate import tabulate
    print(tabulate(key_vals))