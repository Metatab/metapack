import logging
import shutil
import sys
from itertools import islice
from os import getenv, listdir
from os.path import join, exists, isdir, splitext, abspath
from uuid import uuid4

import six
from metapack import MetapackDoc, MetapackUrl
from metapack.appurl import SearchUrl
from metapack.package import *
from metapack.util import ensure_dir
from metatab import DEFAULT_METATAB_FILE
from metatab.util import make_metatab_file
from rowgenerators import SelectiveRowGenerator, parse_app_url, AppUrlError
from tableintuit import TypeIntuiter


logger = logging.getLogger('user')
logger_err = logging.getLogger('cli-errors')
debug_logger = logging.getLogger('debug')

def cli_init(log_level=logging.INFO):

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

    try:
        search_func = SearchUrl.search_json_indexed_directory(Downloader().cache.getsyspath('/'))
        SearchUrl.register_search(search_func)
    except AppUrlError as e:

        pass

def prt(*args, **kwargs):
    logger.info(' '.join(str(e) for e in args),**kwargs)

def warn(*args, **kwargs):
    logger_err.warn(' '.join(str(e) for e in args),**kwargs)

def err(*args, **kwargs):
    logger_err.critical(' '.join(str(e) for e in args),**kwargs)
    sys.exit(1)


def metatab_info(cache):
   pass


def new_metatab_file(mt_file, template):
    template = template if template else 'metatab'

    if not exists(mt_file):
        doc = make_metatab_file(template)

        doc['Root']['Identifier'] = str(uuid4())

        doc.write_csv(mt_file)


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

            w = csv.writer(sys.stdout if six.PY2 else sys.stdout.buffer)

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

PACKAGE_PREFIX = '_packages'

def make_excel_package(file, package_root, cache, env, skip_if_exists):

    assert package_root

    p = ExcelPackageBuilder(file, package_root, callback=prt,  env=env)
    prt('Making Excel Package')

    if not p.exists() or not skip_if_exists:
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():
        prt("Excel Package already exists")
        created = False
        url = p.package_path.path

    return p, MetapackUrl(url, downloader=package_root.downloader), created


def make_zip_package(file, package_root, cache, env, skip_if_exists):

    assert package_root


    p = ZipPackageBuilder(file, package_root, callback=prt,  env=env)
    prt('Making ZIP Package')
    if not p.exists() or not skip_if_exists:
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():
        prt("ZIP Package already exists")
        created = False
        url = p.package_path.path

    return p, MetapackUrl(url, downloader=package_root.downloader), created


def make_filesystem_package(file, package_root, cache, env, skip_if_exists):

    assert package_root

    p = FileSystemPackageBuilder(file, package_root, callback=prt, env=env)

    if skip_if_exists is None:
        skip_if_exists = p.is_older_than_metatada()

    if not p.exists() or not skip_if_exists:
        prt('Making Filesystem Package ',
            '; existing package is older than metadata {}'.format(file) if (p.exists() and not skip_if_exists) else '')
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():

        prt("Filesystem Package already exists")
        created = False
        url = join(p.package_path.path.rstrip('/'), DEFAULT_METATAB_FILE)

    return p, MetapackUrl(url, downloader=package_root.downloader), created


def make_csv_package(file, package_root, cache, env, skip_if_exists):
    assert package_root

    p = CsvPackageBuilder(file, package_root, callback=prt,  env=env)
    prt('Making CSV Package')
    if not p.exists() or not skip_if_exists:
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():
        prt("CSV Package already exists")
        created = False
        url = p.package_path.path

    return p, MetapackUrl(url, downloader=package_root.downloader), created

def make_s3_package(file, package_root,  cache,  env,  skip_if_exists, acl='public-read'):

    assert package_root

    p = S3PackageBuilder(file, package_root, callback=prt,  env=env, acl=acl)

    if not p.exists() or not skip_if_exists:
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():
        prt("S3 Filesystem Package already exists")
        created = False
        url = p.access_url

    return p, MetapackUrl(url, downloader=file.downloader), created



def update_name(mt_file, fail_on_missing=False, report_unchanged=True, force=False):

    if isinstance(mt_file, MetapackDoc):
        doc = mt_file
    else:
        doc = MetapackDoc(mt_file)

    o_name = doc.find_first_value("Root.Name", section=['Identity', 'Root'])

    updates = doc.update_name(force=force)

    for u in updates:
        prt(u)

    prt("Name is: ", doc.find_first_value("Root.Name", section=['Identity', 'Root']))

    if o_name != doc.find_first_value("Root.Name", section=['Identity', 'Root']) or force:
        write_doc(doc, mt_file)


def write_doc(doc, mt_file):
    """
    Write a Metatab doc to a CSV file, and update the Modified time
    :param doc:
    :param mt_file:
    :return:
    """


    import subprocess

    try:
        out = subprocess.run(['git', 'remote', 'show','origin'], stdout=subprocess.PIPE, timeout=6)\
            .stdout.decode('utf-8')

        fetchline = next(l.split() for l in out.splitlines() if 'Fetch' in l )
    except (TimeoutError, StopIteration, subprocess.TimeoutExpired):
        fetchline = None

    if fetchline:
        t = doc['Root'].get_or_new_term('GitUrl')
        t.value = fetchline[-1]

    u = parse_app_url(mt_file)

    if u.scheme == 'file':
        doc.write_csv(mt_file)
        return True
    else:
        return False
        #warn("Not writing back to url ", mt_file)


def process_schemas(mt_file, cache=None, clean=False):
    from rowgenerators import SourceError, SchemaError
    from requests.exceptions import ConnectionError

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
        doc.new_section('Schema', ['DataType', 'Altname', 'Description'])

    for r in doc['Resources'].find('Root.Resource'):

        schema_term = r.schema_term

        col_count = len(list(r.columns()))
        datatype_count = sum(1 for c in r.columns() if c['datatype'])

        if schema_term and col_count == datatype_count:
            prt("Found table for '{}'; skipping".format(r.schema_name))
            continue

        if col_count != datatype_count:
            prt(f"Found table for '{r.schema_name}'; but {col_count-datatype_count} columns don't have datatypes")

        prt("Processing {}".format(r.name))

        try:
            slice = islice(r.row_generator, 500)
        except SchemaError:
            warn("Failed to build row processor table, using raw row generator")
            slice = islice(r.raw_row_generator, 500)

        si = SelectiveRowGenerator(slice,
                                   headers=[int(i) for i in r.get_value('headerlines', '0').split(',')],
                                   start=int(r.get_value('startline', 1)))

        try:
            ti = TypeIntuiter().run(si)
        except SourceError as e:
            warn("Failed to process resource '{}'; {}".format(r.name, e))
            continue
        except ConnectionError as e:
            warn("Failed to download resource '{}'; {}".format(r.name, e))
            continue

        if schema_term:
            table = schema_term
            prt("Updating table '{}' ".format(r.schema_name))

            col_map = { c.name.lower():c for c in table.children if c.term_is('Table.Column')}

            for i, c in enumerate(ti.to_rows()):
                extant = col_map.get(c['header'])
                if extant:
                    extant.datatype = type_map.get(c['resolved_type'], c['resolved_type'])

        else:

            table = doc['Schema'].new_term('Table', r.schema_name)
            prt("Adding table '{}' ".format(r.schema_name))

            for i, c in enumerate(ti.to_rows()):

                raw_alt_name = alt_col_name(c['header'], i)
                alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

                t = table.new_child('Column', c['header'],
                                datatype=type_map.get(c['resolved_type'], c['resolved_type']),
                                altname=alt_name)

    if write_doc_to_file:
        write_doc(doc, mt_file)


def extract_path_name(ref):
    from os.path import splitext, basename, abspath

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
    six.text_type.__name__: 'string',
    six.binary_type.__name__: 'text',

}


class MetapackCliMemo(object):
    def __init__(self, args, downloader):
        from os import getcwd

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


        self.init_stage2(mtf, frag)


    def init_stage2(self, mtf, frag):

        self.frag = frag
        self.mtfile_arg = mtf + frag

        self.mtfile_url = MetapackUrl(self.mtfile_arg, downloader=self.downloader)

        # Find the target for a search URL
        if self.mtfile_url.scheme =='index':
            self.mtfile_url = parse_app_url(self.mtfile_arg, downloader=self.downloader).get_resource()

        self.resource = self.mtfile_url.resource_name

        self.package_url = self.mtfile_url.package_url
        self.mt_file = self.mtfile_url.metadata_url

        assert self.package_url.scheme == 'file'
        self.package_root = self.package_url.join(PACKAGE_PREFIX)
        assert self.package_root._downloader

    @property
    def doc(self):
        return MetapackDoc(self.mt_file)

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

    paths = [ environ.get("METAPACK_CONFIG"),'~/.metapack.yaml','/etc/metapack.yaml']

    for p in paths:
        try:
            if pexp(p).exists():
                with  pexp(p).open() as f:
                    config = yaml.safe_load(f)
                    config['_loaded_from'] = str(pexp(p) )
                    return config
        except TypeError:
            pass


    return {}

def add_package_to_index(pkg, package_db):

    ref_url = pkg.package_url.clone()
    ref_url.path = abspath(ref_url.path)

    ref = str(ref_url).encode('utf8')

    package_db[pkg.get_value('Root.Identifier')] = ref # identifier

    nv_name =(pkg._generate_identity_name(mod_version=None)) # Non versioned-name, for the latest package

    try:
        # JSON stores strings, DBM stores bytes
        try:
            max_package = open_package(package_db[nv_name].decode('utf8'))
        except AttributeError:
            max_package = open_package(package_db[nv_name])

        if max_package and max_package.get_value('Root.Version') < pkg.get_value('Root.Version'):
            max_package_ref = ref
        else:
            max_package_ref = package_db[nv_name]

    except (KeyError, ValueError):
        max_package_ref = ref

    package_db[pkg._generate_identity_name()] = max_package_ref
    package_db[nv_name] = max_package_ref

    return [pkg.get_value('Root.Identifier'), pkg._generate_identity_name(), nv_name]

def update_index(packages, package_path, suffix=''):


    if packages:
        # Just update one packages
        add_package_to_index(package_path, packages, suffix=suffix)

    else:
        # Build the whole package index
        packages = {}

        def yield_packages(d):

            for e in listdir(d):
                path = join(d, e)
                bn, ext = splitext(path)
                if isdir(path):
                    if exists(join(path, 'metadata.csv')):
                        yield join(path, 'metadata.csv')
                elif ext in ('.xls', '.xlsx', '.zip'):
                    yield path

        for p in yield_packages(d):
            add_package_to_index(p, packages, suffix=None)



    return packages





