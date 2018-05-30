# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Support for IPython and Python kernels in Jupyter Notebooks"""

from metapack import open_package as op
from metapack.constants import PACKAGE_PREFIX
from os import getcwd
from metapack.util import walk_up
from os.path import getmtime, join, exists
from metapack.exc import PackageError
from rowgenerators.exceptions import RowGeneratorError


def caller_locals():
    """Get the local variables in the caller's frame."""
    import inspect
    frame = inspect.currentframe()
    try:
        return frame.f_back.f_back.f_locals
    finally:
        del frame


def in_build():
    """Return True if running in a build, rather than interactively in Jupyter"""
    return 'metatab_doc' in caller_locals()


def open_source_package(dr=None):
    """Like open_package(), but always open the source package"""
    if dr is None:
        dr = getcwd()

    for i, e in enumerate(walk_up(dr)):

        if 'metadata.csv' in e[2]:
            return op(join(e[0], 'metadata.csv'))

        if i > 2:
            break

    return None


def open_package(locals=None, dr=None):
    """Try to open a package with the metatab_doc variable, which is set when a Notebook is run
    as a resource. If that does not exist, try the local _packages directory"""

    if locals is None:
        locals = caller_locals()

    try:
        # Running in a package build
        return op(locals['metatab_doc'])

    except KeyError:
        # Running interactively in Jupyter

        package_name = None
        build_package_dir = None
        source_package = None

        if dr is None:
            dr = getcwd()

        for i, e in enumerate(walk_up(dr)):

            if 'metadata.csv' in e[2]:
                source_package = join(e[0], 'metadata.csv')
                p = op(source_package)
                package_name = p.find_first_value("Root.Name")

                if not package_name:
                    raise PackageError("Source package in {} does not have root.Name term".format(e[0]))

                if PACKAGE_PREFIX in e[1]:
                    build_package_dir = join(e[0], PACKAGE_PREFIX)

                break

            if i > 2:
                break

        if build_package_dir and package_name and exists(join(build_package_dir, package_name)):
            # Open the previously built package
            built_package = join(build_package_dir, package_name)
            try:
                return op(built_package)
            except RowGeneratorError as e:
                pass  # Probably could not open the metadata file.

        if source_package:
            # Open the source package
            return op(source_package)

    raise PackageError("Failed to find package, either in locals() or above dir '{}' ".format(dr))


def rebuild_schema(doc, r, df):
    """Rebuild the schema for a resource based on a dataframe"""
    import numpy as np

    # Re-get the resource in the doc, since it may be different.
    try:
        r = doc.resource(r.name)
    except AttributeError:
        # Maybe r is actually a resource name
        r = doc.resource(r)

    def alt_col_name(name, i):
        import re

        if not name:
            return 'col{}'.format(i)

        return re.sub('_+', '_', re.sub('[^\w_]', '_', str(name)).lower()).rstrip('_')

    df_types = {
        np.dtype('O'): 'text',
        np.dtype('int64'): 'integer',
        np.dtype('float64'): 'number'
    }

    try:
        df_index_frame = df.index.to_frame()
    except AttributeError:
        df_index_frame = None

    def get_col_dtype(c):

        c = str(c)

        try:
            return df_types[df[c].dtype]
        except KeyError:
            # Maybe it is in the index?
            pass

        try:
            return df_types[df_index_frame[c].dtype]
        except TypeError:
            # Maybe not a multi-index
            pass

        if c == 'id' or c == df.index.name:
            return df_types[df.index.dtype]

        return 'unknown'

    columns = []
    schema_term = r.schema_term[0]

    if schema_term:

        old_cols = {c['name'].value: c.properties for c in schema_term.children}
        for c in schema_term.children:
            schema_term.remove_child(c)

        schema_term.children = []

    else:
        old_cols = {}
        schema_term = doc['Schema'].new_term('Table', r.schema_name)

    index_names = [n if n else "id" for n in df.index.names]

    for i, col in enumerate(index_names + list(df.columns)):
        acn = alt_col_name(col, i) if alt_col_name(col, i) != str(col) else ''

        d = {'name': col, 'datatype': get_col_dtype(col), 'altname': acn}

        if col in old_cols.keys():
            lookup_name = col
        elif acn in old_cols.keys():
            lookup_name = acn
        else:
            lookup_name = None

        if lookup_name and lookup_name in old_cols:

            for k, v in schema_term.properties.items():

                old_col = old_cols.get(lookup_name)

                for k, v in old_col.items():
                    if k != 'name' and v:
                        d[k] = v

        columns.append(d)

    for c in columns:
        name = c['name']
        del c['name']
        datatype = c['datatype']
        del c['datatype']
        altname = c['altname']
        del c['altname']

        schema_term.new_child('Column', name, datatype=datatype, altname=altname, **c)


def rewrite_schema(r, df, doc=None):
    """Rebuild the schema for a resource based on a dataframe and re-write the doc"""

    from metapack.cli.core import write_doc

    if doc is None:
        doc = open_source_package()

    rebuild_schema(doc, r, df)

    write_doc(doc, doc.ref)


def interactive_rewrite_schema(r, df, doc=None):
    """Rebuild the schema for a resource based on a dataframe and re-write the doc,
    but only if running the notebook interactively, not while building"""

    if 'metatab_doc' in caller_locals():
        return False

    if doc is None:
        doc = open_source_package()

    rewrite_schema(r, df, doc)

    return True


def get_dataframes():
    """Yield tuples of dataframe variable name and the dataframe. Skips variables with names that
    start with an underscore"""

    for k, v in caller_locals().items():
        if k.startswith('_'):
            continue

        if isinstance(v, pd.core.frame.DataFrame):
            yield k, v


import json
import os.path
import re
import ipykernel
import requests
from urllib.parse import urljoin
from notebook.notebookapp import list_running_servers

def get_notebook_path():
    """
    Return the full path of the jupyter notebook.
    """
    kernel_id = re.search('kernel-(.*).json',
                          ipykernel.connect.get_connection_file()).group(1)
    servers = list_running_servers()
    for ss in servers:
        response = requests.get(urljoin(ss['url'], 'api/sessions'),
                                params={'token': ss.get('token', '')})
        for nn in json.loads(response.text):
            if nn['kernel']['id'] == kernel_id:
                relative_path = nn['notebook']['path']
                return os.path.join(ss['notebook_dir'], relative_path)


def get_notebook_rel_path(pkg=None):
    """Get the path of a notebook, relative to the current soruce package"""
    pkg = pkg or open_source_package()
    pkg_path = str(pkg.package_url.fspath)
    nb_path = get_notebook_path()

    return nb_path.replace(pkg_path, '').strip('/')


def add_dataframe(df, name, pkg=None, description=''):
    """Add a dataframe to a source package. Pass in either the name of the dataframe, or the dataframe.
    If the dataframeis passed it, the name will be the dataframe's variable name. The function
    will re-write the source package with the new resource.

    """
    from warnings import warn
    from metapack.cli.core import alt_col_name, type_map
    import numpy as np

    if name is None or df is None:
        warn("Did not find dataframe for reference '{}' ".format(ref))
        return

    pkg = pkg or open_source_package()

    resource_ref = 'file:' + get_notebook_rel_path(pkg) + '#' + name

    t = pkg.find_first('Root.Datafile', value=resource_ref)
    col_props = {}

    if t:
        print("Datafile exists for url '{}', deleting".format(resource_ref))

        if t.schema_term:
            col_props = { c['name']:c for c in t.columns()}
            pkg.remove_term(t.schema_term)

        pkg.remove_term(t)

    t = pkg['Resources'].new_term('Root.Datafile', resource_ref, name=name, description=description)

    st = pkg['Schema'].new_term('Table', t.schema_name, description=description)

    for i, name in enumerate(df.columns):

        props = col_props.get(name,{})

        try:
            native_type = type(np.asscalar(df[name].dtype.type(0))).__name__
        except ValueError:
            native_type = df[name].dtype.name
        except AttributeError:
            native_type = type(df[name][0]).__name__

        for pn in 'datatype name pos header'.split():
            if pn in props:
                del props[pn]

        if 'altname' in props:
            altname = props['altname']
            del props['altname']
        else:
            raw_alt_name = alt_col_name(name, i)
            altname = raw_alt_name if raw_alt_name != name else ''

        col = df[name]

        if hasattr(col, 'description'):  # custom property
            props['description'] = col.description

        t = st.new_child('Column', name,
                            datatype=type_map.get(native_type, native_type),
                            altname=altname,
                            **props)


    pkg.write_csv()