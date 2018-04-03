
def test_data(*paths):
    from os.path import dirname, join, abspath
    import metapack.test.test_data

    return join(dirname(abspath(metapack.test.test_data.__file__)), *paths)


def cache_fs():

    from fs.tempfs import TempFS

    return TempFS('rowgenerator')

def get_cache():
    return cache_fs()