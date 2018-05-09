from itertools import islice

from metapack.appurl import MetapackPackageUrl
from metapack.doc import EMPTY_SOURCE_HEADER
from metapack.exc import MetapackError, ResourceError
from metatab import Term
from rowgenerators import parse_app_url
from rowgenerators.exceptions import  DownloadError
from rowgenerators.rowpipe import RowProcessor


class Resource(Term):
    # These property names should return null if they aren't actually set.
    _common_properties = 'url name description schema'.split()

    def __init__(self, term, value, term_args=False, row=None, col=None, file_name=None, file_type=None,
                 parent=None, doc=None, section=None,
                 ):

        self.errors = {}  # Typecasting errors

        # Metadata returned by the iteratator, available after iteration
        self.post_iter_meta = {}

        super().__init__(term, value, term_args, row, col, file_name, file_type, parent, doc, section)

    @property
    def base_url(self):
        """Base URL for resolving resource URLs"""

        if self.doc.package_url:
            return self.doc.package_url

        return self.doc._ref

    @property
    def _envvar_env(self):
        return {
            # These become their own env vars when calling a program.
            'CACHE_DIR': self._doc._cache.getsyspath('/'),
            'RESOURCE_NAME': self.name,
            'RESOLVED_URL': str(self.resolved_url),
            'WORKING_DIR': str(self._doc.doc_dir),
            'METATAB_DOC': str(self._doc.ref),
            'METATAB_WORKING_DIR': str(self._doc.doc_dir),
            'METATAB_PACKAGE': str(self._doc.package_url)
        }

    @property
    def env(self):
        """The execution context for rowprocessors and row-generating notebooks and functions. """
        from copy import copy

        env = copy(self.doc.env)

        env.update(self._envvar_env)

        env.update(self.all_props)

        return env

    @property
    def code_path(self):
        from .util import slugify
        from fs.errors import DirectoryExists

        sub_dir = 'resource-code/{}'.format(slugify(self.doc.name))
        try:
            self.doc.cache.makedirs(sub_dir)
        except DirectoryExists:
            pass

        return self.doc.cache.opendir(sub_dir).getsyspath(slugify(self.name) + '.py')

    @property
    def expanded_url(self):

        if not self.url:
            return None

        u = parse_app_url(self.url)

        if u.scheme == 'index':
            u = u.resolve()

        return u


    @property
    def resolved_url(self):
        """Return a URL that properly combines the base_url and a possibly relative
        resource url"""

        if not self.url:
            return None

        u = parse_app_url(self.url)

        if u.scheme == 'index':
            u = u.resolve()

        if u.scheme != 'file':
            # Hopefully means the URL is http, https, ftp, etc.
            return u
        elif u.resource_format == 'ipynb':

            # This shouldn't be a special case, but ...
            t = self.doc.package_url.inner.join_dir(self.url)
            t = t.as_type(type(u))
            t.fragment = u.fragment

            return t

        elif u.proto == 'metapack':

            if not u.resource:
                raise ResourceError(f"Metapack url '{u}' doesn't have a resource")

            return u.resource.resolved_url.get_resource().get_target()


        else:

            assert isinstance(self.doc.package_url, MetapackPackageUrl), (
                type(self.doc.package_url), self.doc.package_url)

            try:
                t = self.doc.package_url.resolve_url(self.url)

                # Also a hack
                t.scheme_extension = parse_app_url(self.url).scheme_extension

                # Another Hack!
                if not t.fragment and u.fragment:
                    t.fragment = u.fragment

                # Yet more hack!
                t = parse_app_url(str(t))

                return t

            except ResourceError as e:
                # This case happens when a filesystem packages has a non-standard metadata name
                # Total hack
                raise



    @property
    def inner(self):
        """For compatibility with the Appurl interface"""
        return self.resolved_url.get_resource().get_target().inner

    @property
    def parsed_url(self):
        return parse_app_url(self.url)

    def _name_for_col_term(self, c, i):

        altname = c.get_value('altname')
        name = c.value if c.value != EMPTY_SOURCE_HEADER else None
        default = "col{}".format(i)

        for n in [altname, name, default]:
            if n:
                return n

    @property
    def schema_name(self):
        """The value of the Name or Schema property"""
        return self.get_value('schema', self.get_value('name'))

    @property
    def schema_table(self):
        """Deprecated. Use schema_term()"""
        return self.schema_term

    @property
    def schema_term(self):
        """Return the Table term for this resource, which is referenced either by the `table` property or the
        `schema` property"""

        if not self.name:
            raise MetapackError("Resource for url '{}' doe not have name".format(self.url))

        t = self.doc.find_first('Root.Table', value=self.get_value('name'))
        frm = 'name'

        if not t:
            t = self.doc.find_first('Root.Table', value=self.get_value('schema'))
            frm = 'schema'

        if not t:
            frm = None

        return t

    @property
    def headers(self):
        """Return the headers for the resource. Returns the AltName, if specified; if not, then the
        Name, and if that is empty, a name based on the column position. These headers
        are specifically applicable to the output table, and may not apply to the resource source. FOr those headers,
        use source_headers"""

        t = self.schema_term

        if t:
            return [self._name_for_col_term(c, i)
                    for i, c in enumerate(t.children, 1) if c.term_is("Table.Column")]
        else:
            return None

    @property
    def source_headers(self):
        """"Returns the headers for the resource source. Specifically, does not include any header that is
        the EMPTY_SOURCE_HEADER value of _NONE_"""

        t = self.schema_term

        if t:
            return [self._name_for_col_term(c, i)
                    for i, c in enumerate(t.children, 1) if c.term_is("Table.Column")
                    and c.get_value('name') != EMPTY_SOURCE_HEADER
                    ]
        else:
            return None

    def columns(self):

        try:
            # For resources that are metapack packages.
            r =  self.resolved_url.resource.columns()
            return list(r)
        except AttributeError:
            pass

        t = self.schema_term

        columns = []

        if t:
            for i, c in enumerate(t.children):

                if c.term_is("Table.Column"):
                    p = c.all_props
                    p['pos'] = i
                    p['name'] = c.value
                    p['header'] = self._name_for_col_term(c, i)

                    columns.append(p)

        return columns

    def row_processor_table(self, ignore_none=False):
        """Create a row processor from the schema, to convert the text values from the
        CSV into real types"""
        from rowgenerators.rowpipe import Table

        type_map = {
            None: None,
            'string': 'str',
            'text': 'str',
            'number': 'float',
            'integer': 'int'
        }

        def map_type(v):
            return type_map.get(v, v)

        if self.schema_term:

            t = Table(self.get_value('name'))

            col_n = 0

            for c in self.schema_term.children:

                if ignore_none and c.name == EMPTY_SOURCE_HEADER:
                    continue

                if c.term_is('Table.Column'):
                    t.add_column(self._name_for_col_term(c, col_n),
                                 datatype=map_type(c.get_value('datatype')),
                                 valuetype=map_type(c.get_value('valuetype')),
                                 transform=c.get_value('transform'),
                                 width=c.get_value('width')
                                 )
                    col_n += 1

            return t

        else:
            return None

    @property
    def raw_row_generator(self):
        """Like rowgenerator, but does not try to create a row processor table"""
        from rowgenerators import get_generator

        self.doc.set_sys_path()  # Set sys path to package 'lib' dir in case of python function generator

        ru = self.resolved_url

        try:
            resource = ru.resource # For Metapack urls

            return resource.row_generator
        except AttributeError:
            pass

        ut = ru.get_resource().get_target()

        # Encoding is supposed to be preserved in the URL but isn't
        source_url = parse_app_url(self.url)

        # source_url will be None for Sql terms.

        ut.encoding = self.get_value('encoding') or (source_url.encoding if source_url else None)

        g = get_generator(ut,  resource=self,
                          doc=self._doc, working_dir=self._doc.doc_dir,
                          env=self.env)

        assert g, ut

        return g

    @property
    def row_generator(self):
        from rowgenerators import get_generator

        self.doc.set_sys_path()  # Set sys path to package 'lib' dir in case of python function generator

        if not self.value:
            raise ResourceError("Can't generate rows, term '{}' has no url value  ".format(self.name))

        ru = self.resolved_url

        if not ru:
            raise ResourceError("Failed to resolve url for  '{}' ".format(self))

        try:
            resource = ru.resource # For Metapack urls

            return resource.row_generator
        except AttributeError:
            pass

        rur = ru.get_resource()

        if not rur:
            raise ResourceError("Failed to get resource for '{}' ".format(ru))

        ut = rur.get_target()

        # Encoding is supposed to be preserved in the URL but isn't
        source_url = parse_app_url(self.url)

        # source_url will be None for Sql terms.
        ut.encoding = source_url.encoding if source_url else self.get_value('encoding')

        table = self.row_processor_table()

        g = get_generator(ut, table=table, resource=self,
                          doc=self._doc, working_dir=self._doc.doc_dir,
                          env=self.env)

        assert g, ut

        return g

    def _get_header(self):
        """Get the header from the deinfed header rows, for use  on references or resources where the schema
        has not been run"""

        try:
            header_lines = [int(e) for e in str(self.get_value('headerlines', 0)).split(',')]
        except ValueError as e:
            header_lines = [0]

        # We're processing the raw datafile, with no schema.
        header_rows = islice(self.row_generator, min(header_lines), max(header_lines) + 1)

        from tableintuit import RowIntuiter
        headers = RowIntuiter.coalesce_headers(header_rows)

        return headers

    def __iter__(self):
        """Iterate over the resource's rows"""

        headers = self.headers

        # There are several args for SelectiveRowGenerator, but only
        # start is really important.
        try:
            start = int(self.get_value('startline', 1))
        except ValueError as e:
            start = 1

        if headers:  # There are headers, so use them, and create a RowProcess to set data types
            yield headers

            base_row_gen = self.row_generator

            assert base_row_gen is not None

            assert type(self.env) == dict

            rg = RowProcessor(islice(base_row_gen, start, None),
                              self.row_processor_table(),
                              source_headers=self.source_headers,
                              manager = self,
                              env=self.env,
                              code_path=self.code_path)

        else:
            headers = self._get_header()  # Try to get the headers from defined header lines

            yield headers
            rg = islice(self.row_generator, start, None)

        yield from rg

        try:
            self.errors = rg.errors if rg.errors else {}
        except AttributeError:
            self.errors = {}

        self.post_iter_meta = base_row_gen.meta

    @property
    def iterdict(self):
        """Iterate over the resource in dict records"""
        from collections import OrderedDict

        headers = None

        for row in self:

            if headers is None:
                headers = row
                continue

            yield OrderedDict(zip(headers, row))

    @property
    def iterrows(self):
        """Iterate over the resource as row proxy objects, which allow acessing colums as attributes"""

        from rowgenerators.rowproxy import RowProxy

        row_proxy = None

        headers = None

        for row in self:

            if not headers:
                headers = row
                row_proxy = RowProxy(headers)
                continue

            yield row_proxy.set_row(row)

    @property
    def json_headers(self):
        return [(c['pos'], c.get('json') or c['header']) for c in self.columns() if c.get('json')]

    @property
    def iterstruct(self):
        """Yield data structures built from the JSON header specifications in a table"""
        from rowgenerators.rowpipe.json import add_to_struct

        json_headers = self.json_headers

        for row in islice(self, 1, None): # islice skips header
            d = {}
            for pos, jh in json_headers:
                add_to_struct(d, jh, row[pos])
            yield d

    def iterjson(self, *args, **kwargs):
        """Yields the data structures from iterstruct as JSON strings"""
        from rowgenerators.rowpipe.json import VTEncoder
        import json

        if 'cls' not in kwargs:
            kwargs['cls'] = VTEncoder

        for s in self.iterstruct:
            yield (json.dumps(s, *args, **kwargs))

    def iteryaml(self, *args, **kwargs):
        """Yields the data structures from iterstruct as YAML strings"""
        from rowgenerators.rowpipe.json import VTEncoder
        import yaml

        if 'cls' not in kwargs:
            kwargs['cls'] = VTEncoder

        for s in self.iterstruct:
            yield (yaml.safe_dump(s))

    def dataframe(self, limit=None):
        """Return a pandas datafrome from the resource"""

        from metapack.jupyter.pandas import MetatabDataFrame

        rg = self.row_generator

        # Maybe generator has it's own Dataframe method()
        try:
            return rg.dataframe()
        except AttributeError:
            pass

        # Just normal data, so use the iterator in this object.
        headers = next(islice(self, 0, 1))
        data = islice(self, 1, None)

        df = MetatabDataFrame(list(data), columns=headers, metatab_resource=self)

        self.errors = df.metatab_errors = rg.errors if hasattr(rg, 'errors') and rg.errors else {}

        return df

    def geoframe(self):
        """Return a Geo dataframe"""

        return self.dataframe().geo

    def read_csv(self, *args, **kwargs):
        """Fetch the target and pass through to pandas.read_csv

        Don't provide the first argument of read_csv(); it is supplied internally.
        """
        import pandas

        t = self.resolved_url.get_resource().get_target()

        return pandas.read_csv(t.fspath, *args, **kwargs)

    def read_fwf(self, *args, **kwargs):
        """Fetch the target and pass through to pandas.read_fwf.

        Don't provide the first argument of read_fwf(); it is supplied internally. """
        import pandas

        t = self.resolved_url.get_resource().get_target()

        return pandas.read_fwf(t.fspath, *args, **kwargs)

    def readlines(self):
        """Load the target, open it, and return the result from readlines()"""

        t = self.resolved_url.get_resource().get_target()
        with open(t.fspath) as f:
            return f.readlines()

    def petl(self, *args, **kwargs):
        """Return a PETL source object"""
        import petl

        t = self.resolved_url.get_resource().get_target()

        if t.target_format == 'txt':
            return petl.fromtext(str(t.fspath), *args, **kwargs)
        elif t.target_format == 'csv':
            return petl.fromcsv(str(t.fspath), *args, **kwargs)
        else:
            raise Exception("Can't handle")

    def _repr_html_(self):


        try:
            return self.sub_resource._repr_html_()
        except AttributeError:
            pass
        except DownloadError:
            pass

        return (
                   "<h3><a name=\"resource-{name}\"></a>{name}</h3><p><a target=\"_blank\" href=\"{url}\">{url}</a></p>" \
                       .format(name=self.name, url=self.resolved_url)) + \
               "<table>\n" + \
               "<tr><th>Header</th><th>Type</th><th>Description</th></tr>" + \
               '\n'.join(
                   "<tr><td>{}</td><td>{}</td><td>{}</td></tr> ".format(c.get('header', ''),
                                                                        c.get('datatype', ''),
                                                                        c.get('description', ''))
                   for c in self.columns()) + \
               '</table>'

    @property
    def markdown(self):

        from .html import ckan_resource_markdown
        return ckan_resource_markdown(self)


class Reference(Resource):
    @property
    def env(self):
        e = super().env
        e['reference'] = self
        return e

    def __iter__(self):
        """Iterate over the resource's rows"""

        try:
            # For Metapack references
            yield from self.resolved_url.resource
        except AttributeError:
            yield from self.row_generator

class SqlQuery(Resource):

    @property
    def context(self):
        """Build the interpolation context from the schemas"""

        # Can't use self.columns b/c of recursion with resolved_url

        t = self.schema_term

        if not t:
            return {}

        sql_columns = []
        all_columns = []

        for i, c in enumerate(t.children):
            if c.term_is("Table.Column"):
                p = c.all_props

                if p.get('sqlselect'): # has a value for SqlSqlect
                    sql_columns.append(p.get('sqlselect'))

                all_columns.append(c.name)

        return {
            'SQL_COLUMNS': ', '.join(sql_columns),
            'ALL_COLUMNS': ', '.join(all_columns)
        }

    @property
    def resolved_url(self):

        if not self.query:
            return None

        # SQL Urls can be split into a Dsn part ( connection info ) and the SQL
        #  so the Sql urls have special handing for the references.
        dsns = {t.name:t.value for t in self.doc.find('Root.Dsn') }

        try:
            u = parse_app_url(dsns[self.get_value('dsn')])
        except KeyError:
            raise MetapackError(f"Sql term '{self.name}' does not have a Dsn property")

        if self.query.startswith('file:'): # .query resolves to value
            qu = parse_app_url(self.query, working_dir=self._doc.doc_dir).get_resource().get_target()

            with open(qu.fspath) as f:
                u.sql = f.read().format(**self.context)
        else:
            u.sql = self.query.format(**self.context)

        assert isinstance(self.doc.package_url, MetapackPackageUrl), (
            type(self.doc.package_url), self.doc.package_url)

        return u


class Distribution(Term):
    @property
    def type(self):

        # The following order is really important.
        if self.package_url.target_format == 'xlsx':
            return 'xlsx'
        elif self.package_url.resource_format == 'zip':
            return "zip"
        elif self.metadata_url.target_file == 'metadata.csv':
            return 'fs'
        elif self.package_url.target_format == 'csv':
            return "csv"

        else:
            return "unk"

    @property
    def package_url(self):
        from metapack import MetapackPackageUrl
        return MetapackPackageUrl(self.value, downloader=self.doc.downloader)

    @property
    def metadata_url(self):
        from metapack import MetapackDocumentUrl
        return MetapackDocumentUrl(self.value, downloader=self.doc.downloader)


