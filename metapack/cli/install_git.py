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
from metapack.util import ensure_dir, slugify

from .core import MetapackCliMemo as _MetapackCliMemo
from .core import prt, err
import json
from .install_file import update_index

downloader = Downloader.get_instance()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)

def install_git(subparsers):

    parser = subparsers.add_parser(
        'git',
        help='Install git repos as source directories'
    )

    parser.set_defaults(run_command=run_git_install)

    if getenv('METAPACK_DATA'):
       d_args = '?'
       defaults_to=f"Defaults to METAPACK_DATA env var, '{getenv('METAPACK_DATA')}'"
    else:
        d_args = 1
        defaults_to = 'May also be set with the METAPACK_DATA env var'

    parser.add_argument('-d', '--directory', nargs=d_args, default=getenv('METAPACK_DATA'),
                        help='Directory to which to install files. '+defaults_to)

    parser.add_argument('giturl', nargs=1, help='URL to a git repo')


def run_git_install(args):
    try:
        from git import RemoteProgress, Repo, GitCommandError, InvalidGitRepositoryError
    except ImportError:
        err("This command requires the git python module. Run 'pip install gitpython'")

    class MyProgressPrinter(RemoteProgress):
        def update(self, op_code, cur_count, max_count=None, message=''):
            print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")

    if isinstance(args.giturl, list):
        giturl = args.giturl[0]
    else:
        giturl = args.giturl

    target = join(args.directory, 'source', slugify(giturl))

    ensure_dir(target)

    try:
        repo = Repo(target)
        repo.remotes.origin.pull()
        prt(f"Pulling to existing repo, '{target} ")
    except InvalidGitRepositoryError:
        repo = Repo.clone_from(giturl, target)
        prt(f"Cloning to new repo, '{target} ")

    update_index(args.directory, target, suffix='source')

