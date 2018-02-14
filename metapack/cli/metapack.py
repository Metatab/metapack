# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import re

from metapack import MetapackDoc, Downloader
from metapack.cli.core import prt, err, warn, metatab_info, get_lib_module_dict, write_doc, \
    make_excel_package, make_filesystem_package, make_csv_package, make_zip_package, update_name, \
    process_schemas, extract_path_name, MetapackCliMemo, cli_init
from metapack.util import make_metatab_file, datetime_now
from rowgenerators import SourceError, parse_app_url
from rowgenerators.util import clean_cache
from tableintuit import RowIntuitError

downloader = Downloader()


def metapack(subparsers):
    parser = subparsers.add_parser(
        'pack',
        help='Manipulate data packages',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_metapack)

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    parser.add_argument('--exceptions', default=False, action='store_true',
                        help='Show full stack tract for some unhandled exceptions')


    parser.set_defaults(handler=None)

    ##
    ## Build Group

    build_group = parser.add_argument_group('Manipulate Metatab Files', 'Create and alter metatab files')

    build_group.add_argument('-c', '--create', action='store', nargs='?', default=False,
                             help="Create a new metatab file, from named template. With no argument, uses the "
                                  "'metatab' template ")

    build_group.add_argument('-a', '--add', default=False,
                             help='Add a file or url to the resources. With a directory add a data files in the directory. '
                                  'If given a URL to a web page, will add all links that point to CSV, Excel Files and'
                                  'data files in ZIP files. (Caution: it will download and cache all of these files. )')

    build_group.add_argument('-s', '--schemas', default=False, action='store_true',
                             help='Rebuild the schemas for files referenced in the resource section')

    build_group.add_argument('-u', '--update', action='store_true', default=False,
                             help="Update the Name from the Datasetname, Origin and Version terms")

    build_group.add_argument('-F', '--force', action='store_true', default=False,
                             help='Force some operations, like updating the name and building packages')




    ##
    ## Administration Group

    admin_group = parser.add_argument_group('Administration', 'Information and administration')

    admin_group.add_argument('--clean-cache', default=False, action='store_true',
                             help="Clean the download cache")

    admin_group.add_argument('-C', '--clean', default=False, action='store_true',
                             help="For some operations, like updating schemas, clear the section of existing terms first")

    admin_group.add_argument('-i', '--info', default=False, action='store_true',
                             help="Show configuration information")

    admin_group.add_argument('-n', '--name', default=False, action='store_true',
                             help="Print the name of the package")

    admin_group.add_argument('-E', '--enumerate',
                             help='Enumerate the resources referenced from a URL. Does not alter the Metatab file')



def run_metapack(args):

    m = MetapackCliMemo(args, downloader)

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    try:
        for handler in (metatab_build_handler,  metatab_admin_handler):
            handler(m)
    except Exception as e:
        if m.args.exceptions:
            raise e
        else:
            err(e)

    clean_cache(m.cache)


def metatab_build_handler(m):
    if m.args.create is not False:

        template = m.args.create if m.args.create else 'metatab'

        if not m.mt_file.exists():

            doc = make_metatab_file(template)

            doc['Root']['Created'] = datetime_now()

            write_doc(doc, m.mt_file)

            prt('Created', m.mt_file)
        else:
            err('File', m.mt_file, 'already exists')

    if m.args.add:

        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        add_resource(m.mt_file, m.args.add, cache=m.cache)

    if m.args.schemas:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        process_schemas(m.mt_file, cache=m.cache, clean=m.args.clean)


    if m.mtfile_url.scheme == 'file' and m.args.update:
        update_name(m.mt_file, fail_on_missing=True, force=m.args.force)



def metatab_admin_handler(m):
    if m.args.enumerate:

        from metatab.util import enumerate_contents

        specs = list(enumerate_contents(m.args.enumerate, m.cache, callback=prt))

        for s in specs:
            prt(classify_url(s.url), s.target_format, s.url, s.target_segment)

    if m.args.clean_cache:
        clean_cache('metapack')

    if m.args.name:
        doc = MetapackDoc(m.mt_file)
        prt(doc.find_first_value("Root.Name"))
        exit(0)

def classify_url(url):
    ss = parse_app_url(url)

    if ss.target_format in DATA_FORMATS:
        term_name = 'DataFile'
    elif ss.target_format in DOC_FORMATS:
        term_name = 'Documentation'
    else:
        term_name = 'Resource'

    return term_name


def add_resource(mt_file, ref, cache):
    """Add a resources entry, downloading the intuiting the file, replacing entries with
    the same reference"""

    if isinstance(mt_file, MetapackDoc):
        doc = mt_file
    else:
        doc = MetapackDoc(mt_file)

    if not 'Resources' in doc:
        doc.new_section('Resources')

    doc['Resources'].args = [e for e in set(doc['Resources'].args + ['Name', 'StartLine', 'HeaderLines', 'Encoding']) if
                             e]

    seen_names = set()

    u = parse_app_url(ref)

    # The web and file URLs don't list the same.

    if u.proto == 'file':
        entries = u.list()
    else:
        entries = [ssu for su in u.list() for ssu in su.list()]

    print(type(u), u)

    for e in entries:
        add_single_resource(doc, e, cache=cache, seen_names=seen_names)

    write_doc(doc, mt_file)


def add_single_resource(doc, ref, cache, seen_names):
    from metatab.util import slugify

    t = doc.find_first('Root.Datafile', value=ref)

    if t:
        prt("Datafile exists for '{}', deleting".format(ref))
        doc.remove_term(t)
    else:
        prt("Adding {}".format(ref))

    term_name = classify_url(ref)

    path, name = extract_path_name(ref)

    # If the name already exists, try to create a new one.
    # 20 attempts ought to be enough.
    if name in seen_names:
        base_name = re.sub(r'-?\d+$', '', name)

        for i in range(1, 20):
            name = "{}-{}".format(base_name, i)
            if name not in seen_names:
                break

    seen_names.add(name)

    encoding = start_line = None
    header_lines = []

    if False:
        try:
            encoding, ri = run_row_intuit(path, cache)
            prt("Added resource for '{}', name = '{}' ".format(ref, name))
            start_line = ri.start_line
            header_lines = ri.header_lines
        except RowIntuitError as e:
            warn("Failed to intuit '{}'; {}".format(path, e))

        except SourceError as e:
            warn("Source Error: '{}'; {}".format(path, e))

        except Exception as e:
            warn("Error: '{}'; {}".format(path, e))

    if not name:
        from hashlib import sha1
        name = sha1(slugify(path).encode('ascii')).hexdigest()[:12]

        # xlrd gets grouchy if the name doesn't start with a char
        try:
            int(name[0])
            name = 'a' + name[1:]
        except:
            pass

    return doc['Resources'].new_term(term_name, ref, name=name,
                                     startline=start_line,
                                     headerlines=','.join(str(e) for e in header_lines),
                                     encoding=encoding)


def run_row_intuit(path, cache):
    from tableintuit import RowIntuiter
    from itertools import islice
    from rowgenerators import TextEncodingError, get_generator

    for encoding in ('ascii', 'utf8', 'latin1'):
        try:

            u = parse_app_url(path)
            u.encoding = encoding

            rows = list(islice(get_generator(url=str(u), cache=cache, ), 5000))
            return encoding, RowIntuiter().run(list(rows))
        except (TextEncodingError, UnicodeEncodeError) as e:
            pass

    raise RowIntuitError('Failed to convert with any encoding')


DATA_FORMATS = ('xls', 'xlsx', 'tsv', 'csv')
DOC_FORMATS = ('pdf', 'doc', 'docx', 'html')
