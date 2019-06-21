# Copyright (c) 2019 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """

from rowgenerators import Downloader as _Downloader
from rowgenerators import parse_app_url

from metapack.appurl import MetapackUrl

DEFAULT_CACHE_NAME = 'metapack'


class Downloader(_Downloader):
    """"Local version of the downloader. Also should be used as the source of the cache"""

    ok = True

    def __init__(self, cache=None, account_accessor=None, logger=None, working_dir='', callback=None):
        from rowgenerators import get_cache
        super().__init__(cache or get_cache('metapack'),
                         account_accessor, logger, working_dir, callback)

    def download(self, url):
        return super().download(url)


def open_package(ref, downloader=None):
    from metapack.doc import MetapackDoc

    if downloader is None:
        downloader = Downloader()

    if isinstance(ref, MetapackUrl):
        p = MetapackDoc(ref, downloader=downloader)
        p.default_resource = None
        return p

    else:

        ref = str(ref)

        if ref.startswith('index:'):
            from metapack.appurl import SearchUrl
            SearchUrl.initialize()
            ref = str(parse_app_url(ref).resolve())

        u = MetapackUrl(ref, downloader=downloader)

        p = MetapackDoc(u, downloader=downloader)
        p.default_resource = u.resource_name
        return p
