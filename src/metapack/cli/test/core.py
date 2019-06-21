# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Tests for the CLI
"""

import argparse
# from https://stackoverflow.com/a/10743550
import contextlib
import sys
from pkg_resources import (
    DistributionNotFound,
    get_distribution,
    iter_entry_points
)
from shlex import split

from metapack.cli.core import err, prt


@contextlib.contextmanager
def capture():
    import sys
    from io import StringIO
    oldout,olderr = sys.stdout, sys.stderr
    try:
        out=[StringIO(), StringIO()]
        sys.stdout,sys.stderr = out
        yield out
    finally:
        sys.stdout,sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()

def exec_cmd(args):
    """"Execute a CLI command, through the backdoor"""

    parser = argparse.ArgumentParser(
        prog='mp',
        description='Create and manipulate metatab data packages. ')

    subparsers = parser.add_subparsers(help='Commands')

    for ep in iter_entry_points(group='mt.subcommands'):
        f = ep.load()
        f(subparsers)

    if isinstance(args, str):
        args = split(args)

    args = parser.parse_args(args)

    try:
        with capture() as c:
            args.run_command(args)
        exc = None
    except Exception as e:
        exc = e
    except SystemExit as e:
        exc = e


    return c+[exc]


def delete_contents(directory):
    import os
    import glob
    import shutil

    files = glob.glob(directory+'/*')

    for f in files:
        shutil.rmtree(f)
