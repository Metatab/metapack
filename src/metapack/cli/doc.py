# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

import sys
from functools import total_ordering

from tabulate import tabulate

from metapack.cli.core import err, prt, warn
from metapack.package import *

from .core import MetapackCliMemo as _MetapackCliMemo

downloader = Downloader.get_instance()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)
        self


def doc_args(subparsers):

    parser = subparsers.add_parser(
        'doc',
        help='Generate documentation'
    )

    cmdsp = parser.add_subparsers(help='sub-command help')

    cmdp = cmdsp.add_parser('graph', help='Dependency graph')
    cmdp.set_defaults(run_command=graph_cmd)

    cmdp.add_argument('-d', '--dependencies', default=False, action='store_true',
                        help="List the dependencies")

    cmdp.add_argument('-v', '--view', default=False, action='store_true',
                       help="View doc file after creating it")

    cmdp.add_argument('-V', '--graphviz', default=False, action='store_true',
                       help="Also dump the Graphviz file to the stdout")

    cmdp.add_argument('-D', '--directory',  help="Output file name")

    cmdp.add_argument('-N', '--nonversion', default=False, action='store_true',
                      help="Use the nonversioned package name for the file name")

    cmdp.add_argument('metatabfile', nargs='?',
                      help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    ##
    ##
    cmdp = cmdsp.add_parser('deps', help='Display a table of dependencies')
    cmdp.set_defaults(run_command=deps_cmd)

    cmdp.add_argument('-p', '--packages', default=False, action='store_true',
                        help="When listing dependencies, list only packages")

    cmdp.add_argument('-f', '--format', default='pipe',
                      help="Table format, an argument to tabulate(). Common options are:"
                      " plain, simple, jira, html, pipe, rst, mediawiki. Use pipe for markdown.")

    cmdp.add_argument('metatabfile', nargs='?',
                      help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    ##
    ##
    cmdp = cmdsp.add_parser('schema', help='Print a schema')
    cmdp.set_defaults(run_command=dump_schemas)

    cmdp.add_argument('-f', '--format', default='pipe',
                      help="Table format, an argument to tabulate(). Common options are:"
                      " plain, simple, jira, html, pipe, rst, mediawiki. Use pipe for markdown.")

    cmdp.add_argument('-c', '--column', action='append',
                      help="Add a column from the schema to the output table. If specified, only the"
                           "'name' column is included by default")

    ##
    ##
    for arg, help, cmd in [
        ('markdown', 'Output the package markdown documentation', dump_markdown),
        ('html', 'Output the package html documentation', dump_html),
        ('json', 'Output the package documentation context in json format', dump_json),
        ('jsonld', 'Output the package description in Schema.org JSONLD format', dump_jsonld),
        ('yaml', 'Output the package documentation context in yaml format', dump_yaml)
    ]:
        cmdp = cmdsp.add_parser(arg,help=help)
        cmdp.set_defaults(run_command=cmd)

        if arg in ('html', 'markdown'):
            cmdp.add_argument('-t', '--template', default='short_documentation.md',
                          help="Set the template.")

        if arg in ('json', 'yaml', 'jsonld'):
            cmdp.add_argument('-c', '--contact', action='store_true',
                              help='Show only the contact information')

        cmdp.add_argument('metatabfile', nargs='?',
                          help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")


def graph_cmd(args):

    m = MetapackCliMemo(args, downloader)

    graph(m)


@total_ordering
class _DependencyNode(object):

    @property
    def name(self):
        return self.node['name']

    @property
    def label(self):
        return self.node['label']

    @property
    def shape(self):
        return self.node['shape']

    def slugify(self,v):
        from rowgenerators.util import slugify

        return slugify(v)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __str__(self):
        return '<{} {} {} {}>'.format(type(self).__name__, self.name, self.label, self.shape)


class DependencyNode(_DependencyNode):

    def __new__(cls, ref, parent):
        from metapack import MetapackDoc
        from metapack.appurl import is_metapack_url
        from rowgenerators.appurl.sql import Sql

        if isinstance(ref,MetapackDoc):
            return PackageDependencyNode(ref, parent)

        u = ref.expanded_url

        if is_metapack_url(u):
            return PackageDependencyNode(u.doc, parent)
        elif isinstance(u,Sql):
            return SqlDependencyNode(ref, parent)
        elif u:
            return UrlDependencyNode(u, parent)
        else:
            return ResourceDependencyNode(ref, parent)


class PackageDependencyNode(_DependencyNode):
    """Dependency node that references a metapack package"""
    def __init__(self, ref, parent):
        self.doc = ref
        self.parent = parent

    @property
    def node(self):
        return {
            'name': self.slugify(self.doc.name),
            'label': self.doc.name,
            'shape': 'component'
        }

class UrlDependencyNode(_DependencyNode):
    """Dependency node that references a url"""
    def __init__(self, ref, parent):
        self.url = ref
        self.parent = parent

    def _shape(self):
        if self.url.scheme == 'file':
            return 'folder'
        elif self.url.scheme.startswith('http'):
            if self.url.proto != self.url.scheme:
                return 'cds' # An HTTP based API
            else:
                return 'note'
        else:
            return 'box'

    def _label(self):
        if self.url.scheme == 'file':
            return self.url.path
        elif self.url.scheme.startswith('http'):
            if self.url.scheme != self.url.proto:
                proto = '{}+{}'.format(self.url.scheme,self.url.proto)
            else:
                proto = '{}'.format(self.url.scheme)

            return "Proto: {}\nHost: {}\nPath: {}\nApi: {}".format(proto, self.url.netloc,self.url.path,
                                                                 self.url.fragment[0])
        else:
            return str(self.url)

    @property
    def node(self):
        return {
            'name': self.slugify(str(self.url)),
            'label': str(self.url),
            'shape': self._shape()
        }

class ResourceDependencyNode(_DependencyNode):
    """Dependency node that references a resoruce where the URL doesn't expand"""
    def __init__(self, ref, parent):
        self.resource = ref
        self.parent = parent

    @property
    def node(self):
        return {
            'name': self.slugify(self.resource.name),
            'label': self.resource.name,
            'shape': 'oval'
        }

class SqlDependencyNode(_DependencyNode):

    def __init__(self, ref, parent):
        self.resource = ref
        self.parent = parent

    @property
    def node(self):
        return {
            'name': self.slugify(self.resource.name),
            'label': self.resource.name,
            'shape': 'cylinder'
        }

def yield_deps(doc):
    """
    TODO: This implementation is very specific to a particular environment and project, and should be generalized.
    :param doc:
    :return:
    """

    this_node = DependencyNode(doc, None)

    for r in doc.references():

        other_node = DependencyNode(r, this_node)

        yield (this_node, other_node)

        if isinstance(other_node, PackageDependencyNode):
            yield from yield_deps(other_node.doc)

def nodes_edges(m):
    nodes = set()
    edges = set(yield_deps(m.doc))

    for this, that in edges:
        nodes.add(this)
        nodes.add(that)

    return nodes, list(edges)

def deps_cmd(args):

    m = MetapackCliMemo(args, downloader)

    nodes, edges = nodes_edges(m)

    if m.args.packages:
        for n in nodes:
            if isinstance(n,PackageDependencyNode):
                print(n.label)

    else:
        rows = [ (this.label, that.label) for this, that in sorted(edges) ]

        print (tabulate(rows,headers='This That'.split()))


def wrap_url(s, l):
    """Wrap a URL string"""
    parts = s.split('/')

    if len(parts) == 1:
        return parts[0]
    else:
        i = 0
        lines = []
        for j in range(i, len(parts) + 1):
            tv = '/'.join(parts[i:j])
            nv = '/'.join(parts[i:j + 1])

            if len(nv) > l or nv == tv:
                i = j
                lines.append(tv)

        return '/\n'.join(lines)



def legend_subgraph(g):

    with g.subgraph(name='cluster1') as c:
        c.attr(rank='sink')
        #c.attr(rankdir='TB')
        c.attr(labeltoc='t')
        c.attr(label='Legend')
        c.node(name='Datapackage', label='datapackage', shape='component')
        c.node(name='Database', label='Database', shape='cylinder')
        c.node(name='DataFile', label='Data File', shape='folder')
        c.node(name='Other', label='Other Datafile', shape='oval')
        c.node(name='Rest', label='REST', shape='cds')
        c.node(name='Web', label='Web Doc', shape='note')

        c.edge('Datapackage', 'Database', style='invis')
        c.edge('Database','DataFile', style='invis')
        #c.edge('DataFile', 'Other')
        c.edge('Other', 'Rest', style='invis')
        c.edge('Rest', 'Web', style='invis')

def graph(m):
    """

    :param m:
    :return:
    """
    from graphviz import Digraph

    from os.path import splitext, dirname

    if m.args.nonversion:
        output = m.doc.nonver_name + '.jpg'
    else:
        output = m.doc.name + '.jpg'


    basename, format = splitext(output)

    g = Digraph(comment=m.doc.name, filename=basename+'.gv', directory=m.args.directory)

    legend_subgraph(g)

    nodes, edges = nodes_edges(m)

    for n in nodes:
        g.node(name=n.name, label=wrap_url(n.label,40), shape = n.shape)

    for this, that in edges:
        g.edge(that.name, this.name)

    g.attr(overlap='false')
    g.attr(rankdir='LR')

    g.format = format.lstrip('.')
    g.engine = 'dot'
    g.render(basename, view=m.args.view, cleanup=True)

    if m.args.graphviz:
        prt(g.source)

    if not m.args.view:
        prt("Wrote file "+output)



def dump_schemas(args):
    from .run import get_resource

    m = MetapackCliMemo(args, downloader)

    r = m.doc.resource(m.resource)

    if not r:
        # Try a reference, which must be resolved to a resource in the foreign data package
        # to get a schema.
        outer_r = m.doc.reference(m.resource)

        if outer_r:
            try:
                r = outer_r.expanded_url.resource
            except AttributeError:
                warn("Reference '{}' is not a Metapack url, doesn't have a schema".format(m.resource))
        else:
            r = None


    if not r:
        prt('\nSelect a resource or reference to display the schema for:\n')
        d = []
        for r in m.doc.resources():
            d.append(('Resource', r.name, r.url))

        for r in m.doc.references():
            d.append(('Reference', r.name, r.url))


        prt(tabulate(d, 'Type Name Url'.split()))

        prt('')
        prt("Specify the resource as a fragment, escaping it if the '#' is the first character. For instance: ")
        prt("  mp doc schema .#resource_name")
        prt('')
        sys.exit(0)

    dump_schema(m, r)

def dump_schema(m, r):

    st = r.schema_term
    rows_about_columns = []

    if m.args.column:

        headers = ['Name']+[e.title() for e in m.args.column]

        for c in st.find('Table.Column'):
            table_row = [c.name]
            for table_col in m.args.column:
                table_row.append(c.get_value(table_col))
            rows_about_columns.append(table_row)

    else:
        headers = 'Name AltName DataType Description'.split()
        for c in st.find('Table.Column'):
            rows_about_columns.append((c.name, c.get_value('altname'), c.get_value('datatype'), c.get_value('description')))

    prt(tabulate(rows_about_columns, headers=headers, tablefmt=m.args.format))

def dump_markdown(args):
    from metapack.html import markdown

    m = MetapackCliMemo(args, downloader)

    print(markdown(m.doc, template=args.template))

def dump_html(args):
    from metapack.html import html
    m = MetapackCliMemo(args, downloader)

    print(html(m.doc, template=m.args.template))


def dump_json(args):
    from metapack.html import display_context
    import json

    m = MetapackCliMemo(args, downloader)

    print(json.dumps(display_context(m.doc), indent=4))


def dump_jsonld(args):
    from metapack.html import jsonld
    import json

    m = MetapackCliMemo(args, downloader)

    print(json.dumps(jsonld(m.doc), indent=4))



def dump_yaml(args):
    from metapack.html import display_context
    from collections import OrderedDict
    import yaml

    def represent_odict(dump, tag, mapping, flow_style=None):
        """Like BaseRepresenter.represent_mapping, but does not issue the sort().
        """
        value = []
        node = yaml.MappingNode(tag, value, flow_style=flow_style)
        if dump.alias_key is not None:
            dump.represented_objects[dump.alias_key] = node
        best_style = True
        if hasattr(mapping, 'items'):
            mapping = mapping.items()
        for item_key, item_value in mapping:
            node_key = dump.represent_data(item_key)
            node_value = dump.represent_data(item_value)
            if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
                best_style = False
            if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
                best_style = False
            value.append((node_key, node_value))
        if flow_style is None:
            if dump.default_flow_style is not None:
                node.flow_style = dump.default_flow_style
            else:
                node.flow_style = best_style
        return node

    yaml.SafeDumper.add_representer(OrderedDict,
                                    lambda dumper, value: represent_odict(dumper, u'tag:yaml.org,2002:map', value))

    m = MetapackCliMemo(args, downloader)

    o = display_context(m.doc)

    if args.contact:
       o = o['contacts']

    y = yaml.safe_dump(o, default_flow_style=False)

    print(y)
