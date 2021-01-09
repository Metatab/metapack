# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE
"""
Record objects for the Simple Data Package format.
"""

from rowgenerators import get_cache # noqa: 401
from .exc import *  # noqa: 403
from .doc import MetapackDoc, Resolver  # noqa: 401
from .package import open_package,  multi_open, Downloader  # noqa: 401
from .appurl import MetapackUrl, MetapackDocumentUrl, MetapackResourceUrl, MetapackPackageUrl  # noqa: 401
from .terms import Resource  # noqa: 401
from metapack.appurl import is_metapack_url  # noqa: 401
import rowgenerators.appurl.url  # noqa: 401
from rowgenerators import set_default_cache_name  # noqa: 401
from pkg_resources import get_distribution, DistributionNotFound  # noqa: 401
import metapack.jupyter  # noqa: 401

# from metapack.jupyter.magic import load_ipython_extension, unload_ipython_extension


try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound

set_default_cache_name('metapack')

rowgenerators.appurl.url.default_downloader = Downloader.get_instance()
