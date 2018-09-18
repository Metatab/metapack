# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

from metapack import Downloader
from .s3 import metas3
from .metakan import metakan
from .install_file import  install_file
from .install_git import  install_git

downloader = Downloader.get_instance()

def install(subparsers):

    install_parser = subparsers.add_parser(
        'install',
        help='Install metatap packages',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    install_subparser = install_parser.add_subparsers(help='Install Commands')

    metas3(install_subparser)
    metakan(install_subparser)
    install_file(install_subparser)
    install_git(install_subparser)






