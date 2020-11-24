import logging
from pathlib import Path

from metatab import (
    DEFAULT_METATAB_FILE,
    IPYNB_METATAB_FILE,
    LINES_METATAB_FILE
)
from tabulate import tabulate

from metapack.constants import PACKAGE_PREFIX
from metapack.doc import MetapackDoc

logger = logging.getLogger('user')
logger_err = logging.getLogger('cli-errors')
debug_logger = logging.getLogger('debug')
download_logger = logging.getLogger('rowgenerators.appurl.web.download')


def cli_init(log_level=logging.INFO):
    import sys

    from metapack.appurl import SearchUrl

    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter('%(message)s'))
    out_hdlr.setLevel(log_level)
    logger.addHandler(out_hdlr)
    logger.setLevel(log_level)

    out_hdlr = logging.StreamHandler(sys.stderr)
    out_hdlr.setFormatter(logging.Formatter('%(message)s'))
    out_hdlr.setLevel(logging.WARN)
    logger_err.addHandler(out_hdlr)
    logger_err.setLevel(logging.WARN)

    def set_debug_out_handler(logger, log_level):
        out_hdlr = logging.StreamHandler(sys.stdout)
        out_hdlr.setFormatter(logging.Formatter('DEBUG: %(message)s'))
        out_hdlr.setLevel(log_level)
        logger.addHandler(out_hdlr)
        logger.setLevel(log_level)

    set_debug_out_handler(debug_logger, log_level)
    set_debug_out_handler(download_logger, log_level)

    SearchUrl.initialize()  # Setup the JSON index search.


def prt(*args, **kwargs):
    logger.info(' '.join(str(e) for e in args), **kwargs)


def warn(*args, **kwargs):
    logger_err.warning('⚠️ ' + ' '.join(str(e) for e in args), **kwargs)


def err(*args, **kwargs):
    import sys
    logger_err.critical('❌ ' + ' '.join(str(e) for e in args), **kwargs)
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


def update_name(mt_file, fail_on_missing=False, report_unchanged=True, force=False,
                mod_version=False):
    from metapack import MetapackDoc

    if isinstance(mt_file, MetapackDoc):
        doc = mt_file
    else:
        doc = MetapackDoc(mt_file)

    o_name = doc.find_first_value("Root.Name", section=['Identity', 'Root'])

    updates = doc.update_name(force=force, report_unchanged=report_unchanged,
                              mod_version=mod_version)

    for u in updates:
        prt(u)

    prt("Name is: ", doc.find_first_value("Root.Name", section=['Identity', 'Root']))

    if o_name != doc.find_first_value("Root.Name", section=['Identity', 'Root']) or force:
        write_doc(doc, mt_file)


def add_giturl(doc: MetapackDoc, force=False):
    import subprocess

    if not doc['Root'].find('GitUrl') or force:

        try:
            out = subprocess.run(['git', 'remote', 'show', 'origin'], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, timeout=6) \
                .stdout.decode('utf-8')

            fetchline = next(l.split() for l in out.splitlines() if 'Fetch' in l)

        except (TimeoutError, StopIteration, subprocess.TimeoutExpired, FileNotFoundError) as e:
            fetchline = None
            if force:
                err(str(e))

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

            if not Path(mtf).exists():
                mtf = '.'

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
        elif str(self.package_url) == str(self.mt_file):  # specified the metadata file, not metadata.csv in a dir
            self.package_root = parse_app_url(str(self.package_url.fspath.parent.joinpath(PACKAGE_PREFIX)))
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

    @property
    def filesystem_package(self):
        """Return a FileSystemPackage object"""
        from metapack_build.package import FileSystemPackageBuilder

        return FileSystemPackageBuilder(self.mt_file, self.package_root)


def get_resource(m):
    if m.resource:
        r = m.doc.resource(m.resource)

        if r:
            return r

        r = m.doc.reference(m.resource)

        if r:
            return r

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


def list_rr(doc):
    d = []
    for r in doc.resources():
        d.append(('Resource', '#' + r.name, r.url))

    for r in doc.references():
        d.append(('Reference', '#' + r.name, r.url))

    prt(tabulate(d, 'Type Ref Url'.split()))


def find_packages(name, pkg_dir):
    """Locate pre-built packages in the _packages directory"""

    from metapack_build.package import FileSystemPackageBuilder, ZipPackageBuilder, ExcelPackageBuilder

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
