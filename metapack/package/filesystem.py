# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """


import json
import shutil
from genericpath import exists, getmtime
from os import getcwd, makedirs, remove, getenv
from os.path import join, dirname, isdir

from nbconvert.writers import FilesWriter
from rowgenerators import parse_app_url
from metatab.datapackage import convert_to_datapackage
from metatab import DEFAULT_METATAB_FILE
from .core import PackageBuilder
from metapack.util import ensure_dir, write_csv, slugify, datetime_now
from metapack.appurl import MetapackUrl, SearchUrl
from metapack.util import slugify

def count_decl(doc):
    decls = doc.find('Root.Declare')
    assert len(doc.terms) == 0 or len(decls) == 1, (len(decls), len(doc.terms) )



class FileSystemPackageBuilder(PackageBuilder):
    """Build a filesystem package"""

    type_code = 'fs'
    type_suffix = ''

    def __init__(self, source_ref, package_root, callback=None, env=None, reuse_resources = False):

        super().__init__(source_ref, package_root,  callback, env)

        if not self.package_root.isdir():
            self.package_root.ensure_dir()

        self.reuse_resources = reuse_resources

        self.package_path, self.cache_path = self.make_package_path(self.package_root, self.package_name)

        self.doc_file = self.package_path.join(DEFAULT_METATAB_FILE)


    @classmethod
    def make_package_path(cls, package_root, package_name):

        cache_path = join(package_name, DEFAULT_METATAB_FILE)

        package_path = package_root.join(package_name)

        return package_path, cache_path

    def exists(self):

        try:
            path = self.doc_file.path
        except AttributeError:
            path = self.doc_file

        return self.package_path.isdir() and exists(path)

    def remove(self):

        if self.package_path.is_dir():
            shutil.rmtree(self.package_path.path)

    def package_build_time(self):
        from genericpath import getmtime


        try:
            path = self.doc_file.path
        except AttributeError:
            path = self.doc_file

        return getmtime(path)

    def is_older_than_metadata(self):
        """
        Return True if the package save file is older than the metadata. If it is, it should be rebuilt.  Returns
        False if the time of either can't be determined

        :param path: Optional extra save path, used in save_path()

        """

        try:
            path = self.doc_file.path
        except AttributeError:
            path = self.doc_file

        source_ref = self._doc.ref.path

        try:
            age_diff = getmtime(source_ref) - getmtime(path)

            return age_diff > 0

        except (FileNotFoundError, OSError):
            return False

    def save(self):

        self.check_is_ready()

        self.sections.resources.sort_by_term()

        self.doc.cleanse()

        self.load_declares()

        self._load_documentation_files()

        self._load_resources()

        self._load_files()

        self._write_dpj()

        self._clean_doc()

        doc_file = self._write_doc()

        self._write_html() # Why does this happen after _write_doc?

        return doc_file

    def _write_doc(self):

        self._doc['Root'].get_or_new_term('Root.Issued').value = datetime_now()

        self._doc.write_csv(self.doc_file)
        return MetapackUrl(self.doc_file, downloader=self._downloader)

    def _write_dpj(self):

        with open(join(self.package_path.path, 'datapackage.json'), 'w', encoding="utf-8") as f:
            f.write(json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _write_html(self):

        with open(join(self.package_path.path, 'index.html'), 'w', encoding="utf-8") as f:

            f.write(self._doc.html)

    def _load_resource(self, source_r, abs_path=False):
        """The CSV package has no resources, so we just need to resolve the URLs to them. Usually, the
            CSV package is built from a file system ackage on a publically acessible server. """

        from itertools import islice
        from metapack.exc import MetapackError
        from os.path import splitext

        # Refetch the resource ... IIRC b/c the source_r resource may actually be from
        # a different package. So r is the resource we want to possibly modify in this package,
        # while source_r is from a different souce package, whose data is being loaded into this
        # one.

        r = self.datafile(source_r.name)

        if self.reuse_resources:
            self.prt("Re-using data for '{}' ".format(r.name))
        else:
            self.prt("Loading data for '{}' ".format(r.name))

        if not r.name:
            raise MetapackError(f"Resource/reference term has no name: {str(r)}")

        # Special handing for SQL should not be done here; it should be done in Rowgenerators, probably.
        if r.term_is('root.sql'):
            new_r = self.doc['Resources'].new_term('Root.Datafile', '')
            new_r.name = r.name

            self.doc.remove_term(r)

            r = new_r

        r.url = 'data/' + r.name + '.csv' # Re-writing the URL for the resource.

        path = join(self.package_path.path, r.url)

        makedirs(dirname(path), exist_ok=True)

        if not self.reuse_resources or not exists(path):

            if self.reuse_resources:
                self.prt("Resource {} doesn't exist, rebuilding".format(path))

            if exists(path):
                remove(path)

            gen = islice(source_r, 1, None)
            headers = source_r.headers
            self.write_csv(path, headers, gen)

        for k, v in source_r.post_iter_meta.items():
            r[k] = v

        try:
            if source_r.errors:
                for col_name, errors in source_r.errors.items():
                    self.warn("ERRORS for column '{}' ".format(col_name))
                    for e in islice(errors,5):
                        self.warn('   {}'.format(e))
                    if len(errors) > 5:
                        self.warn("... and {} more ".format(len(errors)-5))
        except AttributeError:
            pass # Maybe generator does not track errors

        if source_r.errors:
            self.err("Resource processing generated conversion errors")

        # Writing between resources so row-generating programs and notebooks can
        # access previously created resources. We have to clean the doc before writing it

        ref = self._write_doc()

        # What a wreck ... we also have to get rid of the 'Transform' values, since the CSV files
        # that are written don't need them, and a lot of intermediate processsing ( specifically,
        # jupyter Notebooks, ) does not load them.
        p = FileSystemPackageBuilder(ref, self.package_root)
        p._clean_doc()

        ref = p._write_doc()

    def _load_documentation_files(self):

        from metapack.jupyter.exporters import DocumentationExporter

        notebook_docs = []

        # First find and remove notebooks from the docs. These wil get processed to create
        # normal documents.
        try:
            for term in list(self.doc['Documentation'].find('Root.Documentation')):
                u = parse_app_url(term.value)
                if u.target_format == 'ipynb' and u.proto == 'file':
                    notebook_docs.append(term)
                    self.doc.remove_term(term)
        except KeyError:
            self.warn("No documentation defined in metadata")

        # Process all of the normal files
        super()._load_documentation_files()

        fw = FilesWriter()
        fw.build_directory = join(self.package_path.path,'docs')

        # Now, generate the notebook documents directly into the filesystem package
        for term in notebook_docs:

            de = DocumentationExporter(base_name=term.name or slugify(term.title))

            u = parse_app_url(term.value)

            nb_path = join(self.source_dir, u.path) # Only works if the path is relative.

            try:
                output, resources = de.from_filename(nb_path)
                fw.write(output, resources, notebook_name=de.base_name+'_full') # Write notebook html with inputs

                de.update_metatab(self.doc, resources)
            except Exception as e:
                from metapack.cli.core import warn
                warn("Failed to convert document for {}: {}".format(term.name, e))


    def _load_documentation(self, term, contents, file_name):
        """Load a single documentation entry"""

        try:
            title = term['title'].value
        except KeyError:
            self.warn("Documentation has no title, skipping: '{}' ".format(term.value))
            return

        if term.term_is('Root.Readme'): # This term type has inline content, not a url
            package_sub_dir = 'docs'
        else:
            try:
                eu = term.expanded_url
                parsed_url = term.parsed_url
            except AttributeError:
                parsed_url = eu = parse_app_url(term.value)

            # Can't used expanded_url here because expansion makes file system URLS absolute.
            if eu.proto == 'file' and not parsed_url.path_is_absolute:
                package_sub_dir = parsed_url.fspath.parent
            else:
                package_sub_dir = 'docs'


        path = join(self.package_path.path,  package_sub_dir, file_name)

        self.prt("Loading documentation for '{}', '{}' to '{}'  ".format(title, file_name, path))

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)

        with open(path, 'wb') as f:
            f.write(contents)

    def _load_file(self,  filename, contents):

        if "__pycache__" in filename:
            return

        path = join(self.package_path.path, filename)

        ensure_dir(dirname(path))

        with open(path, 'wb') as f:
            f.write(contents)