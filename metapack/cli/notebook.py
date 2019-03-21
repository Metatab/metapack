# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import sys

import requests
from metapack import Downloader, MetapackDoc
from metapack.cli.core import list_rr, warn, prt, err, MetapackCliMemo, write_doc

from metapack.jupyter.core import edit_notebook, set_cell_source
from metapack.util import ensure_dir
from os.path import dirname, basename, exists, splitext

downloader = Downloader.get_instance()


def notebook(subparsers):
    parser = subparsers.add_parser(
        'notebook',
        help='Create and convet Jupyter notebooks ',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.add_argument('notebook', nargs='?',
                        help="Path to a notebok file' ")

    parser.set_defaults(handler=None)

    ##
    ## New Notebooks

    cmdsp = parser.add_subparsers(help='sub-command help')

    cmdp = cmdsp.add_parser('new', help='Create new notebooks')
    cmdp.set_defaults(run_command=new_cmd)

    cmdp.add_argument('-m', '--metatab', action='store_true', default=False,
                      help='Create a metatab notebook from a metatab file')

    cmdp.add_argument('-E', '--eda', action='store_true', default=False,
                      help='Create an EDA notebook for a resource')

    cmdp.add_argument('-b', '--notebook', action='store_true', default=False,
                      help='Create a new, blank notebook')

    cmdp.add_argument('metatabfile', nargs='?',
                      help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    ##
    ## Build Group

    cmdp = cmdsp.add_parser('convert', help='Convert to other formats')
    cmdp.set_defaults(run_command=convert_cmd)

    cmdp.add_argument('-H', '--hugo', default=False, nargs='?',
                      help='Write images and Markdown into a Hugo static site directory. or use '
                           'METAPACK_HUGO_DIR env var')

    cmdp.add_argument('-m', '--metatab', default=False,
                      help='Convert metatab data between .ipynb and .csv files, depending on argument')


def new_cmd(args):
    downloader = Downloader.get_instance()

    m = MetapackCliMemo(args, downloader)

    if m.args.eda:
        write_eda_notebook(m)

    elif m.args.notebook:
        write_notebook(m)

    elif m.args.metatab:
        write_metatab_notebook(m)


def convert_cmd(args):
    from metapack.jupyter.convert import convert_hugo

    if False:  # args.package:
        convert_notebook(args.notebook)

    elif False:  # args.documentation:
        convert_documentation(args.notebook)

    elif False:  # args.metatab:
        doc = extract_metatab(args.notebook)

        if args.lines:
            for line in doc.lines:
                print(": ".join(line))
        else:
            print(doc.as_csv())

    elif args.hugo:
        convert_hugo(args.notebook, args.hugo)

    elif args.metatab:
        convert_metatab_notebook(args.metatab)


def write_notebook(m):
    # Get the EDA notebook file from Github

    url = "https://raw.githubusercontent.com/Metatab/notebook-templates/master/package-notebook.ipynb"

    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()

    nb_path = 'notebooks/new-notebook.ipynb'

    ensure_dir(dirname(nb_path))

    if exists(nb_path):
        err("Notebook {} already exists".format(nb_path))

    with open(nb_path, 'wb') as f:
        f.write(r.content)

    prt('Wrote {}'.format(nb_path))


def write_eda_notebook(m):
    # Get the EDA notebook file from Github

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

    with edit_notebook(nb_path) as nb:
        set_cell_source(nb, 'resource_name', "resource_name='{}'".format(resource.name))


def write_metatab_notebook(m):
    from metapack.jupyter.convert import write_metatab_notebook as _write_metatab_notebook
    _write_metatab_notebook(m.doc)


def convert_metatab_notebook(source):
    from metapack.jupyter.convert import extract_notebook_metatab
    from metapack.jupyter.convert import write_metatab_notebook as _write_metatab_notebook
    from pathlib import Path

    source = Path(source)

    if source.suffix == '.csv':
        dest = source.with_suffix('.ipynb')
        doc = MetapackDoc(source)
        doc.ensure_identifier()
        doc.update_name(create_term=True)
        _write_metatab_notebook(doc, dest)

    elif source.suffix == '.ipynb':
        dest = source.with_suffix('.csv')

        doc = extract_notebook_metatab(source)
        doc.ensure_identifier()
        doc.update_name(create_term=True)
        write_doc(doc, dest)

    else:
        err("Source file must be either .ipynb or .csv")
