# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Extensions to the MetatabDoc, Resources and References, etc.
"""

EMPTY_SOURCE_HEADER = '_NONE_'  # Marker for a column that is in the destination table but not in the source

from metatab import MetatabDoc, WebResolver

from metapack.appurl import MetapackDocumentUrl, MetapackResourceUrl, MetapackUrl
from .html import linkify
from .util import slugify
from metapack.package.core import Downloader
from rowgenerators import Source, parse_app_url
from rowgenerators.exceptions import RowGeneratorError, AppUrlError
from metapack.util import datetime_now
from metapack.exc import MetatabFileNotFound

class Resolver(WebResolver):
    def get_row_generator(self, ref, cache=None):

        try:
            return ref.metadata_url.generator
        except AttributeError:
            return super().get_row_generator(ref, cache)

class MetapackDoc(MetatabDoc):

    lib_dir_names = ('lib', 'pylib') # Names of subdirs to look for to find a loadable module

    def __init__(self, ref=None, decl=None,  cache=None, resolver=None, package_url=None, clean_cache=False,
                 downloader=None):

        #assert isinstance(ref, (MetapackDocumentUrl, MetapackResourceUrl)), (type(ref), ref)

        if downloader:
            self.downloader = downloader
        elif cache:
            self.downloader = Downloader(cache)
        else:
            self.downloader = Downloader()

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
        except RowGeneratorError as e:
            raise MetatabFileNotFound("Failed to get Metatabfile for reference: '{}' ".format(ref))


        self.default_resource = None # Set externally in open_package when the URL has a resource.

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
        return self.get_value('root.name', self.get_value('root.identifier',slugify(self._ref)))

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

        return ' '.join( e.value.strip() for e in self['Root'].find(term) if e and e.value)


    def set_wrappable_term(self, v, term):
        """Set the Root.Description, possibly splitting long descriptions across multiple terms. """

        import textwrap

        for t in self['Root'].find(term):
            self.remove_term(t)

        for l in textwrap.wrap(v, 80):
            self['Root'].new_term(term, l)

    @property
    def description(self):
        return self.wrappable_term('Root.Description')

    @description.setter
    def description(self, v):
        return self.set_wrappable_term(v, 'Root.Description')

    @property
    def abstract(self):
        return self.wrappable_term('Root.Abstract')

    @description.setter
    def abstract(self, v):
        return self.set_wrappable_term(v, 'Root.Abstract')

    @property
    def env(self):
        """Return the module associated with a package's python library"""

        try:

            return self.get_lib_module_dict()
        except ImportError:
            return {}

    def set_sys_path(self):
        from os.path import join, isdir, dirname, abspath
        import sys

        if not self.ref:
            return False

        u = parse_app_url(self.ref)
        doc_dir = dirname(abspath(u.path))
        # Add the dir with the metatab file to the system path

        for lib_dir_name in  self.lib_dir_names:
            if isdir(join(doc_dir, lib_dir_name)):
                if not 'docdir' in sys.path:
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
                    return {k: v for k, v in m.__dict__.items() if not k.startswith('__')}
                except ImportError as e:
                    continue

                raise ImportError(f"Failed to import python module from lib directory; tried: {lib_dir_names}; ", str(e))

        else:
            return {}

    def resources(self, term='Root.Resource', section='Resources'):
        return self.find(term=term, section=section)

    def resource(self, name=None, term='Root.Resource', section='Resources'):
        return self.find_first(term=term, name=name, section=section)

    def references(self, term='Root.*', section='References'):
        return self.find(term=term, section=section)

    def reference(self, name=None, term='Root.Reference', section='References'):
        return self.find_first(term=term, name=name, section=section)

    def _repr_html_(self, **kwargs):
        """Produce HTML for Jupyter Notebook"""
        from jinja2 import Template
        from markdown import markdown as convert_markdown

        extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.admonition'
        ]

        def resource_repr(r, anchor=kwargs.get('anchors', False)):

            try:
                resolved_url = r.resolved_url if hasattr(r, 'resolved_url') else r.value
            except AppUrlError:
                resolved_url = r.value

            return "<p><strong>{name}</strong> - <a target=\"_blank\" href=\"{url}\">{url}</a> {description}</p>" \
                .format(name='<a href="#resource-{name}">{name}</a>'.format(name=r.name) if anchor else r.name,
                        description=r.get_value('description', ''),
                        url=resolved_url)

        def documentation():

            out = ''

            try:
                self['Documentation']
            except KeyError:
                return ''

            try:
                for t in self['Documentation'].find('Root.Documentation'):
                    if t.get_value('url'):
                        out += ("\n**{} **{}"
                                .format(linkify(t.get_value('url'), t.get_value('title')),
                                        t.get_value('description')
                                        ))

                    else:  # Mostly for notes
                        out += ("\n**{}: **{}"
                                .format(t.record_term.title(), t.value))


            except KeyError:
                raise
                pass

            return out

        def contacts():

            out = ''

            try:
                self['Contacts']
            except KeyError:
                return ''

            try:

                for t in self['Contacts']:
                    name = t.get_value('name', 'Name')
                    email = "mailto:" + t.get_value('email') if t.get_value('email') else None

                    web = t.get_value('url')
                    org = t.get_value('organization', web)

                    out += ("\n**{}:** {}"
                            .format(t.record_term.title(),
                                    (linkify(email, name) or '') + " " + (linkify(web, org) or '')
                                    ))

            except KeyError:
                pass

            return out

        t = Template("""
## {{title|default(name, True) }}
{% if title %}
<p>{{name|default("", True)}}</p>
{% endif %}
<p>{{description|default("", True) }}</p>
<p>{{ref|default("", True)}}</p>
{% if doc %}
### Documentation
{{doc}}
{% endif %}
### Contacts
{{contact}}
{% if resources %}
### Resources
<ol>
{{resources}}
</ol>
{% endif%}
{% if references %}
### References
<ol>
{{references}}
{% endif %}
</ol>""")

        try:
            resources = '\n'.join(
                ["<li>" + resource_repr(r) + "</li>" for r in self['Resources'].find('Root.Resource')])
        except KeyError as e:
            resources = None

        try:
            references = '\n'.join(
                ["<li>" + resource_repr(r) + "</li>" for r in self['References'].find('Root.Resource')])
        except KeyError as e:
            references = None

        v = t.render(
            title=self.find_first_value('Root.Title', section='Root'),
            name=self.find_first_value('Root.Name', section='Root'),
            ref=self.ref,
            description=self.find_first_value('Root.Description', section='Root'),
            doc=documentation(),
            contact=contacts(),
            resources=resources,
            references=references,

        )

        return convert_markdown(v, extensions)

    @property
    def html(self):
        from .html import html
        return html(self)

    @property
    def markdown(self):
        from .html import markdown
        return markdown(self)

    def write_csv(self, path=None):
        """Write CSV file. Sorts the sections before calling the superclass write_csv"""

        # Sort the Sections

        self.sort_sections(['Root', 'Contacts', 'Documentation', 'References','Resources','Citations','Schema'])

        # Sort Terms in the root section

        # Re-wrap the description and abstract
        if self.description:
            self.description = self.description

        if self.abstract:
            self.description = self.abstract

        t = self['Root'].get_or_new_term('Root.Modified')
        t.value = datetime_now()

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
            'Root.Access',
            'Root.Access',
            'Root.Distribution'
        ])



        return super().write_csv(path)
