# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

from metapack import Downloader
from metapack.jupyter.convert import convert_documentation, convert_notebook, convert_wordpress,\
    extract_metatab, convert_hugo
from metapack.cli.core import prt, err, warn, get_config
from os import environ
from os.path import basename
import re

downloader = Downloader()


def notebook(subparsers):
    parser = subparsers.add_parser(
        'notebook',
        help='Convert Metatab-formatted Jupyter notebooks. ',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_notebook)

    parser.add_argument('notebook', nargs='?',
                        help="Path to a notebok file' ")

    parser.add_argument('-p', '--profile', help="Name of a BOTO or AWS credentails profile", required=False)

    parser.add_argument('--exceptions', default=False, action='store_true',
                        help='Show full stack tract for some unhandled exceptions')

    parser.set_defaults(handler=None)

    ##
    ## Build Group

    build_group = parser.add_argument_group('Building Metatab Files', 'Build and manage a metatab file for a pacakge')

    build_group.add_argument('-m', '--metatab', default=False, action='store_true',
                             help='Extract the metatab file')

    build_group.add_argument('-l', '--lines', default=False, action='store_true',
                             help='When displaying a Metatab file, display as lines, not as CSV')

    build_group.add_argument('-P', '--package', default=False, action='store_true',
                             help='Build a package from a Jupyter notebook')

    build_group.add_argument('-D', '--documentation', default=False, action='store_true',
                             help='With -M, make only the documentation')

    build_group.add_argument('-H', '--hugo', default=False, nargs='?',
                             help='Write images and Markdown into a Hugo statis site directory. or use METAPACK_HUGO_DIR env var')

    build_group.add_argument('-w', '--wordpress', default=False, nargs='?',
                             help='Publish the notebook to a Wordpress blog as a post. Arg refers to credentials in the config')

    build_group.add_argument('-W', '--wordpress-page', default=False, nargs='?',
                             help='Publish the notebook to a Wordpress blog as a page. Arg refers to credentials in the config')

def run_notebook(args):

    # Maybe need to convert a notebook first
    if args.package:
        convert_notebook(args.notebook)

    elif args.documentation:
        convert_documentation(args.notebook)

    elif args.metatab:
        doc = extract_metatab(args.notebook)

        if args.lines:
            for line in doc.lines:
                print(": ".join(line))
        else:
            print(doc.as_csv())

    elif args.hugo:
        convert_hugo(args.notebook,args.hugo)

    elif args.wordpress:

        from os import makedirs
        from os.path import exists
        from metapack.util import ensure_dir

        p = '/tmp/metapack-wp-notebook/'
        ensure_dir(p)

        output_file, resources = convert_wordpress(args.notebook, p)

        r, post = publish_wp(args.wordpress, output_file, resources)
        prt("Post url: ", post.link)

def get_site_config(site_name):
    from textwrap import dedent
    config = get_config()

    if not config:
        err("No metatab configuration found. Can't get Wordpress credentials")

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
    import json
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
        return dict( (e['key'],e['value']) for e in post.custom_fields)

    post = None
    for _post in wp.call(GetPosts()):
        if cust_field_dict(_post).get('identifier') == fm['identifier']:
            post = _post
            prt("Updating old post")
            break

    if not post:
        post = WordPressPost()
        post.id = wp.call(NewPost(post))
        prt("Creating new post")

    post.title = fm.get('title','')
    post.slug = fm.get('slug')

    with open(output_file) as f:
        content = f.read()

    post.terms_names = {
        'post_tag': ['test', 'firstpost'],
        'category': ['Introductions', 'Tests']
    }
    post.custom_fields = [
        {'key': 'identifier', 'value': fm['identifier']},

    ]

    post.excerpt = meta.get('bref', meta.get('description'))

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
            prt("Post already has image:", extant_image.link)
            img_to = extant_image.link

        elif r.endswith('.png'): # Foolishly assuming all images are PNGs
            response = wp.call(UploadFile(image_data, overwrite=True))

            prt("Uploaded image {} to id={}, {}".format(basename(r), response['id'], response['link']))

            img_to = response['link']

        content = content.replace(img_from, img_to)


    post.content = content

    r = wp.call(EditPost(post.id, post))

    return r,  wp.call(GetPost(post.id))