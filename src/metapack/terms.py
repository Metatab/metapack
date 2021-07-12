from itertools import islice
from os.path import join

from metatab import Term
from rowgenerators import parse_app_url
from rowgenerators.exceptions import DownloadError
from rowgenerators.rowpipe import RowProcessor
from rowgenerators.rowproxy import RowProxy

from metapack.appurl import MetapackPackageUrl
from metapack.doc import EMPTY_SOURCE_HEADER
from metapack.exc import (
    MetapackError,
    NoResourceError,
    NoRowProcessor,
    PackageError,
    ResourceError
)


def int_maybe(v):
    try:
        return int(float(v))
    except Exception:
        return None


def first_not_none(*a):
    try:
        return next(e for e in a if e is not None)
    except StopIteration:
        return None


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

        # env.update(self.all_props)

        return env

    @property
    def code_path(self):
        from metatab.util import slugify
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
                    try:
                        setattr(ru, p, self.get_value(pns))
                    except AttributeError:
                        # Can't set the attribute, probaby because it is a property
                        pass
                elif self.get_value(p):  # Legacy version with '_'
                    try:
                        setattr(ru, p, self.get_value(p))
                    except AttributeError:
                        # Can't set attribute. Some of the attributes in the for list
                        # may actually be properties that can't be set for a paricular object.
                        pass

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
            raise MetapackError("Resource for url '{}' does not have name".format(self.url))

        t = self.doc.find_first('Root.Table', value=self.get_value('name'))

        if not t:
            t = self.doc.find_first('Root.Table', value=self.get_value('schema'))

        return t

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

    @property
    def header_map(self):
        """Return a list of tuples that translates column names"""

        from collections import namedtuple
        HeaderPair = namedtuple('HeaderPair', 'source dest')

        import csv
        from pathlib import Path

        cm_name = self.get_value('colmap')

        if not cm_name:
            return None

        if not self.doc.ref.scheme == 'file':
            return None

        # Path(str()) to convert PurePosixPath to PosixPath
        path = Path(str(self.doc.ref.fspath)).parent.joinpath(f"colmap-{cm_name}.csv")

        if not path.exists():
            return None

        with path.open() as f:
            cm = []
            for row in csv.DictReader(f):
                if row['index']:
                    cm.append(HeaderPair(source=row[self.name], dest=row['index']))

        return cm

    def _get_start_end_header(self):
        """Identify the start row, end row and header rows from the url or resource"""

        # There are several args for SelectiveRowGenerator, but only
        # start is really important.
        start = first_not_none(int_maybe(self.get_value('startline')),
                               int_maybe(self.resolved_url.start),
                               1)

        end = first_not_none(int_maybe(self.get_value('endline')),
                             int_maybe(self.resolved_url.end))

        headers = first_not_none(self.get_value('headerlines'),
                                 self.resolved_url.headers,
                                 0)

        try:
            header_lines = [int(e) for e in str(headers).split(',')]
        except ValueError:
            header_lines = [0]

        return header_lines, start, end

    def _get_header(self):
        """Get the header from the defined header rows, for use  on references or resources where the schema
        has not been run"""

        return next(iter(self.selective_row_generator), 1)

    @property
    def headers(self):
        """Return the headers for the resource. Returns the AltName, if specified; if not, then the
        Name, and if that is empty, a name based on the column position. These headers
        are specifically applicable to the output table, and may not apply to the resource source. For those headers,
        use source_headers"""

        t = self.schema_term

        if t:
            # Get the header from the schema
            return [self._name_for_col_term(c, i)
                    for i, c in enumerate(t.children, 1) if c.term_is("Table.Column")]
        else:
            return self._get_header()

    def columns(self):
        """Return column information from the schema or from an upstreram package"""

        try:
            # For resources that are metapack packages.
            r = self.expanded_url.resource.columns()
            return list(r)
        except AttributeError:

            pass

        return self.schema_columns

    @property
    def schema_columns(self):
        """Return column information only from this schema"""
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

    def row_processor_table(self, ignore_none=False, width_column='width'):
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
                                 width=c.get_value(width_column)
                                 )
                    col_n += 1

            return t

        else:
            return None

    @property
    def row_generator(self):
        return self._row_generator()

    @property
    def raw_row_generator(self):
        return self._row_generator(rptable=None)

    def _row_generator(self, rptable=True):
        '''
        Return a row generator for the URL

        :param table: Row Processor table, for the  rowgenerators.generator.fixed.FixedSource generator
        :return:
        '''
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
            raise NoResourceError("Failed to get resource for '{}' ".format(ru))

        ut = rur.get_target()

        if rptable is True:
            rptable = self.row_processor_table()
        elif rptable is False:
            rptable = None

        g = get_generator(ut, table=rptable, resource=self,
                          doc=self._doc, working_dir=self._doc.doc_dir,
                          env=self.env, source_url=self.expanded_url)

        assert g, ut

        return g

    @property
    def selective_row_generator(self):
        """Like row_generator, but respects start, end and header URL parameters"""

        from rowgenerators.source import SelectiveRowGenerator

        header_lines, start, end = self._get_start_end_header()

        return SelectiveRowGenerator(self.row_generator, header_lines=header_lines, start=start, end=end)

    @property
    def iterselectiverows(self):
        """Most basic iterator that respects start, end and header"""
        yield from self.selective_row_generator

    @property
    def itermetatabrows(self):

        try:
            yield from self.resolved_url.resource
            # For Metapack references, just iterate over the upstream resource
        except AttributeError as e:
            raise PackageError(f"Resource '{self.name}' is not a metatab package") from e

        except TypeError as e:  # resource is None:
            # The URL type has a resource property, so it should be iterable, but
            # the resource is None
            raise NoResourceError("Reference '{}' doesn't specify a valid resource in the URL. ".format(self.name) +
                                  "\n Maybe need to add '#<resource_name>' to the end of the url '{}'".format(
                                      self.url)) from e

    @property
    def iterprocessedrows(self):
        """Iterate using a row processor table, which requires a schema"""

        assert type(self.env) == dict

        _, start, end = self._get_start_end_header()

        rptable = self.row_processor_table()  # Requires a schema term

        if not rptable:
            raise NoRowProcessor("No row processor for resource (")

        base_row_gen = self.row_generator

        rg = RowProcessor(islice(base_row_gen, start, end),
                          rptable,
                          source_headers=self.source_headers,
                          manager=self,
                          env=self.env,
                          code_path=self.code_path)

        yield self.headers
        yield from rg

        self.post_iter_meta = base_row_gen.meta

        try:
            self.errors = rg.errors if rg.errors else {}
        except AttributeError:
            self.errors = {}

    @property
    def iterrawrows(self):
        """Iterate without a row processor table"""
        try:
            yield from self.itermetatabrows

        except PackageError:  # self.resolved_url has no attribute 'resource'

            _, start, end = self._get_start_end_header()

            headers = self._get_header()

            yield headers

            base_row_gen = self.row_generator

            yield from islice(base_row_gen, start, end)

            self.post_iter_meta = base_row_gen.meta

    def __iter__(self):
        """General data iterator. Tries to iterate as a Metatab package, then with
        a row processor ( schema ) and finally, raw rows. """
        #
        # Maybe it is a metatab resource
        from rowgenerators.source import SelectiveRowGenerator

        headers = None
        base_row_gen = None

        try:
            yield from self.resolved_url.resource
            return
        except AttributeError:
            base_row_gen = self.row_generator

        except TypeError as e:  # resource is None:
            # The URL type has a resource property, so it should be iterable, but
            # the resource is None
            raise NoResourceError("Reference '{}' doesn't specify a valid resource in the URL. ".format(self.name) +
                                  "\n Maybe need to add '#<resource_name>' to the end of the url '{}'".format(
                                      self.url)) from e

        header_lines, start, end = self._get_start_end_header()

        rptable = self.row_processor_table()  # Requires a schema term

        if rptable:

            rg = iter(RowProcessor(islice(base_row_gen, start, end),
                                   rptable,
                                   source_headers=self.source_headers,
                                   manager=self,
                                   env=self.env,
                                   code_path=self.code_path))
            headers = self.headers
        else:
            rg = iter(SelectiveRowGenerator(base_row_gen, header_lines=header_lines, start=start, end=end))
            headers = next(rg)

        yield headers
        yield from rg

        self.post_iter_meta = base_row_gen.meta

        try:
            self.errors = rg.errors if rg.errors else {}
        except AttributeError:
            self.errors = {}

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

        yield from self.iterrowproxy()

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

    def dataframe(self, dtype=True, parse_dates=True, *args, **kwargs):
        """Return a pandas datafrome from the resource"""

        import pandas as pd
        import warnings
        from rowgenerators.exceptions import RowGeneratorConfigError, RowGeneratorError

        rg = self.row_generator

        mod_kwargs = self._update_pandas_kwargs(dtype, parse_dates, kwargs)

        # Unecessary?
        self.resolved_url.get_resource().get_target()

        # Maybe generator has it's own Dataframe method()
        if not self.resolved_url.start and not self.resolved_url.headers:
            # The if clause is b/c the generators don't respect the start, end and headers
            # url arguments.
            while True:
                try:
                    df = rg.dataframe(*args, **mod_kwargs)
                    return df
                except AttributeError:
                    break
                except RowGeneratorConfigError as e:

                    if e.config_type == 'dtype':
                        warnings.warn('Failed to set dtype of columns. Trying again without dtype configuration')
                        del mod_kwargs['dtype']
                    elif e.config_type == 'dates' or 'parse_dates' in str(e):
                        warnings.warn('Failed to set parse dates . Trying again without parse_dates configuration')
                        del mod_kwargs['parse_dates']
                    else:
                        break
                except RowGeneratorError as e:
                    if 'parse_dates' in str(e):
                        warnings.warn('Failed to set parse dates . Trying again without parse_dates configuration')
                        del mod_kwargs['parse_dates']
                    else:
                        break

        # The CSV generator can handle dataframes itself, so this code should not be
        # needed any longer
        # if t.target_format == 'csv' and not self.resolved_url.start and not self.resolved_url.headers:
        #    df = self.read_csv(*args, **mod_kwargs)
        #    return df

        # Just normal data, so use the iterator in this object.

        headers = next(islice(self, 0, 1))  # Why not using the schema?
        data = islice(self, 1, None)

        df = pd.DataFrame(list(data), columns=headers, *args, **kwargs)

        self.errors = rg.errors if hasattr(rg, 'errors') and rg.errors else {}

        return df

    @property
    def isgeo(self):
        return 'geometry' in [c['name'] for c in self.columns()]

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

                    def robust_loads(data):
                        try:
                            return loads(data)
                        except AttributeError:  # 'float' object has no attribute 'encode' -> loads got a nan
                            return None

                    shapes = [robust_loads(row['geometry']) for i, row in gdf.iterrows()]

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
                    gdf.crs = 'epsg:4326'

            except KeyError:
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

        kwargs = dict(kwargs.items())

        try:
            # Nullable integers added to pandas about 0.24
            from pandas.arrays import IntegerArray # noqa F401
            int_type = 'Int64'
        except ModuleNotFoundError:
            int_type = int

        type_map = {
            None: None,
            'unknown': str,
            'string': str,
            'geometry': str,
            'text': str,
            'number': float,
            'integer': int_type,
            'datetime': str,  # datetime,
            'time': str,  # time,
            'date': str,  # date

        }

        if dtype is True:
            kwargs['dtype'] = {c['header']: type_map.get(c['datatype'], c['datatype']) for c in self.columns()}
        elif dtype:
            kwargs['dtype'] = dtype

        if parse_dates is True:
            date_cols = [c['header'] for c in self.columns() if c['datatype'] in ('date', 'datetime', 'time')]
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
        from .exc import InternalError

        t = self.resolved_url.get_resource().get_target()

        kwargs = self._update_pandas_kwargs(dtype, parse_dates, kwargs)

        last_exception = None
        try:
            return pandas.read_csv(t.fspath, *args, **kwargs)
        except Exception as e:
            last_exception = e

        if 'not in list' in str(last_exception) and 'parse_dates' in kwargs:

            # This case happens when there is a mismatch between the headings in the
            # file we're reading and the schema. for insance, the file header has a leading space,
            # and we're areying to parse dates for that column. So, try again
            # without parsing dates.
            del kwargs['parse_dates']
            try:
                return pandas.read_csv(t.fspath, *args, **kwargs)
            except Exception as e:
                last_exception = e

        raise InternalError(f"{last_exception} in read_csv: path={t.fspath} args={args} kwargs={kwargs}\n")

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

        return (("<h3><a name=\"resource-{name}\"></a>{name}</h3><p><a target=\"_blank\" href=\"{url}\">{url}</a></p>"
                 .format(name=self.name, url=self.resolved_url)) +
                "<table>\n" +
                "<tr><th>Header</th><th>Type</th><th>Description</th></tr>" +
                '\n'.join(
                    "<tr><td>{}</td><td>{}</td><td>{}</td></tr> ".format(c.get('header', ''),
                                                                         c.get('datatype', ''),
                                                                         c.get('description', ''))
                    for c in self.columns()) +
                '</table>')


@property
def hash(self):
    """Return a hash from th source_generator"""

    return self.row_generator.hash


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

    @property
    def resource(self):
        """Interpret the URL as a metatab package with a resource reference,
        and return the resource"""
        return self.expanded_url.resource

    @property
    def package(self):
        """Interpret the URL as a metatab package"""
        return self.expanded_url.doc

    def _repr_html_(self):
        try:
            return self.resource._repr_html_()
        except AttributeError:
            return super()._repr_html_()

    def read_csv(self, dtype=False, parse_dates=True, *args, **kwargs):

        kwargs = self._update_pandas_kwargs(dtype, parse_dates, kwargs)

        try:
            return self.resource.read_csv(*args, **kwargs)
        except AttributeError:
            pass

        return super().read_csv(*args, **kwargs)

    def dataframe(self, dtype=False, parse_dates=True, *args, **kwargs):

        try:
            return self.resource.dataframe(*args, **kwargs)
        except AttributeError:
            pass

        return super().dataframe(*args, **kwargs)


class SqlQuery(Resource):

    @property
    def context(self):
        """Build the interpolation context from the schemas"""

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
        elif self.package_url.scheme == 's3':
            return "s3"
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

    def resource_url(self, r):
        """Return a resource URL for this distribution"""

        if self.package_url.target_format == 'xlsx':
            return r.url
        elif self.package_url.resource_format == 'zip':
            return r.url
        elif self.metadata_url.target_file == 'metadata.csv':
            return r.url
        elif self.package_url.scheme == 's3':
            return r.s3url
        elif self.package_url.target_format == 'csv':
            return r.url

        else:
            return r.url
