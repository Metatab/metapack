# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Classes to build a Metatab document
"""
import mimetypes
import os
import shutil
from genericpath import exists
from os import makedirs
from os.path import join


def declaration_path(name):
    """Return the path to an included declaration"""
    from os.path import dirname, join, exists
    import metatab.declarations
    from metatab.exc import IncludeError

    d = dirname(metatab.declarations.__file__)

    path = join(d, name)

    if not exists(path):
        path = join(d, name + '.csv')

    if not exists(path):
        raise IncludeError("No local declaration file for name '{}' ".format(name))

    return path


def linkify(v, description=None, cwd_url=None):
    from rowgenerators import Url
    if not v:
        return None

    u = Url(v)

    target = 'target="_blank"'

    if u.scheme in ('http', 'https', 'mailto'):

        if description is None:
            description = v
        return '<a href="{url}" {target} >{desc}</a>'.format(url=v, target=target, desc=description)

    elif u.scheme == 'file':

        return '<a href="file:{url}" >{desc}</a>'.format(url=u.parts.path, desc=description)

    else:
        return v


def flatten(d, sep='.'):
    """Flatten a data structure into tuples"""

    def _flatten(e, parent_key='', sep='.'):
        import collections

        prefix = parent_key + sep if parent_key else ''

        if isinstance(e, collections.MutableMapping):
            return tuple((prefix + k2, v2) for k, v in e.items() for k2, v2 in _flatten(v, k, sep))
        elif isinstance(e, collections.MutableSequence):
            return tuple((prefix + k2, v2) for i, v in enumerate(e) for k2, v2 in _flatten(v, str(i), sep))
        else:
            return (parent_key, (e,)),

    return tuple((k, v[0]) for k, v in _flatten(d, '', sep))


# From http://stackoverflow.com/a/2597440
class Bunch(object):
    def __init__(self, adict):
        self.__dict__.update(adict)


MP_DIR = '_metapack'
DOWNLOAD_DIR = join(MP_DIR, 'download')
PACKAGE_DIR = join(MP_DIR, 'package')
OLD_DIR = join(MP_DIR, 'old')


def make_metatab_file(template='metatab'):
    from os.path import dirname, exists
    from rowgenerators.util import fs_join as join
    import metatab.templates
    from metapack import MetapackDoc

    if exists(template):
        template_path = template
    else:
        template_path = join(dirname(metatab.templates.__file__), template + '.csv')

    doc = MetapackDoc(template_path)

    return doc


def scrape_urls_from_web_page(page_url):
    from bs4 import BeautifulSoup
    from urllib.error import HTTPError
    from urllib.parse import urlsplit, urlunsplit
    from urllib.request import urlopen, Request
    import os
    from os.path import dirname

    parts = list(urlsplit(page_url))

    parts[2] = ''
    root_url = urlunsplit(parts)

    try:
        # Some sites return 403 without minimal header
        r = Request(page_url, headers={'User-Agent': 'Mozilla/5.0'})
        html_page = urlopen(r).read()

    except HTTPError as e:

        return {'sources': {}, 'links': {}, 'external_documentation': {}, 'error': e}

    soup = BeautifulSoup(html_page, "lxml")

    d = dict(external_documentation={}, sources={}, links={})

    for link in soup.findAll('a'):

        if not link:
            continue

        if link.string:
            text = link.string
        else:
            text = None

        url = link.get('href')

        if not url:
            continue

        if 'javascript' in url:
            continue

        if url.startswith('http'):
            pass
        elif url.startswith('/'):
            url = os.path.join(root_url, url[1:])

        elif page_url.endswith(".html") or page_url.endswith(".htm") or page_url.endswith(".asp"):
            # This part is a real hack. There should be a better way to determine if the URL point
            # to a directory or a file.
            url = os.path.join(dirname(page_url), url)
        else:
            url = os.path.join(page_url, url)

        base = os.path.basename(url)

        if '#' in base:
            continue

        try:
            fn, ext = base.split('.', 1)
        except ValueError:
            fn = base
            ext = ''

        text = ' '.join(text.split()) if text else ''

        # xlsm is a bug that adds 'm' to the end of the url. No idea.
        if ext.lower() in ('zip', 'csv', 'xls', 'xlsx', 'xlsm', 'txt'):
            d['sources'][fn] = dict(url=url, description=text)

        elif ext.lower() in ('pdf', 'html', 'asp'):
            d['external_documentation'][fn] = dict(url=url, description=text)

        else:
            d['links'][text] = dict(url=url, description=text)

    return d


mimetypes.init()
mime_map = {v: k.strip('.') for k, v in mimetypes.types_map.items()}
mime_map['application/x-zip-compressed'] = 'zip'
mime_map['application/vnd.ms-excel'] = 'xls'
mime_map['text/html'] = 'html'


def guess_format(url):
    """Try to guess  the format of a resource, possibly with a HEAD request"""
    import requests
    from requests.exceptions import InvalidSchema
    from rowgenerators import parse_url_to_dict

    parts = parse_url_to_dict(url)

    # Guess_type fails for root urls like 'http://civicknowledge.com'
    if parts.get('path'):
        type, encoding = mimetypes.guess_type(url)
    elif parts['scheme'] in ('http', 'https'):
        type, encoding = 'text/html', None  # Assume it is a root url
    else:
        type, encoding = None, None

    if type is None:
        try:
            r = requests.head(url, allow_redirects=False)
            type = r.headers['Content-Type']

            if ';' in type:
                type, encoding = [e.strip() for e in type.split(';')]

        except InvalidSchema:
            pass  # It's probably FTP

    return type, mime_map.get(type)


def enumerate_contents(url, cache, callback=None):
    from rowgenerators import enumerate_contents as rg_ec

    mt, format = guess_format(url)

    if mt == 'text/html':
        d = scrape_urls_from_web_page(url)
        urls = [v['url'] for k, v in d['sources'].items()]

    elif isinstance(url, (list, tuple)):
        urls = url
    else:
        urls = [url]

    for url in urls:

        for s in rg_ec(url, cache, callback=callback):
            yield s


# From https://gist.github.com/zdavkeos/1098474
def walk_up(bottom):
    """  mimic os.walk, but walk 'up' instead of down the directory tree
    :param bottom:
    :return:
    """
    import os
    from os import path

    bottom = path.realpath(bottom)

    # get files in current dir
    try:
        names = os.listdir(bottom)
    except Exception as e:
        raise e

    dirs, nondirs = [], []
    for name in names:
        if path.isdir(path.join(bottom, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    yield bottom, dirs, nondirs

    new_path = path.realpath(path.join(bottom, '..'))

    # see if we are at the top
    if new_path == bottom:
        return

    for x in walk_up(new_path):
        yield x


def ensure_dir(path):
    if path and not exists(path):
        makedirs(path)


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def write_csv(path_or_flo, headers, gen):
    import csv
    try:
        f = open(path_or_flo, "wb")

    except TypeError:
        f = path_or_flo  # Assume that it's already a file-like-object

    try:
        w = csv.writer(f)
        w.writerow(headers)

        row = None
        try:
            for row in gen:
                w.writerow(row)
        except Exception:
            import sys
            print("write_csv: ERROR IN ROW", row, file=sys.stderr)
            raise

        try:
            return f.getvalue()
        except AttributeError:
            return None

    finally:
        f.close()


def datetime_now():
    import datetime

    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()


def get_materialized_data_cache(doc=None):
    """Return the cache directory where data can be written during a build, usually for
    a Jupyter notebook that generates many files for each execution"""

    from metapack.constants import MATERIALIZED_DATA_PREFIX
    from os.path import join

    if not doc:
        from metapack import Downloader
        downloader = Downloader()
        return downloader.cache.getsyspath(MATERIALIZED_DATA_PREFIX)
    else:
        dr = doc._cache.getsyspath(join(MATERIALIZED_DATA_PREFIX, doc.name))

        ensure_dir(dr)

        return dr


def dump_stack(n=4):
    import traceback
    import os

    lines = []
    for filename, line, function, text in traceback.extract_stack()[-n:-1]:
        fn_parts = filename.split(os.sep)
        sub_path = '/'.join(fn_parts[-3:])
        lines.append('{}:{} {} {} '.format(sub_path, line, function, text))

    return '\n'.join(lines)


# From: https://stackoverflow.com/a/35936407
def iso8601_duration_as_seconds(d):
    from re import findall
    if d[0] != 'P':
        raise ValueError('Not an ISO 8601 Duration string')
    seconds = 0
    # split by the 'T'
    for i, item in enumerate(d.split('T')):
        for number, unit in findall(r'(?P<number>\d+)(?P<period>S|M|H|D|W|Y)', item):
            # print '%s -> %s %s' % (d, number, unit )
            number = int(number)
            this = 0
            if unit == 'Y':
                this = number * 31557600  # 365.25
            elif unit == 'W':
                this = number * 604800
            elif unit == 'D':
                this = number * 86400
            elif unit == 'H':
                this = number * 3600
            elif unit == 'M':
                # ambiguity ellivated with index i
                if i == 0:
                    this = number * 2678400  # assume 30 days
                    # print "MONTH!"
                else:
                    this = number * 60
            elif unit == 'S':
                this = number
            seconds = seconds + this
    return seconds
