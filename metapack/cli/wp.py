# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

from metapack import Downloader
from metapack.cli.core import prt, err, warn, get_config
from os import environ
from os.path import basename
import re

downloader = Downloader.get_instance()


def wp(subparsers):
    parser = subparsers.add_parser(
        'wp',
        help='Publish a Jupyter notebook to Wordpress ',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_notebook)

    parser.add_argument('site_name', help="Site name, in the .metapack.yaml configuration file")

    parser.add_argument('notebook', help="Path to a notebook file")

    parser.add_argument('-p', '--profile', help="Name of a BOTO or AWS credentails profile", required=False)


def run_notebook(args):
    from metapack.jupyter.convert import convert_wordpress
    from metapack.util import ensure_dir

    p = '/tmp/metapack-wp-notebook/'
    ensure_dir(p)

    output_file, resources = convert_wordpress(args.notebook, p)

    r, post = publish_wp(args.site_name, output_file, resources)
    prt("Post url: ", post.link)

def get_site_config(site_name):
    from textwrap import dedent
    config = get_config()

    if config is None:
        err("No metatab configuration found. Can't get Wordpress credentials. Maybe create '~/.metapack.yaml'")

    site_config = config.get('wordpress', {}).get(site_name, {})

    if not site_config:
        err("In config file '{}', expected 'wordpress.{}' section for site config"
            .format(config['_loaded_from'], site_name))

    if 'url' not in site_config or 'user' not in site_config or 'password' not in site_config:
        err(dedent(
            """
            Incomplete configuration. Expected:
                wordpress.{site_name}.url
                wordpress.{site_name}.user
                wordpress.{site_name}.password
            In configuration file '{cfg_file}'
            """.format(site_name=site_name, cfg_file=config['_loaded_from'])
        ))

    return site_config['url'], site_config['user'], site_config['password']

def prepare_image(slug, file_name, post_id):
    from xmlrpc import client as xmlrpc_client

    # prepare metadata
    data = {
        'name': 'picture.jpg',
        'type': 'image/jpeg',  # mimetype
    }

    # read the binary file and let the XMLRPC library encode it into base64
    with open(file_name, 'rb') as img:
        return {
            'name': '{}-{}'.format(slug,basename(file_name)),
            'type': 'image/png',  # mimetype
            'bits': xmlrpc_client.Binary(img.read()),
            'post_id': post_id
        }


def publish_wp(site_name, output_file, resources):

    """Publish a notebook to a wordpress post, using Gutenberg blocks.

    Here is what the metadata looks like, in a section of the notebook tagged 'frontmatter'

    show_input: hide
    github: https://github.com/sandiegodata/notebooks/blob/master/tutorial/American%20Community%20Survey.ipynb
    identifier: 5c987397-a954-46ca-8743-bdcd7a71579c
    featured_image: 171
    authors:
    - email: eric@civicknowledge.com
      name: Eric Busboom
      organization: Civic Knowledge
      type: wrangler
    tags:
    - Tag1
    - Tag2
    categories:
    - Demographics
    - Tutorial

    'Featured_image' is an attachment id

    """

    import json
    import yaml
    from uuid import uuid4
    from wordpress_xmlrpc import Client, WordPressPost
    from wordpress_xmlrpc.methods.posts import GetPosts, NewPost, EditPost, GetPost
    from wordpress_xmlrpc.methods.users import GetUserInfo
    from wordpress_xmlrpc.methods.media import UploadFile, GetMediaLibrary

    # http://busboom.org/wptest/wp-content/uploads/sites/7/2017/11/output_16_0-300x200.png

    url, user, password = get_site_config(site_name)

    meta = {}
    for r in resources:
        if r.endswith('.json'):
            with open(r) as f:
                meta = json.load(f)

    fm = meta.get('frontmatter',{})

    if not 'identifier' in fm or not fm['identifier']:
        err("Can't publish notebook without a unique identifier. Add this to the "
            "Metatab document or frontmatter metadata:\n   identifier: {}".format(str(uuid4())))

    wp = Client(url, user, password)

    def cust_field_dict(post):
        try:
            return dict( (e['key'],e['value']) for e in post.custom_fields)
        except (KeyError, AttributeError):
            return {}

    post = None
    for _post in wp.call(GetPosts()):
        if cust_field_dict(_post).get('identifier') == fm['identifier']:
            post = _post
            break

    if post:
        prt("Updating old post")
    else:
        post = WordPressPost()
        post.id = wp.call(NewPost(post))
        prt("Creating new post")

    post.title = fm.get('title','')
    post.slug = fm.get('slug')

    with open(output_file) as f:
        content = f.read()

    post.terms_names = {
        'post_tag': fm.get('tags',[]),
        'category':  fm.get('categories',[])
    }

    print(yaml.dump(fm, default_flow_style=False))

    if not hasattr(post, 'custom_fields') or not 'identifier' in [ e['key'] for e in post.custom_fields]:

        post.custom_fields = [
            {'key': 'identifier', 'value': fm['identifier']},
        ]

    post.excerpt = fm.get('excerpt', fm.get('brief', fm.get('description')))

    def strip_image_name(n):
        """Strip off the version number from the media file"""
        from os.path import splitext
        import re
        return re.sub(r'\-\d+$','',splitext(n)[0])

    extant_files = list(wp.call(GetMediaLibrary(dict(parent_id=post.id))))

    def find_extant_image(image_name):
        for img in extant_files:
            if strip_image_name(basename(img.metadata['file'])) == strip_image_name(image_name):
                return img

        return None

    for r in resources:

        image_data = prepare_image(fm['identifier'], r, post.id)
        img_from = "/{}/{}".format(fm['slug'], basename(r))

        extant_image = find_extant_image(image_data['name'])

        if  extant_image:
            prt("Post already has image:", extant_image.id, extant_image.link)
            img_to = extant_image.link

        elif r.endswith('.png'): # Foolishly assuming all images are PNGs
            response = wp.call(UploadFile(image_data, overwrite=True))

            prt("Uploaded image {} to id={}, {}".format(basename(r), response['id'], response['link']))

            img_to = response['link']

        content = content.replace(img_from, img_to)

    if fm['featured_image']:
        post.thumbnail = int(fm['featured_image'])
    elif isinstance(post.thumbnail, dict):
        # The thumbnail expects an attachment id on EditPost, but returns a dict on GetPost
        post.thumbnail = post.thumbnail['attachment_id']


    post.content = content

    r = wp.call(EditPost(post.id, post))

    return r,  wp.call(GetPost(post.id))