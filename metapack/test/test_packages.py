import unittest
from csv import DictReader

from metapack import MetapackDoc
from metapack import MetapackPackageUrl, MetapackUrl, ResourceError, Downloader
from metapack.cli.core import (make_filesystem_package, make_s3_package, make_excel_package, make_zip_package,
                               make_csv_package,
                               PACKAGE_PREFIX, cli_init)
from metapack.test.support import test_data
from metatab.generate import TextRowGenerator
from rowgenerators import get_generator,  parse_app_url
from rowgenerators.exceptions import RowGeneratorError
import platform

downloader = Downloader()


class TestPackages(unittest.TestCase):
    def test_resolve_resource_urls(self):
        """Test how resources are resolved in packages.
            - A name, for excel and CSV packages
            - a path, for ZIP and filesystem packages
            - a web url, for any kind of package
        """
        with open(test_data('packages.csv')) as f:
            for i, l in enumerate(DictReader(f)):


                print(l['url'], l['target_file'])

                u = MetapackPackageUrl(l['url'], downloader=Downloader())

                try:
                    t = u.resolve_url(l['target_file'])
                    self.assertFalse(bool(l['resolve_error']))
                except ResourceError as e:
                    self.assertTrue(bool(l['resolve_error']))
                    continue

                # Testing containment because t can have path in local filesystem, which changes depending on where
                # test is run



                print("   ", t)
                self.assertTrue(l['resolved_url'] in str(t), (i, l['resolved_url'], str(t)))

                try:
                    g = get_generator(t.get_resource().get_target())


                    self.assertEqual(101, len(list(g)))
                    self.assertFalse(bool(l['generate_error']))
                except RowGeneratorError:
                    self.assertTrue(bool(l['generate_error']))
                    continue

    def test_build_package(self):

        try:
            import shapely
            import pyproj
        except ImportError:
            unittest.skip("Pandas not installed")
            return

        cli_init()

        m = MetapackUrl(test_data('packages/example.com/example.com-full-2017-us/metadata.csv'),
                        downloader=downloader)

        package_dir = m.package_url.join_dir(PACKAGE_PREFIX)

        cache = Downloader().cache

        _, fs_url, created = make_filesystem_package(m, package_dir, cache, {}, False)

        print(created)

        return

        fs_url = MetapackUrl('/Volumes/Storage/proj/virt-proj/metapack/metapack/test-data/packages/example.com/' \
                             'example-package/_packages/example.com-example_data_package-2017-us-1/metadata.csv',
                             downloader=downloader)

        # _, url, created =  make_excel_package(fs_url,package_dir,get_cache(), {}, False)

        # _, url, created = make_zip_package(fs_url, package_dir, get_cache(), {}, False)

        # _, url, created = make_csv_package(fs_url, package_dir, get_cache(), {}, False)

        package_dir = parse_app_url('s3://test.library.civicknowledge.com/metatab', downloader=downloader)

        _, url, created = make_s3_package(fs_url, package_dir, cache, {}, False)

        print(url)
        print(created)

    def test_build_simple_package(self):

        cli_init()

        cache = Downloader().cache

        m = MetapackUrl(test_data('packages/example.com/example.com-simple_example-2017-us'), downloader=downloader)

        package_dir = m.package_url.join_dir(PACKAGE_PREFIX)
        package_dir = package_dir

        _, fs_url, created = make_filesystem_package(m, package_dir, cache, {}, False)

        fs_doc = MetapackDoc(fs_url, cache=downloader.cache)

        r = fs_doc.resource('random-names')

        # Excel

        _, url, created = make_excel_package(fs_url, package_dir, cache, {}, False)

        self.assertEquals(['random-names', 'renter_cost', 'unicode-latin1'], [r.name for r in url.doc.resources()])

        self.assertEquals(['random-names', 'renter_cost', 'unicode-latin1'], [r.url for r in url.doc.resources()])

        # ZIP

        _, url, created = make_zip_package(fs_url, package_dir, cache, {}, False)

        self.assertEquals(['random-names', 'renter_cost', 'unicode-latin1'], [r.name for r in url.doc.resources()])

        self.assertEquals(['data/random-names.csv', 'data/renter_cost.csv', 'data/unicode-latin1.csv'],
                          [r.url for r in url.doc.resources()])

        #  CSV

        _, url, created = make_csv_package(fs_url, package_dir, cache, {}, False)

        self.assertEquals(['random-names', 'renter_cost', 'unicode-latin1'], [r.name for r in url.doc.resources()])


        self.assertEquals(
            ['com-simple_example-2017-us-2/data/random-names.csv',
             '.com-simple_example-2017-us-2/data/renter_cost.csv',
             'm-simple_example-2017-us-2/data/unicode-latin1.csv'],
            [str(r.url)[-50:] for r in url.doc.resources()])

    def test_sync_csv_package(self):

        from metapack.package import CsvPackageBuilder

        package_root = MetapackPackageUrl(
            test_data('packages/example.com/example.com-simple_example-2017-us/_packages'), downloader=downloader)

        source_url = 'http://library.metatab.org/example.com-simple_example-2017-us-2/metadata.csv'

        u = MetapackUrl(source_url, downloader=downloader)

        t = u.get_resource().get_target()

        p = CsvPackageBuilder(u, package_root, resource_root=u.dirname().as_type(MetapackPackageUrl))

        csv_url = p.save()

        doc = csv_url.metadata_url.doc

        for r in doc.resources():
            print(r.name, r.url)

            # with open(csv_url.path, mode='rb') as f:
            #    print (f.read())
            #    #urls.append(('csv', s3.write(f.read(), csv_url.target_file, acl)))

    @unittest.skip('References non existen url')
    def test_build_geo_package(self):

        from rowgenerators.valuetype import ShapeValue

        m = MetapackUrl(test_data('packages/sangis.org/sangis.org-census_regions/metadata.csv'), downloader=downloader)

        package_dir = m.package_url.join_dir(PACKAGE_PREFIX)

        _, fs_url, created = make_filesystem_package(m, package_dir, downloader.cache, {}, True)

        print(fs_url)

        doc = MetapackDoc(fs_url)

        r = doc.resource('sra')

        rows = list(r.iterdict)

        self.assertEqual(41, len(rows))

        self.assertIsInstance(rows[1]['geometry'], ShapeValue)

    def test_build_transform_package(self):

        m = MetapackUrl(test_data('packages/example.com/example.com-transforms/metadata.csv'), downloader=downloader)

        package_dir = m.package_url.join_dir(PACKAGE_PREFIX)

        _, fs_url, created = make_filesystem_package(m, package_dir, downloader.cache, {}, False)

        print(fs_url)

    def test_read_geo_packages(self):
        try:
            from publicdata.censusreporter.dataframe import CensusDataFrame
        except ImportError:
            unittest.skip("Public data isn't installed")
            return

        from metapack.jupyter.pandas import MetatabDataFrame
        from metapack.jupyter.pandas import MetatabSeries
        from geopandas.geoseries import GeoSeries
        from rowgenerators.valuetype import ShapeValue

        with open(test_data('line', 'line-oriented-doc.txt')) as f:
            text = f.read()

        doc = MetapackDoc(TextRowGenerator("Declare: metatab-latest\n" + text))

        r = doc.reference('B09020')
        df = r.dataframe()

        self.assertIsInstance(df, CensusDataFrame)

        r = doc.reference('sra_geo')
        df = r.dataframe()

        self.assertIsInstance(df, MetatabDataFrame)

        self.assertIsInstance(df.geometry, MetatabSeries)

        self.assertIsInstance(df.geo.geometry, GeoSeries)

        row = next(r.iterdict)

        self.assertIsInstance(row['geometry'], ShapeValue, type(row['geometry']))


    @unittest.skipIf(platform.system() == 'Windows','Program generators do not work on windows')
    def test_program_resource(self):

        m = MetapackUrl(test_data('packages/example.com/example.com-full-2017-us/metadata.csv'), downloader=downloader)

        doc = MetapackDoc(m)

        r = doc.resource('rowgen')

        self.assertEqual('program+file:scripts/rowgen.py', str(r.url))

        print(r.resolved_url)

        g = r.row_generator

        print(type(g))

        for row in r:
            print(row)

    def test_fixed_resource(self):
        from itertools import islice
        from rowgenerators.generator.fixed import FixedSource

        m = MetapackUrl(test_data('packages/example.com/example.com-full-2017-us/metadata.csv'), downloader=downloader)

        doc = MetapackDoc(m)

        r = doc.resource('simple-fixed')

        self.assertEqual('fixed+http://public.source.civicknowledge.com/example.com/sources/simple-example.txt',
                         str(r.url))
        self.assertEqual('fixed+http://public.source.civicknowledge.com/example.com/sources/simple-example.txt',
                         str(r.resolved_url))

        g = r.row_generator

        print(r.row_processor_table())

        self.assertIsInstance(g, FixedSource)

        rows = list(islice(r, 10))

        print('----')
        for row in rows:
            print(row)

        self.assertEqual('f02d53a3-6bbc-4095-a889-c4dde0ccf5', rows[5][1])

    def test_petl(self):
        from petl import look

        m = MetapackUrl(test_data('packages/example.com/example.com-full-2017-us/metadata.csv'), downloader=downloader)

        doc = MetapackDoc(m)

        r = doc.resource('simple-example')

        t = r.resolved_url.get_resource().get_target()

        p = r.petl()

        print(look(p))

    def test_metapack_resources(self):

        cli_init()

        p = test_data('packages/example.com/example.com-metab_reuse/metadata.csv')

        m = MetapackUrl(p,downloader=downloader)

        print (m.doc.resources())

        print(m.get_resource().get_target().exists())


if __name__ == '__main__':
    unittest.main()
