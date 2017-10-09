from __future__ import print_function

import json
import unittest
from appurl import parse_app_url


from metapack import MetapackUrl, Downloader


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class TestBasic(unittest.TestCase):

    def test_resolve_packages(self):


        def u(v):
            return "http://example.com/d/{}".format(v)

        def f(v):
            return "file:/d/{}".format(v)

        for us in (u('package.zip'), u('package.xlsx'), u('package.csv'), u('package/metadata.csv'),
                   f('package.zip'), f('package.xlsx'), f('package.csv'), f('package/metadata.csv'),):

            u = MetapackUrl(us, downloader=Downloader())

            print(u.metadata_url)


    def test_open_package(self):

        from metapack import open_package
        from metapack.terms import Resource

        p = open_package(test_data('packages/example.com/example.com-full-2017-us/metadata.csv'))

        self.assertEqual(Resource, type(p.find_first('root.datafile')))

        self.assertEqual('example.com-full-2017-us-1', p.find_first('Root.Name').value)

        self.assertEqual(16, len(list(p['Resources'].find('Root.Resource'))))


        all_names = [ r.name for r in p.find('Datafile') ]
        for name in ['renter_cost', 'simple-example-altnames', 'simple-example', 'unicode-latin1', 'unicode-utf8',
                     'renter_cost_excel07', 'renter_cost_excel97', 'renter_cost-2', 'random-names',
                     'random-names-fs', 'random-names-csv', 'random-names-xlsx', 'random-names-zip', 'sra']:
            self.assertIn(name, all_names)



        self.assertIsInstance (p.resource('random-names'), Resource)
        self.assertEqual('random-names', p.resource('random-names').name)

        r = p.find_first('Root.DataFile')
        print(r.resolved_url)
        self.assertEqual('http://public.source.civicknowledge.com/example.com/sources/test_data.zip#renter_cost.csv',
                          str(r.resolved_url))

        for r in p.find('Root.DataFile'):

            if r.name != 'unicode-latin1':
                continue

            self.assertEqual(int(r.nrows), len(list(r)))

        self.assertEqual(['ipums', 'bordley', 'mcdonald', 'majumder'],
                          [c.name for c in p['Bibliography']])





if __name__ == '__main__':
    unittest.main()
