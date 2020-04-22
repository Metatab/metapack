import unittest
from textwrap import dedent

from metatab.rowgenerators import TextRowGenerator

from metapack import Downloader, MetapackDoc

downloader = Downloader()


class TestIssues(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

    def test_integer_version(self):
        mt_lines = dedent("""
        Declare: metatab-latest
        Identifier: foobar

        Dataset: foobar
        Origin: foo.com
        Version: 1


        Section: References

        """)

        doc = MetapackDoc(TextRowGenerator(mt_lines))

        self.assertEqual('foo.com-foobar-1', doc._generate_identity_name())
        self.assertEqual('foo.com-foobar-1', doc._generate_identity_name(False))
        self.assertEqual('foo.com-foobar', doc._generate_identity_name(None))
        self.assertEqual('foo.com-foobar-10', doc._generate_identity_name(10))

        self.assertEqual('foo.com-foobar', doc.nonver_name)

        # Semantic

        mt_lines = dedent("""
        Declare: metatab-latest
        Identifier: foobar

        Dataset: foobar
        Origin: foo.com
        Version:
        Version.Major: 1
        Version.Minor: 2
        Version.Patch: 3

        Section: References

        """)

        doc = MetapackDoc(TextRowGenerator(mt_lines))

        self.assertEqual('foo.com-foobar-1.2.3', doc._generate_identity_name())
        self.assertEqual('foo.com-foobar-1.2.3', doc._generate_identity_name(False))
        self.assertEqual('foo.com-foobar', doc._generate_identity_name(None))
        self.assertEqual('foo.com-foobar-1.2.10', doc._generate_identity_name(10))

        self.assertEqual('foo.com-foobar', doc.nonver_name)

        mt_lines = dedent("""
        Declare: metatab-latest
        Identifier: foobar

        Dataset: foobar
        Origin: foo.com
        Version:
        Version.Major: 1

        Section: References

        """)

        doc = MetapackDoc(TextRowGenerator(mt_lines))

        self.assertEqual('foo.com-foobar-1.1.1', doc._generate_identity_name())
        self.assertEqual('foo.com-foobar-1.1.1', doc._generate_identity_name(False))
        self.assertEqual('foo.com-foobar', doc._generate_identity_name(None))
        self.assertEqual('foo.com-foobar-1.1.10', doc._generate_identity_name(10))

        self.assertEqual('foo.com-foobar', doc.nonver_name)


if __name__ == '__main__':
    unittest.main()
