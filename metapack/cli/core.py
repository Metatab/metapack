import logging
from pathlib import Path

from metapack.constants import PACKAGE_PREFIX
from metapack.doc import MetapackDoc
from metatab import DEFAULT_METATAB_FILE, LINES_METATAB_FILE, IPYNB_METATAB_FILE
from tabulate import tabulate

logger = logging.getLogger('user')
logger_err = logging.getLogger('cli-errors')
debug_logger = logging.getLogger('debug')
download_logger = logging.getLogger('debug')

from rowgenerators.appurl.web.download import logger as download_logger


def cli_init(log_level=logging.INFO):
    import sys

    from metapack.appurl import SearchUrl

    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter('%(message)s'))
    out_hdlr.setLevel(log_level)
    logger.addHandler(out_hdlr)
    logger.setLevel(log_level)

    out_hdlr = logging.StreamHandler(sys.stderr)
    out_hdlr.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    out_hdlr.setLevel(logging.WARN)
    logger_err.addHandler(out_hdlr)
    logger_err.setLevel(logging.WARN)

    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter('DEBUG: %(message)s'))
    out_hdlr.setLevel(log_level)
    debug_logger.addHandler(out_hdlr)
    debug_logger.setLevel(log_level)

    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter('DEBUG: %(message)s'))
    out_hdlr.setLevel(log_level)
    download_logger.addHandler(out_hdlr)
    download_logger.setLevel(log_level)

    SearchUrl.initialize()  # Setup the JSON index search.


def prt(*args, **kwargs):
    logger.info(' '.join(str(e) for e in args), **kwargs)


def warn(*args, **kwargs):
    logger_err.warning(' '.join(str(e) for e in args), **kwargs)


def err(*args, **kwargs):
    import sys
    logger_err.critical(' '.join(str(e) for e in args), **kwargs)
    sys.exit(1)


def metatab_info(cache):
    pass


def new_metatab_file(mt_file, template):
    from os.path import exists
    from uuid import uuid4

    from metatab.util import make_metatab_file

    template = template if template else 'metatab'

    if not exists(mt_file):
        doc = make_metatab_file(template)

        doc['Root']['Identifier'] = str(uuid4())

        write_doc(doc, mt_file)


def find_files(base_path, types):
    from os import walk
    from os.path import join, splitext

    for root, dirs, files in walk(base_path):
        if '_metapack' in root:
            continue

        for f in files:
            if f.startswith('_'):
                continue

            b, ext = splitext(f)
            if ext[1:] in types:
                yield join(root, f)


def get_lib_module_dict(doc):
    return doc.get_lib_module_dict()


def dump_resources(doc):
    for r in doc.resources():
        prt(r.name, r.resolved_url)


def dump_resource(doc, name, lines=None):
    import unicodecsv as csv
    import sys
    from itertools import islice
    from tabulate import tabulate
    from rowgenerators.rowpipe.exceptions import CasterExceptionError, TooManyCastingErrors

    r = doc.resource(name=name)

    if not r:
        err("Did not get resource for name '{}'".format(name))

    # WARNING! This code will not generate errors if line is set ( as for the -H
    # option because the errors are tansfered from the row pipe to the resource after the
    # iterator is exhausted

    gen = islice(r, 1, lines)

    def dump_errors(error_set):
        for col, errors in error_set.items():
            warn("Errors in casting column '{}' in resource '{}' ".format(col, r.name))
            for error in errors:
                warn("    ", error)

    try:
        if lines and lines <= 20:
            try:
                prt(tabulate(list(gen), list(r.headers)))
            except TooManyCastingErrors as e:
                dump_errors(e.errors)
                err(e)

        else:

            w = csv.writer(sys.stdout.buffer)

            if r.headers:
                w.writerow(r.headers)
            else:
                warn("No headers for resource '{}'; have schemas been generated? ".format(name))

            for row in gen:
                w.writerow(row)

    except CasterExceptionError as e:  # Really bad errors, not just casting problems.
        raise e
        err(e)
    except TooManyCastingErrors as e:
        dump_errors(e.errors)
        err(e)

    dump_errors(r.errors)


def dump_schema(doc, name):
    from tabulate import tabulate

    t = get_table(doc, name)

    rows = []
    header = 'name altname datatype description'.split()
    for c in t.children:
        cp = c.properties
        rows.append([cp.get(h) for h in header])

    prt(tabulate(rows, header))


def get_table(doc, name):
    t = doc.find_first('Root.Table', value=name)

    if not t:

        table_names = ["'" + t.value + "'" for t in doc.find('Root.Table')]

        if not table_names:
            table_names = ["<No Tables>"]

        err("Did not find schema for table name '{}' Tables are: {}"
            .format(name, " ".join(table_names)))

    return t


def update_name(mt_file, fail_on_missing=False, report_unchanged=True, force=False):
    from metapack import MetapackDoc

    if isinstance(mt_file, MetapackDoc):
        doc = mt_file
    else:
        doc = MetapackDoc(mt_file)

    o_name = doc.find_first_value("Root.Name", section=['Identity', 'Root'])

    updates = doc.update_name(force=force, report_unchanged=report_unchanged)

    for u in updates:
        prt(u)

    prt("Name is: ", doc.find_first_value("Root.Name", section=['Identity', 'Root']))

    if o_name != doc.find_first_value("Root.Name", section=['Identity', 'Root']) or force:
        write_doc(doc, mt_file)


def add_giturl(doc: MetapackDoc):
    import subprocess

    if not doc['Root'].find('GitUrl'):
        try:
            out = subprocess.run(['git', 'remote', 'show', 'origin'], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, timeout=6) \
                .stdout.decode('utf-8')

            fetchline = next(l.split() for l in out.splitlines() if 'Fetch' in l)
        except (TimeoutError, StopIteration, subprocess.TimeoutExpired, FileNotFoundError):
            fetchline = None

        if fetchline:
            t = doc['Root'].get_or_new_term('GitUrl')
            t.value = fetchline[-1]


def write_doc(doc: MetapackDoc, mt_file=None):
    """
    Write a Metatab doc to a CSV file, and update the Modified time
    :param doc:
    :param mt_file:
    :return:
    """

    from rowgenerators import parse_app_url

    if not mt_file:
        mt_file = doc.ref

    add_giturl(doc)

    u = parse_app_url(mt_file)

    if u.scheme == 'file':
        doc.write(mt_file)
        return True
    else:
        return False
        # warn("Not writing back to url ", mt_file)


def process_schemas(mt_file, resource=None, cache=None, clean=False, report_found=True, force=False):
    from metapack import MetapackDoc, MetapackResourceUrl, MetapackDocumentUrl

    if isinstance(mt_file, MetapackDoc):
        doc = mt_file
        write_doc_to_file = False
    else:
        doc = MetapackDoc(mt_file)
        write_doc_to_file = True

    try:
        if clean:
            doc['Schema'].clean()
        else:
            doc['Schema']

    except KeyError:
        doc.new_section('Schema', ['DataType', 'AltName', 'Description'])

    schemas_processed = 0

    for r in doc['Resources'].find('Root.Resource'):

        if resource and r.name != resource:
            continue

        schema_term = r.schema_term

        col_count = len(list(r.columns()))
        datatype_count = sum(1 for c in r.columns() if c['datatype'])

        if schema_term and col_count == datatype_count and force == False:
            if report_found:
                prt("Found table for '{}'; skipping".format(r.schema_name))
            continue

        if col_count != datatype_count:
            prt("Found table for '{}'; but {} columns don't have datatypes"
                .format(r.schema_name, col_count - datatype_count))

        prt("Processing {}".format(r.name))

        schemas_processed += 1

        rr = r.resolved_url

        if isinstance(rr, MetapackDocumentUrl):
            warn('{} is a MetapackDocumentUrl; skipping', r.name)
        elif isinstance(rr, MetapackResourceUrl):
            _process_metapack_resource(doc, r, force)
        else:
            _process_normal_resource(doc, r, force)

    if write_doc_to_file and schemas_processed:
        write_doc(doc, mt_file)


def _process_normal_resource(doc, r, force):
    """Process a resource that requires reading the file; not a metatab resource"""

    from rowgenerators.exceptions import SourceError, SchemaError
    from requests.exceptions import ConnectionError
    from itertools import islice

    from rowgenerators.source import SelectiveRowGenerator
    from tableintuit import TypeIntuiter

    schema_term = r.schema_term

    try:
        if force:
            rg = r.raw_row_generator
        else:
            rg = r.row_generator

    except SchemaError:
        rg = r.raw_row_generator
        warn("Failed to build row processor table, using raw row generator")

    slice = islice(rg, 5000)
    si = SelectiveRowGenerator(slice,
                               headers=[int(i) for i in r.get_value('headerlines', '0').split(',')],
                               start=int(r.get_value('startline', 1)))

    try:
        ti = TypeIntuiter().run(si)
    except SourceError as e:
        warn("Failed to process resource '{}'; {}".format(r.name, e))
        return
    except ConnectionError as e:
        warn("Failed to download resource '{}'; {}".format(r.name, e))
        return
    except UnicodeDecodeError as e:
        warn("Text encoding error for resource '{}'; {}".format(r.name, e))
        return

    if schema_term:

        prt("Updating table '{}' ".format(r.schema_name))

        # Existing columns
        orig_columns = {e['name'].lower() if e['name'] else '': e for e in r.schema_columns or {}}

        # Remove existing columns, so add them back later, possibly in a new order
        for child in list(schema_term.children):
            schema_term.remove_child(child)

    else:
        prt("Adding table '{}' ".format(r.schema_name))
        schema_term = doc['Schema'].new_term('Table', r.schema_name)
        orig_columns = {}

    for i, c in enumerate(ti.to_rows()):

        raw_alt_name = alt_col_name(c['header'], i)
        alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

        kwargs = {}

        if alt_name:
            kwargs['AltName'] = alt_name

        schema_term.new_child('Column', c['header'],
                              datatype=type_map.get(c['resolved_type'], c['resolved_type']),
                              # description = get_col_value(c['header'].lower(),'description'),
                              **kwargs)

    update_resource_properties(r, orig_columns=orig_columns, force=force)


def _process_metapack_resource(doc, r, force):

    remote_resource = r.resolved_url.resource

    if not remote_resource:
        warn('Metatab resource could not be resolved from {}'.format(r.resolved_url))
        return

    remote_st = remote_resource.schema_term

    schema_term = r.schema_term

    if schema_term:

        prt("Updating table '{}' ".format(r.schema_name))

        # Remove existing columns, so add them back later, possibly in a new order
        for child in list(schema_term.children):
            schema_term.remove_child(child)

    else:
        prt("Adding table '{}' ".format(r.schema_name))
        schema_term = doc['Schema'].new_term('Table', r.schema_name)

    for c in remote_st.children:
        schema_term.add_child(c)


def update_schema_properties(doc, force=False):
    for r in doc['Resources'].find('Root.Resource'):
        update_resource_properties(r, force=False)


def update_resource_properties(r, orig_columns={}, force=False):
    """Get descriptions and other properties from this, or upstream, packages, and add them to the schema. """

    added = []

    schema_term = r.schema_term

    if not schema_term:
        warn("No schema term for ", r.name)
        return

    rg = r.raw_row_generator

    # Get columns information from the schema, or, if it is a package reference,
    # from the upstream schema

    upstream_columns = {e['name'].lower() if e['name'] else '': e for e in r.columns() or {}}

    # Just from the local schema
    schema_columns = {e['name'].lower() if e['name'] else '': e for e in r.schema_columns or {}}

    # Ask the generator if it can provide column descriptions and types
    generator_columns = {e['name'].lower() if e['name'] else '': e for e in rg.columns or {}}

    def get_col_value(col_name, value_name):

        v = None

        if not col_name:
            return None

        for d in [generator_columns, upstream_columns, orig_columns, schema_columns]:
            v_ = d.get(col_name.lower(), {}).get(value_name)
            if v_:
                v = v_

        return v

    # Look for new properties
    extra_properties = set()
    for d in [generator_columns, upstream_columns, orig_columns, schema_columns]:
        for k, v in d.items():
            for kk, vv in v.items():
                extra_properties.add(kk)

    # Remove the properties that are already accounted for
    extra_properties = extra_properties - {'pos', 'header', 'name', ''}

    # Add any extra properties, such as from upstream packages, to the schema.

    for ep in extra_properties:
        r.doc['Schema'].add_arg(ep)

    for c in schema_term.find('Table.Column'):

        for ep in extra_properties:
            t = c.get_or_new_child(ep)
            v = get_col_value(c.name, ep)
            if v:
                t.value = v
                added.append((c.name, ep, v))

    prt('Updated schema for {}. Set {} properties'.format(r.name, len(added)))


def extract_path_name(ref):
    from os.path import basename
    from os.path import splitext, abspath

    from rowgenerators import parse_app_url

    uparts = parse_app_url(ref)

    ss = parse_app_url(ref)

    if not uparts.scheme:
        path = abspath(ref)
        name = basename(splitext(path)[0])
    else:
        path = ref

        v = ss.target_file if ss.target_file else uparts.path

        name = basename(splitext(v)[0])

    return path, name


def alt_col_name(name, i):
    import re

    if not name:
        return 'col{}'.format(i)

    return re.sub('_+', '_', re.sub('[^\w_]', '_', str(name)).lower()).rstrip('_')


type_map = {
    float.__name__: 'number',
    int.__name__: 'integer',
    bytes.__name__: 'string',
    str.__name__: 'text',

    # Numpy types
    'datetime64[ns]': 'datetime'
}


class MetapackCliMemo(object):
    def __init__(self, args, downloader):
        from os import getcwd
        from os.path import join

        self.cwd = getcwd()
        self.args = args

        self.downloader = downloader

        self.cache = self.downloader.cache

        self.config = get_config()

        frag = ''

        if isinstance(args.metatabfile, (list, tuple)):
            args.metatabfile = args.metatabfile.pop(0)

        # Just the fragment was provided
        if args.metatabfile and args.metatabfile.startswith('#'):
            frag = args.metatabfile
            mtf = None
        else:
            frag = ''
            mtf = args.metatabfile

        # If could not get it from the args, Set it to the default file name in the current dir
        if not mtf:
            mtf = join(self.cwd, DEFAULT_METATAB_FILE)

            if not Path(mtf).exists():
                mtf = join(self.cwd, LINES_METATAB_FILE)

            if not Path(mtf).exists():
                mtf = join(self.cwd, IPYNB_METATAB_FILE)

        self.init_stage2(mtf, frag)

        self._doc = None

    def init_stage2(self, mtf, frag):
        from metapack import MetapackUrl
        from rowgenerators import parse_app_url

        self.frag = frag

        self.mtfile_arg = mtf + frag

        u = parse_app_url(self.mtfile_arg, downloader=self.downloader)

        if u.scheme == 'index':
            self.mtfile_url = MetapackUrl(u.resolve(), downloader=self.downloader)
        else:

            if u.scheme == 'file':
                self.mtfile_url = MetapackUrl(u.absolute(), downloader=self.downloader)
            else:
                self.mtfile_url = MetapackUrl(self.mtfile_arg, downloader=self.downloader)

        self.resource = self.mtfile_url.resource_name

        # This is probably a bug in AppUrl, but I'm not sure.
        if self.mtfile_url.resource_format == 'zip' and self.resource == 'metadata.csv':
            self.resource = None

        self.package_url = self.mtfile_url.package_url
        self.mt_file = self.mtfile_url.metadata_url

        if hasattr(self.args, 'build_directory') and self.args.build_directory:
            self.package_root = parse_app_url(self.args.build_directory)
        else:
            self.package_root = self.package_url.join(PACKAGE_PREFIX)

        assert self.package_root._downloader

    @property
    def doc(self):
        from metapack import MetapackDoc
        if self._doc is None:
            self._doc = MetapackDoc(self.mt_file)

        return self._doc

    def get_resource(self):
        return get_resource(self)


def get_resource(m):
    if m.resource:
        r = m.doc.resource(m.resource)
        return r if r else m.doc.reference(m.resource)
    elif hasattr(m.args, 'resource') and m.args.resource:
        return m.doc.resource(m.args.resource)
    elif hasattr(m.args, 'reference') and m.args.reference:
        return m.doc.reference(m.args.reference)
    else:
        return None


def get_config():
    """Return a configuration dict"""
    from os import environ
    from os.path import expanduser
    from pathlib import Path
    import yaml

    def pexp(p):
        try:
            return Path(p).expanduser()
        except AttributeError:
            # python 3.4
            return Path(expanduser(p))

    paths = [environ.get("METAPACK_CONFIG"), '~/.metapack.yaml', '/etc/metapack.yaml']

    for p in paths:

        if not p:
            continue

        p = pexp(p)

        if p.exists():
            with p.open() as f:
                config = yaml.safe_load(f)
                if not config:
                    config = {}

                config['_loaded_from'] = str(p)
                return config

    return None


def update_index(packages, package_path, suffix=''):
    from os import listdir
    from os.path import join, exists, isdir, splitext

    raise DeprecationWarning()

    if packages:
        # Just update one packages
        add_package_to_index(package_path, packages, suffix=suffix)

    else:
        # Build the whole package index
        packages = []

        def yield_packages(d):

            for e in listdir(d):
                path = join(d, e)
                bn, ext = splitext(path)
                if isdir(path):
                    if exists(join(path, 'metadata.csv')):
                        yield join(path, 'metadata.csv')
                elif ext in ('.xls', '.xlsx', '.zip'):
                    yield path

        for p in yield_packages(package_path):
            add_package_to_index(p, packages, suffix=None)

    return packages


def new_search_index():
    return []


def list_rr(doc):
    d = []
    for r in doc.resources():
        d.append(('Resource', '#' + r.name, r.url))

    for r in doc.references():
        d.append(('Reference', '#' + r.name, r.url))

    prt(tabulate(d, 'Type Ref Url'.split()))


def find_packages(name, pkg_dir):
    from metapack_build.package import FileSystemPackageBuilder, ZipPackageBuilder, ExcelPackageBuilder

    """Locate pre-built packages in the _packages directory"""
    for c in (FileSystemPackageBuilder, ZipPackageBuilder, ExcelPackageBuilder):

        package_path, cache_path = c.make_package_path(pkg_dir, name)

        if package_path.exists():
            yield c.type_code, package_path, cache_path  # c(package_path, pkg_dir)


def md5_file(filePath):
    import hashlib

    with open(filePath, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
