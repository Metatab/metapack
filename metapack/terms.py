from itertools import islice
from os.path import join

from metapack.appurl import MetapackPackageUrl
from metapack.doc import EMPTY_SOURCE_HEADER
from metapack.exc import MetapackError, ResourceError
from metatab import Term
from rowgenerators import parse_app_url
from rowgenerators.exceptions import DownloadError
from rowgenerators.rowpipe import RowProcessor
from rowgenerators.rowproxy import RowProxy


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

        assert env is not None, 'Got a null execution context'

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
    def parsed_url(self):
        return parse_app_url(self.url)

    @property
    def expanded_url(self):

        from os.path import normpath

        if not self.url:
            return None

        u = self.parsed_url

        if u.scheme == 'index':
            u = u.resolve()

        if u.scheme == 'file' and not u.path_is_absolute:

            if self.doc.package_url.isdir():
                u.path = normpath(join(self.doc.package_url.path, u.path))
            else:
                u = self.doc.package_url.join_target(u.path)

        return u

    @property
    def resolved_url(self):

        ru = self._resolved_url()

        # source_url will be None for Sql terms.
        if ru:
            for p in ('target_format', 'target_file', 'encoding', 'headers', 'start', 'end'):

                pns = ''.join(p.split('_'))  # attr names have '_', but Metatab props dont

                if self.get_value(pns):
                    setattr(ru, p, self.get_value(pns))
                elif self.get_value(p):  # Legacy version with '_'
                    setattr(ru, p, self.get_value(p))

        return ru

    def _resolved_url(self):
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
            t.target_file = u.target_file

            return t

        elif u.proto == 'metatab':

            u = self.expanded_url

            return u.get_resource().get_target()

        elif u.proto == 'metapack':

            u = self.expanded_url

            if u.resource:
                return u.resource.resolved_url.get_resource().get_target()
            else:
                return u

        if u.scheme == 'file':

            return self.expanded_url

        else:
            raise ResourceError('Unknown case for url {} '.format(self.url))

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
        """Return column information from the schema or from an upstreram package"""

        try:
            # For resources that are metapack packages.
            r = self.expanded_url.resource.columns()
            return list(r)
        except AttributeError as e:

            pass

        return self.schema_columns

    @property
    def schema_columns(self):
        """Return column informatino only from this schema"""
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

        ru = self.resolved_url8

        try:
            resource = ru.resource  # For Metapack urls

            return resource.row_generator
        except AttributeError:
            pass

        ut = ru.get_resource().get_target()

        # Encoding is supposed to be preserved in the URL but isn't
        source_url = parse_app_url(self.url)

        g = get_generator(ut, resource=self,
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
            resource = ru.resource  # For Metapack urls

            return resource.row_generator
        except AttributeError:
            pass

        rur = ru.get_resource()

        if not rur:
            raise ResourceError("Failed to get resource for '{}' ".format(ru))

        ut = rur.get_target()

        source_url = parse_app_url(self.url)

        table = self.row_processor_table()

        g = get_generator(ut, table=table, resource=self,
                          doc=self._doc, working_dir=self._doc.doc_dir,
                          env=self.env, source_url=self.expanded_url)

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

        try:
            end = int(self.get_value('endline', self.parsed_url.end))
        except (ValueError, TypeError) as e:
            end = None

        base_row_gen = self.row_generator
        assert base_row_gen is not None

        if headers:  # There are headers, so use them, and create a RowProcess to set data types
            yield headers

            assert type(self.env) == dict

            rg = RowProcessor(islice(base_row_gen, start, end),
                              self.row_processor_table(),
                              source_headers=self.source_headers,
                              manager=self,
                              env=self.env,
                              code_path=self.code_path)


        else:
            headers = self._get_header()  # Try to get the headers from defined header lines

            yield headers
            rg = islice(base_row_gen, start, None)

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

        row_proxy = None

        headers = None

        for row in self:

            if not headers:
                headers = row
                row_proxy = RowProxy(headers)
                continue

            yield row_proxy.set_row(row)

    def iterrowproxy(self, cls=RowProxy):
        """Iterate over the resource as row proxy objects, which allow acessing colums as attributes. Like iterrows,
        but allows for setting a specific RowProxy class. """

        row_proxy = None

        headers = None

        for row in self:

            if not headers:
                headers = row
                row_proxy = cls(headers)
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

        for row in islice(self, 1, None):  # islice skips header
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

    def dataframe(self, dtype=False, parse_dates=True, *args, **kwargs):
        """Return a pandas datafrome from the resource"""

        import pandas as pd

        rg = self.row_generator

        t = self.resolved_url.get_resource().get_target()

        if t.target_format == 'csv':
            return self.read_csv(dtype, parse_dates, *args, **kwargs)

        # Maybe generator has it's own Dataframe method()
        try:

            return rg.dataframe(*args, **kwargs)
        except AttributeError:
            pass

        # Just normal data, so use the iterator in this object.
        headers = next(islice(self, 0, 1))
        data = islice(self, 1, None)

        df = pd.DataFrame(list(data), columns=headers, *args, **kwargs)

        self.errors = df.metatab_errors = rg.errors if hasattr(rg, 'errors') and rg.errors else {}

        return df

    def geoframe(self, *args, **kwargs):
        """Return a Geo dataframe"""

        from geopandas import GeoDataFrame
        import geopandas as gpd
        from shapely.geometry.polygon import BaseGeometry
        from shapely.wkt import loads

        gdf = None
        try:
            gdf = self.resolved_url.geoframe(*args, **kwargs)
        except AttributeError:
            pass

        if gdf is None:
            try:
                gdf = self.resolved_url.geo_generator.geoframe(*args, **kwargs)
            except AttributeError:
                pass

        if gdf is None:
            try:
                gdf = self.row_generator.geoframe(*args, **kwargs)
            except AttributeError:
                pass

        if gdf is None:
            try:

                gdf = GeoDataFrame(self.dataframe(*args, **kwargs))

                first = next(gdf.iterrows())[1]['geometry']

                if isinstance(first, str):
                    # We have a GeoDataframe, but the geometry column is still strings, so
                    # it must be converted
                    shapes = [loads(row['geometry']) for i, row in gdf.iterrows()]

                elif not isinstance(first, BaseGeometry):
                    # If we are reading a metatab package, the geometry column's type should be
                    # 'geometry' which will give the geometry values class type of
                    # rowpipe.valuetype.geo.ShapeValue. However, there are other
                    # types of objects that have a 'shape' property.

                    shapes = [row['geometry'].shape for i, row in gdf.iterrows()]

                else:
                    shapes = gdf['geometry']

                gdf['geometry'] = gpd.GeoSeries(shapes)
                gdf.set_geometry('geometry')

                # Wild guess. This case should be most often for Metatab processed geo files,
                # which are all 4326
                if gdf.crs is None:
                    gdf.crs = {'init': 'epsg:4326'}


            except KeyError as e:
                raise ResourceError(
                    "Failed to create GeoDataFrame for resource '{}': No geometry column".format(self.name))
            except (KeyError, TypeError) as e:
                raise ResourceError("Failed to create GeoDataFrame for resource '{}': {}".format(self.name, str(e)))

        assert gdf.crs is not None
        return gdf

    def _update_pandas_kwargs(self, dtype=False, parse_dates=True, kwargs={}):
        """ Construct args suitable for pandas read_csv
        :param dtype: If true, create a dtype type map. Otherwise, pass argument value to read_csv
        :param parse_dates: If true, create a list of date/time columns for the parse_dates argument of read_csv
        :param kwargs:
        :return:
        """

        from datetime import datetime, time, date

        type_map = {
            None: None,
            'string': str,
            'text': str,
            'number': float,
            'integer': int,
            'datetime': datetime,
            'time': time,
            'date': date

        }

        if dtype is True:
            kwargs['dtype'] = {c['name']: type_map.get(c['datatype'], c['datatype']) for c in self.columns()}
        elif dtype:
            kwargs['dtype'] = dtype

        if parse_dates is True:
            date_cols = [c['name'] for c in self.columns() if c['datatype'] in ('date', 'datetime', 'time')]
            kwargs['parse_dates'] = date_cols or True
        elif parse_dates:
            kwargs['parse_dates'] = parse_dates

        kwargs['low_memory'] = False

        return kwargs

    def read_csv(self, dtype=False, parse_dates=True, *args, **kwargs):
        """Fetch the target and pass through to pandas.read_csv

        Don't provide the first argument of read_csv(); it is supplied internally.
        """

        import pandas

        t = self.resolved_url.get_resource().get_target()

        kwargs = self._update_pandas_kwargs(dtype, parse_dates, kwargs)

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

            if self.resolved_url.resource is None:
                raise ResourceError("Reference '{}' doesn't specify a valid resource in the URL. ".format(self.name) +
                                    "\n Maybe need to add '#<resource_name>' to the end of the url '{}'".format(
                                        self.url))

            yield from self.resolved_url.resource
        except AttributeError:

            # There are several args for SelectiveRowGenerator, but only
            # start is really important.
            try:
                start = int(self.get_value('startline', 1))
            except ValueError as e:
                start = 1

            try:
                end = int(self.get_value('endline', self.parsed_url.end))
            except (ValueError, TypeError) as e:
                end = None

            headers = self._get_header()

            yield headers

            yield from islice(self.row_generator, start, end)

    @property
    def resource(self):
        return self.expanded_url.resource

    def _repr_html_(self):
        try:
            return self.resource._repr_html_()
        except AttributeError:
            return super()._repr_html_()

    def read_csv(self, dtype=False, parse_dates=True, *args, **kwargs):
        try:
            return self.resource.read_csv(dtype, parse_dates, *args, **kwargs)
        except AttributeError as e:
            return super().read_csv(dtype=dtype, parse_dates=parse_dates, *args, **kwargs)

    def dataframe(self, limit=None):
        try:
            return self.resource.dataframe(limit)
        except AttributeError:
            return super().dataframe(limit)


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

                if p.get('sqlselect'):  # has a value for SqlSqlect
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
        #  so the Sql urls have special handling for the references.
        dsns = {t.name: t.value for t in self.doc.find('Root.Dsn')}

        try:
            u = parse_app_url(dsns[self.get_value('dsn')])
        except KeyError:
            raise MetapackError(f"Sql term '{self.name}' does not have a Dsn property")

        if self.query.startswith('file:'):  # .query resolves to value
            qu = parse_app_url(self.query, working_dir=self._doc.doc_dir).get_resource().get_target()

            with open(qu.fspath) as f:
                u.sql = f.read().format(**self.context)
        else:
            u.sql = self.query.format(**self.context)

        assert isinstance(self.doc.package_url, MetapackPackageUrl), (
            type(self.doc.package_url), self.doc.package_url)

        return u


class Distribution(Term):

    def __init__(self, term, value, term_args=False, row=None, col=None, file_name=None, file_type=None, parent=None,
                 doc=None, section=None):
        super().__init__(term, value, term_args, row, col, file_name, file_type, parent, doc, section)

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
