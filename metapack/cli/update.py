# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

from metapack import Downloader
from metapack.cli.core import update_name, process_schemas, MetapackCliMemo, warn, prt, \
    update_schema_properties, write_doc

downloader = Downloader.get_instance()


def update(subparsers):
    parser = subparsers.add_parser(
        'update',
        help='Update a metatab file or metatpack package',
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_update)

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    parser.set_defaults(handler=None)

    ##
    ## Build Group

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-c', '--categories', default=False, action='store_true',
                       help='Update categories, creating a new categories.csv metadata file')

    group.add_argument('-n', '--name', action='store_true', default=False,
                       help="Update the Name from the Datasetname, Origin and Version terms")

    group.add_argument('-s', '--schemas', default=False, action='store_true',
                       help='Rebuild the schemas for files referenced in the resource section')

    group.add_argument('-P', '--schema-properties', default=False, action='store_true',
                       help='Load schema properties from generators and upstream sources')



    group.add_argument('-D', '--descriptions', action='store_true', default=False,
                       help='Import descriptions for package references')

    parser.add_argument('-A', '--alt-name', default=False, action='store_true',
                       help='Move AltNames to column name')

    parser.add_argument('-X', '--clean-properties', default=False, action='store_true',
                       help='Remove unused columns in the schema, like AltName')

    parser.add_argument('-C', '--clean', default=False, action='store_true',
                        help='Clean schema before processing')

    parser.add_argument('-F', '--force', action='store_true', default=False,
                        help='Force the operation')


def run_update(args):
    m = MetapackCliMemo(args, downloader)

    if m.args.schemas:
        update_schemas(m)

    if m.args.schema_properties:
        update_schema_props(m)

    if m.args.clean_properties:
        clean_properties(m)

    if m.args.alt_name:
        move_alt_names(m)

    if m.args.categories:
        update_categories(m)

    elif m.mtfile_url.scheme == 'file' and m.args.name:
        update_name(m.mt_file, fail_on_missing=True, force=m.args.force)

    elif m.args.descriptions:
        update_descriptions(m)


def update_schemas(m):
    update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    resource = m.get_resource()

    force = m.args.force

    if m.resource:
        if not resource:
            warn("Resource {} is not in metadata".format(m.resource))
        else:
            force = True

    process_schemas(m.mt_file, resource=m.resource, cache=m.cache, clean=m.args.clean, force=force)


def update_schema_props(m):
    doc = m.doc

    update_schema_properties(doc, force=m.args.force)

    write_doc(doc)


def clean_properties(m):
    doc = m.doc

    doc.clean_unused_schema_terms()

    write_doc(doc)


def update_descriptions(m):
    doc = m.doc

    for ref in doc.resources():
        print ('!!!', ref.resource)
        ref['Description'] = ref.description

        print(ref.name, id(ref))
        print("Updated '{}' to '{}'".format(ref.name, ref.description))

    # print(m.doc.as_csv())

    for ref in doc.references():
        v = ref.find_first('Description')

        print(ref.name, id(ref), ref.description)




    write_doc(doc)


def update_categories(m):
    import metapack as mp

    doc = mp.MetapackDoc()
    doc['Root'].get_or_new_term('Root.Title', 'Schema and Value Categories')
    doc.new_section('Schema', ['Description', 'Ordered'])

    update_resource_categories(m, m.get_resource(), doc)

    doc.write_csv('categories.csv')


def update_resource_categories(m, resource, doc):
    columns = resource.row_generator.columns

    tab = doc['Schema'].new_term('Root.Table', m.get_resource().name)

    for col in columns:

        doc_col = tab.new_child('Column', col.get('name'), description=col.get('description'))

        if col.get('ordered'):
            doc_col.new_child('Column.Ordered', 'true')

        for k, v in col.get('values', {}).items():
            doc_col.new_child('Column.Value', k, description=v)

    doc.cleanse()  # Creates Modified and Identifier

    return doc


def move_alt_names(m):
    doc = m.doc

    for t in doc['Schema'].find('Root.Table'):
        moved = 0
        for c in t.find('Table.Column'):

            altname = c.get('AltName')
            if altname:

                if not c.get('Description'):
                    c.description = c.name.replace('\n',' ')

                c.name = altname.value
                c.remove_child(altname)

                moved += 1


        prt("Moved {} names in '{}'".format(moved, t.name))

    write_doc(doc)
