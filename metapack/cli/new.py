# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Metapack CLI program for creating new metapack package directories
"""

from metapack.package import *

from .core import MetapackCliMemo as _MetapackCliMemo
import argparse

downloader = Downloader()


class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)

def new_args(subparsers):
    """
    The `mp new` command creates source package directories
    with a proper name, a `.gitignore` file, and optionally, example data,
    entries and code. Typical usage, for creating a new package with most
    of the example options, is ::
    
        mp new -o metatab.org -d tutorial -L -E -T "Quickstart Example Package" 
    
    The :option:`-C` option will set a configuration file, which is a
    Metatab file that with terms that are copied into the `metadata.csv` file
    of the new package. Currently, it copies a limited number of terms,
     including:
    
    - Terms in the Contacts section
    - Root.Space
    - Root.Time
    - Root.Grain
    - Root.Variant
    - Root.Version

    """
    parser = subparsers.add_parser(
        'new',
        help='Create new Metatab packages',
        description=new_args.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.set_defaults(run_command=new_cmd)

    parser.add_argument('-o', '--origin', help="Dataset origin, usually a second-level domain name. Required")
    parser.add_argument('-d', '--dataset', help="Main dataset name. Required", required = True)
    parser.add_argument('-t', '--time', help="Temporal extents, usually a year, ISO8601 time, or interval. ")
    parser.add_argument('-s', '--space', help="Space, geographic extent, such as a name of a state or a Census geoid")
    parser.add_argument('-g', '--grain', help="Grain, the type of entity a row represents")
    parser.add_argument('-v', '--variant', help="Variant, any distinguishing string")
    parser.add_argument('-r', '--revision', help="Version, defaults to 1", default=1)

    parser.add_argument('-T', '--title', help="Set the title")

    parser.add_argument('-L', '--pylib', help="Configure a pylib directory for Python code extensions", action='store_true')

    parser.add_argument('-E', '--example', help="Add examples of resources",
                        action='store_true')

    parser.add_argument('--template', help="Metatab file template, defaults to 'metatab' ", default='metatab')
    parser.add_argument('-C', '--config', help="Path to config file. "
                                               "Defaults to ~/.metapack-defaults.csv or value of METAPACK_DEFAULTS env var."
                                                "Sets defaults for specia root terms and the Contacts section.")


    return parser

def doc_parser():
    from .mp import base_parser

    return new_args(base_parser())

def new_cmd(args):

    from metapack import MetapackDoc
    from metapack.util import make_metatab_file, datetime_now, ensure_dir
    from metapack.cli.core import write_doc, prt, err
    from os.path import exists, join, expanduser
    from metatab import DEFAULT_METATAB_FILE
    from os import getenv

    if args.config:
        config_file = args.config
    elif getenv("METAPACK_CONFIG"):
        config_file = getenv("METAPACK_DEFAULTS")
    elif expanduser('~/.metapack-default.csv'):
        config_file = expanduser('~/.metapack-defaults.csv')
    else:
        config_file = None

    if config_file and exists(config_file):
        prt(f"Using defaults file '{config_file}'")
        config = MetapackDoc(config_file)
    else:
        config = MetapackDoc()

    doc = make_metatab_file(args.template)

    doc['Root']['Created'] = datetime_now()

    origin = args.origin or config.get_value('Root.Origin')

    if not origin:
        err("Must specify a value for origin, either on command line or in defaults file")

    doc['Root'].find_first('Root.Origin').value = origin
    doc['Root'].find_first('Root.Dataset').value = args.dataset
    doc['Root'].find_first('Root.Space').value = args.space or config.get_value('Root.Space')
    doc['Root'].find_first('Root.Time').value = args.time or config.get_value('Root.Time')
    doc['Root'].find_first('Root.Grain').value = args.grain or config.get_value('Root.Grain')
    doc['Root'].find_first('Root.Variant').value = args.variant or config.get_value('Root.Variant')
    doc['Root'].find_first('Root.Version').value = args.revision or config.get_value('Root.Version')

    # Copy contacts in
    if 'Contacts' in config:
        for c in config['Contacts']:
            doc['Contacts'].add_term(c)


    if args.title:
        doc['Root'].find_first('Root.Title').value = args.title.strip()

    nv_name = doc.as_version(None)

    if exists(nv_name):
        err(f"Directory {nv_name} already exists")

    ensure_dir(nv_name)

    doc['Documentation'].new_term('Root.IncludeDocumentation', 'file:README.md', title='README')

    if args.example:
        doc['Resources'].new_term('Root.Datafile',
                                  'http://public.source.civicknowledge.com/example.com/sources/random-names.csv',
                                  name='random_names')

        doc['Documentation'].new_term('Root.Homepage', 'http://metatab.org', title='Metatab Home Page')

    if args.pylib:
        from metapack.support import pylib
        pylib_dir = join(nv_name,'pylib')
        ensure_dir(pylib_dir)
        with open(join(pylib_dir, '__init__.py'), 'w') as f_out, open(pylib.__file__) as f_in:
            f_out.write(f_in.read())

        if args.example:
            doc['Resources'].new_term('Root.Datafile','python:pylib#row_generator', name='row_generator')

    prt(f"Writing to '{nv_name}'")

    write_doc(doc, join(nv_name, DEFAULT_METATAB_FILE))

    with open(join(nv_name,'.gitignore'), 'w') as f:
        f.write("_packages\n")

    if args.title:
        readme = '# {}\n'.format(args.title)
    else:
        readme = '# {}\n'.format(doc.get_value('Root.Name'))

    with open(join(nv_name,'README.md'), 'w') as f:
        f.write(readme)



