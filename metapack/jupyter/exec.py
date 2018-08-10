# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Functions for executing Jupyter notebooks
"""

from .exc import NotebookError


def execute_notebook(nb_path, pkg_dir, dataframes, write_notebook=False, env=None):
    """
    Execute a notebook after adding the prolog and epilog. Can also add %mt_materialize magics to
    write dataframes to files

    :param nb_path: path to a notebook.
    :param pkg_dir: Directory to which dataframes are materialized
    :param dataframes: List of names of dataframes to materialize
    :return: a Notebook object
    """

    import nbformat
    from metapack.jupyter.preprocessors import AddEpilog, AddProlog
    from metapack.jupyter.exporters import ExecutePreprocessor, Config
    from os.path import dirname, join, splitext, basename
    from nbconvert.preprocessors.execute import CellExecutionError

    with open(nb_path, encoding='utf8') as f:
        nb = nbformat.read(f, as_version=4)

    root, ext = splitext(basename(nb_path))

    c = Config()

    nb, resources = AddProlog(config=c, env=env or {}).preprocess(nb, {})

    nb, resources = AddEpilog(config=c, pkg_dir=pkg_dir,
                              dataframes=dataframes,
                              ).preprocess(nb, {})

    def _write_notebook(nb_path, root, ext, write_notebook):
        if write_notebook:
            if write_notebook is True:
                exec_nb_path = join(dirname(nb_path), root + '-executed' + ext)
            else:
                exec_nb_path = write_notebook

            with open(exec_nb_path, 'w', encoding='utf8') as f:
                nbformat.write(nb, f)

    _write_notebook(nb_path, root, ext, write_notebook)

    try:
        ep = ExecutePreprocessor(config=c)

        ep.timeout = 5*60

        nb, _ = ep.preprocess(nb, {'metadata': {'path': dirname(nb_path)}})
    except (CellExecutionError, TimeoutError) as e:
        err_nb_path = join(dirname(nb_path), root + '-errors' + ext)
        with open(err_nb_path, 'w', encoding='utf8') as f:
            nbformat.write(nb, f)

        raise CellExecutionError("Errors executing noteboook. See notebook at {} for details.\n{}"
                                 .format(err_nb_path, ''))

    except ImportError as e:
        raise NotebookError("Failed to import a library required for notebook execution: {}".format(str(e)))

    _write_notebook(nb_path, root, ext, write_notebook)

    return nb