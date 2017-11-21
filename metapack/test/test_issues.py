


import unittest
from appurl import parse_app_url, match_url_classes, WebUrl, FileUrl, ZipUrl, CsvFileUrl

from metapack import MetapackDoc
from metapack.appurl import MetapackUrl, MetapackResourceUrl, MetapackDocumentUrl
from rowgenerators import get_generator
from csv import DictReader
from metapack.test.support import test_data


class TestIssues(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""



    def test_ref_resource_confusion(self):
        from metapack import open_package
        u = 'http://library.metatab.org/ffiec.gov-cra_disclosure_smb_orig-2010_2015-2.csv'

        p = open_package(u)

        self.assertEqual(1, len(list(r for r in p['Resources'].find('Root.Resource'))))



if __name__ == '__main__':
    unittest.main()
