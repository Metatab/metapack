# Copyright (c) 2019 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE


"""Support for IPython and Python kernels in Jupyter Notebooks"""

from os import getcwd
from os.path import exists, join

from metatab import (
    DEFAULT_METATAB_FILE,
    IPYNB_METATAB_FILE,
    LINES_METATAB_FILE
)
from rowgenerators.exceptions import RowGeneratorError

from metapack import open_package as op
from metapack.constants import PACKAGE_PREFIX
from metapack.exc import PackageError
from metapack.util import walk_up


def init():
    """Initialize features that are normally initialized in the CLI"""

    from metapack.appurl import SearchUrl
    import metapack as mp
    from os import environ

    SearchUrl.initialize()  # This makes the 'index:" urls work
    mp.Downloader.context.update(environ)  # Allows resolution of environmental variables in urls


def in_build():
    """Return True if running in a build, rather than interactively in Jupyter"""
    return 'metatab_doc' in caller_locals()


def open_package(locals=None, dr=None):
    """Try to open a package with the metatab_doc variable, which is set when a Notebook is run
    as a resource. If that does not exist, try the local _packages directory"""

    if locals is None:
        locals = caller_locals()

    try:
        # Running in a package build
        return op(locals['metatab_doc'])

    except KeyError:
        # Running interactively in Jupyter

        package_name = None
        build_package_dir = None
        source_package = None

        if dr is None:
            dr = getcwd()

        unbilt_mtfiles = []

        for i, e in enumerate(walk_up(dr)):

            intr = set([DEFAULT_METATAB_FILE, LINES_METATAB_FILE, IPYNB_METATAB_FILE]) & set(e[2])

            if intr:

                source_package = join(e[0], list(intr)[0])
                p = op(source_package)
                package_name = p.find_first_value("Root.Name")

                if not package_name:
                    raise PackageError("Source package in {} does not have root.Name term".format(e[0]))

                if PACKAGE_PREFIX in e[1]:
                    build_package_dir = join(e[0], PACKAGE_PREFIX)
                else:
                    unbilt_mtfiles.append(intr)

                break

            if i > 2:
                break

        if build_package_dir and package_name and exists(join(build_package_dir, package_name)):
            # Open the previously built package
            built_package = join(build_package_dir, package_name)
            try:
                return op(built_package)
            except RowGeneratorError:
                pass  # Probably could not open the metadata file.

        # if source_package:
        #    # Open the source package
        #    return op(source_package)

    if unbilt_mtfiles:
        raise PackageError(
            f"Found a metatab package, but did not find a built package in {PACKAGE_PREFIX}. Has package been built?")
    else:
        raise PackageError("Failed to find package, either in locals() or above dir '{}' ".format(dr))


def open_source_package(dr=None):
    """Like open_package(), but always open the source package"""
    if dr is None:
        dr = getcwd()

    for i, e in enumerate(walk_up(dr)):

        intr = set([DEFAULT_METATAB_FILE, LINES_METATAB_FILE, IPYNB_METATAB_FILE]) & set(e[2])

        if intr:
            return op(join(e[0], list(intr)[0]))

        if i > 2:
            break

    return None


def caller_locals():
    """Get the local variables in the caller's frame."""
    import inspect
    frame = inspect.currentframe()
    try:
        return frame.f_back.f_back.f_locals
    finally:
        del frame
