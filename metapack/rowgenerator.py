# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from rowgenerators import Source
from metapack.jupyter.exec import execute_notebook
from os.path import join, exists
from csv import reader

from rowgenerators.exceptions import AppUrlError
from metapack.util import get_materialized_data_cache

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

        from os.path import basename

        self.start()

        dr_name = get_materialized_data_cache(self.doc)

        path = join(dr_name,  self.ref.target_file + ".csv")

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


class PandasDataframeSource(Source):
    """Iterates a pandas dataframe  """


    def __init__(self, url, df, cache, working_dir=None, **kwargs):
        super().__init__(url, cache, working_dir, **kwargs)

        self._df = df

    def __iter__(self):

        import numpy as np

        self.start()

        df = self._df

        if len(df.index.names) == 1 and df.index.names[0] is None and df.index.dtype != np.dtype('O'):
            # For an unnamed, single index, assume that it is just a row number
            # and we don't really need it

            yield list(df.columns)

            for index, row in df.iterrows():
                yield list(row)

        else:

            # Otherwise, either there are more than

            index_names = [n if n else "index{}".format(i) for i, n in enumerate(df.index.names)]

            yield index_names + list(df.columns)

            if len(df.index.names) == 1:
                idx_list = lambda x: [x]
            else:
                idx_list = lambda x: list(x)

            for index, row in df.iterrows():
                yield idx_list(index) + list(row)


        self.finish()


def copy_reference(resource, doc, env, *args, **kwargs):
    """A row-generating function that yields from a reference. This permits an upstream package to be
    copied and modified by this package, while being formall referenced as a dependency

    The function will generate rows from a reference that has the same name as the resource term
    """

    yield from doc.reference(resource.name)


