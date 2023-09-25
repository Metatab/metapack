import unittest


def open_package(name, downloader=None):
    d = test_data('packages', name)

    from metapack import open_package as op, Downloader

    if downloader is None:
        downloader = Downloader()

    return op(d, downloader)


def test_data(*paths):
    from os.path import dirname, join, abspath
    import test_data

    return join(dirname(abspath(test_data.__file__)), *paths)


def cache_fs():
    from fs.tempfs import TempFS

    return TempFS('rowgenerator')


def get_cache():
    return cache_fs()


class MetapackTest(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')
