# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

from __future__ import print_function

import sys
import six
from itertools import islice
from uuid import uuid4

from metapack._meta import __version__
from metapack.util import make_dir_structure, make_metatab_file
from metatab import MetatabDoc
from os import getcwd
from os.path import exists, join, isdir
from rowgenerators import RowGenerator
from tableintuit import TypeIntuiter, SelectiveRowGenerator

METATAB_FILE = 'metadata.csv'


def prt(*args):
    print(*args)

def warn( *args):
    print('WARN:',*args)

def err(*args):
    import sys
    print("ERROR:", *args)
    sys.exit(1)


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


def metapack():
    import argparse

    parser = argparse.ArgumentParser(
        prog='metapack',
        description='Create metatab data packages, version {}'.format(__version__))

    parser.add_argument('-i', '--init', action='store', nargs='?', default=False,
                        help='Set the cache directory for downloads and building packages')

    parser.add_argument('-a', '--add', default=False,
                        help='Add a file or url to the resources. With a directory add a data files in the directory')

    parser.add_argument('-r', '--resources', default=False, action='store_true',
                        help='Rebuild the resources, intuiting rows and encodings from the URLs')

    parser.add_argument('-s', '--schemas', default=False, action='store_true',
                        help='Rebuild the schemas for files referenced in the resource section')

    parser.add_argument('-e', '--excel', action='store', nargs='?', default=False,
                        help='Create an excel archive from a metatab file')

    parser.add_argument('-z', '--zip', action='store', nargs='?', default=False,
                        help='Create a zip archive from a metatab file')

    parser.add_argument('-R', '--resource-format', action='store_true', default=False,
                        help="Re-write the metatab file in 'Resource' format ")

    parser.add_argument('metatabfile', nargs='?')

    args = parser.parse_args(sys.argv[1:])

    d = getcwd()

    cache = get_cache(d)

    prt('Cache dir: {}'.format(str(cache)))

    mt_file = args.metatabfile if args.metatabfile else join(d, METATAB_FILE)

    if args.init is not False:
        init_metatab(mt_file, args.init)

    if args.resources:
        process_resources(mt_file, cache=cache)

    if args.schemas:
        process_schemas(mt_file)

    if args.add:
        add_resource(mt_file, args.add, cache=cache)

    if args.excel is not False:
        write_excel_package(mt_file, args.excel, cache=cache)

    if args.zip is not False:
        write_zip_package(mt_file, args.zip, cache=cache)

    if args.resource_format:
        rewrite_resource_format(mt_file)


def get_cache(d):
    from fs.opener import fsopendir

    make_dir_structure(d)

    return fsopendir(join(d, '_metapack', 'download'))


def init_metatab(mt_file, d):
    d = d if d is not None else getcwd()

    prt("Initializing '{}'".format(d))

    make_dir_structure(d)

    if not exists(mt_file):
        doc = make_metatab_file()

        doc['Root']['Identifier'] = str(uuid4())

        doc.write_csv(mt_file)
    else:
        prt("Doing nothing; file '{}' already exists".format(mt_file))


def add_resource(mt_file, ref, cache):
    """Add a resources entry, downloading the intuiting the file, replacing entries with
    the same reference"""

    if isinstance(mt_file, six.string_types):
        write = True
        doc = MetatabDoc().load_csv(mt_file)
    else:
        write = False
        doc = mt_file

    if isdir(ref):
        for f in find_files(ref, ['csv']):

            if f.endswith(METATAB_FILE):
                continue

            add_resource_term(f, doc['Resources'], cache=cache)
    else:

        t = doc.find_first('Root.Datafile', value=ref)

        if t:
            doc.remove_term(t)

        add_resource_term(ref, doc['Resources'], cache=cache)

    if write:
        doc.write_csv(mt_file)


def add_resource_term(ref, section, cache):

    path, name = extract_path_name(ref)

    prt("Adding resource for '{}'".format(ref))

    encoding, ri = run_row_intuit(path, cache)

    return section.new_term('Datafile', ref, name=name,
                            startline=ri.start_line,
                            headerlines=','.join(str(e) for e in ri.header_lines),
                            encoding=encoding)


def run_row_intuit(path, cache):
    from rowgenerators import RowGenerator
    from tableintuit import RowIntuiter
    from itertools import islice


    for encoding in ('ascii', 'utf8', 'latin1'):
        try:
            rows = list(islice(RowGenerator(url=path, encoding=encoding, cache=cache), 5000))
            return encoding, RowIntuiter().run(list(rows))
        except UnicodeDecodeError:
            pass

    raise Exception('Failed to convert with any encoding')


def extract_path_name(ref):
    from os.path import splitext, basename, abspath
    from rowgenerators.util import parse_url_to_dict

    uparts = parse_url_to_dict(ref)

    if not uparts['scheme']:
        path = abspath(ref)
        name = basename(splitext(path)[0])
    else:
        path = ref
        name = basename(splitext(uparts['path'])[0])

    return path, name


def alt_col_name(name):
    import re
    return re.sub('_+', '_', re.sub('[^\w_]', '_', name).lower()).rstrip('_')


def process_resources(mt_file, cache):
    doc = MetatabDoc().load_csv(mt_file)

    try:
        doc['Schema'].clean()
    except KeyError:
        pass

    for t in list(doc['Resources']): # w/o list(), will iterate over new terms

        if not t.term_is('root.datafile'):
            continue

        if t.as_dict().get('url'):
            add_resource(doc, t.as_dict()['url'], cache)

        else:
            warn("Entry '{}' on row {} is missing a url; skipping".format(t.join, t.row))

    doc.write_csv(mt_file)

def process_schemas(mt_file):

    doc = MetatabDoc().load_csv(mt_file)

    try:
        doc['Schema'].clean()
    except KeyError:
        doc.new_section('Schema',['DataType', 'Altname', 'Description'])

    for t in doc['Resources']:

        if not t.term_is('root.datafile'):
            continue

        e = { k:v for k,v in t.properties.items() if v}

        path, name = extract_path_name(t.value)

        slice = islice(RowGenerator(url=path, encoding=e.get('encoding', 'utf8')), 5000)

        si = SelectiveRowGenerator(slice,
                                   headers=[int(i) for i in e.get('headerlines', '0').split(',')],
                                   start=e.get('startline', 1))

        ti = TypeIntuiter().run(si)

        table = doc['Schema'].new_term('Table', e['name'])

        prt("Adding table '{}' ".format(e['name']))

        for c in ti.to_rows():
            raw_alt_name = alt_col_name(c['header'])
            alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

            table.new_child('Column', c['header'],
                            datatype=c['resolved_type'], altname=alt_name)

    doc.write_csv(mt_file)


def write_excel_package(mt_file, d, cache):
    from metatab.excel import ExcelPackage
    from metatab import MetatabDoc

    d = d if d is not None else getcwd()

    in_doc = MetatabDoc().load_csv(mt_file)

    name = in_doc.find_first_value('root.name')

    if not name:
        err("Input metadata must define a package name in the Root.Name term")

    ep = ExcelPackage(join(d, name + '.xls'))

    ep.copy_section('root', in_doc)

    table_schemas = {t.value: t.as_dict()['column'] for t in in_doc['schema']}
    file_resources = [fr.as_dict() for fr in in_doc['resources']]

    if len(table_schemas) == 0:
        err("Cant create package without table schemas")

    for resource in file_resources:
        prt("Processing {}".format(resource['name']))
        try:
            columns = table_schemas[resource['name']]
        except KeyError:
            prt("WARN: Didn't get schema for table '{}', skipping".format(resource['name']))
            continue

        ep.add_data_file(resource['url'], resource['name'], resource.get('description'),
                         columns, int(resource.get('startline', 1))
                         , resource.get('encoding', 'latin1'),
                         cache=cache)

    ep.save()


def write_zip_package(mt_file, d, cache):
    from metatab.zip import ZipPackage
    from metatab import MetatabDoc

    d = d if d is not None else getcwd()

    in_doc = MetatabDoc().load_csv(mt_file)

    name = in_doc.find_first_value('root.name')

    if not name:
        err("Input metadata must define a package name in the Root.Name term")

    zp = ZipPackage(in_doc, d, cache)

    return

    zp.save()


def rewrite_resource_format(mt_file):
    doc = MetatabDoc().load_csv(mt_file)

    if 'schema' in doc:
        table_schemas = {t.value: t.as_dict() for t in doc['schema']}
        del doc['schema']

        for resource in doc['resources']:
            s = resource.new_child('Schema', '')
            for column in table_schemas.get(resource.get_child_value('name'), {})['column']:
                c = s.new_child('column', column['name'])

                for k, v in column.items():
                    if k != 'name':
                        c.new_child(k, v)

    doc.write_csv(mt_file)
