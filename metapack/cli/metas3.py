# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

from os import getcwd, getenv
from os.path import basename

from botocore.exceptions import  NoCredentialsError


from metapack import MetapackDoc, MetapackUrl
from metapack import MetapackPackageUrl
from metapack.cli.core import prt, err, make_s3_package, PACKAGE_PREFIX
from metapack.package import *
from metapack.package.s3 import S3Bucket
from metapack.util import datetime_now
from metatab import DEFAULT_METATAB_FILE
from rowgenerators import parse_app_url
from rowgenerators.util import clean_cache
from rowgenerators.util import fs_join as join

class MetapackCliMemo(object):

    def __init__(self, args):
        from appurl import get_cache
        self.cwd = getcwd()

        self.args = args

        self.downloader = Downloader()

        self.cache = self.downloader.cache

        self.mtfile_arg = self.args.metatabfile if self.args.metatabfile else join(self.cwd, DEFAULT_METATAB_FILE)

        self.mtfile_url = MetapackUrl(self.mtfile_arg, downloader=self.downloader)

        self.resource = self.mtfile_url.fragment

        self.package_url = self.mtfile_url.package_url
        self.mt_file = self.mtfile_url.metadata_url

        self.package_root = self.package_url.join(PACKAGE_PREFIX)

        if not self.args.s3:
            doc = MetapackDoc(self.mt_file)
            self.args.s3 = doc['Root'].find_first_value('Root.S3')

        self.s3_url = parse_app_url(self.args.s3)

        if not self.s3_url.scheme == 's3':
            self.s3_url = parse_app_url("s3://{}".format(self.args.s3))

        self.doc = MetapackDoc(self.mt_file)

        access_value = self.doc.find_first_value('Root.Access')

        self.acl = 'private' if access_value == 'private' else 'public-read'

        self.bucket = S3Bucket(self.s3_url, acl=self.acl , profile=self.args.profile)


def metas3(subparsers):

    parser = subparsers.add_parser(
        's3',
        help='Create packages and store them in s3 buckets',
    )

    parser.set_defaults(run_command=run_s3)

    parser.add_argument('-p', '--profile', help="Name of a BOTO or AWS credentails profile", required=False)

    parser.add_argument('-s', '--s3', help="URL to S3 where packages will be stored", required=False)

    parser.add_argument('-C', '--credentials', help="Show S3 Credentials and exit. "
                                                    "Eval this string to setup credentials in other shells.",
                        action='store_true', default=False)

    parser.add_argument('metatabfile', nargs='?', help='Path to a Metatab file')


def find_packages(name, pkg_dir):
    """Locate pre-built packages in the _packages directory"""
    for c in (FileSystemPackageBuilder, ZipPackageBuilder, ExcelPackageBuilder):

        package_path, cache_path = c.make_package_path(pkg_dir, name)

        if package_path.exists():

            yield c.type_code, package_path, cache_path #c(package_path, pkg_dir)

def run_s3(args):

    m = MetapackCliMemo(args)

    if m.args.credentials:
        show_credentials(m.args.profile)
        exit(0)

    dist_urls = upload(m)

    if dist_urls:
        prt("Synchronized these Package Urls")
        prt("-------------------------------")
        for au in dist_urls:
            prt(au)
        prt("-------------------------------")

    else:
        prt("Did not find any packages to upload")


    set_distributions(m, dist_urls)

def set_distributions(m, dist_urls):

    for t in m.doc.find('Root.Distribution'):
        m.doc.remove_term(t)

    for au in dist_urls:
        m.doc['Root'].new_term('Root.Distribution', au)

    m.doc.write_csv()


def upload(m):

    dist_urls = []

    fs_p = None

    for ptype, purl, cache_path in find_packages(m.doc.get_value('Root.Name'), m.package_root):
        au = m.bucket.access_url(cache_path)

        if ptype in ('xlsx', 'zip'):
            with open(purl.path, mode='rb') as f:
                m.bucket.write(f.read(), basename(purl.path), m.acl)
                prt("Added {} distribution: {} ".format(ptype, au))
                dist_urls.append(au)

        elif ptype == 'fs':

            env = {}
            skip_if_exist = False

            try:
                s3_package_root = MetapackPackageUrl(str(m.s3_url), downloader=m.downloader)

                fs_p, fs_url, created = make_s3_package(purl.metadata_url, s3_package_root, m.cache, env, m.acl, skip_if_exist)
            except NoCredentialsError:
                print(getenv('AWS_SECRET_ACCESS_KEY'))
                err("Failed to find boto credentials for S3. "
                    "See http://boto3.readthedocs.io/en/latest/guide/configuration.html ")

            # A crappy hack. make_s3_package should return the correct url
            if fs_p:
                if m.acl == 'private':
                    au = fs_p.private_access_url.inner
                else:
                    au = fs_p.public_access_url.inner

                dist_urls.append(au)

    m.doc['Root'].get_or_new_term('Root.Issued').value = datetime_now()

    if dist_urls:

        # Create the CSV package, with links into the
        if fs_p:
            u = MetapackUrl(fs_p.access_url, downloader=m.downloader)

            resource_root = u.dirname().as_type(MetapackPackageUrl)

            p = CsvPackageBuilder(u, m.package_root, resource_root)

            for au in dist_urls:
                p.doc['Root'].new_term('Root.Distribution', au)

            csv_url = p.save()

            with open(csv_url.path, mode='rb') as f:
                m.bucket.write(f.read(), csv_url.target_file, m.acl)

            dist_urls.append(m.bucket.access_url(p.cache_path))
        else:
            # If this happens, then no packages were created, because an FS package
            # is always built first
            prt("Not creating CSV package; no FS package was uploaded")

    return dist_urls



def show_credentials(profile):
    import boto3

    session = boto3.Session(profile_name=profile)

    if profile:
        cred_line = " 'eval $(metasync -C -p {} )'".format(profile)
    else:
        cred_line = " 'eval $(metasync -C)'"

    prt("export AWS_ACCESS_KEY_ID={} ".format(session.get_credentials().access_key))
    prt("export AWS_SECRET_ACCESS_KEY={}".format(session.get_credentials().secret_key))
    prt("# Run {} to configure credentials in a shell".format(cred_line))


def run_docker(m):
    """Re-run the metasync command in docker. """

    import botocore.session
    from subprocess import Popen, PIPE, STDOUT

    raise NotImplementedError("No longer have access to raw_args")

    session = botocore.session.get_session()

    args = ['docker', 'run', '--rm', '-t', '-i',
            '-eAWS_ACCESS_KEY_ID={}'.format(session.get_credentials().access_key),
            '-eAWS_SECRET_ACCESS_KEY={}'.format(session.get_credentials().secret_key),
            'civicknowledge/metatab',
            'metasync']

    for a in ('-D', '--docker'):
        try:
            m.raw_args.remove(a)
        except ValueError:
            pass

    args.extend(m.raw_args[1:])

    if m.args.verbose:
        prt("Running Docker Command: ", ' '.join(args))
    else:
        prt("Running In Docker")

    process = Popen(args, stdout=PIPE, stderr=STDOUT)
    with process.stdout:
        for line in iter(process.stdout.readline, b''):
            prt(line.decode('ascii'), end='')

    exitcode = process.wait()  # 0 means success

    exit(exitcode)

