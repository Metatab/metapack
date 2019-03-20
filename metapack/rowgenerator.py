# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from csv import reader
from metapack.jupyter.core import get_cell_source
from metapack.jupyter.exec import execute_notebook
from metapack.util import get_materialized_data_cache
from metatab.rowgenerators import TextRowGenerator
from os.path import join, exists
from rowgenerators import Source, SourceError
from rowgenerators.exceptions import AppUrlError


# The class used to be here, and still gets referenced here

class JupyterNotebookSource(Source):
    """Generate rows from an IPython Notebook.

     This generator will execute a Jupyter notebook. Before execution, it adds an "%mt_materalize"
     magic to the notebook, which will cause the target dataframe to be written to a temporary file, and
     the temporary file is yielded to the caller. Not most efficient, but it fits the model.
     """

    def __init__(self, ref, cache=None, working_dir=None, env=None, doc=None, **kwargs):
        super().__init__(ref, cache, working_dir, **kwargs)

        self.env = env
        self.doc = doc

    def start(self):
        pass

    def finish(self):
        pass

    def __iter__(self):

        self.start()

        dr_name = get_materialized_data_cache(self.doc)

        path = join(dr_name, self.ref.target_file + ".csv")

        # The first python notebook in the resources will get executed, cache the datafiles,
        # then the remaining ones will just use the caches data.
        if not exists(path):

            # The execute_notebook() function will add a cell with the '%mt_materialize' magic,
            # with a path that will case the file to be written to the same location as
            # path, below.

            if not self.ref.target_dataframe():
                raise AppUrlError('Url did not specify a dataframe; use the "#" fragment ')

            nb = execute_notebook(self.ref.path, dr_name, [self.ref.target_dataframe()], True, self.env)

        with open(path) as f:
            yield from reader(f)

        self.finish()


def copy_reference(resource, doc, env, *args, **kwargs):
    """A row-generating function that yields from a reference. This permits an upstream package to be
    copied and modified by this package, while being formally referenced as a dependency

    The function will generate rows from a reference that has the same name as the resource term
    """

    yield from doc.reference(resource.name)


class IpynbRowGenerator(TextRowGenerator):
    """Generate metatab rows from the text lines in a Jupyter notebook"""

    def __init__(self, ref, cache=None, working_dir=None, path=None, **kwargs):


        super().__init__(ref, cache, working_dir, path, **kwargs)

        self._ref = ref

        self._path = path or '<none>'

    def _open(self):
        import nbformat

        ref = self._ref

        while True:

            try:
                # Pathlib Path
                with ref.open() as f:
                    nb = nbformat.read(f, as_version=4)

                break
            except:
                pass

            try:
                # Filehandle
                nb = nbformat.read(ref, as_version=4)
                break
            except:
                pass

            try:
                # Url
                with ref.inner.fspath.open() as f:
                    nb = nbformat.read(f, as_version=4)
                break
            except:

                pass

            try:
                # File name
                with open(ref) as r:
                    nb = nbformat.read(f, as_version=4)
                break
            except:
                pass

            raise SourceError("Can't handle ref of type {}".format(type(ref)))

        return nb

    def _iter_lines(self, text, row_cb):
        import re

        for line in (text or '').splitlines():
            if re.match(r'^\s*#', line):  # Skip comments
                continue

            # Special handling for ====, which implies a section:
            #   ==== Schema
            # is also
            #   Section: Schema

            if line.startswith('===='):
                line = re.sub(r'^=*','Section:', line.strip())

            row = [e.strip() for e in line.split(':', 1)]

            # Pipe characters separate columns, so they get escaped when they are not seperators
            if len(row) > 1:
                row = [row[0]] + [ e.replace('\|','|') for e in re.split(r'(?<!\\)\|', row[1]) ]

            yield row

            yield from row_cb(row)

    def __iter__(self):

        nb = self._open()

        yield ['Declare', 'metatab-latest']
        yield ['Title', get_cell_source(nb, 'Title').strip('#').strip()]
        yield ['Description', get_cell_source(nb, 'Description') ]

        def row_cb(row):

            if row[0] == 'Section' and row[1] == 'Documentation':
                yield ('Readme', get_cell_source(nb, 'readme'))

        for tag in ['metadata', 'resources', 'schema']:
            yield from self._iter_lines(get_cell_source(nb, tag), row_cb)
