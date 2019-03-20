# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import re

from metapack import MetapackDoc, Downloader
from metapack.cli.core import prt, warn, write_doc, \
    update_name, extract_path_name, MetapackCliMemo
from rowgenerators import parse_app_url
from rowgenerators.exceptions import SourceError, RowGeneratorError
from tableintuit import RowIntuitError

downloader = Downloader.get_instance()



def url(subparsers):
    parser = subparsers.add_parser(
        'url',
        help='Add resource urls to a package',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_url)

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    parser.set_defaults(handler=None)

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-a', '--add', default=False,
                       help='Add a file or url to the resources. With a directory add a data files in the directory. '
                            'If given a URL to a web page, will add all links that point to CSV, Excel Files and '
                            'data files in ZIP files. (Caution: it will download and cache all of these files. )')

    group.add_argument('-E', '--enumerate',
                       help='Enumerate the resources referenced from a URL. Does not alter the Metatab file')


    group.add_argument('-S', '--scrape', help='Scrape data and documentation URLs from a web page')


def run_url(args):
    m = MetapackCliMemo(args, downloader)

    if m.args.add:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        add_resource(m.mt_file, m.args.add, cache=m.cache)

    if m.args.enumerate:
        enumerate(m)

    if m.args.scrape:
        scrape_page(m)

def enumerate(m):

    u = parse_app_url(m.args.enumerate)

    if u.proto == 'file':
        entries = u.list()
    else:
        entries = [ssu for su in u.list() for ssu in su.list()]

    for e in entries:
        print(e)

    return

    for s in specs:
        prt(classify_url(s.url), s.target_format, s.url, s.target_segment)

def classify_url(url):
    ss = parse_app_url(url)

    if ss.target_format in DATA_FORMATS:
        term_name = 'DataFile'
    elif ss.target_format in DOC_FORMATS:
        term_name = 'Documentation'
    else:
        term_name = 'Datafile'

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

    errors = []

    for e in entries:
        if not add_single_resource(doc, e, cache=cache, seen_names=seen_names):
            errors.append(e)

    if errors:
        prt()
        warn("Found, but failed to add these urls:")
        for e in errors:
            print('    ', e)

    write_doc(doc, mt_file)


def add_single_resource(doc, ref, cache, seen_names):
    from metatab.util import slugify

    t = doc.find_first('Root.Datafile', value=ref)

    if t:
        prt("Datafile exists for '{}', deleting".format(ref))
        doc.remove_term(t)

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

    try:
        encoding, ri = run_row_intuit(path, cache)

        start_line = ri.start_line or None
        header_lines = ri.header_lines
    except RowIntuitError as e:
        warn("Failed to intuit '{}'; {}".format(ref, e))
    except RowGeneratorError as e:
        warn("Can't generate rows for: '{}'; {}".format(ref, e))
        return None
    except SourceError as e:
        warn("Source Error: '{}'; {}".format(ref, e))
        return None

    except Exception as e:
        warn("Error: '{}'; {}".format(ref, e))
        raise

    if not name:
        from hashlib import sha1
        name = sha1(slugify(path).encode('ascii')).hexdigest()[:12]

        # xlrd gets grouchy if the name doesn't start with a char
        try:
            int(name[0])
            name = 'a' + name[1:]
        except:
            pass

    prt("Added {}, url: {} ".format(name, ref))

    return doc['Resources'].new_term(term_name, ref, name=name,
                                     startline=start_line,
                                     headerlines=','.join(str(e) for e in header_lines)
                                     )

def run_row_intuit(path, cache):
    from tableintuit import RowIntuiter
    from itertools import islice
    from rowgenerators.exceptions import TextEncodingError

    for encoding in ('ascii', 'utf8', 'latin1'):
        try:

            u = parse_app_url(path)
            u.encoding = encoding

            rows = list(islice(u.get_resource().get_target().generator, 5000))
            ri = RowIntuiter().run(list(rows))
            return encoding, ri
        except (TextEncodingError, UnicodeEncodeError, UnicodeDecodeError) as e:
            pass # Try the next encoding


    raise RowIntuitError('Failed to convert with any encoding')

DATA_FORMATS = ('xls', 'xlsx', 'tsv', 'csv')
DOC_FORMATS = ('pdf', 'doc', 'docx', 'html')


def scrape_page(m):
    from metapack.util import scrape_urls_from_web_page

    doc = m.doc
    url = m.args.scrape

    doc['resources'].new_term('DownloadPage', url)

    d = scrape_urls_from_web_page(url)

    new_resources = 0
    new_documentation = 0

    for k, v in d['sources'].items():
        doc['Resources'].new_term('DataFile', v['url'], description=v.get('description'))
        new_resources += 1

    for k, v in d['external_documentation'].items():
        term_name = classify_url(v['url'])
        doc['Documentation'].new_term(term_name, v['url'], description=v.get('description'))
        new_documentation += 1

    prt("Added {} resource and {} documentation terms".format(new_resources, new_documentation))

    write_doc(doc)
