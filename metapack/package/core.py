# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """

from collections import namedtuple
from genericpath import exists
from hashlib import sha1
from itertools import islice
from os import walk
from os.path import dirname, abspath, basename, splitext, join, isdir
from time import time

import unicodecsv as csv  # legacy; shoudl convert to csv package.
from metapack.appurl import MetapackUrl, MetapackPackageUrl
from metapack.exc import PackageError
from metapack.terms import Resource
from metapack.util import Bunch
from metatab import DEFAULT_METATAB_FILE
from rowgenerators import Downloader as _Downloader, get_generator, parse_app_url
from rowgenerators.util import slugify
from tableintuit import RowIntuiter

DEFAULT_CACHE_NAME = 'metapack'

class Downloader(_Downloader):
    """"Local version of the downloader. Also should be used as the source of the cache"""

    ok = True

    def __init__(self, cache=None, account_accessor=None, logger=None, working_dir='', callback=None):
        from rowgenerators import get_cache
        super().__init__(cache or get_cache('metapack'),
                         account_accessor, logger, working_dir, callback)

    def download(self, url):
        return super().download(url)

class PackageBuilder(object):

    type_code = 'unk'
    type_suffix = ''

    def __init__(self, source_ref=None, package_root = None,  callback=None, env=None):
        from metapack.doc import MetapackDoc

        self._downloader = source_ref._downloader
        self._cache = self._downloader.cache

        self._source_ref = source_ref
        self.source_dir = dirname(parse_app_url(self._source_ref).path)

        self.package_root = package_root
        self._callback = callback
        self._env = env if env is not None else {}

        self._source_doc = MetapackDoc(self._source_ref, cache=self._cache) # this one stays constant

        self._doc = MetapackDoc(self._source_ref, cache=self._cache) # This one gets edited

        self._last_write_path = None

        if not self.doc.find_first_value('Root.Name'):
            raise PackageError("Package must have Root.Name term defined")

    @property
    def path(self):
        return self._source_ref

    @property
    def source_url(self):
        return parse_app_url(self._source_ref)


    def exists(self):
        return self.package_path.exists()

    @property
    def doc(self):
        return self._doc

    def copy_section(self, section_name, doc):

        for t in doc[section_name]:
            self.doc.add_term(t)

    def resources(self, name=None, term=None, section='resources'):

        for r in self.doc['Resources'].find('root.resource'):
            yield r


    @property
    def datafiles(self):
        """Iterate over data file *in the original document*. Don't alter these! """
        for r in self._source_doc['Resources'].find(['root.datafile',
                                                     'root.suplimentarydata',
                                                     'root.datadictionary',
                                                     'root.sql']):
            yield r

    def datafile(self, ref):
        """Return a resource, as a file-like-object, given it's name or url as a reference.

        Returns from the editable document copy.
        """

        return self.doc.resource(ref)

    @property
    def documentation(self):
        for t in self.doc._terms:
            if t.term_is(['root.documentation']):
                yield Resource(t, self)

    def schema(self, ref):
        """Return information about a resource, given a name or url"""
        raise NotImplementedError()

    @property
    def package_name(self):
        return slugify(self.doc.get_value('Root.Name'))

    @property
    def nv_package_name(self):
        """Non versioned package name"""
        return slugify(self.doc.as_version(None))

    @property
    def sections(self):

        class _Sections(object):

            def __init__(self, doc):
                self.doc = doc

            @property
            def root(self):
                return self.doc['root']

            @property
            def resources(self):
                if not 'resources' in self.doc:
                    self.doc.get_or_new_section('Resources',
                                                "Name Schema Space Time StartLine HeaderLines Encoding Description".split())

                return self.doc['resources']

            @property
            def contacts(self):
                if not 'Contacts' in self.doc:
                    self.doc.get_or_new_section('Contacts', 'Email Org Url'.split())

                return self.doc['Contacts']

            @property
            def documentation(self):
                if not 'Documentation' in self.doc:
                    self.doc.get_or_new_section('Documentation', 'Title Schema Description '.split())

                return self.doc['documentation']

            @property
            def schema(self):
                if not 'Schema' in self.doc:
                    self.doc.get_or_new_section('Schema', 'DataType AltName Description'.split())

                return self.doc['schema']

        return _Sections(self._doc)

    @staticmethod
    def extract_path_name(ref):

        du = parse_app_url(ref)

        if du.proto == 'file':
            path = abspath(ref)
            name = basename(splitext(path)[0])
            ref = "file://" + path
        else:
            path = ref

            if du.target_segment:
                try:
                    int(du.target_segment)
                    name = du.target_file + str(du.target_segment)

                except ValueError:
                    name = du.target_segment

            else:
                name = splitext(du.target_file)[0]

        return ref, path, name

    @staticmethod
    def classify_url(url):

        ss = parse_app_url(url=url)

        if ss.format in ('xls', 'xlsx', 'tsv', 'csv'):
            term_name = 'DataFile'
        elif ss.format in ('pdf', 'doc', 'docx', 'html'):
            term_name = 'Documentation'
        else:
            term_name = 'Resource'

        return term_name

    @staticmethod
    def run_row_intuit(url, cache):

        for encoding in ('ascii', 'utf8', 'latin1'):

            rows = list(islice(get_generator(url), 5000))
            return encoding, RowIntuiter().run(list(rows))


        raise Exception('Failed to convert with any encoding')

    @staticmethod
    def find_files(base_path, types):

        for root, dirs, files in walk(base_path):
            if '_metapack' in root:
                continue

            for f in files:
                if f.startswith('_'):
                    continue

                b, ext = splitext(f)
                if ext[1:] in types:
                    yield join(root, f)

    def load_declares(self):

        self.doc.load_declarations(t.value for t in self.doc.find('Root.Declare'))

    def prt(self, *args):
        if self._callback:
            self._callback(*args)

    def warn(self, *args):
        if self._callback:
            self._callback('WARN', *args)

    def err(self, *args):
        if self._callback:
            self._callback('ERROR', *args)

    def add_single_resource(self, ref, **properties):
        """ Add a single resource, without trying to enumerate it's contents
        :param ref:
        :return:
        """

        t = self.doc.find_first('Root.Datafile', value=ref)

        if t:
            self.prt("Datafile exists for '{}', deleting".format(ref))
            self.doc.remove_term(t)

        term_name = self.classify_url(ref)

        ref, path, name = self.extract_path_name(ref)

        self.prt("Adding resource for '{}'".format(ref))

        try:
            encoding, ri = self.run_row_intuit(path, self._cache)
        except Exception as e:
            self.warn("Failed to intuit '{}'; {}".format(path, e))
            return None

        if not name:

            name = sha1(slugify(path).encode('ascii')).hexdigest()[:12]

            # xlrd gets grouchy if the name doesn't start with a char
            try:
                int(name[0])
                name = 'a' + name[1:]
            except:
                pass

        if 'name' in properties:
            name = properties['name']
            del properties['name']

        return self.sections.resources.new_term(term_name, ref, name=name,
                                                startline=ri.start_line,
                                                headerlines=','.join(str(e) for e in ri.header_lines),
                                                encoding=encoding,
                                                **properties)

    def add_resource(self, ref, **properties):
        """Add one or more resources entities, from a url and property values,
        possibly adding multiple entries for an excel spreadsheet or ZIP file"""

        raise NotImplementedError("Still uses decompose_url")

        du = Bunch(decompose_url(ref))

        added = []
        if du.proto == 'file' and isdir(ref):
            for f in self.find_files(ref, ['csv']):

                if f.endswith(DEFAULT_METATAB_FILE):
                    continue

                if self._doc.find_first('Root.Datafile', value=f):
                    self.prt("Datafile exists for '{}', ignoring".format(f))
                else:
                    added.extend(self.add_resource(f, **properties))
        else:
            self.prt("Enumerating '{}'".format(ref))

            for c in enumerate_contents(ref, self._cache):
                added.append(self.add_single_resource(c.rebuild_url(), **properties))

        return added

    def _clean_doc(self, doc=None):
        """Clean the doc before writing it, removing unnecessary properties and doing other operations."""

        if doc is None:
            doc = self.doc

        resources = doc['Resources']

        # We don't need these anymore because all of the data written into the package is normalized.
        for arg in ['startline', 'headerlines', 'encoding']:
            for e in list(resources.args):
                if e.lower() == arg:
                    resources.args.remove(e)

        for term in resources:
            term['startline'] = None
            term['headerlines'] = None
            term['encoding'] = None

        schema = doc['Schema']

        ## FIXME! This is probably dangerous, because the section args are changing, but the children
        ## are not, so when these two are combined in the Term.properties() acessors, the values are off.
        ## Because of this, _clean_doc should be run immediately before writing the doc.
        for arg in ['altname', 'transform']:
            for e in list(schema.args):
                if e.lower() == arg:
                    schema.args.remove(e)

        for table in self.doc.find('Root.Table'):
            for col in table.find('Column'):
                try:
                    col.value = col['altname'].value
                except:
                    pass

                col['altname'] = None
                col['transform'] = None

        # Remove any DSNs

        #for dsn_t in self.doc.find('Root.Dsn'):
        #    self.doc.remove_term(dsn_t)


        return doc

    def _load_resources(self, abs_path=False):
        """Copy all of the Datafile entries into the package"""
        from metapack.doc import MetapackDoc

        assert type(self.doc) == MetapackDoc

        for r in self.datafiles:

            if r.term_is('root.sql'):

                if not r.value:
                    self.warn("No value for SQL URL for {} ".format(r.term))
                    continue

                try:
                    self._load_resource(r, abs_path)
                except Exception as e:
                    if r.props.get('ignoreerrors'):
                        self.warn(f"Ignoring errors for {r.name}: {str(e)}")
                        pass
                    else:
                        raise e

            else:

                if not r.url:
                    self.warn("No value for URL for {} ".format(r.term))
                    continue

                try:
                    if self._resource.exists(r):
                        self.prt("Resource '{}' exists, skipping".format(r.name))
                    continue
                except AttributeError:
                    pass

                self.prt("Reading resource {} from {} ".format(r.name, r.resolved_url))

                try:
                    if not r.headers:
                        raise PackageError("Resource {} does not have header. Have schemas been generated?"
                                            .format(r.name))
                except AttributeError:
                    raise PackageError("Resource '{}' of type {} does not have a headers property"
                                       .format(r.url, type(r)))

                try:
                    self._load_resource(r, abs_path)
                except Exception as e:
                    if r.props.get('ignoreerrors'):
                        self.warn(f"Ignoring errors for {r.name}: {str(e)}")
                        pass
                    else:
                        raise e

    def _load_resource(self, source_r, abs_path):
        raise NotImplementedError()

    def write_csv(self, path_or_flo, headers, gen):

        try:
            f = open(path_or_flo, "wb")

        except TypeError:
            f = path_or_flo  # Assume that it's already a file-like-object

        last_time = start_time = time()
        i = 0
        try:
            w = csv.writer(f)
            w.writerow(headers)

            row = None
            try:
                for row in gen:
                    w.writerow(row)
                    i += 1

                    if time() - last_time > 25:
                        dt = time()-start_time
                        rate = float(i)/(dt)
                        self.prt(f'Processed {i} rows in {round(dt,0)} sec, rate = {round(rate,2)} rows/sec')
                        last_time = time()

            except:
                import sys
                print("write_csv: ERROR IN ROW", row, file=sys.stderr)
                raise

            try:
                return f.getvalue()
            except AttributeError:
                return None

        finally:
            dt = time() - start_time
            rate = round((float(i) / (dt)),2) if dt != 0 else 'undef'
            self.prt(f'Processed {i} rows in {round(dt,0)} sec, rate = {rate} rows/sec')
            f.close()

    def _get_ref_contents(self, t, working_dir=None):

        uv = parse_app_url(t.value, working_dir=abspath(self.source_dir))

        # In the case that the input doc is a file, and the ref is to a file,
        # try interpreting the file as relative.
        if self.source_url.proto == 'file' and uv.proto == 'file':
            u = self.source_url.join_dir(uv)
        else:
            u = uv

        return u.get_resource() if u else None

    def _load_documentation_files(self):
        """Copy all of the Datafile entries into the Excel file"""

        for doc in self.doc.find(['Root.Documentation', 'Root.Image', 'Root.IncludeDocumentation']):

            resource = self._get_ref_contents(doc)

            if not resource:
                continue

            if doc.term_is('Root.Documentation'):
                # Prefer the slugified title to the base name, because in cases of collections
                # of many data releases, like annual datasets, documentation files may all have the same name,
                # but the titles should be different.
                real_name_base, ext = splitext(resource.resource_file)

                name = doc.get_value('name') if doc.get_value('name') else real_name_base
                real_name = slugify(name) + ext

            self._load_documentation(doc, resource.read(), resource.resource_file)

    def _load_documentation(self, term, contents):
        raise NotImplementedError()

    def _load_files(self):
        """Load other files"""

        def copy_dir(path):
            for (dr, _, files) in walk(path):
                for fn in files:

                    if '__pycache__' in fn:
                        continue

                    relpath = dr.replace(self.source_dir, '').strip('/')
                    src = parse_app_url(join(dr, fn))
                    dest = join(relpath, fn)

                    resource = src.get_resource()

                    self._load_file( dest, resource.read())

        for term in self.resources(term = 'Root.Pythonlib'):

            uv = parse_app_url(term.value)
            ur = parse_app_url(self.source_dir)

            # In the case that the input doc is a file, and the ref is to a file,
            # try interpreting the file as relative.
            if ur.proto == 'file' and uv.proto == 'file':

                # Either a file or a directory
                path = join(self.source_dir, uv.path)
                if isdir(path):
                    copy_dir(path)

            else:
                # Load it as a URL
                real_name, f = self._get_ref_contents(term)
                self._load_file(term.value,f.read() )

        nb_dir = join(self.source_dir, 'notebooks')

        if exists(nb_dir) and isdir(nb_dir):
            copy_dir(nb_dir)


    def _load_file(self,  filename, contents):
        raise NotImplementedError()


    def check_is_ready(self):
        pass

    def create_nv_link(self):
        """After a save(), write a link to the saved file using a non-versioned name"""
        from os.path import abspath, islink
        from os import unlink, symlink

        nv_name = self.doc.as_version(None)

        from_path =  abspath(self._last_write_path or self.package_path.path)

        to_path = join(dirname(from_path), nv_name + self.type_suffix)

        if islink(to_path):
            unlink(to_path)

        symlink(from_path, to_path)

    def move_to_nv_name(self):
        """After a save, move a file package to a non-versioned name"""

        from os.path import abspath, islink
        from os import unlink, rename

        nv_name = self.doc.as_version(None)

        from_path =  abspath(self._last_write_path or self.package_path.path)

        to_path = join(dirname(from_path), nv_name + self.type_suffix)

        rename(from_path, to_path)


    def is_older_than_metadata(self):
        """
        Return True if the package save file is older than the metadata. Returns False if the time of either can't be determined

        :param path: Optional extra save path, used in save_path()

        """
        from genericpath import getmtime


        try:
            path = self.path.path
        except AttributeError:
            path = self.path

        source_ref = self._doc.ref.path

        try:
            age_diff = getmtime(source_ref) - getmtime(path)

            return age_diff > 0

        except (FileNotFoundError, OSError):
            return False


TableColumn = namedtuple('TableColumn', 'path name start_line header_lines columns')


def open_package(ref, cache=None, clean_cache=False, downloader=None):
    from metapack.doc import MetapackDoc

    if downloader is None:
        downloader = Downloader()

    resource = None

    if isinstance(ref, MetapackUrl):
        u = ref
    else:

        ref = str(ref)

        if ref.startswith('index:'):
            from metapack.appurl import  SearchUrl
            SearchUrl.initialize()
            ref = str(parse_app_url(ref).resolve())

        u = MetapackUrl(ref, downloader=downloader)

        resource = u.resource

    cache = cache if cache else downloader.cache

    p = MetapackDoc(u, downloader=downloader)
    p.default_resource = resource
    return p


