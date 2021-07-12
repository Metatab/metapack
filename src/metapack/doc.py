# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Extensions to the MetatabDoc, Resources and References, etc.
"""

from pathlib import Path

from metatab import MetatabDoc, WebResolver
from metatab.util import slugify
from rowgenerators import Source, parse_app_url
from rowgenerators.exceptions import RowGeneratorError

from metapack.appurl import MetapackDocumentUrl
from metapack.exc import MetatabFileNotFound
from metapack.package import Downloader
from metapack.util import datetime_now

EMPTY_SOURCE_HEADER = '_NONE_'  # Marker for a column that is in the destination table but not in the source


class Resolver(WebResolver):
    def get_row_generator(self, ref, cache=None):

        try:
            return ref.metadata_url.generator
        except AttributeError:
            return super().get_row_generator(ref, cache)


class MetapackDoc(MetatabDoc):
    lib_dir_names = ('lib', 'pylib')  # Names of subdirs to look for to find a loadable module

    def __init__(self, ref=None, decl=None, cache=None, resolver=None, package_url=None, clean_cache=False,
                 downloader=None):

        if downloader:
            self.downloader = downloader
        elif cache:
            self.downloader = Downloader.get_instance(cache)
        else:
            self.downloader = Downloader.get_instance()

        cache = self.downloader.cache

        if not isinstance(ref, (MetapackDocumentUrl)) and not isinstance(ref, Source) and ref is not None:
            ref = MetapackDocumentUrl(str(ref), downloader=self.downloader)

        self.register_term_class('root.resource', 'metapack.terms.Resource')
        self.register_term_class('root.reference', 'metapack.terms.Reference')
        self.register_term_class('root.distribution', 'metapack.terms.Distribution')
        self.register_term_class('root.sql', 'metapack.terms.SqlQuery')

        resolver = resolver or Resolver()

        assert resolver is not None

        if package_url is None:
            try:
                package_url = ref.package_url
            except AttributeError:
                # For iterators, generators
                package_url = None

        try:

            super().__init__(ref, decl, package_url, cache, resolver, clean_cache)
        except RowGeneratorError:
            raise MetatabFileNotFound("Failed to get Metatabfile for reference: '{}' ".format(ref))

        self.default_resource = None  # Set externally in open_package when the URL has a resource.

    def __enter__(self):
        """Context Management entry. Does nothing"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context management exit. Writes the document as a CSV file"""

        if not exc_type:
            self.write_csv()

    @property
    def path(self):
        """Return the path to the file, if the ref is a file"""

        if self.ref.inner.proto != 'file':
            return None

        return self.ref.path

    @property
    def name(self):
        """Return the name from the metatab document, or the identity, and as a last resort,
        the slugified file reference"""
        return self.get_value('root.name', self.get_value('root.identifier', slugify(self._ref)))

    @property
    def nonver_name(self):
        """Return the non versioned name"""
        nv = self.as_version(None)
        if not nv:
            import re
            nv = re.sub(r'-[^-]+$', '', self.name)

        return nv

    @property
    def version(self):
        return self.get_value('Root.Version')

    @property
    def identifier(self):

        # Maybe there are multiple values
        t = None
        for t in self['Root'].find('root.identifier'):
            pass

        if t:
            return t.value

        return None

    def wrappable_term(self, term):
        """Return the Root.Description, possibly combining multiple terms.
        :return:
        """

        return ' '.join(e.value.strip() for e in self['Root'].find(term) if e and e.value)

    def set_wrappable_term(self, v, term):
        """Set the Root.Description, possibly splitting long descriptions across multiple terms. """

        import textwrap

        for t in self['Root'].find(term):
            self.remove_term(t)

        for line in textwrap.wrap(v, 80):
            self['Root'].new_term(term, line)

    @property
    def description(self):
        return self.wrappable_term('Root.Description')

    @description.setter
    def description(self, v):
        return self.set_wrappable_term(v, 'Root.Description')

    @property
    def abstract(self):
        return self.wrappable_term('Root.Abstract')

    @abstract.setter
    def abstract(self, v):
        return self.set_wrappable_term(v, 'Root.Abstract')

    @property
    def env(self):
        """Return the module associated with a package's python library"""
        import importlib

        try:
            r = self.get_lib_module_dict()
        except ImportError:
            r = {}

        m = importlib.import_module('metapack.env')

        for f in m.__all__:
            r[f.__name__] = f

        return r

    def set_sys_path(self):
        from os.path import join, isdir, dirname, abspath
        import sys

        if not self.ref:
            return False

        u = parse_app_url(self.ref)
        doc_dir = dirname(abspath(u.path))
        # Add the dir with the metatab file to the system path

        for lib_dir_name in self.lib_dir_names:
            if isdir(join(doc_dir, lib_dir_name)):
                if 'docdir' not in sys.path:
                    sys.path.insert(0, doc_dir)
                return True

        return False

    def get_lib_module_dict(self):
        """Load the 'lib' directory as a python module, so it can be used to provide functions
        for rowpipe transforms. This only works filesystem packages"""

        from importlib import import_module

        if not self.ref:
            return {}

        u = parse_app_url(self.ref)

        if u.scheme == 'file':

            if not self.set_sys_path():
                return {}

            for module_name in self.lib_dir_names:

                try:
                    m = import_module(module_name)
                    d = {k: v for k, v in m.__dict__.items() if not k.startswith('__')}
                    return d

                except ModuleNotFoundError as e:

                    # We need to know if it is the datapackage's module that is missing
                    # or if it is a module that it imported
                    if module_name not in str(e):
                        raise  # If not our module, it's a real error.

                    continue
        else:
            return {}

        assert False, "Should not get here. No idea why we did. Maybe errors in pylib/__init__.py?"

    def resources(self, term='Root.Resource', section='Resources'):
        return self.find(term=term, section=section)

    def resource(self, name=None, term='Root.Resource', section='Resources'):

        if name is None and self.default_resource is not None:
            name = self.default_resource

        return self.find_first(term=term, name=name, section=section)

    def references(self, term='Root.*', section='References'):
        return self.find(term=term, section=section)

    def reference(self, name=None, term='Root.Reference', section='References'):
        return self.find_first(term=term, name=name, section=section)

    def _repr_html_(self, **kwargs):
        """Produce HTML for Jupyter Notebook"""
        from markdown import markdown as convert_markdown

        extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.admonition'
        ]

        return convert_markdown(self.markdown, extensions=extensions)

    def _repr_pretty_(self, p, cycle):
        p.text(self.markdown)

    def __str__(self):
        return self.markdown

    @property
    def html(self):
        from .html import html
        return html(self)

    @property
    def markdown(self):
        from .html import markdown

        return markdown(self)

    def sort_by_term(self):
        self['Root'].sort_by_term(order=[
            'Root.Declare',
            'Root.Title',
            'Root.Description',
            'Root.Identifier',
            'Root.Name',
            'Root.Dataset',
            'Root.Origin',
            'Root.Time',
            'Root.Space',
            'Root.Grain',
            'Root.Variant',
            'Root.Version',
            'Root.Group',
            'Root.Tag',
            'Root.Keyword',
            'Root.Subject',
            'Root.Created',
            'Root.Modified',
            'Root.Issued',
            'Root.Updatefrequency',
            'Root.Access',
            'Root.Distribution'
        ])

    def write_csv(self, path=None):
        """Write CSV file. Sorts the sections before calling the superclass write_csv"""

        # Sort the Sections

        self.sort_sections(['Root', 'Contacts', 'Documentation', 'References', 'Resources', 'Citations', 'Schema'])

        # Sort Terms in the root section

        # Re-wrap the description and abstract
        if self.description:
            self.description = self.description

        if self.abstract:
            self.description = self.abstract

        t = self['Root'].get_or_new_term('Root.Modified')
        t.value = datetime_now()

        self.sort_by_term()

        return super().write_csv(str(path))

    def write_ipynb(self, path: Path = None):
        from metapack_jupyter.convert import write_metatab_notebook

        write_metatab_notebook(self, path)

    def write(self, path=None):
        from metatab.exc import FormatError

        path = self._write_path(path)

        if path.suffix == '.txt':
            self.write_lines(path)
        elif path.suffix == '.csv':
            self.write_csv(path)
        elif path.suffix == '.ipynb':
            self.write_ipynb(path)
        else:
            raise FormatError("Can't write to filetype of {}".format(path.suffix))
