# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

import shutil
from os import getenv, remove, listdir
from os.path import join, basename, exists, isdir, splitext

from metapack.package import *
from metapack.util import ensure_dir

from .core import MetapackCliMemo as _MetapackCliMemo
from .core import prt
import json

downloader = Downloader.get_instance()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)
        self


def index_args(subparsers):

    parser = subparsers.add_parser(
        'file',
        help='Index packages for searching. '
    )

    parser.set_defaults(run_command=index)

    parser.add_argument('-l', '--list', default=False, action='store_true',
                             help="List the packages that would be indexed")

    parser.add_argument('metatab_url', nargs='?', default='./',
                        help='URL to a metatab package or container for packages')



def index(args):

    from rowgenerators import parse_app_url


    u = parse_app_url(args.metatab_url)

    for e in u.list():
        print(e)



def find_packages(name, pkg_dir):
    """Locate pre-built packages in the _packages directory"""
    for c in (FileSystemPackageBuilder, ZipPackageBuilder, ExcelPackageBuilder):

        package_path, cache_path = c.make_package_path(pkg_dir, name)

        if package_path.exists():

            yield c.type_code, package_path, cache_path #c(package_path, pkg_dir)

def copy_packages(m):

    for ptype, purl, cache_path in find_packages(m.doc.get_value('Root.Name'), m.package_root):

        dest = join(m.args.directory, basename(purl.path))

        ensure_dir(m.args.directory)

        if ptype in ('xlsx', 'zip'):
            copy_file(m, purl.path, dest)

        elif ptype == 'fs':
            copy_dir(m, purl.path, dest)


def update_index(d, package_path, suffix=''):

    index_path = join(d,'index.json')

    def add_package_to_index(p, packages, suffix=suffix):

        def add_suffix(name):
            if not suffix:
                return name
            else:
                return name + '-' + suffix

        pkg = open_package(p)

        packages[add_suffix(pkg.get_value('Root.Identifier'))] = p # identifier

        packages[add_suffix(pkg._generate_identity_name())] = p # Fully qualified name

        nv_name = add_suffix((pkg._generate_identity_name(mod_version=None)))

        if not '_versions' in packages:
            packages['_versions'] = {}

        if not nv_name in packages['_versions']:
            packages['_versions'][nv_name] = {}

        packages['_versions'][nv_name][pkg.get_value('Root.Version')] = p

        # Find latest version
        versions = set()
        for ver in packages['_versions'][nv_name].keys():
            try:
                versions.add(int(ver))
            except ValueError:
                # Only doing integer versions name. Need to figure out
                # how to handle Semantic Versions, later.
                pass

        if versions:
            latest = max(versions)

            packages[nv_name] = packages['_versions'][nv_name][str(latest)]

            packages[nv_name+'-latest'] = packages['_versions'][nv_name][str(latest)]

        # Remove the unziped zip package. FIXME It really should just pull the
        # metadata file without unzipping the whole package.

        if exists(p + '_d'):
            shutil.rmtree(p + '_d')

    if exists(index_path):
        with open(index_path) as f:
            packages = json.load(f)

        add_package_to_index(package_path, packages, suffix=suffix)

        with open(index_path,'w') as f:
            json.dump(packages, f, indent=4)

    else:

        packages = {}

        def yield_packages(d):

            for e in listdir(d):
                path = join(d, e)
                bn, ext = splitext(path)
                if isdir(path):
                    if exists(join(path, 'metadata.csv')):
                        yield join(path, 'metadata.csv')
                elif ext in ('.xls', '.xlsx', '.zip'):
                    yield path

        for p in yield_packages(d):
            add_package_to_index(p, packages, suffix=None)

        ensure_dir(join(d,'source'))

        for p in yield_packages(join(d,'source')):
            add_package_to_index(p, packages, suffix='source')

        with open(index_path,'w') as f:
            json.dump(packages, f, indent=4)




