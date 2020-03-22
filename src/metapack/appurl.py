# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from os.path import basename, dirname, join

from metatab import DEFAULT_METATAB_FILE, LINES_METATAB_FILE
from rowgenerators import Url, parse_app_url
from rowgenerators.appurl.file.file import FileUrl
from rowgenerators.appurl.util import file_ext
from rowgenerators.appurl.web.web import WebUrl
from rowgenerators.exceptions import AppUrlError, DownloadError

from metapack.exc import MetapackError, ResourceError

METATAB_FILES = (DEFAULT_METATAB_FILE, LINES_METATAB_FILE, DEFAULT_METATAB_FILE.replace('.csv', '.ipynb'))

SIMPLE_FILE_FORMATS = ('csv', 'txt', 'ipynb')


class _MetapackUrl(object):

    def exists(self):

        if self.inner.proto == 'file':
            return self.inner.exists()
        else:
            # Hack, really ought to implement exists() for web urls.
            return True

    @property
    def resource_name(self):
        return self._parts['target_file']  # Must be underlying property

    def absolute(self):
        return self.inner.absolute()


def is_metapack_url(u):
    return isinstance(u, _MetapackUrl)


class MetapackDocumentUrl(Url, _MetapackUrl):

    def __init__(self, url=None, downloader=None, **kwargs):

        assert downloader

        super().__init__(url, downloader=downloader, **kwargs)

        self.scheme_extension = 'metapack'

        self._set_target_file()

    @classmethod
    def _match(cls, url, **kwargs):
        raise MetapackError("This class should not be constructed through matching")

    def _set_target_file(self):

        if self.resource_file in METATAB_FILES:
            return  # self.resource_file

        elif self.resource_format in SIMPLE_FILE_FORMATS:
            return  # self.resource_file

        elif self.resource_format == 'xlsx':
            self.target_file = 'meta'
            return

        elif self.resource_format == 'zip':
            self.target_file = DEFAULT_METATAB_FILE
            return

        elif file_ext(self.resource_file) not in SIMPLE_FILE_FORMATS:
            self.path = join(self.path, DEFAULT_METATAB_FILE)

        else:
            return self.resource_file

    @property
    def doc(self):
        """Return the metatab document for the URL"""
        from metapack import MetapackDoc
        t = self.get_resource().get_target()
        return MetapackDoc(t, package_url=self.package_url)

    @property
    def generator(self):

        from rowgenerators import get_generator

        # HACK! This used to be:
        # t = self.get_resource().get_target().inner
        # I don't know why, but stripping off the proto is problematic
        # for other cases.

        t = self.get_resource().get_target()

        return get_generator(t)

    def resolve_url(self, resource_name):
        """Return a URL to a local copy of a resource, suitable for get_generator()"""

        if self.target_format == 'csv' and self.target_file != DEFAULT_METATAB_FILE:
            # For CSV packages, need to get the package and open it to get the resoruce URL, becuase
            # they are always absolute web URLs and may not be related to the location of the metadata.
            s = self.get_resource()
            rs = s.doc.resource(resource_name)
            return parse_app_url(rs.url)
        else:
            jt = self.join_target(resource_name)
            rs = jt.get_resource()
            t = rs.get_target()
        return t

    @property
    def metadata_url(self):

        if not basename(self.resource_url):
            return self.clone(path=join(self.path, DEFAULT_METATAB_FILE))
        else:
            return self.clone()

    @property
    def package_url(self):
        """Return the package URL associated with this metadata"""

        if self.resource_file == DEFAULT_METATAB_FILE or self.target_format in ('txt', 'ipynb'):
            u = self.inner.clone().clear_fragment()
            u.path = dirname(self.path) + '/'

        else:
            u = self.clear_fragment()

        return MetapackPackageUrl(str(u), downloader=self._downloader)

    def get_resource(self):

        if self.scheme == 'file':
            u = self
        else:
            u = WebUrl(str(self), downloader=self._downloader).get_resource()

        return MetapackDocumentUrl(str(u), downloader=self._downloader)

    def get_target(self):
        u = self.inner.get_target().clone(scheme_extension=self.proto)
        u.scheme_extension = self.scheme_extension
        return parse_app_url(str(u), downloader=self._downloader)

    def join_target(self, tf):

        if self.target_file in METATAB_FILES:
            return self.inner.join_dir(tf)
        else:
            return self.inner.join_target(tf)

    @property
    def resource(self):
        """Return the Metapack resource, different from the URL resource returned by get_resource"""

        r = self.doc.resource(self.resource_name)
        return r


class MetapackPackageUrl(FileUrl, _MetapackUrl):
    """Special version of MetapackUrl for package urls, which never have a fragment"""

    def __init__(self, url=None, downloader=None, **kwargs):

        kwargs['scheme_extension'] = 'metapack'

        super().__init__(url, downloader=downloader, **kwargs)

        assert self._downloader

    @property
    def package_url(self):
        return self

    @property
    def metadata_url(self):

        return MetapackDocumentUrl(str(self.clone().clear_fragment()), downloader=self._downloader).metadata_url

    @property
    def doc(self):
        """Return the metatab document for the URL"""
        return self.metadata_url.doc

    def join_resource_name(self, v):
        """Return a MetapackResourceUrl that includes a reference to the resource. Returns a
        MetapackResourceUrl, which will have a fragment """
        d = self.dict
        self.target_file = v
        return MetapackResourceUrl(downloader=self._downloader, **d)

    def join_resource_path(self, v):
        """Return a regular AppUrl that combines the package with a URL path """
        return self.inner.join(v)

    def join_target(self, tf):
        """Like join(), but returns the inner URL, not a package url class"""
        if self.target_file in METATAB_FILES:
            return self.inner.join_dir(tf)
        else:
            return self.inner.join_target(tf)

    def resolve_url(self, resource_name):
        """Return a URL to a local copy of a resource, suitable for get_generator()

        For Package URLS, resolution involves generating a URL to a data file from the package URL and the
        value of a resource. The resource value, the url, can be one of:

        - An absolute URL, with a web scheme
        - A relative URL, relative to the package, with a file scheme.

        URLs with non-file schemes are returned. File scheme are assumed to be relative to the package,
        and are resolved according to the type of resource.

        """

        u = parse_app_url(resource_name)

        if u.scheme != 'file':
            t = u

        elif self.target_format == 'csv' and self.target_file != DEFAULT_METATAB_FILE:
            # Thre are two forms for CSV package URLS:
            # - A CSV package, which can only have absolute URLs
            # - A Filesystem package, which can have relative URLs.

            # The complication is that the filsystem package usually has a metadata file named
            # DEFAULT_METATAB_FILE, which can distinguish it from a CSV package, but it's also possible
            # to have a filesystem package with a non standard package name.

            # So, this clause can happed for two cases: A CSV package or a Filesystem package with a nonstandard
            # metadata file name.

            # For CSV packages, need to get the package and open it to get the resource URL, because
            # they are always absolute web URLs and may not be related to the location of the metadata.

            s = self.get_resource()
            rs = s.metadata_url.doc.resource(resource_name)
            if rs is not None:
                t = parse_app_url(rs.url)
            else:
                raise ResourceError("No resource for '{}' in '{}' ".format(resource_name, self))

        else:
            jt = self.join_target(resource_name)

            try:
                rs = jt.get_resource()
            except DownloadError:
                raise DownloadError(
                    "Failed to download resource for '{}' for '{}' in '{}'".format(jt, resource_name, self))
            t = rs.get_target()

        return t

    @property
    def inner(self):
        return super().inner


class MetapackResourceUrl(FileUrl, _MetapackUrl):
    def __init__(self, url=None, downloader=None, base_url=None, **kwargs):

        kwargs['proto'] = 'metapack'

        super().__init__(url, downloader=downloader, **kwargs)
        self.scheme_extension = 'metapack'

        # Expand the path in the same was as the document URL

        # Using .clone() causes recursion
        d = self.dict
        # Remove the resource
        d['target_file'] = None
        d['target_segment'] = None

        md = MetapackDocumentUrl(None, downloader=downloader, **d)
        self.path = md.path

        self.base_url = base_url

    @classmethod
    def _match(cls, url, **kwargs):
        raise MetapackError("This class should not be contructed through matching")

    @property
    def doc(self):
        """Return the metatab document for the URL"""
        return self.metadata_url.doc

    @property
    def metadata_url(self):
        assert self._downloader
        return MetapackDocumentUrl(str(self.clone().clear_fragment()), downloader=self._downloader).metadata_url

    @property
    def package_url(self):
        """Return the package URL associated with this metadata"""
        return MetapackDocumentUrl(str(self.clear_fragment()), downloader=self._downloader).package_url

    def get_resource(self):
        if self.scheme == 'file':
            return self
        else:
            u = WebUrl(str(self), downloader=self._downloader)
            r = u.get_resource()
            mru = MetapackResourceUrl(str(r), base_url=self, downloader=self._downloader)
            return mru

    def get_target(self):
        return self.resource.resolved_url.get_resource().get_target()

    @property
    def generator(self):
        # Use fragment b/c it could be target_file, for .zip, or target_segment, for .xlsx
        return self.resource

    @property
    def resource(self):

        r = self.doc.resource(self.resource_name)

        if not r:
            r = self.doc.reference(self.resource_name)

        return r


# Would have made this a function, but it needs to be a class to have the match() method
class MetapackUrl(Url):
    """Implements __new__ to return either a  MetapackResourceUrl or a MetapackDocumentUrl"""

    match_priority = WebUrl.match_priority - 1

    def __new__(cls, url=None, downloader=None, **kwargs):

        assert downloader

        u = Url(url, **kwargs)

        if u._parts['target_file']:  # must be underlying property, not .target_file
            return MetapackResourceUrl(url, downloader, **kwargs)
        else:
            return MetapackDocumentUrl(url, downloader, **kwargs)

    @classmethod
    def _match(cls, url, **kwargs):
        """Return True if this handler can handle the input URL"""
        return url.proto in ('metapack', 'metatab')


class SearchUrl(Url):
    """Look up a url using a list of callbacks. """

    match_priority = FileUrl.match_priority - 10

    search_callbacks = []

    _search_initialized = False

    def __init__(self, url=None, **kwargs):
        kwargs['scheme'] = 'index'
        super().__init__(url, **kwargs)

    @classmethod
    def _match(cls, url, **kwargs):
        return url.scheme == 'search' or url.scheme == 'index'

    @classmethod
    def register_search(cls, f):
        """Register a function that will lookup the search URL and return a URL if found"""

        cls.search_callbacks.append(f)

    @classmethod
    def initialize(cls):
        if SearchUrl._search_initialized is False:
            from metapack.package import Downloader  # Breaks inclusion cycle
            try:
                search_func = cls.search_json_indexed_directory(Downloader.get_instance().cache.getsyspath('/'))
                SearchUrl.register_search(search_func)
            except AppUrlError:
                pass

            SearchUrl._search_initialized = True

    @staticmethod
    def search_json_indexed_directory(directory):
        """Return a search function for searching a directory of packages, which has an index.json file
        created by the `mp install file` command.

        This will only search the issued index; it will not return results for the source index
        """

        from metapack.index import SearchIndex, search_index_file

        idx = SearchIndex(search_index_file())

        def _search_function(url):

            packages = idx.search(url, format='issued')

            if not packages:
                return None

            package = packages.pop(0)

            try:
                resource_str = '#' + url.resource_name if url.resource_name else ''

                return parse_app_url(package['url'] + resource_str, downloader=url.downloader)
            except KeyError:
                return None

        return _search_function

    def search(self):
        """Search for a url by returning the value from the first callback that
        returns a non-None value"""

        for cb in SearchUrl.search_callbacks:

            try:
                v = cb(self)
                if v is not None:
                    return v
            except Exception:
                raise

    def resolve(self):
        u = self.search()

        if not u:
            raise AppUrlError("Search URL failed to resolve reference to {} ".format(str(self)))

        # u.set_fragment(self.fragment)

        return u

    def get_resource(self):

        return self.resolve().get_resource()

    def get_target(self):
        return self

    @property
    def resource_name(self):
        """Name of a Metatab resource ( not the URL resource ) which is specified in the fragment"""

        return self._parts.get('target_file')
