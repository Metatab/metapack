import unittest

from metapack import MetapackDoc
from metapack.test.support import test_data
from metatab.generate import TextRowGenerator

class TestIssues(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""



    def test_ref_resource_confusion(self):
        from metapack import open_package
        u = 'http://library.metatab.org/ffiec.gov-cra_disclosure_smb_orig-2010_2015-2.csv'

        p = open_package(u)

        self.assertEqual(1, len(list(r for r in p['Resources'].find('Root.Resource'))))


    def test_no_reference_descriptions(self):

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
        from rowgenerators.valuetype import ShapeValue

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


if __name__ == '__main__':
    unittest.main()
