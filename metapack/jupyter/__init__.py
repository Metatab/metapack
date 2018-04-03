# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Support for IPython and Python kernels in Jupyter Notebooks"""


from .metapack import MetapackExporter
from .exporters import HugoExporter
from .ipython import open_package, open_source_package

def init():
    """Initialize features that are normally initialized in the CLI"""

    from metapack.appurl import SearchUrl
    import metapack as mp
    from os import environ

    SearchUrl.initialize()  # This makes the 'index:" urls work
    mp.Downloader.context.update(environ)  # Allows resolution of environmental variables in urls