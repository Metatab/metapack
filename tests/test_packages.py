import unittest

from support import open_package, test_data
from tabulate import tabulate


def ds_hash(r):
    import hashlib

    m = hashlib.md5()

    for row in r:
        for col in row:
            m.update(str(col).encode('utf8'))

    return m.hexdigest()

class TestPackages(unittest.TestCase):
    """"""

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

    def test_iterators(self):
        from itertools import chain
        pkg = open_package('example.com-iterators')

        print('== References')

        for r in chain(pkg.references(), pkg.resources()):

            if r.get_value('Iterator'):
                itr = getattr(r,r.get_value('Iterator') )
            else:
                itr = iter(r)


            data = list(itr)
            hash = ds_hash(data)

            if hash != r.get_value('Hash'):
                print(tabulate(data))
                print(r.name, hash)



if __name__ == '__main__':
    unittest.main()
