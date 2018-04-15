# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """

from os.path import join, dirname, exists, abspath, islink
from os import unlink, symlink
from metapack import PackageError
from metapack.util import datetime_now
from metapack.package.core import PackageBuilder
from rowgenerators import parse_app_url


class CsvPackageBuilder(PackageBuilder):
    """"""

    type_code = 'csv'
    type_suffix = '.csv'

    def __init__(self, source_ref=None, package_root=None,  resource_root=None, callback=None, env=None):

        super().__init__(source_ref, package_root,  callback, env)
        from metapack import MetapackPackageUrl

        self.package_path, self.cache_path = self.make_package_path(self.package_root, self.package_name)

        if self.package_root.proto == 'file':
            self.package_root.ensure_dir()

        if resource_root is not None:
            self.resource_root = resource_root
        else:
            self.resource_root = source_ref.dirname().as_type(MetapackPackageUrl)

        assert isinstance(self.resource_root, MetapackPackageUrl), (type(self.resource_root), self.resource_root)

        self._last_write_path = None

    @classmethod
    def make_package_path(cls, package_root, package_name):

        # self.package_path, self.cache_path = self.make_package_path(self.package_name, self.package_root)

        cache_path = package_name + cls.type_suffix

        package_path = package_root.join(cache_path)

        return package_path, cache_path


    def _load_resource(self, source_r, abs_path=False):
        """The CSV package has no reseources, so we just need to resolve the URLs to them. Usually, the
            CSV package is built from a file system ackage on a publically acessible server. """

        r = self.doc.resource(source_r.name)

        r.url = self.resource_root.join(r.url).inner #r.resolved_url


    def _relink_documentation(self):

        for doc in self.doc['Documentation'].find(['Root.Documentation', 'Root.Image']):
            doc.url =  doc.resolved_url

    def save(self, path=None):
        from metapack import MetapackPackageUrl

        # HACK ...
        if not self.doc.ref:
            self.doc._ref = self.package_path  # Really should not do this but ...

        self.check_is_ready()

        self.load_declares()

        self.doc.cleanse()

        self._load_resources()

        self._relink_documentation()

        self._clean_doc()

        if path is None:
            if self.package_path.inner.proto == 'file':
                path = self.package_path.path
            else:
                raise PackageError("Can't write doc to path: '{}'".format(path))

        self.doc['Root'].get_or_new_term('Root.Issued').value = datetime_now()

        self._last_write_path = path

        self.doc.write_csv(path)

        return parse_app_url(abspath(path)).as_type(MetapackPackageUrl)


