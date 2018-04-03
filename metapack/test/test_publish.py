import unittest

from metapack import Downloader

downloader = Downloader()



class TestPublish(unittest.TestCase):


    def test_config(self):
        from metapack.cli.core import get_config

        print(get_config())


    @unittest.skip("Need Sensible Credentials")
    def test_publish_wp(self):
        pass

        from wordpress_xmlrpc import Client, WordPressPost
        from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
        from wordpress_xmlrpc.methods.users import GetUserInfo

        wp = Client('url', 'user', 'password')

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

    @unittest.skip("Need Sensible Credentials")
    def test_list_wp(self):

        from wordpress_xmlrpc import Client
        from wordpress_xmlrpc.methods.posts import GetPosts
        from wordpress_xmlrpc.methods.media import GetMediaLibrary

        wp = Client('url', 'user', 'password')

        for p in wp.call(GetPosts()):
            print(p, p.slug,)
            for t in  p.custom_fields:
                print ('   ',t)
            print('   ','---')
            for img in wp.call(GetMediaLibrary(dict(parent_id=p.id))):
                print('   ',img.id, img.metadata, img.link )


if __name__ == '__main__':
    unittest.main()
