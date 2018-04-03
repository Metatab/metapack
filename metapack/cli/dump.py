#
#
# Code storage for the dump_resource features of the metapack program

from metapack import MetapackDoc, Downloader

from metapack.cli.core import err, dump_resource, dump_resources


def metatab_query_handler(m):
    if m.args.resource or m.args.head:

        limit = 20 if m.args.head else None

        try:
            doc = MetapackDoc(m.mt_file, cache=m.cache)

        except OSError as e:
            err("Failed to open Metatab doc: {}".format(e))
            return

        if m.resource:
            dump_resource(doc, m.resource, limit)
        else:
            dump_resources(doc)