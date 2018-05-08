# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN

The program uses the Root.Distributions in the source package to locate packages to link into a CKAN record.

"""

from metapack.cli.core import prt, err
from metapack.package import *
from .core import MetapackCliMemo as _MetapackCliMemo
from tabulate import tabulate
import sys

downloader = Downloader()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)
        self


def doc_args(subparsers):

    parser = subparsers.add_parser(
        'doc',
        help='Generate documentation'
    )

    parser.set_defaults(run_command=doc)

    parser.add_argument('-g', '--graph', default=False, action='store_true',
                             help="Create a dependency graph")

    parser.add_argument('-d', '--dependencies', default=False, action='store_true',
                        help="List the dependencies")

    parser.add_argument('-p', '--packages', default=False, action='store_true',
                        help="When listing dependencies, list only packages")

    parser.add_argument('-v', '--view', default=False, action='store_true',
                       help="View doc file after creating it")

    parser.add_argument('-D', '--directory',  help="Output file name")

    parser.add_argument('--legend', action='store_true', help="Create the dependency graph legend")

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

def doc(args):

    m = MetapackCliMemo(args, downloader)

    if m.args.graph:
        graph(m)
    elif m.args.dependencies:
        dependencies(m)

    if m.args.legend:
        legend(m)

from functools import total_ordering

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

def dependencies(m):

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

def graph(m):
    """

    :param m:
    :return:
    """
    from graphviz import Digraph

    from os.path import splitext, dirname

    output =  m.doc.name+'.jpg'

    basename, format = splitext(output)

    g = Digraph(comment=m.doc.name, filename=basename+'.gv', directory=m.args.directory)

    nodes, edges = nodes_edges(m)

    for n in nodes:
        g.node(name=n.name, label=wrap_url(n.label,40), shape = n.shape)

    for this, that in edges:
        g.edge(that.name, this.name)

    g.attr(overlap='false')
    g.format = format.lstrip('.')
    g.engine = 'dot'
    g.render(basename, view=m.args.view, cleanup=True)

    if not m.args.view:
        prt("Wrote file "+output)


# This draws the legend for the interface documents.
dependency_legend = """
digraph {
    labelloc="t";
    label="Legend";
	"Datapackage" [label="datapackage" shape=component]
    "Database" [label="Database" shape=cylinder]
    "DataFile" [label="Data File" shape=folder]
    "Other" [label="Other Datafile" shape=oval]
    "Rest" [label="REST" shape=cds]
    "Web" [label="Web Doc" shape=note]

}
"""

def legend(m):
    from graphviz import Source

    g = Source(dependency_legend)

    g.format = 'jpg'
    g.engine = 'dot'

    g.render(filename='legend', directory=m.args.directory, cleanup=True)

    prt("Wrote legend file")





