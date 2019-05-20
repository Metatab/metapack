import unittest
import metapack as mp
from rowgenerators import parse_app_url
from metapack import Downloader
from pprint import pprint

downloader = Downloader()

class TestIssues(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

    def test_ref_resource_confusion(self):
        from metapack import open_package
        u = 'http://library.metatab.org/ffiec.gov-cra_disclosure_smb_orig-2010_2015-2.csv'

        p = open_package(u)

        self.assertEqual(1, len(list(r for r in p['Resources'].find('Root.Resource'))))


    def test_no_reference_descriptions(self):

        from metapack import MetapackDoc
        from metapack.test.support import test_data
        from metatab.rowgenerators import TextRowGenerator

        mt_lines="""
Declare: metatab-latest
Identifier: foobar
Name: sandiegodata.org-cra_demo-1

Dataset: foobar
Origin: civiknowledge.com
Version: 1


Section: References

Reference: metapack+http://library.metatab.org/ffiec.gov-cra_aggregate_smb-orig-4.csv#sb_agg_loan_orig
Reference.Name: agg_loan_orig
Reference.Description: CRA Loan originations, aggregated to tracts.
        """

        doc = MetapackDoc(TextRowGenerator(mt_lines))

        r = doc.reference('agg_loan_orig')

        for c in r.columns():
            print(c.get('name'), c.get('description'))

    def test_refs_not_using_schemas(self):

        from metapack import  MetapackDoc
        from rowgenerators.valuetype import ShapeValue
        from metapack.test.support import test_data
        from metatab.rowgenerators import TextRowGenerator

        with open(test_data('line', 'line-oriented-doc.txt')) as f:
            text = f.read()

        doc = MetapackDoc(TextRowGenerator("Declare: metatab-latest\n" + text))

        r = doc.reference('sra_geo')

        self.assertEqual('civicknowledge.com-rcfe_affordability-2015-4',r.doc.name)
        self.assertEqual('sangis.org-census_regions-2010-sandiego-7', r.resolved_url.resource.doc.name)

        rs = r.resolved_url.resource

        self.assertIsNotNone(rs.row_processor_table())

        self.assertEqual([int,int,str,ShapeValue],  list(type(c) for c in list(rs)[1]))

        self.assertIsNone(r.row_processor_table())

        self.assertEqual([int, int, str, ShapeValue], list(type(c) for c in list(r)[1]))

        for c in rs.columns():
            print(c.get('description'))

        print('---')

        for c in r.columns():
            print(c.get('description'))


    def x_test_csv_join(self):



        import metapack as mp

        pkg = mp.open_package('http://library.metatab.org/noaa.gov-localclimate-200808_201807-san-3.csv')

        for t in pkg['Documentation'].find('Root.Documentation'):
            u = parse_app_url(t.value)

            t = pkg.package_url.join_target(u).get_resource().get_target()
            print("u=",u)
            print("pu=",pkg.package_url)
            print("jt=",pkg.package_url.join_target(u))
            print("R=",pkg.package_url.join_target(u).get_resource() )
            print('A', t._fragment)


    def x_test_wack_doc_urls(self):
        """Getting inline documentation fails when the package URL is for an online CSV package"""

        import metapack as mp

        from rowgenerators import parse_app_url

        pkg = mp.open_package('http://library.metatab.org/noaa.gov-localclimate-200808_201807-san-3.csv')

        for t in pkg['Documentation'].find('Root.IncludeDocumentation'):
            u = parse_app_url(t.value)

            t = pkg.package_url.join_target(u).get_resource().get_target()
            print("u=",u)
            print("pu=",pkg.package_url)
            print("jt=",pkg.package_url.join_target(u))
            print("R=",pkg.package_url.join_target(u).get_resource() )
            print('A', t._fragment)


        pkg = mp.open_package('http://library.metatab.org/noaa.gov-localclimate-200808_201807-san-3.zip')

        for t in pkg['Documentation'].find('Root.IncludeDocumentation'):
            u = parse_app_url(t.value)

            t = pkg.package_url.join_target(u).get_resource().get_target()
            self.assertTrue(t.exists())
            self.assertTrue(t.path.endswith('README.md'))

        pkg = mp.open_package('/Users/eric/Library/Application '
                              'Support/metapack/library.metatab.org/noaa.gov-localclimate-200808_201807-san-3/')

        for t in pkg['Documentation'].find('Root.IncludeDocumentation'):
            u = parse_app_url(t.value)
            t = pkg.package_url.join_target(u).get_resource().get_target()
            self.assertTrue(t.exists())
            self.assertTrue(t.path.endswith('README.md'))

    def x_test_multi_load_geoframe(self):



        pkg = mp.open_package('/Users/eric/proj/virt-proj/data-project/gis-projects/sandiegodata.org-stormdrains/')

        comm = pkg.reference('communities').geoframe()

        dc = pkg.reference('drain_conveyance_file').geoframe().dropna(subset=['geometry'])

        dc.to_crs(comm.crs)

    @unittest.skip('Has local path')
    def test_something_about_package_references(self):

        us = '/Users/eric/proj/virt-proj/planning/planning-database/datasets/sangis.org-business_sites/metadata.csv'

        pkg = mp.open_package(us)

        r = pkg.reference('tracts_boundaries')

        rr = r.resolved_url

        self.assertEqual('metapack+http://library.metatab.org/sandiegodata.org-geography-2018-1.csv#tract_boundaries', str(rr))

        print(rr.resource)

        df = r.dataframe()

    def test_mp_url_drop_frag(self):

        from metapack import MetapackUrl
        from metapack import MetapackUrl, Downloader

        downloader = Downloader()

        us = '.#resource'

        u = parse_app_url(us, downloader=downloader)

        mpu = MetapackUrl(u.fspath.resolve(), downloader=downloader)

        print(u, u.fspath.resolve(), mpu)


    def test_broken_metatab_urls(self):
        from metapack.appurl import  MetapackDocumentUrl

        # Filesystem
        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv',
                         str(ud))


        u = MetapackDocumentUrl('/Users/eric/proj/data-projects/metatab-packages/census.foobtomtoob', downloader=downloader)
        print(str(u))

    def test_broken_package_urls(self):
        from metapack import open_package
        from metapack.appurl import MetapackPackageUrl

        p = open_package('metapack+file:///Users/eric/proj/data-projects/cde.ca.gov/cde.ca.gov-current_expense/metadata.csv')

        u  = parse_app_url('file:README.md')

        r = p.package_url.join_target(u).get_resource()

        print(p.package_url)
        print(r)
        del r._parts['fragment']
        del r._parts['fragment_query']
        print(r.get_target())
        pprint(r._parts)



if __name__ == '__main__':
    unittest.main()
