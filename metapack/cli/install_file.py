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

downloader = Downloader()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)
        self


def install_file(subparsers):

    parser = subparsers.add_parser(
        'file',
        help='Install packages to a filesystem'
    )

    parser.set_defaults(run_command=run_file_install)

    parser.add_argument('-l', '--list', default=False, action='store_true',
                             help="List installed packages")

    parser.add_argument('metatabfile', nargs='?', default='./',
                        help='Path to a Metatab file. Optional; if not specified, use metatab.csv for package specification ')

    if getenv('METAPACK_DATA'):
       d_args = '?'
       defaults_to=f"Defaults to METAPACK_DATA env var, '{getenv('METAPACK_DATA')}'"
    else:
        d_args = 1
        defaults_to = 'May also be set with the METAPACK_DATA env var'

    parser.add_argument('directory', nargs=d_args, default=getenv('METAPACK_DATA'),
                        help='Directory to which to install files. '+defaults_to)

def run_file_install(args):

    if args.list:
        index_path = join(args.directory, 'index.json')

        if exists(index_path):
            with open(index_path) as f:
                packages = json.load(f)
                for n in packages.keys():
                    if not n.startswith('_'):
                        prt(n)
        return

    try:
        args.directory = args.directory.pop(0) # Its a list
    except AttributeError:
        pass # its a string

    m = MetapackCliMemo(args, downloader=downloader)

    copy_packages(m)

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


def copy_file(m, source, dest):

    if exists(dest):
        remove(dest)

    prt(f"Copy file {source} to {dest} ")
    shutil.copy(source, dest)

    update_index(m.args.directory, join(dest))

def copy_dir(m, source, dest):

    if exists(dest):
        shutil.rmtree(dest)

    prt(f"Copy dir {source} to {dest}")
    shutil.copytree(source, dest)

    update_index(m.args.directory, dest)

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




