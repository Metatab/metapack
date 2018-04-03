# -*- coding: utf-8 -*
# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

jupyter nbextension install --py metatab.jupyter.magic

"""

from __future__ import print_function

import logging
import os
import shlex
import sys
from collections import OrderedDict
from os import makedirs, getcwd
from os.path import join, abspath, dirname, exists, normpath
from warnings import warn

import docopt
from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic, line_cell_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)
from IPython.display import  display, HTML, Latex

from rowgenerators import Downloader, parse_app_url
from metapack import MetapackDoc
from metapack.appurl import MetapackPackageUrl
from metapack.cli.core import process_schemas
from metapack.html import bibliography, data_sources
from metatab import TermParser
from metatab.generate import TextRowGenerator

logger = logging.getLogger('user')
logger_err = logging.getLogger('cli-errors')
doc_logger = logging.getLogger('doc')
debug_logger = logging.getLogger('debug_logger')

MT_DOC_VAR = 'mt_pkg' # Namespace name for the metatab document.

@magics_class
class MetatabMagic(Magics):

    """Magics for using Metatab in Jupyter Notebooks

    """



    @property
    def mt_doc(self):
        """Return the current metatab document, which must be created with either %%metatab
        or %mt_load_package"""



        if MT_DOC_VAR not in self.shell.user_ns:

            package_url = MetapackPackageUrl("metapack+file:" + os.getcwd() + '/', downloader=Downloader())

            self.shell.user_ns[MT_DOC_VAR] = \
                MetapackDoc(TextRowGenerator("Declare: metatab-latest\n"), package_url=package_url)

            inline_doc = self.shell.user_ns[MT_DOC_VAR]

            if not 'Resources' in inline_doc:
                inline_doc.new_section('Resources', ['Name', 'Description'])
            if not 'Resources' in inline_doc:
                inline_doc.new_section('References', ['Name', 'Description'])

            # Give all of the sections their standard args, to make the CSV versions of the doc
            # prettier
            for name, s in inline_doc.sections.items():
                try:
                    s.args = inline_doc.decl_sections[name.lower()]['args']
                except KeyError:
                    pass

        return self.shell.user_ns[MT_DOC_VAR]

    @property
    def package_dir(self):
        """Return the current metatab document, which must be created with either %%metatab
        or %mt_load_package"""

        return self.shell.user_ns['_package_dir']

    def add_term_lines(self, text):


        assert 'root.reference' in TermParser.term_classes

        tp = TermParser(TextRowGenerator(text), resolver= self.mt_doc.resolver, doc= self.mt_doc)

        self.mt_doc.load_terms(tp)


    def clean_doc(self, doc):

        # Some sections have terms that are unique on Name

        for sec in ['Resources','References','Bibliography', 'Schema', 'Contacts']:
            try:
                seen = set()
                for t in doc[sec]:
                    if t.name in seen:
                        doc.remove_term(t)
                    seen.add(t.name)
            except KeyError:
                pass

        # For the Root, just make every term unique name term name, keeping the last one

        seen = {}
        for t in list(doc['Root']):
            if t.term in seen:
                extant = seen[t.term]
                doc.remove_term(extant)
            seen[t.term] = t

    @magic_arguments()
    @argument('-s', '--show', help='After loading, display the document', action='store_true')
    @argument('-p', '--package_dir', help='Set the directory where the package will be created')
    @cell_magic
    def metatab(self, line, cell):
        """Process a cell of Metatab data, in line format. Stores document in the `mt_pkg` variable
        """

        args = parse_argstring(self.metatab, line)

        inline_doc = self.mt_doc

        self.add_term_lines(cell)

        extant_identifier = inline_doc.get_value('Root.Identifier')
        extant_name = inline_doc.get_value('Root.Name')

        inline_doc.update_name(force=True, create_term=True)

        process_schemas(inline_doc)

        self.clean_doc(inline_doc)

        if args.show:
            for l in inline_doc.lines:
                print(': '.join(str(e) for e in l))

        if args.package_dir:
            self.shell.user_ns['_package_dir'] = abspath(join(getcwd(), args.package_dir))
        else:
            self.shell.user_ns['_package_dir'] = join(getcwd(), inline_doc.get_value('Root.Name'))

        if extant_identifier != inline_doc.get_value('Root.Identifier'):
            print("Identifier updated.  Set 'Identifier: {}'  in document".format(inline_doc.get_value('Root.Identifier')))

        if extant_name != inline_doc.get_value('Root.Name'):
            print("Name Changed. Set 'Name: {}'  in document".format(inline_doc.get_value('Root.Name')))


    @magic_arguments()
    @argument('-s', '--source', help='Force opening the source package', action='store_true')
    @line_magic
    def mt_open_package(self, line):
        """Find the metatab file for this package, open it, and load it into the namespace. """

        from metapack.jupyter.ipython import open_package

        args = parse_argstring(self.mt_open_package, line)
        self.shell.user_ns[MT_DOC_VAR] = open_package(self.shell.user_ns)


        if self.mt_doc.package_url:
            u = parse_app_url(self.mt_doc.package_url)

    @line_magic
    def mt_import_terms(self, line):
        """Import the value of some Metatab terms into the notebook namespace """

        mt_terms = {}

        doc = self.mt_doc

        mt_terms['root.title'] = doc['Root'].find_first_value('Root.Title')
        mt_terms['root.description'] = doc['Root'].find_first_value('Root.Description')
        mt_terms['root.name'] = doc['Root'].find_first_value('Root.Name')
        mt_terms['root.identifier'] = doc['Root'].find_first_value('Root.Identifier')

        mt_terms['contacts'] = []

        for t in doc.get_section('Contacts', []):
            d = t.as_dict()
            d['type'] = t.record_term_lc
            mt_terms['contacts'].append(d)

        mt_terms['bibliography'] = []

        for t in doc.get_section('Bibliography', []):
            d = t.as_dict()
            d['type'] = t.record_term_lc
            mt_terms['bibliography'].append(d)

        mt_terms['references'] = []

        for t in doc.get_section('References', []):
            d = t.as_dict()
            d['type'] = t.record_term_lc
            mt_terms['references'].append(d)

        print('mt_terms')

        self.shell.user_ns['mt_terms'] = mt_terms

    @line_magic
    def mt_process_schemas(self, line):
        """Add Schema entries for resources to the metatab file. Does not write the doc file"""

        process_schemas(self.mt_doc)

    @magic_arguments()
    @argument('package_dir', help='Package directory')
    @argument('--feather', help='Use feather for serialization', action='store_true' )
    @line_magic
    def mt_materialize_all(self, line):
        """Materialize all of the dataframes that has been previoulsly added with mt_add_dataframe
        """

        from json import dumps

        from metapack.rowgenerator import PandasDataframeSource
        import csv

        materialized = []

        args = parse_argstring(self.mt_materialize_all, line)

        try:
            cache = self.mt_doc._cache
        except KeyError:
            cache = Downloader().cache

        for df_name, ref in self.shell.user_ns.get('_material_dataframes',{}).items():

            u = parse_app_url(args.package_dir).join(ref)

            path = u.path

            if not exists(dirname(path)):
                makedirs(dirname(path))

            df = self.shell.user_ns[df_name].fillna('')

            if args.feather:
                path = path.replace('.csv','.feather')
                df.to_feather(path)
            else:
                gen = PandasDataframeSource(u, df, cache=cache)
                with open(path, 'w') as f:
                    w = csv.writer(f)
                    w.writerows(gen)

            materialized.append({
                'df_name': df_name,
                'path': path,
                'ref':ref
            })

        # Show information about the dataframes that were materialized, so it can be harvested later
        print(dumps(materialized, indent=4))

    @magic_arguments()
    @argument('df_name', help='Dataframe name')
    @argument('dir', help='Path to output directory. Created if it does not exist')
    @argument('--feather', help='Materialize with feather', action="store_true")
    @line_magic
    def mt_materialize(self, line):
        """Materialize all of the dataframes that has been previoulsly added with mt_add_dataframe
        """

        from json import dumps
        from rowgenerators import get_cache
        from metapack.rowgenerator import PandasDataframeSource
        import csv
        from os.path import join

        args = parse_argstring(self.mt_materialize, line)

        try:
            cache = self.mt_doc._cache
        except KeyError:
            cache = get_cache()

        if not exists(args.dir):
            makedirs(args.dir)

        if args.feather:
            path = join(args.dir, args.df_name+".feather")
            df = self.shell.user_ns[args.df_name]
            df.to_feather(path)
        else:
            path = join(args.dir, args.df_name + ".csv")
            df = self.shell.user_ns[args.df_name].fillna('')
            gen = PandasDataframeSource(parse_app_url(path), df, cache=cache)

            with open(path, 'w') as f:
                w = csv.writer(f)
                w.writerows(gen)

        print(dumps({
            'df_name': args.df_name,
            'path': path,

        }, indent=4))


    @line_magic
    def mt_show_metatab(self, line):
        """Dump the metatab file to the output, so it can be harvested after the notebook is executed"""

        try:
            for line in self.mt_doc.lines:

                if  line[1]: # Don't display "None"
                    print(': '.join(line))
        except KeyError:
            pass

    @magic_arguments()
    @argument('-m','--materialize', help='Save the data for the dataframe during package conversion', action="store_true")
    @argument('-n','--name', help='Metadata reference name of the dataframe')
    @argument('-t','--title', help='Title of the dataframe')
    @argument('-d', '--dump', help='Dump example schema for the dataframe. Implied when used as line magic', action="store_true")
    @argument('--feather', help='Materialize with feather', action="store_true")
    @argument('dataframe_name', nargs=1, help='Variable name of the dataframe name')
    @line_cell_magic
    def mt_add_dataframe(self, line, cell=''):
        """Add a dataframe to a metatab document's data files

        """
        from metapack.jupyter.core import process_schema
        from metatab.exc import ParserError

        args = parse_argstring(self.mt_add_dataframe, line)

        if not cell:
            is_line = True
            args.dump = True
        else:
            is_line = False

        dataframe_name = args.dataframe_name[0]

        if not '_material_dataframes' in self.shell.user_ns:
            self.shell.user_ns['_material_dataframes'] = {}

        df = self.shell.user_ns[dataframe_name]

        try:
            cell_doc = MetapackDoc(TextRowGenerator("Declare: metatab-latest\n" + cell))
        except ParserError as e:
            warn('Failed to parse Metatab in cell: {} '.format(e))
            return

        cell_table = cell_doc.find_first('Root.Table')

        if cell_table and ( args.name or args.title ):
            warn("The name and title arguments are ignored when the cell includes a Metatab table definition")

        if cell_table:
            name = cell_table.get_value('name')
            title = cell_table.get_value('title','')
            description = cell_table.get_value('description','')
        else:
            name = None
            title = ''
            description = ''


        if not name:
            name = args.name or dataframe_name;

        if not title:
            title = args.title or dataframe_name

        if not name:
            warn("Name must be set with .name property, or --name option".format(args['<dataframe_name>']))
            return

        title = title.strip("'").strip('"')

        try:
            doc = self.mt_doc
        except KeyError:
            doc = None

        if args.materialize:
            ref = 'file:data/{}.csv'.format(name)
            self.shell.user_ns['_material_dataframes'][dataframe_name] = ref

        elif doc is not None:
            ref = 'ipynb:notebooks/{}.ipynb#{}'.format( doc.as_version(None), dataframe_name)

        else:
            ref = None

        table = None

        resource_term = None

        ##
        ## First, process the schema, extracting the columns from the dataframe.
        ##

        if doc and ref:
            if not 'Resources' in doc:
                doc.new_section('Resources')

            resource_term = doc['Resources'].get_or_new_term("Root.Datafile", ref)

            resource_term['name'] = name
            resource_term['title'] = title
            resource_term['description'] = description

            df = df.reset_index()

            table = process_schema(doc, doc.resource(name), df)

            if not table:
                table = doc['Schema'].find_first('Root.Table', name)

        ##
        ## Next, apply the names from  table description from the cell
        ##

        if cell_table:

            cols_by_name = {c.name:c for c in cell_table.find('Table.Column') }

            for i,c in enumerate(table.find('Table.Column')):

                cell_column = cols_by_name.get(c.name)
                try:
                    cell_col_by_pos = list(cols_by_name.values())[i]
                except KeyError:
                    cell_col_by_pos = None
                except IndexError:
                    cell_col_by_pos = None

                if cell_column:
                    c.description = cell_column.description
                    c.name = cell_column.name
                elif cell_col_by_pos:
                    c.description = cell_col_by_pos.description
                    c.name = cell_col_by_pos.name


        if args.dump and table:
            print("Table:", resource_term.name)

            if resource_term and resource_term.title:
                print("Table.Title:", resource_term.get_value('title'))
                print("Table.Description:", resource_term.get_value('description') if resource_term.get_value('description')  else '')

            for c in table.find('Table.Column'):
                print("Table.Column:", c.name)
                print("  .Datatype:", c.datatype)
                print("  .Description:",  c.description or '')

            if is_line:
                print("\nCopy the above into the cell, and change to a cell magic, with '%%' ")


    @magic_arguments()
    @argument('--format', help="Format, html or latex. Defaults to 'all' ", default='all', nargs='?', )
    @argument('converters', help="Class names for citation converters", nargs='*', )
    @line_magic
    def mt_bibliography(self, line):
        """Display, as HTML, the bibliography for the metatab document. With no argument,
         concatenate all doc, or with an arg, for only one. """

        args = parse_argstring(self.mt_bibliography, line)

        def import_converter(name):
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod

        converters = [ import_converter(e) for e in args.converters ]

        if args.format == 'html' or args.format == 'all':
            display(HTML(bibliography(self.mt_doc, converters=converters, format='html')))

        if args.format == 'latex' or args.format == 'all':
            display(Latex(bibliography(self.mt_doc, converters=converters, format='latex')))

    @magic_arguments()
    @argument('--format', help="Format, html or latex. Defaults to 'all' ", default='all', nargs='?', )
    @argument('converters', help="Class names for citation converters", nargs='*', )
    @line_magic
    def mt_data_references(self, line):
        """Display, as HTML, the bibliography for the metatab document. With no argument,
         concatenate all doc, or with an arg, for only one. """

        args = parse_argstring(self.mt_bibliography, line)

        def import_converter(name):
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod

        converters = [import_converter(e) for e in args.converters]

        if args.format == 'html' or args.format == 'all':
            display(HTML(data_sources(self.mt_doc, converters=converters, format='html')))

        if args.format == 'latex' or args.format == 'all':
            display(Latex(data_sources(self.mt_doc, converters=converters, format='latex')))

    @magic_arguments()
    @argument('lib_dir', help='Directory', nargs='?',)
    @line_magic
    def mt_lib_dir(self, line):
        """Declare a source code directory and add it to the sys path

        The argument may be a directory, a URL to a Metatab ZIP archive, or a reference to a
        Root.Reference or Root.Resource term that references a Metatab ZIP Archive

        If lib_dir is not specified, it defaults to 'lib'

        If lib_dir is a directory, the target is either at the same level as the CWD or
        one level up.

        If lib_dir is a URL, it must point to a Metatab ZIP archive that has an interal Python
        package directory. The URL may hav path elements after the ZIP archive to point
        into the ZIP archive. For instance:

            %mt_lib_dir http://s3.amazonaws.com/library.metatab.org/ipums.org-income_homevalue-5.zip

        If lib_dir is anything else, it is a reference to the name of a Root.Reference or Root.Resource term that
        references a Metatab ZIP Archive. For instance:

            %%metatab
            ...
            Section: References
            Reference: metatab+http://s3.amazonaws.com/library.metatab.org/ipums.org-income_homevalue-5.zip#income_homeval
            ...


            %mt_lib_dir incv
            from lib.incomedist import *

        """

        from os.path import splitext, basename

        args = parse_argstring(self.mt_lib_dir, line) # Its a normal string

        if not args.lib_dir:
            lib_dir = 'lib'

        else:
            lib_dir = args.lib_dir

        if not '_lib_dirs' in self.shell.user_ns:
            self.shell.user_ns['_lib_dirs'] = set()

        u = parse_app_url(lib_dir)

        # Assume files are actually directories
        # This clause will pickup both directories and reference names, but ref names should not
        # exist as directories.
        if u.proto == 'file':

            lib_dir = normpath(lib_dir).lstrip('./')

            for path in [ abspath(lib_dir), abspath(join('..',lib_dir))]:
                if exists(path) and path not in sys.path:
                    sys.path.insert(0,path)
                    self.shell.user_ns['_lib_dirs'].add(lib_dir)
                    return

        # Assume URLS are to Metapack packages on the net
        if (u.scheme == 'https' or u.scheme == 'http'):

            # The path has to be a Metatab ZIP archive, and the root directory must be the same as
            # the name of the path

            r = u.get_resource()

            pkg_name, _ = splitext(basename(r.path))

            lib_path = r.join(pkg_name).path

            if lib_path not in sys.path:
                sys.path.insert(0,lib_path)

        # Assume anything else is a Metatab Reference term name
        elif self.mt_doc.find_first('Root.Reference', name=lib_dir) or self.mt_doc.resource(lib_dir) :

            r = self.mt_doc.find_first('Root.Reference', name=lib_dir) or self.mt_doc.resource(lib_dir)

            ur = parse_app_url(r.url).inner

            return self.mt_lib_dir(str(ur))

        else:
            logger.error("Can't find library directory: '{}' ".format(lib_dir))


    @line_magic
    def mt_show_libdirs(self, line):
        """Dump the list of lib dirs as JSON"""
        import json

        if '_lib_dirs' in self.shell.user_ns:
            print(json.dumps(list(self.shell.user_ns['_lib_dirs'])))
        else:
            print(json.dumps([]))


def load_ipython_extension(ipython):
    # In order to actually use these magics, you must register them with a
    # running IPython.  This code must be placed in a file that is loaded once
    # IPython is up and running:
    ip = get_ipython()
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ip.register_magics(MetatabMagic)

    # init_logging()


def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    pass
