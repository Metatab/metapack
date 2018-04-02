# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Metapack CLI program for creating new metapack package directories
"""

from metapack.package import *

from .core import MetapackCliMemo as _MetapackCliMemo

downloader = Downloader()


class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)

def new_args(subparsers):

    parser = subparsers.add_parser(
        'new',
        help='Create new Metatab packages'
    )

    parser.set_defaults(run_command=new_cmd)

    parser.add_argument('-o', '--origin', help="Dataset origin, usually a second-level domain name")
    parser.add_argument('-d', '--dataset', help="Main dataset name", required = True)
    parser.add_argument('-t', '--time', help="Temporal extents")
    parser.add_argument('-s', '--space', help="Space, geographic extent")
    parser.add_argument('-g', '--grain', help="Grain, the type of entity a row represents")
    parser.add_argument('-v', '--variant', help="Variant, any distinguishing string")
    parser.add_argument('-r', '--revision', help="Version, defaults to 1", default=1)

    parser.add_argument('-T', '--template', help="Metatab file template, defaults to 'metatab' ", default='metatab')
    parser.add_argument('-C', '--config', help="Path to config file. Defaults to ~/.metapack-defaults.csv or value of METAPACK_DEFAULTS env var")

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

    nv_name = doc.as_version(None)

    if exists(nv_name):
        err(f"Directory {nv_name} already exists")

    ensure_dir(nv_name)

    prt(f"Writing to '{nv_name}'")

    write_doc(doc, join(nv_name, DEFAULT_METATAB_FILE))

    with open(join(nv_name,'.gitignore'), 'w') as f:
        f.write("_packages\n")


