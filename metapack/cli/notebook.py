# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

from metapack import Downloader
from metapack.cli.core import prt, err, warn, get_config
from os import environ
from os.path import basename
import re

downloader = Downloader.get_instance()


def notebook(subparsers):
    parser = subparsers.add_parser(
        'notebook',
        help='Convert Metatab-formatted Jupyter notebooks. ',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_notebook)

    parser.add_argument('notebook', nargs='?',
                        help="Path to a notebok file' ")

    parser.add_argument('-p', '--profile', help="Name of a BOTO or AWS credentails profile", required=False)


    parser.set_defaults(handler=None)

    ##
    ## Build Group

    build_group = parser.add_argument_group('Building Metatab Files', 'Build and manage a metatab file for a pacakge')

    build_group.add_argument('-m', '--metatab', default=False, action='store_true',
                             help='Extract the metatab file')

    build_group.add_argument('-l', '--lines', default=False, action='store_true',
                             help='When displaying a Metatab file, display as lines, not as CSV')

    build_group.add_argument('-P', '--package', default=False, action='store_true',
                             help='Build a package from a Jupyter notebook')

    build_group.add_argument('-D', '--documentation', default=False, action='store_true',
                             help='With -M, make only the documentation')

    build_group.add_argument('-H', '--hugo', default=False, nargs='?',
                             help='Write images and Markdown into a Hugo static site directory. or use '
                                  'METAPACK_HUGO_DIR env var')


def run_notebook(args):
    from metapack.jupyter.convert import convert_documentation, convert_notebook, convert_wordpress, \
        extract_metatab, convert_hugo

    # Maybe need to convert a notebook first
    if args.package:
        convert_notebook(args.notebook)

    elif args.documentation:
        convert_documentation(args.notebook)

    elif args.metatab:
        doc = extract_metatab(args.notebook)

        if args.lines:
            for line in doc.lines:
                print(": ".join(line))
        else:
            print(doc.as_csv())

    elif args.hugo:
        convert_hugo(args.notebook,args.hugo)

