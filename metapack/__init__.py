# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE
"""
Record objects for the Simple Data Package format.
"""

from rowgenerators import get_cache
from .exc import *
from .doc import MetapackDoc, Resolver
from .package import open_package, Downloader
from .appurl import MetapackUrl, MetapackDocumentUrl, MetapackResourceUrl, MetapackPackageUrl
from .terms import Resource

#from metapack.jupyter.magic import load_ipython_extension, unload_ipython_extension

from rowgenerators import set_default_cache_name


from pkg_resources import get_distribution, DistributionNotFound

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound

set_default_cache_name('metapack')

import rowgenerators.appurl.url

rowgenerators.appurl.url.default_downloader = Downloader.get_instance()
