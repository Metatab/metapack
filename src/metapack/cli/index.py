# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

import argparse
import tempfile
from os.path import join

from rowgenerators import parse_app_url
from rowgenerators.appurl.file import FileUrl
from rowgenerators.appurl.web import S3Url
from rowgenerators.exceptions import RowGeneratorError
from tabulate import tabulate

from metapack.constants import PACKAGE_PREFIX
from metapack.exc import MetatabFileNotFound
from metapack.index import SearchIndex, search_index_file
from metapack.package import Downloader, open_package

from .core import err, prt

downloader = Downloader.get_instance()


def index_args(subparsers):
    """Index packages for searching.

    The index file is a JSON file, which is by default index.json in the cache.
    The file can be moved by setting the METAPACK_SEARCH_INDEX environmental variable.

    """
    parser = subparsers.add_parser(
        'index',
        description=index_args.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.set_defaults(run_command=index)

    parser.add_argument('-l', '--list', default=False, action='store_true',
                        help="List the packages that would be indexed")

    parser.add_argument('-c', '--clear', default=False, action='store_true',
                        help="Clear the index")

    parser.add_argument('-C', '--config', default=False, action='store_true',
                        help="Show the location of the index file")

    parser.add_argument('-f', '--file', help="Alternative path to index file")

    parser.add_argument('-w', '--write', help="After creating an index file from S3 and  write back the index file",
                        action='store_true', required=False)

    parser.add_argument('-D', '--dump',
                        help="Dump a Metatab formatted version of the index")

    parser.add_argument('-L', '--load',
                        help="Load in a Metatab formatted index file ")

    parser.add_argument('-p', '--profile', help="Name of a BOTO or AWS credentials profile, for S3 indexing",
                        required=False)

    parser.add_argument('-r', '--result', action='store_true', default=False,
                        help="If mp -q flag set, still report results")

    parser.add_argument('metatab_url', nargs='?', default='./',
                        help='URL to a metatab package or container for packages')


def walk_packages(args, u):
    from os import walk
    from os.path import islink, join, isdir

    seen = set()

    # Try all files as packages
    if not isdir(u.path):
        try:
            yield open_package(u.path)
        except (RowGeneratorError, MetatabFileNotFound):
            pass

        return

    for root, dirs, files in walk(u.path):

        try:
            p = open_package(root)

            # This was a package, so only recurse if it is a source package and has a _packages dir

            if PACKAGE_PREFIX in dirs:
                del dirs[:]
                dirs.append(PACKAGE_PREFIX)
            else:
                del dirs[:]

            if str(p.ref) not in seen:
                yield p

            seen.add(str(p.ref))
            continue

        except (RowGeneratorError, MetatabFileNotFound):
            # directory is not a package, carry on
            pass

        for f in files:
            if not islink(join(root, f)):
                try:

                    p = open_package(join(root, f))
                    if str(p.ref) not in seen:
                        yield p
                    seen.add(str(p.ref))
                except (RowGeneratorError, MetatabFileNotFound):
                    # directory is not a package, carry on
                    pass


def write_s3(m):
    raise NotImplementedError()

    path = None

    print('Indexing tmp index', path)

    idx = SearchIndex(path)

    index_s3(m.s3_url, idx)

    with open(path) as f:
        m.bucket.write(f.read(), 'index.json', m.acl)


def index(args):
    n_indexed = 0
    write_index = False

    if args.write and args.list:
        err("Can't combine --write and --list")

    if args.write:
        if not args.file:
            args.file = join(tempfile.mkdtemp(), 'something')
            args.file = '/tmp/index.json'

    idx = SearchIndex(args.file or search_index_file())

    u = parse_app_url(args.metatab_url)

    if not isinstance(u, S3Url) and args.write:
        err("--write can only be used with S3 urls")

    if args.list:

        pkg_list = []
        for p in walk_packages(args, u):
            pkg_list.append((p.name, p.ref))

        prt(tabulate(pkg_list, headers='name Url'.split()))
    elif args.config:
        prt(idx.path)

    elif args.clear:
        idx.clear()
        prt('Cleared the index')
    elif args.dump:
        dump_index(args, idx)
    elif args.load:
        load_index(args, idx)
    elif isinstance(u, FileUrl):
        entries = []
        for p in walk_packages(args, u):
            if p.ref.get_resource().get_target().target_format == 'ipynb':
                continue
            prt('Adding: ', p.ref)
            idx.add_package(p)
            entries.append(p.name)
            n_indexed += 1

        write_index = True

        prt("Indexed ", len(entries), 'entries')

    elif isinstance(u, S3Url):
        index_s3(u, idx)

        if args.write:
            from metapack.package.s3 import S3Bucket

            acl = 'public-read'

            bucket = S3Bucket(u, acl=acl, profile=args.profile)

            with open(args.file, mode='rb') as f:
                bucket.write(f.read(), 'index.json', acl=acl)

    else:
        err(f"Can only index File and S3 urls, not {type(u)}")

    if args.result and n_indexed > 0:
        print(f"🗂 Indexed {n_indexed} packages")

    if write_index:
        idx.write()


def index_s3(u, idx):
    # S3 package collections are flat, so we don't have to walk recursively.
    # However, we are only going to take the S3 packages, because they have the distribution
    # information for the rest of the packages, so we can get info about Excel and Zip packages
    # without opening them.
    entries = []
    import re

    for e in u.list():

        if e.target_format == 'csv':

            prt("Processing ", e)

            p = open_package(e)

            for d in p.find('Root.Distribution'):
                u = parse_app_url(d.value)

                version_m = re.search('-([^-]+)$', p.name)

                if u.target_format in ('xlsx', 'zip', 'csv'):
                    idx.add_entry(p.identifier, p.name, p.nonver_name, version_m.group(1), u.target_format,
                                  'metapack+' + str(u))

                    entries.append(p.name)
    idx.write()

    prt("Indexed ", len(entries), 'entries to ', idx.path)


def dump_index(args, idx):
    """Create a metatab file for the index"""

    from metatab import MetatabDoc

    doc = MetatabDoc()

    pack_section = doc.new_section('Packages', ['Identifier', 'Name', 'Nvname', 'Version', 'Format'])

    r = doc['Root']
    r.new_term('Root.Title', 'Package Index')

    for p in idx.list():
        pack_section.new_term('Package',
                              p['url'],
                              identifier=p['ident'],
                              name=p['name'],
                              nvname=p['nvname'],
                              version=p['version'],
                              format=p['format'])

    doc.write_csv(args.dump)


def load_index(args, idx):
    from metatab import MetatabDoc

    doc = MetatabDoc(args.load)

    entries = set()

    for t in doc['Packages']:
        idx.add_entry(t.identifier, t.name, t.nvname, t.version, t.format, t.value)
        entries.add(t.value)

    prt("Loaded {} packages".format(len(entries)))

    idx.write()
