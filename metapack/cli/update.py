# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

from metapack import Downloader
from metapack.util import  ensure_dir
from metapack.cli.core import update_name, process_schemas, MetapackCliMemo, list_rr, warn, prt, err
import sys
import requests
from os.path import dirname, basename, exists, splitext

downloader = Downloader()


def update(subparsers):
    parser = subparsers.add_parser(
        'update',
        help='Update a metatab file or metatpack package',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_update)

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    parser.set_defaults(handler=None)

    ##
    ## Build Group

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-s', '--schemas', default=False, action='store_true',
                       help='Rebuild the schemas for files referenced in the resource section')

    group.add_argument('-n', '--name', action='store_true', default=False,
                       help="Update the Name from the Datasetname, Origin and Version terms")

    parser.add_argument('-C', '--clean', action='store_true', default=False,
                        help='When building a schema, rebuild completely')

    parser.add_argument('-F', '--force', action='store_true', default=False,
                        help='Force the operation')

    parser.add_argument('-E', '--eda', action='store_true', default=False,
                        help='Create an EDA notebook for a resource')

    parser.add_argument('-D', '--descriptions', action='store_true', default=False,
                        help='Import descriptions for package references')

def run_update(args):
    m = MetapackCliMemo(args, downloader)

    if m.args.schemas:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        process_schemas(m.mt_file, cache=m.cache, clean=m.args.clean)

    elif m.mtfile_url.scheme == 'file' and m.args.name:
        update_name(m.mt_file, fail_on_missing=True, force=m.args.force)

    elif m.args.eda:
        write_eda_notebook(m)

    elif m.args.descriptions:
        update_descriptions(m)


def write_eda_notebook(m):
    # Get the EDA notebook file from Github
    import nbformat

    url = "https://raw.githubusercontent.com/Metatab/exploratory-data-analysis/master/eda.ipynb"

    resource = m.get_resource()

    if not resource:
        warn('Must specify a resource. Select one of:')
        list_rr(m.doc)
        sys.exit(0)

    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()

    nb_path = 'notebooks/{}-{}.ipynb'.format(splitext(basename(url))[0], resource.name)

    ensure_dir(dirname(nb_path))

    if exists(nb_path):
        err("Notebook {} already exists".format(nb_path))

    with open(nb_path, 'wb') as f:
        f.write(r.content)

    prt('Wrote {}'.format(nb_path))

    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=4)

    for cell in nb['cells']:
        if 'resource_name' in cell.get('metadata',{}).get('tags',[]):
            cell.source = "resource_name='{}'".format(resource.name)


    with open(nb_path, 'wt') as f:
        nbformat.write(nb, f)

def update_descriptions(m):

    doc = m.doc

    for ref in doc.references():

        v = ref.find_first('Description')

        ref['Description'] = ref.resource.description

        print(ref.name, id(ref))
        print("Updated '{}' to '{}'".format(ref.name, ref.description))

    #print(m.doc.as_csv())

    for ref in doc.references():
        v = ref.find_first('Description')

        print(ref.name, id(ref), ref.description)

    doc.write_csv()


