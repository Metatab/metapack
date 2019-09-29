import unittest


class TestDisplay(unittest.TestCase):
    """"""

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

    def test_contacts(self):

        from metapack.html import process_contact
        from itertools import combinations
        import json
        from textwrap import dedent

        parts = ['email', 'organization', 'url', 'name']

        out = {}

        for l in range(1, 5):
            for c in combinations(zip(parts, parts), l):
                out[','.join(sorted(dict(c).keys()))] = ','.join(process_contact(dict(c))['parts'])

        outs = json.dumps(out, indent=4)

        gauge_s = dedent("""
        {
            "email": "[email](mailto:email)",
            "organization": "organization",
            "url": "[url](url)",
            "name": "name",
            "email,organization": "organization,[email](mailto:email)",
            "email,url": "[url](url),[email](mailto:email)",
            "email,name": "[name](mailto:email)",
            "organization,url": "[organization](url)",
            "name,organization": "name,organization",
            "name,url": "name,[url](url)",
            "email,organization,url": "[organization](url),[email](mailto:email)",
            "email,name,organization": "[name](mailto:email),organization",
            "email,name,url": "[name](mailto:email),url",
            "name,organization,url": "name,[organization](url)",
            "email,name,organization,url": "[name](mailto:email),[organization](url)"
        }
        """).strip()

        self.assertEqual(gauge_s, outs)


if __name__ == '__main__':
    unittest.main()
