# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """
import json
from io import BytesIO
from os.path import join, getsize
from os import walk
import boto3
import unicodecsv as csv

from rowgenerators import parse_app_url
from metatab import DEFAULT_METATAB_FILE

from .core import PackageBuilder




class S3PackageBuilder(PackageBuilder):
    """A FS package in an S3 bucket """

    type_code = 's3'

    def __init__(self, source_ref=None, package_root=None, callback=None, env=None, acl=None, force=False):

        super().__init__(source_ref, package_root, callback, env)

        self.package_path = self.package_root.join(self.package_name)

        self.cache_path = self.package_name

        self.force = force

        self._acl = acl if acl else 'public-read'

        self.bucket = S3Bucket(self.package_path, acl=self._acl)

        self.files_processed = []


    @property
    def access_url(self):
        from metapack import MetapackPackageUrl
        return MetapackPackageUrl(self.bucket.access_url(DEFAULT_METATAB_FILE),
                                  downloader=self._source_ref.downloader)
    @property
    def private_access_url(self):
        from metapack import MetapackPackageUrl
        return MetapackPackageUrl(self.bucket.access_url(DEFAULT_METATAB_FILE),
                                  downloader=self._source_ref.downloader)

    @property
    def public_access_url(self):
        from metapack import MetapackPackageUrl

        return MetapackPackageUrl(self.bucket.public_access_url(DEFAULT_METATAB_FILE),
                                  downloader=self._source_ref.downloader)

    @property
    def signed_url(self):
        """A URL with an access signature or password """
        return self.bucket.signed_access_url(DEFAULT_METATAB_FILE)

    def exists(self, url=None):
        return self.bucket.exists(DEFAULT_METATAB_FILE)


    def save(self):

        self.check_is_ready()

        # Resets the ref so that resource.resolved_url link to the resources as written in S3
        self._doc._ref = self.access_url.join('metatab.csv')

        # Copy all of the files from the Filesystem package
        for root, dirs, files in walk(self.source_dir):
            for f in files:
                source = join(root, f)
                rel = source.replace(self.source_dir, '').strip('/')

                with open(source,'rb') as f:
                    self.write_to_s3(rel,f)

        # Re-write the URLS for the datafiles
        for r in self.datafiles:
            r.url = self.bucket.access_url(r.url)

        # Re-write the HTML index file.
        self._write_html()

        # Rewrite Documentation urls:
        for r in self.doc.find(['Root.Documentation', 'Root.Image']):

            url = parse_app_url(r.url)
            if url.proto == 'file':
                r.url = self.bucket.access_url(url.path)


        return self.access_url

    def close(self):
        pass

    def write_to_s3(self, path, body, reason=''):
        from metapack.exc import PackageError

        access_url = self.bucket.write(body, path, acl=self._acl, force=self.force)

        if self.bucket.error:
            raise PackageError(self.bucket.last_reason[1])

        if self.bucket.last_reason:
            self.files_processed.append((*self.bucket.last_reason, access_url, path))

        return

    def _write_doc(self):

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerows(self.doc.rows)

        self.write_to_s3('metadata.csv', bio.getvalue())

    def _write_html(self):

        old_ref = self._doc._ref
        self._doc._ref = self.access_url.join('metatab.csv')
        self.write_to_s3('index.html',  self._doc.html)
        self._doc._ref = old_ref

    def _load_resource(self, r, abs_path=False):
        from itertools import islice
        gen = islice(r, 1, None)
        headers = r.headers

        r.url = 'data/' + r.name + '.csv'

        bio = BytesIO()

        data = write_csv(bio, headers, gen)

        self.prt("Loading data ({} bytes) to '{}' ".format(len(data), r.url))

        self.write_to_s3(r.url, data)

    def _load_documentation(self, term, contents, file_name):

        title = term['title'].value

        term['url'].value = 'docs/' + file_name

        self.wrote_files[file_name]
        self.write_to_s3(term['url'].value, contents)


def set_s3_profile(profile_name):
    """Load the credentials for an s3 profile into environmental variables"""
    import os

    session = boto3.Session(profile_name=profile_name)

    os.environ['AWS_ACCESS_KEY_ID'] = session.get_credentials().access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = session.get_credentials().secret_key


class S3Bucket(object):

    def __init__(self, url, acl='public', profile=None):
        import socket

        if url.scheme != 's3':
            raise ReferenceError("Must be an S3 url; got: {}".format(url))

        self.url = url

        session = boto3.Session(profile_name=profile)

        self._s3 = session.resource('s3')

        if acl == 'public':
            acl = 'public-read'

        # Reason that the last written file was either written or skipped
        self.last_reason = None

        self.error = False # Flag for error condition

        self._acl = acl


        self._bucket = self._s3.Bucket(self.bucket_name)

        # Check if the bucket name is a resolvable address.
        try:
            socket.getaddrinfo(self.bucket_name, None)
            self.dns_bucket = True
        except socket.gaierror:
            self.dns_bucket = False

    @property
    def prefix(self):
        return self.url.path

    @property
    def bucket_name(self):
        return self.url.netloc

    def access_url(self, *paths):

        if self._acl == 'private':
            return self.private_access_url(*paths)
        else:
            return self.public_access_url(*paths)

    def private_access_url(self, *paths):

        key = join(self.prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return "s3://{}/{}".format(self.bucket_name, key)

    def public_access_url(self, *paths):

        key = join(self.prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        url = s3.meta.endpoint_url.replace('https', 'http')

        if self.dns_bucket:
            url = url.replace('/s3.amazonaws.com','') # Assume bucket has name because it is setup as a CNAME

        return '{}/{}/{}'.format(url, self.bucket_name, key)

    def signed_access_url(self, *paths):

        import pdb;
        pdb.set_trace()

        key = join(self.prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return s3.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name, 'Key': key})


    def exists(self, *paths):
        import botocore

        # index.html is the last file written
        key = join(self.prefix, *paths).strip('/')

        exists = False

        try:
            self._bucket.Object(key).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                exists = False
            else:
                raise
        else:
            exists = True

        return exists

    def list(self):

        s3 = boto3.client('s3')

        # Create a reusable Paginator
        paginator = s3.get_paginator('list_objects')

        # Create a PageIterator from the Paginator
        page_iterator = paginator.paginate(Bucket=self.bucket_name)

        for page in page_iterator:
            for c in page['Contents']:
                yield c

    def write(self, body, path, acl=None, force=False):
        from botocore.exceptions import ClientError
        import mimetypes
        from metapack.cli.core import err, prt
        import hashlib

        acl = acl if acl is not None else self._acl

        key = join(self.prefix, path).strip('/')

        self.last_reason = ('wrote','Normal write')

        try:
            file_size = getsize(body.name) # Maybe it's an open file
        except AttributeError:
            # Nope, hope it is the file contents
            file_size = len(body)

        try:
            o = self._bucket.Object(key)

            md5 = o.e_tag[1:-1] # Rumor is this only works for single-part uplaoaded files

            if o.content_length == file_size:
                if force:
                    self.last_reason =('wrote',"File already in bucket, but forcing overwrite")
                else:

                    try:
                        local_md5 = (hashlib.md5(body).hexdigest())
                    except TypeError:
                        local_md5 = md5

                    if(local_md5 != md5):

                        self.last_reason = ('wrote',"File already in bucket, but md5 sums differ")
                    else:
                        self.last_reason = ('skip',"File already in bucket; skipping")

                        return self.access_url(path)
            else:
                self.last_reason = ('wrote',"File already in bucket, but length is different; re-writting")

        except ClientError as e:
            if int(e.response['Error']['Code']) in (403, 405):
                self.last_reason = ('error',"S3 Access failed for '{}:{}': {}\nNOTE: With Docker, this error is often "
                                    "the result of container clock drift. Check your container clock. "
                    .format(self.bucket_name, key, e))
                self.error = True
                return

            elif int(e.response['Error']['Code']) != 404:
                self.last_reason = ('error',"S3 Access failed for '{}:{}': {}".format(self.bucket_name, key, e))
                self.error = True
                return

        ct = mimetypes.guess_type(key)[0]

        try:
            self._bucket.put_object(Key=key,
                                    Body=body,
                                    ACL=acl,
                                    ContentType=ct if ct else 'binary/octet-stream')
        except Exception as e:
            self.last_reason = ('error',"Failed to write '{}' to '{}': {}".format(key, self.bucket_name, e))
            self.error = True

        return self.access_url(path)