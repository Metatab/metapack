import unittest
from csv import DictReader
from os.path import exists

from rowgenerators import get_generator, parse_app_url
from rowgenerators.appurl.archive import ZipUrl
from rowgenerators.appurl.file import CsvFileUrl
from rowgenerators.appurl.web import WebUrl
from support import test_data

from metapack.appurl import MetapackDocumentUrl, MetapackResourceUrl


class TestUrls(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

    def test_metapack_urls(self):

        groups = {}

        with open(test_data('mpurls.csv')) as f:
            for i, l in enumerate(DictReader(f)):

                #print(i,l['in_url'])

                u = parse_app_url(l['in_url'])

                self.assertEqual(l['url_class'], u.__class__.__name__)
                self.assertEqual(l['url'], str(u))
                self.assertEqual(l['package_url'], str(u.package_url))

                # The second instance in each group is a resource url for the the
                # metadata url of the first instance.
                if (l['url_class'] == 'MetapackDocumentUrl'):

                    self.assertNotIn(l['group'], groups)
                    self.assertEqual(str(u), str(u.metadata_url))
                else:
                    self.assertIn(l['group'], groups)
                    self.assertEqual(str(groups[l['group']]), str(u.metadata_url))

                groups[l['group']] = u

                self.assertEqual(l['metadata_url'], str(u.metadata_url))

                r = u.get_resource()
                self.assertTrue(r.inner.exists())

                t = r.get_target()
                try:
                    self.assertTrue(t.inner.exists(), (type(r), t, t.inner))
                except AssertionError:
                    t = r.get_target()

                # Check that the generator for the metadata gets the right number of rows
                self.assertEqual(50, len(list(u.metadata_url.generator)))

                self.assertEqual('example.com-simple_example-2017-us-1', (u.doc.find_first_value('Root.Name')))

    def test_metapack_url(self):

        # Zip

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.zip'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.zip#metadata.csv',
                         str(ud))
        self.assertIsInstance(ud, MetapackDocumentUrl)

        self.assertIsInstance(ud.inner, WebUrl)

        r = ud.get_resource()

        self.assertIsInstance(r, MetapackDocumentUrl)
        self.assertIsInstance(r.inner, ZipUrl)

        t = r.get_target()
        self.assertIsInstance(t.inner, CsvFileUrl)

        g = get_generator(t)
        self.assertEquals(50, len(list(g)))

        self.assertEquals('example.com-simple_example-2017-us-1', (ud.doc.find_first_value('Root.Name')))

        # Excel

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.xlsx'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.xlsx#meta',
                         str(ud))
        self.assertIsInstance(ud, MetapackDocumentUrl)
        self.assertEquals('example.com-simple_example-2017-us-1', (ud.doc.find_first_value('Root.Name')))

        # Filesystem
        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv',
                         str(ud))
        self.assertIsInstance(ud, MetapackDocumentUrl)
        self.assertEquals('example.com-simple_example-2017-us-1', (ud.doc.find_first_value('Root.Name')))

        # Filesystem
        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv',
                         str(ud))
        self.assertIsInstance(ud, MetapackDocumentUrl)
        self.assertEquals('example.com-simple_example-2017-us-1', (ud.doc.find_first_value('Root.Name')))

        self.assertTrue(str(ud.get_resource()).endswith(
            'library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv'))

        self.assertTrue(str(ud.get_resource().get_target()).endswith(
            'library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv'))

        # -----
        # Resource Urls

        us = 'metapack+http://library.metatab.org.s3.amazonaws.com/example.com-simple_example-2017-us-1/metadata.csv#random_names'

        ur = parse_app_url(us)
        self.assertEqual('metapack', ur.proto)
        self.assertIsInstance(ur, MetapackResourceUrl)

    def test_inner(self):
        u_s = 'metapack+http://public.source.civicknowledge.com.s3.amazonaws.com/example.com/geo/Parks_SD.zip#encoding=utf8'

        u = parse_app_url(u_s)

        self.assertIsInstance(u, MetapackDocumentUrl)
        self.assertIsInstance(u.inner, WebUrl)

        r = u.get_resource()
        self.assertIsInstance(r, MetapackDocumentUrl)
        self.assertIsInstance(r.inner, ZipUrl)


    def test_document_urls(self):

        urls = [
            ('metapack+http://example.com/packagename/', 'metadata.csv', 'metadata.csv'),
            ('metapack+http://example.com/packagename/metadata.csv', 'metadata.csv', 'metadata.csv'),
            ('metapack+http://example.com/packagename/metadata.txt', 'metadata.txt', 'metadata.txt'),
            ('metapack+http://example.com/packagename/metadata.ipynb', 'metadata.ipynb', 'metadata.ipynb'),
            ('metapack+http://example.com/packagename.csv', 'packagename.csv', 'packagename.csv'),
            ('metapack+http://example.com/packagename.txt', 'packagename.txt', 'packagename.txt'),
            ('metapack+http://example.com/packagename.ipynb', 'packagename.ipynb', 'packagename.ipynb'),
            ('metapack+http://example.com/packagename.xlsx', 'packagename.xlsx', 'meta')
        ]
        for us, rf, tf in urls:

            u = parse_app_url(us)
            print(type(u))
            self.assertEqual(rf, u.resource_file)
            self.assertEqual(tf, u.target_file)



    def test_fs_resource(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/#random_names'

        u = parse_app_url(us)

        self.assertIsInstance(u, MetapackResourceUrl, type(u))

        self.assertEquals('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv',
                          str(u.metadata_url))

        pu = u.package_url

        self.assertEquals('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/',str(pu))

    def test_xlsx_parse(self):

        ru = parse_app_url('/foo/bar/bax.xlsx',fragment='fragment')

        # print (repr(ru))

    def test_metatab_resource(self):

        u_str = 'metapack+http://library.metatab.org/ffiec.gov-cra_aggregate_smb-orig-1.csv#sb_agg_loan_orig'

        u = parse_app_url(u_str)

        print(type(u))

        print(u.resource)

    def test_metatab_resource_zip(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.zip#random-names'

        u = parse_app_url(us)

        doc = u.metadata_url.doc

        r = doc.resource(u.target_file)

        self.assertEqual(101, len(list(r)))

    def test_metatab_resource_xlsx(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.xlsx#random-names'

        u = parse_app_url(us)
        self.assertIsInstance(u, MetapackResourceUrl)
        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.xlsx#random-names',
                         str(u))

        self.assertEqual('random-names', u.target_file)


        return

        r = u.doc.resource(u.target_file)
        self.assertEqual('random-names',r.value)

        ru = r.resolved_url
        print('a', r.value)
        print ('b', ru)
        rur = ru.get_resource()
        print ('c', rur)
        rurt = rur.get_target()
        print ('d', rurt)

        self.assertEqual(101, len(list(r)))

    def test_metatab_resource_csv(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.csv#random-names'

        u = parse_app_url(us)
        doc = u.metadata_url.doc

        r = doc.resource(u.target_file)

        self.assertEqual(101, len(list(r)))

    def test_metatab_resource_fs(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv#random-names'

        u = parse_app_url(us)
        doc = u.metadata_url.doc

        r = u.resource
        ru = r.resolved_url

        # print(ru.inner)
        # print(ru.get_resource())

        return

    def test_shape_resource(self):
        us = 'http://library.metatab.org/sandiegodata.org-geography-2018-1/data/tract_boundaries.csv'
        u = parse_app_url(us)


    def test_metatab_resource_zip(self):
        from metapack.appurl import MetapackResourceUrl

        us = 'metapack+http://s3.amazonaws.com/library.metatab.org/ipums.org-income_homevalue-5.zip#income_homeval'

        u = parse_app_url(us)

        self.assertIsInstance(u, MetapackResourceUrl)


    def test_metatab_resource_fs_pkg(self):
        from metapack.appurl import MetapackDocumentUrl

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv'

        u = parse_app_url(us)

        self.assertIsInstance(u, MetapackDocumentUrl)


    @unittest.skip('Requires special setup')
    def test_search_url(self):
        from metapack.appurl import SearchUrl
        from os import getenv
        from unittest import SkipTest

        us = 'search:bc.edu-creations-comments#comments'

        u = parse_app_url(us)

        if getenv('METAPACK_DATA') is None or not exists(getenv('METAPACK_DATA')):
            raise SkipTest("Test requires the METAPACK_DATA envoironment variable to be set")

        search_func = SearchUrl.search_json_indexed_directory(getenv('METAPACK_DATA'))

        SearchUrl.register_search(search_func)

        self.assertEqual('metapack+file:/Volumes/Storage/Data/metapack/bc.edu-creations-comments-3.zip#comments',
                          str(u.get_resource()))

    def x_test_stata(self):

        from itertools import islice, chain
        from metapack import MetapackDoc
        from os import getcwd
        from os.path import dirname, join, relpath
        from rowgenerators.appurl.test import test_data as rg_test_data

        def chained(g):
            return list(chain(*islice(g, 10)))

        doc = MetapackDoc(test_data('empty_resources.csv'))

        # The main problem is with handling of relative paths
        base_path = relpath(dirname(rg_test_data.__file__) )

        u = parse_app_url(join(base_path, 'stata.dta'))
        self.assertTrue(140, len(chained(u.generator)))

        u = parse_app_url(join(base_path, 'stata_package.zip')+'#stata.dta', downloader=doc.downloader)
        self.assertTrue(140, len(chained(u.generator)))

        base_path = relpath(dirname(rg_test_data.__file__), dirname(test_data('empty_resources.csv')))

        doc['Resources'].new_term('Root.Datafile', join(base_path,
                                                        'stata.dta#&target_format=dta&values=codes'),
                                  name='stata_file')
        doc['Resources'].new_term('Root.Datafile', join(base_path, 'stata_package.zip')+'#stata.dta', \
                                                                                     name='stata_package')

        self.assertTrue( 140, len(chained(doc.resource('stata_file'))))
        self.assertTrue(140, len(chained(doc.resource('stata_package'))))

        g = doc.resource('stata_package').row_generator

        print(type(g))


if __name__ == '__main__':
    unittest.main()
