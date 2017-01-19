# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Class for reading Metapack packages"""

from .util import get_cache
from six import string_types

class Package(object):

    def __init__(self, ref, cache=None):

        self._cache = get_cache(cache) if isinstance(cache, string_types) else cache
        self._ref = ref

    def _open(self):
        """Open the package, possibly downloading it to the cache."""
        if not self._cache:
            raise IOError("Package must have a cache, set either in the package constructor, or with the METAPACK_CACHE env var")


    @property
    def doc(self):
        """Return the Metatab metadata document"""
        pass

    def resource(self, ref):
        """Return a resource, as a file-like-object, given it's name or url as a reference. """
        pass

    def schema(self, ref):
        """Return information about a resource, given a name or url"""
        pass

class Resource(object):
    """A package resource, which may be constructed from a URL that also references the package, or
    with a package handle and a reference to the resource in that package"""

    def __init__(self, ref, package=None):

        if package:
            pass
        else:
            pass

class ZipPackage(object):
    """A Zip File package"""

class ExcelPackage(object):
    """An Excel File Package"""

class FileSystemPackage(object):
    """A File System package"""

class SocrataPackage(object):
    """"""

class CkanPackage(object):
    """"""
