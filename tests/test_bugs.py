import unittest
from pathlib import Path

import requests

from metapack.package import Downloader
from rowgenerators.appurl.util import copy_file_or_flo
from rowgenerators.appurl.web.web import WebUrl


class TestUrls(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

    def test_metapack_urls(self):

        dl = Downloader.get_instance()

        fn = Path('/tmp/foo.csv')
        if fn.exists():
            fn.unlink()

        u = 'metapack+https://library.metatab.org/ffiec.gov-census-2013e2021-tract-1.7.2/metadata.csv'
        u = WebUrl(str(u), downloader=dl)

        headers = {}
        r = requests.get(u.inner, headers=headers, stream=True)
        r.raise_for_status()

        import functools

        if r.headers.get('content-encoding') in ('br', 'gzip'):
            r.raw.read = functools.partial(r.raw.read, decode_content=True)

        print(r.headers)
        print(r.raw.read())

        with Path('/tmp/foo.csv').open('wb') as f:
            copy_file_or_flo(r.raw, f)


if __name__ == '__main__':
    unittest.main()
