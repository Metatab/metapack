import unittest
from csv import DictReader
from metapack import MetapackDoc

from appurl import parse_app_url
from metapack import MetapackPackageUrl,  MetapackUrl, ResourceError, Downloader
from metapack.cli.core import (make_filesystem_package, make_s3_package, make_excel_package, make_zip_package, make_csv_package,
                                PACKAGE_PREFIX, cli_init )
from rowgenerators import get_generator, RowGeneratorError
from metatab.generate import TextRowGenerator

downloader = Downloader()


def test_data(*paths):
    from os.path import dirname, join, abspath
    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


def cache_fs():
    from fs.tempfs import TempFS
    return TempFS('rowgenerator')

class TestPublish(unittest.TestCase):


    def test_config(self):
        from metapack.cli.core import get_config

        print(get_config())



    def test_publish_wp(self):
        pass

        from wordpress_xmlrpc import Client, WordPressPost
        from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
        from wordpress_xmlrpc.methods.users import GetUserInfo

        wp = Client('http://busboom.org/wptest/xmlrpc.php', 'test', 'F5@w@@NrqQRgUHdtcCdEZEmD')

        print(wp.call(GetPosts()))

        print(wp.call(GetUserInfo()))

        post = WordPressPost()
        post.title = 'My new title'
        post.content = 'This is the body of my new post.'
        post.terms_names = {
          'post_tag': ['test', 'firstpost'],
          'category': ['Introductions', 'Tests']
        }
        post.custom_fields = [
            {'key': 'cf_1','value':'cfv_1'},
            {'key': 'cf_2', 'value': 'cfv_2'}
        ]
        wp.call(NewPost(post))

    def test_list_wp(self):

        from wordpress_xmlrpc import Client, WordPressPost
        from wordpress_xmlrpc.methods.posts import GetPosts
        from wordpress_xmlrpc.methods.taxonomies import GetTaxonomies
        from wordpress_xmlrpc.methods.media import GetMediaLibrary

        wp = Client('http://busboom.org/wptest/xmlrpc.php', 'test', 'F5@w@@NrqQRgUHdtcCdEZEmD')

        for p in wp.call(GetPosts()):
            print(p, p.slug,)
            for t in  p.custom_fields:
                print ('   ',t)
            print('   ','---')
            for img in wp.call(GetMediaLibrary(dict(parent_id=p.id))):
                print('   ',img.id, img.metadata, img.link )


if __name__ == '__main__':
    unittest.main()
