import unittest

from metapack import MetapackDoc
from metapack import MetapackUrl, Downloader
from metapack.terms import Reference, Resource
from metapack.test.support import test_data
from metatab import TermParser
from metatab.generate import TextRowGenerator


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

    def test_line_oriented(self):

        doc = MetapackDoc(TextRowGenerator("Declare: metatab-latest"))

        with open(test_data('line','line-oriented-doc.txt')) as f:
            text = f.read()

        tp = TermParser(TextRowGenerator(text), resolver=doc.resolver, doc=doc)

        doc.load_terms(tp)

        self.assertEqual('47bc1089-7584-41f0-b804-602ec42f1249', doc.get_value('Root.Identifier'))
        self.assertEqual(148, len(doc.terms))

        self.assertEqual(5, len(list(doc['References'])))

        self.assertEqual(5, len(list(doc['References'].find('Root.Reference'))))

        self.assertEqual(5, len(list(doc['References'].find('Root.Resource'))))  # References are Resources

        rt = list(doc['References'].find('Root.Resource'))[0]

        self.assertIsInstance(rt, Reference)

    def test_line_doc_parts(self):

        doc = MetapackDoc(TextRowGenerator("Declare: metatab-latest"))

        for fn in ('line/line-oriented-doc-root.txt',
                   'line/line-oriented-doc-contacts.txt',
                   'line/line-oriented-doc-datafiles.txt',
                   'line/line-oriented-doc-references-1.txt',
                   'line/line-oriented-doc-references-2.txt',
                   'line/line-oriented-doc-bib.txt',
                   ):
            with open(test_data(fn)) as f:
                text = f.read()

            tp = TermParser(TextRowGenerator(text), resolver=doc.resolver, doc=doc)

            doc.load_terms(tp)

        self.assertEqual('47bc1089-7584-41f0-b804-602ec42f1249', doc.get_value('Root.Identifier'))
        self.assertEqual(153, len(doc.terms))

        self.assertEqual(5, len(list(doc['References'])))

        self.assertEqual(5, len(list(doc['References'].find('Root.Reference'))))

        self.assertEqual(5, len(list(doc['References'].find('Root.Resource'))))  # References are Resources

        rt = list(doc['References'].find('Root.Resource'))[0]

        self.assertIsInstance(rt, Reference)

        self.assertEqual(5, len(list(doc['Resources'])))

        self.assertEqual(5, len(list(doc['Resources'].find('Root.Datafile'))))

        self.assertEqual(5, len(list(doc['Resources'].find('Root.Resource'))))  # References are Resources

        rt = list(doc['Resources'].find('Root.Resource'))[0]

        self.assertIsInstance(rt, Resource)

        doc._repr_html_() # Check no exceptions



if __name__ == '__main__':
    unittest.main()
