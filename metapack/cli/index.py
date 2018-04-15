# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

from shutil import copy
from os import listdir, remove, rename
from os.path import join, exists

from metapack.package import *
from rowgenerators import parse_app_url
from rowgenerators.appurl.file import FileUrl
from rowgenerators.exceptions import RowGeneratorError
from .core import MetapackCliMemo as _MetapackCliMemo
from .core import err, PACKAGE_PREFIX, add_package_to_index, prt, debug_logger
import dbm
import json
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
            if exists(join( p.ref.dirname().path, PACKAGE_PREFIX)):
                yield from yield_packages(parse_app_url((join( p.ref.dirname().path, PACKAGE_PREFIX))))

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

def dump_data(db, index_file):

    new_index_file = index_file + '.new'
    bak_index_file = index_file + '.bak'

    with open(new_index_file, 'w') as f:
        json.dump(db, f, indent=4)

    if exists(index_file):
        copy(index_file, bak_index_file)

    rename(new_index_file, index_file)


def index(args):

    index_file = join(args.directory, 'index.json')

    try:
        with open(index_file,'r') as f:
            db = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        db = {}

    prt('Index file:', index_file)

    u = parse_app_url(args.metatab_url)

    if not isinstance(u, FileUrl):
        err(f"Can only index File urls, not {type(u)}")

    for p in yield_unique_packages(u):
        add_package_to_index(p, db)

    dump_data(db, index_file)

    ident_vals = []
    key_vals = []
    for k, v in db.items():
        if v['type'] == 'ident':
            ident_vals.append((k, v['type'], v['url']))
        else:
            key_vals.append((k, v['type'], v['url']))

    print(tabulate(ident_vals+(sorted(key_vals)), headers='key type url'.split()))