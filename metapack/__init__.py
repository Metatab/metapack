# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE
"""
Record objects for the Simple Data Package format.
"""

from rowgenerators import get_generator, get_cache
from .exc import *
from .doc import MetapackDoc, Resolver
from .package import open_package, Downloader
from .appurl import MetapackUrl, MetapackDocumentUrl, MetapackResourceUrl, MetapackPackageUrl
from .terms import Resource


from metapack.jupyter.magic import load_ipython_extension, unload_ipython_extension

import rowgenerators.appurl.url

rowgenerators.appurl.url.default_downloader = Downloader(get_cache('metapack'))
